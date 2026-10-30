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
          "10": "RT10.pdf", "11": "RT11.pdf", "12": "RT12.pdf", "14": "RT14.pdf", "17": "RT17.pdf",
          "18": "RT18.pdf", "22": "RT22.pdf", "31": "RT31.pdf"}
PDF_RT5 = {"1": "RTCBMRS 5 parte 1 - 1 2016 - ppci na forma completa.pdf", "7": "RT 05 Parte 07.pdf",
           "8": "RT05P08.pdf"}
PDF_COMENTADA = [  # prefixo do normas/<rt>.md
    ("rt-01-", PDF_RT["1"]), ("rt-02-", PDF_RT["2"]), ("rt-04-", PDF_RT["4"]),
    ("rt-05-parte01", PDF_RT5["1"]), ("rt-05-parte07", PDF_RT5["7"]), ("rt-05-parte08", PDF_RT5["8"]),
    ("rt-10-", "RT10.pdf"),
    ("rt-11-", "RT11.pdf"), ("rt-12-", "RT12.pdf"), ("rt-14-", "RT14.pdf"), ("rt-17-", "RT17.pdf"),
    ("rt-18-", "RT18.pdf"), ("rt-22-", "RT22.pdf"), ("rt-31-", "RT31.pdf"), ("rt-implantacao-sol", "RTISOL.pdf"),
    ("decreto-51803", "DECRETO51803.pdf"), ("lei-complementar-14376", "Lec nº 14.376.pdf"),
    ("in-045-", "IN45.pdf"), ("in-066-", "IN66.pdf"), ("in-067-", "IN67.pdf"),
]
ITEM = re.compile(r"(?<![\d.,])\d{1,2}(?:\.\d{1,2}){1,4}(?![\d,]|\.\d)")


def pdf_citado(texto):
    """Primeira norma citada num texto (modelo do banco) → nome do PDF, ou None."""
    t = normalizar(texto)
    achados = []
    for m in re.finditer(r"\b(?:rt|resolucao tecnica)\s*(?:cbmrs)?\s*(?:n\.?\s*o?\.?\s*)?0?(\d{1,2})\b(?:\s*parte\s*0?(\d))?", t):
        pdf = PDF_RT5.get(m.group(2) or "") if m.group(1) == "5" else PDF_RT.get(m.group(1))
        achados.append((m.start(), pdf))
    for rx, pdf in ((r"\bdecreto\s*(?:estadual\s*)?(?:n\.?\s*o?\.?\s*)?51\.?803", "DECRETO51803.pdf"),
                    (r"\b(?:lc|lei complementar)\s*(?:n\.?\s*o?\.?\s*)?14\.?376", "Lec nº 14.376.pdf"),
                    (r"\bin\s*(?:n\.?\s*o?\.?\s*)?0?(45|66|67)\b", None), (r"\bit\s*37\b", "IT37.pdf"),
                    # "RT de Implantação do SOL-CBMRS" não tem número (2.7.6)
                    (r"\b(?:rt|resolucao tecnica)\s*(?:cbmrs\s*)?(?:de|da)\s*implantacao\b|\brtisol\b", "RTISOL.pdf")):
        for m in re.finditer(rx, t):
            achados.append((m.start(), pdf or "IN%s.pdf" % m.group(1)))
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
