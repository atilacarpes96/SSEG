#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
revisar_cia.py — conferencias deterministicas da CIA antes de fechar a analise.

Roda na revisao final (skill ppci-revisao-cia), depois de "atualizar a pasta". Faz o que o
modelo esquece em esforco baixo e o que so a fonte primaria responde. NAO decide nada: tudo
sai como insumo para o analista, no padrao do sseg.py (OK / !! / XX / ??).

CONFERE
  - forma de cada caixa "Especificar": ate 1.950 caracteres, "m2" em vez de "m²",
    sem quebra de linha dentro do paragrafo, "campo" (e nao "item") para secao do SOL;
  - cada item de norma citado existe no PDF oficial de normas/pdf/ (busca do numero no
    texto do pdftotext; achar o numero NAO prova que o texto diz o que a CIA afirma);
  - versao da norma citada x data de protocolo (dados/indice_normas.json);
  - medida exigida pela tabela da divisao definidora e ausente no campo 4, com o texto da
    nota da celula (a nota e do analista) e se a CIA fala dela;
  - REITERO: se a CIA anterior tem um paragrafo parecido.

USO
  python3 revisar_cia.py --cia "CIA 2.pdf" [--textos "CIA 2 textos.json"] [--json 2.json]
                         [--anterior "CIA 1.pdf"]

  --cia       PDF (ou .txt) da CIA gerada pelo SOL.
  --textos    JSON com o texto de cada caixa, lido pela API do SOL:
              [{"campo": "4", "item": "Alarme de Incendio", "texto": "..."}]
              Sem ele, a forma e conferida no texto inteiro da CIA e o limite de caracteres
              por caixa nao e conferido.
  --json      registro do processo (<N>.json, schema do sseg.py): protocolo, situacao,
              ocupacoes, alturas e medidas do campo 4.
  --anterior  PDF (ou .txt) da CIA anterior, para conferir REITERO.
  --normas    pasta dos PDFs das normas, se nao for ../normas/pdf (ex.: no Cowork).
"""

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import sseg      # noqa: E402  (Saida, _norm, canon_medida, altura_governante, _data)
import tabelas   # noqa: E402  (fonte_por_situacao, acha_divisao, notas, arquivos por grupo)

NORMAS_PDF = os.path.normpath(os.path.join(BASE, "..", "normas", "pdf"))
LIMITE_SEGURO, LIMITE_SOL = 1950, 2000


# ------------------------------------------------------------------------------ texto

def texto_de(caminho):
    """Texto de um PDF (pdftotext, sem -layout, sem form feed) ou de um .txt."""
    if caminho.lower().endswith(".pdf"):
        exe = shutil.which("pdftotext")
        if not exe:
            sys.exit("pdftotext nao encontrado: instale o poppler ou passe um .txt")
        r = subprocess.run([exe, caminho, "-"], capture_output=True)
        if r.returncode != 0:
            sys.exit("pdftotext falhou em %s: %s" % (caminho, r.stderr.decode(errors="replace")))
        t = r.stdout.decode("utf-8", errors="replace")
    else:
        with open(caminho, encoding="utf-8") as fh:
            t = fh.read()
    return t.replace("\f", "\n").replace("\r\n", "\n")


_cache_pdf = {}


def texto_norma(arquivo):
    if arquivo not in _cache_pdf:
        _cache_pdf[arquivo] = sseg._norm(texto_de(os.path.join(NORMAS_PDF, arquivo)))
    return _cache_pdf[arquivo]


# ------------------------------------------------------------------ norma -> PDF local

def _pdf(padrao):
    achados = [os.path.basename(p) for p in glob.glob(os.path.join(NORMAS_PDF, "*.pdf"))
               if re.search(padrao, sseg._norm(os.path.basename(p)))]
    return achados[0] if achados else None


def identifica_norma(trecho):
    """Recebe o texto logo depois de 'item X.Y' e devolve (rotulo, arquivo_pdf, numero, ano)."""
    n = sseg._norm(trecho)
    m = re.search(r"decreto[^0-9]{0,20}51\.?803", n)
    if m:
        return "Decreto 51.803/2014", _pdf(r"decreto\s*51803"), None, None
    if re.search(r"implanta\w*\s+do\s+sol|rt\s*de\s*implanta", n):
        return "RT de Implantacao do SOL", _pdf(r"^rtisol"), None, None
    m = re.search(r"\b(?:in|instrucao normativa)\s*(?:cbmrs\s*)?(?:n\S*\s*)?0*(\d{1,3})", n)
    if m:
        return "IN %s" % m.group(1), _pdf(r"^in0*%s\b" % m.group(1)), None, None
    m = re.search(r"\b(?:it|instrucao tecnica)\s*(?:n\S*\s*)?0*(\d{1,3})", n)
    if m:
        return "IT %s" % m.group(1), _pdf(r"^it0*%s\b" % m.group(1)), None, None
    m = re.search(r"\b(?:rt\s*cbmrs|rtcbmrs|resolucao tecnica(?: cbmrs)?|rt)\s*(?:n\S*\s*)?0*(\d{1,2})"
                  r"(?:\s*[,-]?\s*parte\s*0*(\d+(?:[.,]\d+)?))?(?:\s*(?:/|de)\s*(\d{4}))?", n)
    if not m:
        return None, None, None, None
    num, parte, ano = int(m.group(1)), m.group(2), m.group(3)
    if num == 5:
        if parte and parte.startswith("7"):
            return "RT 05 Parte 07", _pdf(r"^rt 05 parte 07"), num, ano
        if parte and parte.replace(",", ".").startswith("1"):
            return "RT 05 Parte 1.1", _pdf(r"5 parte 1"), num, ano
        return "RT 05 (parte?)", None, num, ano
    if num in (1, 2, 4):
        return "RT %02d" % num, _pdf(r"^rt cbmrs 0?%d\b" % num), num, ano
    return "RT %02d" % num, _pdf(r"^rt0?%d\.pdf$" % num), num, ano


def item_existe(numero, arquivo):
    return re.search(r"(?<![\d.])%s(?![\d])" % re.escape(numero), texto_norma(arquivo)) is not None


# ------------------------------------------------------------------------- conferencias

def confere_forma(caixas, s, com_limite=True):
    s.titulo("Forma das caixas 'Especificar'")
    for rot, txt in caixas:
        tam = len(txt.strip()) if com_limite else 0
        if tam > LIMITE_SOL:
            s.erro("%s — %d caracteres: passa de %d e o SOL corta sem avisar." % (rot, tam, LIMITE_SOL))
        elif tam > LIMITE_SEGURO:
            s.atencao("%s — %d caracteres: acima da margem de %d." % (rot, tam, LIMITE_SEGURO))
        if "²" in txt:
            s.erro("%s — tem '²': no PDF da CIA 'm²' sai como 'm'. Escrever 'm2'." % rot)
        for par in re.split(r"\n\s*\n", txt.strip()):
            if "\n" in par.strip():
                s.atencao("%s — quebra de linha dentro do paragrafo: '%s...'"
                          % (rot, par.strip().split("\n")[0][:60]))
                break
        m = re.search(r"\bite(?:m|ns)\s+\d{1,2}(?![\d.,]\d)\s+(?:do|deste)\s+(?:processo|memorial|ppci|sol)\b",
                      txt, re.I)
        if m:
            s.atencao("%s — '%s': secao do SOL e 'campo', 'item' so para norma." % (rot, m.group(0)))


def confere_citacoes(texto, protocolo, s):
    s.titulo("Itens de norma citados")
    idx = sseg._dados("indice_normas.json")["normas"]
    vistos = set()
    for m in re.finditer(r"\b(?:sub)?ite(?:m|ns)\s+((?:\d+\.)+\d+)", texto, re.I):
        numero = m.group(1)
        trecho = texto[m.end():m.end() + 160]
        rotulo, arquivo, num, ano = identifica_norma(trecho)
        chave = (numero, rotulo)
        if chave in vistos:
            continue
        vistos.add(chave)
        if not rotulo:
            s.pergunta("item %s — nao identifiquei a norma logo depois da citacao." % numero)
            continue
        if not arquivo:
            s.pergunta("item %s da %s — PDF nao esta em normas/pdf/; conferir na fonte." % (numero, rotulo))
            continue
        if item_existe(numero, arquivo):
            s.ok("item %s da %s existe no PDF (%s). Conferir se o texto diz o que a CIA afirma."
                 % (numero, rotulo, arquivo))
        else:
            s.erro("item %s da %s NAO aparece no PDF (%s)." % (numero, rotulo, arquivo))

    # vigencia pela data de protocolo: toda RT citada com ano, com ou sem numero de item
    if not protocolo:
        return
    anos = set()
    for m in re.finditer(r"\b(?:rt\s*cbmrs|rtcbmrs|resolucao tecnica(?: cbmrs)?|rt)\s*(?:n\S*\s*)?0*(\d{1,2})"
                         r"(?:\s*[,-]?\s*parte\s*0*\d+(?:[.,]\d+)?)?\s*(?:/|de)\s*(\d{4})", sseg._norm(texto)):
        anos.add((int(m.group(1)), m.group(2)))
    for num, ano in sorted(anos):
        alvo = next((k for k in idx if re.fullmatch(r"RT 0?%d/%s" % (num, ano), k)), None)
        if not alvo:
            continue
        meta = idx[alvo]
        desde, ate = sseg._data(meta.get("vigente_desde")), sseg._data(meta.get("vigente_ate"))
        if desde and protocolo < desde:
            s.erro("%s citada, mas so vigora desde %s; protocolo em %s."
                   % (alvo, desde.isoformat(), protocolo.isoformat()))
        elif ate and protocolo > ate:
            s.erro("%s citada, mas vigorou ate %s; protocolo em %s (substituida por %s)."
                   % (alvo, ate.isoformat(), protocolo.isoformat(), meta.get("substituida_por", "?")))
        else:
            s.ok("%s: vigente na data de protocolo (%s)." % (alvo, protocolo.isoformat()))


def _tabela_da_divisao(p):
    """(fonte, rotulo, medidas{nome: celula}, texto das notas) da divisao definidora."""
    fkey, _ = tabelas.fonte_por_situacao(p.get("situacao_existencia"))
    div = next((o.get("divisao") for o in p.get("ocupacoes", []) if o.get("definidora")), None)
    area = sseg._num(p.get("area_a_proteger")) or sseg._num(p.get("area_total_construida"))
    h, _q = sseg.altura_governante(p)
    if not (fkey and div and area is not None and h is not None):
        return None, "faltam situacao, divisao definidora, area ou altura no JSON"
    indice = tabelas.carrega_indice()
    if area <= 750 and h <= 12:
        t = tabelas.carrega_arquivo("tab-%s-tabela5.json" % fkey)
        cols = t["colunas"]
        alvo, grupo = sseg._norm(div).replace(" ", ""), sseg._norm(div)[:1]
        ci = next((i for i, c in enumerate(cols)
                   if alvo in [sseg._norm(x).replace(" ", "") for x in re.split(r",| e ", c)]), None)
        if ci is None:
            ci = next((i for i, c in enumerate(cols)
                       if grupo in [sseg._norm(x).replace(" ", "") for x in re.split(r",| e ", c)]), None)
        if ci is None:
            return None, "divisao %s nao localizada nas colunas da Tabela 5" % div
        med = _acha_medidas(t)
        cel = {k: v[ci] for k, v in med["medidas"].items()}
        return (fkey, "Tabela 5, coluna '%s'" % cols[ci], cel, med), None
    achou = tabelas.acha_divisao(indice, fkey, div)
    if not achou:
        return None, "divisao %s nao localizada na fonte %s" % (div, fkey)
    tab, bloco, rot = achou[0]
    t = tabelas.carrega_arquivo(tabelas.arquivo_da_tabela(fkey, tab))["tabelas"][tab]
    col = tabelas.coluna_altura(h)
    ci = sseg.COLUNAS.index(col)
    cel = {k: v[bloco * 6 + ci] for k, v in t["medidas"].items()}
    return (fkey, "Tabela %s, %s, coluna %s" % (tab, rot, col), cel, t), None


def _acha_medidas(o):
    if isinstance(o, dict):
        if isinstance(o.get("medidas"), dict):
            return o
        for v in o.values():
            r = _acha_medidas(v)
            if r:
                return r
    elif isinstance(o, list):
        for v in o:
            r = _acha_medidas(v)
            if r:
                return r
    return None


def confere_medidas(p, texto_cia, s):
    s.titulo("Medidas exigidas pela tabela x campo 4")
    r, erro = _tabela_da_divisao(p)
    if not r:
        s.pergunta("Nao deu para rotear a tabela: %s." % erro)
        return
    fkey, rotulo, celulas, t = r
    s.info("Fonte: %s — %s" % ("RT 05 P07, Anexo A" if fkey == "rt05" else "Decreto 51.803, Anexo B", rotulo))
    no_campo4 = {sseg.canon_medida(m.get("medida")) for m in p.get("medidas", [])}
    cia = sseg._norm(texto_cia)
    for nome, cel in celulas.items():
        if not cel.strip().upper().startswith("X"):
            continue
        chave = sseg.canon_medida(nome)
        if chave in no_campo4:
            continue
        notas = re.findall(r"\d+", cel)
        txt_nota = ""
        if notas and t.get("notas"):
            esp, _ger = tabelas.texto_das_notas(t, notas)
            txt_nota = " Nota: " + " ".join(x.strip() for x in esp) if esp else ""
        citada = any(w in cia for w in dict(sseg._MEDIDAS_CANON).get(chave, [sseg._norm(nome)]))
        if citada:
            s.ok("%s — exigida (%s) e ausente no campo 4; a CIA fala dela.%s" % (nome, cel, txt_nota))
        else:
            s.erro("%s — exigida (%s) e ausente no campo 4, e a CIA NAO fala dela.%s"
                   " A nota, se houver, e do analista." % (nome, cel, txt_nota))
    if (sseg._num((p.get("pavimentos") or {}).get("subsolo")) or 0) > 0:
        s.atencao("Ha subsolo ocupado: conferir tambem a Tabela 7 (exigencias adicionais).")


def _palavras(t):
    return {w for w in re.findall(r"[a-z0-9]{4,}", sseg._norm(t))}


def confere_reitero(caixas, anterior, s):
    s.titulo("REITERO")
    alvos = [(rot, txt) for rot, txt in caixas if re.search(r"\breitero\b", txt, re.I)]
    if not alvos:
        s.info("Nenhum REITERO na CIA.")
        return
    if not anterior:
        for rot, _ in alvos:
            s.pergunta("%s — REITERO sem --anterior: conferir se a CIA anterior notificou isso." % rot)
        return
    pars = [x for x in re.split(r"\n\s*\n", anterior) if len(x.strip()) > 40]
    for rot, txt in alvos:
        a = _palavras(txt)
        melhor = max(((len(a & _palavras(x)) / (len(a | _palavras(x)) or 1), x) for x in pars),
                     default=(0, ""))
        if melhor[0] >= 0.25:
            s.ok("%s — REITERO com correspondente na CIA anterior (%.0f%%): '%s...'"
                 % (rot, melhor[0] * 100, " ".join(melhor[1].split())[:80]))
        else:
            s.atencao("%s — REITERO sem paragrafo parecido na CIA anterior (melhor: %.0f%%). "
                      "REITERO so cabe para exigencia anterior nao atendida." % (rot, melhor[0] * 100))


# ------------------------------------------------------------------------------- cli

def revisar(a):
    global NORMAS_PDF
    if getattr(a, "normas", None):
        NORMAS_PDF = a.normas
    s = sseg.Saida()
    texto_cia = texto_de(a.cia)
    s.add("", "REVISAO DA CIA — %s" % os.path.basename(a.cia))
    if a.textos:
        with open(a.textos, encoding="utf-8") as fh:
            caixas = [("campo %s, %s" % (c.get("campo", "?"), c.get("item", "?")), c.get("texto", ""))
                      for c in json.load(fh)]
    else:
        caixas = [("CIA inteira", texto_cia)]
        s.pergunta("Sem --textos: limite de caracteres por caixa NAO conferido.")
    confere_forma(caixas, s, com_limite=bool(a.textos))

    p = sseg._load(a.json) if a.json else {}
    protocolo = sseg._data(p.get("data_protocolo"))
    if a.json and not protocolo:
        s.atencao("Data de protocolo ausente no JSON: vigencia das normas nao conferida.")
    confere_citacoes(texto_cia, protocolo, s)

    if a.json:
        confere_medidas(p, texto_cia, s)
    else:
        s.pergunta("Sem --json: medidas exigidas x campo 4 NAO conferidas.")

    confere_reitero(caixas if a.textos else [("CIA", x) for x in re.split(r"\n\s*\n", texto_cia)],
                    texto_de(a.anterior) if a.anterior else None, s)
    return s


def args_parser(ap=None):
    ap = ap or argparse.ArgumentParser(description="Conferencias da CIA antes de fechar a analise.")
    ap.add_argument("--cia", required=True)
    ap.add_argument("--textos")
    ap.add_argument("--json")
    ap.add_argument("--anterior")
    ap.add_argument("--normas", help="pasta dos PDFs das normas (padrao: ../normas/pdf)")
    return ap


def main():
    print(revisar(args_parser().parse_args()).texto())


if __name__ == "__main__":
    main()
