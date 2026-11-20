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
    d.setdefault("marcas", {})       # "pre_analise": data da pré-análise mandada ao Claude (o quadro encolhe)
    # 2.14.0 (ideia do Átila, 18/11/2026): o que foi batido no chat aparece no checklist com cor. Chave = a mesma de
    # "itens" ("medida|item") ou "passo:N"; {estado: ok | exigencia | ver, nota, exig (id na coluna CIA), quando}.
    # É a leitura do Claude: a marca do analista em "itens"/"passos" manda por cima.
    d.setdefault("vistos", {})
    return d


def gravar(pasta, d):
    """Grava inteiro, por arquivo temporário e troca (a janela lê enquanto o Claude escreve)."""
    os.makedirs(pasta, exist_ok=True)
    d["alterado"] = time.time()
    fd, tmp = tempfile.mkstemp(prefix=".analise-", suffix=".json", dir=pasta)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    # Windows: a janela do SSEG.exe lendo o analise.json na hora da troca dá "Acesso negado" (WinError 5, 51398,
    # 20/11/2026: o comando do Claude caiu e o .analise-*.json ficou largado na pasta). Tenta de novo por até 3 s.
    for i in range(16):
        try:
            os.replace(tmp, caminho(pasta))
            break
        except PermissionError:
            if i == 15:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
                raise
            time.sleep(0.2)
    return d


def _novo_id(lista, prefixo):
    n = max([int(x["id"][len(prefixo):]) for x in lista if str(x.get("id", "")).startswith(prefixo)] + [0])
    return "%s%d" % (prefixo, n + 1)


# palavras que aparecem em quase toda pergunta de análise e não dizem o assunto
_COMUNS = {"planta", "area", "areas", "cada", "ainda", "como", "qual", "quais", "voce", "quer", "existe", "dentro",
           "traz", "esta", "isso", "para", "pela", "pelo", "processo", "analise", "sobre", "algum", "alguma", "foram",
           "ficou", "continua", "continuam", "tambem", "informada", "informado", "aparece"}


def _palavras(t):
    import re
    import unicodedata
    t = unicodedata.normalize("NFD", t or "").encode("ascii", "ignore").decode().lower()
    divisoes = set(re.findall(r"\b[a-m]-\d+\b", t))  # J-3, D-1: o assunto, não número solto
    t = re.sub(r"\b[a-m]-\d+\b", " ", t)
    return divisoes | {w for w in re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?", t)
                       if w not in _COMUNS and (len(w) > 3 or (len(w) > 1 and any(c.isdigit() for c in w)))}


def parecida(d, texto):
    """Pendência já registrada (aberta ou respondida) sobre o mesmo assunto. Nas conversas de 17/10/2026 a mesma
    pergunta entrou 2 ou 3 vezes (pelo sseg.py e pelo bloco de perguntas, com outras palavras). Mesmo assunto =
    a menor das duas tem metade das palavras na outra (3 em comum) ou 2/3 delas (2 em comum)."""
    novo = _palavras(texto)
    melhor, nota = None, 0.0
    for p in d["pendencias"]:
        velho = _palavras(p["texto"])
        if not (novo and velho):
            continue
        comum = len(novo & velho)
        ov = comum / float(min(len(novo), len(velho)))
        if ((comum >= 3 and ov >= 0.5) or (comum >= 2 and ov >= 0.66)) and ov > nota:
            melhor, nota = p, ov
    return melhor


def pendencia(pasta, texto, origem="claude"):
    d = ler(pasta)
    if origem == "claude":
        ja = parecida(d, texto)
        if ja:
            return dict(ja, repetida=True)
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


def descartar(pasta, ids):
    """Tira da coluna CIA o rascunho que o Claude gravou e que não vale mais. Item com texto final
    salvo fica: quem salvou foi o analista, e quem apaga é ele (botão "excluir")."""
    d = ler(pasta)
    por_id = {e["id"]: e for e in d["exigencias"]}
    fora, salvos, nao_ha = [], [], []
    for i in ids:
        e = por_id.get(i)
        if e is None:
            nao_ha.append(i)
        elif (e.get("final") or "").strip():
            salvos.append(i)
        else:
            fora.append(i)
    if fora:
        d["exigencias"] = [e for e in d["exigencias"] if e["id"] not in fora]
        gravar(pasta, d)
    partes = ["descartado(s): %s" % (", ".join(fora) or "nenhum")]
    if salvos:
        partes.append("NÃO descartado(s), têm texto final salvo pelo analista: %s (ele exclui no item)" % ", ".join(salvos))
    if nao_ha:
        partes.append("não existe(m): %s" % ", ".join(nao_ha))
    return "; ".join(partes)


def marcar(pasta, grupo, chave, valor):
    """grupo "passos" (chave = nº do passo), "itens" (chave = "medida|item") ou "marcas" (estado da
    janela, ex.: "pre_analise"). valor None desmarca."""
    d = ler(pasta)
    if valor in (None, False, ""):
        d[grupo].pop(str(chave), None)
    else:
        d[grupo][str(chave)] = valor
    gravar(pasta, d)
    return d


VISTO = {"ok": "conforme", "exigencia": "vira exigência", "ver": "falta ver", "ia": "palpite da IA local"}


def visto(pasta, chave, estado, nota="", exig="", palpite=None):
    """O Claude marca o resultado de um item do checklist que foi conferido (ou que ficou pendente) no chat.
    estado None/"" apaga a marca."""
    d = ler(pasta)
    if not estado:
        d["vistos"].pop(chave, None)
    elif estado not in VISTO:
        raise ValueError("estado inválido: %r (use ok, exigencia ou ver)" % estado)
    else:
        d["vistos"][chave] = {"estado": estado, "nota": (nota or "").strip()[:300], "exig": exig or "", "quando": time.time()}
        if palpite:   # 2.14.1: azul = depende do palpite nº N do quadro azul (reanálise), ainda sem a sua conferência
            d["vistos"][chave]["palpite"] = int(palpite)
    gravar(pasta, d)
    return d


def _checklist(pasta):
    """[(código, chave, rótulo)] dos itens que o Claude pode marcar: P<n> (passos) e M<medida>.<item> (Anexo L), na
    mesma ordem da janela. Monta pelo processo.py do app (sseg/app), que é quem desenha o checklist."""
    import sys
    clone = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app = os.path.join(clone, "sseg", "app")
    if app not in sys.path:
        sys.path.insert(0, app)
    import processo
    j = processo.montar(clone, pasta)
    out = [("P%d" % p["n"], "passo:%d" % p["n"], "%s" % p["t"]) for p in j["passos"]]
    for a, m in enumerate(j["medidas"], 1):
        for b, i in enumerate(m["itens"], 1):
            out.append(("M%d.%d" % (a, b), m["nome"] + "|" + i, "%s — %s" % (m["nome"], i)))
    return out


def chave_de(pasta, codigo):
    for c, k, r in _checklist(pasta):
        if c.upper() == codigo.strip().upper():
            return k, r
    raise ValueError("item %r não existe no checklist deste processo (veja: sseg.py analise itens)" % codigo)


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
    p.add_argument("--item", default="", help="código do item do checklist (ex.: M3.2): fica vermelho, ligado a esta exigência")
    p = sub.add_parser("rascunho", help="rascunho para um item que já existe na coluna CIA (pedido pelo analista)")
    p.add_argument("id", help="id do item (ex.: e3)")
    p.add_argument("texto", help='texto, ou "-" para ler da entrada (heredoc)')
    p.add_argument("--medida", default="")
    p.add_argument("--fundamento", default="")
    p = sub.add_parser("resolver", help="marca pendências como resolvidas (ex.: p2 p3) — sai do topo do checklist")
    p.add_argument("ids", nargs="+")
    p = sub.add_parser("passo", help="marca passos do checklist (1 a 16), um ou vários: passo 1 3 4 5")
    p.add_argument("n", type=int, nargs="+")
    p = sub.add_parser("descartar", help="tira da coluna CIA um rascunho sem texto final salvo (ex.: e2); o salvo é do analista")
    p.add_argument("ids", nargs="+")
    sub.add_parser("itens", help="lista o checklist com os códigos (P6, M3.2) e o que já está marcado")
    p = sub.add_parser("visto", help="resultado de itens do checklist conferidos no chat: visto ok M3.1 M3.2 --nota ...")
    p.add_argument("estado", choices=["ok", "exigencia", "ver", "ia", "apagar"])
    p.add_argument("codigos", nargs="+", help="códigos de sseg.py analise itens (P6, M3.2)")
    p.add_argument("--nota", default="", help="por quê, em uma linha (aparece ao passar o mouse)")
    p.add_argument("--palpite", type=int, help='com "ia": nº do palpite no quadro azul')
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
        if p.get("repetida"):
            print("NÃO registrada: parecida com %s (\"%s\")%s. Use essa; não pergunte de novo."
                  % (p["id"], p["texto"][:120], ("; o analista já respondeu: " + p["resposta"]) if p.get("resposta") else
                     "; ainda aberta"))
        else:
            print("pendência %s registrada" % p["id"])
    elif args.acao == "exigencia":
        k = chave_de(args.pasta, args.item)[0] if args.item else ""
        e = exigencia(args.pasta, args.texto, args.medida, args.fundamento)
        if k:
            visto(args.pasta, k, "exigencia", (args.texto.strip().lstrip("- ").splitlines() or [""])[0][:200], e["id"])
        print("exigência %s registrada como rascunho (o analista salva o texto final)%s" % (e["id"], "; item %s em vermelho" % args.item if k else ""))
    elif args.acao == "itens":
        d = ler(args.pasta)
        for c, k, r in _checklist(args.pasta):
            an = d["passos"].get(k[6:]) if k.startswith("passo:") else d["itens"].get(k)
            v = d["vistos"].get(k)
            marca = (["analista: %s" % ("feito" if an is True else an)] if an else []) + (["seu: %s" % VISTO[v["estado"]]] if v else [])
            print("%-6s %s%s" % (c, r, "   [%s]" % "; ".join(marca) if marca else ""))
    elif args.acao == "visto":
        feitos = []
        for c in args.codigos:
            k, _r = chave_de(args.pasta, c)
            visto(args.pasta, k, None if args.estado == "apagar" else args.estado, args.nota, palpite=args.palpite)
            if k.startswith("passo:") and args.estado in ("ok", "exigencia"):
                marcar(args.pasta, "passos", k[6:], True)   # conferido = passo feito
            feitos.append(c)
        print("%s: %s" % ("apagado(s)" if args.estado == "apagar" else VISTO[args.estado], ", ".join(feitos)))
    elif args.acao == "resolver":
        feitas = [i for i in args.ids if atualizar(args.pasta, "pendencias", i, feita=True)]
        print("resolvida(s): %s" % (", ".join(feitas) or "nenhuma (ids não existem)"))
    elif args.acao == "passo":
        for n in args.n:
            marcar(args.pasta, "passos", n, True)
        print("passo(s) %s marcado(s)" % ", ".join(str(n) for n in args.n))
    elif args.acao == "descartar":
        print(descartar(args.pasta, args.ids))
    elif args.acao == "sol-pdf":
        print(sol_pdf(args.pasta, args.id, args.nome))
    else:
        d = ler(args.pasta)
        print(json.dumps({"pendencias": d["pendencias"], "passos": d["passos"],
                          # tamanho e quebras já contados (04/11/2026): o revisor-cia contava com python solto, barrado na janela
                          "cia_final": [{"id": e["id"], "medida": e["medida"], "final": e["final"],
                                         "fundamento": e["fundamento"], "caracteres": len(e["final"]),
                                         "quebras_de_linha": e["final"].count("\n"),
                                         "acima_de_1950": len(e["final"]) > 1950} for e in texto_cia(d)],
                          "rascunhos_sem_final": [e["id"] for e in d["exigencias"] if not e.get("final")]},
                         ensure_ascii=False, indent=1))
