#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ct_recursos.py — CT e recursos em aberto das planilhas da SSeg viram <código>/ct.json e
<código>/recurso.json (SSEG.exe 2.3.0).

Roda no servidor, na rotina do Painel do Dia, sobre os downloads (xlsx) das planilhas
"CONSULTAS TÉCNICAS 6°BBM" (aba Consulta Técnica) e "OFÍCIOS, INVIABILIDADES, RECURSOS E
FACTs 6°BBM" (aba Rec. Análise/Vistoria). Para cada linha com código A000…:
  - minuta sem "Finalizado" ......................... estado "minuta" (CT marcada ou pendente;
                                                        recurso para redigir)
  - minuta finalizada, chefia sem "Finalizado" ...... estado "chefia" (aguardando a chefia)
  - os dois finalizados ............................. sai (o card esquece)
O primeiro "Finalizado" depois do analista (ME) é o da minuta; o último da linha, o da chefia.

Cada pasta leva a lista do que está aberto nela, com o analista (nome da escala quando casa).
Pasta que tinha CT/recurso e ficou sem nada aberto recebe {"itens": []}: apagar não desce ao
PC no Sincronizar, mudar desce. A porta.py mostra a pasta também a quem é ME de um item
aberto, mesmo que o processo seja de outro analista.

USO
  python3 ct_recursos.py --pasta ~/SSEG/sseg/processos [arquivo do download ...]
  (sem arquivo, procura os downloads das duas planilhas nos últimos 90 min)
"""

import argparse
import base64
import json
import os
import re
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from distribuicao import CODIGO, _norm, achar_arquivos, data_iso, linhas_da_aba, nome_conhecido, nomes_conhecidos  # noqa: E402
from escala import abas  # noqa: E402

PLANILHA_CT = "CONSULTAS TECNICAS"
PLANILHA_REC = "OFICIOS, INVIABILIDADES"
ARQ = {"ct": "ct.json", "recurso": "recurso.json"}


def finalizado(v):
    try:
        return float(str(v).replace(",", ".").strip() or 0) == 1
    except ValueError:
        return False


def _cabecalho(linhas, *precisa):
    """Índice da linha de cabeçalho (a que tem todos os nomes pedidos) e a lista normalizada."""
    for i, r in enumerate(linhas[:10]):
        cab = [_norm(c) for c in r]
        if all(any(c.startswith(p) for c in cab) for p in precisa):
            return i, cab
    raise ValueError("cabeçalho não encontrado (%s)" % ", ".join(precisa))


def _idx(cab, nome, depois=-1):
    return next((i for i, c in enumerate(cab) if i > depois and c.startswith(nome)), None)


def hora(v):
    """0.375 (fração do dia, como o Excel guarda) → "09:00"; "14:00" fica."""
    try:
        m = round(float(str(v).replace(",", ".")) * 24 * 60)
        return "%02d:%02d" % divmod(m % (24 * 60), 60)
    except ValueError:
        return str(v or "").strip()


def _celula(r, i):
    return r[i].strip() if i is not None and i < len(r) else ""


def ler_ct(linhas, conhecidos=()):
    """Aba Consulta Técnica → {código: [item]} só do que não está todo finalizado."""
    h, cab = _cabecalho(linhas, "PPCI", "ME", "FINALIZADO")
    i = {"cod": _idx(cab, "PPCI"), "fact": _idx(cab, "FACT"), "pedida": _idx(cab, "DATA SOLICITACAO"), "me": _idx(cab, "ME")}
    i.update(data=_idx(cab, "DATA", i["me"]), hora=_idx(cab, "HORA", i["me"]), modo=_idx(cab, "MODALIDADE", i["me"]),
             minuta=_idx(cab, "FINALIZADO", i["me"]))
    i["chefia"] = max(k for k, c in enumerate(cab) if c.startswith("FINALIZADO"))
    out = {}
    for r in linhas[h + 1:]:
        cod = _celula(r, i["cod"]).upper()
        if not CODIGO.match(cod) or finalizado(_celula(r, i["chefia"])):
            continue
        me = _celula(r, i["me"])
        out.setdefault(cod, []).append({
            "tipo": "CT", "fact": _celula(r, i["fact"]), "pedida": data_iso(_celula(r, i["pedida"])),
            "data": data_iso(_celula(r, i["data"])), "hora": hora(_celula(r, i["hora"])), "modalidade": _celula(r, i["modo"]),
            "analista": nome_conhecido(me, conhecidos) if me else "",
            "estado": "chefia" if finalizado(_celula(r, i["minuta"])) else "minuta"})
    return out


def ler_recursos(linhas, conhecidos=()):
    """Aba Rec. Análise/Vistoria → {código: [item]} só do que não está todo finalizado."""
    h, cab = _cabecalho(linhas, "PPCI", "DOCUMENTO", "ME RASCUNHO")
    i = {"cod": _idx(cab, "PPCI"), "doc": _idx(cab, "DOCUMENTO"), "dist": _idx(cab, "DATA PARA DISTRIBUICAO"),
         "me": _idx(cab, "ME RASCUNHO"), "objeto": _idx(cab, "OBJETO"), "resp": _idx(cab, "ME RESP"), "decisao": _idx(cab, "DECIS")}
    i["minuta"] = _idx(cab, "FINALIZADO", i["me"])
    i["chefia"] = max(k for k, c in enumerate(cab) if c.startswith("FINALIZADO"))
    out = {}
    for r in linhas[h + 1:]:
        cod = _celula(r, i["cod"]).upper()
        if not CODIGO.match(cod) or finalizado(_celula(r, i["chefia"])):
            continue
        me = _celula(r, i["me"])
        out.setdefault(cod, []).append({
            "tipo": _celula(r, i["doc"]) or "Recurso", "distribuido": data_iso(_celula(r, i["dist"])),
            "analista": nome_conhecido(me, conhecidos) if me else "", "objeto": _celula(r, i["objeto"]),
            "chefia": _celula(r, i["resp"]), "decisao": _celula(r, i["decisao"]),
            "estado": "chefia" if finalizado(_celula(r, i["minuta"])) else "minuta"})
    return out


def gravar(raiz, tipo, abertos):
    """Grava <código>/<ct|recurso>.json. Quem tinha arquivo e saiu da lista ganha {"itens": []}."""
    nome = ARQ[tipo]
    cont = {"gravados": 0, "zerados": 0, "iguais": 0}
    com_arquivo = {c for c in os.listdir(raiz) if CODIGO.match(c) and os.path.isfile(os.path.join(raiz, c, nome))} \
        if os.path.isdir(raiz) else set()
    for cod in sorted(set(abertos) | com_arquivo):
        novo = {"itens": abertos.get(cod, [])}
        pasta = os.path.join(raiz, cod)
        caminho = os.path.join(pasta, nome)
        try:
            with open(caminho, encoding="utf-8") as fh:
                velho = json.load(fh)
        except (OSError, ValueError):
            velho = None
        if velho is not None and velho.get("itens") == novo["itens"]:
            cont["iguais"] += 1
            continue
        if velho is None and not novo["itens"]:
            continue
        os.makedirs(pasta, exist_ok=True)
        novo["atualizado_em"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        fd, tmp = tempfile.mkstemp(prefix=".%s-" % tipo, suffix=".json", dir=pasta)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(novo, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, caminho)
        cont["zerados" if not novo["itens"] else "gravados"] += 1
    return cont


def _xlsx(arquivo):
    """(título normalizado, bytes) do JSON do download_file_content, ou de um .xlsx."""
    if arquivo.endswith(".xlsx"):
        return _norm(os.path.basename(arquivo)), open(arquivo, "rb").read()
    with open(arquivo, encoding="utf-8") as fh:
        d = json.load(fh)
    if "spreadsheetml" not in (d.get("mimeType") or ""):
        return "", None
    return _norm(d.get("title")), base64.b64decode(d["content"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("arquivos", nargs="*")
    ap.add_argument("--pasta", required=True)
    a = ap.parse_args(argv)
    raiz, conhecidos, feito = os.path.expanduser(a.pasta), nomes_conhecidos(), set()
    for f in a.arquivos or achar_arquivos():
        titulo, x = _xlsx(f)
        if x is None:
            continue
        if PLANILHA_CT in titulo and "ct" not in feito:
            aba = next(n for n in abas(x) if _norm(n).startswith("CONSULTA TECNICA"))
            ab = ler_ct(linhas_da_aba(x, _norm(aba)), conhecidos)
            tipo = "ct"
        elif PLANILHA_REC in titulo and "recurso" not in feito:
            aba = next(n for n in abas(x) if re.match(r"REC\.? ?ANALISE", _norm(n)))
            ab = ler_recursos(linhas_da_aba(x, _norm(aba)), conhecidos)
            tipo = "recurso"
        else:
            continue
        feito.add(tipo)
        c = gravar(raiz, tipo, ab)
        n = sum(len(v) for v in ab.values())
        print("ct_recursos %s: %d em aberto (%d na minuta, %d com a chefia); %d pasta(s) gravada(s), %d zerada(s), %d igual(is)"
              % (tipo, n, sum(1 for v in ab.values() for it in v if it["estado"] == "minuta"),
                 sum(1 for v in ab.values() for it in v if it["estado"] == "chefia"), c["gravados"], c["zerados"], c["iguais"]))
    for t in ("ct", "recurso"):
        if t not in feito:
            print("ct_recursos %s: planilha não veio no download" % t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
