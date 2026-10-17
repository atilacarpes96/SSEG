#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sol_senha.py — a senha do SOL para o login automático do servidor (sol_caixa.py, entrar()).

Autorizado pelo Átila em 17/10/2026: ele grava matrícula e senha UMA vez, num terminal do
servidor; quando a sessão do SOL cai, o sol_caixa.py preenche o login do SOE na aba do Chromium
do servidor. Uma tentativa por queda: se falhar, liga a trava e só volta depois de um novo `gravar`.

A senha fica em ~/sseg-acesso/sol-login.json (permissão 600, fora do Git). Nunca passa por
argumento de linha de comando, log, chat ou commit, e este script nunca a imprime. O Claude não
roda o `gravar`: quem digita é o Átila.

USO (no servidor)
---
  python3 ~/SSEG/sseg/scripts/sol_senha.py gravar   # pede matrícula e senha (sem eco)
  python3 ~/SSEG/sseg/scripts/sol_senha.py estado   # gravada? trava ligada? último login automático
  python3 ~/SSEG/sseg/scripts/sol_senha.py apagar   # remove a senha
"""

import argparse
import getpass
import json
import os
import sys

PASTA = os.path.expanduser("~/sseg-acesso")
ARQUIVO = os.path.join(PASTA, "sol-login.json")
TRAVA = os.path.join(PASTA, "sol-login-falhou")
ULTIMO = os.path.join(PASTA, "sol-login-ultimo.txt")


def ler():
    """{"matricula", "senha"} ou None. Só o sol_caixa.py usa."""
    try:
        with open(ARQUIVO, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if d.get("matricula") and d.get("senha") else None
    except (OSError, ValueError):
        return None


def _ler_texto(arq):
    try:
        with open(arq, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def gravar():
    matricula = input("Matrícula do SOL: ").strip()
    senha = getpass.getpass("Senha do SOL (não aparece): ")
    if not matricula or not senha:
        print("Nada gravado: matrícula e senha são obrigatórias.")
        return 1
    if getpass.getpass("Repita a senha: ") != senha:
        print("Nada gravado: as senhas não conferem.")
        return 1
    os.makedirs(PASTA, mode=0o700, exist_ok=True)
    tmp = ARQUIVO + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump({"matricula": matricula, "senha": senha}, fh)
    os.replace(tmp, ARQUIVO)
    if os.path.exists(TRAVA):
        os.remove(TRAVA)
        print("Trava de falha apagada.")
    print("Gravado (matrícula %s). O sol_caixa.py entra sozinho quando a sessão cair." % matricula)
    return 0


def estado():
    d = ler()
    print("Senha: " + ("gravada (matrícula %s)" % d["matricula"] if d else "não gravada"))
    trava = _ler_texto(TRAVA)
    print("Trava: " + ("LIGADA — " + trava + " (rode `gravar` de novo para soltar)" if os.path.exists(TRAVA) else "desligada"))
    print("Último login automático: " + (_ler_texto(ULTIMO) or "nenhum"))
    return 0


def apagar():
    for arq in (ARQUIVO, TRAVA):
        if os.path.exists(arq):
            os.remove(arq)
    print("Senha apagada. O login automático fica desligado.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("acao", choices=["gravar", "estado", "apagar"])
    sys.exit({"gravar": gravar, "estado": estado, "apagar": apagar}[ap.parse_args().acao]())
