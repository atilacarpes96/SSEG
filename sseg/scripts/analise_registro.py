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


def _data(v, campo):
    v = (v or "").strip()
    if v and not (len(v) == 10 and v[4] == v[7] == "-" and (v[:4] + v[5:7] + v[8:]).isdigit()):
        raise ValueError("data inválida em %s: %r" % (campo, v))
    return v


def situacao(pasta, **campos):
    """Dados da caixa marcados à mão na janela do processo (2.1.13), para quando a planilha
    "Distribuição Análise" não tem o processo: distribuido, concluido, ct ("AAAA-MM-DD" ou "") e
    resultado ("CIA", "CA" ou ""). O que vem da planilha mora em distribuicao.json e manda nele."""
    d = ler(pasta)
    for k, v in campos.items():
        if k in ("distribuido", "concluido", "ct"):
            v = _data(v, k)
        elif k == "resultado":
            v = (v or "").strip().upper()
            if v not in ("", "CIA", "CA"):
                raise ValueError("resultado inválido: %r" % v)
        else:
            raise ValueError("campo inválido: %r" % k)
        if v:
            d[k] = v
        else:
            d.pop(k, None)
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
    p = sub.add_parser("resolver", help="marca pendências como resolvidas (ex.: p2 p3) — sai do topo do checklist")
    p.add_argument("ids", nargs="+")
    p = sub.add_parser("passo", help="marca passos do checklist (1 a 16), um ou vários: passo 1 3 4 5")
    p.add_argument("n", type=int, nargs="+")
    sub.add_parser("ver", help="mostra o registro (pendências e o texto final da CIA)")
    p = sub.add_parser("sol-pdf", help="arquivo do SOL baixado em base64 (sol-arquivo-<id>.b64.json) → PDF + texto")
    p.add_argument("id", help="id do arquivo no SOL (GET /solcbm/api/v1/adm/arquivo/<id>)")
    p.add_argument("--nome", default="sol", help='prefixo dos arquivos; "cia" também grava cia-ultima.txt')


def sol_pdf(pasta, ident, nome="sol"):
    """O SOL só entrega o arquivo à aba logada (token no sessionStorage): o Claude baixa com
    evaluate_script + filePath em <pasta>/sol-arquivo-<id>.b64.json ({"status", "n", "b64"}) e
    esta rotina faz o resto, sem Python solto na janela: decodifica, grava o PDF, extrai o texto
    com o pdftotext e apaga o intermediário."""
    import base64
    import shutil
    import subprocess
    origem = os.path.join(pasta, "sol-arquivo-%s.b64.json" % ident)
    if not os.path.exists(origem):
        return ("não achei %s — baixe antes com evaluate_script (filePath nesse caminho), devolvendo "
                '{"status", "n", "b64"}' % origem)
    with open(origem, encoding="utf-8") as fh:
        t = fh.read()
    d = json.loads(t[t.index("{"):t.rindex("}") + 1])   # o filePath às vezes grava algo antes do JSON
    if d.get("status") != 200:
        return "o SOL respondeu %s para o arquivo %s; nada gravado" % (d.get("status"), ident)
    dados = base64.b64decode(d["b64"])
    if not dados.startswith(b"%PDF"):
        return "o arquivo %s não é PDF (começa com %r); nada gravado" % (ident, dados[:8])
    pdf = os.path.join(pasta, "%s-%s.pdf" % (nome, ident))
    with open(pdf, "wb") as fh:
        fh.write(dados)
    os.remove(origem)
    linhas = ["PDF gravado: %s (%d bytes)" % (pdf, len(dados))]
    if not shutil.which("pdftotext"):
        return "\n".join(linhas + ["pdftotext não encontrado: texto não extraído"])
    txt = os.path.splitext(pdf)[0] + ".txt"
    subprocess.run(["pdftotext", "-layout", pdf, txt], check=True,
                   creationflags=0x08000000 if os.name == "nt" else 0)
    linhas.append("Texto: %s" % txt)
    if nome == "cia":
        shutil.copyfile(txt, os.path.join(pasta, "cia-ultima.txt"))
        linhas.append("Cópia: %s" % os.path.join(pasta, "cia-ultima.txt"))
    with open(txt, encoding="utf-8", errors="replace") as fh:
        conteudo = fh.read()
    if not conteudo.strip():
        linhas.append("ATENÇÃO: texto vazio — PDF escaneado; ler as páginas como imagem (pdftoppm)")
    else:
        linhas.append("%d caracteres; leia o .txt com Read" % len(conteudo))
    return "\n".join(linhas)


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
    elif args.acao == "resolver":
        feitas = [i for i in args.ids if atualizar(args.pasta, "pendencias", i, feita=True)]
        print("resolvida(s): %s" % (", ".join(feitas) or "nenhuma (ids não existem)"))
    elif args.acao == "passo":
        for n in args.n:
            marcar(args.pasta, "passos", n, True)
        print("passo(s) %s marcado(s)" % ", ".join(str(n) for n in args.n))
    elif args.acao == "sol-pdf":
        print(sol_pdf(args.pasta, args.id, args.nome))
    else:
        d = ler(args.pasta)
        print(json.dumps({"pendencias": d["pendencias"], "passos": d["passos"],
                          "cia_final": [{"id": e["id"], "medida": e["medida"], "final": e["final"],
                                         "fundamento": e["fundamento"]} for e in texto_cia(d)],
                          "rascunhos_sem_final": [e["id"] for e in d["exigencias"] if not e.get("final")]},
                         ensure_ascii=False, indent=1))
