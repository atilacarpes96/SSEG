#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quadro.py — tarefas soltas da tela Quadro do SSEG.exe (2.1.14): pendência de trabalho que sobrou de
uma conversa, fiscalização, reunião, administrativo. Os processos entram no quadro sozinhos, pela
caixa (distribuicao.json); este arquivo guarda só o que não é processo.

Mora em <pasta dos processos>/quadro.json, no PC, fora do Git (o texto pode citar processo ou
pessoa). A pasta vem da configuração do SSEG.exe (%APPDATA%\\SSEG\\config.json) ou de --pasta.

Quadro da seção (2.3.0): o mesmo formato, em ~/sseg-quadro/quadro.json no servidor, lido e mexido pela
porta.py. Lá cada cartão leva quem criou ("autor"), quem pegou ("pegou"), o que foi feito ("feito_texto")
e as datas de início (entrou em Fazendo) e de fim (entrou em Feito).

USO (o Claude da conversa, depois de o analista confirmar a pendência)
  python sseg/scripts/quadro.py adicionar "Conferir o log da rotina das 7h47" --origem "conversa: cards do SSEG"
  python sseg/scripts/quadro.py listar
"""

import argparse
import json
import os
import secrets
import sys
import tempfile
import time

ARQUIVO = "quadro.json"
COLUNAS = ["afazer", "fazendo", "esperando", "feito"]
NOMES = {"afazer": "A fazer", "fazendo": "Fazendo", "esperando": "Esperando", "feito": "Feito"}


def pasta_da_config():
    base = os.environ.get("APPDATA") or os.path.expanduser("~/.config")
    try:
        with open(os.path.join(base, "SSEG", "config.json"), encoding="utf-8") as fh:
            return json.load(fh).get("processos") or ""
    except (OSError, ValueError):
        return ""


def ler(raiz):
    try:
        with open(os.path.join(raiz, ARQUIVO), encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        d = {}
    d.setdefault("versao", 1)
    d.setdefault("cartoes", [])  # {id, titulo, coluna, origem, criado, movido, checklist: [{texto, feito}]} (+ seção: autor, pegou, feito_texto, inicio, fim)
    return d


def gravar(raiz, d):
    os.makedirs(raiz, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".quadro-", suffix=".json", dir=raiz)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(raiz, ARQUIVO))
    return d


def _achar(d, id_):
    c = next((c for c in d["cartoes"] if c["id"] == id_), None)
    if not c:
        raise ValueError("cartão não encontrado: %s" % id_)
    return c


def adicionar(raiz, titulo, origem="", coluna="afazer", autor=""):
    titulo = " ".join((titulo or "").split())[:200]
    if not titulo:
        raise ValueError("cartão sem título")
    if coluna not in COLUNAS:
        raise ValueError("coluna inválida: %r" % coluna)
    d = ler(raiz)
    # a mesma pendência mandada de novo (outra tentativa da conversa) não duplica
    igual = next((c for c in d["cartoes"] if c["titulo"].lower() == titulo.lower() and c["coluna"] != "feito"), None)
    if igual:
        return igual
    agora = time.time()
    c = {"id": secrets.token_hex(4), "titulo": titulo, "coluna": coluna, "origem": (origem or "").strip()[:200],
         "criado": agora, "movido": agora, "checklist": []}
    if autor:
        c["autor"] = autor
    _datas(c, coluna, agora)
    d["cartoes"].append(c)
    gravar(raiz, d)
    return c


def _datas(c, coluna, agora):
    """Fazendo marca o início (uma vez); Feito marca o fim; sair do Feito apaga o fim."""
    if coluna == "fazendo" and not c.get("inicio"):
        c["inicio"] = agora
    if coluna == "feito":
        c["fim"] = agora
        c.setdefault("inicio", c.get("criado", agora))
    else:
        c.pop("fim", None)


def alterar(raiz, id_, **campos):
    """coluna, titulo, checklist ([{texto, feito}]), pegou (nome ou "") e feito_texto."""
    d = ler(raiz)
    c = _achar(d, id_)
    if "coluna" in campos:
        if campos["coluna"] not in COLUNAS:
            raise ValueError("coluna inválida: %r" % campos["coluna"])
        if campos["coluna"] != c["coluna"]:
            c["coluna"], c["movido"] = campos["coluna"], time.time()
            _datas(c, c["coluna"], c["movido"])
    if "pegou" in campos:
        p = " ".join(str(campos["pegou"] or "").split())[:60]
        if p:
            c["pegou"] = p
        else:
            c.pop("pegou", None)
    if "feito_texto" in campos:
        c["feito_texto"] = str(campos["feito_texto"] or "").strip()[:2000]
    if "titulo" in campos:
        t = " ".join((campos["titulo"] or "").split())[:200]
        if not t:
            raise ValueError("cartão sem título")
        c["titulo"] = t
    if "checklist" in campos:
        c["checklist"] = [{"texto": str(x.get("texto", "")).strip()[:200], "feito": bool(x.get("feito"))}
                          for x in campos["checklist"] or [] if str(x.get("texto", "")).strip()]
    gravar(raiz, d)
    return c


def remover(raiz, id_):
    """Devolve o cartão tirado, para o "Desfazer" pôr de volta no mesmo lugar."""
    d = ler(raiz)
    i = next((k for k, c in enumerate(d["cartoes"]) if c["id"] == id_), None)
    if i is None:
        raise ValueError("cartão não encontrado: %s" % id_)
    c = d["cartoes"].pop(i)
    gravar(raiz, d)
    return {"cartao": c, "pos": i}


def restaurar(raiz, cartao, pos=None):
    d = ler(raiz)
    if not any(c["id"] == cartao.get("id") for c in d["cartoes"]):
        d["cartoes"].insert(len(d["cartoes"]) if pos is None else int(pos), cartao)
        gravar(raiz, d)
    return cartao


def main(argv=None):
    ap = argparse.ArgumentParser(description="Tarefas soltas da tela Quadro do SSEG.exe")
    ap.add_argument("--pasta", default="", help="pasta dos processos (padrão: a da configuração do SSEG.exe)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("adicionar")
    a.add_argument("titulo")
    a.add_argument("--origem", default="")
    a.add_argument("--coluna", default="afazer", choices=COLUNAS)
    sub.add_parser("listar")
    args = ap.parse_args(argv)
    raiz = args.pasta or pasta_da_config()
    if not raiz or not os.path.isdir(raiz):
        print("quadro: pasta dos processos não encontrada (configure no SSEG.exe ou passe --pasta)")
        return 1
    if args.cmd == "adicionar":
        c = adicionar(raiz, args.titulo, args.origem, args.coluna)
        print("quadro: \"%s\" em %s" % (c["titulo"], NOMES[c["coluna"]]))
    else:
        for c in ler(raiz)["cartoes"]:
            print("%-9s %s%s" % (NOMES[c["coluna"]], c["titulo"], "  (" + c["origem"] + ")" if c["origem"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
