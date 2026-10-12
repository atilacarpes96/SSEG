# -*- coding: utf-8 -*-
"""
processo.py — monta a janela do processo (SSEG.exe 2.1): checklist do fluxo, medidas do SOL com
os itens do Anexo L e o registro analise.json. Só lê a pasta do processo; não chama o Claude
(abrir o processo não dispara nada — decisão do Átila, 12/10/2026).

Fontes únicas, no clone: sseg/workflow/checklist-analise.json (os 16 passos),
sseg/workflow/anexo-l.json (RT 05 Parte 1.1, Anexo L) e o JSON da API do SOL na pasta do processo.
"""

import glob
import json
import os
import re
import sys
import unicodedata


def _registro(clone):
    """analise_registro.py mora em sseg/scripts (o sseg.py usa o mesmo); no .exe, vem empacotado."""
    try:
        import analise_registro
    except ImportError:
        sys.path.insert(0, os.path.join(clone, "sseg", "scripts"))
        import analise_registro
    return analise_registro


def _norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _ler_json(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return json.load(fh)


def json_do_sol(pasta):
    """O JSON da API com especSeguranca (api-<id>.json ou <N>.json), o mais novo."""
    candidatos = sorted(glob.glob(os.path.join(pasta, "*.json")), key=os.path.getmtime, reverse=True)
    for c in candidatos:
        if os.path.basename(c) == "analise.json" or os.path.basename(c).startswith("."):
            continue
        try:
            d = _ler_json(c)
        except (OSError, ValueError):
            continue
        if isinstance(d, dict) and isinstance(d.get("especSeguranca"), dict):
            return c, d
    return None, None


def itens_da_medida(nome, anexo):
    """Memorial sempre; os itens de planta da L.1 (coluna "A") quando a medida é da L.1."""
    n = _norm(nome)
    itens = [anexo["memorial"]]
    tabela = "L.2"
    for linha in sorted(anexo["l1"], key=lambda x: -len(x["chave"])):  # "hidrante urbano" antes de "hidrantes"
        if _norm(linha["chave"]) in n:
            itens += ["Planta: " + i for i in linha["planta"]]
            tabela = "L.1"
            break
    nota = next((t for k, t in anexo.get("notas", {}).items() if k in n), "")
    return tabela, itens, nota


def montar(clone, pasta):
    reg = _registro(clone)
    wf = os.path.join(clone, "sseg", "workflow")
    passos = _ler_json(os.path.join(wf, "checklist-analise.json"))["passos"]
    anexo = _ler_json(os.path.join(wf, "anexo-l.json"))
    arq, sol = json_do_sol(pasta)
    medidas, laudo = [], ""
    if sol:
        esp = sol["especSeguranca"]
        laudo = ((esp.get("laudo") or {}).get("txtClob") or "").strip()
        for m in esp.get("medidas") or []:  # na ordem do SOL
            nome = ((m.get("tipo") or {}).get("nome") or "").strip() or "(medida sem nome)"
            tabela, itens, nota = itens_da_medida(nome, anexo)
            inv = m.get("inviabilidade") or "NAO_POSSUI"
            if inv != "NAO_POSSUI":
                itens.append("Compensatórias do laudo representadas em planta")
            medidas.append({"nome": nome, "norma": re.sub(r"\s+", " ", ((m.get("norma") or {}).get("nome") or "")).strip(),
                            "inviabilidade": inv, "tabela": tabela, "itens": itens, "nota": nota})
    arquivos = sorted(os.listdir(pasta)) if os.path.isdir(pasta) else []
    return {"codigo": os.path.basename(os.path.normpath(pasta)), "pasta": pasta, "json_sol": arq and os.path.basename(arq),
            "passos": passos, "medidas": medidas, "laudo": laudo, "compensatoria": anexo.get("compensatoria", ""),
            "cias": [a for a in arquivos if re.match(r"CIA \d+", a)], "analise": reg.ler(pasta)}
