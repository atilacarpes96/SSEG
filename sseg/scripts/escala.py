#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
escala.py — horas de cada analista por dia, tiradas da planilha "Escala Análise", para a meta
da semana do SSEG.exe (2 PPCI por período de 6 horas).

A planilha tem uma aba por mês ("Outubro26"). Em cada aba, a primeira tabela tem as HORAS de cada
analista por dia (nome na coluna B, dias a partir da D) e, logo abaixo, uma linha com as datas
(número de série do Excel); a tabela de códigos (M, T, SV, F, FER...) vem depois e não é usada:
as horas já dizem quanto cada código vale, e férias, folga e licença ficam com 0.

Roda no servidor, sobre o xlsx que a rotina do Painel do Dia baixou (download_file_content), e
grava ~/sseg-escala/escala.json fora do repositório (tem nome de militar; não vai ao GitHub).
O SSEG.exe busca esse arquivo pelo SSH.

USO
  python3 escala.py [arquivo do download ...] [--saida ~/sseg-escala/escala.json] [--dias 45]
  Quem está em ~/sseg-escala/fora.txt (um nome por linha) não entra no escala.json, mesmo que
  ainda apareça numa aba da planilha.
"""

import argparse
import datetime
import io
import json
import math
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from distribuicao import M, R, _norm, achar_arquivos, linhas_da_aba  # noqa: E402 — o mesmo leitor de xlsx

TITULO = "Escala Análise"
SAIDA = "~/sseg-escala/escala.json"
FORA = "~/sseg-escala/fora.txt"  # quem saiu da análise: um nome por linha, como na escala (fora do Git)
HORAS_POR_PERIODO = 6
ABA_MES = re.compile(r"^[A-ZÇ]+\d{2}$")  # OUTUBRO26, MARCO26 (já sem acento)


def abas(xlsx_bytes):
    z = zipfile.ZipFile(io.BytesIO(xlsx_bytes))
    return [s.get("name") for s in ET.fromstring(z.read("xl/workbook.xml")).find(M + "sheets")]


def _data(v):
    v = str(v or "").strip()
    if re.fullmatch(r"\d{5}(\.0+)?", v):
        return datetime.date(1899, 12, 30) + datetime.timedelta(days=int(float(v)))
    return None


def _num(v):
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return 0.0


def horas_da_aba(linhas):
    """{nome: {AAAA-MM-DD: horas}} da tabela de horas (a que fica acima da linha de datas)."""
    i_datas = next((i for i, l in enumerate(linhas) if sum(1 for v in l[3:] if _data(v)) >= 20), None)
    if i_datas is None:
        return {}
    datas = {j: _data(v) for j, v in enumerate(linhas[i_datas]) if j >= 3 and _data(v)}
    out = {}
    for l in linhas[:i_datas]:
        nome = re.sub(r"\s+", " ", str(l[1] if len(l) > 1 else "")).strip()
        if not nome or _norm(nome) in ("ANO", "MES"):
            continue
        dias = {datas[j].isoformat(): _num(l[j]) for j in datas if j < len(l) and _num(l[j]) > 0}
        out.setdefault(nome, {}).update(dias)
    return out


def ler(xlsx_bytes, hoje=None, dias=45):
    """Todas as abas de mês; guarda só de `dias` antes a `dias` depois de hoje."""
    hoje = hoje or datetime.date.today()
    ini, fim = (hoje - datetime.timedelta(days=dias)).isoformat(), (hoje + datetime.timedelta(days=dias)).isoformat()
    horas = {}
    for aba in abas(xlsx_bytes):
        if not ABA_MES.match(_norm(aba)):
            continue
        for nome, d in horas_da_aba(linhas_da_aba(xlsx_bytes, _norm(aba))).items():
            horas.setdefault(nome, {}).update({k: v for k, v in d.items() if ini <= k <= fim})
    return {k: dict(sorted(v.items())) for k, v in sorted(horas.items())}


def meta_da_semana(horas_dia, segunda, ppci_por_periodo=2):
    """Horas de segunda a domingo → períodos de 6 h (arredonda meio para cima) → meta em PPCI."""
    dias = [(segunda + datetime.timedelta(days=i)).isoformat() for i in range(7)]
    h = sum(float((horas_dia or {}).get(d, 0)) for d in dias)
    periodos = math.floor(h / HORAS_POR_PERIODO + 0.5)
    return {"horas": h, "periodos": periodos, "meta": periodos * ppci_por_periodo}


def xlsx_do_download(arquivo):
    import base64
    with open(arquivo, encoding="utf-8") as fh:
        d = json.load(fh)
    if "spreadsheetml" not in (d.get("mimeType") or "") or _norm(d.get("title")) != _norm(TITULO):
        return None
    return base64.b64decode(d["content"])


def ler_fora(caminho=FORA):
    try:
        with open(os.path.expanduser(caminho), encoding="utf-8") as fh:
            return {_norm(l) for l in fh if l.strip() and not l.lstrip().startswith("#")}
    except OSError:
        return set()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("arquivos", nargs="*", help="JSON do download_file_content ou .xlsx")
    ap.add_argument("--saida", default=SAIDA)
    ap.add_argument("--dias", type=int, default=45)
    ap.add_argument("--fora", default=FORA, help="nomes que não entram (um por linha)")
    a = ap.parse_args(argv)
    fora = ler_fora(a.fora)
    for f in a.arquivos or achar_arquivos():
        x = open(f, "rb").read() if f.endswith(".xlsx") else xlsx_do_download(f)
        if x is None:
            continue
        horas = {n: h for n, h in ler(x, dias=a.dias).items() if _norm(n) not in fora}
        saida = os.path.expanduser(a.saida)
        os.makedirs(os.path.dirname(saida), exist_ok=True)
        tmp = saida + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"gerado": datetime.datetime.now().isoformat(timespec="seconds"), "fonte": TITULO, "horas": horas},
                      fh, ensure_ascii=False)
        os.replace(tmp, saida)
        print("escala: %d analista(s), %d dia(s) com turno" % (len(horas), sum(len(v) for v in horas.values())))
        return 0
    print("escala: planilha %s não veio no download" % TITULO)
    return 0


if __name__ == "__main__":
    sys.exit(main())
