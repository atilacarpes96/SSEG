#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
caixa_pc.py — a caixa do SOL lida no PC do analista, pela aba do SOL em que ELE já entrou (2.6.3).

Por quê: o servidor lê a caixa com a sessão do administrador (sol_caixa.py). Para os outros analistas a
caixa do SOL não chegava: o Início dependia só da planilha da distribuição, que entra uma vez por dia
(7h47), e a razão social ficava "—" (caso do Sgt Magalhães, 20/10/2026). Agora o botão Atualizar do
SSEG.exe lê a caixa no Chrome do próprio analista, com a depuração remota que ele já ligou para o
Chrome DevTools MCP — o token da sessão não sai da página.

Quem chama é o SSEG.exe (api.caixa_atualizar), que entrega a `aba`: um objeto com avaliar(js) que roda
o script na aba logada e devolve o JSON (app/sol_aba.py). Este arquivo fica no clone para a regra
mudar pelo GitHub, sem .exe novo.

O que grava, na pasta dos processos do PC (o mesmo que o sol_caixa.py grava no servidor):
  <código>/sol-caixa.json      a linha da caixa (sempre; lido_em = hoje)
  <código>/api-<ID>.json       o licenciamento, só se ainda não houver
  <código>/marcos*.json, historico.json, facts.json   uma vez por dia (protocolo, análises, recursos)
  <código>/cia-*.pdf/.txt      CIAs anteriores que faltam (precisa do pdftotext)
  .caixa/caixa.json            quem estava na caixa; quem sai ganha saiu_em no sol-caixa.json
Tudo isso é "gerado" para o sincronizar.py: sobe ao servidor e, se mudar dos dois lados, vale o do servidor.

O que NÃO faz: não digita senha, não clica, não muda nada no SOL. Não cria cartão no Quadro da seção.
"""

import datetime
import json
import os
import re
import time

import sol_caixa

CODIGO = re.compile(r"^A\d{8}[A-Z]{2}\d{3}$")  # o código vira nome de pasta: nada além disso


def _ler(arq):
    try:
        with open(arq, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _de_hoje(arq):
    try:
        return datetime.date.fromtimestamp(os.path.getmtime(arq)) == datetime.date.today()
    except OSError:
        return False


def levantar(aba, raiz, baixar=True):
    """Lê a caixa na aba e grava na pasta `raiz`. Devolve {total, novos, sairam, avisos, analista}.
    PermissionError: o SOL recusou (sessão caída na aba) — quem chama pede para entrar de novo."""
    itens = sol_caixa.ler_caixa(aba)
    pasta_caixa = os.path.join(raiz, ".caixa")
    os.makedirs(pasta_caixa, exist_ok=True)
    antes = _ler(os.path.join(pasta_caixa, "caixa.json"))
    estavam = {i.get("codigo") for i in antes.get("itens") or []} if antes else None
    resumo, avisos = [], []
    for it in itens:
        ident = sol_caixa._achar(it, "id", "licenciamento.id", "idLicenciamento", "licenciamentoId")
        codigo = sol_caixa._achar(it, "numeroLicenciamento", "licenciamento.numero", "numero", "codigo")
        if not (ident and codigo and CODIGO.match(str(codigo))):
            avisos.append("item da caixa sem id ou código")
            continue
        linha = {"id": ident, "id_analise": sol_caixa._achar(it, "idAnalise", "idAnaliseTecnica"), "codigo": codigo, "novo": False}
        pasta = os.path.join(raiz, codigo)
        sol_caixa.gravar_sol_caixa(pasta, it, ident, linha["id_analise"])
        if baixar:
            try:
                arq = os.path.join(pasta, "api-%s.json" % ident)
                if not os.path.exists(arq):
                    d = sol_caixa.buscar(aba, "%s/%s" % (sol_caixa.LICENCIAMENTO, ident))
                    with open(arq, "w", encoding="utf-8") as fh:
                        json.dump(d, fh, ensure_ascii=False)
                    linha["novo"] = True
                if linha["novo"] or not _de_hoje(os.path.join(pasta, "marcos.json")):
                    sol_caixa.marcos_proc(aba, ident, codigo, linha, raiz=raiz, gatilho=False)
                sol_caixa.baixar_cias(aba, codigo, linha, raiz=raiz)
            except PermissionError:
                raise
            except (RuntimeError, OSError, ValueError) as e:
                linha["aviso"] = str(e)
        if linha.get("aviso"):
            avisos.append("%s: %s" % (codigo, linha["aviso"]))
        resumo.append(linha)
    sairam = []
    if estavam is not None and itens:  # caixa vazia na leitura = leitura suspeita: ninguém sai
        atuais = {r["codigo"] for r in resumo}
        for cod in sorted(c for c in estavam - atuais if c):
            try:
                if sol_caixa.marcar_saida(aba, cod, raiz=raiz):
                    sairam.append(cod)
            except PermissionError:
                raise
            except (RuntimeError, OSError, ValueError) as e:
                avisos.append("%s: %s" % (cod, e))
    with open(os.path.join(pasta_caixa, "caixa.json"), "w", encoding="utf-8") as fh:
        json.dump({"lido_em": time.strftime("%Y-%m-%d %H:%M"), "total": len(itens), "itens": resumo, "onde": "pc"},
                  fh, ensure_ascii=False, indent=1)
    nomes = {it.get("nomeAnalista") for it in itens if it.get("nomeAnalista")}
    return {"total": len(itens), "novos": [r["codigo"] for r in resumo if r["novo"]], "sairam": sairam,
            "avisos": avisos, "analista": nomes.pop() if len(nomes) == 1 else ""}

