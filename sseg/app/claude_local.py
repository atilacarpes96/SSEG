# -*- coding: utf-8 -*-
"""
claude_local.py — "Iniciar conversa" e "Subagentes" do SSEG.exe (itens 5 e 6 do PLANO.md).

Nada aqui decide modelo: tudo vem de sseg/workflow/fluxos.json, gerado pelo painel.py a partir
da política de modelo (a mesma fonte do Painel SSEG). Subagentes são lidos de .claude/agents/.
Um programa de fora não comanda subagente no meio da conversa: quem chama é a conversa
principal. Aqui se mostra quem existe, com que modelo, e quais cada tipo de demanda usa.
"""

import glob
import json
import os
import re
import subprocess
import tempfile

NOVA_JANELA = 0x00000010 if os.name == "nt" else 0
CODIGO = re.compile(r"^A\d{8}[A-Z]{2}\d{3}$")
ATALHOS = {"haiku": "aponta para o Haiku 4.5, não o 5.5", "sonnet": "atalho sem versão",
           "opus": "atalho sem versão", "inherit": "herda o modelo da conversa"}


def ler_fluxos(clone):
    with open(os.path.join(clone, "sseg", "workflow", "fluxos.json"), encoding="utf-8") as fh:
        return json.load(fh)["lista"]


def montar_prompt(fluxo, codigo=""):
    if fluxo["pede_codigo"]:
        codigo = codigo.strip().upper()
        if not CODIGO.match(codigo):
            raise ValueError("Código de processo no formato A00012345AA001.")
        return fluxo["prompt"].replace("{codigo}", codigo)
    return fluxo["prompt"]


def comando(fluxo, prompt, claude):
    """A linha que abre a conversa no terminal — também mostrada ao analista."""
    return [claude, "--model", fluxo["modelo"], "--effort", fluxo["esforco"]] + ([prompt] if prompt else [])


def iniciar(clone, fluxo, prompt, claude):
    """Abre o Claude Code numa janela própria, na pasta do SSEG. O prompt vai por arquivo para o
    PowerShell não quebrar acento nem aspas."""
    arq = os.path.join(tempfile.gettempdir(), "sseg-prompt.txt")
    with open(arq, "w", encoding="utf-8") as fh:
        fh.write(prompt)
    ps = ("$p = Get-Content -Raw -Encoding UTF8 '%s'; & '%s' --model %s --effort %s %s"
          % (arq.replace("'", "''"), claude.replace("'", "''"), fluxo["modelo"], fluxo["esforco"],
             "$p" if prompt else ""))
    subprocess.Popen(["powershell", "-NoExit", "-NoProfile", "-Command", ps], cwd=clone, creationflags=NOVA_JANELA)


def _frontmatter(texto):
    m = re.match(r"^---\s*\n(.*?)\n---", texto, re.S)
    fm = {}
    for linha in (m.group(1) if m else "").splitlines():
        if ":" in linha:
            k, v = linha.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm


def subagentes(clone, fluxos=None):
    """[{nome, modelo, descricao, aviso, usado_em}]."""
    usado = {}
    for f in fluxos or []:
        for s in f["subagentes"]:
            usado.setdefault(s, []).append(f["titulo"])
    out = []
    for arq in sorted(glob.glob(os.path.join(clone, ".claude", "agents", "*.md"))):
        fm = _frontmatter(open(arq, encoding="utf-8", errors="replace").read())
        nome = fm.get("name") or os.path.splitext(os.path.basename(arq))[0]
        modelo = fm.get("model", "inherit")
        aviso = ATALHOS.get(modelo.lower())
        if not aviso and not re.match(r"^claude-(haiku|sonnet|opus|fable)-\d", modelo):
            aviso = "nome de modelo desconhecido"
        out.append({"nome": nome, "modelo": modelo, "descricao": fm.get("description", ""),
                    "aviso": aviso, "usado_em": usado.get(nome, [])})
    return out
