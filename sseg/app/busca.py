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
import unicodedata

GRUPOS = [
    ("banco", "Banco de notificações (modelos validados pela chefia)"),
    ("comentada", "Normas comentadas (sseg/normas)"),
    ("literal", "Texto convertido (normas/md) — só localiza: conferir o item no PDF antes de citar"),
]
FORA = {"banco-notificacoes-padrao.md", "README.md"}


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
    return out[:limite]
