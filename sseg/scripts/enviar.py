#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enviar.py — leva a pasta do processo do PC do trabalho para o servidor, sem as plantas.

As plantas baixas servem só na hora da análise e o SOL guarda o original: não saem do PC.
Vai o que deixa continuar o processo de qualquer lugar (casa, celular, conversa no servidor):
os JSON (API do SOL, registro de trabalho, textos da CIA), <N>.pdf, CIA <N>.pdf, memorial e
o registro processos/<código>.md do clone, se existir.

A regra é uma lista do que PODE ir (ENVIA); o resto fica. Arquivo novo de nome estranho
fica no PC e aparece no resumo — nunca vai por engano.

Transporte: ssh/scp do OpenSSH (vem no Windows 10/11). Destino no servidor:
~/SSEG/sseg/processos/<código>/ (fora do Git). Os dados não passam pelo GitHub.
Servidor: --servidor, ou a variável SSEG_SERVIDOR, ou o apelido "sseg-servidor" do
~/.ssh/config do PC.

USO
  python sseg.py enviar --pasta "<print ppci>\\<processo>" [--simular]
"""

import os
import re
import subprocess

ENVIA = [r"\.json$", r"\.md$", r"\.txt$", r"^\d+\.pdf$", r"^CIA \d+.*\.pdf$", r"memorial.*\.pdf$"]
DESTINO = "SSEG/sseg/processos"


def selecionar(nomes):
    """Separa (vai, fica) pela lista ENVIA."""
    vai, fica = [], []
    for n in sorted(nomes):
        (vai if any(re.search(p, n, re.I) for p in ENVIA) else fica).append(n)
    return vai, fica


def enviar(pasta, processo=None, servidor=None, simular=False):
    pasta = os.path.abspath(pasta)
    if not os.path.isdir(pasta):
        raise SystemExit("pasta não encontrada: %s" % pasta)
    processo = processo or os.path.basename(pasta.rstrip("\\/"))
    if not re.fullmatch(r"[A-Za-z0-9_-]+", processo):
        raise SystemExit("código de processo inválido: %r (use --processo)" % processo)
    servidor = servidor or os.environ.get("SSEG_SERVIDOR") or "sseg-servidor"

    nomes = [n for n in os.listdir(pasta) if os.path.isfile(os.path.join(pasta, n))]
    vai, fica = selecionar(nomes)
    registro = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "processos", processo + ".md"))

    print("%s → %s:~/%s/%s/" % (processo, servidor, DESTINO, processo))
    print("  vai (%d): %s" % (len(vai), ", ".join(vai) or "nada"))
    if fica:
        print("  fica no PC (%d): %s" % (len(fica), ", ".join(fica)))
    if os.path.exists(registro):
        print("  registro: processos/%s.md" % processo)
    if simular or not (vai or os.path.exists(registro)):
        print("  (simulação, nada enviado)" if simular else "  nada a enviar")
        return

    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15"]
    scp = ["scp", "-q", "-p", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15"]
    try:
        subprocess.run(ssh + [servidor, "mkdir -p %s/%s" % (DESTINO, processo)], check=True)
        if vai:
            subprocess.run(scp + [os.path.join(pasta, n) for n in vai]
                           + ["%s:%s/%s/" % (servidor, DESTINO, processo)], check=True)
        if os.path.exists(registro):
            subprocess.run(scp + [registro, "%s:%s/" % (servidor, DESTINO)], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise SystemExit("  NÃO enviado (%s). Conferir: `ssh %s echo ok` no PowerShell — chave SSH "
                         "autorizada no servidor e rede liberando SSH de saída. A pasta no PC está intacta."
                         % (e.__class__.__name__, servidor))
    print("  enviado.")


def args_parser(sp):
    sp.add_argument("--pasta", required=True, help="pasta do processo em print ppci")
    sp.add_argument("--processo", help="código, se a pasta não tiver o nome do processo")
    sp.add_argument("--servidor", help="host ssh (padrão: SSEG_SERVIDOR ou sseg-servidor)")
    sp.add_argument("--simular", action="store_true", help="só mostra o que iria")
