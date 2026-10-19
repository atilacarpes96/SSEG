#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sol_snapshot.py — o memorial e a CIA de uma análise, congelados como estavam (SSEG.exe 2.6.0).

Por quê: quando o RT entrega o projeto corrigido, o memorial no SOL já é outro. Para comparar, a pasta
precisa ter o memorial de quando a CIA saiu. A CIA só aparece depois que o analista emite, então o
memorial é pego ANTES (no passo de lançar a notificação) e a CIA depois (salvar).

Só LÊ o SOL (GET do licenciamento e do arquivo), pela aba logada do Chromium do servidor, no mesmo ritmo
educado do sol_caixa.py. Nunca escreve no SOL.

Arquivos, na pasta do processo (todos dentro da lista do enviar.py, sobem ao servidor e descem ao PC):
  memorial <N>.pdf          o memorial descritivo (caracteristica.arquivo) da análise N
  licenciamento <N>.json    o JSON do licenciamento no mesmo instante (o que o RT tinha declarado)
  CIA <N>.pdf               a CIA emitida na análise N (cópia de cia-<id>.pdf)
N = número da análise em andamento (marcos-resumo.json, "analise"): a CIA dela leva o mesmo N.

USO
  python3 sseg/scripts/sol_snapshot.py congelar <código> [--refazer]
  python3 sseg/scripts/sol_snapshot.py salvar <código>
Saída: uma linha JSON {"ok": ..., "arquivos": [...], "avisos": [...]}.
"""

import argparse
import base64
import glob
import json
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import sol_caixa as sc  # noqa: E402 — a sessão, o ritmo e o download são os mesmos da leitura da caixa

CODIGO = re.compile(r"^A\d{8}[A-Z]{2}\d{3}$")


def _ler(arq):
    try:
        with open(arq, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _pasta(codigo):
    if not CODIGO.match(codigo or ""):
        raise ValueError("código de processo inválido: %r" % codigo)
    p = os.path.join(sc.PROCESSOS, codigo)
    if not os.path.isdir(p):
        raise ValueError("não há pasta %s no servidor" % codigo)
    return p


def _ident(pasta):
    """Id do licenciamento: sol-caixa.json, senão o nome do api-<ID>.json mais novo."""
    i = _ler(os.path.join(pasta, "sol-caixa.json")).get("id")
    if i:
        return i
    apis = sorted(glob.glob(os.path.join(pasta, "api-*.json")), key=os.path.getmtime)
    return re.search(r"api-(\d+)\.json$", apis[-1]).group(1) if apis else None


def _numero(pasta):
    return _ler(os.path.join(pasta, "marcos-resumo.json")).get("analise")


def _baixar_pdf(aba, ident_arquivo, destino):
    d = sc._consultar(aba, sc.BAIXAR, "%s/%s" % (sc.ARQUIVO, ident_arquivo))
    if d["status"] != 200:
        raise RuntimeError("SOL respondeu %s ao baixar o arquivo %s" % (d["status"], ident_arquivo))
    dados = base64.b64decode(d["b64"])
    if not dados.startswith(b"%PDF"):
        raise RuntimeError("o arquivo %s não veio como PDF" % ident_arquivo)
    tmp = destino + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(dados)
    os.replace(tmp, destino)


def congelar(codigo, refazer=False, aba=None):
    """Memorial e JSON do licenciamento de agora. Se já existem para esta análise, mantém (o que vale é o de
    quando a CIA foi lançada); `refazer` sobrescreve."""
    pasta = _pasta(codigo)
    n, ident = _numero(pasta), _ident(pasta)
    if not n or not ident:
        raise ValueError("faltam os Marcos ou o id do licenciamento na pasta: rode a leitura da caixa antes")
    out = {"ok": True, "analise": n, "arquivos": [], "avisos": []}
    mem, lic = os.path.join(pasta, "memorial %s.pdf" % n), os.path.join(pasta, "licenciamento %s.json" % n)
    if os.path.exists(mem) and os.path.exists(lic) and not refazer:
        out["avisos"].append("a análise %s já tinha memorial congelado: mantido (use refazer para trocar)" % n)
        out["arquivos"] = [os.path.basename(mem), os.path.basename(lic)]
        return out
    aba = aba or sc.aba_do_sol()
    if aba is None:
        raise RuntimeError("Chrome do servidor fora do ar ou sem aba do SOL")
    s = sc._logar_se_caiu(aba)
    if not s["logado"]:
        raise PermissionError("sessão do SOL caída")
    lic_json = sc.buscar(aba, "%s/%s" % (sc.LICENCIAMENTO, ident))
    arq = ((lic_json.get("caracteristica") or {}).get("arquivo") or {})
    if not arq.get("id"):
        out["avisos"].append("o licenciamento não tem memorial anexado (caracteristica.arquivo vazio)")
    else:
        _baixar_pdf(aba, arq["id"], mem)
        out["arquivos"].append(os.path.basename(mem))
        out["memorial"] = arq.get("nomeArquivo")
    with open(lic, "w", encoding="utf-8") as fh:
        json.dump(lic_json, fh, ensure_ascii=False)
    out["arquivos"].append(os.path.basename(lic))
    return out


def salvar(codigo, aba=None):
    """Depois da emissão: atualiza os Marcos, baixa a CIA e grava CIA <N>.pdf. Sem memorial congelado, avisa."""
    pasta = _pasta(codigo)
    ident = _ident(pasta)
    out = {"ok": True, "arquivos": [], "avisos": []}
    aba = aba or sc.aba_do_sol()
    if aba is None:
        raise RuntimeError("Chrome do servidor fora do ar ou sem aba do SOL")
    s = sc._logar_se_caiu(aba)
    if not s["logado"]:
        raise PermissionError("sessão do SOL caída")
    linha = {}
    sc.marcos_proc(aba, ident, codigo, linha)
    sc.baixar_cias(aba, codigo, linha)
    if linha.get("aviso"):
        out["avisos"].append(linha["aviso"])
    resumo = _ler(os.path.join(pasta, "marcos-resumo.json"))
    ultima = max(resumo.get("analises") or [{}], key=lambda a: a.get("data") or "")
    if ultima.get("resultado") != "CIA" or not ultima.get("arquivo"):
        out["ok"] = False
        out["avisos"].append("a última análise do SOL é %s, não uma CIA: emita a CIA no SOL antes de salvar (CA não tem CIA para guardar)"
                             % (ultima.get("resultado") or "outra"))
        return out
    n = resumo.get("analise") or 0
    # a análise em andamento é a (nº de análises emitidas + 1) enquanto não emite; emitida, a CIA é a nº len(analises)
    n_cia = len(resumo.get("analises") or [])
    pdf = os.path.join(pasta, "cia-%s.pdf" % ultima["arquivo"])
    if not os.path.exists(pdf):
        out["ok"] = False
        out["avisos"].append("a CIA %s ainda não foi baixada" % ultima["arquivo"])
        return out
    dest = os.path.join(pasta, "CIA %d.pdf" % n_cia)
    if os.path.exists(dest):  # a que o analista já guardou vale: nunca sobrescreve
        out["avisos"].append("CIA %d.pdf já existia: mantida" % n_cia)
    else:
        shutil.copy2(pdf, dest)
    out["arquivos"].append(os.path.basename(dest))
    out["analise"] = n_cia
    if not (os.path.exists(os.path.join(pasta, "memorial %d.pdf" % n_cia))):
        out["avisos"].append("não há memorial congelado da análise %d: o do SOL agora pode já ser o corrigido" % n_cia)
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("acao", choices=["congelar", "salvar"])
    ap.add_argument("codigo")
    ap.add_argument("--refazer", action="store_true")
    a = ap.parse_args()
    try:
        r = congelar(a.codigo, a.refazer) if a.acao == "congelar" else salvar(a.codigo)
    except (ValueError, RuntimeError, PermissionError, OSError) as e:
        r = {"ok": False, "arquivos": [], "avisos": [str(e)]}
    print(json.dumps(r, ensure_ascii=False))
    sys.exit(0 if r["ok"] else 1)
