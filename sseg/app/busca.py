# -*- coding: utf-8 -*-
"""
busca.py — "Buscar nas normas e no banco" do SSEG.exe (versão 1.2, item 1 do PLANO.md).

O trabalho do subagente localizador-normas sem gastar token: acha o trecho e diz arquivo e
linha. Não decide nada — escolher o modelo do banco e dizer se a exigência procede continua com
o analista e o Claude. Ordem e peso das fontes como nas Instruções ("Onde procurar primeiro"):

  banco      banco-notificacoes-padrao.md — o modelo inteiro, com a seção e as ressalvas
  comentada  normas/<rt>.md — transcrição comentada, itens já conferidos
  literal    normas/md/ — extração automática: SÓ LOCALIZA; o PDF de normas/pdf/ fundamenta

Sem acento e sem maiúscula; todos os termos têm de aparecer; "frase entre aspas" é um termo.
"""

import glob
import os
import re
import subprocess
import unicodedata

GRUPOS = [
    ("banco", "Banco de notificações (modelos validados pela chefia)"),
    ("comentada", "Normas comentadas (sseg/normas)"),
    ("literal", "Texto convertido (normas/md) — só localiza: conferir o item no PDF antes de citar"),
]
FORA = {"banco-notificacoes-padrao.md", "README.md"}


# Norma → PDF oficial em sseg/normas/pdf/ (o que fundamenta). Sem PDF na pasta: sem link.
PDF_RT = {"1": "RT CBMRS 01 – Diretrizes Básicas de Segurança Contra Incêndio.pdf",
          "2": "RT CBMRS 02 – Termos e Definições.pdf", "4": "RT CBMRS 04 – Isolamento de Riscos.pdf",
          "10": "RT10.pdf", "11": "RT11.pdf", "12": "RT12.pdf", "14": "RT14.pdf", "15": "RT15.pdf", "17": "RT17.pdf",
          "18": "RT18.pdf", "22": "RT22.pdf", "31": "RT31.pdf"}
PDF_RT5 = {"1": "RTCBMRS 5 parte 1 - 1 2016 - ppci na forma completa.pdf", "7": "RT 05 Parte 07.pdf",
           "8": "RT05P08.pdf"}
PDF_COMENTADA = [  # prefixo do normas/<rt>.md
    ("rt-01-", PDF_RT["1"]), ("rt-02-", PDF_RT["2"]), ("rt-04-", PDF_RT["4"]),
    ("rt-05-parte01", PDF_RT5["1"]), ("rt-05-parte07", PDF_RT5["7"]), ("rt-05-parte08", PDF_RT5["8"]),
    ("rt-10-", "RT10.pdf"),
    ("rt-11-", "RT11.pdf"), ("rt-12-", "RT12.pdf"), ("rt-14-", "RT14.pdf"), ("rt-15-", "RT15.pdf"), ("rt-17-", "RT17.pdf"),
    ("rt-18-", "RT18.pdf"), ("rt-22-", "RT22.pdf"), ("rt-31-", "RT31.pdf"), ("rt-implantacao-sol", "RTISOL.pdf"),
    ("decreto-51803", "DECRETO51803.pdf"), ("lei-complementar-14376", "Lec nº 14.376.pdf"),
    ("in-045-", "IN45.pdf"), ("in-066-", "IN66.pdf"), ("in-067-", "IN67.pdf"), ("it-25-", "IT25P4.pdf"),
]
ITEM = re.compile(r"(?<![\d.,])\d{1,2}(?:\.\d{1,2}){1,4}(?![\d,]|\.\d)")


def pdf_citado(texto):
    """Primeira norma citada num texto (modelo do banco) → nome do PDF, ou None."""
    t = normalizar(texto)
    achados = []
    # "RTCBMRS nº 05, Parte 1.1" (vírgula antes da Parte) e "RT 05 P1.1" (Parte abreviada) também (03/11/2026)
    for m in re.finditer(r"\b(?:rt|resolucao tecnica)\s*(?:cbmrs)?\s*(?:n\.?\s*o?\.?\s*)?0?(\d{1,2})\b(?:\s*,?\s*(?:parte|p\.?)\s*0?(\d))?", t):
        pdf = PDF_RT5.get(m.group(2) or "") if m.group(1) == "5" else PDF_RT.get(m.group(1))
        achados.append((m.start(), pdf))
    for rx, pdf in ((r"\bdecreto\s*(?:estadual\s*)?(?:n\.?\s*o?\.?\s*)?51\.?803", "DECRETO51803.pdf"),
                    (r"\b(?:lc|lei complementar)\s*(?:n\.?\s*o?\.?\s*)?14\.?376", "Lec nº 14.376.pdf"),
                    (r"\bin\s*(?:n\.?\s*o?\.?\s*)?0?(45|66|67)\b", None), (r"\bit\s*37\b", "IT37.pdf"),
                    # "RT de Implantação do SOL-CBMRS" não tem número (2.7.6)
                    (r"\b(?:rt|resolucao tecnica)\s*(?:cbmrs\s*)?(?:de|da)\s*implantacao\b|\brtisol\b", "RTISOL.pdf")):
        for m in re.finditer(rx, t):
            achados.append((m.start(), pdf or "IN%s.pdf" % m.group(1)))
    # IT 25 do CBPMESP (03/11/2026): só a Parte 4 está em normas/pdf. A numeração continua entre as Partes: item 33 a
    # 49 ou Tabela 4.x = Parte 4. Outra Parte citada (ou item de outra Parte) fica sem PDF, para não abrir o errado.
    for m in re.finditer(r"\bit\s*(?:n\.?\s*o?\.?\s*)?25\b(?:\s*/\s*\d{4})?(?:\s*[-\u2013,]?\s*(?:parte|p\.?)\s*0?(\d))?", t):
        parte = m.group(1)
        if not parte:
            n = ITEM.search(t)
            parte = "4" if re.search(r"\btabela\s+4\.", t) or n and n.group(0).split(".")[0] in [str(i) for i in range(33, 50)] else None
        achados.append((m.start(), "IT25P4.pdf" if parte == "4" else None))
    achados = [a for a in sorted(achados) if a[1]]
    return achados[0][1] if achados else None


def pdf_do_resultado(r):
    nome = os.path.basename(r["arquivo"])
    if r["grupo"] == "literal":
        pdf = nome[:-3] + ".pdf"
    elif r["grupo"] == "comentada":
        pdf = next((p for pre, p in PDF_COMENTADA if nome.startswith(pre)), None)
    else:
        pdf = pdf_citado(r["texto"])
    return pdf and "sseg/normas/pdf/" + pdf


# ---- link de item no texto do Claude (2.8.0, pedido do Átila em 02/11/2026) ----
# O programa transforma "item 5.2.2 da RT 01/2024" num link que abre o PDF oficial na página do item.
# A versão de cada PDF sai do nome da transcrição comentada (rt-01-2024-... → 2024): citação de outro ano
# abre o PDF com aviso, porque a vigência é pela data de protocolo e quem escolhe a versão é o analista.
TABELA = re.compile(r"\btabela\s+((?:[a-z]\.)?\d{1,2}[a-z]?(?:\.[a-z]?\d{1,2})*)\b")  # e "Tabela 4.A1" (IT 25)  # "Tabela L.1" do Anexo L (03/11/2026)
ANEXO = re.compile(r"\banexo\s+[\"\u201c\u201d]?([a-z])[\"\u201c\u201d]?(?![a-z])")
ARTIGO = re.compile(r"\bart(?:igo)?\.?\s*(\d{1,3})\s*[o\u00ba\u00b0]?(?!\d)")


def ano_do_pdf(pdf, clone):
    """Ano da versão do PDF, tirado do normas/<rt>-<ano>-....md que aponta para ele; sem transcrição: None."""
    pre = next((pre for pre, p in PDF_COMENTADA if p == pdf), None)
    if not pre:
        return None
    for arq in glob.glob(os.path.join(clone, "sseg", "normas", pre + "*.md")):
        m = re.search(r"-(\d{4})-", os.path.basename(arq)[len(pre) - 1:])
        if m:
            return m.group(1)
    return None


def _pdf_rt_novo(rotulo, clone):
    """RT que entrou em normas/pdf depois deste .exe (03/11/2026): RTnn.pdf no clone já abre pelo link, sem versão
    nova do programa. Só o nome padrão RTnn.pdf; a RT 05 (por Parte) fica no mapa fixo."""
    m = re.search(r"\b(?:rt|resolucao tecnica)\s*(?:cbmrs)?\s*(?:n\.?\s*o?\.?\s*)?0?(\d{1,2})\b", normalizar(rotulo))
    if not m or m.group(1) == "5":
        return None
    for nome in ("RT%s.pdf" % m.group(1), "RT%02d.pdf" % int(m.group(1))):
        if os.path.isfile(os.path.join(clone, "sseg", "normas", "pdf", nome)):
            return nome
    return None


def norma_status(rotulo, clone):
    """{pdf, aviso}: pdf None = a norma não está em normas/pdf (sinal de norma a incorporar)."""
    pdf = pdf_citado(rotulo) or _pdf_rt_novo(rotulo, clone)
    if not pdf or not os.path.isfile(os.path.join(clone, "sseg", "normas", "pdf", pdf)):
        return {"pdf": None, "aviso": "Esta norma não está em normas/pdf — sem PDF para abrir (vale incorporar)."}
    t = normalizar(rotulo)
    m = re.search(r"(?:rt|resolucao tecnica|\bit)[^/]{0,40}?/\s*(\d{4})\b", t) or re.search(r"\bparte\s*0?\d{1,2}\s*/\s*(\d{4})\b", t)
    ano, ano_pdf = (m.group(1) if m else None), ano_do_pdf(pdf, clone)
    if ano and ano_pdf and ano != ano_pdf:
        return {"pdf": pdf, "aviso": "O texto cita a versão de %s; o PDF da pasta é a de %s. Confira qual vale pela data de protocolo." % (ano, ano_pdf)}
    return {"pdf": pdf, "aviso": None}


_LINHAS = {}


def _paginas_linhas(caminho, pdftotext="pdftotext"):
    if caminho not in _LINHAS:
        out = subprocess.run([pdftotext, "-enc", "UTF-8", caminho, "-"], capture_output=True,
                             creationflags=0x08000000 if os.name == "nt" else 0, timeout=60).stdout
        _LINHAS[caminho] = [[(normalizar(l).strip(), l.strip()) for l in p.splitlines()] for p in out.decode("utf-8", "replace").split("\f")]
    return _LINHAS[caminho]


def pagina_item(caminho, rotulo, pdftotext="pdftotext"):
    """(página 1-based, assunto) do item ou tabela do rótulo. Prefere a página em que o número ABRE a linha
    (título do item) fora do sumário; depois qualquer menção; não achou → (1, ""). Só aproxima."""
    t = normalizar(rotulo).split(" \u00b7 ")[0]  # "5.2.2 · RT 01/2024": o item é só a parte antes do ponto
    m, tab, art = ITEM.search(t), TABELA.search(t), ARTIGO.search(t)
    anx = ANEXO.search(t) if not m and not tab and not art else None
    if not m and not tab and not art and not anx:
        return 1, ""
    try:
        pags = _paginas_linhas(caminho, pdftotext)
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    if anx:  # "Anexo L": a página do título do anexo (linha só com ele), não as menções no texto
        cab = re.compile(r"^anexo\s+[\"\u201c\u201d]?" + anx.group(1) + r"[\"\u201c\u201d]?\s*$()")
        meio = re.compile(r"\banexo\s+[\"\u201c\u201d]?" + anx.group(1) + r"(?![a-z])")
    elif art and not m and not tab:
        cab = re.compile(r"^art\.?\s*" + art.group(1) + r"\s*[o\u00ba\u00b0]?(?!\d)\s*[-\u2013.]?\s*(.*)")
        meio = re.compile(r"\bart\.?\s*" + art.group(1) + r"(?!\d)")
    elif tab:
        cab = re.compile(r"^tabela\s+" + re.escape(tab.group(1)) + r"(?![\da-z.])")
        meio = re.compile(r"\btabela\s+" + re.escape(tab.group(1)) + r"(?![\da-z.])")
    else:
        cab = re.compile(r"^" + re.escape(m.group(0)) + r"\.?(?![\d.])\s*(.*)")
        meio = re.compile(r"(?<![\d.])" + re.escape(m.group(0)) + r"(?![\d])")
    sumario = lambda linhas: sum(1 for l in linhas if re.search(r"\.{5,}|…{3,}", l)) >= 5 or any(l in ("sumario", "indice") for l in linhas)  # noqa: E731
    # tabela: primeiro o título com separador ("Tabela L.1 – ...", "Tabela 4: ..."), que a lista de tabelas e a
    # menção quebrada no começo da linha ("Tabela 1, do Anexo A") não têm; não achou, o critério de antes
    cabs = [cab]
    if tab:
        cabs.insert(0, re.compile(cab.pattern + r"\s*[-\u2013\u2014:]\s*(.*)"))
    for i, linhas, cab in ((i, l, c) for c in cabs for i, l in enumerate(pags)):
        if sumario([n for n, _o in linhas]):
            continue
        for n, orig in linhas:
            achou = cab.match(n)
            if achou:
                # o texto normalizado tem o mesmo tamanho do original só sem acento: corta o original na mesma posição
                ini = achou.start(1) if achou.groups() and achou.group(1) else 0
                assunto = orig[ini:ini + 90] if len(orig) == len(n) else (achou.group(1) if achou.groups() else n)[:90]
                return i + 1, assunto.strip(" -–:")
    for i, linhas in enumerate(pags):
        if any(meio.search(n) for n, _o in linhas):
            return i + 1, ""
    return 1, ""


_PAGINAS = {}


def paginas(caminho, pdftotext="pdftotext"):
    """Texto de cada página do PDF, normalizado (guardado: cada PDF é lido uma vez)."""
    if caminho not in _PAGINAS:
        out = subprocess.run([pdftotext, "-enc", "UTF-8", caminho, "-"], capture_output=True,
                             creationflags=0x08000000 if os.name == "nt" else 0, timeout=60).stdout
        _PAGINAS[caminho] = [re.sub(r"\s+", " ", normalizar(p)) for p in out.decode("utf-8", "replace").split("\f")]
    return _PAGINAS[caminho]


def pagina(caminho, consulta, texto="", pdftotext="pdftotext"):
    """Página (1-based) mais provável do trecho: o item citado junto com os termos, depois só os
    termos, depois só o item; não achou → 1. Só aproxima: quem confere é o analista."""
    try:
        pags = paginas(caminho, pdftotext)
    except (OSError, subprocess.SubprocessError):
        return 1
    ts = termos(consulta)
    m = ITEM.search(texto)
    item = re.compile(r"(?<![\d.])" + re.escape(m.group(0)) + r"(?![\d])") if m else None
    testes = ([lambda p: item.search(p) and all(t.search(p) for t in ts)] if item else []) + \
             [lambda p: all(t.search(p) for t in ts)] + ([lambda p: item.search(p)] if item else [])
    for teste in testes:
        for i, p in enumerate(pags):
            if teste(p):
                return i + 1
    return 1


def normalizar(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def termos(consulta):
    """Cada termo vira uma expressão; número não casa no meio de outro ("5 m" não acha "15 m")."""
    out = []
    for t in re.findall(r'"[^"]+"|\S+', consulta):
        t = normalizar(t.strip('"')).strip()
        if t:
            out.append(re.compile(("(?<![\\d.,])" if t[0].isdigit() else "") + re.escape(t)))
    return out


def _ler(caminho):
    with open(caminho, encoding="utf-8", errors="replace") as fh:
        return fh.read().splitlines()


def carregar(clone):
    """{grupo: [(arquivo relativo, linhas)]} — relido a cada busca (os arquivos são pequenos)."""
    base = os.path.join(clone, "sseg", "normas")
    rel = lambda p: os.path.relpath(p, clone).replace("\\", "/")  # noqa: E731
    banco = os.path.join(base, "banco-notificacoes-padrao.md")
    return {
        "banco": [(rel(banco), _ler(banco))] if os.path.exists(banco) else [],
        "comentada": [(rel(p), _ler(p)) for p in sorted(glob.glob(os.path.join(base, "*.md")))
                      if os.path.basename(p) not in FORA and not os.path.basename(p).startswith("conferencia-")],
        "literal": [(rel(p), _ler(p)) for p in sorted(glob.glob(os.path.join(base, "md", "*.md")))],
    }


def _secao(linhas, i):
    for j in range(i, -1, -1):
        if re.match(r"^#{2,4} ", linhas[j]):
            return linhas[j].lstrip("#").strip()
    return ""


def _blocos_banco(linhas):
    """Cada modelo: a linha "- ..." e as ressalvas logo abaixo ("  > ..."). Para no Histórico."""
    i = 0
    while i < len(linhas):
        if linhas[i].startswith("## Histórico"):
            return
        if linhas[i].startswith("- "):
            j = i + 1
            while j < len(linhas) and re.match(r"^\s+(>|\S)", linhas[j]) and not linhas[j].startswith("- "):
                j += 1
            yield i, linhas[i:j]
            i = j
        else:
            i += 1


def buscar(indice, consulta, limite=80):
    """[{grupo, arquivo, linha (1-based), secao, texto, copiar}] na ordem banco → comentada → literal."""
    ts = termos(consulta)
    if not ts:
        return []
    out = []
    for arq, linhas in indice.get("banco", []):
        for i, bloco in _blocos_banco(linhas):
            texto = "\n".join(bloco)
            if all(t.search(normalizar(texto)) for t in ts):
                modelo = bloco[0][2:].strip()
                out.append({"grupo": "banco", "arquivo": arq, "linha": i + 1, "secao": _secao(linhas, i),
                            "texto": texto, "copiar": modelo})
    for grupo in ("comentada", "literal"):
        for arq, linhas in indice.get(grupo, []):
            ultimo = -10
            baixas = [normalizar(l) for l in linhas]
            for i in range(len(linhas)):
                janela = " ".join(baixas[i:i + 3])  # termo pode quebrar de linha
                if i - ultimo > 3 and all(t.search(janela) for t in ts) and any(t.search(baixas[i]) for t in ts):
                    ultimo = i
                    ini, fim = max(0, i - 1), min(len(linhas), i + 4)
                    trecho = "\n".join(l for l in linhas[ini:fim] if l.strip())
                    out.append({"grupo": grupo, "arquivo": arq, "linha": i + 1, "secao": _secao(linhas, i),
                                "texto": trecho, "copiar": "%s\n(%s:%d)" % (trecho, arq, i + 1)})
    ordem = {g: k for k, (g, _) in enumerate(GRUPOS)}
    out.sort(key=lambda r: ordem[r["grupo"]])
    for r in out[:limite]:
        r["pdf"] = pdf_do_resultado(r)
    return out[:limite]
