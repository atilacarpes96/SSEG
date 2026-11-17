#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cotas_desenho.py — prancha com o texto convertido em desenho (o PDF não tem texto: cada letra virou traço). Acha as
cotas pela geometria, recorta cada uma já na horizontal e deixa a IA local transcrever, duas vezes, para o
palpite_local procurar o valor que a exigência pede. Sem IA aqui: quem pergunta ao modelo é quem chama (ler()).

COMO ACHA A COTA (provas de 16 e 17/11/2026 nas pranchas do 44312, E:\\ia-local\\leitura\\rodada-17-11)
  - Traço curto (< 8 pt) é pedaço de letra; os pedaços a menos de EPS pt uns dos outros viram um bloco de texto.
  - Bloco "de cota": tem uma linha longa (>= 8 pt) quase paralela logo ao lado (até meia altura + 4 pt) e o centro
    dentro do comprimento dela. O ângulo do bloco encaixa no da linha (número curto entorta a medida do bloco:
    o 1215 saiu 4-5° torto e escapava).
  - Duas leituras (recorte justo e recorte com folga). A comparação com o valor esperado é feita aqui, no código,
    pelos algarismos: 12,15 m = 12.15 = 1215 cm. Pergunta sim/não ao modelo foi frouxa (disse "sim" a 12,50).

CACHE ao lado do PDF: <prancha>.cotas.json (candidatos e leituras por modelo). A leitura de uma prancha custa minutos;
com o cache, a segunda exigência na mesma prancha e a rodada seguinte não releem nada.

Pede PyMuPDF (pip install pymupdf==1.28.2; o instalador do SSEG já instala).
"""
import json
import math
import os
import re

EPS = 4.5           # distância (pt) para juntar os traços de uma letra/número
TRACO = 8.0         # abaixo disto o traço é pedaço de letra; acima, linha do desenho
MIN_PONTOS = 6
TOL_ANG = 10.0      # graus entre o bloco e a linha de cota
ZOOM_A, ZOOM_B, FOLGA_B = 10, 6, 1.8
ALT_A = 64          # px de altura da 1ª leitura: gemma 33/34 cotas, 0 número inventado, 7 s (17/11/2026; a 10x: 12 s)
VERSAO_LEITURA = "a64"
VERSAO = 1
SEM_TEXTO = 20      # página com menos palavras que isto no pdftotext: o texto virou desenho


def _fitz():
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf  # noqa: N813 — nome antigo do PyMuPDF
        except ImportError:
            raise RuntimeError("Falta o PyMuPDF no Python do PC (pip install pymupdf==1.28.2).") from None
    return pymupdf


# ------------------------------------------------------------------ comparação (sem IA)

def algarismos(s):
    """Só os algarismos; "|" entre algarismos é o 1 desenhado como traço reto ("12|5" → "1215")."""
    s = re.sub(r"(?<=\d)\|(?=\d)|^\|(?=\d)|(?<=\d)\|$", "1", (s or "").strip())
    return re.sub(r"\D", "", s)


# número solto (não "P3", não "A-2"), com milhar opcional ("1.496,51"); a unidade, se houver, logo depois
VALOR = re.compile(r"(?<![\w,.\-/])(\d{1,3}(?:\.\d{3})+(?:,\d{1,3})?|\d{1,4}(?:[,.]\d{1,3})?)\s*(m²|m2|cm|mm|m)?(?![\w²/])", re.I)


def valores(esperado):
    """Números do texto esperado, em metros quando a unidade é m, cm ou mm: "altura de 12,15 m" → [12.15].
    Ponto com três algarismos é milhar quando há vírgula depois ("1.496,51") ou a unidade é cm/mm ("2.400 mm")."""
    out = []
    for num, un in VALOR.findall(esperado or ""):
        un = (un or "").lower()
        milhar = re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", num) and ("," in num or un in ("cm", "mm"))
        v = float(num.replace(".", "").replace(",", ".") if milhar else num.replace(",", "."))
        v = v / 100 if un == "cm" else v / 1000 if un == "mm" else v
        if v > 0 and v not in out:
            out.append(v)
    return out


def grafias(v):
    """O mesmo valor em m e em cm, só algarismos: 12.15 → {"1215"}; 1.2 → {"120", "12"}; 16 → {"16", "1600"}."""
    g = {algarismos("%.2f" % v), algarismos(("%.2f" % v).rstrip("0").rstrip(".")), str(round(v * 100))}
    if abs(v - round(v)) < 1e-9:
        g.add(str(int(round(v))))
    return {x.lstrip("0") for x in g if len(x.lstrip("0")) >= 2}   # um algarismo só bate em qualquer coisa


def bate(leitura, v):
    a = algarismos(leitura).lstrip("0") or ""
    return bool(a) and a in grafias(v)


# ------------------------------------------------------------------ geometria

def _dist_seg(p, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    L2 = (bx - ax) ** 2 + (by - ay) ** 2 or 1e-9
    t = max(0, min(1, ((p[0] - ax) * (bx - ax) + (p[1] - ay) * (by - ay)) / L2))
    return math.dist(p, (ax + t * (bx - ax), ay + t * (by - ay)))


def _norm(th):
    while th > 90:
        th -= 180
    while th <= -90:
        th += 180
    return th - 180 if th > 85 else th   # quase vertical: o texto do CAD lê de baixo para cima


def candidatos(pagina_pdf):
    """Blocos de texto desenhado que têm linha de cota ao lado: [{id, x, y, ang, mw, mh}] (pt do PDF)."""
    pontos, linhas = [], []
    for x in pagina_pdf.get_drawings():
        for it in x["items"]:
            if it[0] == "l":
                a, b = (it[1].x, it[1].y), (it[2].x, it[2].y)
                L = math.dist(a, b)
                if L >= TRACO:
                    linhas.append((a, b))
                else:
                    n = max(1, int(L))
                    pontos.extend((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1))
            elif it[0] == "c":
                pontos.append(((it[1].x + it[4].x) / 2, (it[1].y + it[4].y) / 2))
    if not pontos or not linhas:
        return []
    pai = list(range(len(pontos)))

    def ach(i):
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i
    grade = {}
    for i, (x, y) in enumerate(pontos):
        grade.setdefault((int(x // EPS), int(y // EPS)), []).append(i)
    for i, (x, y) in enumerate(pontos):
        gx, gy = int(x // EPS), int(y // EPS)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in grade.get((gx + dx, gy + dy), ()):
                    if j > i and math.dist(pontos[i], pontos[j]) < EPS:
                        pai[ach(i)] = ach(j)
    grupos = {}
    for i in range(len(pontos)):
        grupos.setdefault(ach(i), []).append(pontos[i])
    grupos = sorted((g for g in grupos.values() if len(g) >= MIN_PONTOS),
                    key=lambda g: (min(p[1] for p in g), min(p[0] for p in g)))

    def medidas(g, cx, cy, th):
        r = math.radians(th)
        u = [((p[0] - cx) * math.cos(r) + (p[1] - cy) * math.sin(r), -(p[0] - cx) * math.sin(r) + (p[1] - cy) * math.cos(r)) for p in g]
        return max(abs(q[0]) for q in u) + 3.5, max(abs(q[1]) for q in u) + 3.0

    out = []
    for k, g in enumerate(grupos):
        cx = sum(p[0] for p in g) / len(g)
        cy = sum(p[1] for p in g) / len(g)
        sxx = sum((p[0] - cx) ** 2 for p in g)
        syy = sum((p[1] - cy) ** 2 for p in g)
        sxy = sum((p[0] - cx) * (p[1] - cy) for p in g)
        th = math.degrees(0.5 * math.atan2(2 * sxy, sxx - syy))
        tr, dt = (sxx + syy) / 2, math.sqrt(((sxx - syy) / 2) ** 2 + sxy ** 2)
        if (tr + dt) < 2.2 * max(tr - dt, 1e-9):   # bloco pouco alongado: vale a linha mais próxima
            a, b = min(linhas, key=lambda s: _dist_seg((cx, cy), *s))
            th = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        th = _norm(th)
        mw, mh = medidas(g, cx, cy, th)
        cota = False
        for a, b in linhas:
            L = math.dist(a, b)
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            dif = (ang - th + 90) % 180 - 90
            if abs(dif) > TOL_ANG or L < 2 * mw - 7:
                continue
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            t_ = (cx - a[0]) * ux + (cy - a[1]) * uy
            if 0 < t_ < L and abs(-(cx - a[0]) * uy + (cy - a[1]) * ux) <= mh + 4:
                cota, th = True, _norm(th + dif)
                break
        if not cota:
            continue
        mw, mh = medidas(g, cx, cy, th)
        if mh > 12 or mw > 60:   # bloco grande demais: é desenho, não texto
            continue
        out.append({"id": "c%03d" % k, "x": round(cx, 1), "y": round(cy, 1), "ang": round(th, 2), "mw": round(mw, 1), "mh": round(mh, 1)})
    return out


def imagem(pagina_pdf, c, zoom=ZOOM_A, folga=1.0):
    """PNG do bloco c já na horizontal (só PyMuPDF: gira na renderização e corta o meio)."""
    fz = _fitz()
    lado = math.hypot(c["mw"], c["mh"]) * max(folga, 1.0) + 4
    clip = fz.Rect(c["x"] - lado, c["y"] - lado, c["x"] + lado, c["y"] + lado)
    mat = fz.Matrix(zoom, zoom) * fz.Matrix(-c["ang"])
    pix = pagina_pdf.get_pixmap(matrix=mat, clip=clip, alpha=False)
    w = c["mw"] * zoom * folga
    h = c["mh"] * zoom * folga + (2 * zoom if folga > 1 else 0)
    ir = fz.IRect(pix.irect)   # o pixmap tem origem própria (pix.x, pix.y): o corte é no mesmo sistema
    cx, cy = (ir.x0 + ir.x1) / 2, (ir.y0 + ir.y1) / 2
    corte = fz.IRect(int(cx - w), int(cy - h), int(cx + w), int(cy + h)) & ir
    novo = fz.Pixmap(fz.csRGB, corte, False)
    novo.set_rect(novo.irect, (255, 255, 255))
    novo.copy(pix, corte)   # (o construtor Pixmap(pix, w, h, clip) derruba o Python na 1.28.2)
    return novo.tobytes("png")


# ------------------------------------------------------------------ cache e leitura

def _arq(pdf):
    return pdf + ".cotas.json"


def _carregar(pdf):
    try:
        with open(_arq(pdf), encoding="utf-8") as f:
            d = json.load(f)
        if d.get("versao") == VERSAO and d.get("tamanho") == os.path.getsize(pdf):
            return d
    except (OSError, ValueError):
        pass
    return {"versao": VERSAO, "tamanho": os.path.getsize(pdf), "paginas": {}}


def _gravar(pdf, d):
    tmp = _arq(pdf) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, _arq(pdf))


def ler(pdf, pagina, transcrever, modelo, aviso=None, toque=None):
    """Lê todas as cotas da página (0-based) com transcrever(png) -> str. Duas leituras: a justa sempre; a com folga
    só se a primeira tiver algarismo. Devolve [{id, x, y, ang, mw, mh, a, b}]. Grava o cache depois de cada leitura,
    então uma rodada que cair continua de onde parou."""
    fz = _fitz()
    d = _carregar(pdf)
    pg_d = d["paginas"].setdefault(str(pagina), {})
    with fz.open(pdf) as doc:
        pg = doc[pagina]
        if "candidatos" not in pg_d:
            pg_d["candidatos"] = candidatos(pg)
            _gravar(pdf, d)
        lidas = pg_d.setdefault("leituras", {}).setdefault(modelo + "@" + VERSAO_LEITURA, {})
        cands = pg_d["candidatos"]
        for i, c in enumerate(cands, 1):
            r = lidas.get(c["id"])
            if r is None:
                r = lidas[c["id"]] = {"a": transcrever(imagem(pg, c, ALT_A / (2 * c["mh"]), 1.0))}
                if algarismos(r["a"]):
                    r["b"] = transcrever(imagem(pg, c, ZOOM_B, FOLGA_B))
                _gravar(pdf, d)
                if toque:
                    toque()
                if aviso and i % 10 == 0:
                    aviso("cotas: %d de %d lidas" % (i, len(cands)))
    return [dict(c, a=lidas[c["id"]].get("a", ""), b=lidas[c["id"]].get("b")) for c in cands]


def procurar(leituras, vs):
    """Onde os valores vs aparecem. certos: as duas leituras batem; conferir: só uma bate (a outra discorda)."""
    certos, conferir = [], []
    for c in leituras:
        for v in vs:
            ba, bb = bate(c["a"], v), bate(c.get("b") or "", v)
            if ba and bb:
                certos.append(dict(c, valor=v))
            elif ba or bb:
                conferir.append(dict(c, valor=v))
    return certos, conferir
