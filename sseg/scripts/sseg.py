#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sseg.py — ferramenta de apoio a analise de PPCI no SOL-CBMRS.

O QUE ESTE SCRIPT FAZ E O QUE NAO FAZ
-------------------------------------
FAZ (trabalho deterministico, sempre igual):
  - rotear qual tabela do Anexo B do Decreto 51.803/2014 e qual coluna de altura se aplicam;
  - devolver a contagem de medidas SOMENTE quando a linha ja foi conferida por humano na
    imagem da tabela oficial (dados/tabelas_conferidas.json);
  - conferir as normas citadas no campo "4. Medidas de seguranca" contra o indice do projeto,
    aplicando a regra de vigencia por data de protocolo;
  - rodar as travas de consistencia do projeto (altura, area, medidas faltantes, laudo);
  - renderizar o HTML/PDF de arquivo da pagina da analise tecnica;
  - comparar duas analises do mesmo processo campo a campo.

NAO FAZ (por regra fixa do projeto):
  - NAO conta medidas por extracao automatica de PDF. Se a linha nao estiver conferida,
    responde NAO CONFERIDO e manda pedir a imagem da tabela.
  - NAO cria fundamento normativo. Item/subitem sai do PDF oficial, conferido a olho.
  - NAO decide nada: tudo que sai daqui e insumo para o analista.

USO
---
  python3 sseg.py schema
  python3 sseg.py check     --json processo.json
  python3 sseg.py tabela    --json processo.json
  python3 sseg.py definidora --json processo.json
  python3 sseg.py normas    --json processo.json
  python3 sseg.py render    --json processo.json --out 1.html
  python3 sseg.py pdf       --json processo.json --out 1.pdf
  python3 sseg.py diff      --a 1.json --b 2.json
"""

import argparse
import datetime as _dt
import html as _html
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(BASE, "dados")

COLUNAS = ["Terrea", "H<=6", "6<H<=12", "12<H<=23", "23<H<=30", "H>30"]


# --------------------------------------------------------------------------- util

def _norm(s):
    """minusculas, sem acento, espacos colapsados — para casar rotulos."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _dados(nome):
    return _load(os.path.join(DADOS, nome))


def _data(s):
    if not s:
        return None
    try:
        return _dt.date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


# Nomes canonicos das medidas de seguranca. Casar por prefixo produz falso positivo
# (Compartimentacao Horizontal x Vertical), entao toda comparacao passa por aqui.
_MEDIDAS_CANON = [
    ("compart_horizontal", ["compartimentacao horizontal"]),
    ("compart_vertical", ["compartimentacao vertical"]),
    ("acesso_viaturas", ["acesso de viatura", "acesso de viaturas"]),
    ("seguranca_estrutural", ["seguranca estrutural"]),
    ("cmar", ["controle de materiais de acabamento", "cmar"]),
    ("controle_fumaca", ["controle de fumaca"]),
    ("saidas_emergencia", ["saida de emergencia", "saidas de emergencia"]),
    ("brigada", ["brigada"]),
    ("plano_emergencia", ["plano de emergencia"]),
    ("iluminacao_emergencia", ["iluminacao de emergencia"]),
    ("deteccao", ["deteccao"]),
    ("alarme", ["alarme"]),
    ("sinalizacao", ["sinalizacao"]),
    ("extintores", ["extintor"]),
    ("hidrantes", ["hidrante", "mangotinho"]),
    ("chuveiros", ["chuveiro", "sprinkler"]),
]


def canon_medida(nome):
    """Devolve a chave canonica da medida, ou None se nao reconhecida."""
    n = _norm(re.sub(r"\(.*?\)", "", nome or ""))
    for chave, marcas in _MEDIDAS_CANON:
        if any(m in n for m in marcas):
            return chave
    return None


def _num(v):
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    v = str(v).strip().replace(".", "").replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return None


class Saida:
    """Acumula linhas com um marcador de severidade, para o relatorio final."""

    OK, INFO, ATENCAO, ERRO, PERGUNTA = "OK", "  ", "!!", "XX", "??"

    def __init__(self):
        self.linhas = []

    def add(self, marca, texto):
        self.linhas.append((marca, texto))

    def ok(self, t):
        self.add(self.OK, t)

    def info(self, t):
        self.add(self.INFO, t)

    def atencao(self, t):
        self.add(self.ATENCAO, t)

    def erro(self, t):
        self.add(self.ERRO, t)

    def pergunta(self, t):
        self.add(self.PERGUNTA, t)

    def titulo(self, t):
        self.add("", "")
        self.add("", "== %s ==" % t)

    def texto(self):
        out = []
        for marca, t in self.linhas:
            out.append(("%s %s" % (marca, t)).rstrip() if marca.strip() else t)
        return "\n".join(out)


# ----------------------------------------------------------------------- rota tabela

def coluna_altura(h):
    """Coluna de altura das Tabelas 6 do Anexo B."""
    if h is None:
        return None
    if h <= 0:
        return "Terrea"
    if h <= 6:
        return "H<=6"
    if h <= 12:
        return "6<H<=12"
    if h <= 23:
        return "12<H<=23"
    if h <= 30:
        return "23<H<=30"
    return "H>30"


def altura_governante(p):
    """
    Altura usada para escolher a coluna. RT 02/2014 item 4.20: a altura e medida pelo
    PERCURSO DO OCUPANTE ate a saida, nao pela posicao do pavimento em relacao ao solo.
    Usa a maior entre ascendente e descendente e sempre devolve qual foi usada, para o
    analista confirmar.
    """
    asc = _num(p.get("altura_ascendente")) or 0.0
    desc = _num(p.get("altura_descendente")) or 0.0
    if desc >= asc:
        return desc, "descendente"
    return asc, "ascendente"


def rota_tabela(p, s=None):
    """Roteia ate a tabela e a coluna aplicaveis. Nunca conta medidas aqui."""
    s = s or Saida()
    situacao = _norm(p.get("situacao_existencia"))
    area = _num(p.get("area_total_construida"))
    h, qual = altura_governante(p)
    subsolo_ocupado = bool(p.get("subsolo_ocupado")) or (
        (p.get("pavimentos") or {}).get("subsolo") or 0
    ) > 0

    s.titulo("Fonte das exigencias")
    if "regularizada" in situacao and "nao" not in situacao:
        s.atencao(
            "Situacao declarada: EXISTENTE REGULARIZADA -> as medidas exigidas saem da "
            "RT 05 Parte 07/2025, NAO das tabelas do Decreto 51.803/2014. "
            "O roteamento abaixo so vale se a situacao for 'existente nao regularizada' ou 'a construir'."
        )
    elif situacao:
        s.ok("Situacao declarada: %s -> exigencias pelo Decreto 51.803/2014 (Anexo B)."
             % p.get("situacao_existencia"))
    else:
        s.pergunta("Situacao de existencia nao informada no JSON. Ela decide a fonte "
                   "(RT 05 P07/2025 se 'existente regularizada'; Decreto 51.803/2014 nos demais casos).")

    s.titulo("Rota da tabela (Anexo B do Decreto 51.803/2014)")
    if area is None:
        s.pergunta("Area total construida ausente — impossivel rotear.")
        return None, None, s
    if h is None:
        s.pergunta("Altura ausente — impossivel rotear.")
        return None, None, s

    s.info("Area total construida: %s m2" % ("%.2f" % area))
    s.info("Altura governante: %.2f m (%s) — RT 02/2014, item 4.20: a altura e o percurso "
           "do ocupante ate a saida." % (h, qual))

    if abs(area - 750.0) < 0.005 or abs(h - 12.0) < 0.005:
        s.atencao("Valor exatamente no limite (750 m2 e/ou 12,00 m). A Tabela 4 roteia por "
                  "'< 750 e < 12' e a Tabela 5 se declara para '<= 750 e <= 12'. Conferir a "
                  "redacao do Anexo B para este caso limite antes de fundamentar.")

    if area <= 750.0 and h <= 12.0:
        tabela = "5"
        s.ok("Tabela 4 roteia para -> TABELA 5 (area <= 750 m2 E altura <= 12,00 m).")
        coluna = None
    else:
        divisao = next((o.get("divisao") for o in p.get("ocupacoes", []) if o.get("definidora")), None)
        coluna = coluna_altura(h)
        if divisao:
            tabela, confirmada = tabela_para_divisao(divisao)
            s.ok("Tabela 4 roteia para -> TABELAS 6 (area > 750 m2 e/ou altura > 12 m). "
                 "Divisao definidora %s -> TABELA %s." % (divisao, tabela))
            if not confirmada:
                s.pergunta("A subdivisao da Tabela 6 para %s ainda NAO foi confirmada no projeto "
                           "(as Tabelas 6 se subdividem em 6F.1/6F.2/6F.3 etc., o que nao se deduz "
                           "do grupo). Confirmar no Anexo B qual subdivisao contem essa divisao." % divisao)
        else:
            tabela = "6?"
            s.pergunta("Nenhuma ocupacao marcada como definidora no JSON — nao da para "
                       "nomear a Tabela 6X. Rodar 'definidora' antes.")
        s.ok("Coluna de altura -> %s" % coluna)

    if subsolo_ocupado:
        s.atencao("Ha subsolo ocupado -> verificar tambem a TABELA 7 (subsolos ocupados).")

    return tabela, coluna, s


def tabela_para_divisao(divisao):
    """
    Nome da Tabela 6X que contem a divisao. As Tabelas 6 tem subdivisoes (6F.1, 6F.2, 6F.3...)
    que NAO dao para deduzir do grupo — so as confirmadas em dados/tabelas_conferidas.json
    sao devolvidas com certeza. Retorna (tabela, confirmada?).
    """
    div = _norm(divisao).upper().replace(" ", "")
    mapa = _dados("tabelas_conferidas.json")["grupos_por_tabela"]
    for tab, meta in mapa.items():
        if any(_norm(d).upper().replace(" ", "") == div for d in meta["divisoes"]):
            return tab, meta.get("status") == "confirmado"
    grupo = (divisao or "").split("-")[0].strip().upper()
    return ("6%s" % grupo) if grupo else None, False


def linha_conferida(divisao, coluna):
    tabela, _conf = tabela_para_divisao(divisao)
    if not tabela:
        return None
    dados = _dados("tabelas_conferidas.json")
    for ln in dados["linhas"]:
        if (_norm(ln["tabela"]) == _norm(tabela)
                and _norm(ln["divisao"]) == _norm(divisao)
                and _norm(ln["coluna"]) == _norm(coluna)):
            return ln
    return None


# ------------------------------------------------------------------------ definidora

def grau_risco(carga):
    """
    Tabela 3 do Decreto 51.803/2014, por carga de incendio (MJ/m2).
    CONFERIDO no projeto: acima de 300 ate 1.200 = MEDIO.
    Os limites de baixo/alto sao inferidos a partir dessa faixa — o script marca isso.
    """
    c = _num(carga)
    if c is None:
        return None, "carga de incendio nao informada"
    if c <= 300:
        return "baixo", "inferido (so a faixa 'medio' esta conferida no projeto)"
    if c <= 1200:
        return "medio", "conferido (>300 ate 1.200 MJ/m2 = medio)"
    return "alto", "inferido (so a faixa 'medio' esta conferida no projeto)"


def definidora(p, s=None):
    """Confere se a definidora declarada pelo RT esta correta. RT 01/2024, item 5.1.2."""
    s = s or Saida()
    s.titulo("Ocupacao definidora de medidas (RT 01/2024, item 5.1.2)")

    ocupacoes = p.get("ocupacoes", [])
    if not ocupacoes:
        s.pergunta("Nenhuma ocupacao no JSON.")
        return s

    declarada = [o for o in ocupacoes if o.get("definidora")]
    predominantes = [o for o in ocupacoes if o.get("predominante")]

    if len(declarada) == 1:
        s.info("Definidora declarada pelo RT (coluna 'Medidas de seguranca contra incendio? = Sim'): %s"
               % declarada[0].get("divisao"))
    elif not declarada:
        s.atencao("Nenhuma ocupacao marcada como definidora. No print do SOL, a definidora e a "
                  "unica com 'Sim' na coluna 'Medidas de seguranca contra incendio?'.")
    else:
        s.erro("Mais de uma ocupacao marcada como definidora (%s) — no SOL so uma pode ser 'Sim'."
               % ", ".join(o.get("divisao", "?") for o in declarada))

    if len(predominantes) <= 1:
        s.ok("Uma unica ocupacao predominante — nao ha disputa de definidora.")
        return s

    # Regra especial: F-6 e sempre definidora quando presente (item 5.1.2.1).
    f6 = [o for o in ocupacoes if (o.get("divisao") or "").upper().replace(" ", "") == "F-6"]
    if f6:
        s.atencao("Existe divisao F-6 no processo. RT 01/2024, item 5.1.2.1: a F-6 e SEMPRE "
                  "definidora nas ocupacoes mistas. Se o RT declarou outra, vira exigencia.")
        return s

    s.info("Predominantes: %s" % ", ".join(o.get("divisao", "?") for o in predominantes))

    # Criterio (a): maior grau de risco.
    graus = {}
    for o in predominantes:
        g, obs = grau_risco(o.get("carga_incendio"))
        graus[o.get("divisao")] = g
        s.info("  %s — carga %s MJ/m2 -> grau %s [%s]"
               % (o.get("divisao"), o.get("carga_incendio"), g, obs))

    ordem = {"baixo": 1, "medio": 2, "alto": 3}
    validos = {d: g for d, g in graus.items() if g}
    if not validos:
        s.pergunta("Sem carga de incendio nao da para aplicar o criterio (a).")
        return s
    maior = max(ordem[g] for g in validos.values())
    lideres = [d for d, g in validos.items() if ordem[g] == maior]

    if len(lideres) == 1:
        s.ok("Criterio (a) resolve: %s tem o maior grau de risco -> e a definidora." % lideres[0])
        if declarada and declarada[0].get("divisao") != lideres[0]:
            s.erro("DIVERGENCIA: o RT declarou %s como definidora, mas o criterio (a) aponta %s."
                   % (declarada[0].get("divisao"), lideres[0]))
        return s

    s.info("Empate no grau de risco entre %s -> vai para o criterio (b): maior numero "
           "absoluto de medidas exigidas." % ", ".join(lideres))

    h, _q = altura_governante(p)
    coluna = coluna_altura(h)
    contagens, faltando = {}, []
    for div in lideres:
        tab, _c = tabela_para_divisao(div)
        ln = linha_conferida(div, coluna)
        if ln:
            contagens[div] = ln["total_medidas"]
            s.ok("  %s -> Tabela %s, coluna %s = %d medidas (linha conferida na imagem em %s)"
                 % (div, tab, coluna, ln["total_medidas"], ln["conferido_em"]))
        else:
            faltando.append((div, tab, coluna))

    for div, tab, col in faltando:
        s.pergunta("  %s -> Tabela %s, coluna %s: NAO CONFERIDO. Contagem de medidas nunca sai "
                   "de extracao de PDF. Mandar a IMAGEM dessa linha da tabela para eu ler celula "
                   "a celula e registrar em dados/tabelas_conferidas.json." % (div, tab, col))

    if contagens and not faltando:
        vencedor = max(contagens, key=contagens.get)
        empate = [d for d, n in contagens.items() if n == contagens[vencedor]]
        if len(empate) > 1:
            s.atencao("Empate tambem no criterio (b) (%s). Escalar: o Decreto nao resolve sozinho."
                      % ", ".join(empate))
        else:
            s.ok("Criterio (b) resolve: %s exige %d medidas -> e a definidora."
                 % (vencedor, contagens[vencedor]))
            if declarada and declarada[0].get("divisao") != vencedor:
                s.erro("DIVERGENCIA: o RT declarou %s, mas quem exige mais medidas e %s. "
                       "Vira exigencia na notificacao." % (declarada[0].get("divisao"), vencedor))
            else:
                s.ok("O RT acertou a definidora.")
    return s


# ---------------------------------------------------------------------------- normas

def confere_normas(p, s=None):
    s = s or Saida()
    idx = _dados("indice_normas.json")
    protocolo = _data(p.get("data_protocolo"))

    s.titulo("Normas citadas no campo '4. Medidas de seguranca'")
    if not protocolo:
        s.atencao("Data de protocolo do PPCI ausente. A versao aplicavel de uma RT e a que "
                  "estava vigente NA DATA DE PROTOCOLO — sem ela nao da para decidir entre "
                  "versoes (ex.: RT 01/2022 x RT 01/2024). Pedir ao usuario.")
    else:
        s.info("Data de protocolo: %s" % protocolo.isoformat())

    medidas = p.get("medidas", [])
    if not medidas:
        s.pergunta("Nenhuma medida no JSON.")
        return s

    mapa = idx["medida_para_norma"]
    sem_rt = set(idx["medidas_sem_rt_propria_mapeada"])

    def _bate(citada, alvo):
        return _norm(alvo).replace(" ", "").replace("parte", "p") in \
               _norm(citada).replace(" ", "").replace("parte", "p")

    for m in medidas:
        nome = m.get("medida", "?")
        citada = (m.get("norma") or "").strip()
        chave = canon_medida(nome)

        if chave is None:
            s.pergunta("%s — medida nao reconhecida. Conferir '%s' na fonte oficial."
                       % (nome, citada or "vazio"))
            continue
        if chave in sem_rt:
            s.info("%s — sem RT propria do CBMRS mapeada no indice; conferir a fonte citada "
                   "('%s') manualmente." % (nome, citada or "vazio"))
            continue
        esperadas = mapa.get(chave)
        if not esperadas:
            s.pergunta("%s — medida sem norma mapeada no indice. Conferir '%s'."
                       % (nome, citada or "vazio"))
            continue

        if not citada or citada in ("-", "--"):
            s.atencao("%s — nenhuma norma citada no processo. Esperada: %s."
                      % (nome, " ou ".join(esperadas)))
            continue

        aceita = next((a for a in esperadas if _bate(citada, a)), None)
        if aceita:
            s.ok("%s — cita %s (bate com o indice)." % (nome, citada))
            continue

        alvo = esperadas[0]
        meta = idx["normas"].get(alvo, {})
        vig = _data(meta.get("vigente_desde"))

        if meta.get("facultativa_antes") and vig and protocolo and protocolo < vig:
            s.info("%s — cita '%s'. A %s so e obrigatoria a partir de %s; ate la e facultativa, "
                   "entao citar outra norma aqui NAO e pendencia por si so."
                   % (nome, citada, alvo, vig.isoformat()))
        elif vig and protocolo and protocolo < vig:
            s.atencao("%s — cita '%s'. A %s so passou a vigorar em %s, DEPOIS do protocolo (%s): "
                      "a versao anterior pode estar correta. Confirmar qual estava vigente na data "
                      "antes de notificar." % (nome, citada, alvo, vig.isoformat(), protocolo.isoformat()))
        elif meta.get("transicao_desconhecida") or idx["normas"].get(citada, {}).get("transicao_desconhecida"):
            s.pergunta("%s — cita '%s'; o indice espera %s. As datas de transicao entre as versoes "
                       "dessa RT NAO estao registradas no projeto — nao dar como errado sem confirmar."
                       % (nome, citada, alvo))
        else:
            s.atencao("%s — cita '%s'; o indice aponta %s como vigente%s. Conferir e, se for o caso, "
                      "notificar 'Adequar norma utilizada'."
                      % (nome, citada, alvo, " desde %s" % vig.isoformat() if vig else ""))
    return s


# ----------------------------------------------------------------------- consistencia

def travas(p, s=None):
    """Travas de erro ja cometidas no projeto — nunca repetir."""
    s = s or Saida()
    s.titulo("Travas de consistencia")

    asc = _num(p.get("altura_ascendente")) or 0.0
    desc = _num(p.get("altura_descendente")) or 0.0
    pav = p.get("pavimentos") or {}
    acima = _num(pav.get("acima")) or 0
    subsolo = _num(pav.get("subsolo")) or 0

    # A trava mais importante do projeto: NAO apontar inversao de altura por geometria.
    if desc > 0 and subsolo == 0:
        s.ok("Altura descendente %.2f m com 0 subsolos e o preenchimento CORRETO (RT 02/2014, "
             "item 4.20: o ocupante desce para sair). Nao apontar inversao." % desc)
    if acima > 0 and desc == 0:
        s.atencao("Ha %d pavimento(s) acima do solo e altura descendente zerada — verificar "
                  "com o RT antes de notificar (RT 02/2014, item 4.20)." % acima)
    if subsolo > 0 and asc == 0:
        s.atencao("Ha subsolo ocupado e altura ascendente zerada — verificar (RT 02/2014, item 4.20).")

    pmp = p.get("pavimento_maior_populacao") or {}
    if pmp:
        s.info("Pavimento de maior populacao informado — RT 02/2014, item 4.30: desconsiderar "
               "o pavimento de DESCARGA nessa informacao.")

    a_total = _num(p.get("area_total_construida"))
    a_prot = _num(p.get("area_a_proteger"))
    if a_total and a_prot and a_prot < a_total:
        s.info("Area a proteger (%.2f) menor que a construida (%.2f) — ha desconto declarado. "
               "Conferir o fundamento do desconto e a nota em planta." % (a_prot, a_total))

    # Compartimentacao declarada x representada: so da para conferir com a planta.
    for m in p.get("medidas", []):
        if _norm(m.get("compartimentacao")) in ("sim", "s"):
            s.info("'%s' marcada com compartimentacao = Sim -> conferir na planta se ha elemento "
                   "corta-fogo representado; se nao houver, ha modelo de notificacao no banco."
                   % m.get("medida"))

    # Laudo de inviabilidade x campo 4.
    laudo = p.get("laudo_inviabilidade") or {}
    if laudo.get("presente"):
        s.titulo("Laudo de inviabilidade tecnica x campo 4")
        s.info("Laudo ja aprovado pela chefia antes de chegar a analise — nesta fase NAO se "
               "reavalia a admissibilidade da medida compensatoria, e sim representacao, "
               "coerencia com a planta e correspondencia com o campo 4.")
        chaves4 = {canon_medida(m.get("medida")) for m in p.get("medidas", [])} - {None}
        for mc in laudo.get("medidas_compensatorias", []):
            achou = canon_medida(mc) in chaves4
            if achou:
                s.ok("Compensatoria '%s' tem linha no campo 4 -> conferir representacao e "
                     "dimensionamento na planta." % mc)
            else:
                s.erro("Compensatoria '%s' NAO tem linha no campo 4 -> nao esta lancada no "
                       "processo, logo nao sera analisada nem cobrada em vistoria -> NOTIFICAR. "
                       "Atencao: se ela nao e exigida pela tabela do Decreto para essa "
                       "divisao/altura, a obrigatoriedade nasce do PROPRIO LAUDO — o campo "
                       "'Especificar' precisa dizer isso, porque a opcao padrao do SOL "
                       "('exigida conforme a legislacao e regulamentacao aplicaveis') diria o "
                       "contrario e o RT contestaria com razao." % mc)

    # Medidas exigidas pela linha conferida x medidas presentes no campo 4.
    div = next((o.get("divisao") for o in p.get("ocupacoes", []) if o.get("definidora")), None)
    if div:
        h, _q = altura_governante(p)
        ln = linha_conferida(div, coluna_altura(h))
        if ln:
            s.titulo("Medidas exigidas (linha conferida) x campo 4")
            presentes = {canon_medida(m.get("medida")) for m in p.get("medidas", [])} - {None}
            for exig in ln["exigidas"]:
                if canon_medida(exig) in presentes:
                    s.ok("%s — presente no campo 4." % exig)
                else:
                    s.erro("%s — EXIGIDA pela Tabela %s (%s, %s) e ausente do campo 4."
                           % (exig, ln["tabela"], ln["divisao"], ln["coluna"]))
            for nao in ln["nao_exigidas"]:
                if canon_medida(nao) in presentes:
                    s.atencao("%s consta no campo 4 mas NAO e exigida nessa linha da tabela — "
                              "se veio de laudo/opcao do RT, o fundamento nao e a tabela." % nao)
        else:
            s.pergunta("Linha da tabela nao conferida para %s / %s — nao da para cruzar as "
                       "medidas exigidas com o campo 4. Mandar a imagem da tabela."
                       % (div, coluna_altura(h)))
    return s


# ----------------------------------------------------------------------------- render

_CSS = """
@page { size: A4; margin: 12mm 10mm; }
* { box-sizing: border-box; }
body { font: 10.5px/1.45 "DejaVu Sans", Arial, sans-serif; color: #111; margin: 0; }
h1 { font-size: 15px; margin: 0 0 2px; }
h2 { font-size: 11.5px; margin: 14px 0 5px; padding-bottom: 3px;
     border-bottom: 1.5px solid #444; text-transform: uppercase; letter-spacing: .04em; }
.meta { color: #555; font-size: 9.5px; margin-bottom: 6px; }
table { width: 100%; border-collapse: collapse; margin: 4px 0 8px; }
th, td { border: 1px solid #bbb; padding: 3px 5px; text-align: left; vertical-align: top; }
th { background: #eee; font-weight: 600; }
td.num { text-align: right; white-space: nowrap; }
.badge { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 9px;
         font-weight: 700; color: #fff; white-space: nowrap; }
.b-aprovado { background: #1a7f37; }
.b-reprovado { background: #b3261e; }
.b-analisar { background: #7a6000; }
dl { display: grid; grid-template-columns: max-content 1fr; gap: 2px 10px; margin: 4px 0 8px; }
dt { color: #555; }
dd { margin: 0; font-weight: 600; }
.rodape { margin-top: 14px; padding-top: 5px; border-top: 1px solid #ccc;
          color: #666; font-size: 8.5px; }
"""


def _badge(status):
    n = _norm(status)
    cls = "b-analisar"
    if "aprov" in n:
        cls = "b-aprovado"
    elif "reprov" in n:
        cls = "b-reprovado"
    return '<span class="badge %s">%s</span>' % (cls, _html.escape(str(status or "Analisar")))


def _tabela(cols, rows, num_cols=()):
    out = ["<table><thead><tr>"]
    out += ["<th>%s</th>" % _html.escape(c) for c in cols]
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for i, c in enumerate(r):
            cls = ' class="num"' if i in num_cols else ""
            out.append("<td%s>%s</td>" % (cls, c))
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def render_html(p):
    e = lambda v: _html.escape("" if v is None else str(v))
    pav = p.get("pavimentos") or {}
    partes = []
    partes.append("<h1>Análise técnica do licenciamento — %s</h1>" % e(p.get("processo")))
    partes.append('<div class="meta">%sª Análise &middot; cópia gerada em %s &middot; '
                  "SOL-CBMRS</div>"
                  % (e(p.get("analise")), _dt.date.today().strftime("%d/%m/%Y")))

    partes.append("<h2>Identificação e localização</h2><dl>")
    for rot, ch in [("Processo", "processo"), ("Análise", "analise"),
                    ("Data de protocolo", "data_protocolo"),
                    ("Responsável técnico", "responsavel_tecnico"),
                    ("Proprietário / responsável pelo uso", "proprietario"),
                    ("Endereço", "endereco"), ("Município", "municipio")]:
        if p.get(ch) not in (None, ""):
            partes.append("<dt>%s</dt><dd>%s</dd>" % (rot, e(p.get(ch))))
    partes.append("</dl>")

    partes.append("<h2>Características da edificação</h2><dl>")
    for rot, val in [
        ("Tipo de edificação", p.get("tipo_edificacao")),
        ("Situação de existência", p.get("situacao_existencia")),
        ("Característica construtiva", p.get("caracteristica_construtiva")),
        ("Área total construída", "%s m²" % p.get("area_total_construida") if p.get("area_total_construida") else None),
        ("Área a proteger", "%s m²" % p.get("area_a_proteger") if p.get("area_a_proteger") else None),
        ("Pavimentos acima do solo", pav.get("acima")),
        ("Subsolos", pav.get("subsolo")),
        ("Altura descendente", "%s m" % p.get("altura_descendente") if p.get("altura_descendente") is not None else None),
        ("Altura ascendente", "%s m" % p.get("altura_ascendente") if p.get("altura_ascendente") is not None else None),
        ("População total", p.get("populacao_total")),
    ]:
        if val not in (None, ""):
            partes.append("<dt>%s</dt><dd>%s</dd>" % (rot, e(val)))
    partes.append("</dl>")

    if p.get("ocupacoes"):
        partes.append("<h2>3. Ocupações</h2>")
        partes.append(_tabela(
            ["Divisão", "Descrição", "Área (m²)", "Carga (MJ/m²)", "Predominante",
             "Subsolo", "Medidas de segurança?"],
            [[e(o.get("divisao")), e(o.get("descricao")), e(o.get("area")),
              e(o.get("carga_incendio")), "Sim" if o.get("predominante") else "Não",
              "Sim" if o.get("subsolo") else "Não",
              "<b>Sim</b>" if o.get("definidora") else "Não"] for o in p["ocupacoes"]],
            num_cols=(2, 3)))

    if p.get("medidas"):
        partes.append("<h2>4. Medidas de segurança</h2>")
        partes.append(_tabela(
            ["Medida de segurança", "Norma", "Inviabilidade técnica", "Compartimentação", "Status"],
            [[e(m.get("medida")), e(m.get("norma")), e(m.get("inviabilidade") or "Não"),
              e(m.get("compartimentacao") or "Não"), _badge(m.get("status"))]
             for m in p["medidas"]]))

    if p.get("riscos_especificos"):
        partes.append("<h2>5. Riscos específicos</h2>")
        partes.append(_tabela(
            ["Risco", "Detalhe", "Status"],
            [[e(r.get("risco")), e(r.get("detalhe")), _badge(r.get("status"))]
             for r in p["riscos_especificos"]]))

    if p.get("elementos_graficos"):
        partes.append("<h2>6. Elementos gráficos</h2>")
        partes.append(_tabela(
            ["Arquivo", "Tipo", "Data", "Status"],
            [[e(g.get("nome")), e(g.get("tipo")), e(g.get("data")), _badge(g.get("status"))]
             for g in p["elementos_graficos"]]))

    if p.get("demais_inconformidades"):
        partes.append("<h2>Demais inconformidades</h2>")
        partes.append(_tabela(
            ["Item", "Status"],
            [[e(d.get("item")), _badge(d.get("status"))] for d in p["demais_inconformidades"]]))

    laudo = p.get("laudo_inviabilidade") or {}
    if laudo.get("presente"):
        partes.append("<h2>Laudo de inviabilidade técnica</h2><ul>")
        for mc in laudo.get("medidas_compensatorias", []):
            partes.append("<li>%s</li>" % e(mc))
        partes.append("</ul>")

    partes.append('<div class="rodape">Cópia de arquivo interno da página da análise técnica do '
                  "SOL-CBMRS, gerada a partir do registro estruturado do processo. Os textos das "
                  "inconformidades não constam desta página — ficam na caixa &quot;Especificar&quot; "
                  "de cada medida e só são impressos na CIA. Arquivar sempre os dois.</div>")

    return ("<!doctype html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\">"
            "<title>%s — %sª Análise</title><style>%s</style></head><body>%s</body></html>"
            % (e(p.get("processo")), e(p.get("analise")), _CSS, "".join(partes)))


def _chrome():
    for cand in ("/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
                 "/opt/pw-browsers/chromium/chrome-linux/chrome"):
        if os.path.exists(cand):
            return cand
    import glob
    for pat in ("/opt/pw-browsers/chromium*/chrome-linux/chrome",
                "/opt/pw-browsers/chromium*/chrome-linux/headless_shell"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return shutil.which("chromium") or shutil.which("google-chrome") or shutil.which("chrome")


def gerar_pdf(html_path, out_pdf):
    chrome = _chrome()
    if not chrome:
        raise SystemExit("Chromium nao encontrado neste ambiente.")
    cmd = [chrome, "--headless", "--disable-gpu", "--no-sandbox",
           "--no-pdf-header-footer", "--print-to-pdf=%s" % os.path.abspath(out_pdf),
           "file://%s" % os.path.abspath(html_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if not os.path.exists(out_pdf):
        raise SystemExit("Falha ao gerar PDF.\n%s\n%s" % (r.stdout, r.stderr))
    return out_pdf


# ------------------------------------------------------------------------------- diff

_ROTULOS = {
    "data_protocolo": "Data de protocolo", "situacao_existencia": "Situacao de existencia",
    "tipo_edificacao": "Tipo de edificacao", "caracteristica_construtiva": "Caracteristica construtiva",
    "area_total_construida": "Area total construida", "area_a_proteger": "Area a proteger",
    "altura_descendente": "Altura descendente", "altura_ascendente": "Altura ascendente",
    "populacao_total": "Populacao total", "responsavel_tecnico": "Responsavel tecnico",
    "endereco": "Endereco",
}


def diff(a, b, s=None):
    s = s or Saida()
    s.titulo("Comparacao %sa Analise -> %sa Analise (%s)"
             % (a.get("analise"), b.get("analise"), a.get("processo") or b.get("processo")))

    if (a.get("processo") or "") != (b.get("processo") or ""):
        s.erro("Processos diferentes (%s x %s) — nao comparar." % (a.get("processo"), b.get("processo")))
        return s

    mudou = False
    for ch, rot in _ROTULOS.items():
        va, vb = a.get(ch), b.get(ch)
        if va != vb:
            mudou = True
            s.atencao("%s: %s -> %s" % (rot, va, vb))

    pa, pb = a.get("pavimentos") or {}, b.get("pavimentos") or {}
    if pa != pb:
        mudou = True
        s.atencao("Pavimentos: %s -> %s" % (pa, pb))

    oa = {o.get("divisao"): o for o in a.get("ocupacoes", [])}
    ob = {o.get("divisao"): o for o in b.get("ocupacoes", [])}
    for d in sorted(set(oa) - set(ob)):
        mudou = True
        s.atencao("Ocupacao REMOVIDA: %s" % d)
    for d in sorted(set(ob) - set(oa)):
        mudou = True
        s.atencao("Ocupacao INCLUIDA: %s" % d)
    for d in sorted(set(oa) & set(ob)):
        for k in ("area", "carga_incendio", "predominante", "definidora", "subsolo"):
            if oa[d].get(k) != ob[d].get(k):
                mudou = True
                s.atencao("Ocupacao %s, %s: %s -> %s" % (d, k, oa[d].get(k), ob[d].get(k)))

    ma = {_norm(m.get("medida")): m for m in a.get("medidas", [])}
    mb = {_norm(m.get("medida")): m for m in b.get("medidas", [])}
    for k in sorted(set(ma) - set(mb)):
        mudou = True
        s.erro("Medida REMOVIDA do campo 4: %s" % ma[k].get("medida"))
    for k in sorted(set(mb) - set(ma)):
        mudou = True
        s.ok("Medida INCLUIDA no campo 4: %s" % mb[k].get("medida"))
    for k in sorted(set(ma) & set(mb)):
        for campo in ("norma", "inviabilidade", "compartimentacao", "status"):
            if (ma[k].get(campo) or "") != (mb[k].get(campo) or ""):
                mudou = True
                marca = s.ok if campo == "status" else s.atencao
                marca("Medida %s, %s: %s -> %s"
                      % (mb[k].get("medida"), campo, ma[k].get(campo), mb[k].get(campo)))

    ga = {g.get("nome"): g.get("data") for g in a.get("elementos_graficos", [])}
    gb = {g.get("nome"): g.get("data") for g in b.get("elementos_graficos", [])}
    for n in sorted(set(gb) - set(ga)):
        mudou = True
        s.ok("Elemento grafico NOVO: %s (%s)" % (n, gb[n]))
    for n in sorted(set(ga) & set(gb)):
        if ga[n] != gb[n]:
            mudou = True
            s.ok("Elemento grafico REENVIADO: %s (%s -> %s)" % (n, ga[n], gb[n]))
    for n in sorted(set(ga) - set(gb)):
        mudou = True
        s.atencao("Elemento grafico REMOVIDO: %s" % n)

    if not mudou:
        s.ok("Nenhuma diferenca nos campos comparados — o RT nao alterou o memorial.")
    s.info("")
    s.info("Os textos das inconformidades NAO estao nesta pagina: comparar tambem as CIAs "
           "arquivadas para saber o que foi respondido.")
    return s


# ------------------------------------------------------------------------------ schema

SCHEMA = {
    "processo": "A00016097AA002",
    "analise": 1,
    "data_protocolo": "2026-07-15",
    "situacao_existencia": "existente nao regularizada | existente regularizada | a construir",
    "responsavel_tecnico": "", "proprietario": "", "endereco": "", "municipio": "",
    "tipo_edificacao": "", "caracteristica_construtiva": "X | Y | Z",
    "area_total_construida": 6233.53, "area_a_proteger": 6233.53,
    "pavimentos": {"acima": 4, "subsolo": 0},
    "altura_descendente": 9.08, "altura_ascendente": 0.0,
    "populacao_total": 0,
    "pavimento_maior_populacao": {"area": 0, "populacao": 0},
    "ocupacoes": [{"divisao": "B-1", "descricao": "", "area": 0, "carga_incendio": 500,
                   "predominante": True, "subsolo": False, "definidora": True}],
    "medidas": [{"medida": "Alarme de Incendio", "norma": "RT 18/2025",
                 "inviabilidade": "Nao", "compartimentacao": "Nao", "status": "Analisar"}],
    "riscos_especificos": [{"risco": "", "detalhe": "", "status": "Analisar"}],
    "elementos_graficos": [{"nome": "", "tipo": "", "data": "", "status": "Analisar"}],
    "demais_inconformidades": [{"item": "", "status": "Analisar"}],
    "laudo_inviabilidade": {"presente": False, "medidas_compensatorias": []},
}


# -------------------------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description="Apoio a analise de PPCI no SOL-CBMRS.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for nome in ("check", "tabela", "definidora", "normas", "travas"):
        sp = sub.add_parser(nome)
        sp.add_argument("--json", required=True)

    sp = sub.add_parser("render")
    sp.add_argument("--json", required=True)
    sp.add_argument("--out", required=True)

    sp = sub.add_parser("pdf")
    sp.add_argument("--json", required=True)
    sp.add_argument("--out", required=True)

    sp = sub.add_parser("diff")
    sp.add_argument("--a", required=True)
    sp.add_argument("--b", required=True)

    sub.add_parser("schema")

    args = ap.parse_args()

    if args.cmd == "schema":
        print(json.dumps(SCHEMA, indent=2, ensure_ascii=False))
        return

    if args.cmd == "diff":
        print(diff(_load(args.a), _load(args.b)).texto())
        return

    p = _load(args.json)

    if args.cmd == "render":
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(render_html(p))
        print("HTML gravado em %s" % args.out)
        return

    if args.cmd == "pdf":
        tmp = os.path.splitext(args.out)[0] + ".html"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(render_html(p))
        gerar_pdf(tmp, args.out)
        print("PDF gravado em %s (HTML intermediario: %s)" % (args.out, tmp))
        return

    s = Saida()
    s.add("", "PROCESSO %s — %sa Analise" % (p.get("processo"), p.get("analise")))
    if args.cmd in ("check", "definidora"):
        definidora(p, s)
    if args.cmd in ("check", "tabela"):
        rota_tabela(p, s)
        div = next((o.get("divisao") for o in p.get("ocupacoes", []) if o.get("definidora")), None)
        if div:
            h, _q = altura_governante(p)
            ln = linha_conferida(div, coluna_altura(h))
            if ln:
                s.ok("Linha CONFERIDA: Tabela %s, %s, %s = %d medidas exigidas."
                     % (ln["tabela"], ln["divisao"], ln["coluna"], ln["total_medidas"]))
            else:
                s.pergunta("Linha NAO CONFERIDA para %s na coluna %s. Pedir a IMAGEM da tabela — "
                           "contagem nunca sai de extracao de PDF." % (div, coluna_altura(h)))
    if args.cmd in ("check", "normas"):
        confere_normas(p, s)
    if args.cmd in ("check", "travas"):
        travas(p, s)
    print(s.texto())


if __name__ == "__main__":
    main()
