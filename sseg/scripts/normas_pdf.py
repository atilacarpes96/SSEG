#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normas_pdf.py — achar trecho e página nos PDFs oficiais de sseg/normas/pdf/ (17/10/2026).

POR QUÊ
-------
Nas conversas de análise de 16 e 17/10/2026 o Claude extraía o PDF da norma por conta própria a cada
processo: `pdftotext` do Git (Xpdf, texto sem acento), arquivo temporário gravado na pasta do processo
ou fora do clone, várias tentativas até achar a página da tabela e `pdftoppm` com a página errada.
Aqui é um comando só, sempre com o Poppler, em UTF-8, com o texto guardado em cache na pasta
temporária do sistema (nunca na pasta do processo nem no clone).

USO
---
  python sseg/scripts/sseg.py norma decreto --tabela 6J.2     # página da tabela + imagem para ler
  python sseg/scripts/sseg.py norma rt14 --busca "risco médio" # trechos com a página
  python sseg/scripts/sseg.py norma rt11 --pagina 12           # imagem de uma página
  python sseg/scripts/sseg.py norma --listar                   # nomes aceitos

A imagem sai em <temp>/sseg-paginas/; leia com Read. O texto localiza, a imagem fundamenta
(trava nº 2: contagem de medidas nunca sai do texto extraído).
"""

import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
PDFS = os.path.normpath(os.path.join(AQUI, "..", "normas", "pdf"))
CACHE = os.path.join(tempfile.gettempdir(), "sseg-paginas")
# duas colunas: o -layout embaralha (Instruções do projeto, "Onde procurar primeiro")
DUAS_COLUNAS = ("rtisol", "rt18", "rt11", "it37", "rt05p08")
APELIDOS = {"decreto": "DECRETO51803", "anexob": "DECRETO51803", "rt01": "RT CBMRS 01", "rt1": "RT CBMRS 01",
            "rt02": "RT CBMRS 02", "rt2": "RT CBMRS 02", "rt04": "RT CBMRS 04", "rt4": "RT CBMRS 04",
            "rt05p07": "RT 05 Parte 07", "rt5p7": "RT 05 Parte 07", "rt05p01": "RTCBMRS 5 parte 1",
            "rt5p1": "RTCBMRS 5 parte 1", "rt05p08": "RT05P08", "rt5p8": "RT05P08", "lei": "Lec",
            "lc14376": "Lec", "isol": "RTISOL"}


def _chave(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)


def pdfs():
    return sorted(glob.glob(os.path.join(PDFS, "*.pdf")))


def achar_pdf(nome):
    """'decreto', 'rt14', 'RT 05 Parte 07', 'it37'... → caminho do PDF. Ambíguo ou ausente: SystemExit."""
    k = _chave(nome)
    k = _chave(APELIDOS.get(k, nome))
    todos = pdfs()
    exatos = [p for p in todos if _chave(os.path.splitext(os.path.basename(p))[0]) == k]
    if exatos:
        return exatos[0]
    parecidos = [p for p in todos if k and k in _chave(os.path.basename(p))]
    if len(parecidos) == 1:
        return parecidos[0]
    nomes = ", ".join(os.path.basename(p) for p in (parecidos or todos))
    raise SystemExit("Norma '%s' %s. PDFs: %s. Norma que falta: pedir o PDF ao analista."
                     % (nome, "ambígua" if parecidos else "não está em normas/pdf/", nomes))


def _poppler(prog):
    """O pdftotext do Poppler, não o Xpdf que vem com o Git: a pasta do pdftoppm (o Git não traz pdftoppm)."""
    base = shutil.which("pdftoppm")
    if base:
        cand = os.path.join(os.path.dirname(base), prog + (".exe" if os.name == "nt" else ""))
        if os.path.exists(cand):
            return cand
    exe = shutil.which(prog)
    if not exe:
        raise SystemExit("%s não encontrado: instale o Poppler (Configuração → Programas no SSEG.exe)." % prog)
    return exe


def paginas_texto(pdf, layout=None):
    """Lista com o texto de cada página (UTF-8), guardada em cache pela data do PDF."""
    nome = _chave(os.path.splitext(os.path.basename(pdf))[0])
    if layout is None:
        layout = not any(nome.startswith(d) for d in DUAS_COLUNAS)
    h = hashlib.md5(("%s|%s|%s" % (pdf, os.path.getmtime(pdf), layout)).encode()).hexdigest()[:12]
    arq = os.path.join(CACHE, "%s-%s.txt" % (nome, h))
    if not os.path.exists(arq):
        os.makedirs(CACHE, exist_ok=True)
        cmd = [_poppler("pdftotext"), "-enc", "UTF-8"] + (["-layout"] if layout else []) + [pdf, arq + ".tmp"]
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        os.replace(arq + ".tmp", arq)
    with open(arq, encoding="utf-8", errors="replace") as fh:
        return fh.read().split("\f")


def renderizar(pdf, pagina, dpi=110):
    os.makedirs(CACHE, exist_ok=True)
    base = os.path.join(CACHE, "%s-p%d" % (_chave(os.path.splitext(os.path.basename(pdf))[0]), pagina))
    for f in glob.glob(base + "*.png"):
        return f
    subprocess.run([_poppler("pdftoppm"), "-f", str(pagina), "-l", str(pagina), "-r", str(dpi), "-png", pdf, base],
                   check=True, capture_output=True, timeout=120)
    achados = glob.glob(base + "*.png")
    if not achados:
        raise SystemExit("pdftoppm não gerou a imagem da página %d." % pagina)
    return achados[0]


def _sem_acento(s):
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()


def buscar(pdf, termo, contexto=2, maximo=15):
    """Trechos com o termo (sem diferença de acento e maiúscula), com página e linhas em volta."""
    alvo = _sem_acento(termo)
    saida = []
    for n, pag in enumerate(paginas_texto(pdf), 1):
        linhas = pag.splitlines()
        plano = [_sem_acento(l) for l in linhas]
        for i, l in enumerate(plano):
            if alvo in l:
                ini, fim = max(0, i - contexto), min(len(linhas), i + contexto + 1)
                saida.append((n, "\n".join(x.rstrip() for x in linhas[ini:fim])))
                if len(saida) >= maximo:
                    return saida
    return saida


def pagina_da_tabela(pdf, tabela):
    """Páginas cujo texto tem 'TABELA <tabela>' como título (6J.2, 5, 7...). Mais provável primeiro."""
    t = re.escape(tabela.upper().replace(" ", "")).replace(r"\.", r"\s*\.\s*")
    rx = re.compile(r"TABELA\s*%s(?![\d.])" % t)
    titulo = re.compile(r"^\s*TABELA\s*%s\s*(?:[-–:].*)?$" % t)
    achadas = []
    for n, pag in enumerate(paginas_texto(pdf, layout=True), 1):
        txt = _sem_acento(pag).upper()
        if not rx.search(txt):
            continue
        # o título da tabela é uma linha só dele ("TABELA 5"); "Conforme Tabela 5" no corpo é citação
        peso = 2 if any(titulo.match(l) for l in txt.splitlines()) else 0
        achadas.append((-peso, n))
    return [n for _p, n in sorted(achadas)]


def args_parser(sp):
    sp.add_argument("norma", nargs="?", help="decreto, rt14, rt05p07, it37... (--listar mostra todos)")
    sp.add_argument("--tabela", help="título da tabela (5, 6J.2, 7, 2...): devolve a página e a imagem")
    sp.add_argument("--busca", help="texto a localizar (sem diferença de acento): devolve trechos com a página")
    sp.add_argument("--pagina", type=int, help="gera a imagem desta página")
    sp.add_argument("--listar", action="store_true")


def principal(a):
    if a.listar or not a.norma:
        print("PDFs em normas/pdf/ (nome ou apelido: %s):" % ", ".join(sorted(APELIDOS)))
        for p in pdfs():
            print("  " + os.path.basename(p))
        return
    pdf = achar_pdf(a.norma)
    print("Norma: %s" % os.path.basename(pdf))
    if a.busca:
        achados = buscar(pdf, a.busca)
        if not achados:
            print("'%s' não aparece no texto extraído (ausência aqui não prova ausência na norma: tabela e "
                  "expoente se desalinham). Tente outra palavra ou leia a página na imagem." % a.busca)
        for n, trecho in achados:
            print("\n--- página %d ---\n%s" % (n, trecho))
    if a.tabela:
        pags = pagina_da_tabela(pdf, a.tabela)
        if not pags:
            print("Tabela %s não achada pelo título. Use --busca com uma palavra da tabela." % a.tabela)
        else:
            print("Tabela %s: página %d%s." % (a.tabela, pags[0], (" (citada também em %s)" % ", ".join(map(str, pags[1:5])))
                                                if len(pags) > 1 else ""))
            print("Imagem para ler (Read): %s" % renderizar(pdf, pags[0]))
            print("Se a tabela continua na página seguinte: --pagina %d" % (pags[0] + 1))
    if a.pagina:
        print("Imagem da página %d (Read): %s" % (a.pagina, renderizar(pdf, a.pagina)))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    args_parser(ap)
    principal(ap.parse_args())
