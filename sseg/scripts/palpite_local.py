#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
palpite_local.py — palpite da IA local (modelo de visão no Ollama do PC) sobre as exigências da última CIA, na
reanálise. Palpite, nunca decisão: quem diz se a exigência foi cumprida é o analista, no quadro azul do SSEG.exe.

AÇÕES (python sseg/scripts/sseg.py palpite --pasta "<pasta do processo>" <ação>)
  exigencias   lista as exigências da última CIA (cia-ultima.txt), numeradas, e as pranchas: novas, não reenviadas
               e as que a última CIA analisou e foram trocadas (api-<id>.json).
  procurar     onde um termo está escrito nas pranchas (texto exato do PDF), para escolher o ponto do recorte.
  preparar     recebe a classificação de cada exigência (JSON pela entrada) e monta: recorte na planta nova, o mesmo
               lugar na planta anterior (contraprova) e a comparação exata do texto entre as duas. Grava palpites.json.
  rodar        pergunta ao modelo local (3 tamanhos de recorte + contraprova) e grava o rótulo de cada palpite.
               Sem Ollama neste PC não inventa nada: o item fica na fila, sem palpite.
  ver          mostra o que está no palpites.json.

ONDE FICA
  <pasta do processo>/palpites.json   só texto; vai ao servidor com a pasta, nunca ao Git
  <pasta do processo>/plantas/        PDFs das pranchas e recortes (subpasta: a sincronização não leva)

REGRAS (testes de 13 e 14/11/2026 com o gemma4:31b-it-qat)
  - Palpite firme só em exigência de texto com valor, igual nos três tamanhos de recorte e com "não cumpriu" na
    planta anterior. Fora disso sai como fraco ou inconclusivo, dito na tela.
  - Desenho e ausência: palpite fraco (o modelo errou muito nesses tipos).
  - Memorial, cadastro e exigência remissiva: sem palpite.
  - Falha, demora ou Ollama fora do ar: sem palpite. Nunca "não sei" inventado.

PRANCHA COM O TEXTO CONVERTIDO EM DESENHO (17/11/2026; cotas_desenho.py)
  O pdftotext não acha palavra nenhuma, então não há termo para apontar o recorte. Em exigência de texto com valor
  ("12,15 m"), a IA lê as cotas da prancha uma a uma (duas leituras cada) e o código procura o valor. O palpite
  sai no máximo como fraco: o método foi testado em um processo só. Não achar o valor nunca vira "não cumpriu"
  (o filtro pode deixar a cota de fora). A leitura fica em cache ao lado do PDF; a primeira custa minutos.

Só biblioteca padrão; Poppler (pdftotext, pdftoppm) e, para o palpite, o Ollama em http://localhost:11434.
A leitura de cotas desenhadas pede também o PyMuPDF (o instalador do SSEG já instala).
"""

import base64
import glob
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from collections import Counter

ARQ = "palpites.json"
SUB = "plantas"
MODELO = os.environ.get("SSEG_IA_LOCAL_MODELO", "gemma4:31b-it-qat")
OLLAMA = os.environ.get("SSEG_OLLAMA", "http://localhost:11434")
POPPLER = ""          # pasta do Poppler; o SSEG.exe preenche (o pdftotext do Git, sem -bbox, vem antes no PATH)
LADO = 180            # meia largura do recorte, em pontos do PDF (o mesmo das provas)
MARGENS = (60, 30, 100)  # a primeira é a do palpite; as outras duas só conferem se ele se mantém
DPI = 250
MAX_RECORTES = 3
NUM_CTX = 8192
NUM_PREDICT = 600     # teto da resposta: sem ele o modelo às vezes repete texto até estourar o contexto
SEM_JANELA = 0x08000000 if os.name == "nt" else 0

TIPOS = {"texto": "Texto com valor", "desenho": "Desenho", "ausencia": "Algo que tinha de passar a existir",
         "fora_da_planta": "Fora da planta (memorial ou cadastro)", "remissiva": "Remete a outra exigência"}
COM_RECORTE = ("texto", "desenho", "ausencia")
VEREDITOS = ("cumpriu", "nao_cumpriu", "nao_sei")
NOME = {"cumpriu": "Cumpriu", "nao_cumpriu": "Não cumpriu", "nao_sei": "Não sei"}
CONFIANCA = {
    "texto": "Tipo em que a IA foi bem nos testes: nenhum \"cumpriu\" falso em 22 plantas não corrigidas (prova de 41 itens).",
    "desenho": "Tipo em que a IA foi mal nos testes: acertou 13 de 63 e deu \"cumpriu\" falso em 2 de 12 plantas não corrigidas.",
    "ausencia": "Tipo pouco testado: 19 itens, com \"cumpriu\" falso nas 2 plantas não corrigidas que havia.",
}

ESQUEMA = {"type": "object", "properties": {"veredito": {"type": "string", "enum": list(VEREDITOS)},
                                            "evidencia": {"type": "string"}}, "required": ["veredito", "evidencia"]}

# O mesmo texto das provas (corrida.py). Mudou aqui, os números dos testes deixam de valer: medir de novo.
PROMPT = """Você confere uma planta de PPCI (prevenção de incêndio) para um analista do Corpo de Bombeiros.
A imagem é {onde}.

Exigência a conferir: {pergunta}

Responda só com JSON: {{"veredito": "cumpriu" | "nao_cumpriu" | "nao_sei", "evidencia": "..."}}
Regras:
- "cumpriu" só se você LÊ na imagem a prova de que a exigência foi atendida (cota, texto, símbolo legível).
- "nao_cumpriu" só se você LÊ na imagem algo que mostra que não foi atendida.
- Se no lugar indicado está escrito um valor diferente do que a exigência pede (outro número, outro código,
  outra ocupação), isso é "nao_cumpriu": copie o valor que está escrito.
- Se o elemento não aparece, o texto está ilegível ou você está em dúvida: "nao_sei". Não adivinhe.
- Em "evidencia", copie exatamente o que leu (cotas, rótulos, notas) e onde está na imagem. Não invente valores."""


# ------------------------------------------------------------------ texto e pasta

def sem_acento(t):
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _ler_json(arq, padrao=None):
    try:
        with open(arq, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return padrao


def _exe(nome):
    pasta = POPPLER or os.environ.get("SSEG_POPPLER") or os.path.dirname(shutil.which("pdftoppm") or "")
    return os.path.join(pasta, nome + (".exe" if os.name == "nt" else "")) if pasta else nome


def _rodar(cmd, timeout=300):
    return subprocess.run(cmd, capture_output=True, timeout=timeout, creationflags=SEM_JANELA, stdin=subprocess.DEVNULL)


_POPPLER_OK = {}


def tem_poppler():
    """O pdftotext que vai ser usado é o do Poppler (tem -bbox)? Conferido uma vez por caminho."""
    exe = _exe("pdftotext")
    if exe not in _POPPLER_OK:
        try:
            r = _rodar([exe, "-h"], 20)
            _POPPLER_OK[exe] = b"-bbox" in (r.stderr or b"") + (r.stdout or b"")
        except (OSError, subprocess.SubprocessError):
            _POPPLER_OK[exe] = False
    return _POPPLER_OK[exe]


# ------------------------------------------------------------------ exigências da última CIA

RODAPE = re.compile(r"^\s*CBMRS \d\d/\d\d/\d{4}.*Pagina \d+ de \d+\s*$")
FIM_CIA = re.compile(r"O\s+PPCI deverá ser encaminhado|deverá ser encaminhado para nova análise", re.I)
ITEM_NUM = re.compile(r"^\s*\d+\.\s+\S")


def partir(texto):
    """Texto do PDF da CIA → [(seção, subtítulo, exigência)]. Seção = medida ou bloco (Característica, Elementos
    Gráficos...); subtítulo = nome da prancha, dentro de Elementos Gráficos. Cada "- ..." é uma exigência."""
    i = texto.find("apresentou as seguintes inconformidades")
    corpo = texto[i:] if i >= 0 else texto
    m = FIM_CIA.search(corpo)
    if m:
        corpo = corpo[:m.start()]
    linhas = [l for l in corpo.replace("\f", "\n").splitlines()[1:] if not RODAPE.match(l)]
    secao, sub, out, atual = "", "", [], None
    sem_hifen = False
    for l in linhas:
        s = l.strip()
        if not s:
            continue
        ind = len(l) - len(l.lstrip())
        if s.startswith("- "):
            atual = [secao, sub, s[2:].strip()]
            out.append(atual)
        elif ITEM_NUM.match(l) and ind > 4:
            rot = re.sub(r"^\d+\.\s+", "", s)
            if rot.lower().startswith("outros"):
                resto = re.sub(r"^-\s*", "", rot[6:].strip())
                atual = None  # "1. Outros": rótulo do SOL; o texto vem abaixo
                sem_hifen = True
                if resto:  # "1. Outros Deverá adequar...": o texto começa na linha do rótulo
                    atual = [secao, sub, resto]
                    out.append(atual)
                    sem_hifen = False
            else:  # opção pronta do SOL ("1. Ausência de marcação ..."): o próprio item é a exigência
                atual = [secao, sub, rot]
                out.append(atual)
                sem_hifen = False
        elif ind >= 12 and atual is not None:
            atual[2] += " " + s  # continuação do texto
        elif ind >= 12 and sem_hifen:
            # 17/11/2026: há analista (Sgt Magalhães) que escreve a exigência logo abaixo do "1. Outros", sem "- ".
            # Sem isto a CIA dele dava 0 exigências e a reanálise não tinha palpite nem conferência
            atual = [secao, sub, s]
            out.append(atual)
        elif ind < 8:
            if s in ("Medidas de Segurança", "Elementos Gráficos"):
                secao, sub = s, ""
            elif secao == "Elementos Gráficos":
                sub = s
            else:
                secao, sub = s, ""
            atual = None
    return [tuple(x) for x in out]


def exigencias(pasta):
    try:
        with open(os.path.join(pasta, "cia-ultima.txt"), encoding="utf-8", errors="replace") as fh:
            return partir(fh.read())
    except OSError:
        return []


def _ids_cia(pasta):
    ids = sorted(int(m.group(1)) for m in (re.search(r"cia-(\d+)\.txt$", f) for f in glob.glob(os.path.join(pasta, "cia-*.txt"))) if m)
    ult = ((_ler_json(os.path.join(pasta, "marcos-resumo.json"), {}) or {}).get("ultima_cia") or {}).get("arquivo")
    if ult and ult not in ids:
        ids = sorted(ids + [int(ult)])
    return ids


def _api(pasta):
    arqs = sorted(glob.glob(os.path.join(pasta, "api-*.json")), key=os.path.getmtime)
    return _ler_json(arqs[-1], {}) if arqs else {}


TIPOS_PRANCHA = (("PLANTA_BAIXA", "Planta baixa"), ("IMPLANTACAO", "Implantação"), ("CORTE", "Corte"))


def rotulo_tipo(tipo):
    return dict(TIPOS_PRANCHA).get(tipo) or (tipo or "Elemento gráfico").replace("_", " ").capitalize()


def nome_no_sol(lado, tipo, descricao, nome, ident):
    """Nome do arquivo na pasta, igual ao que o SOL mostra do elemento gráfico: "<tipo> - <descrição> (<id>).pdf".
    O botão de baixar do SOL entrega um nome que não diz qual prancha é (pedido do Átila, 16/11/2026). O id do
    arquivo no SOL vai no fim: é ele que liga o PDF ao elemento, e duas pranchas podem ter a mesma descrição."""
    desc = " ".join(re.sub(r'[\\/:*?"<>|\x00-\x1f]+', " ", descricao or os.path.splitext(nome or "")[0]).split()).strip(" .")[:80].strip()
    rot = rotulo_tipo(tipo)
    base = desc if sem_acento(desc).startswith(sem_acento(rot)) else ("%s - %s" % (rot, desc) if desc else rot)
    return ("anterior - " if lado == "antes" else "") + "%s (%s).pdf" % (base, ident)


def _ja_baixada(nomes, ident):
    """O PDF deste id que já está em plantas/, no nome novo ("... (<id>).pdf") ou no antigo ("depois-<id>-...")."""
    rx = re.compile(r"(?:^(?:antes|depois)-%s-.*| \(%s\))\.pdf$" % (ident, ident), re.I)
    return next((n for n in nomes if rx.search(n)), None)


def plantas(pasta):
    """Pranchas do processo para a reanálise: [{lado, id, arquivo, nome, tipo, descricao, nao_reenviada, tem}].
    lado "depois" = ATIVA (a que o analista vai analisar); "antes" = a que a última CIA analisou e o RT trocou.
    O id do arquivo no SOL cresce com o tempo: prancha ativa com id menor que o do PDF da última CIA não foi reenviada."""
    ids = _ids_cia(pasta)
    ultima = ids[-1] if ids else 0
    penultima = ids[-2] if len(ids) > 1 else 0
    out = []
    try:
        nomes = sorted(os.listdir(os.path.join(pasta, SUB)))
    except OSError:
        nomes = []
    for e in _api(pasta).get("elemGraficos") or []:
        a = e.get("arquivo") or {}
        ident = a.get("id")
        if not ident:
            continue
        ativo = e.get("situacao") == "ATIVO"
        if not (ativo or penultima < ident < ultima):
            continue
        lado = "depois" if ativo else "antes"
        desc = " ".join(str(e.get("descricao") or "").split())
        # o que já foi baixado vale com o nome que tem (palpites.json guarda o nome); o que falta nasce com o do SOL
        arq = _ja_baixada(nomes, ident) or nome_no_sol(lado, e.get("tipo") or "", desc, a.get("nomeArquivo") or "", ident)
        cam = os.path.join(pasta, SUB, arq)
        out.append({"lado": lado, "id": ident, "arquivo": arq, "nome": a.get("nomeArquivo") or "", "tipo": e.get("tipo") or "",
                    "descricao": desc,
                    "nao_reenviada": bool(ativo and ultima and ident < ultima),
                    "tem": os.path.isfile(cam) and os.path.getsize(cam) > 0})
    return out


def _rotulo_planta(p):
    desc = p["descricao"] or p["tipo"].replace("_", " ").lower()
    return "%s (%s)" % (desc if len(desc) <= 48 else desc[:46].rstrip() + "…", p["nome"] or p["arquivo"])


def par_anterior(todas, p):
    """A prancha que a última CIA analisou e que esta substituiu: mesmo tipo e, se der, mesmo começo de descrição."""
    ant = [a for a in todas if a["lado"] == "antes" and a["tipo"] == p["tipo"]]
    perto = [a for a in ant if sem_acento(a["descricao"])[:6] == sem_acento(p["descricao"])[:6]] or ant
    return max(perto, key=lambda a: a["id"]) if perto else None


# ------------------------------------------------------------------ texto da prancha, com posição

def palavras(pdf):
    """({página: [(palavra sem acento, x0, y0, x1, y1, original)]}, {página: (largura, altura)}), em pontos do PDF com
    a origem no canto de cima à esquerda (pdftotext -bbox). Cache ao lado do PDF."""
    cache = pdf + ".bbox.json"
    d = _ler_json(cache) if os.path.exists(cache) and os.path.getmtime(cache) >= os.path.getmtime(pdf) else None
    if not d:
        out = _rodar([_exe("pdftotext"), "-bbox", pdf, "-"]).stdout.decode("utf-8", "replace")
        d, pag = {"ws": {}, "tam": {}}, 0
        for linha in out.splitlines():
            m = re.search(r'<page width="([\d.]+)" height="([\d.]+)"', linha)
            if m:
                pag += 1
                d["ws"][str(pag)], d["tam"][str(pag)] = [], [float(m.group(1)), float(m.group(2))]
                continue
            m = re.search(r'xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*)</word>', linha)
            if m and pag:
                orig = html.unescape(m.group(5))
                d["ws"][str(pag)].append([sem_acento(orig)] + [round(float(m.group(i)), 1) for i in range(1, 5)] + [orig])
        if not pag:
            raise RuntimeError("o pdftotext não leu a prancha (Poppler instalado?): " + os.path.basename(pdf))
        try:
            with open(cache, "w", encoding="utf-8") as fh:
                json.dump(d, fh, ensure_ascii=False)
        except OSError:
            pass
    return ({int(k): [tuple(w) for w in v] for k, v in d["ws"].items()}, {int(k): tuple(v) for k, v in d["tam"].items()})


def deslocamento(a, d, celula=8):
    """(dx, dy) que leva a planta anterior para cima da nova, quando o desenho inteiro foi movido na folha. Sai das
    palavras que aparecem uma vez só em cada lado; sem maioria clara, (0, 0)."""
    ca, cd = Counter(w[0] for w in a), Counter(w[0] for w in d)
    pa = {w[0]: w for w in a if ca[w[0]] == 1 and len(w[0]) > 2}
    difs = [(w[1] - pa[w[0]][1], w[2] - pa[w[0]][2]) for w in d if cd[w[0]] == 1 and w[0] in pa]
    if len(difs) < 8:
        return 0, 0
    (gx, gy), _n = Counter((round(x / celula), round(y / celula)) for x, y in difs).most_common(1)[0]
    perto = [(x, y) for x, y in difs if abs(x / celula - gx) <= 1 and abs(y / celula - gy) <= 1]
    if len(perto) < 0.3 * len(difs):
        return 0, 0
    dx = sorted(x for x, _ in perto)[len(perto) // 2]
    dy = sorted(y for _, y in perto)[len(perto) // 2]
    return (round(dx, 1), round(dy, 1)) if abs(dx) > 2 or abs(dy) > 2 else (0, 0)


def mudancas(a, d, raio=14):
    """Palavras que só existem na planta nova (entraram) e só na anterior (saíram), casando palavra igual em posição
    próxima. Devolve (entraram, saíram, (dx, dy)); as que saíram já vêm na posição da planta nova."""
    ox, oy = deslocamento(a, d)
    if ox or oy:
        a = [(w[0], w[1] + ox, w[2] + oy, w[3] + ox, w[4] + oy, w[5]) for w in a]
    grade = {}
    for i, w in enumerate(a):
        grade.setdefault((w[0], int(w[1] // raio), int(w[2] // raio)), []).append(i)
    usados, entraram = set(), []
    for w in d:
        gx, gy = int(w[1] // raio), int(w[2] // raio)
        achou = next((i for ex in (-1, 0, 1) for ey in (-1, 0, 1) for i in grade.get((w[0], gx + ex, gy + ey), [])
                      if i not in usados and abs(a[i][1] - w[1]) <= raio and abs(a[i][2] - w[2]) <= raio), None)
        if achou is None:
            entraram.append(w)
        else:
            usados.add(achou)
    return entraram, [w for i, w in enumerate(a) if i not in usados], (ox, oy)


def ocorrencias(ws, termo, pulo=2, dy=14):
    """Centros (x, y) do termo: palavras seguidas na ordem de leitura, sem acento e sem pontuação nas pontas. Aceita
    quebra de linha no meio (a palavra seguinte até `dy` pontos abaixo) e até `pulo` palavras estranhas entre duas
    do termo (um rótulo de desenho que o PDF intercala no meio do texto)."""
    limpa = lambda w: w.strip(".,;:()[]\"'=")
    partes = [p for p in (limpa(p) for p in sem_acento(termo).split()) if p]
    out = []
    if not partes:
        return out
    for i, w in enumerate(ws):
        if limpa(w[0]) != partes[0]:
            continue
        k, ok = i, True
        for p in partes[1:]:
            k = next((j for j in range(k + 1, min(len(ws), k + 2 + pulo)) if limpa(ws[j][0]) == p and abs(ws[j][2] - ws[k][2]) < dy), None)
            if k is None:
                ok = False
                break
        if ok:
            out.append(((w[1] + ws[k][3]) / 2, (w[2] + ws[k][4]) / 2))
    return out


def frases(ws, folga_y=4.0, folga_x=14.0):
    """Junta palavras vizinhas na mesma linha em trechos legíveis (texto original)."""
    ws = sorted(ws, key=lambda w: (round(w[2] / folga_y), w[1]))
    out, atual = [], None
    for w in ws:
        if atual and abs(w[2] - atual[-1][2]) <= folga_y and w[1] - atual[-1][3] <= folga_x:
            atual.append(w)
        else:
            atual = [w]
            out.append(atual)
    return [" ".join(v[5] for v in g) for g in out]


def _dentro(ws, caixa, folga=0):
    x0, y0, x1, y1 = caixa
    return [w for w in ws if x0 - folga <= w[1] <= x1 + folga and y0 - folga <= w[2] <= y1 + folga]


def _caixa(cx, cy, tam):
    """Quadrado de 2*LADO em volta do ponto, puxado para dentro da folha."""
    w, h = tam
    x0 = min(max(0, cx - LADO), max(0, w - 2 * LADO))
    y0 = min(max(0, cy - LADO), max(0, h - 2 * LADO))
    return [round(x0), round(y0), round(min(w, x0 + 2 * LADO)), round(min(h, y0 + 2 * LADO))]


# ------------------------------------------------------------------ imagem do recorte

def recorte(pdf, pagina, caixa, margem, dpi=DPI, jpeg=False):
    """Bytes da imagem do recorte, direto do PDF (pdftoppm corta sem renderizar a prancha inteira)."""
    palavras_, tam = palavras(pdf)
    w, h = tam.get(pagina, (0, 0))
    x0, y0 = max(0, caixa[0] - margem), max(0, caixa[1] - margem)
    x1, y1 = min(w or caixa[2] + margem, caixa[2] + margem), min(h or caixa[3] + margem, caixa[3] + margem)
    if x1 - x0 < 20 or y1 - y0 < 20:
        raise RuntimeError("recorte fora da folha")
    s = dpi / 72.0
    cmd = [_exe("pdftoppm"), "-r", str(dpi), "-f", str(pagina), "-l", str(pagina), "-x", str(int(x0 * s)), "-y", str(int(y0 * s)),
           "-W", str(int((x1 - x0) * s)), "-H", str(int((y1 - y0) * s))]
    cmd += ["-jpeg", "-jpegopt", "quality=80"] if jpeg else ["-png"]
    out = _rodar(cmd + [pdf]).stdout
    if not out.startswith(b"\xff\xd8" if jpeg else b"\x89PNG"):
        raise RuntimeError("o pdftoppm não gerou o recorte de " + os.path.basename(pdf))
    return out


def recorte_tela(pasta, r, margem=60, dpi=170):
    """JPEG do recorte para o quadro azul, guardado em plantas/recortes/ (o mesmo recorte não é gerado duas vezes)."""
    nome = "%s-p%d-%s-m%d.jpg" % (os.path.splitext(r["pdf"])[0], r["pagina"], "_".join(str(int(v)) for v in r["caixa"]), margem)
    arq = os.path.join(pasta, SUB, "recortes", nome)
    pdf = os.path.join(pasta, SUB, r["pdf"])
    if os.path.exists(arq) and os.path.getmtime(arq) >= os.path.getmtime(pdf):
        with open(arq, "rb") as fh:
            return fh.read()
    dados = recorte(pdf, r["pagina"], r["caixa"], margem, dpi=dpi, jpeg=True)
    try:
        os.makedirs(os.path.dirname(arq), exist_ok=True)
        with open(arq, "wb") as fh:
            fh.write(dados)
    except OSError:
        pass
    return dados


def elementos(pasta):
    """Elementos gráficos ATIVOS agrupados por tipo, para os botões da janela do processo:
    [{tipo, rotulo, itens: [{id, descricao, arquivo, tem, nao_reenviada}]}], planta baixa, implantação, corte e o resto."""
    ordem = [t for t, _r in TIPOS_PRANCHA]
    grupos = {}
    for p in plantas(pasta):
        if p["lado"] == "depois":
            grupos.setdefault(p["tipo"], []).append({k: p[k] for k in ("id", "descricao", "arquivo", "tem", "nao_reenviada")})
    return [{"tipo": t, "rotulo": rotulo_tipo(t), "itens": sorted(grupos[t], key=lambda x: x["id"])}
            for t in sorted(grupos, key=lambda t: (ordem.index(t) if t in ordem else len(ordem), t))]


def ultima_cia(pasta):
    """A última CIA do processo, pelos Marcos que o servidor baixa (marcos-resumo.json): {id, data, analista, arquivo,
    tem}. None na primeira análise ou sem os Marcos. O PDF fica na pasta do processo como cia-<id>.pdf, o mesmo nome
    que o Claude e os scripts procuram (2.13.5, pedido do Átila em 17/11/2026)."""
    u = (_ler_json(os.path.join(pasta, "marcos-resumo.json"), {}) or {}).get("ultima_cia") or {}
    if not u.get("arquivo"):
        return None
    arq = "cia-%s.pdf" % u["arquivo"]
    return {"id": int(u["arquivo"]), "data": u.get("data") or "", "analista": u.get("responsavel") or "", "arquivo": arq,
            "tem": os.path.exists(os.path.join(pasta, arq))}


def gravar_cia(pasta, ident, dados):
    """PDF da CIA baixado do SOL → cia-<id>.pdf, o texto em cia-<id>.txt e, se for a última, cia-ultima.txt (o que a
    pré-análise, os palpites e o Claude leem). Devolve o caminho do PDF."""
    if not dados.startswith(b"%PDF"):
        raise RuntimeError("o SOL não devolveu um PDF")
    pdf = os.path.join(pasta, "cia-%s.pdf" % ident)
    tmp = pdf + ".parte"
    with open(tmp, "wb") as fh:
        fh.write(dados)
    os.replace(tmp, pdf)
    txt = os.path.splitext(pdf)[0] + ".txt"
    r = _rodar([_exe("pdftotext"), "-layout", pdf, txt], 120)
    u = ultima_cia(pasta)
    if not r.returncode and u and u["id"] == int(ident):
        shutil.copyfile(txt, os.path.join(pasta, "cia-ultima.txt"))
    return pdf


def nomes_do_sol(pasta):
    """Passa para o nome do SOL as pranchas baixadas antes de 16/11/2026 ("depois-<id>-..."), com os arquivos de apoio
    ao lado, e acerta o nome onde o palpites.json o cita (o quadro azul acha o recorte por ele). Com a rodada da IA
    local em andamento não mexe. Devolve quantas mudou."""
    if rodando(pasta):
        return 0
    d = os.path.join(pasta, SUB)
    troca = {}
    for p in plantas(pasta):
        velho = p["arquivo"]
        if not p["tem"] or not re.match(r"(antes|depois)-\d+-", velho):
            continue
        novo = nome_no_sol(p["lado"], p["tipo"], p["descricao"], p["nome"], p["id"])
        try:
            os.replace(os.path.join(d, velho), os.path.join(d, novo))
        except OSError:
            continue  # PDF aberto no leitor: fica com o nome antigo, que continua valendo
        troca[velho] = novo
        for f in os.listdir(d):
            if f.startswith(velho + "."):  # caches ao lado do PDF (.bbox.json, .camadas.json)
                try:
                    os.replace(os.path.join(d, f), os.path.join(d, novo + f[len(velho):]))
                except OSError:
                    pass
    if troca and os.path.exists(caminho(pasta)):
        def acertar(x):
            if isinstance(x, dict):
                for k, v in x.items():
                    x[k] = troca.get(v, v) if isinstance(v, str) else acertar(v)
            elif isinstance(x, list):
                for k, v in enumerate(x):
                    x[k] = troca.get(v, v) if isinstance(v, str) else acertar(v)
            return x
        _atualizar(pasta, acertar)
    return len(troca)


def baixar_plantas(pasta, buscar, lados=("depois", "antes")):
    """Traz para <pasta>/plantas/ as pranchas que faltam. buscar(id do arquivo no SOL) devolve os bytes do PDF: quem
    chama é o SSEG.exe, pela aba do SOL em que o analista já entrou (só leitura). Devolve {baixadas, falhas}.
    lados=("depois",): só as ativas (botão "Elementos gráficos"); as anteriores só servem aos palpites da IA local."""
    os.makedirs(os.path.join(pasta, SUB), exist_ok=True)
    baixadas, falhas = [], []
    for p in plantas(pasta):
        if p["tem"] or p["lado"] not in lados:
            continue
        try:
            dados = buscar(p["id"])
            if not dados.startswith(b"%PDF"):
                raise RuntimeError("o SOL não devolveu um PDF")
            tmp = os.path.join(pasta, SUB, "." + p["arquivo"] + ".parte")
            with open(tmp, "wb") as fh:
                fh.write(dados)
            os.replace(tmp, os.path.join(pasta, SUB, p["arquivo"]))
            baixadas.append(_rotulo_planta(p))
        except PermissionError:
            raise
        except Exception as e:  # noqa: BLE001 — uma prancha que falha não impede as outras
            falhas.append("%s: %s" % (_rotulo_planta(p), str(e)[:160]))
    return {"baixadas": baixadas, "falhas": falhas}


# ------------------------------------------------------------------ palpites.json

def caminho(pasta):
    return os.path.join(pasta, ARQ)


def ler(pasta):
    return _ler_json(caminho(pasta)) or {}


def _atualizar(pasta, fn):
    """Lê, aplica fn(d) e grava, com trava: a rodada (outro processo), o programa e a conversa escrevem no mesmo
    arquivo. Temporário e trava começam com ponto: a sincronização não os leva."""
    trava = os.path.join(pasta, ".palpites.lock")
    fim = time.time() + 15
    while True:
        try:
            os.close(os.open(trava, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            break
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(trava) > 60:
                    os.remove(trava)  # trava esquecida por um processo que caiu
                    continue
            except OSError:
                pass
            if time.time() > fim:
                raise RuntimeError("o palpites.json está travado por outro processo")
            time.sleep(0.2)
    try:
        d = ler(pasta)
        r = fn(d)
        tmp = os.path.join(pasta, ".palpites-%d.json" % os.getpid())
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, caminho(pasta))
        return r
    finally:
        try:
            os.remove(trava)
        except OSError:
            pass


def _item(d, n):
    return next((i for i in d.get("itens") or [] if i.get("n") == n), None)


def pergunta(it):
    p = "Reanálise de PPCI. Exigência da análise anterior (%s): \"%s\"." % (it.get("sub") or it.get("secao") or "", it["exigencia"])
    if it.get("esperado"):
        p += " Para estar cumprida, tem de estar escrito na planta: %s." % it["esperado"]
    return p + (" Os %d recorte(s) mostram a planta nova, enviada pelo responsável técnico depois dessa exigência, na região "
                "em volta de \"%s\". A planta nova atende a exigência?" % (len(it["recortes"]), it.get("termo") or it.get("termo_antes") or ""))


def _assinatura(it):
    base = [it["exigencia"], it["tipo"], it.get("esperado"), it.get("termo"), it.get("termo_antes"),
            [[r["pdf"], r["pagina"], r["caixa"], (r.get("antes") or {}).get("pdf"), (r.get("antes") or {}).get("caixa")] for r in it.get("recortes") or []],
            MODELO, list(MARGENS), hashlib.sha1(PROMPT.encode()).hexdigest()[:8]]
    if it.get("cotas"):   # só entra quando há: a assinatura dos itens antigos não muda
        base.append([[c["pdf"], c["pagina"], (c.get("antes") or {}).get("pdf")] for c in it["cotas"]] + [P_COTA])
    if com_numero(it):    # 18/11/2026: exigência com número ganha a conta com a cota lida (refaz o palpite)
        base.append([MARGEM_LEITURA, hashlib.sha1(PROMPT_NUM.encode()).hexdigest()[:8]])
    return hashlib.sha1(json.dumps(base, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


# ------------------------------------------------------------------ número de ordem filtrado pela camada (19/11/2026)
# Cada medida numera a sua: a placa nº 39, o extintor nº 39 e o hidrante nº 39 convivem na mesma prancha. Ideia do Átila:
# a camada do PDF diz de qual medida é o número. Na bateria (30 itens) o recorte pelo número sozinho caiu no extintor e no
# hidrante; pela camada, caiu na placa. Só filtra quando o PDF tem camada com nome de medida; sem PyMuPDF, sem camada
# ou sem tipo claro, fica como estava.
TIPO_CTX = [(r"(placa|sos|s\.o\.s\.?|sinaliza\w*)$", "sinalizacao"), (r"(porta|portao|portoes|saida|saidas)$", "saida"),
            (r"(extintor|extintores)$", "extintores"), (r"(hidrante|hidrantes|mangotinho)$", "hidrantes"),
            (r"(acionador|acionadores|alarme)$", "alarme"), (r"(bloco|luminaria|iluminacao)$", "iluminacao")]
ACEITA = {"sinalizacao": {"sinalizacao", "saida"}, "saida": {"saida", "sinalizacao"}, "iluminacao": {"iluminacao", "saida"},
          "extintores": {"extintores"}, "hidrantes": {"hidrantes"}, "alarme": {"alarme"}}
NEUTRAS = {"outra", "distancia", "-"}   # camada sem nome de medida: não prova nada, o ponto fica
_spans = {}


def _camadas_mod():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import camadas
    return camadas


def tipo_do_numero(exig, termo):
    """(número, medida) do número de ordem do termo: a palavra de medida mais próxima antes do número, no termo ou na
    exigência ("placa S14 n°16" → sinalizacao; "porta próxima ao extintor nº 03" → extintores). Sem número: (None, None)."""
    m = re.search(r"(\d{1,3})\s*$", sem_acento(termo or "").strip(" .;:)"))
    if not m:
        return None, None
    num = m.group(1).lstrip("0") or "0"
    for txt in (sem_acento(termo), sem_acento(exig)):
        for mm in re.finditer(r"(?<![\d,.])0*%s(?![\d]|[,.]\d)" % num, txt):
            ctx = txt[max(0, mm.start() - 30):mm.start()]
            achou = [(k2.end(), k) for p, k in TIPO_CTX for k2 in re.finditer(p.replace("$", r"\b"), ctx)]
            if achou:
                return num, max(achou)[1]
    return num, None


def _rotulos_camada(pdf):
    """{página: [(cx, cy, texto, medida)]} dos textos curtos com camada, no sistema da página girada (o mesmo do
    pdftotext/pdftoppm). None se o PDF não tem camada ou falta o PyMuPDF."""
    if pdf in _spans:
        return _spans[pdf]
    out = None
    try:
        cm = _camadas_mod()
        fitz = cm.tem_pymupdf()
        d = fitz.open(pdf)
        if d.get_ocgs():
            out = {}
            for n, pg in enumerate(d, 1):
                rot, lst = pg.rotation_matrix, []
                for t in pg.get_texttrace():
                    ch = [c for c in t.get("chars") or () if c[0] >= 32]
                    s = "".join(chr(c[0]) for c in ch).strip()
                    lay = t.get("layer") or ""
                    if not s or len(s) > 20:
                        continue
                    r = fitz.Rect(min(c[3][0] for c in ch), min(c[3][1] for c in ch),
                                  max(c[3][2] for c in ch), max(c[3][3] for c in ch)) * rot
                    lst.append(((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, s, cm.medida_da_camada(lay)[0] if lay else "-"))
                out[n] = lst
        d.close()
    except Exception:  # noqa: BLE001 — sem PyMuPDF ou PDF estranho: segue sem o filtro
        out = None
    if len(_spans) > 20:
        _spans.clear()
    _spans[pdf] = out
    return out


def rotulo_de_numero(s, num):
    """"Nº 39", "N.º 44", "S 60", "P- nº06", "06": o texto é o rótulo do número, não cota nem área."""
    return bool(re.fullmatch(r"(?:[A-Z]{0,3}\d{0,2}\s*)?(?:N\.?\s*[\u00ba\u00b0O]\.?|NR\.?|SOS|S|P|H|E)?\s*-?\s*"
                             r"(?:N\.?\s*[\u00ba\u00b0O]\.?)?\s*0*" + num, s.strip().upper()))


def filtro_camada(pdf, pag, pontos, num, tipo, raio=30):
    """Separa os pontos do termo: (ficam, saíram com a medida da camada). Sai o ponto cujo rótulo do número mais
    próximo está na camada de OUTRA medida ou de base (esquadria, texto, legenda). Entra o rótulo do número na camada
    do próprio elemento que a busca pela palavra não achou ("Nº39" grudado, que o pdftotext dá como uma palavra só)."""
    rot = _rotulos_camada(pdf)
    if not rot or not tipo or tipo not in ACEITA:
        return pontos, []
    ficam, sairam = [], []
    for x, y in pontos:
        perto = [(abs(cx - x) + abs(cy - y), med) for cx, cy, s, med in rot.get(pag, []) if rotulo_de_numero(s, num)
                 and abs(cx - x) <= raio and abs(cy - y) <= raio]
        med = min(perto)[1] if perto else None
        if med is None or med in NEUTRAS or med in ACEITA[tipo]:
            ficam.append((x, y))
        else:
            sairam.append(med)
    for cx, cy, s, med in rot.get(pag, []):
        if med in ACEITA[tipo] and rotulo_de_numero(s, num) and not any(abs(cx - x) <= raio and abs(cy - y) <= raio for x, y in ficam):
            ficam.append((cx, cy))
    return ficam, sairam


def _recortes(pasta, cfg, todas):
    """Recortes de uma exigência: [(recorte)], fatos, motivo de não haver. Procura o termo nas pranchas novas e o
    termo_antes nas que a última CIA analisou (o ponto é levado para a planta nova pelo deslocamento do desenho)."""
    filtro = sem_acento(cfg.get("prancha") or "")
    serve = lambda p: not filtro or filtro in sem_acento(p["descricao"] + " " + p["nome"] + " " + p["arquivo"])
    novas = [p for p in todas if p["lado"] == "depois" and serve(p)]
    if not novas:
        return [], [], "Nenhuma prancha ativa casa com \"%s\"." % (cfg.get("prancha") or "")
    faltam = [p for p in novas if not p["tem"]]
    fatos, pontos = [], []  # pontos: (prancha nova, página, cx, cy)
    fora_camada = []        # medidas das camadas de onde saiu o número (era de outro elemento)
    for p in novas:
        if not p["tem"]:
            continue
        pdf = os.path.join(pasta, SUB, p["arquivo"])
        ws, tam = palavras(pdf)
        a = par_anterior(todas, p)
        for pag in sorted(ws):
            if cfg.get("termo"):
                achados = ocorrencias(ws[pag], cfg["termo"])
                num, tipo = tipo_do_numero(cfg.get("exigencia"), cfg["termo"])
                if achados and num:
                    achados, sairam = filtro_camada(pdf, pag, achados, num, tipo)
                    fora_camada += sairam
                pontos += [(p, pag, x, y) for x, y in achados]
            if cfg.get("termo_antes") and a and a["tem"] and not p["nao_reenviada"]:
                wa, _t = palavras(os.path.join(pasta, SUB, a["arquivo"]))
                ox, oy = deslocamento(wa.get(pag, []), ws[pag])
                pontos += [(p, pag, x + ox, y + oy) for x, y in ocorrencias(wa.get(pag, []), cfg["termo_antes"])]
    # pontos vizinhos na mesma prancha viram um recorte só, centrado no meio deles (cabem juntos no quadrado de 2*LADO)
    grupos = []  # [prancha, página, x médio, y médio, quantos]
    for p, pag, x, y in pontos:
        g = next((g for g in grupos if g[0] is p and g[1] == pag and abs(g[2] - x) <= LADO * 1.3 and abs(g[3] - y) <= LADO * 1.3), None)
        if g is None:
            grupos.append([p, pag, x, y, 1])
        else:
            g[2], g[3], g[4] = (g[2] * g[4] + x) / (g[4] + 1), (g[3] * g[4] + y) / (g[4] + 1), g[4] + 1
    if fora_camada:
        fatos.append("O nº do termo também aparece na camada de %s: esse lugar ficou fora do recorte (é outro elemento "
                     "com o mesmo número)." % ", ".join(sorted(set(fora_camada))))
    if not grupos and fora_camada:
        return [], fatos, "O número só aparece na camada de %s, não na do elemento citado: sem recorte, para a IA não " \
            "julgar o elemento errado." % ", ".join(sorted(set(fora_camada)))
    if not grupos:
        if faltam:
            return [], fatos, "Falta baixar a planta: %s." % "; ".join(_rotulo_planta(p) for p in faltam)
        quais = " nem ".join("\"%s\"" % t for t in (cfg.get("termo"), cfg.get("termo_antes")) if t)
        return [], ["Não está escrito %s em nenhuma prancha%s." % (quais, " que casa com \"%s\"" % cfg["prancha"] if filtro else "")], \
            "Sem lugar escrito na planta para apontar o recorte."
    if len(grupos) > MAX_RECORTES:
        return [], fatos, "O termo aparece em %d lugares: precisa de um termo mais específico ou do nome da prancha." % len(grupos)
    recs = []
    for k, (p, pag, x, y, _n) in enumerate(grupos, 1):
        pdf = os.path.join(pasta, SUB, p["arquivo"])
        ws, tam = palavras(pdf)
        caixa = _caixa(x, y, tam[pag])
        r = {"pdf": p["arquivo"], "pagina": pag, "caixa": caixa, "prancha": _rotulo_planta(p)}
        onde = ("Recorte %d, prancha %s" % (k, _rotulo_planta(p))) if len(grupos) > 1 else "Prancha " + _rotulo_planta(p)
        a = par_anterior(todas, p)
        if p["nao_reenviada"]:
            r["nao_reenviada"] = True
            fatos.append("%s: não foi reenviada. É o mesmo arquivo que a última CIA analisou." % onde)
        elif not a:
            fatos.append("%s: nova, sem versão anterior do mesmo tipo entre as que a última CIA analisou." % onde)
        elif not a["tem"]:
            fatos.append("%s: falta baixar a versão que a última CIA analisou (%s) para comparar." % (onde, a["nome"]))
        else:
            wa, _t = palavras(os.path.join(pasta, SUB, a["arquivo"]))
            ent, sai, (ox, oy) = mudancas(wa.get(pag, []), ws[pag])
            r["antes"] = {"pdf": a["arquivo"], "pagina": pag, "caixa": [round(caixa[0] - ox), round(caixa[1] - oy), round(caixa[2] - ox), round(caixa[3] - oy)]}
            e_, s_ = frases(_dentro(ent, caixa, 60)), frases(_dentro(sai, caixa, 60))
            if e_ or s_:
                fatos.append("%s, neste trecho: entrou no texto: %s; saiu do texto: %s." % (
                    onde, " · ".join(e_)[:300] or "nada", " · ".join(s_)[:300] or "nada"))
            else:
                fatos.append("%s, neste trecho: o texto é idêntico ao da planta que a última CIA analisou "
                             "(a mudança, se houve, é só de desenho)." % onde)
        dica = dica_cotas(cfg, frases(_dentro(ws[pag], caixa, 30)), onde)
        if dica:
            fatos.append(dica)
        recs.append(r)
    if all(r.get("nao_reenviada") for r in recs):
        return recs, fatos, "A prancha não foi reenviada: não há planta nova para a IA olhar."
    if not any(r.get("antes") for r in recs):
        fatos.append("Sem a planta anterior para a contraprova: o palpite sai, no máximo, como fraco.")
    return recs, fatos, ""


# ------------------------------------------------------------------ dica de cotas (sem IA, 21/11/2026)
# Caminho (2) da bateria da IA local: decidir "cumpriu" pela cota escrita no recorte foi reprovado (b2-medir no
# PLACAR: o número lido certo era de outra porta ou de outro percurso). Serve como dica ao analista, ao lado dos
# outros fatos: o que está escrito no recorte e o limite que a exigência pede. Nunca vira palpite nem vai ao modelo.

_NUM = r"(\d{1,3}(?:[.,]\d{1,2})?)"


def _f(x):
    return float(x.replace(",", "."))


def limite_exigencia(exigencia, esperado=""):
    """("largura", mínimo) | ("distancia", máximo) | None, lido no texto da exigência."""
    t = sem_acento(" ".join([esperado or "", exigencia or ""]))
    ns = []
    for m in re.finditer(_NUM + r"\s*(?:m|metros)\b", t):
        if re.search(r"mais de\s*$|superior a\s*$|acima de\s*$", t[max(0, m.start() - 14):m.start()]):
            continue  # "rampa com mais de 2,20 m deve ter corrimão intermediário" é condição, não limite
        n = _f(m.group(1))
        if 0.5 <= n <= 80:
            ns.append(n)
    if not ns:
        return None
    if re.search(r"largura|unidades? de passagem|vao livre", t):
        cand = [n for n in ns if n <= 3]
        return ("largura", max(cand)) if cand else None
    if re.search(r"maxim|menos de|nao mais|ate \d|no maximo|distante a nao|percorrer", t):
        cand = [n for n in ns if n >= 3]
        return ("distancia", min(cand)) if cand else None
    return None


def cotas_escritas(tipo, linhas):
    """Números do recorte do mesmo tipo do limite: porta "LxA" (altura de porta 2,00 a 2,40 m; placa "S1 300x150"
    fica fora) ou "L = 1,20" para largura; anotação de distância/percurso para distância."""
    vs = []
    for s in (sem_acento(x) for x in linhas):
        if tipo == "distancia":
            for m in re.finditer(r"(?:distancia|percorr|total|caminhamento)[^0-9]{0,80}?" + _NUM + r"\s*m\b", s):
                vs.append(_f(m.group(1)))
            continue
        for m in re.finditer(r"(?<![s]\d)(?<![s]\d\d)(?<![s]\d )(?<![s]\d\d )\(?\b(\d{2,3}|[0-3][.,]\d{2})\s*x\s*(\d{3}|[1-3][.,]\d{2})\b", s):
            w, h = _f(m.group(1)), _f(m.group(2))
            w, h = (w / 100 if w > 10 else w), (h / 100 if h > 10 else h)
            if 0.5 <= w <= 2.5 and 2.0 <= h <= 2.4:
                vs.append(w)
        for m in re.finditer(r"\b(?:l|larg(?:ura)?)\s*[=:]\s*" + _NUM + r"\s*m?\b", s):
            w = _f(m.group(1))
            w = w / 100 if w > 10 else w
            if 0.5 <= w <= 6:
                vs.append(w)
    return vs


def dica_cotas(it, linhas, onde):
    """Fato com as cotas lidas no recorte e o limite da exigência, ou "" quando não há limite ou número."""
    lim = limite_exigencia(it.get("exigencia"), it.get("esperado"))
    if not lim:
        return ""
    tipo, L = lim
    vs = cotas_escritas(tipo, linhas)
    if not vs:
        return ""
    br = lambda v: ("%.2f" % v).replace(".", ",")
    return "%s: cotas escritas no recorte (%s): %s · a exigência pede %s %s m. Dica do texto do PDF, sem saber de " \
        "qual porta ou percurso é cada cota: confira na planta." % (
            onde, "portas/larguras" if tipo == "largura" else "distâncias", "; ".join(br(v) for v in vs[:8]),
            "largura mínima de" if tipo == "largura" else "no máximo", br(L))


# ------------------------------------------------------------------ prancha com o texto convertido em desenho

SEM_TEXTO = 60    # página com menos palavras que isto no pdftotext: o texto virou traço
MAX_PRANCHAS_COTA = 2
P_COTA = ("Recorte de planta de PPCI com um único texto (em geral uma cota em metros, como 1,20). Transcreva exatamente o "
          "texto escrito. Se não houver texto legível, responda texto vazio. Não invente.")
ESQ_COTA = {"type": "object", "properties": {"texto": {"type": "string"}}, "required": ["texto"]}


def _cd():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import cotas_desenho
    return cotas_desenho


def _alvos_cotas(pasta, it, todas):
    """Exigência de texto com valor numa prancha sem texto: [{pdf, pagina, prancha, antes}] para ler as cotas, e os
    fatos. Vazio quando não se aplica (sem valor no esperado, prancha com texto, nada baixado)."""
    if it["tipo"] != "texto" or not _cd().valores(it.get("esperado")):
        return [], []
    filtro = sem_acento(it.get("prancha") or "")
    serve = lambda p: not filtro or filtro in sem_acento(p["descricao"] + " " + p["nome"] + " " + p["arquivo"])
    alvos = []
    for p in todas:
        if p["lado"] != "depois" or not p["tem"] or p["nao_reenviada"] or not serve(p):
            continue
        ws, _t = palavras(os.path.join(pasta, SUB, p["arquivo"]))
        for pag in sorted(ws):
            if len(ws[pag]) < SEM_TEXTO:
                a = par_anterior(todas, p)
                alvos.append({"pdf": p["arquivo"], "pagina": pag, "prancha": _rotulo_planta(p),
                              "antes": {"pdf": a["arquivo"], "pagina": pag} if a and a["tem"] else None})
    if not alvos or len(alvos) > MAX_PRANCHAS_COTA:
        return [], ["Texto convertido em desenho em %d prancha(s): para ler as cotas, diga em \"prancha\" qual delas." % len(alvos)] if alvos else []
    fatos = ["%s: o texto está convertido em desenho (o PDF não tem palavras). A IA vai ler as cotas uma a uma e "
             "procurar %s." % (a["prancha"], " ou ".join(_cd_valor(v) for v in _cd().valores(it["esperado"]))) for a in alvos]
    return alvos, fatos


def _cd_valor(v):
    return ("%.2f" % v).replace(".", ",") + " m"


def _transcrever(png):
    r = _ollama("/api/chat", {
        "model": MODELO, "messages": [{"role": "user", "content": P_COTA, "images": [base64.b64encode(png).decode()]}],
        "format": ESQ_COTA, "stream": False, "think": False, "keep_alive": "30m",
        "options": {"temperature": 0, "seed": 0, "num_ctx": 4096, "num_predict": 80}})
    try:
        t = str(json.loads((r.get("message") or {}).get("content", "")).get("texto", ""))
    except Exception:  # noqa: BLE001
        raise RuntimeError("resposta fora do formato na leitura de cota")
    return "" if t.strip().lower() in ("texto vazio", "vazio") else t.strip()


def _caixa_cota(c):
    return [round(c["x"] - 45), round(c["y"] - 30), round(c["x"] + 45), round(c["y"] + 30)]


def _rodar_cotas(pasta, it, marca):
    """Lê as cotas das pranchas alvo, procura o valor esperado e monta o resultado (rodadas, controle, rótulo e os
    recortes onde o valor apareceu). A planta anterior só é lida se o valor apareceu na nova."""
    cd = _cd()
    vs = cd.valores(it["esperado"])
    toque = lambda: os.utime(marca)
    t0 = time.time()
    certos, conferir, lidas = [], [], 0
    for a in it["cotas"]:
        leit = cd.ler(os.path.join(pasta, SUB, a["pdf"]), a["pagina"] - 1, _transcrever, MODELO, toque=toque)
        lidas += len(leit)
        c, f = cd.procurar(leit, vs)
        certos += [dict(x, alvo=a) for x in c]
        conferir += [dict(x, alvo=a) for x in f]
    quais = " ou ".join(_cd_valor(v) for v in vs)
    ondes = lambda xs: "; ".join("%s: \"%s\"%s" % (x["alvo"]["prancha"], x["a"], "" if x.get("b") in (None, x["a"]) else " / \"%s\"" % x["b"]) for x in xs[:4])
    seg = round(time.time() - t0, 1)
    if certos:
        nova = {"veredito": "cumpriu", "evidencia": "%s escrito em %d lugar(es), com as duas leituras iguais: %s." % (quais, len(certos), ondes(certos)), "segundos": seg}
    elif conferir:
        nova = {"veredito": "nao_sei", "evidencia": "Uma das duas leituras achou %s e a outra discordou: %s." % (quais, ondes(conferir)), "segundos": seg}
    else:
        nova = {"veredito": "nao_sei", "evidencia": "Não achei %s entre as %d cotas lidas." % (quais, lidas), "segundos": seg}
    ctrl, antes_achou = None, None
    alvos_antes = [a for a in it["cotas"] if a.get("antes")]
    if certos and alvos_antes:
        t1, ac = time.time(), []
        for a in alvos_antes:
            leit = cd.ler(os.path.join(pasta, SUB, a["antes"]["pdf"]), a["antes"]["pagina"] - 1, _transcrever, MODELO, toque=toque)
            ac += cd.procurar(leit, vs)[0]
        antes_achou = bool(ac)
        ctrl = {"veredito": "cumpriu" if ac else "nao_cumpriu", "segundos": round(time.time() - t1, 1),
                "evidencia": ("%s também está escrito na planta anterior (%d lugar(es))." % (quais, len(ac))) if ac else
                             "%s não aparece entre as cotas lidas da planta anterior." % quais}
    expl = " Leitura das cotas uma a uma (texto convertido em desenho): método novo, testado em um processo só."
    if certos and antes_achou:
        rot = {"classe": "ambar", "titulo": "Inconclusivo: %s já estava na planta anterior" % quais, "veredito": "", "motivo": "cotas_ja_estava",
               "explicacao": "%s está escrito na planta nova, mas já estava na anterior, que recebeu a exigência: achar o valor não prova a correção. Olhe o recorte." % quais}
    elif certos:
        rot = {"classe": "ambar", "veredito": "cumpriu", "motivo": "cotas_achou",
               "titulo": "Palpite fraco (Cumpriu): %s escrito na planta nova%s" % (quais, ", e não na anterior" if antes_achou is False else ""),
               "explicacao": ("%s aparece escrito na planta nova%s." % (quais, " e não aparecia na anterior" if antes_achou is False else ", sem a planta anterior para comparar")) + expl}
    elif conferir:
        rot = {"classe": "ambar", "titulo": "Inconclusivo: as duas leituras da cota discordam", "veredito": "", "motivo": "cotas_discordam",
               "explicacao": "As duas leituras da IA discordaram onde %s pode estar escrito. Olhe o recorte." % quais}
    else:
        rot = {"classe": "ambar", "titulo": "Inconclusivo: não achei %s nas cotas lidas" % quais, "veredito": "", "motivo": "cotas_nao_achou",
               "explicacao": "Não achei %s entre as %d cotas lidas. Isso não prova que falta: a cota pode ter ficado fora do filtro. Olhe a planta." % (quais, lidas)}
    recs = []
    for x in (certos or conferir)[:MAX_RECORTES]:
        a = x["alvo"]
        r = {"pdf": a["pdf"], "pagina": a["pagina"], "caixa": _caixa_cota(x), "prancha": a["prancha"]}
        if a.get("antes"):  # mesma posição na anterior (sem texto não há como medir o deslocamento): só se cabe na folha
            _ws, tam = palavras(os.path.join(pasta, SUB, a["antes"]["pdf"]))
            w, h = tam.get(a["antes"]["pagina"], (0, 0))
            cx = _caixa_cota(x)
            if cx[2] <= w and cx[3] <= h:
                r["antes"] = {"pdf": a["antes"]["pdf"], "pagina": a["antes"]["pagina"], "caixa": cx}
        recs.append(r)
    return {"rodadas": [dict(nova, margem="cotas")], "controle": ctrl, "rotulo": rot, "recortes": recs}


def preparar(pasta, curadoria):
    """curadoria: [{n, tipo, esperado, termo, termo_antes, prancha, motivo}] (uma por exigência da última CIA; as que
    faltarem ficam "não preparada"). Monta recortes e fatos, mantém o palpite e a conferência do que não mudou e
    grava o palpites.json. Devolve o dicionário gravado."""
    ex = exigencias(pasta)
    if not ex:
        raise RuntimeError("Sem cia-ultima.txt na pasta (ou sem exigências nela): não há o que conferir.")
    cur = {}
    for c in curadoria or []:
        n = c.get("n")
        if not isinstance(n, int) or not 1 <= n <= len(ex):
            raise RuntimeError("n=%r não é uma exigência da última CIA (1 a %d)." % (n, len(ex)))
        if c.get("tipo") not in TIPOS:
            raise RuntimeError("exigência %d: tipo %r inválido (use %s)." % (n, c.get("tipo"), ", ".join(TIPOS)))
        if c["tipo"] in COM_RECORTE and not (c.get("termo") or c.get("termo_antes") or c.get("motivo")):
            raise RuntimeError("exigência %d: falta o termo escrito na planta (termo ou termo_antes), ou o motivo de não haver." % n)
        if c["tipo"] == "texto" and not (c.get("esperado") or "").strip():
            raise RuntimeError("exigência %d: tipo texto pede \"esperado\" (o valor que tem de estar escrito)." % n)
        cur[n] = c
    todas = plantas(pasta)
    ids = _ids_cia(pasta)

    def montar(d):
        antigos = {i["n"]: i for i in d.get("itens") or []}
        itens = []
        for n, (secao, sub, texto) in enumerate(ex, 1):
            c = cur.get(n) or {k: antigos[n][k] for k in ("tipo", "esperado", "termo", "termo_antes", "prancha", "motivo")
                               if n in antigos and antigos[n].get("exigencia") == texto and antigos[n].get(k)}
            it = {"n": n, "secao": secao, "sub": sub, "exigencia": texto, "tipo": c.get("tipo") or "",
                  "esperado": (c.get("esperado") or "").strip(), "termo": (c.get("termo") or "").strip(),
                  "termo_antes": (c.get("termo_antes") or "").strip(), "prancha": (c.get("prancha") or "").strip(),
                  "motivo": (c.get("motivo") or "").strip(), "fatos": [], "recortes": [], "estado": "sem_palpite"}
            if not it["tipo"]:
                it["motivo"] = "Esta exigência não foi preparada para a IA local."
            elif it["tipo"] in COM_RECORTE:
                motivo = it["motivo"]  # sem termo: fica o motivo dado na classificação
                if it["termo"] or it["termo_antes"]:
                    try:
                        it["recortes"], it["fatos"], motivo = _recortes(pasta, it, todas)
                    except (RuntimeError, OSError, subprocess.SubprocessError) as e:
                        motivo = "Não deu para ler a planta (%s)." % str(e)[:160]
                if not it["recortes"]:  # nenhum lugar escrito: a prancha pode ter o texto convertido em desenho
                    try:
                        alvos, fatos_c = _alvos_cotas(pasta, it, todas)
                    except (RuntimeError, OSError, subprocess.SubprocessError):
                        alvos, fatos_c = [], []
                    if alvos:
                        it["cotas"], it["fatos"], motivo = alvos, fatos_c, ""
                    elif fatos_c:
                        it["fatos"] = it["fatos"] + fatos_c
                if motivo:
                    it["motivo"] = motivo
                else:
                    it["motivo"] = ""
                    it["estado"] = "fila"
            elif not it["motivo"]:
                it["motivo"] = ("Remete às exigências acima." if it["tipo"] == "remissiva" else
                                "Confere-se no memorial ou no cadastro do SOL, não na planta.")
            it["assinatura"] = _assinatura(it)
            velho = antigos.get(n)
            if velho and velho.get("exigencia") == texto:
                if velho.get("conferencia"):
                    it["conferencia"] = velho["conferencia"]
                if it["estado"] == "fila" and velho.get("assinatura") == it["assinatura"] and velho.get("estado") == "pronto":
                    guarda = ("estado", "rodadas", "controle", "leitura", "rotulo", "feito_em") + (("recortes",) if it.get("cotas") else ())
                    it.update({k: velho[k] for k in guarda if k in velho})
            itens.append(it)
        d.clear()
        d.update({"versao": 1, "processo": os.path.basename(os.path.normpath(pasta)), "cia": ids[-1] if ids else 0,
                  "plantas": [{k: p[k] for k in ("lado", "id", "arquivo", "nome", "tipo", "descricao", "nao_reenviada")} for p in todas],
                  "modelo": MODELO, "preparado_em": time.strftime("%Y-%m-%dT%H:%M:%S"), "itens": itens})
        return dict(d)
    return _atualizar(pasta, montar)


def valido(pasta, d=None):
    """O palpites.json é da última CIA e das pranchas que estão ativas agora? (motivo, se não)"""
    d = d if d is not None else ler(pasta)
    if not d.get("itens"):
        return "sem palpites"
    ids = _ids_cia(pasta)
    if ids and d.get("cia") != ids[-1]:
        return "os palpites são de uma CIA anterior"
    agora = sorted(p["id"] for p in plantas(pasta) if p["lado"] == "depois")
    if agora != sorted(p["id"] for p in d.get("plantas") or [] if p["lado"] == "depois"):
        return "as pranchas ativas mudaram depois dos palpites"
    return ""


# ------------------------------------------------------------------ Ollama

def _ollama(caminho_, dados=None, timeout=900):
    req = urllib.request.Request(OLLAMA + caminho_, data=None if dados is None else json.dumps(dados).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:  # o corpo do erro diz o motivo; sem ele só aparece "500"
        raise RuntimeError("HTTP %s: %s" % (e.code, e.read().decode("utf-8", "replace")[:300])) from None


def ia_local():
    """(pronta?, motivo). Pronta = o Ollama responde neste PC e o modelo está instalado."""
    try:
        nomes = {m["name"] for m in _ollama("/api/tags", timeout=4)["models"]}
    except Exception:  # noqa: BLE001 — sem Ollama é o caso normal fora do PC de casa
        return False, "A IA local (Ollama) não está ligada neste PC."
    if MODELO not in nomes:
        return False, "O Ollama deste PC não tem o modelo %s." % MODELO
    return True, ""


def perguntar(texto, onde, png):
    t0 = time.time()
    r = _ollama("/api/chat", {
        "model": MODELO, "messages": [{"role": "user", "content": PROMPT.format(pergunta=texto, onde=onde),
                                       "images": [base64.b64encode(png).decode()]}],
        "format": ESQUEMA, "stream": False, "think": False, "keep_alive": "30m",
        "options": {"temperature": 0, "seed": 0, "num_ctx": NUM_CTX, "num_predict": NUM_PREDICT}})
    bruto = (r.get("message") or {}).get("content", "")
    try:
        j = json.loads(bruto)
        v, ev = j.get("veredito"), str(j.get("evidencia", ""))
        if v not in VEREDITOS:
            raise ValueError(v)
    except Exception:  # noqa: BLE001
        raise RuntimeError("resposta fora do formato: " + bruto[:200])
    return {"veredito": v, "evidencia": ev, "segundos": round(time.time() - t0, 1)}


def agregar(partes):
    """Vários recortes → um veredito. Conservador: conflito vira nao_sei."""
    vs = {p["veredito"] for p in partes}
    if "cumpriu" in vs and "nao_cumpriu" in vs:
        return "nao_sei"
    return "nao_cumpriu" if "nao_cumpriu" in vs else "cumpriu" if "cumpriu" in vs else "nao_sei"


def _rodada(pasta, it, recs, margem, perg):
    partes = []
    for k, r in enumerate(recs, 1):
        onde = ("recorte %d de %d: " % (k, len(recs)) if len(recs) > 1 else "") + "recorte da prancha em volta do elemento citado"
        p = perguntar(perg, onde, recorte(os.path.join(pasta, SUB, r["pdf"]), r["pagina"], r["caixa"], margem))
        p["onde"] = onde
        partes.append(p)
    ev = " | ".join(("[recorte %d] " % k if len(partes) > 1 else "") + p["evidencia"] for k, p in enumerate(partes, 1) if p["veredito"] != "nao_sei") \
        or partes[0]["evidencia"]
    return {"veredito": agregar(partes), "evidencia": ev, "segundos": round(sum(p["segundos"] for p in partes), 1)}


# ------------------------------------------------------------------ conta com a cota lida (18/11/2026)
# Bateria da IA local (servidor, ~/ia-local/bateria/PLACAR.md, rodadas 1–3): em exigência com número, o modelo LÊ o
# valor escrito no elemento e o CÓDIGO compara com o exigido. Palpite firme só quando a conta e o veredito da IA
# concordam: 0 erro em 21 itens da parte guardada (15 respondidos, 6 "não sei"), com o recorte mais apertado (30).
NUM = re.compile(r"\d+[,.]?\d*\s*(m²|m2|metros?|m\b|cm|mm|pessoas?)|pessoa por m|por m²|\bm[ií]nim|\bm[aá]xim", re.I)
MARGEM_LEITURA = 30
ESQ_NUM = {"type": "object", "properties": {
    "comparacao": {"type": "string", "enum": ["minimo", "maior_que", "maximo", "taxa_pessoas_por_m2"]},
    "exigido": {"type": "number"}, "valor_no_elemento": {"type": ["number", "null"]},
    "area_m2": {"type": ["number", "null"]}, "evidencia": {"type": "string"}},
    "required": ["comparacao", "exigido", "valor_no_elemento", "area_m2", "evidencia"]}
# O mesmo texto da bateria (harness/bateria_num.py). Mudou aqui, os números da bateria deixam de valer.
PROMPT_NUM = """Você lê uma planta de PPCI (prevenção de incêndio) para um analista do Corpo de Bombeiros. A imagem é {onde}.

{pergunta}

NÃO decida se cumpriu: só preencha o JSON; quem compara é um programa.
- "comparacao": o que a exigência pede. "minimo" (pelo menos X), "maior_que" (maior que X), "maximo" (no máximo X),
  "taxa_pessoas_por_m2" (população proporcional à área).
- "exigido": o número da exigência. Larguras e distâncias SEMPRE em metros (90 cm = 0.9). Na taxa: pessoas por m².
- "valor_no_elemento": o número que está ESCRITO na imagem no elemento citado (a cota de largura em metros; na taxa, o
  número de pessoas escrito). null se o elemento ou a cota não aparece, está ilegível, ou você não tem certeza de que a
  cota é desse elemento. Não calcule nem estime pela escala.
- "area_m2": só na taxa, a área escrita no próprio elemento; senão null.
- "evidencia": copie exatamente o que leu e onde está na imagem."""
COMPARA = {"minimo": "mín.", "maior_que": "maior que", "maximo": "máx.", "taxa_pessoas_por_m2": "mín."}


def com_numero(it):
    return it.get("tipo") == "texto" and bool(NUM.search("%s %s" % (it.get("exigencia") or "", it.get("esperado") or "")))


def numerico(j):
    """A conta: {veredito, comparacao, exigido, lido} a partir do que a IA leu. Sem valor lido = nao_sei."""
    v, x, c = j.get("valor_no_elemento"), j.get("exigido"), j.get("comparacao")
    out = {"veredito": "nao_sei", "comparacao": c, "exigido": x, "lido": v}
    if v is None or x is None:
        return out
    if c != "taxa_pessoas_por_m2":
        v = v / 100 if v >= 20 else v      # cota em cm escrita como 110
        x = x / 100 if x >= 20 else x
        ok = v >= x - 1e-6 if c == "minimo" else v > x + 1e-6 if c == "maior_que" else v <= x + 1e-6
    else:
        a = j.get("area_m2")
        if not a:
            return out
        x = int(a * x + 1e-6)             # "na ordem de": 34,72 m² x 1 = 34 pessoas, 35 atende
        ok = v >= x
    out.update(veredito="cumpriu" if ok else "nao_cumpriu", exigido=x, lido=v)
    return out


def fmt_valor(x, c):
    if x is None:
        return "?"
    if c == "taxa_pessoas_por_m2":
        return "%d pessoas" % round(x)
    return ("%.2f" % x).rstrip("0").rstrip(".").replace(".", ",") + " m"


def _leitura(pasta, it, recs):
    """Conta com a cota lida em cada recorte novo (margem 30). Recortes que discordam: nao_sei."""
    partes, t0 = [], time.time()
    for k, r in enumerate(recs, 1):
        onde = ("recorte %d de %d: " % (k, len(recs)) if len(recs) > 1 else "") + "recorte da prancha em volta do elemento citado"
        png = recorte(os.path.join(pasta, SUB, r["pdf"]), r["pagina"], r["caixa"], MARGEM_LEITURA)
        resp = _ollama("/api/chat", {
            "model": MODELO, "messages": [{"role": "user", "content": PROMPT_NUM.format(pergunta=pergunta(it), onde=onde),
                                           "images": [base64.b64encode(png).decode()]}],
            "format": ESQ_NUM, "stream": False, "think": False, "keep_alive": "30m",
            "options": {"temperature": 0, "seed": 0, "num_ctx": NUM_CTX, "num_predict": NUM_PREDICT}})
        try:
            j = json.loads((resp.get("message") or {}).get("content", ""))
            p = numerico(j)
            p["evidencia"] = str(j.get("evidencia", ""))
        except Exception:  # noqa: BLE001
            p = {"veredito": "nao_sei", "evidencia": "resposta fora do formato"}
        partes.append(p)
    lidos = [p for p in partes if p["veredito"] != "nao_sei"]
    base = lidos[0] if lidos else partes[0]
    ev = "; ".join("%s lido %s (exigido %s %s)" % (("[recorte %d] " % k if len(partes) > 1 else ""), fmt_valor(p.get("lido"), p.get("comparacao")),
                                                   COMPARA.get(p.get("comparacao"), ""), fmt_valor(p.get("exigido"), p.get("comparacao")))
                   for k, p in enumerate(partes, 1) if p["veredito"] != "nao_sei") or "a IA não leu a cota do elemento"
    return {"veredito": agregar(partes), "comparacao": base.get("comparacao"), "exigido": base.get("exigido"),
            "lido": base.get("lido"), "evidencia": "Conta do programa: %s. %s" % (ev, " | ".join(p["evidencia"] for p in partes)[:600]),
            "segundos": round(time.time() - t0, 1), "margem": MARGEM_LEITURA}


# Largura de trecho (corredor, circulação, passagem, rota): vale o ponto mais estreito, e o RT pode cotar só onde passa do
# mínimo (caso da copa, julgado pelo Átila em 19/11/2026). Uma cota lida não prova o trecho inteiro: o verde vira âmbar.
# Só rebaixa — nunca cria exigência nem decide o que é rota de fuga (isso vem do texto que o analista escreveu).
# Porta, vão e escada sozinhos têm uma cota só e seguem a regra normal.
TRECHO = re.compile(r"corredor|circula[cç]|passage(m|ns)|\brotas?\b|trecho|faixa livre|acesso(s)? (de|à|a) sa[ií]da", re.I)


def largura_de_trecho(exig, leitura=None):
    if not exig or not TRECHO.search(exig) or not re.search(r"largura|\d+[,.]\d+\s*m\b|\d+\s*cm", exig, re.I):
        return False
    return not leitura or leitura.get("comparacao") in (None, "minimo", "maior_que")


def conclusao(tipo, rodadas, ctrl, leitura=None, exig=""):
    r = _conclusao(tipo, rodadas, ctrl, leitura)
    if r["classe"] == "verde" and largura_de_trecho(exig, leitura):
        r = {"classe": "ambar", "titulo": "Medir na planta: largura de trecho vale no ponto mais estreito",
             "explicacao": "A IA achou cota que atende (%s), mas em corredor ou circulação a largura vale no ponto mais estreito, "
                           "e o RT pode ter cotado só onde passa do mínimo. Confira com a régua o trecho mais estreito."
                           % r["titulo"].split(": ", 1)[-1],
             "veredito": "", "motivo": "trecho_estreito"}
    return r


def _conclusao(tipo, rodadas, ctrl, leitura=None):
    """Rótulo honesto do palpite: {classe, titulo, explicacao, veredito, motivo}. O título já diz o porquê; o motivo
    (código curto) vai junto da conferência do analista para medir, depois, qual tipo de palpite erra.
    veredito só vem quando há palpite a mostrar."""
    vs = [r["veredito"] for r in rodadas]
    def rot(classe, titulo, expl, v="", motivo=""):
        return {"classe": classe, "titulo": titulo, "explicacao": expl, "veredito": v, "motivo": motivo}
    if len(set(vs)) > 1:
        return rot("ambar", "Inconclusivo: a resposta muda com o tamanho do recorte",
                   "A IA respondeu %s conforme o recorte. Olhe a planta." % ", ".join(NOME[v] for v in vs), motivo="muda_recorte")
    v = vs[0]
    if v == "nao_sei":
        return rot("ambar", "Inconclusivo: a IA não achou o elemento no recorte",
                   "Respondeu \"não sei\" nos três tamanhos de recorte (elemento fora do recorte, ilegível ou ambíguo). Olhe a planta.",
                   motivo="ia_nao_sabe")
    if ctrl and ctrl["veredito"] == "cumpriu":
        return rot("ambar", "Inconclusivo: a IA também diz \"cumpriu\" na planta anterior",
                   "A planta anterior recebeu a exigência, então lá o certo era \"não cumpriu\". A IA não distingue o antes do "
                   "depois aqui: o palpite \"%s\" não vale." % NOME[v], motivo="contraprova_falhou")
    if leitura:
        lv, c = leitura["veredito"], leitura.get("comparacao")
        conta = "cota lida %s, exigido %s %s" % (fmt_valor(leitura.get("lido"), c), COMPARA.get(c, ""), fmt_valor(leitura.get("exigido"), c))
        if lv == "nao_sei":
            return rot("ambar", "Inconclusivo: a IA diz %s, mas não leu a cota para a conta" % NOME[v],
                       "O veredito da IA não foi conferido pela conta do programa: ela não leu (ou não teve certeza de) a cota do "
                       "próprio elemento. Olhe a cota.", motivo="conta_sem_leitura")
        if lv != v:
            return rot("ambar", "Inconclusivo: a IA diz %s, mas a conta diz %s (%s)" % (NOME[v], NOME[lv], conta),
                       "O veredito e a conta com a cota que a própria IA leu discordam: ou ela leu a cota de outro elemento, ou "
                       "errou o veredito. Confira a cota do elemento.", motivo="conta_discorda")
        expl = "O veredito da IA e a conta do programa com a cota que ela leu concordam (%s)%s. Na bateria, esse acordo " \
               "teve 0 erro em 21 itens guardados." % (conta, "; e na planta anterior ela disse \"não cumpriu\"" if ctrl and ctrl["veredito"] == "nao_cumpriu" else "")
        return rot("verde" if v == "cumpriu" else "vermelho",
                   ("Parece cumprida: " if v == "cumpriu" else "Parece não cumprida: ") + conta, expl, v, motivo="conta_confirma")
    if not ctrl:
        return rot("ambar", "Palpite fraco (%s): sem a planta anterior para comparar" % NOME[v],
                   "Igual nos três tamanhos de recorte, mas sem a planta anterior para a contraprova.", v, motivo="sem_contraprova")
    if v == "cumpriu" and ctrl["veredito"] == "nao_sei":
        return rot("ambar", "Palpite fraco (Cumpriu): na planta anterior a IA não soube",
                   "Na planta anterior a IA respondeu \"não sei\": o contraste com o antes não foi confirmado.", v, motivo="contraprova_nao_sei")
    if tipo != "texto":
        return rot("ambar", "Palpite fraco (%s): tipo de exigência em que a IA erra muito" % NOME[v],
                   "Igual nos três tamanhos de recorte, mas %s é um tipo em que a IA errou muito nos testes." % TIPOS.get(tipo, tipo).lower(),
                   v, motivo="tipo_fraco")
    if v == "cumpriu":
        return rot("verde", "Parece cumprida: o valor pedido aparece na planta nova e não na anterior",
                   "Igual nos três tamanhos de recorte e a IA disse \"não cumpriu\" na planta anterior.", v, motivo="contraprova_confirma")
    return rot("vermelho", "Parece não cumprida: a planta nova continua sem o valor pedido",
               "Igual nos três tamanhos de recorte" + (" e a IA também disse \"não cumpriu\" na planta anterior." if ctrl["veredito"] == "nao_cumpriu" else "."),
               v, motivo="continua_igual")


def rodar(pasta, de_novo=False, aviso=print):
    """Roda a IA local nos itens da fila (e nos que falharam, com de_novo). Grava depois de cada item. Devolve
    (feitos, motivo de não ter rodado)."""
    ok, motivo = ia_local()
    if not ok:
        return 0, motivo
    marca = os.path.join(pasta, SUB, ".rodando")
    try:
        if time.time() - os.path.getmtime(marca) < 180:
            return 0, "Já há uma rodada da IA local neste processo."
    except OSError:
        pass
    os.makedirs(os.path.join(pasta, SUB), exist_ok=True)
    # item que ficou "rodando" de uma rodada que caiu volta para a fila (não há outra rodada: a marca acima diria)
    _atualizar(pasta, lambda x: [i.update(estado="fila") for i in x.get("itens") or [] if i.get("estado") == "rodando"])
    feitos, tentados = 0, set()
    try:
        while True:
            with open(marca, "w") as fh:
                fh.write(str(os.getpid()))
            d = ler(pasta)
            it = next((i for i in d.get("itens") or [] if i["n"] not in tentados and
                       (i.get("estado") == "fila" or (de_novo and i.get("estado") == "falhou"))), None)
            if it is None:
                break
            n, ass = it["n"], it["assinatura"]
            tentados.add(n)
            _atualizar(pasta, lambda x: _item(x, n).update(estado="rodando"))
            novos = [r for r in it["recortes"] if not r.get("nao_reenviada")]
            antes = [r["antes"] for r in novos if r.get("antes")]
            res = {"estado": "pronto", "feito_em": time.strftime("%Y-%m-%dT%H:%M:%S"), "rodadas": [], "controle": None}
            try:
                if it.get("cotas"):  # prancha com o texto convertido em desenho: lê as cotas, sem os três tamanhos
                    res.update(_rodar_cotas(pasta, it, marca))
                else:
                    perg = pergunta(it)
                    for m in MARGENS:
                        os.utime(marca)
                        res["rodadas"].append(dict(_rodada(pasta, it, novos, m, perg), margem=m))
                    if antes:
                        os.utime(marca)
                        res["controle"] = _rodada(pasta, it, antes, MARGENS[0], perg)
                    if com_numero(it) and len({r["veredito"] for r in res["rodadas"]}) == 1 and res["rodadas"][0]["veredito"] != "nao_sei":
                        os.utime(marca)
                        res["leitura"] = _leitura(pasta, it, novos)
                    res["rotulo"] = conclusao(it["tipo"], res["rodadas"], res["controle"], res.get("leitura"), it.get("exigencia") or "")
                    # 2.13.9: classificação feita pela IA local (medida em 18/11/2026: tipo igual ao do Claude em 8 de
                    # 16) segura o palpite em "fraco": verde e vermelho só com a classificação conferida
                    rot = res["rotulo"]
                    if str(d.get("classificado_por") or "").startswith("IA local") and rot.get("classe") in ("verde", "vermelho"):
                        res["rotulo"] = dict(rot, classe="ambar", motivo=rot.get("motivo", "") + "+ia_escolheu_onde",
                                             titulo="Palpite fraco (%s): quem escolheu onde olhar foi a IA local" % NOME[rot["veredito"]],
                                             explicacao=rot["titulo"] + ". " + rot["explicacao"] + " Fraco porque quem escolheu onde olhar "
                                             "foi a IA local, ainda em teste.")
            except Exception as e:  # noqa: BLE001 — um item com problema não derruba os outros; nunca vira "não sei"
                res = {"estado": "falhou", "erro": "%s: %s" % (type(e).__name__, str(e)[:300]), "feito_em": res["feito_em"]}
            def gravar(x, n=n, ass=ass, res=res):
                alvo = _item(x, n)
                if alvo and alvo.get("assinatura") == ass:  # a conversa pode ter preparado de novo no meio da rodada
                    for k in ("rodadas", "controle", "leitura", "rotulo", "erro") + (("recortes",) if alvo.get("cotas") else ()):
                        alvo.pop(k, None)
                    alvo.update(res)
            _atualizar(pasta, gravar)
            feitos += 1
            aviso("exigência %d: %s" % (n, (res.get("rotulo") or {}).get("titulo") or "falhou (%s)" % res.get("erro", "")))
    finally:
        try:
            os.remove(marca)
        except OSError:
            pass
    return feitos, ""


def rodando(pasta):
    try:
        return time.time() - os.path.getmtime(os.path.join(pasta, SUB, ".rodando")) < 180
    except OSError:
        return False


IMG_CONF = re.compile(r"^conferencia-n(\d{1,3})-(\d)\.(png|jpg)$")  # sincronizar/enviar levam este nome ao servidor
IMG_DATA = re.compile(r"^data:image/(png|jpeg);base64,([A-Za-z0-9+/=\s]+)$")
MAX_IMG_CONF, MAX_IMG_BYTES = 4, 6 * 1024 * 1024


def _gravar_imagens(pasta, n, urls):
    """19/11/2026 (pedido do Átila): print/recorte marcado que o analista junta à conferência, para mostrar o que a IA
    errou. Fica na pasta do processo como conferencia-n<N>-<k>.png|jpg (sobe ao servidor no Sincronizar, nunca ao Git);
    as imagens antigas da mesma exigência saem. Devolve os nomes gravados."""
    for nome in os.listdir(pasta):
        m = IMG_CONF.match(nome)
        if m and int(m.group(1)) == n:
            os.remove(os.path.join(pasta, nome))
    nomes = []
    for url in (urls or [])[:MAX_IMG_CONF]:
        m = IMG_DATA.match(url or "")
        if not m:
            continue
        dados = base64.b64decode(m.group(2))
        if not dados or len(dados) > MAX_IMG_BYTES:
            continue
        nome = "conferencia-n%d-%d.%s" % (n, len(nomes) + 1, "png" if m.group(1) == "png" else "jpg")
        with open(os.path.join(pasta, nome), "wb") as fh:
            fh.write(dados)
        nomes.append(nome)
    return nomes


def imagem_conferencia(pasta, nome):
    """Bytes de uma imagem da conferência (só nomes do padrão, sem caminho)."""
    if not IMG_CONF.match(nome or ""):
        raise RuntimeError("nome de imagem inválido")
    with open(os.path.join(pasta, nome), "rb") as fh:
        return fh.read()


def responder(pasta, respostas):
    """Conferência do analista: {n: {resposta, nota, imagens?}}; resposta em cumpriu | nao_cumpriu | parcial | nao_da.
    imagens: lista de data: URLs (substitui as gravadas da exigência); sem a chave, as já gravadas ficam."""
    novas = {}
    for n, r in (respostas or {}).items():
        if isinstance(r, dict) and "imagens" in r and (r.get("resposta") in ("cumpriu", "nao_cumpriu", "parcial", "nao_da")):
            novas[int(n)] = _gravar_imagens(pasta, int(n), r.get("imagens") or [])

    def gravar(d):
        for n, r in (respostas or {}).items():
            it = _item(d, int(n))
            if it is not None and (r or {}).get("resposta") in ("cumpriu", "nao_cumpriu", "parcial", "nao_da"):
                rot, lt = it.get("rotulo") or {}, it.get("leitura") or {}
                imagens = novas[int(n)] if int(n) in novas else (it.get("conferencia") or {}).get("imagens") or []
                # 18/11/2026: o que a IA disse e por quê vai junto da resposta — é o gabarito para medir, por motivo,
                # onde ela erra (~/ia-local/conferencias.py junta tudo para o treino)
                it["conferencia"] = {"resposta": r["resposta"], "nota": (r.get("nota") or "").strip()[:1000],
                                     "em": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                     "palpite": rot.get("titulo") or "sem palpite", "motivo": rot.get("motivo") or "",
                                     "veredito_ia": rot.get("veredito") or "", "tipo": it.get("tipo"), "modelo": MODELO,
                                     "leitura": {k: lt.get(k) for k in ("veredito", "comparacao", "exigido", "lido")} if lt else None,
                                     "imagens": imagens}
    _atualizar(pasta, gravar)


def estado(pasta):
    """O que o quadro azul do SSEG.exe mostra: o palpites.json mais como está a IA local neste PC."""
    d = ler(pasta)
    ok, motivo = ia_local()
    pl = plantas(pasta)
    for it in d.get("itens") or []:
        it["tipo_nome"] = TIPOS.get(it.get("tipo"), "Não preparada")
        it["confianca"] = CONFIANCA.get(it.get("tipo"), "")
    return {"palpites": d, "velho": valido(pasta, d) if d.get("itens") else "", "ia": {"pronta": ok, "motivo": motivo, "modelo": MODELO},
            "rodando": rodando(pasta), "faltam_plantas": [_rotulo_planta(p) for p in pl if not p["tem"]],
            "reanalise": bool(exigencias(pasta)), "poppler": tem_poppler()}


# ------------------------------------------------------------------ textos para a conversa

def texto_exigencias(pasta):
    ex = exigencias(pasta)
    if not ex:
        return "Sem cia-ultima.txt na pasta, ou sem exigências nela: não há reanálise para conferir."
    L = ["EXIGÊNCIAS DA ÚLTIMA CIA (cia-ultima.txt), na ordem do PDF:"]
    for n, (secao, sub, texto) in enumerate(ex, 1):
        L.append("%d. [%s] %s" % (n, " / ".join(x for x in (secao, sub) if x), texto))
    L += ["", "PRANCHAS (api-<id>.json do SOL):"]
    for p in plantas(pasta):
        sit = ("anterior: a que a última CIA analisou e foi trocada" if p["lado"] == "antes" else
               "ativa, NÃO reenviada (a mesma que a última CIA analisou)" if p["nao_reenviada"] else "ativa, reenviada depois da última CIA")
        L.append("- %s · %s%s" % (_rotulo_planta(p), sit, "" if p["tem"] else " · FALTA BAIXAR (o programa baixa pela aba do SOL)"))
    return "\n".join(L)


def texto_procurar(pasta, termo):
    L = []
    for p in plantas(pasta):
        if not p["tem"]:
            L.append("- %s: falta baixar" % _rotulo_planta(p))
            continue
        ws, _tam = palavras(os.path.join(pasta, SUB, p["arquivo"]))
        for pag in sorted(ws):
            ocs = ocorrencias(ws[pag], termo)
            L.append("- %s [%s]%s: %d vez(es)" % (_rotulo_planta(p), "nova" if p["lado"] == "depois" else "anterior",
                                                  " pág. %d" % pag if len(ws) > 1 else "", len(ocs)))
            for x, y in ocs[:6]:
                perto = frases([w for w in ws[pag] if abs((w[1] + w[3]) / 2 - x) <= 110 and abs((w[2] + w[4]) / 2 - y) <= 28])
                L.append("    em volta: " + " · ".join(perto)[:300])
    return "\n".join(L) or "Sem pranchas no cadastro."


def texto_ver(d):
    if not d.get("itens"):
        return "Sem palpites.json nesta pasta."
    L = ["PALPITES DA IA LOCAL (%s) · preparados em %s" % (d.get("modelo"), d.get("preparado_em"))]
    for it in d["itens"]:
        if it["estado"] == "pronto":
            sit = it["rotulo"]["titulo"]
        elif it["estado"] == "fila":
            sit = "na fila da IA local (%d recorte(s))" % len(it["recortes"])
        elif it["estado"] == "rodando":
            sit = "a IA local está olhando"
        elif it["estado"] == "falhou":
            sit = "a IA falhou: " + it.get("erro", "")[:120]
        else:
            sit = "sem palpite: " + it.get("motivo", "")
        L.append("%d. [%s] %s" % (it["n"], TIPOS.get(it["tipo"], "não preparada"), sit))
        L += ["     fato: " + f for f in it.get("fatos") or []]
        if it.get("leitura"):
            L.append("     conta: " + it["leitura"].get("evidencia", "")[:300])
        if it.get("conferencia"):
            c = it["conferencia"]
            L.append("     analista: %s%s" % (c["resposta"], " — " + c["nota"] if c.get("nota") else ""))
    return "\n".join(L)


# ------------------------------------------------------------------ classificação pela IA local (17/11/2026)
# Pedido do Átila: a classificação das exigências não depende do Claude; a IA local classifica e o Claude só apresenta
# o quadro azul. A IA diz o tipo, o valor esperado e a palavra escrita na planta; o código confere se a palavra existe
# nas pranchas (e, se não existe, procura uma palavra da própria exigência que exista em poucos lugares).

ESQ_CLASS = {"type": "object", "required": ["tipo", "esperado", "termo", "termo_antes", "prancha", "motivo"],
             "properties": {"tipo": {"type": "string", "enum": list(TIPOS)}, "esperado": {"type": "string"},
                            "termo": {"type": "string"}, "termo_antes": {"type": "string"},
                            "prancha": {"type": "string"}, "motivo": {"type": "string"}}}
P_CLASS = """Você organiza a conferência de uma reanálise de PPCI (prevenção de incêndio, Corpo de Bombeiros do RS).
A exigência abaixo foi feita na análise anterior. Classifique como ela se confere agora, sem decidir se foi cumprida.

Seção da CIA: {secao}
Exigência: "{exig}"
Pranchas do processo (descrição no SOL): {pranchas}

Responda só com JSON:
- tipo: "texto" (confere-se um VALOR escrito na planta: cota, largura, distância, área, população, código, divisão),
  "desenho" (símbolo, traçado, posição ou quantidade de elemento desenhado), "ausencia" (algo que tinha de passar a
  existir na planta: nota, legenda, rótulo, representação), "fora_da_planta" (documento: ART/RRT, procuração, contrato,
  assinatura; cadastro do SOL: campo de medidas, área, riscos específicos; memorial) ou "remissiva" (só remete a
  inconformidades já citadas).
- esperado: o que tem de estar escrito para estar cumprida, com o valor quando houver (obrigatório em "texto").
- termo: palavras que provavelmente estão ESCRITAS na planta no ponto em que se confere (nome do ambiente, rótulo,
  título da nota, sigla). Curto (1 a 3 palavras), em maiúsculas como em planta. Vazio se não houver.
- termo_antes: texto que estava na planta anterior e devia sair ou mudar (vazio se não houver).
- prancha: parte da descrição da prancha onde se confere (ex.: "corte", "implantação"), vazio se não souber.
- motivo: só para fora_da_planta, remissiva ou quando não há lugar escrito para apontar: diga em uma frase por quê."""

PALAVRAS_FRACAS = set("deve deverá devera conforme item observar sendo para pela pelo como entre sobre ainda ambos ambas "
                      "planta prancha projeto representar representado representada informar informada informado "
                      "apresentar edificacao medidas seguranca segurança incendio incêndio "
                      # 18/11/2026: "MESMA" (de "na mesma camada") venceu "MOEGA" na medição da classificação
                      "mesma mesmo mesmas mesmos camada camadas cada todos todas outro outra outros outras devem "
                      "previsto prevista previstas previstos exigida exigido aplicavel aplicaveis caso quando "
                      "acordo forma maneira demais respectivo respectiva indicar indicado indicada".split())


def _onde(pasta, todas, termo, lado="depois", prancha=""):
    """[(prancha, n)] das pranchas do lado pedido em que o termo está escrito."""
    filtro = sem_acento(prancha)
    out = []
    for p in todas:
        if p["lado"] != lado or not p["tem"] or (filtro and filtro not in sem_acento(p["descricao"] + " " + p["nome"] + " " + p["arquivo"])):
            continue
        ws, _t = palavras(os.path.join(pasta, SUB, p["arquivo"]))
        n = sum(len(ocorrencias(ws[pg], termo)) for pg in ws)
        if n:
            out.append((p, n))
    return out


def _termo_valido(pasta, todas, c, texto):
    """Confere o termo proposto; se não está escrito nas pranchas novas, tenta o termo_antes nas anteriores e depois uma
    palavra da própria exigência que apareça em 1 a MAX_RECORTES lugares. Devolve a classificação ajustada."""
    if c["tipo"] not in COM_RECORTE:
        return c
    for campo, lado in (("termo", "depois"), ("termo_antes", "antes")):
        t = (c.get(campo) or "").strip()
        if t:
            achou = _onde(pasta, todas, t, lado, c.get("prancha") or "") or _onde(pasta, todas, t, lado)
            if achou and sum(n for _p, n in achou) <= MAX_RECORTES * 3:
                if not _onde(pasta, todas, t, lado, c.get("prancha") or ""):
                    c["prancha"] = ""
                return c
            c[campo] = ""
    cands = [w for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}", texto) if sem_acento(w) not in PALAVRAS_FRACAS and (len(w) >= 5 or w.isupper())]
    # palavra em MAIÚSCULAS na exigência ("MOEGA", "PCF") é nome próprio do projeto: vem antes das outras
    cands = sorted(dict.fromkeys(cands), key=lambda w: not w.isupper())
    melhor, nota = None, None   # nota = (está em maiúsculas na exigência, -ocorrências): maior é melhor
    for w in cands:
        achou = _onde(pasta, todas, w, "depois", c.get("prancha") or "")
        n = sum(k for _p, k in achou)
        if 1 <= n <= MAX_RECORTES and (nota is None or (w.isupper(), -n) > nota):
            melhor, nota = (w.upper(), n), (w.isupper(), -n)
    if melhor:
        c["termo"] = melhor[0]
        return c
    c["motivo"] = c.get("motivo") or "A IA local não achou na planta nova uma palavra escrita no ponto desta exigência."
    return c


def classificar(pasta, aviso=None):
    """Classificação de cada exigência da última CIA pela IA local, já conferida contra as pranchas. [{n, tipo, ...}]."""
    ex = exigencias(pasta)
    todas = plantas(pasta)
    descr = "; ".join(sorted({p["descricao"] or p["nome"] for p in todas if p["lado"] == "depois"})) or "(nenhuma)"
    out = []
    for n, (secao, sub, texto) in enumerate(ex, 1):
        r = _ollama("/api/chat", {"model": MODELO, "messages": [{"role": "user", "content": P_CLASS.format(
            secao=" / ".join(x for x in (secao, sub) if x) or "(sem seção)", exig=texto, pranchas=descr)}],
            "format": ESQ_CLASS, "stream": False, "think": False, "keep_alive": "30m",
            "options": {"temperature": 0, "seed": 0, "num_ctx": 4096, "num_predict": 400}})
        try:
            c = json.loads((r.get("message") or {}).get("content", ""))
        except ValueError:
            c = {"tipo": "fora_da_planta", "motivo": "a IA local não classificou esta exigência"}
        c = {k: str(c.get(k) or "").strip() for k in ("tipo", "esperado", "termo", "termo_antes", "prancha", "motivo")}
        if c["tipo"] not in TIPOS:
            c["tipo"] = "fora_da_planta"
        if c["tipo"] == "texto" and not c["esperado"]:
            c["tipo"] = "ausencia"
        if c["tipo"] in COM_RECORTE and not c["esperado"]:
            c["esperado"] = texto[:300]
        c = _termo_valido(pasta, todas, c, texto + " " + c["esperado"])
        if c["tipo"] in COM_RECORTE and not (c["termo"] or c["termo_antes"] or c["motivo"]):
            c["motivo"] = "sem lugar escrito na planta para apontar o recorte"
        c["n"] = n
        out.append(c)
        if aviso:
            aviso("exigência %d: %s%s" % (n, c["tipo"], " · termo \"%s\"" % (c["termo"] or c["termo_antes"]) if c["termo"] or c["termo_antes"] else ""))
    return out


def automatico(pasta, aviso=print):
    """O que o SSEG.exe roda em segundo plano na reanálise: classifica pela IA local quando ainda não há classificação
    válida (nada do Claude é preciso), prepara e roda. Classificação já gravada (pela IA ou pelo Claude) é mantida."""
    ok, motivo = ia_local()
    if not ok:
        return 0, motivo
    if not exigencias(pasta):
        return 0, "Sem exigências da última CIA na pasta."
    d = ler(pasta)
    if not d.get("itens") or valido(pasta, d) or not any(i.get("tipo") for i in d.get("itens") or []):
        marca = os.path.join(pasta, SUB, ".rodando")   # o quadro azul mostra "classificando" enquanto isto corre
        if rodando(pasta):
            return 0, "Já há uma rodada da IA local neste processo."
        os.makedirs(os.path.join(pasta, SUB), exist_ok=True)

        def toque(t):
            with open(marca, "w") as fh:
                fh.write("classificando")
            aviso(t)
        try:
            toque("classificando as exigências da última CIA")
            cur = classificar(pasta, toque)
            preparar(pasta, cur)
            _atualizar(pasta, lambda x: x.update(classificado_por="IA local (%s)" % MODELO))
        finally:
            try:
                os.remove(marca)
            except OSError:
                pass
    r = rodar(pasta, aviso=aviso)
    try:  # o resumo que vai ao chat no passo 2 (amarelo × azul) acompanha os palpites
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import resumo_ia
        resumo_ia.gravar(pasta)
    except Exception:  # noqa: BLE001 — o resumo nunca derruba a rodada
        pass
    return r


# ------------------------------------------------------------------ linha de comando

def args_parser(sp):
    sp.add_argument("--pasta", required=True, help="pasta do processo")
    sub = sp.add_subparsers(dest="acao", required=True)
    sub.add_parser("exigencias", help="exigências da última CIA, numeradas, e as pranchas")
    p = sub.add_parser("procurar", help="onde um termo está escrito nas pranchas")
    p.add_argument("termo")
    p = sub.add_parser("preparar", help="classificação das exigências (JSON) → recortes, fatos e fila da IA local")
    p.add_argument("json", help="lista em JSON como argumento (entre aspas simples), ou - para ler da entrada")
    p = sub.add_parser("rodar", help="roda a IA local nos itens da fila")
    p.add_argument("--de-novo", action="store_true", help="tenta de novo os que falharam")
    sub.add_parser("ver", help="mostra o palpites.json")
    sub.add_parser("estado", help="JSON com o estado (uso do programa)")
    sub.add_parser("classificar", help="a IA local classifica as exigências (JSON na saída, nada gravado)")
    sub.add_parser("auto", help="classifica pela IA local se faltar, prepara e roda (o que o SSEG.exe chama)")


def principal(args):
    pasta = os.path.abspath(args.pasta)
    if not os.path.isdir(pasta):
        sys.exit("pasta não encontrada: " + pasta)
    if args.acao == "exigencias":
        print(texto_exigencias(pasta))
    elif args.acao == "procurar":
        print(texto_procurar(pasta, args.termo))
    elif args.acao == "preparar":
        bruto = sys.stdin.read() if args.json == "-" else args.json
        try:
            cur = json.loads(bruto)
            if not isinstance(cur, list):
                raise ValueError("o JSON tem de ser uma lista")
            d = preparar(pasta, cur)
        except (ValueError, RuntimeError) as e:
            sys.exit("Não preparei: %s" % e)
        print(texto_ver(d))
        ok, motivo = ia_local()
        print("\n" + ("A IA local roda os itens da fila em segundo plano, pelo programa. " if ok else motivo + " Os itens ficam sem palpite, só com os fatos. ")
              + "Responda com o bloco sseg-palpites: o quadro azul é desenhado pelo programa a partir do palpites.json.")
    elif args.acao == "rodar":
        n, motivo = rodar(pasta, args.de_novo)
        print(motivo or "%d item(ns) rodado(s)." % n)
    elif args.acao == "ver":
        print(texto_ver(ler(pasta)))
    elif args.acao == "estado":
        print(json.dumps(estado(pasta), ensure_ascii=False))
    elif args.acao == "classificar":
        ok, motivo = ia_local()
        print(json.dumps(classificar(pasta, lambda t: print(t, file=sys.stderr)), ensure_ascii=False, indent=1) if ok else motivo)
    elif args.acao == "auto":
        n, motivo = automatico(pasta)
        print(motivo or "%d item(ns) rodado(s)." % n)


if __name__ == "__main__":
    import argparse
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    args_parser(ap)
    principal(ap.parse_args())
