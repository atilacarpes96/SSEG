#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
distribuicao.py — a planilha "Distribuição Análise" vira <código>/distribuicao.json (SSEG.exe 2.1.13).

Roda no servidor, dentro da rotina do Painel do Dia (dias úteis, 7h47), logo depois do download da
planilha em xlsx: o download_file_content salva o arquivo em tool-results e este script lê de lá,
sem o modelo abrir a planilha. Só a aba ANÁLISE vale (as abas por analista têm fórmula que não vem
na exportação). Linhas do analista:
  - sem DATA CONCLUSÃO (na fila ou na caixa) ................. cria a pasta do processo, se faltar
  - concluídas nos últimos --dias dias ....................... cria a pasta, se faltar
  - concluídas antes ......................................... só atualiza pasta que já existe
O "Sincronizar processos" do SSEG.exe desce a pasta e o distribuicao.json para o PC.

Só biblioteca padrão (o xlsx é um zip de XML), para rodar no servidor e no testar.py.

USO
  python3 distribuicao.py --pasta ~/SSEG/sseg/processos [--analista "Sd Carpes" ...] [--dias 30] [arquivo ...]
  (sem --analista: TODOS os processos da planilha, de todos os analistas, numa pasta só por código.
  O distribuicao.json de cada um diz o "analista" responsável — com o nome da escala quando dá para
  casar — e guarda em "analistas_anteriores" por quem o processo já passou. A porta.py mostra a
  pasta só ao responsável; o servidor, que vê todas, pode cruzar as notificações de todo mundo.)
  (sem arquivo, procura os downloads da planilha nos últimos 90 min, como o planilhas.py)
"""

import argparse
import base64
import datetime
import glob
import io
import json
import os
import re
import sys
import tempfile
import time
import unicodedata
import zipfile
import xml.etree.ElementTree as ET

CODIGO = re.compile(r"^A\d{8}[A-Z]{2}\d{3}$")
ARQUIVO = "distribuicao.json"
TITULO = "Distribuição Análise"
ABA = "ANALISE"
M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().upper()


def _col(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group():
        n = n * 26 + ord(ch) - 64
    return n - 1


def linhas_da_aba(xlsx_bytes, aba=ABA):
    """Linhas (listas de texto) da aba pedida, sem acento no nome. Número fica como texto do XML."""
    z = zipfile.ZipFile(io.BytesIO(xlsx_bytes))
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        ss = ["".join(t.text or "" for t in si.iter(M + "t")) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(M + "si")]
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    alvo = None
    for s in ET.fromstring(z.read("xl/workbook.xml")).find(M + "sheets"):
        if _norm(s.get("name")) == aba:
            alvo = rels[s.get(R + "id")]
            break
    if not alvo:
        raise ValueError("aba %s não encontrada" % aba)
    alvo = alvo.lstrip("/")
    caminho = alvo if alvo.startswith("xl/") else "xl/" + alvo
    out = []
    for row in ET.fromstring(z.read(caminho)).iter(M + "row"):
        cel = {}
        for c in row.iter(M + "c"):
            v = c.find(M + "v")
            if v is not None:
                val = ss[int(v.text)] if c.get("t") == "s" else (v.text or "")
            else:
                i = c.find(M + "is")
                val = "".join(t.text or "" for t in i.iter(M + "t")) if i is not None else ""
            cel[_col(c.get("r"))] = val
        if cel:
            out.append([cel.get(i, "") for i in range(max(cel) + 1)])
    return out


def data_iso(v):
    """Número de série do Excel (45869 ou 45869.0) ou dd/mm/aaaa → AAAA-MM-DD; o resto → ""."""
    v = str(v or "").strip()
    if re.fullmatch(r"\d{5}(\.\d+)?", v):
        return (datetime.date(1899, 12, 30) + datetime.timedelta(days=int(float(v)))).isoformat()
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", v)
    if m:
        try:
            return datetime.date(int(m[3]), int(m[2]), int(m[1])).isoformat()
        except ValueError:
            return ""
    return ""


def registros(linhas, analista=None, conhecidos=()):
    """Linhas da aba ANÁLISE → [{codigo, analista, analista_planilha, protocolo, distribuido, concluido, resultado, tipo, ocupacao, area}].
    analista=None: todas as linhas. Com nome ("Sgt Magalhães"), só as dele (casa pela última palavra).
    "analista" é o nome da escala/cadastro quando um dos `conhecidos` casa; senão, o da planilha.
    Atribuído sem DISTRIBUIÇÃO = na fila (o prazo de 10 dias ainda não corre)."""
    cab_i = next((i for i, r in enumerate(linhas[:10]) if "LICENCIAMENTO" in [_norm(c) for c in r]), None)
    if cab_i is None:
        raise ValueError("cabeçalho LICENCIAMENTO não encontrado na aba ANÁLISE")
    cab = [_norm(c) for c in linhas[cab_i]]

    def idx(*nomes):
        for n in nomes:
            for i, c in enumerate(cab):
                if c.startswith(n):
                    return i
        return None
    I = {"codigo": idx("LICENCIAMENTO"), "area": idx("METRAGEM"), "ocupacao": idx("OCUPACAO"), "tipo": idx("ANALISE/"),
         "protocolo": idx("PROTOCOLO"), "distribuido": idx("DISTRIBUICAO"), "analista": idx("ANALISTA"), "concluido": idx("DATA CONCLUSAO"), "resultado": idx("CIA")}
    falta = [k for k in ("codigo", "distribuido", "analista", "concluido") if I[k] is None]
    if falta:
        raise ValueError("colunas não encontradas: " + ", ".join(falta))
    alvo = (_norm(analista).split() or [""])[-1] if analista else None
    out = {}
    for n, r in enumerate(linhas[cab_i + 1:], 1):
        g = lambda k: r[I[k]].strip() if I[k] is not None and I[k] < len(r) else ""
        cod = g("codigo").upper()
        if not CODIGO.match(cod) or (alvo is not None and alvo not in _norm(g("analista"))):
            continue
        quem = analista or nome_conhecido(g("analista"), conhecidos)
        res = _norm(g("resultado"))
        out[cod] = {"codigo": cod, "analista": quem, "analista_planilha": g("analista"), "protocolo": data_iso(g("protocolo")), "distribuido": data_iso(g("distribuido")), "concluido": data_iso(g("concluido")),
                    "resultado": res if res in ("CIA", "CA") else "", "tipo": g("tipo"), "ocupacao": g("ocupacao"), "area": g("area"),
                    "linha": n}  # posição na planilha: o SSEG.exe ordena a caixa como ela (2.6.8)
    return list(out.values())  # a linha mais abaixo vale (reanálise do mesmo código)


def nome_conhecido(da_planilha, conhecidos):
    """"ÁTILA CARPES" → "Sd Carpes" se só um conhecido tem a última palavra entre as palavras da planilha."""
    palavras = set(_norm(da_planilha).split())
    achados = [n for n in conhecidos if (_norm(n).split() or [""])[-1] in palavras]
    return achados[0] if len(achados) == 1 else re.sub(r"\s+", " ", str(da_planilha or "")).strip()


def gravar(raiz, regs, dias=30, hoje=None):
    """Grava <raiz>/<código>/distribuicao.json. Devolve {"criadas", "atualizadas", "iguais"}."""
    hoje = hoje or datetime.date.today()
    corte = (hoje - datetime.timedelta(days=dias)).isoformat()
    cont = {"criadas": [], "atualizadas": [], "iguais": 0}
    for r in regs:
        pasta = os.path.join(raiz, r["codigo"])
        recente = not r["concluido"] or r["concluido"] >= corte
        if not os.path.isdir(pasta):
            if not recente:
                continue
            os.makedirs(pasta)
            cont["criadas"].append(r["codigo"])
        caminho = os.path.join(pasta, ARQUIVO)
        try:
            with open(caminho, encoding="utf-8") as fh:
                velho = json.load(fh)
        except (OSError, ValueError):
            velho = {}
        novo = dict(r, fonte=TITULO)
        anteriores = list(velho.get("analistas_anteriores") or [])
        if velho.get("analista") and _norm(velho["analista"]) != _norm(novo["analista"]) and velho["analista"] not in anteriores:
            anteriores.append(velho["analista"])  # mudou de mãos: a pasta fica, e fica o registro de quem já passou
        if anteriores:
            novo["analistas_anteriores"] = anteriores
        if {k: velho.get(k) for k in novo} == novo:
            cont["iguais"] += 1
            continue
        novo["atualizado_em"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        fd, tmp = tempfile.mkstemp(prefix=".dist-", suffix=".json", dir=pasta)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(novo, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, caminho)
        if r["codigo"] not in cont["criadas"]:
            cont["atualizadas"].append(r["codigo"])
    return cont


def achar_arquivos():
    lim = time.time() - 90 * 60
    fs = [f for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*/tool-results/*download_file_content*.txt"))
          if os.path.getmtime(f) >= lim]
    return sorted(fs, key=os.path.getmtime, reverse=True)


def xlsx_do_download(arquivo):
    """O JSON {content, mimeType, title} do download_file_content → bytes do xlsx, se for a planilha."""
    with open(arquivo, encoding="utf-8") as fh:
        d = json.load(fh)
    if "spreadsheetml" not in (d.get("mimeType") or "") or _norm(d.get("title")) != _norm(TITULO):
        return None
    return base64.b64decode(d["content"])


def nomes_conhecidos(acesso="~/sseg-acesso/analistas.json", escala="~/sseg-escala/escala.json"):
    """Nomes "de escala" para trocar o da planilha: o admin, os cadastrados na porta.py e os da escala."""
    def ler(c):
        try:
            with open(os.path.expanduser(c), encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {}
    a, e = ler(acesso), ler(escala)
    nomes = [a.get("admin") or "Sd Carpes"] + list(a.get("analistas") or {}) + list(e.get("horas") or {})
    return sorted({_norm(n): n for n in nomes}.values())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("arquivos", nargs="*")
    ap.add_argument("--pasta", required=True, help="raiz das pastas de processo (no servidor: ~/SSEG/sseg/processos)")
    ap.add_argument("--analista", action="append",
                    help="nome como na escala; repetível (padrão: o admin e os analistas de ~/sseg-acesso/analistas.json)")
    ap.add_argument("--dias", type=int, default=30, help="concluídos há até N dias também criam pasta")
    a = ap.parse_args(argv)
    for f in a.arquivos or achar_arquivos():
        x = xlsx_do_download(f)
        if x is None:
            continue
        linhas, conhecidos = linhas_da_aba(x), nomes_conhecidos()
        for nome in a.analista or [None]:
            regs = registros(linhas, nome, conhecidos)
            c = gravar(os.path.expanduser(a.pasta), regs, a.dias)
            caixa = sum(1 for r in regs if r["distribuido"] and not r["concluido"])
            fila = sum(1 for r in regs if not r["distribuido"] and not r["concluido"])
            print("distribuicao %s: %d linha(s), %d na fila, %d na caixa; %d pasta(s) criada(s), %d atualizada(s), %d igual(is)"
                  % (nome or "todos", len(regs), fila, caixa, len(c["criadas"]), len(c["atualizadas"]), c["iguais"]))
        return 0
    print("distribuicao: download da planilha \"%s\" (xlsx) não encontrado nos últimos 90 min" % TITULO)
    return 1


if __name__ == "__main__":
    sys.exit(main())
