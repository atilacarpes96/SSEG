#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
camadas.py — confere as camadas (layers) das pranchas do PPCI, sem modelo de IA: lê do próprio PDF o nome de cada
camada, a cor dos traços e o texto que está dentro dela, e cruza com as medidas do campo 4.

Devolve FATOS para o analista, nunca exigência: "a camada da saída não tem área nem população", "não há camada de
extintores", "o texto dos extintores está na camada 0". Quem decide se vira notificação é o analista.

O QUE CONFERE (RT de Implantação do SOL-CBMRS, conferido no PDF oficial em 16/11/2026)
  6.3.6.1.2.4  cada medida e suas distâncias máximas a percorrer em camadas diferentes, habilitáveis
               Nota 01: distância máxima só para extintores, alarme, hidrantes e mangotinhos e saída de emergência
               Nota 02: na camada da saída, largura de acessos, escadas, rampas e descargas, e ocupação, área e
               população de cada compartimento
  6.3.6.1.2.3  medidas na cor vermelha
  6.3.6.1.2.6.1 itens fora da coluna "A" da Tabela L.1 (RT 05 P1.1) na planta são objeto de CIA — medida de
               laudo de inviabilidade deferido continua sendo representada (regra de trabalho de 02/09/2026)
  RT 05 Parte 08, Anexo A (coluna Observação, conferido no PDF em 16/11/2026): "Junto ao símbolo, deverá ser
               informado o número de ordem" — extintores, hidrantes e mangotinhos, acionador de alarme. Só nas
               plantas baixas: número repetido, buraco na sequência, camada sem número, número fora da camada

USO
  python sseg/scripts/sseg.py camadas --pasta "<pasta do processo>"          relatório
  python sseg/scripts/sseg.py camadas --pasta "<pasta>" --json               o mesmo em JSON
  python sseg/scripts/camadas.py --pdf <prancha.pdf>                          só o inventário de uma prancha

As pranchas são as de <pasta>/plantas/ (as mesmas que o quadro azul baixa do SOL). Ler o PDF pede o PyMuPDF 1.28
(pip install pymupdf==1.28.2; o instalador do SSEG já instala); conferir o inventário já lido não pede. Cache ao lado do PDF: <prancha>.camadas.json.
"""

import glob
import json
import os
import re
import sys
import unicodedata
from collections import Counter

VERSAO_CACHE = 2  # 2: pedaços de texto lado a lado na mesma linha viram um texto só


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t or ""))
    return "".join(c for c in t if not unicodedata.combining(c)).upper()


# ------------------------------------------------------------------ medidas

# chave → (nome curto, planta?) · planta = analisada em planta pela coluna "A" da L.1 (sinalização de orientação e
# iluminação de balizamento entram pela alínea "i" da linha Saídas de Emergência)
MEDIDAS = {
    "extintores": ("Extintores", True),
    "alarme": ("Alarme", True),
    "hidrantes": ("Hidrantes e mangotinhos", True),
    "saida": ("Saída de emergência", True),
    "sinalizacao": ("Sinalização (orientação e salvamento)", True),
    "iluminacao": ("Iluminação (balizamento)", True),
    "viaturas": ("Acesso de viaturas", True),
    "isolamento": ("Isolamento de riscos", True),
    "hidrante_urbano": ("Hidrante urbano", True),
    "deteccao": ("Detecção", False),
    "chuveiros": ("Chuveiros automáticos", False),
    "compartimentacao": ("Compartimentação", False),
    "fumaca": ("Controle de fumaça", False),
    "brigada": ("Brigada", False),
    "spda": ("SPDA", False),
    "estrutural": ("Segurança estrutural", False),
    "materiais": ("Controle de materiais", False),
    "plano": ("Plano de emergência", False),
}
COM_DISTANCIA = ("extintores", "alarme", "hidrantes", "saida")  # Nota 01

# nome da medida no campo 4 do SOL → chave
_CAMPO4 = [
    (r"EXTINTOR", "extintores"), (r"ALARME", "alarme"), (r"HIDRANTE URBANO", "hidrante_urbano"),
    (r"HIDRANTE|MANGOTINHO", "hidrantes"), (r"SAIDA", "saida"), (r"SINALIZA", "sinalizacao"),
    (r"ILUMINA", "iluminacao"), (r"VIATURA", "viaturas"), (r"ISOLAMENTO", "isolamento"),
    (r"DETEC", "deteccao"), (r"CHUVEIRO", "chuveiros"), (r"COMPARTIMENTA", "compartimentacao"),
    (r"FUMACA", "fumaca"), (r"BRIGADA", "brigada"), (r"DESCARGA.*ATMOSF|SPDA", "spda"),
    (r"ESTRUTURAL", "estrutural"), (r"MATERIAIS", "materiais"), (r"PLANO DE EMERG", "plano"),
]

# nome da camada → chave (a ordem importa: "HIDRANTE URBANO" antes de "HIDRANTE")
_CAMADA = [
    (r"HIDRANTE\W*URBANO|HID\W*URB", "hidrante_urbano"),
    (r"EXTINT|(?<![A-Z])EXT(?![A-Z])|(?<![A-Z])EXT\d", "extintores"),
    (r"ALARM|(?<![A-Z])ALR(?![A-Z])|(?<![A-Z])ALM(?![A-Z])|ACIONAD", "alarme"),
    (r"HIDRANT|MANGOT|(?<![A-Z])HDR(?![A-Z])|(?<![A-Z])HID(?![A-Z])|(?<![A-Z])RTI(?![A-Z])|RECALQUE", "hidrantes"),
    (r"SAIDA|ROTA|FUGA|ESCAPE|PANICO|(?<![A-Z])S\W?E(?![A-Z])", "saida"),
    (r"SINALIZ|(?<![A-Z])SINAL|(?<![A-Z])SOS(?![A-Z])", "sinalizacao"),
    (r"ILUMIN|BALIZ|(?<![A-Z])ILU(?![A-Z])", "iluminacao"),
    (r"VIATUR", "viaturas"),
    (r"(?<![A-Z])ISOL|AFASTAM|CORTA\W*FOGO", "isolamento"),
    (r"DETEC|DETET", "deteccao"),
    (r"SPRINK|CHUVEIR|(?<![A-Z])SPK(?![A-Z])", "chuveiros"),
    (r"COMPARTIM", "compartimentacao"),
    (r"FUMACA", "fumaca"),
    (r"BRIGAD", "brigada"),
    (r"SPDA|PARA\W*RAIO", "spda"),
]
_DIST_NOME = r"(?<![A-Z])DMP(?![A-Z])|DIST|PERCORR|CAMINHAM"
_BASE = (r"ARQ|FOLHA|CARIMBO|SELO|LAYOUT|MOBIL|PAREDE|PORTA|JANELA|HACH|EIXO|VIEWPORT|DEFPOINTS|COTA|TEXTO|"
         r"^0$|^\d+$|COBERT|TELHA|PISO|ESTRUT|PILAR|VIGA|ESQUADR|LOUCA|VEGETA|TERRENO|LOTE|PASSEIO|CALCADA")


LEGENDA = r"FOLHA|CARIMBO|SELO|LEGENDA|QUADRO"


def medida_do_campo4(nome):
    n = sem_acento(nome)
    return next((k for p, k in _CAMPO4 if re.search(p, n)), None)


def medida_da_camada(nome):
    """(chave da medida ou "base" ou "outra", é camada de distância?)"""
    n = sem_acento(nome).strip()
    dist = bool(re.search(_DIST_NOME, n))
    k = next((k for p, k in _CAMADA if re.search(p, n)), None)
    if k:
        return k, dist
    if dist:
        return "distancia", True
    return ("base" if re.search(_BASE, n) else "outra"), False


# ------------------------------------------------------------------ o que o texto de uma camada mostra

SINAIS = {
    "dmp": r"(?<![A-Z])DMP(?![A-Z])|DIST(ANCIA)?\.?\s*MAX|MAX(IMA)?\.?\s*DIST|A\s+PERCORRER",
    # metro com vírgula ("1,20 m"). Porta em centímetro ("90x210") não conta: a Nota 02 pede a largura dos acessos,
    # escadas, rampas e descargas, e a CIA da 42491 cobrou essa cota de prancha que só tinha as portas
    "largura": r"(?<![\d,.])[0-9],\d{2}(?![\d,])\s*(M(?![A-Z²2])|$|\s)",
    "pessoas": r"PESSOA|(?<![A-Z])PESS(?![A-Z])|(?<![A-Z])POP(?![A-Z])|POPULA",  # "03 PESS." (35938)
    # número seguido de m² (o NFKD faz do ² um 2) ou "ÁREA:" / "A.:" com número; "OCUPAÇÃO M2" (45128) é ocupação
    # (o rótulo inteiro numa alternativa só: "A=278,30M2" conta uma vez, não duas; 50876)
    "area": r"(?<![A-Z0-9-])A(REA)?\.?\s*[:=]\s*\d[\d.,]*\s*(M\s?\^?2(?![0-9]))?|\d\s*M\s?\^?2(?![0-9])",
    # "F-8", "(D1)", "OCUPAÇÃO D1" (45128), "J3 — Depósito" (49907)
    "ocupacao": r"(?<![A-Z0-9])[A-M]-\d{1,2}(?![0-9])|\([A-M]-?\d{1,2}\)|OCUPA\w*\s*:?\s*[A-M]-?\d{1,2}(?![0-9])"
                r"|(?<![A-Z0-9])[A-M]\d{1,2}\s*[—–-]\s*[A-Z]",
    "extintor": r"(?<![A-Z])PQS|(?<![A-Z])CO2(?![0-9])|(?<![A-Z])AP(?![A-Z])\s*\d|\d+-?A\s*:\s*\d+-?B|EXTINT",
    "alarme": r"(?<![A-Z])ALM(?![A-Z])|ALARM|ACIONAD",
    "hidrante": r"HIDRANT|MANGUEIR|(?<![A-Z])RTI(?![A-Z])|RECALQUE|MANGOT",
    "placa": r"(?<![A-Z0-9])S\d{1,2}(?![0-9])",
}
SINAL_DA_MEDIDA = {"extintores": "extintor", "alarme": "alarme", "hidrantes": "hidrante", "sinalizacao": "placa"}


def sinais(texto):
    t = sem_acento(texto)
    return {k: len(re.findall(p, t)) for k, p in SINAIS.items()}


# ------------------------------------------------------------------ leitura do PDF (PyMuPDF)

def _vermelho(cor):
    if not cor or len(cor) != 3:
        return False
    r, g, b = cor
    return r >= 0.75 and g <= 0.35 and b <= 0.35


def ler_pdf(pdf):
    """Inventário de uma prancha: {"camadas": [nomes], "pag": n, "por_camada": {nome: {tracos, vermelho, texto}}}.
    A camada "" é o que está fora de qualquer camada. Cache em <pdf>.camadas.json."""
    cache = pdf + ".camadas.json"
    try:
        if os.path.getmtime(cache) >= os.path.getmtime(pdf):
            with open(cache, encoding="utf-8") as fh:
                d = json.load(fh)
            if d.get("v") == VERSAO_CACHE:
                return d
    except (OSError, ValueError):
        pass
    fitz = tem_pymupdf()
    doc = fitz.open(pdf)
    nomes = sorted({v.get("name") or "" for v in (doc.get_ocgs() or {}).values()})
    por = {}

    def cam(n):
        return por.setdefault(n or "", {"tracos": 0, "vermelho": 0, "texto": []})
    for pag in doc:
        try:
            desenhos = pag.get_cdrawings()
        except AttributeError:
            desenhos = pag.get_drawings()
        for x in desenhos:
            c = cam(x.get("layer"))
            c["tracos"] += 1
            if _vermelho(x.get("color") or x.get("fill")):
                c["vermelho"] += 1
        ultimo = {}    # camada -> (origem do último caractere, direção, tamanho) do último texto dela
        for t in pag.get_texttrace():
            chars = [ch for ch in t.get("chars") or () if ch[0] >= 32]
            s = "".join(chr(ch[0]) for ch in chars).strip()
            if not s:
                continue
            textos = cam(t.get("layer"))["texto"]
            ini, fim = chars[0][2], chars[-1][2]
            dx, dy = t.get("dir") or (1, 0)
            tam = t.get("size") or 1
            u = ultimo.get(t.get("layer"))
            # o PDF guarda "Nº 1" e "0" em pedaços separados (46239): junta o que continua a mesma linha
            if u and textos:
                ox, oy = ini[0] - u[0][0], ini[1] - u[0][1]
                ao_longo, de_lado = ox * dx + oy * dy, abs(-ox * dy + oy * dx)
                if abs(u[1][0] - dx) + abs(u[1][1] - dy) < 0.05 and 0 < ao_longo < 1.6 * tam and de_lado < 0.3 * tam:
                    textos[-1] += (" " if ao_longo > 0.9 * tam else "") + s
                    ultimo[t.get("layer")] = (fim, (dx, dy), tam)
                    continue
            textos.append(s)
            ultimo[t.get("layer")] = (fim, (dx, dy), tam)
    d = {"v": VERSAO_CACHE, "camadas": nomes, "pag": len(doc),
         "por_camada": {k: {"tracos": v["tracos"], "vermelho": v["vermelho"], "texto": " · ".join(v["texto"])[:20000]}
                        for k, v in por.items()}}
    try:
        with open(cache, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False)
    except OSError:
        pass
    return d


# ------------------------------------------------------------------ pasta do processo

def _api(pasta):
    arqs = sorted(glob.glob(os.path.join(pasta, "api-*.json")), key=os.path.getmtime)
    try:
        with open(arqs[-1], encoding="utf-8") as fh:
            return json.load(fh)
    except (IndexError, OSError, ValueError):
        return {}


def medidas_campo4(api):
    """[{chave, nome, laudo}] das medidas do campo 4; laudo = medida com inviabilidade técnica."""
    out = []
    for m in ((api.get("especSeguranca") or {}).get("medidas") or []):
        nome = ((m.get("tipo") or {}).get("nome")) or ""
        out.append({"chave": medida_do_campo4(nome), "nome": nome,
                    "laudo": (m.get("inviabilidade") or "NAO_POSSUI") != "NAO_POSSUI"})
    return out


def pranchas_ativas(pasta, api):
    """[(rótulo, caminho)] das pranchas ATIVAS já baixadas em <pasta>/plantas/: "<nome do SOL> (<id>).pdf" e, nas
    baixadas antes de 16/11/2026, "depois-<id>-*.pdf"."""
    out = []
    for e in api.get("elemGraficos") or []:
        if e.get("situacao") != "ATIVO":
            continue
        ident = (e.get("arquivo") or {}).get("id")
        achou = [x for pad in ("* (%s).pdf", "depois-%s-*.pdf")
                 for x in glob.glob(os.path.join(glob.escape(os.path.join(pasta, "plantas")), pad % ident))] if ident else []
        rot = " ".join(str(e.get("descricao") or e.get("tipo") or "").split()) or str(ident)
        out.append((rot, achou[0] if achou else None, e.get("tipo") or ""))
    return out


# ------------------------------------------------------------------ número de ordem (RT 05 Parte 08, Anexo A)

# "Junto ao símbolo, deverá ser informado o número de ordem" (coluna Observação do Anexo A: extintor, hidrante e
# mangotinho, acionador de alarme). Um texto da camada é número de ordem quando é só o número, com prefixo curto
# conhecido e, no pavimento tipo, o pavimento: "02", "A-03", "ALM- 1", "EXT- 85", "09 - 2° PAV.".
ORDEM = ("extintores", "hidrantes", "alarme")
_PREFIXOS = (r"E|EX|EXT|A|AL|ALM|ALR|AC|ACM|H|HD|HDR|HID|M|MG|N|NO|NR|NUM"
             r"|EXTINTOR|HIDRANTE|MANGOTINHO|ACIONADOR|ALARME|H/M")  # "HIDRANTE 02" (1906), "H/M1" (18168)
# agente do extintor colado ao número: "E01-PQS", "EXT 02 CO2" (49678, 17/11/2026: a camada tinha a numeração e o
# script dizia que não)
_AGENTE = r"(?:\s*-\s*|\s+)(?:PQS|PQ|CO2|AP|AGUA|ABC|BC|AB|ESPUMA|EM|H2O|CLASSE)\b.*"
_NUMERO = re.compile(r"^(?:(?:%s)\s*[-.:]?\s*)?0*(\d{1,3})(?:\s*-\s*\d{1,2}\s*\S{0,2}\s*PAV.*|\s+-\s+\D.*)?$"
                     % _PREFIXOS)
_NUMERO_AGENTE = re.compile(r"^(?:%s)\s*[-.:]?\s*0*(\d{1,3})%s$" % (_PREFIXOS, _AGENTE))  # com prefixo, sempre
# ("H 10 - TIPO 3", 1509: número, traço e a descrição do equipamento)
# lista do pavimento tipo, um número por andar: "N48,50,52,54" (49433)
_LISTA = re.compile(r"^(?:%s)\s*[-.:]?\s*(\d{1,3}(?:\s*,\s*\d{1,3}){2,})$" % _PREFIXOS)  # com prefixo: "2,50" é cota


# fora da camada da medida só vale número com o prefixo dela ("EXT- 1" fora de camada, 49826)
# ("E-1", "H-3" são ocupação e "E5" é placa de sinalização: prefixo de uma letra só não vale fora da camada)
_PREFIXO_DA_MEDIDA = {"extintores": r"EX|EXT", "hidrantes": r"HD|HDR|HID|MG|H/M", "alarme": r"AL|ALM|ALR|AC|ACM"}
# "SHSC T3 Nº 02" (49961) e "N° 75, 76" (bateria, 1764); não "n° 14/2016" (número de RT) nem "EXTINTOR Nº 01= 18,50 M"
# (distância a percorrer citando o extintor, 50906)
_NO = re.compile(r"(?<![A-Z])N[O°]\s*\.?\s*(\d{1,3}(?:\s*[,E]\s*\d{1,3})*)(?![\d.,/=]|\s*=)")


def numeros(texto, medida=None):
    """Números de ordem no texto de uma camada (textos separados por " · "). Com medida: só os de prefixo dela."""
    rx = _NUMERO if not medida else re.compile(
        r"^(?:%s)\s*[-.:]?\s*0*(\d{1,3})(?:\s*-\s*\d{1,2}\s*\S{0,2}\s*PAV.*%s)?$"
        % (_PREFIXO_DA_MEDIDA[medida], "|" + _AGENTE if medida == "extintores" else ""))
    out = []
    for t in (texto or "").split(" · "):
        u = sem_acento(t).strip()
        m = rx.match(u) or (not medida and _NUMERO_AGENTE.match(u))
        if m:
            if int(m.group(1)) > 0:
                out.append(int(m.group(1)))
        elif not medida and _LISTA.match(u):
            out.extend(n for n in map(int, re.findall(r"\d+", _LISTA.match(u).group(1))) if n > 0)
        elif not medida:
            for m in _NO.finditer(u):
                out.extend(n for n in map(int, re.findall(r"\d+", m.group(1))) if n > 0)
    return out


def _faixas(ns):
    """[1, 2, 3, 7] -> "01–03, 07"."""
    out, ini = [], None
    for i, n in enumerate(ns):
        if ini is None:
            ini = n
        if i + 1 == len(ns) or ns[i + 1] != n + 1:
            out.append("%02d" % ini if ini == n else "%02d–%02d" % (ini, n))
            ini = None
    return ", ".join(out)


def numeros_de_ordem(no_campo4, pranchas, repetidas, fato):
    vistas = set()
    nums = {}          # medida -> [(número, rótulo da prancha)]
    sem = {}           # medida -> [pranchas (planta baixa) com a camada desenhada e nenhum número]
    longe = {}         # medida -> {(prancha, camada): quantos} números com o prefixo dela em outra camada
    for rot, inv, tipo in pranchas:
        if tipo not in ("PLANTA_BAIXA", ""):
            continue  # a implantação e o corte repetem o equipamento da planta baixa (49826: extintor 38)
        por = inv.get("por_camada") or {}
        chave = json.dumps(por, sort_keys=True, ensure_ascii=False)
        if chave in vistas:
            continue
        vistas.add(chave)
        desenhada, proprios, outros = set(), {}, {}
        for nome, c in por.items():
            if nome in repetidas or re.search(LEGENDA, sem_acento(nome)):
                continue
            k, dist = medida_da_camada(nome) if nome else ("base", False)
            if k in ORDEM and not dist:
                if c.get("tracos"):
                    desenhada.add(k)
                proprios.setdefault(k, []).extend((n, nome) for n in numeros(c.get("texto")))
            else:
                for med in ORDEM:
                    ns = numeros(c.get("texto"), med)
                    if ns:
                        outros.setdefault(med, {})[nome or "fora de camada"] = ns
        for k in ORDEM:
            if proprios.get(k):
                nums.setdefault(k, []).extend((n, rot, nome) for n, nome in proprios[k])
            elif k in desenhada:
                if outros.get(k):
                    for camada, ns in outros[k].items():
                        longe.setdefault(k, {})[(rot, camada)] = len(ns)
                        nums.setdefault(k, []).extend((n, rot, camada) for n in ns)
                else:
                    txt = [(por.get(n) or {}).get("texto") for n in por if medida_da_camada(n)[0] == k]
                    sem.setdefault(k, []).append((rot, next((t for t in txt if t), "")))
    for k in ORDEM:
        if k not in no_campo4:
            continue
        nome = MEDIDAS[k][0]
        if longe.get(k):
            fato("RT 05 P08 Anexo A", "ordem_fora_da_camada", "%s: o número de ordem não está na camada da medida; "
                 "achei em %s." % (nome, "; ".join("%s · \"%s\" (%d)" % (r, c, q) for (r, c), q in longe[k].items())))
        # 51398 (20/11/2026): "RECALQUE" e "Distância máxima... até o hidrante" eram o único texto da camada; o
        # "HIDRANTE N°01" estava desenhado em traço (fonte do CAD), e o analista viu o número na planta. A frase mostra
        # o texto que a camada tem e lembra o desenho, para não soar como número faltando
        for com_texto, item in ((True, "ordem_sem_numero"), (False, "ordem_sem_texto")):
            lst = [(r, t) for r, t in sem.get(k, ()) if bool(t) == com_texto]
            if not lst:
                continue
            onde = ", ".join(r for r, _t in lst) if len(lst) <= 4 else "%d plantas baixas" % len(lst)
            if com_texto:
                amostra = "; ".join(sorted({'"%s"' % t.split(" · ")[0][:40] for _r, t in lst})[:3])
                frase = ("o texto da camada não é número de ordem (só %s) em %s; o número pode estar em desenho "
                         "(texto do CAD virado traço)" % (amostra, onde))
            else:
                frase = "a camada não tem texto nenhum em %s (o número pode ter virado desenho)" % onde
            fato("RT 05 P08 Anexo A", item, "%s: %s; conferir na planta." % (nome, frase))
        if not nums.get(k):
            continue
        onde_n, por_camada_n = {}, Counter()
        for n, rot, camada in nums[k]:
            onde_n.setdefault(n, []).append(rot)
            por_camada_n[(n, rot, camada)] += 1
        # repetido: na mesma camada ou em pranchas diferentes. Em duas camadas da mesma prancha (28689: "EXTINTOR" e
        # "INVIABILIDADE_EXTINTOR", cada uma de 01 em diante) já sai como "várias camadas"
        dup = sorted(n for n, rots in onde_n.items()
                     if len(set(rots)) > 1 or any(q >= 2 for (m, _r, _c), q in por_camada_n.items() if m == n))
        if dup:
            fato("RT 05 P08 Anexo A", "ordem_repetido", "%s: número de ordem repetido: %s." % (nome, "; ".join(
                "%02d (%s)" % (n, ", ".join(sorted(set(onde_n[n])))) if len(set(onde_n[n])) > 1
                else "%02d (%d vezes em %s)" % (n, len(onde_n[n]), onde_n[n][0]) for n in dup[:6])
                + ("; e mais %d" % (len(dup) - 6) if len(dup) > 6 else "")))
        maior = max(onde_n)
        falta = [i for i in range(1, maior + 1) if i not in onde_n]
        if falta and maior <= 400 and len(falta) <= maior / 2:
            sem_n = [r for r, _t in sem.get(k, ())]
            fato("RT 05 P08 Anexo A", "ordem_buraco", "%s: a numeração lida vai até %02d e não aparece %s. %s" % (
                nome, maior, _faixas(falta),
                ("Os que faltam devem ser os de %s, onde não há número em texto: provavelmente desenhado; conferir lá."
                 % ", ".join(sem_n)) if sem_n and len(sem_n) <= 4 else
                "O equipamento pode estar sem número, ou o número pode estar em desenho; conferir na planta."))


# ------------------------------------------------------------------ conferência (sem PDF: recebe os inventários)

def conferir(medidas, pranchas):
    """medidas: saída de medidas_campo4. pranchas: [(rótulo, inventário de ler_pdf, tipo)].
    Devolve {"fatos": [{grupo, item, texto}], "camadas": {rótulo: [(nome, chave, dist)]}}."""
    fatos = []

    def fato(grupo, item, texto):
        if not any(f["texto"] == texto for f in fatos):  # pranchas com o mesmo nome repetiriam o fato
            fatos.append({"grupo": grupo, "item": item, "texto": texto})

    no_campo4 = {m["chave"] for m in medidas if m["chave"]}
    com_laudo = {m["chave"] for m in medidas if m["chave"] and m["laudo"]}
    onde = {}          # chave → [rótulos das pranchas com camada dela]
    texto_med = {}     # chave → texto somado das camadas dela
    mapa = {}
    sem_camadas = []
    varias = {}        # (medida, camadas) → pranchas em que ela está assim espalhada
    # camada idêntica (mesmos traços e mesmo texto) em 3 ou mais pranchas, até no corte: é legenda ou bloco
    # repetido, não a medida desenhada em cada pavimento (51398: "EXTINTORES" ao lado de "6 EXTINTORES")
    assinaturas = {}
    vistas = set()     # a mesma prancha enviada mais de uma vez (15410) não faz a camada parecer legenda
    for _rot, inv, _tipo in pranchas:
        chave = json.dumps(inv.get("por_camada") or {}, sort_keys=True, ensure_ascii=False)
        if chave in vistas:
            continue
        vistas.add(chave)
        for nome, c in (inv.get("por_camada") or {}).items():
            if c.get("tracos") or c.get("texto"):
                assinaturas.setdefault(nome, []).append((c.get("tracos", 0), c.get("texto") or ""))
    repetidas = {n for n, sig in assinaturas.items() if n and max(sig.count(x) for x in sig) >= 3}
    for rot, inv, _tipo in pranchas:
        nomes = inv.get("camadas") or []
        por = inv.get("por_camada") or {}
        mapa[rot] = []
        if not nomes:
            if _tipo in ("PLANTA_BAIXA", ""):  # justificativa ou termo enviado como elemento gráfico não conta
                sem_camadas.append(rot)
            continue
        # a mesma medida espalhada em mais de uma camada nesta prancha (camada de distância à parte é permitida)
        por_med = {}
        for nome in nomes:
            k, dist = medida_da_camada(nome)
            c = por.get(nome) or {}
            if k in MEDIDAS and not dist and (c.get("tracos") or c.get("texto")) and nome not in repetidas:
                por_med.setdefault(k, []).append(nome)
        for k, ns in sorted(por_med.items()):
            if len(ns) >= 2:
                varias.setdefault((k, tuple(ns)), []).append(rot)
        for nome in nomes:
            k, dist = medida_da_camada(nome)
            mapa[rot].append((nome, k, dist))
            c = por.get(nome) or {}
            if not (c.get("tracos") or c.get("texto")):
                continue  # camada vazia nesta prancha
            if k in MEDIDAS:
                onde.setdefault(k, []).append(rot)
                texto_med[k] = texto_med.get(k, "") + " · " + (c.get("texto") or "")
                # 6.3.6.1.2.3: cor vermelha
                if (c.get("tracos", 0) >= 20 and c.get("vermelho", 0) < 0.5 * c["tracos"]
                        and not re.search(LEGENDA, sem_acento(nome)) and nome not in repetidas):
                    fato("6.3.6.1.2.3", "cor", "%s · camada \"%s\": %d de %d traços em vermelho." % (
                        rot, nome, c.get("vermelho", 0), c["tracos"]))
                # Nota 01: distância em camada de medida que não leva distância
                if k not in COM_DISTANCIA and sinais(c.get("texto"))["dmp"]:
                    fato("6.3.6.1.2.4 Nota 01", "distancia_fora",
                         "%s · camada \"%s\" (%s) tem texto de distância a percorrer; a Nota 01 limita a distância a "
                         "extintores, alarme, hidrantes e saída." % (rot, nome, MEDIDAS[k][0]))
                # mistura: texto típico de outra medida dentro desta camada
                s = sinais(c.get("texto"))
                for outra, sinal in SINAL_DA_MEDIDA.items():
                    if outra != k and s[sinal] >= 3 and not (k == "saida" and outra == "sinalizacao"):
                        fato("6.3.6.1.2.4", "mistura", "%s · camada \"%s\" (%s) tem %d textos de %s." % (
                            rot, nome, MEDIDAS[k][0], s[sinal], MEDIDAS[outra][0].lower()))
        # texto de medida fora de qualquer camada ou em camada de arquitetura, quando a medida não tem camada própria
        # nesta prancha (com camada própria, o que sobra fora é legenda ou quadro-resumo)
        proprias = {medida_da_camada(n)[0] for n in nomes if (por.get(n) or {}).get("tracos") or (por.get(n) or {}).get("texto")}
        for nome, c in por.items():
            k = medida_da_camada(nome)[0] if nome else "base"
            if k not in ("base", "outra") or re.search(LEGENDA, sem_acento(nome)):
                continue  # legenda e carimbo listam todas as medidas
            s = sinais(c.get("texto"))
            for med, sinal in SINAL_DA_MEDIDA.items():
                if s[sinal] >= 5 and med not in proprias:
                    fato("6.3.6.1.2.4", "fora_da_camada", "%s · %d textos de %s %s, e a medida não tem camada própria "
                         "nesta prancha (pode ser legenda)." % (
                             rot, s[sinal], MEDIDAS[med][0].lower(),
                             "fora de qualquer camada" if not nome else "na camada \"%s\"" % nome))

    for (k, ns), rots in varias.items():
        fato("6.3.6.1.2.4", "varias_camadas", "%s em %d camadas (%s): %s." % (
            MEDIDAS[k][0], len(ns), ", ".join(rots) if len(rots) <= 3 else "%d pranchas" % len(rots),
            "; ".join("\"%s\"" % n for n in ns)))
    for rot in sem_camadas:
        fato("6.3.6.1.2.4", "sem_camadas", "%s · o PDF não tem camadas: nenhuma medida pode ser habilitada ou "
             "desabilitada." % rot)

    if not medidas:
        fato("campo 4", "sem_campo4", "O campo 4 (medidas) não veio no JSON do SOL: a comparação camada × medida não foi feita.")
    # medida do campo 4 analisada em planta (ou com laudo) sem camada própria
    for m in medidas:
        k = m["chave"]
        if not k or not (MEDIDAS[k][1] or m["laudo"]):
            continue
        if k == "iluminacao" and not any("BALIZ" in sem_acento(c.get("texto")) for _r, inv, _t in pranchas
                                         for c in (inv.get("por_camada") or {}).values()):
            continue  # sem balizamento na planta, a iluminação não se representa
        if k not in onde and any(inv.get("camadas") for _r, inv, _t in pranchas):
            extra = {"iluminacao": " A planta fala em balizamento (alínea \"i\" da L.1).",
                     "isolamento": " Conferir se o isolamento é usado: as cotas de afastamento e o TRRF podem estar em outra camada.",
                     "viaturas": " Confere-se na implantação."}.get(k, "")
            if m["laudo"] and not MEDIDAS[k][1]:
                extra = " Medida de laudo de inviabilidade: tem de estar representada."
            sinal = SINAL_DA_MEDIDA.get(k)
            if sinal:
                achou = Counter()
                for _rot, inv, _t in pranchas:
                    for nome, c in (inv.get("por_camada") or {}).items():
                        n = sinais(c.get("texto"))[sinal]
                        if n >= 3 and not re.search(LEGENDA, sem_acento(nome)):
                            achou[nome or "fora de camada"] += n
                if achou:
                    extra += " O texto dela está em: %s." % "; ".join("\"%s\" (%d)" % x for x in achou.most_common(3))
            fato("6.3.6.1.2.4", "sem_camada", "%s (campo 4): nenhuma camada com o nome dela nas pranchas.%s" % (
                MEDIDAS[k][0], extra))

    # camada de medida que não está no campo 4, ou de medida só de memorial sem laudo
    for k, rots in sorted(onde.items()):
        if not medidas:
            break
        if k not in no_campo4:
            fato("campo 4", "camada_sem_medida", "Camada de %s (%s) e a medida não está marcada no campo 4." % (
                MEDIDAS[k][0], ", ".join(sorted(set(rots)))))
        elif not MEDIDAS[k][1] and k not in com_laudo:
            fato("6.3.6.1.2.6.1", "fora_coluna_A", "Camada de %s (%s): medida que só se confere no memorial (Tabela "
                 "L.2), sem laudo de inviabilidade." % (MEDIDAS[k][0], ", ".join(sorted(set(rots)))))

    # texto convertido em desenho: sem texto legível nas plantas baixas, as conferências pelo texto não valem
    letras = sum(len(c.get("texto") or "") for _r, inv, t in pranchas if t in ("PLANTA_BAIXA", "")
                 for c in (inv.get("por_camada") or {}).values())
    if letras < 1500 and any(t in ("PLANTA_BAIXA", "") for _r, _i, t in pranchas):  # nenhuma planta lida: não há o que medir
        fato("texto", "ilegivel", "As plantas baixas têm só %d letras de texto legível no PDF (o texto deve ter sido "
             "convertido em desenho): distância (Nota 01) e ocupação, área e população (Nota 02) não foram conferidas "
             "pelo texto; conferir na planta." % letras)
        return {"fatos": fatos, "camadas": mapa}

    numeros_de_ordem(no_campo4, pranchas, repetidas, fato)

    # Nota 01: medida que leva distância e não tem texto de distância na própria camada nem camada de distância dela
    dist_camadas = {(k if k in MEDIDAS else None) for rot in mapa for _n, k, d in mapa[rot] if d}
    sem_d = [MEDIDAS[k][0] for k in COM_DISTANCIA
             if k in onde and not sinais(texto_med.get(k, ""))["dmp"] and k not in dist_camadas]
    if sem_d:
        fato("6.3.6.1.2.4 Nota 01", "sem_distancia", "Sem texto de distância a percorrer (DMP) na camada de: %s. "
             "A distância pode estar só desenhada; conferir na planta." % ", ".join(sem_d))

    # Nota 02: o que a camada da saída tem de trazer
    if "saida" in onde:
        s = sinais(texto_med.get("saida", ""))
        falta = [n for n, chave in (("largura cotada", "largura"), ("ocupação", "ocupacao"), ("área", "area"),
                                    ("população", "pessoas")) if not s[chave]]
        if falta:
            achado = []
            for rot, inv, _t in pranchas:
                for nome, c in (inv.get("por_camada") or {}).items():
                    if medida_da_camada(nome)[0] == "saida":
                        continue
                    sc = sinais(c.get("texto"))
                    for n, chave in (("área", "area"), ("população", "pessoas"), ("ocupação", "ocupacao")):
                        if n in falta and sc[chave] >= 2:
                            achado.append("%s em \"%s\"" % (n, nome or "fora de camada"))
            fato("6.3.6.1.2.4 Nota 02", "nota02", "Camada da saída sem %s.%s" % (
                ", ".join(falta), (" Achei " + "; ".join(sorted(set(achado))) + ".") if achado else ""))
        else:
            # tem de tudo, mas de quantos compartimentos? Nota 02 pede cada um: compara com as áreas rotuladas fora
            areas_fora = sum(sinais(c.get("texto"))["area"] for _r, inv, t in pranchas if t == "PLANTA_BAIXA"
                             for nome, c in (inv.get("por_camada") or {}).items()
                             if medida_da_camada(nome)[0] in ("base", "outra") and not re.search(LEGENDA, sem_acento(nome)))
            if areas_fora >= 4 and s["pessoas"] < 0.5 * areas_fora:
                fato("6.3.6.1.2.4 Nota 02", "nota02_parcial", "A camada da saída traz população em %d ponto(s); as "
                     "plantas baixas rotulam %d áreas em outras camadas. Pode faltar compartimento (a Nota 02 pede "
                     "ocupação, área e população de cada um)." % (s["pessoas"], areas_fora))
    return {"fatos": fatos, "camadas": mapa}


# ------------------------------------------------------------------ texto em desenho: a IA local transcreve, o script confere

# 2.15.0 (pedido do Átila, 16/11/2026): quando o texto das plantas baixas virou desenho, as Notas 01 e 02 não se
# conferem pelo texto. A IA local (Ollama, palpite_local.MODELO) recebe a imagem SÓ da camada da saída, recortada onde
# ela desenha, e apenas transcreve o que lê; as mesmas regras de sinais() decidem o que há. A IA não julga nada.
# Prova de 20/11/2026 (784, planta baixa): leu 0,80 / 1,10 / 1,20 / 1,30, distâncias e placas; trocou 1,40 por 0,41.
IA_PROMPT = """Esta imagem é um recorte de uma planta de prevenção de incêndio, mostrando só uma camada do desenho.
Transcreva todos os textos e números que você consegue ler na imagem, um por item, exatamente como estão escritos.
Não interprete, não complete e não invente: se não der para ler um texto, deixe-o de fora."""
IA_ESQUEMA = {"type": "object", "properties": {"textos": {"type": "array", "items": {"type": "string"}}},
              "required": ["textos"]}
IA_LADO_MAX = 2000    # pixels do lado maior de cada pedaço mandado à IA (a prova de 20/11 leu bem 1085x1734)
IA_DPI = 200
IA_VERSAO = 2         # 2: recorte na folha girada (/Rotate); muda quando a imagem mandada à IA muda
IA_PEDACOS_MAX = 10   # cada pedaço leva perto de 1 minuto na RTX 4070


def _ia():
    import palpite_local as pl  # mesma pasta; só carrega quando a IA é pedida
    return pl


def _grade(largura, altura, passo):
    """Quantos pedaços em x e em y para cobrir a área com pedaços de `passo` pontos. Cabe inteiro: um só (partir
    corta texto na emenda; na prova de 20/11 a IA perdeu duas cotas assim)."""
    return max(1, int(-(-largura // passo))), max(1, int(-(-altura // passo)))


def imagens_da_camada(pdf, chave="saida", dpi=IA_DPI, lado=IA_LADO_MAX, maximo=IA_PEDACOS_MAX):
    """PNGs só com as camadas da medida, recortadas onde ela desenha e partidas em pedaços de até `lado` pixels
    (com sobreposição, para o texto da emenda sair inteiro em um deles). [] quando o PDF não tem essa camada."""
    fitz = tem_pymupdf()
    doc = fitz.open(pdf)
    cfg = doc.layer_ui_configs() or []
    if not any(medida_da_camada(c["text"])[0] == chave for c in cfg):
        return []
    for c in cfg:  # 0 liga, 2 desliga (o set_layer não muda o que o get_pixmap mostra)
        doc.set_layer_ui_config(c["number"], action=0 if medida_da_camada(c["text"])[0] == chave else 2)
    out = []
    for pag in doc:
        try:
            desenhos = pag.get_cdrawings()
        except AttributeError:
            desenhos = pag.get_drawings()
        rs = [x["rect"] for x in desenhos if medida_da_camada(x.get("layer") or "")[0] == chave]
        rs += [t["bbox"] for t in pag.get_texttrace() if medida_da_camada(t.get("layer") or "")[0] == chave]
        if not rs:
            continue
        # desenho e texto vêm na folha sem giro; o recorte é na folha como ela aparece (35938 e 30905: /Rotate 270,
        # sem isto o recorte caía no vazio)
        rs = [tuple(fitz.Rect(q) * pag.rotation_matrix) for q in rs]
        x0, y0 = max(min(q[0] for q in rs) - 20, 0), max(min(q[1] for q in rs) - 20, 0)
        x1, y1 = min(max(q[2] for q in rs) + 20, pag.rect.width), min(max(q[3] for q in rs) + 20, pag.rect.height)
        rects = [fitz.Rect(q) for q in rs]
        d = dpi
        while True:
            passo = lado * 72.0 / d                  # pedaço em pontos do PDF
            nx, ny = _grade(x1 - x0, y1 - y0, passo)
            w, h = (x1 - x0) / nx, (y1 - y0) / ny
            clips = [fitz.Rect(x0 + (i - 0.08) * w, y0 + (j - 0.08) * h, x0 + (i + 1.08) * w, y0 + (j + 1.08) * h) & pag.rect
                     for i in range(nx) for j in range(ny)]
            # pedaço sem nada da camada (ela desenha espalhado pela folha; 30905): não vai à IA
            clips = [c for c in clips if any(q.intersects(c) for q in rects)]
            if len(out) + len(clips) <= maximo or d <= 130:  # abaixo disso a letra pequena da Nota 02 some
                break
            d *= 0.85
        out += [pag.get_pixmap(dpi=d, clip=c).tobytes("png") for c in clips]
    return out[:maximo]


def transcrever(png, ia=None):
    import base64
    ia = ia or _ia()
    r = ia._ollama("/api/chat", {
        "model": ia.MODELO, "messages": [{"role": "user", "content": IA_PROMPT, "images": [base64.b64encode(png).decode()]}],
        "format": IA_ESQUEMA, "stream": False, "think": False, "keep_alive": "30m",
        "options": {"temperature": 0, "seed": 0, "num_ctx": 8192, "num_predict": 1200}})
    try:
        textos = json.loads((r.get("message") or {}).get("content") or "")["textos"]
    except (ValueError, KeyError, TypeError):
        raise RuntimeError("a IA local respondeu fora do formato")
    return [str(t).strip() for t in textos if str(t).strip()]


def ler_com_ia(pdf, chave="saida", aviso=lambda *_: None):
    """Textos que a IA local leu na camada da medida (cache em <pdf>.ia-<chave>.json, refeito se o PDF, o modelo ou o
    pedido mudar). None: o PDF não tem essa camada."""
    ia = _ia()
    cache = "%s.ia-%s.json" % (pdf, chave)
    try:
        if os.path.getmtime(cache) >= os.path.getmtime(pdf):
            with open(cache, encoding="utf-8") as fh:
                d = json.load(fh)
            if d.get("modelo") == ia.MODELO and d.get("prompt") == IA_PROMPT and d.get("lado") == IA_LADO_MAX and d.get("v") == IA_VERSAO:
                return d["textos"]
    except (OSError, ValueError, KeyError):
        pass
    pngs = imagens_da_camada(pdf, chave)
    if not pngs:
        return None
    textos = []
    for i, png in enumerate(pngs, 1):
        aviso("IA local: %s, pedaço %d de %d…" % (os.path.basename(pdf), i, len(pngs)))
        textos += transcrever(png, ia)
    try:
        with open(cache, "w", encoding="utf-8") as fh:
            json.dump({"modelo": ia.MODELO, "prompt": IA_PROMPT, "lado": IA_LADO_MAX, "v": IA_VERSAO, "pedacos": len(pngs), "textos": textos}, fh,
                      ensure_ascii=False)
    except OSError:
        pass
    return textos


def conferir_ia(lidas):
    """lidas: [(rótulo, textos lidos pela IA na camada da saída)]. Fatos de palpite (ia=True) das Notas 02 e 01."""
    fatos = []
    for rot, textos in lidas:
        t = " · ".join(textos)
        s = sinais(t)
        larg = sorted({m.group(0).strip() for m in re.finditer(SINAIS["largura"], sem_acento(t))})
        tem = [n for n, c in (("largura cotada", "largura"), ("ocupação", "ocupacao"), ("área", "area"),
                              ("população", "pessoas")) if s[c]]
        falta = [n for n in ("largura cotada", "ocupação", "área", "população") if n not in tem]
        fatos.append({"grupo": "6.3.6.1.2.4 Nota 02", "item": "ia_nota02", "ia": True, "texto":
                      "%s · a IA local leu %d texto(s) na camada da saída%s. %s" % (
                          rot, len(textos), (" (números com vírgula: %s)" % ", ".join(larg[:10])) if larg else "",
                          ("Não achou: %s." % ", ".join(falta)) if falta else "Achou largura, ocupação, área e população.")})
        if not s["dmp"]:
            fatos.append({"grupo": "6.3.6.1.2.4 Nota 01", "item": "ia_sem_distancia", "ia": True, "texto":
                          "%s · a IA local não leu texto de distância a percorrer na camada da saída." % rot})
    return fatos


def ler_saida_com_ia(pasta, aviso=lambda *_: None):
    """Plantas baixas ativas com a camada da saída: ([(rótulo, textos)], [erros])."""
    lidas, erros = [], []
    for rot, cam, tipo in pranchas_ativas(pasta, _api(pasta)):
        if not cam or tipo not in ("PLANTA_BAIXA", ""):
            continue
        try:
            t = ler_com_ia(cam, "saida", aviso)
        except Exception as e:  # noqa: BLE001 — uma prancha que falha não derruba as outras
            erros.append("%s: IA local: %s" % (rot, str(e)[:160]))
            continue
        if t is not None:
            lidas.append((rot, t))
    return lidas, erros


# ------------------------------------------------------------------ processo inteiro

def tem_pymupdf():
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            raise RuntimeError("falta o PyMuPDF neste Python (pip install pymupdf==1.28.2; o instalador do SSEG já instala)")
    return fitz


def processo(pasta, ia=False, aviso=lambda *_: None):
    """ia=True: com o texto das plantas baixas em desenho, a IA local transcreve a camada da saída (ler_com_ia)."""
    api = _api(pasta)
    medidas = medidas_campo4(api)
    pranchas, faltam, erros = [], [], []
    tem_pymupdf()  # sem ele, sai com erro antes de ler: o SSEG.exe instala e roda de novo (antes cada prancha virava
    # um erro, o script saía com 0 e o "0 letras de texto legível" aparecia como achado)
    for rot, cam, tipo in pranchas_ativas(pasta, api):
        if not cam:
            faltam.append(rot)
            continue
        try:
            pranchas.append((rot, ler_pdf(cam), tipo))
        except Exception as e:  # noqa: BLE001 — PDF que o PyMuPDF não abre: vai para a lista, não derruba o resto
            erros.append("%s: %s" % (rot, str(e)[:160]))
    r = conferir(medidas, pranchas)
    r.update(medidas=[m["nome"] for m in medidas], faltam=faltam, erros=erros)
    r["ia_cabe"] = any(f["item"] == "ilegivel" for f in r["fatos"]) and any(
        "saida" in {k for _n, k, _d in cams} for cams in r["camadas"].values())
    if ia and r["ia_cabe"]:
        ok, motivo = _ia().ia_local()
        if not ok:
            r["erros"].append(motivo)
        else:
            lidas, errs = ler_saida_com_ia(pasta, aviso)
            r["fatos"] += conferir_ia(lidas)
            r["erros"] += errs
    return r


# Medição de 16/11/2026 (40 processos de CIA única, 20 com e 20 sem notificação de camada): estes fatos saíram quase
# na mesma proporção nos dois grupos e ficam como observação, não como achado.
FRACOS = ("sem_distancia", "cor", "distancia_fora", "ordem_sem_texto")
SECUNDARIAS = ("Acesso de viaturas", "Isolamento", "Iluminação", "Hidrante urbano")


def observacao(f):
    if f.get("ia"):
        return False  # palpite da IA local: seção própria
    if f["item"] in FRACOS:
        return True
    if f["item"] == "sem_camada":
        return f["texto"].startswith(SECUNDARIAS) or (f["texto"].startswith("Sinalização") and "está em" not in f["texto"])
    return False


def relatorio(r):
    linhas = ["CAMADAS DAS PRANCHAS (fatos para o analista; nada aqui é exigência pronta)"]
    if r.get("faltam"):
        linhas.append("Pranchas ativas ainda não baixadas em plantas/: " + "; ".join(r["faltam"]))
    for e in r.get("erros") or []:
        linhas.append("! " + e)
    for rot, cams in r["camadas"].items():
        if not cams:
            linhas.append("- %s: sem camadas" % rot)
            continue
        med = ["%s → %s%s" % (n, MEDIDAS[k][0], " + distância" if d else "") for n, k, d in cams if k in MEDIDAS]
        med += ["%s → distância" % n for n, k, d in cams if k == "distancia"]
        linhas.append("- %s: %d camadas; de medida: %s" % (rot, len(cams), "; ".join(med) or "nenhuma"))
    ia = [f for f in r["fatos"] if f.get("ia")]
    achados = [f for f in r["fatos"] if not observacao(f) and not f.get("ia")]
    obs = [f for f in r["fatos"] if observacao(f)]
    linhas.append("ACHADOS:" if achados else "Nenhum achado.")
    linhas += ["[%s] %s" % (f["grupo"], f["texto"]) for f in achados]
    if obs:
        linhas.append("OBSERVAÇÕES (fracas na medição de 16/11/2026: saem quase igual com e sem notificação na CIA):")
        linhas += ["[%s] %s" % (f["grupo"], f["texto"]) for f in obs]
    if ia:
        linhas.append("LIDO PELA IA LOCAL NA IMAGEM DA CAMADA DA SAÍDA (palpite: ela só transcreve e pode ler número "
                      "errado; conferir na planta):")
        linhas += ["[%s] %s" % (f["grupo"], f["texto"]) for f in ia]
    elif r.get("ia_cabe"):
        linhas.append("O texto das plantas baixas virou desenho: a IA local pode ler a camada da saída na imagem (--ia).")
    return "\n".join(linhas)


def args_parser(p):
    p.add_argument("--pasta", required=True, help="pasta do processo")
    p.add_argument("--json", action="store_true", help="saída em JSON")
    p.add_argument("--ia", action="store_true", help="texto em desenho: a IA local (Ollama) transcreve a camada da saída")


def principal(args):
    r = processo(args.pasta, getattr(args, "ia", False), lambda m: print(m, file=sys.stderr, flush=True))
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(relatorio(r))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pasta")
    g.add_argument("--pdf")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.pdf:
        inv = ler_pdf(a.pdf)
        for n in inv["camadas"] + [""]:
            c = inv["por_camada"].get(n)
            if c:
                print("%-40s %-18s traços %6d (vermelho %6d)  %s" % (n or "(fora de camada)", medida_da_camada(n)[0] if n else "",
                                                                  c["tracos"], c["vermelho"], c["texto"][:120]))
    else:
        principal(a)
