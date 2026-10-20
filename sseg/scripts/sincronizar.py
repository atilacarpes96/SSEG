#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sincronizar.py — processos entre o PC e o servidor, nos dois sentidos, por SSH. Nada passa
pelo GitHub.

Sobe o que mudou no PC (como o `enviar`, em todos os processos) e desce o que está mais novo no
servidor: memorial, JSON, CIA e o registro processos/<código>.md. Vale a mesma lista do
`enviar.py` (ENVIA): planta nunca vai, e nunca vem.

COMO DECIDE (por arquivo, comparando com a última sincronização, guardada em
sseg/processos/.sincronizacao.json no clone do PC):
  - só o PC mudou ........... sobe
  - só o servidor mudou ..... desce
  - os dois mudaram ......... CONFLITO: não sobrescreve; o analista escolhe (PC, servidor ou deixar)
  - apagado de um lado ...... não apaga do outro (apagar não se propaga)

O mesmo arquivo roda nos dois lados: no PC (comandos abaixo) e no servidor, chamado pelo SSH
com `remoto-listar`, `remoto-receber` e `remoto-entregar` — os arquivos vão num pacote tar
pelo próprio SSH, sem nome de arquivo na linha de comando.

USO (no PC)
  python sseg.py sincronizar --pasta "<print ppci>" [--simular] [--json] [--escolhas escolhas.json]
  python sseg.py trazer      --pasta "<print ppci>"     # só desce
"""

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import enviar  # noqa: E402 — a lista do que pode sair do PC é uma só

CODIGO = re.compile(r"^A\d{8}[A-Z]{2}\d{3}$")
PROC_CLONE = os.path.normpath(os.path.join(AQUI, "..", "processos"))  # registro <código>.md e a base
BASE = os.path.join(PROC_CLONE, ".sincronizacao.json")
SCRIPT_REMOTO = "SSEG/sseg/scripts/porta.py"  # a porta filtra pelo analista da chave (2.2.0)
SEM_JANELA = 0x08000000 if os.name == "nt" else 0

FALTA_SSH = """Falta a ligação com o servidor neste PC ({motivo}).
No SSEG.exe: Configuração → Servidor → "Pedir acesso", mande o código ao administrador e,
quando ele liberar, "Testar conexão"."""


# --------------------------------------------------------------------- comum aos dois lados

def chave_valida(k):
    """'<código>/<arquivo da lista>' ou '<código>.md' (registro). Barra caminho fora da pasta."""
    if "/" in k:
        cod, nome = k.split("/", 1)
        return (bool(CODIGO.match(cod)) and nome not in ("", ".", "..") and not re.search(r"[\\/:]", nome)
                and enviar.selecionar([nome])[0] == [nome])
    return k.endswith(".md") and bool(CODIGO.match(k[:-3]))


def _sha(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as fh:
        for bloco in iter(lambda: fh.read(1 << 16), b""):
            h.update(bloco)
    return h.hexdigest()


def manifesto(raiz_codigos, raiz_registro):
    """{chave: sha256}. Processos em <raiz_codigos>/<código>/, registros em <raiz_registro>/<código>.md."""
    m = {}
    if os.path.isdir(raiz_codigos):
        for cod in os.listdir(raiz_codigos):
            d = os.path.join(raiz_codigos, cod)
            if CODIGO.match(cod) and os.path.isdir(d):
                for n in os.listdir(d):
                    k = cod + "/" + n
                    if os.path.isfile(os.path.join(d, n)) and chave_valida(k):
                        m[k] = _sha(os.path.join(d, n))
    if os.path.isdir(raiz_registro):
        for n in os.listdir(raiz_registro):
            if os.path.isfile(os.path.join(raiz_registro, n)) and chave_valida(n):
                m[n] = _sha(os.path.join(raiz_registro, n))
    return m


def empacotar(arquivos):
    """{chave: caminho} → bytes de um tar."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for k, caminho in sorted(arquivos.items()):
            tar.add(caminho, arcname=k, recursive=False)
    return buf.getvalue()


def desempacotar(dados, destino_de):
    """Grava cada arquivo do tar em destino_de(chave). Chave inválida, ou destino None, é ignorada. Devolve as gravadas."""
    feitas = []
    with tarfile.open(fileobj=io.BytesIO(dados), mode="r") as tar:
        for mb in tar.getmembers():
            if not mb.isfile() or not chave_valida(mb.name):
                continue
            alvo = destino_de(mb.name)
            if not alvo:  # a porta do servidor recusa o que não é do analista
                continue
            os.makedirs(os.path.dirname(alvo), exist_ok=True)
            tmp = alvo + ".sseg-tmp"
            with tar.extractfile(mb) as src, open(tmp, "wb") as dst:
                dst.write(src.read())
            os.replace(tmp, alvo)
            os.utime(alvo, (mb.mtime, mb.mtime))
            feitas.append(mb.name)
    return feitas


# ------------------------------------------------------------------- lado do servidor

RAIZ_SERVIDOR = PROC_CLONE  # no servidor, ~/SSEG/sseg/processos guarda as duas coisas


def _no_servidor(k):
    return os.path.join(RAIZ_SERVIDOR, *k.split("/"))


def remoto(acao):
    if acao == "remoto-listar":
        sys.stdout.write(json.dumps(manifesto(RAIZ_SERVIDOR, RAIZ_SERVIDOR)))
    elif acao == "remoto-receber":
        print(json.dumps(desempacotar(sys.stdin.buffer.read(), _no_servidor)))
    elif acao == "remoto-entregar":
        pedidas = [k for k in json.loads(sys.stdin.read()) if chave_valida(k) and os.path.isfile(_no_servidor(k))]
        sys.stdout.buffer.write(empacotar({k: _no_servidor(k) for k in pedidas}))


# ------------------------------------------------------------------------ lado do PC

class Servidor:
    """Transporte por SSH. O teste troca por um que chama `remoto` direto numa pasta."""

    def __init__(self, host):
        self.host = host

    def _ssh(self, acao, entrada=b""):
        p = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", self.host,
                            "python3 %s %s" % (SCRIPT_REMOTO, acao)], input=entrada, capture_output=True,
                           timeout=600, creationflags=SEM_JANELA)
        if p.returncode == 255:
            raise RuntimeError(FALTA_SSH.format(motivo="o servidor não aceitou a conexão: "
                                                + p.stderr.decode("utf-8", "replace").strip()[-160:]))
        if p.returncode and SCRIPT_REMOTO.endswith("porta.py") and b"No such file" in p.stderr:
            return self._ssh_antigo(acao, entrada)  # servidor ainda sem a porta (antes do git pull de lá)
        if p.returncode:
            raise RuntimeError("Erro no servidor: " + p.stderr.decode("utf-8", "replace").strip()[-400:])
        return p.stdout

    def _ssh_antigo(self, acao, entrada):
        p = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", self.host,
                            "python3 SSEG/sseg/scripts/sincronizar.py " + acao], input=entrada, capture_output=True,
                           timeout=600, creationflags=SEM_JANELA)
        if p.returncode:
            raise RuntimeError("Erro no servidor: " + p.stderr.decode("utf-8", "replace").strip()[-400:])
        return p.stdout

    def listar(self):
        return json.loads(self._ssh("remoto-listar") or b"{}")

    def receber(self, dados):
        return json.loads(self._ssh("remoto-receber", dados) or b"[]")

    def entregar(self, chaves):
        return self._ssh("remoto-entregar", json.dumps(chaves).encode("utf-8"))


def conferir_ssh(host):
    """Mensagem do que falta, ou None. Só olha o PC (não conecta)."""
    if host != "sseg-servidor":
        return None
    cfg = os.path.join(os.path.expanduser("~"), ".ssh", "config")
    try:
        texto = open(cfg, encoding="utf-8", errors="replace").read()
    except OSError:
        return FALTA_SSH.format(motivo="não há ~/.ssh/config")
    if not re.search(r"^\s*Host\s+(.*\s)?sseg-servidor(\s|$)", texto, re.M | re.I):
        return FALTA_SSH.format(motivo="o apelido sseg-servidor não está em ~/.ssh/config")
    return None


def _ler_base():
    try:
        with open(BASE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _gravar_base(base):
    os.makedirs(os.path.dirname(BASE), exist_ok=True)
    with open(BASE, "w", encoding="utf-8") as fh:
        json.dump(base, fh, ensure_ascii=False, indent=1, sort_keys=True)


# Arquivos que ninguém edita à mão: saem do SOL, da planilha ou de script (2.6.3). Mudou dos dois lados = duas
# leituras do mesmo SOL; vale a do servidor, sem perguntar. Antes isso virava conflito, e o conflito segurava o
# Atualizar inteiro (nada descia até o analista escolher).
GERADO = re.compile(r"^(sol-caixa|marcos|marcos-resumo|historico|facts|pre-analise|distribuicao|ct|recurso)\.(json|txt)$"
                    r"|^(anterior-)?api-\d+\.json$|^cia-(\d+|ultima)\.(pdf|txt)$|^memorial SOL \d+\.(pdf|txt)$|^licenciamento \d+\.json$")


def gerado(k):
    return bool(GERADO.match(k.rsplit("/", 1)[-1]))


def comparar(local, remoto_m, base):
    """Plano de três vias: {sobe, desce, conflito, apagado_pc, apagado_servidor, iguais}."""
    p = {"sobe": [], "desce": [], "conflito": [], "apagado_pc": [], "apagado_servidor": [], "iguais": 0}
    for k in sorted(set(local) | set(remoto_m)):
        L, R, B = local.get(k), remoto_m.get(k), base.get(k)
        if L == R:
            p["iguais"] += 1
        elif L is None:
            p["apagado_pc" if R == B else "desce"].append(k)
        elif R is None:
            p["apagado_servidor" if L == B else "sobe"].append(k)
        elif R == B:
            p["sobe"].append(k)
        elif L == B or gerado(k):
            p["desce"].append(k)
        else:
            p["conflito"].append(k)
    return p


def _no_pc(pasta_ppci):
    def caminho(k):
        if "/" in k:
            cod, nome = k.split("/", 1)
            return os.path.join(pasta_ppci, cod, nome)
        return os.path.join(PROC_CLONE, k)
    return caminho


def planejar(pasta_ppci, servidor):
    local = manifesto(pasta_ppci, PROC_CLONE)
    plano = comparar(local, servidor.listar(), _ler_base())
    return plano


def aplicar(pasta_ppci, servidor, escolhas=None, so_descer=False):
    """Executa o plano. escolhas = {chave em conflito: 'pc' | 'servidor' | 'deixar'}."""
    escolhas = escolhas or {}
    base = _ler_base()
    local = manifesto(pasta_ppci, PROC_CLONE)
    plano = comparar(local, servidor.listar(), base)
    no_pc = _no_pc(pasta_ppci)
    sobe = [] if so_descer else plano["sobe"] + [k for k in plano["conflito"] if escolhas.get(k) == "pc"]
    desce = plano["desce"] + [k for k in plano["conflito"] if escolhas.get(k) == "servidor"]
    if sobe:
        servidor.receber(empacotar({k: no_pc(k) for k in sobe}))
    if desce:
        desempacotar(servidor.entregar(desce), no_pc)
    # nova base: o que ficou igual dos dois lados; apagado de um lado mantém a referência antiga
    local, remoto_m = manifesto(pasta_ppci, PROC_CLONE), servidor.listar()
    nova = {k: v for k, v in local.items() if remoto_m.get(k) == v}
    for k in plano["apagado_pc"] + plano["apagado_servidor"]:
        if k in base:
            nova[k] = base[k]
    _gravar_base(nova)
    resto = [k for k in plano["conflito"] if escolhas.get(k) not in ("pc", "servidor")]
    return {"subiu": sobe, "desceu": desce, "conflito_pendente": resto}


def texto_plano(p):
    linhas = ["sobe para o servidor: %d · desce para o PC: %d · iguais: %d"
              % (len(p["sobe"]), len(p["desce"]), p["iguais"])]
    for rot, ch in (("sobe", "sobe"), ("desce", "desce"), ("CONFLITO (mudou dos dois lados)", "conflito")):
        for k in p[ch]:
            linhas.append("  %s  %s" % (rot, k))
    if p["apagado_pc"]:
        linhas.append("  apagado no PC, fica no servidor: " + ", ".join(p["apagado_pc"]))
    return "\n".join(linhas)


def args_parser(sp_sinc, sp_trazer):
    for sp in (sp_sinc, sp_trazer):
        sp.add_argument("--pasta", help="pasta print ppci (padrão: a de sseg/processos/local.json)")
        sp.add_argument("--servidor", help="host ssh (padrão: SSEG_SERVIDOR ou sseg-servidor)")
    sp_sinc.add_argument("--simular", action="store_true", help="só mostra o plano")
    sp_sinc.add_argument("--json", action="store_true", help="plano em JSON (para o SSEG.exe)")
    sp_sinc.add_argument("--escolhas", help="JSON {chave: pc|servidor|deixar} para os conflitos")


def principal(args, so_descer=False):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    pasta = args.pasta
    if not pasta:
        try:
            pasta = json.load(open(os.path.join(PROC_CLONE, "local.json"), encoding="utf-8"))["print_ppci"]
        except (OSError, ValueError, KeyError):
            raise SystemExit("Informe --pasta (a pasta print ppci) ou rode \"Criar / conferir pastas\" no programa SSEG.")
    host = args.servidor or os.environ.get("SSEG_SERVIDOR") or "sseg-servidor"
    falta = conferir_ssh(host)
    if falta:
        raise SystemExit(falta)
    srv = Servidor(host)
    try:
        if getattr(args, "simular", False) or getattr(args, "json", False):
            p = planejar(pasta, srv)
            print(json.dumps(p, ensure_ascii=False) if args.json else texto_plano(p))
            return
        escolhas = json.load(open(args.escolhas, encoding="utf-8")) if getattr(args, "escolhas", None) else {}
        r = aplicar(pasta, srv, escolhas, so_descer)
    except RuntimeError as e:
        raise SystemExit(str(e))
    print("subiu %d, desceu %d" % (len(r["subiu"]), len(r["desceu"])))
    for k in r["desceu"]:
        print("  ↓ " + k)
    for k in r["subiu"]:
        print("  ↑ " + k)
    if r["conflito_pendente"]:
        print("conflito sem escolha (nada sobrescrito): " + ", ".join(r["conflito_pendente"]))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].startswith("remoto-"):
        remoto(sys.argv[1])
