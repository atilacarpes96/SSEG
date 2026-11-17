#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
resumo_ia.py — resumo curto, por processo, do que os scripts e a IA local já conferiram antes de o analista abrir o
processo (17/11/2026, pedido do Átila). Fica em <pasta>/resumo-ia.md, ao lado da pré-análise; o SSEG.exe manda junto no
passo 2 e o Claude separa: o que pede decisão do analista vira pergunta amarela; palpite de exigência vai no quadro azul.

Lê só o que já está na pasta (não roda IA nem SOL):
  documentos-ia.md   conferência dos documentos dos envolvidos (fatos ✗/? e o palpite das exigências documentais)
  camadas.txt        achados das camadas das pranchas × campo 4
  palpites.json      rótulo dos palpites da IA local sobre as exigências da última CIA

  python3 resumo_ia.py <pasta do processo> [...]
"""
import json
import os
import re
import sys


def _ler(arq):
    try:
        with open(arq, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def documentos(pasta):
    """[(documento, linha)] com o que diverge ou ficou em dúvida, e as linhas de palpite das exigências documentais."""
    t = _ler(os.path.join(pasta, "documentos-ia.md"))
    out, doc, exig = [], "", []
    for l in t.splitlines():
        m = re.match(r"### (.+?)(?: \(\d+ pág.*)?$", l)
        if m:
            doc = m.group(1)
            if doc.startswith("Exigência"):
                exig.append(doc)
            continue
        if l.startswith("- ✗") or (l.startswith("- ?") and "assinatura" not in l):
            out.append((doc, re.sub(r"^- [✗?] ", "", l).replace("**", "")))
        elif l.startswith("- IA: **") and exig and doc == exig[-1]:
            out.append((doc, l[2:].replace("**", "")[:300]))
    return out


def camadas(pasta):
    t = _ler(os.path.join(pasta, "camadas.txt"))
    i = t.find("ACHADOS:")
    if i < 0:
        return []
    fim = re.search(r"\n(?:OBSERVA|[A-ZÇÃÕ ]{6,}:)", t[i + 9:])   # as observações fracas ficam fora
    bloco = t[i + 9: i + 9 + fim.start()] if fim else t[i + 9:]
    return [l.strip() for l in re.split(r"\n(?=\[)", bloco) if l.strip()]


def palpites(pasta):
    try:
        d = json.load(open(os.path.join(pasta, "palpites.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for it in d.get("itens") or []:
        r = it.get("rotulo") or {}
        if r:
            out.append("nº %d: %s" % (it["n"], r.get("titulo", "")))
        elif it.get("estado") == "fila":
            out.append("nº %d: na fila da IA local" % it["n"])
    return out


def montar(pasta):
    cod = os.path.basename(os.path.normpath(pasta))
    L = ["# Resumo dos scripts e da IA local — %s" % cod, "",
         "Feito antes de o processo abrir. Fatos dos scripts e palpites da IA local, não conclusão.", ""]
    doc = documentos(pasta)
    L.append("## Documentos dos envolvidos (pergunta AMARELA o que diverge)")
    L += ["- %s: %s" % (d, t) for d, t in doc] or ["- Nada divergente nos documentos conferidos." if _ler(os.path.join(pasta, "documentos-ia.md"))
                                                    else "- Documentos ainda não conferidos."]
    cam = camadas(pasta)
    L += ["", "## Camadas das pranchas (pergunta AMARELA o que pede decisão)"]
    L += ["- " + c for c in cam] or ["- Nenhum achado." if _ler(os.path.join(pasta, "camadas.txt")) else "- Camadas ainda não lidas."]
    pal = palpites(pasta)
    if pal:
        L += ["", "## Palpites das exigências da última CIA (quadro AZUL, nunca pergunta amarela)"] + ["- " + p for p in pal]
    return "\n".join(L) + "\n"


def gravar(pasta):
    t = montar(pasta)
    with open(os.path.join(pasta, "resumo-ia.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(t)
    return t


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for p in sys.argv[1:]:
        print(gravar(p))
