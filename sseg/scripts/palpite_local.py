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

Só biblioteca padrão; Poppler (pdftotext, pdftoppm) e, para o palpite, o Ollama em http://localhost:11434.
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
    for l in linhas:
        s = l.strip()
        if not s:
            continue
        ind = len(l) - len(l.lstrip())
        if s.startswith("- "):
            atual = [secao, sub, s[2:].strip()]
            out.append(atual)
        elif ITEM_NUM.match(l) and ind > 4:
            atual = None  # "1. Outros": rótulo do SOL
        elif ind >= 12 and atual is not None:
            atual[2] += " " + s  # continuação do texto
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


def plantas(pasta):
    """Pranchas do processo para a reanálise: [{lado, id, arquivo, nome, tipo, descricao, nao_reenviada, tem}].
    lado "depois" = ATIVA (a que o analista vai analisar); "antes" = a que a última CIA analisou e o RT trocou.
    O id do arquivo no SOL cresce com o tempo: prancha ativa com id menor que o do PDF da última CIA não foi reenviada."""
    ids = _ids_cia(pasta)
    ultima = ids[-1] if ids else 0
    penultima = ids[-2] if len(ids) > 1 else 0
    out = []
    for e in _api(pasta).get("elemGraficos") or []:
        a = e.get("arquivo") or {}
        ident = a.get("id")
        if not ident:
            continue
        ativo = e.get("situacao") == "ATIVO"
        if not (ativo or penultima < ident < ultima):
            continue
        lado = "depois" if ativo else "antes"
        nome = re.sub(r"[^\w.-]+", "_", a.get("nomeArquivo") or "planta.pdf")
        arq = "%s-%s-%s" % (lado, ident, nome if nome.lower().endswith(".pdf") else nome + ".pdf")
        cam = os.path.join(pasta, SUB, arq)
        out.append({"lado": lado, "id": ident, "arquivo": arq, "nome": a.get("nomeArquivo") or "", "tipo": e.get("tipo") or "",
                    "descricao": " ".join(str(e.get("descricao") or "").split()),
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


def baixar_plantas(pasta, buscar):
    """Traz para <pasta>/plantas/ as pranchas que faltam. buscar(id do arquivo no SOL) devolve os bytes do PDF: quem
    chama é o SSEG.exe, pela aba do SOL em que o analista já entrou (só leitura). Devolve {baixadas, falhas}."""
    os.makedirs(os.path.join(pasta, SUB), exist_ok=True)
    baixadas, falhas = [], []
    for p in plantas(pasta):
        if p["tem"]:
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
    return hashlib.sha1(json.dumps(base, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


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
    for p in novas:
        if not p["tem"]:
            continue
        pdf = os.path.join(pasta, SUB, p["arquivo"])
        ws, tam = palavras(pdf)
        a = par_anterior(todas, p)
        for pag in sorted(ws):
            if cfg.get("termo"):
                pontos += [(p, pag, x, y) for x, y in ocorrencias(ws[pag], cfg["termo"])]
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
        recs.append(r)
    if all(r.get("nao_reenviada") for r in recs):
        return recs, fatos, "A prancha não foi reenviada: não há planta nova para a IA olhar."
    if not any(r.get("antes") for r in recs):
        fatos.append("Sem a planta anterior para a contraprova: o palpite sai, no máximo, como fraco.")
    return recs, fatos, ""


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
            elif it["tipo"] in COM_RECORTE and not (it["termo"] or it["termo_antes"]):
                pass  # exigência de planta sem ponto escrito para o recorte: fica o motivo dado na classificação
            elif it["tipo"] in COM_RECORTE:
                try:
                    it["recortes"], it["fatos"], motivo = _recortes(pasta, it, todas)
                except (RuntimeError, OSError, subprocess.SubprocessError) as e:
                    motivo = "Não deu para ler a planta (%s)." % str(e)[:160]
                if motivo:
                    it["motivo"] = motivo
                else:
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
                    it.update({k: velho[k] for k in ("estado", "rodadas", "controle", "rotulo", "feito_em") if k in velho})
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


def conclusao(tipo, rodadas, ctrl):
    """Rótulo honesto do palpite: {classe, titulo, explicacao, veredito}. veredito só vem quando há palpite a mostrar."""
    vs = [r["veredito"] for r in rodadas]
    def rot(classe, titulo, expl, v=""):
        return {"classe": classe, "titulo": titulo, "explicacao": expl, "veredito": v}
    if len(set(vs)) > 1:
        return rot("ambar", "Inconclusivo", "O palpite mudou quando o recorte mudou de tamanho (%s). Olhe a planta." % ", ".join(NOME[v] for v in vs))
    v = vs[0]
    if v == "nao_sei":
        return rot("ambar", "Inconclusivo", "A IA respondeu \"não sei\" nos três tamanhos de recorte. Olhe a planta.")
    if ctrl and ctrl["veredito"] == "cumpriu":
        return rot("ambar", "Inconclusivo", "A IA também disse \"cumpriu\" na planta anterior, que recebeu a exigência. Ela não "
                   "distingue o antes do depois aqui: o palpite \"%s\" não vale." % NOME[v])
    if not ctrl:
        return rot("ambar", "Palpite fraco: " + NOME[v], "Igual nos três tamanhos de recorte, mas sem a planta anterior para a contraprova.", v)
    if v == "cumpriu" and ctrl["veredito"] == "nao_sei":
        return rot("ambar", "Palpite fraco: Cumpriu", "Na planta anterior a IA respondeu \"não sei\": o contraste com o antes não foi confirmado.", v)
    if tipo != "texto":
        return rot("ambar", "Palpite fraco: " + NOME[v], "Igual nos três tamanhos de recorte, mas é um tipo de exigência em que a IA errou muito nos testes.", v)
    return rot("verde" if v == "cumpriu" else "vermelho", "Palpite: " + NOME[v],
               "Igual nos três tamanhos de recorte" + (" e a IA disse \"não cumpriu\" na planta anterior." if ctrl["veredito"] == "nao_cumpriu" else "."), v)


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
                perg = pergunta(it)
                for m in MARGENS:
                    os.utime(marca)
                    res["rodadas"].append(dict(_rodada(pasta, it, novos, m, perg), margem=m))
                if antes:
                    os.utime(marca)
                    res["controle"] = _rodada(pasta, it, antes, MARGENS[0], perg)
                res["rotulo"] = conclusao(it["tipo"], res["rodadas"], res["controle"])
            except Exception as e:  # noqa: BLE001 — um item com problema não derruba os outros; nunca vira "não sei"
                res = {"estado": "falhou", "erro": "%s: %s" % (type(e).__name__, str(e)[:300]), "feito_em": res["feito_em"]}
            def gravar(x, n=n, ass=ass, res=res):
                alvo = _item(x, n)
                if alvo and alvo.get("assinatura") == ass:  # a conversa pode ter preparado de novo no meio da rodada
                    for k in ("rodadas", "controle", "rotulo", "erro"):
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


def responder(pasta, respostas):
    """Conferência do analista: {n: {resposta, nota}}; resposta em cumpriu | nao_cumpriu | parcial | nao_da."""
    def gravar(d):
        for n, r in (respostas or {}).items():
            it = _item(d, int(n))
            if it is not None and (r or {}).get("resposta") in ("cumpriu", "nao_cumpriu", "parcial", "nao_da"):
                it["conferencia"] = {"resposta": r["resposta"], "nota": (r.get("nota") or "").strip()[:1000],
                                     "em": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                     "palpite": (it.get("rotulo") or {}).get("titulo") or "sem palpite"}
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
        if it.get("conferencia"):
            c = it["conferencia"]
            L.append("     analista: %s%s" % (c["resposta"], " — " + c["nota"] if c.get("nota") else ""))
    return "\n".join(L)


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


if __name__ == "__main__":
    import argparse
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    args_parser(ap)
    principal(ap.parse_args())
