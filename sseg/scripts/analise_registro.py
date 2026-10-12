# -*- coding: utf-8 -*-
"""
analise_registro.py — o analise.json da pasta do processo (janela do processo, SSEG.exe 2.1).

Um arquivo por processo, ao lado do JSON do SOL e da CIA, em <print ppci>/<código>/analise.json.
Vai ao servidor pelo Sincronizar processos e NUNCA ao GitHub (é dado de processo). Quem escreve:
  - o programa (marcas do checklist, respostas às pendências, texto final da CIA);
  - o Claude da conversa, por `sseg.py analise ...` (pendências e rascunhos de exigência).

Regra do texto (decisão do Átila, 12/10/2026): cada exigência guarda "rascunho" (do Claude) e
"final" (o que o analista salvou). CIA, revisão e lançamento leem só o final; o rascunho fica
para comparação. O Claude nunca escreve no "final".
"""

import json
import os
import tempfile
import time

ARQUIVO = "analise.json"


def caminho(pasta):
    return os.path.join(pasta, ARQUIVO)


def ler(pasta):
    try:
        with open(caminho(pasta), encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        d = {}
    d.setdefault("versao", 1)
    d.setdefault("passos", {})       # "4": true
    d.setdefault("itens", {})        # "Extintores de Incêndio|nº de ordem": "ok" | "exigencia"
    d.setdefault("pendencias", [])   # {id, texto, origem, resposta, feita, quando}
    d.setdefault("exigencias", [])   # {id, medida, rascunho, final, fundamento, origem, quando}
    d.setdefault("chat", {})         # {sessao, pct_5h}
    return d


def gravar(pasta, d):
    """Grava inteiro, por arquivo temporário e troca (a janela lê enquanto o Claude escreve)."""
    os.makedirs(pasta, exist_ok=True)
    d["alterado"] = time.time()
    fd, tmp = tempfile.mkstemp(prefix=".analise-", suffix=".json", dir=pasta)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, caminho(pasta))
    return d


def _novo_id(lista, prefixo):
    n = max([int(x["id"][len(prefixo):]) for x in lista if str(x.get("id", "")).startswith(prefixo)] + [0])
    return "%s%d" % (prefixo, n + 1)


def pendencia(pasta, texto, origem="claude"):
    d = ler(pasta)
    p = {"id": _novo_id(d["pendencias"], "p"), "texto": texto.strip(), "origem": origem,
         "resposta": "", "feita": False, "quando": time.time()}
    d["pendencias"].append(p)
    gravar(pasta, d)
    return p


def exigencia(pasta, texto, medida="", fundamento="", origem="claude"):
    """Do Claude, o texto entra como rascunho; do analista, já como final."""
    d = ler(pasta)
    e = {"id": _novo_id(d["exigencias"], "e"), "medida": medida.strip(), "fundamento": fundamento.strip(),
         "rascunho": texto.rstrip() if origem == "claude" else "", "final": "" if origem == "claude" else texto.rstrip(),
         "origem": origem, "quando": time.time()}
    d["exigencias"].append(e)
    gravar(pasta, d)
    return e


def rascunho(pasta, id_, texto, medida="", fundamento=""):
    """O redator devolve o rascunho para um item que JÁ existe (o "Pedir ao Claude" da coluna CIA).
    Medida e fundamento só entram se o item ainda não tiver. O texto final do analista não é tocado."""
    d = ler(pasta)
    for e in d["exigencias"]:
        if e["id"] == id_:
            e["rascunho"] = texto.rstrip()
            e["pedido"] = False
            if medida.strip() and not e.get("medida"):
                e["medida"] = medida.strip()
            if fundamento.strip() and not e.get("fundamento"):
                e["fundamento"] = fundamento.strip()
            gravar(pasta, d)
            return e
    return None


def atualizar(pasta, colecao, id_, **campos):
    """Muda campos de uma pendência ou exigência (pelo programa). Devolve o item ou None."""
    d = ler(pasta)
    for x in d[colecao]:
        if x["id"] == id_:
            x.update(campos)
            gravar(pasta, d)
            return x
    return None


def remover(pasta, colecao, id_):
    d = ler(pasta)
    d[colecao] = [x for x in d[colecao] if x["id"] != id_]
    gravar(pasta, d)


def marcar(pasta, grupo, chave, valor):
    """grupo "passos" (chave = nº do passo) ou "itens" (chave = "medida|item"). valor None desmarca."""
    d = ler(pasta)
    if valor in (None, False, ""):
        d[grupo].pop(str(chave), None)
    else:
        d[grupo][str(chave)] = valor
    gravar(pasta, d)
    return d


def texto_cia(d):
    """Só o final, na ordem — o que vai para a CIA, a revisão e o SOL."""
    return [e for e in d["exigencias"] if e.get("final", "").strip()]


# ------------------------------------------------------------------ cli (sseg.py analise)

def args_parser(sp):
    sp.add_argument("--pasta", required=True, help="pasta do processo (print ppci/<código>)")
    sub = sp.add_subparsers(dest="acao", required=True)
    p = sub.add_parser("pendencia", help="algo que falta ver ou perguntar ao analista")
    p.add_argument("texto", help='texto, ou "-" para ler da entrada (heredoc)')
    p = sub.add_parser("exigencia", help="rascunho de exigência para a coluna CIA (item novo)")
    p.add_argument("texto", help='texto, ou "-" para ler da entrada (heredoc) — o jeito certo para texto com quebra de linha')
    p.add_argument("--medida", default="")
    p.add_argument("--fundamento", default="", help='ex.: "RT 11/2016, item 5.4.2"')
    p = sub.add_parser("rascunho", help="rascunho para um item que já existe na coluna CIA (pedido pelo analista)")
    p.add_argument("id", help="id do item (ex.: e3)")
    p.add_argument("texto", help='texto, ou "-" para ler da entrada (heredoc)')
    p.add_argument("--medida", default="")
    p.add_argument("--fundamento", default="")
    p = sub.add_parser("passo", help="marca um passo do checklist (1 a 16)")
    p.add_argument("n", type=int)
    sub.add_parser("ver", help="mostra o registro (pendências e o texto final da CIA)")


def _texto(t):
    """"-" lê da entrada: texto longo, com quebra de linha, aspas e $, sem depender de escape."""
    if t == "-":
        import sys
        return sys.stdin.read()
    return t.replace("\\n", "\n")


def principal(args):
    if hasattr(args, "texto"):
        args.texto = _texto(args.texto)
    if args.acao == "rascunho":
        e = rascunho(args.pasta, args.id, args.texto, args.medida, args.fundamento)
        print("rascunho gravado no item %s" % args.id if e else "item %s não existe" % args.id)
        return
    if args.acao == "pendencia":
        p = pendencia(args.pasta, args.texto)
        print("pendência %s registrada" % p["id"])
    elif args.acao == "exigencia":
        e = exigencia(args.pasta, args.texto, args.medida, args.fundamento)
        print("exigência %s registrada como rascunho (o analista salva o texto final)" % e["id"])
    elif args.acao == "passo":
        marcar(args.pasta, "passos", args.n, True)
        print("passo %d marcado" % args.n)
    else:
        d = ler(args.pasta)
        print(json.dumps({"pendencias": d["pendencias"], "passos": d["passos"],
                          "cia_final": [{"id": e["id"], "medida": e["medida"], "final": e["final"],
                                         "fundamento": e["fundamento"]} for e in texto_cia(d)],
                          "rascunhos_sem_final": [e["id"] for e in d["exigencias"] if not e.get("final")]},
                         ensure_ascii=False, indent=1))
