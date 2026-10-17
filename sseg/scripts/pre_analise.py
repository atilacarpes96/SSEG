#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pre_analise.py — pré-análise documental, sem modelo (zero token).

Para cada processo com o JSON do SOL na pasta (api-<ID>.json, gravado pelo sol_caixa.py):
  1. converte para o formato do `sseg.py check` (o mesmo de `sseg.py schema`) → pre-analise.json;
  2. roda o `check` (definidora, rota da tabela, normas do campo 4, travas) → pre-analise.txt.
A conversa da análise começa lendo o pre-analise.txt em vez de refazer essa leitura.

O QUE NÃO FAZ
-------------
  - Não decide nada: é o `check` de sempre, e o que ele marca com ?? continua sendo do analista.
  - Data de protocolo da 1ª análise: não está no JSON do licenciamento (fica na aba Marcos) e
    decide a versão das RTs. Fica vazia, e o check pede (trava de vigência por protocolo).
  - Laudo de inviabilidade: marca "presente", mas não separa as compensatórias (ler o laudo é do
    analista); a lista vai vazia.
  - Não sobrescreve pre-analise.* mais novo que o api-<ID>.json (use --forcar).

USO
---
  python3 sseg/scripts/pre_analise.py                 # todos os processos da caixa (.caixa/caixa.json)
  python3 sseg/scripts/pre_analise.py A00024749AA002  # só estes
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PROCESSOS = os.path.normpath(os.path.join(AQUI, "..", "processos"))
SSEG = os.path.join(AQUI, "sseg.py")

_INVIAB = {"NAO_POSSUI": "Nao", "POSSUI_TOTAL": "Total", "POSSUI_PARCIAL": "Parcial"}


def _espaco(s):
    return re.sub(r"\s+", " ", s or "").strip()


def _sim(v):
    return v is True or str(v).upper() in ("SIM", "TRUE")


def converter(api):
    """JSON do SOL (GET /licenciamentos/<ID>) → formato do `sseg.py check`. Só copia campos."""
    c = api.get("caracteristica") or {}
    esp = api.get("especSeguranca") or {}
    ed = (c.get("edificacao") or "").upper()
    if ed == "EXISTENTE":
        situacao = "existente regularizada" if c.get("regularizada") else "existente nao regularizada"
    elif ed:
        situacao = "a construir"  # NOVA / A_CONSTRUIR: o SOL só tem os dois lados
    else:
        situacao = ""
    ocupacoes = []
    for o in c.get("ocupacoes") or []:
        cnae = o.get("cnae") or {}
        ocupacoes.append({
            "divisao": cnae.get("divisao") or "",
            "descricao": _espaco(cnae.get("descricao")),
            "cnae": cnae.get("cnae") or "",
            "area": 0,  # o SOL não dá área por ocupação
            "carga_incendio": o.get("cargaIncendio"),
            "grau_risco": o.get("grauRisco"),
            "predominante": (o.get("ocupacao") or "").upper() == "PREDOMINANTE",
            "subsolo": _sim(o.get("subsolo")),
            "definidora": bool(o.get("determinaSeguranca")),  # o que o RT marcou, não o que vale
        })
    medidas = []
    for m in esp.get("medidas") or []:
        medidas.append({
            "medida": _espaco((m.get("tipo") or {}).get("nome")),
            "norma": _espaco((m.get("norma") or {}).get("nome")),
            "inviabilidade": _INVIAB.get(m.get("inviabilidade"), m.get("inviabilidade") or "Nao"),
            "compartimentacao": "Sim" if m.get("compartimentacao") else "Nao",
            "status": "Analisar",
        })
    laudo = (esp.get("laudo") or {}).get("txtClob") or ""
    return {
        "processo": api.get("numero"),
        "analise": "?",
        "data_protocolo": None,
        "situacao_existencia": situacao,
        "periodo_construcao": c.get("periodoConstrucao"),
        "caracteristica_construtiva": c.get("caracteristicaConstrutiva"),
        "area_total_construida": c.get("areaConstruida"),
        "area_a_proteger": c.get("areaProtegida"),
        "pavimentos": {"acima": c.get("pavimAcimaSolo") or 0, "subsolo": c.get("pavimAbaixoSolo") or 0},
        "area_subsolo": c.get("areaSubsolo"),
        "altura_descendente": c.get("alturaDescendente"),
        "altura_ascendente": c.get("alturaAscendente"),
        "populacao_total": c.get("populacaoTotal"),
        "pavimento_maior_populacao": {"area": c.get("areaMaiorPopulacao"), "populacao": c.get("populacaoPavimMaior")},
        "ocupacoes": ocupacoes,
        "medidas": medidas,
        "riscos_especificos": [{"risco": _espaco(str((r.get("tipo") or {}).get("nome") or r.get("tipo") or "")),
                                "detalhe": "", "status": "Analisar"} for r in api.get("especsRiscos") or []],
        "elementos_graficos": [{"nome": _espaco(e.get("descricao")), "tipo": e.get("tipo"), "status": "Analisar"}
                               for e in api.get("elemGraficos") or [] if e.get("situacao") != "INATIVO"],
        "demais_inconformidades": [],
        "laudo_inviabilidade": {"presente": bool(_espaco(re.sub(r"<[^>]+>", " ", laudo))),
                                "medidas_compensatorias": []},
    }


INICIO_CIA = "apresentou as seguintes inconformidades"  # frase fixa do PDF do SOL antes dos apontamentos
RODAPE_CIA = re.compile(r"^\s*CBMRS \d\d/\d\d/\d{4} [\d:]+\s+Pagina \d+ de \d+\s*$")


def secao_cia(arq, marcos):
    """Última CIA para o fim do pre-analise.txt. Só o texto: comparar (passo 11) é do analista e do Claude."""
    tem_cia = any(a.get("resultado") == "CIA" for a in marcos.get("analises") or [])
    if not os.path.exists(arq):
        return "\nÚLTIMA CIA: anterior ainda não baixada (sol_caixa.py).\n" if tem_cia else ""
    with open(arq, encoding="utf-8", errors="replace") as fh:
        texto = fh.read()
    m = re.search(INICIO_CIA + r"[^:]*:", texto)  # a frase quebra linha: vai até o "aplicáveis:"
    i = m.end() if m else -1
    if i >= 0:  # corta cabeçalho, identificação, ocupações e laudo (já estão no JSON do SOL)
        texto = texto[i:]
    linhas = [l.rstrip() for l in texto.replace("\f", "\n").splitlines() if not RODAPE_CIA.match(l)]
    texto = re.sub(r"\n{3,}", "\n\n", "\n".join(linhas)).strip()
    return "\n\nÚLTIMA CIA (texto do PDF do SOL, cia-ultima.txt%s):\n%s\n" % (
        "" if i >= 0 else "; texto inteiro, início dos apontamentos não achado", texto)


def pre_analisar(codigo, forcar=False):
    """(situação, texto curto). Grava pre-analise.json e pre-analise.txt na pasta do processo."""
    pasta = os.path.join(PROCESSOS, codigo)
    apis = sorted(glob.glob(os.path.join(pasta, "api-*.json")), key=os.path.getmtime)
    if not apis:
        return "sem-json", "sem api-<ID>.json na pasta (o sol_caixa.py ainda não baixou)"
    api_arq = apis[-1]
    saida_json = os.path.join(pasta, "pre-analise.json")
    saida_txt = os.path.join(pasta, "pre-analise.txt")
    resumo_arq = os.path.join(pasta, "marcos-resumo.json")
    cia_arq = os.path.join(pasta, "cia-ultima.txt")  # o sol_caixa.py baixa: refaz quando chega CIA nova
    base = max([os.path.getmtime(a) for a in (api_arq, resumo_arq, cia_arq) if os.path.exists(a)])
    if not forcar and os.path.exists(saida_txt) and os.path.getmtime(saida_txt) >= base:
        return "em-dia", "já feita"
    with open(api_arq, encoding="utf-8") as fh:
        p = converter(json.load(fh))
    marcos = {}
    if os.path.exists(resumo_arq):  # Marcos (2.3.13): protocolo e nº da análise saem dos marcos do SOL
        try:
            with open(resumo_arq, encoding="utf-8") as fh:
                marcos = json.load(fh)
        except (OSError, ValueError):
            pass
    if marcos.get("protocolo"):
        p["data_protocolo"] = marcos["protocolo"]
    if marcos.get("analise"):
        p["analise"] = marcos["analise"]
    with open(saida_json, "w", encoding="utf-8") as fh:
        json.dump(p, fh, ensure_ascii=False, indent=1)
    r = subprocess.run([sys.executable, SSEG, "check", "--json", saida_json], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env={**os.environ, "PYTHONUTF8": "1"})
    if marcos.get("protocolo"):
        import marcos as mc
        linha_marcos = "MARCOS DO SOL (marcos.py):\n" + mc.texto(marcos) + "\n"
    else:
        linha_marcos = "Data de protocolo da 1ª análise: sem os Marcos na pasta — conferir na aba Marcos.\n"
    cab = ("PRÉ-ANÁLISE DOCUMENTAL (script, sem Claude) · %s · de %s\n%s"
           "Definidora abaixo = a que o RT marcou no SOL (determinaSeguranca), não a que vale.\n\n"
           % (codigo, os.path.basename(api_arq), linha_marcos))
    with open(saida_txt, "w", encoding="utf-8") as fh:
        fh.write(cab + r.stdout + (("\n[erro do check]\n" + r.stderr) if r.returncode else "") + secao_cia(cia_arq, marcos))
    marcas = sum(1 for l in r.stdout.splitlines() if l.startswith(("!!", "??", "XX")))
    return ("feita" if not r.returncode else "erro"), "%d ponto(s) marcados" % marcas


def da_caixa():
    try:
        with open(os.path.join(PROCESSOS, ".caixa", "caixa.json"), encoding="utf-8") as fh:
            return [i["codigo"] for i in json.load(fh)["itens"] if i.get("codigo")]
    except (OSError, ValueError, KeyError):
        return []


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("codigos", nargs="*", help="processos (padrão: os da caixa)")
    ap.add_argument("--forcar", action="store_true")
    a = ap.parse_args()
    cods = a.codigos or da_caixa()
    if not cods:
        print("Nenhum processo: caixa vazia ou ainda não lida (sol_caixa.py).")
    for c in cods:
        sit, txt = pre_analisar(c, a.forcar)
        print("%-16s %-9s %s" % (c, sit, txt))
