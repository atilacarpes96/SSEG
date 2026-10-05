"""Tenta criar a VM do servidor SSEG na Oracle Cloud até abrir vaga.

A A1.Flex grátis em São Paulo vive sem capacidade ("Out of host capacity").
Este script repete o pedido pela API até dar certo, e então grava o IP.
Ver sseg/workflow/plano-servidor-24-7.md.

Pré-requisito: chave de API da Oracle em ~/.oci/config (perfil DEFAULT),
criada pelo Átila no painel (Meu perfil -> Chaves de API).

Uso:
  python criar_vm_oracle.py            # tenta 2 OCPU/12 GB e, sem vaga, 1/6
  python criar_vm_oracle.py --checar   # só confere config, rede e imagem
  python criar_vm_oracle.py --micro    # plano B: a AMD Micro grátis (1/8 OCPU, 1 GB)

Log e resultado: ~/.oci/criar_vm.log e ~/.oci/vm_ip.txt
(--micro: ~/.oci/criar_vm_micro.log e ~/.oci/vm_micro_ip.txt)

O --micro existe porque em 04/10/2026 a A1 passou horas sem vaga. A Micro é
fraca para o Claude Code, mas segura o clone, o git e as rotinas agendadas
enquanto a A1 não sai. As duas cabem juntas no Always Free (2 Micro + 4 OCPU
A1, 200 GB de disco), então os dois modos rodam em paralelo.
"""

import argparse
import os
import sys
import time
from datetime import datetime

import oci

NOME = "carpes-24-7"
SHAPE = "VM.Standard.A1.Flex"
TAMANHOS = [(2, 12), (1, 6)]          # tenta o maior primeiro em cada rodada
CHAVE_SSH = os.path.expanduser("~/.ssh/sseg_servidor.pub")
PASTA = os.path.expanduser("~/.oci")
LOG = os.path.join(PASTA, "criar_vm.log")
RESULTADO = os.path.join(PASTA, "vm_ip.txt")
INTERVALO = 120                       # segundos entre rodadas
DURACAO_MAX = 7 * 24 * 3600


def modo_micro():
    """Troca as constantes para a VM.Standard.E2.1.Micro (x86, tamanho fixo)."""
    global NOME, SHAPE, TAMANHOS, LOG, RESULTADO
    NOME = "carpes-24-7-micro"
    SHAPE = "VM.Standard.E2.1.Micro"
    TAMANHOS = [None]                 # Micro não aceita shape_config
    LOG = os.path.join(PASTA, "criar_vm_micro.log")
    RESULTADO = os.path.join(PASTA, "vm_micro_ip.txt")


def log(msg):
    linha = f"{datetime.now():%d/%m %H:%M:%S}  {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def preparar():
    config = oci.config.from_file()
    oci.config.validate_config(config)
    comp = config["tenancy"]
    ident = oci.identity.IdentityClient(config)
    rede = oci.core.VirtualNetworkClient(config)
    compute = oci.core.ComputeClient(config)

    ad = ident.list_availability_domains(comp).data[0].name

    subnets = [s for s in rede.list_subnets(comp).data
               if s.lifecycle_state == "AVAILABLE" and not s.prohibit_public_ip_on_vnic]
    if not subnets:
        raise RuntimeError("nenhuma sub-rede pública encontrada; crie a rede pelo painel")
    subnet = sorted(subnets, key=lambda s: s.time_created)[0]

    imagens = compute.list_images(
        comp, operating_system="Canonical Ubuntu", operating_system_version="24.04",
        shape=SHAPE, sort_by="TIMECREATED", sort_order="DESC").data
    imagens = [i for i in imagens if "Minimal" not in i.display_name]
    if not imagens:
        raise RuntimeError(f"imagem Ubuntu 24.04 para {SHAPE} não encontrada")

    with open(CHAVE_SSH, encoding="utf-8") as f:
        chave = f.read().strip()

    return config, comp, compute, rede, ad, subnet, imagens[0], chave


def ja_existe(compute, comp):
    for i in compute.list_instances(comp, display_name=NOME).data:
        if i.lifecycle_state not in ("TERMINATED", "TERMINATING"):
            return i
    return None


def ip_publico(compute, rede, comp, instancia_id):
    for a in compute.list_vnic_attachments(comp, instance_id=instancia_id).data:
        v = rede.get_vnic(a.vnic_id).data
        if v.public_ip:
            return v.public_ip
    return None


def esperar_e_gravar(compute, rede, comp, inst):
    log(f"máquina criada ({inst.id[-12:]}), esperando ficar RUNNING...")
    oci.wait_until(compute, compute.get_instance(inst.id), "lifecycle_state", "RUNNING",
                   max_wait_seconds=900)
    ip = None
    for _ in range(30):
        ip = ip_publico(compute, rede, comp, inst.id)
        if ip:
            break
        time.sleep(10)
    log(f"PRONTO. IP público: {ip}")
    with open(RESULTADO, "w", encoding="utf-8") as f:
        f.write(f"{ip}\n{inst.id}\n{datetime.now():%d/%m/%Y %H:%M}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checar", action="store_true")
    ap.add_argument("--micro", action="store_true")
    a = ap.parse_args()
    if a.micro:
        modo_micro()
    os.makedirs(PASTA, exist_ok=True)

    config, comp, compute, rede, ad, subnet, imagem, chave = preparar()
    log(f"região {config['region']} | AD {ad} | sub-rede {subnet.display_name} | "
        f"imagem {imagem.display_name}")
    existente = ja_existe(compute, comp)
    if existente:
        log(f"já existe '{NOME}' ({existente.lifecycle_state}); não crio outra.")
        if existente.lifecycle_state in ("PROVISIONING", "STARTING", "RUNNING"):
            esperar_e_gravar(compute, rede, comp, existente)
        return
    if a.checar:
        log("config ok; nada criado (--checar).")
        return

    inicio = time.time()
    rodada = 0
    while time.time() - inicio < DURACAO_MAX:
        rodada += 1
        for tam in TAMANHOS:
            config_shape = None
            if tam:
                config_shape = oci.core.models.LaunchInstanceShapeConfigDetails(
                    ocpus=tam[0], memory_in_gbs=tam[1])
            detalhes = oci.core.models.LaunchInstanceDetails(
                availability_domain=ad, compartment_id=comp, display_name=NOME, shape=SHAPE,
                shape_config=config_shape,
                source_details=oci.core.models.InstanceSourceViaImageDetails(
                    image_id=imagem.id, boot_volume_size_in_gbs=50),
                create_vnic_details=oci.core.models.CreateVnicDetails(
                    subnet_id=subnet.id, assign_public_ip=True),
                metadata={"ssh_authorized_keys": chave})
            try:
                inst = compute.launch_instance(detalhes).data
                log(f"rodada {rodada}: CONSEGUIU ({SHAPE} {tam or ''})")
                esperar_e_gravar(compute, rede, comp, inst)
                return
            except oci.exceptions.ServiceError as e:
                if e.status == 500 and "capacity" in (e.message or "").lower():
                    continue
                if e.status == 429:
                    log(f"rodada {rodada}: muitas requisições; esperando 5 min")
                    time.sleep(300)
                    break
                log(f"rodada {rodada}: erro {e.status} {e.code}: {e.message}")
                if e.status in (400, 401, 404):
                    raise
        if rodada % 15 == 1:
            log(f"rodada {rodada}: sem vaga ainda ({SHAPE} {TAMANHOS} a cada {INTERVALO}s)")
        time.sleep(INTERVALO)
    log("desisti depois de 7 dias sem vaga.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"PAROU: {type(e).__name__}: {e}")
        sys.exit(1)
