# -*- coding: utf-8 -*-
"""
acesso.py — ligação deste PC com o servidor do SSEG (multiusuário, 2.2.0).

Analista novo:
  1. "Pedir acesso" cria a chave ~/.ssh/sseg_servidor (sem senha), põe o apelido sseg-servidor no
     ~/.ssh/config e monta o código de acesso: uma linha com o nome e a chave PÚBLICA. A chave
     privada nunca sai do PC.
  2. O analista manda o código ao administrador (WhatsApp, e-mail).
  3. O administrador cola o código no SSEG.exe dele → `porta.py autorizar` no servidor.
  4. "Testar conexão" → `porta.py quem-sou` diz com que nome o servidor o reconhece.
Tudo que o programa pede ao servidor passa pela porta.py; o analista não tem shell lá.
"""

import json
import os
import re
import shlex
import subprocess

HOST = "sseg-servidor"
ENDERECO = "163.176.190.159"
USUARIO = "ubuntu"
PORTA = "SSEG/sseg/scripts/porta.py"
PREFIXO = "SSEG-ACESSO"
SEM_JANELA = 0x08000000 if os.name == "nt" else 0
VELHO = "O servidor ainda está numa versão do SSEG sem a porta dos analistas: falta atualizar o clone de lá (git pull)."


def _ssh_dir():
    return os.path.join(os.path.expanduser("~"), ".ssh")


def caminho_chave():
    return os.path.join(_ssh_dir(), "sseg_servidor")


def tem_apelido():
    try:
        texto = open(os.path.join(_ssh_dir(), "config"), encoding="utf-8", errors="replace").read()
    except OSError:
        return False
    return bool(re.search(r"^\s*Host\s+(.*\s)?%s(\s|$)" % HOST, texto, re.M | re.I))


def chave_publica():
    try:
        return open(caminho_chave() + ".pub", encoding="utf-8").read().strip()
    except OSError:
        return ""


def preparar():
    """Cria a chave e o apelido, se faltarem. Não mexe no que já existe. Devolve o que fez."""
    feito = []
    os.makedirs(_ssh_dir(), exist_ok=True)
    if not os.path.isfile(caminho_chave()):
        p = subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "sseg", "-f", caminho_chave()],
                           capture_output=True, text=True, timeout=60, creationflags=SEM_JANELA, stdin=subprocess.DEVNULL)
        if p.returncode or not os.path.isfile(caminho_chave() + ".pub"):
            raise RuntimeError("Não consegui criar a chave (ssh-keygen): " + (p.stderr or p.stdout).strip()[-300:]
                               + "\nO OpenSSH vem no Windows 10/11: Configurações → Aplicativos → Recursos opcionais → Cliente OpenSSH.")
        feito.append("chave criada em " + caminho_chave())
    if not tem_apelido():
        cfg = os.path.join(_ssh_dir(), "config")
        try:
            velho = open(cfg, encoding="utf-8", errors="replace").read()
        except OSError:
            velho = ""
        bloco = ("Host %s\n  HostName %s\n  User %s\n  IdentityFile ~/.ssh/sseg_servidor\n"
                 "  IdentitiesOnly yes\n  StrictHostKeyChecking accept-new\n" % (HOST, ENDERECO, USUARIO))
        with open(cfg, "w", encoding="utf-8", newline="\n") as fh:
            fh.write((velho.rstrip("\n") + "\n\n" if velho.strip() else "") + bloco)
        feito.append("apelido %s em %s" % (HOST, cfg))
    return feito


def codigo_acesso(analista):
    """Uma linha para colar no WhatsApp: SSEG-ACESSO|<nome>|<chave pública sem o comentário>."""
    pub = " ".join(chave_publica().split()[:2])
    if not pub:
        raise RuntimeError("Este PC ainda não tem a chave do servidor.")
    return "%s|%s|%s" % (PREFIXO, analista, pub)


def ler_codigo(texto):
    """O código colado (com quebra de linha do WhatsApp no meio, inclusive) → {analista, chave}."""
    t = re.sub(r"\s+", " ", texto or "").strip()
    m = re.search(PREFIXO + r"\s*\|\s*([^|]{2,40}?)\s*\|\s*((?:ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp\d+) ?[A-Za-z0-9+/= ]{40,})", t)
    if not m:
        raise RuntimeError("Isso não parece um código de acesso do SSEG (começa com %s|)." % PREFIXO)
    tipo, _, resto = m.group(2).partition(" ")
    return {"analista": m.group(1).strip(), "chave": tipo + " " + resto.replace(" ", "")}


def chamar(acao, *args, entrada=b"", timeout=30):
    """ssh sseg-servidor python3 porta.py <ação> <args> → bytes. Erro vira RuntimeError em português."""
    remoto = " ".join(["python3", PORTA, acao] + [shlex.quote(str(a)) for a in args])
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", HOST, remoto],
                       input=entrada, capture_output=True, timeout=timeout, creationflags=SEM_JANELA)
    erro = p.stderr.decode("utf-8", "replace").strip()
    if p.returncode == 255:
        if "Permission denied" in erro:
            raise RuntimeError("O servidor ainda não liberou a chave deste PC. Mande o código de acesso ao administrador.")
        raise RuntimeError("Não alcancei o servidor: " + erro[-200:])
    if p.returncode:
        if "porta.py" in erro and "No such file" in erro:
            raise RuntimeError(VELHO)
        raise RuntimeError(erro[-400:] or "erro no servidor")
    return p.stdout


def chamar_json(acao, *args, entrada=b"", timeout=30):
    return json.loads(chamar(acao, *args, entrada=entrada, timeout=timeout) or b"{}")
