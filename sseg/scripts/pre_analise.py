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


def _br(v, casas=2):
    try:
        return ("{:,.%df}" % casas).format(float(v)).replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "—"


def cadastro(api):
    """O cadastro do SOL em poucas linhas (17/10/2026): o que o Claude procurava no JSON com Grep a cada
    processo (o JSON vem numa linha só e o Grep devolve "[Omitted long matching line]"). Só o que o RT
    declarou; não confere nada."""
    import datetime
    c = api.get("caracteristica") or {}
    L = ["CADASTRO DO SOL (o que o RT declarou; %s):" % (api.get("numero") or "")]
    L.append("Área construída %s m² · protegida %s m² · subsolo %s m² · pavimentos: %s acima, %s abaixo do solo"
             % (_br(c.get("areaConstruida")), _br(c.get("areaProtegida")), _br(c.get("areaSubsolo")),
                c.get("pavimAcimaSolo"), c.get("pavimAbaixoSolo")))
    L.append("Altura descendente %s m · ascendente %s m · população total %s · pavimento de maior população %s (área %s m²)"
             % (_br(c.get("alturaDescendente")), _br(c.get("alturaAscendente")), c.get("populacaoTotal"),
                c.get("populacaoPavimMaior"), _br(c.get("areaMaiorPopulacao"))))
    L.append("Situação: %s%s · característica construtiva %s · depósito descoberto: %s"
             % ((c.get("edificacao") or "?").replace("_", " ").lower(),
                "" if c.get("regularizada") is None else " regularizada" if c.get("regularizada") else " não regularizada",
                c.get("caracteristicaConstrutiva"), "sim" if _sim(c.get("depositoDescoberto")) else "não"))
    L.append("Ocupações (a área de cada uma não está no cadastro: é da planta):")
    for o in c.get("ocupacoes") or []:
        cn = o.get("cnae") or {}
        L.append("  %s %s — %s (CNAE %s) · carga %s MJ/m² · risco %s%s"
                 % ((o.get("ocupacao") or "?").lower(), cn.get("divisao"), _espaco(cn.get("descricao") or ""), cn.get("cnae"),
                    o.get("cargaIncendio"), (o.get("grauRisco") or "?").lower(),
                    " · marcada como definidora pelo RT" if o.get("determinaSeguranca") else ""))
    riscos = api.get("especsRiscos") or []
    if riscos:
        L.append("Riscos específicos: " + "; ".join(
            ((r.get("risco") or {}).get("descricao") or "?") + (" (%s)" % r["outros"] if r.get("outros") else "")
            for r in riscos))
    ativos = [e for e in api.get("elemGraficos") or [] if e.get("situacao") == "ATIVO"]
    if ativos:
        def dia(ms):
            return datetime.datetime.fromtimestamp(ms / 1000).strftime("%d/%m/%Y") if ms else "?"
        L.append("Elementos gráficos ativos (desta análise): " + "; ".join(
            "%s %s (incluído %s)" % ((e.get("tipo") or "").replace("_", " ").lower(), e.get("descricao"), dia(e.get("dthInclusao")))
            for e in ativos))
    return "\n".join(L) + "\n"


def _dia(ms):
    import datetime
    return datetime.datetime.fromtimestamp(ms / 1000).strftime("%d/%m/%Y") if ms else "?"


def _ficha_comparar(api):
    """O que interessa comparar entre duas versões do cadastro."""
    c = api.get("caracteristica") or {}
    med = {((m.get("tipo") or {}).get("nome") or "?"): ((m.get("norma") or {}).get("nome") or "—")
           for m in (api.get("especSeguranca") or {}).get("medidas") or []}
    return {
        "Área construída (m²)": c.get("areaConstruida"), "Altura descendente (m)": c.get("alturaDescendente"),
        "Altura ascendente (m)": c.get("alturaAscendente"), "População total": c.get("populacaoTotal"),
        "Pavimento de maior população": c.get("populacaoPavimMaior"),
        "Pavimentos acima/abaixo": "%s/%s" % (c.get("pavimAcimaSolo"), c.get("pavimAbaixoSolo")),
        "Ocupações": "; ".join(sorted("%s %s" % ((o.get("ocupacao") or "").lower(), (o.get("cnae") or {}).get("divisao"))
                                      for o in c.get("ocupacoes") or [])),
        "Definidora marcada pelo RT": ", ".join(sorted((o.get("cnae") or {}).get("divisao") or "?" for o in c.get("ocupacoes") or []
                                                       if o.get("determinaSeguranca"))),
        "Riscos específicos": "; ".join(sorted(((r.get("risco") or {}).get("descricao") or "?") for r in api.get("especsRiscos") or [])),
        "_medidas": med,
    }


def secao_reanalise(api, anterior, marcos):
    """Reanálise (2.3.23, pedido do Átila): o escopo é a última CIA mais o que mudou. Mostra as plantas trocadas
    (o SOL guarda as inativadas, com o que foi notificado nelas) e, se o servidor guardou o JSON da análise
    anterior (anterior-api-<ID>.json), o que mudou no cadastro e no campo 4."""
    n = marcos.get("analise") or 0
    L = ["REANÁLISE (%sª análise): o escopo é a última CIA e o que mudou. As conferências do processo inteiro, mais "
         "abaixo, são para observação: achado fora dos itens da CIA vai em \"Observações\", sem virar exigência sozinho." % n,
         "", "== Plantas e documentos desta análise × anteriores (elementos gráficos do SOL) =="]
    els = api.get("elemGraficos") or []
    ativos = [e for e in els if e.get("situacao") == "ATIVO"]
    inativos = sorted([e for e in els if e.get("situacao") != "ATIVO"], key=lambda e: e.get("dthExclusao") or 0)
    ult = max([e.get("dthExclusao") or 0 for e in inativos] or [0])
    for e in ativos:
        novo = (e.get("dthInclusao") or 0) >= ult - 86400000 and ult
        L.append("  %s %s: %s (incluído %s)" % ("NOVO" if novo else "mantido", (e.get("tipo") or "").replace("_", " ").lower(),
                                                 e.get("descricao"), _dia(e.get("dthInclusao"))))
    for e in inativos:
        just = " | ".join(" ".join((j.get("justificativa") or "").split())[:160] for j in e.get("justificativas") or [])
        L.append("  substituído %s: %s (inativado %s)%s" % ((e.get("tipo") or "").replace("_", " ").lower(), e.get("descricao"),
                                                           _dia(e.get("dthExclusao")), (" — notificado: " + just) if just else ""))
    L += ["", "== O que mudou no cadastro e no campo 4 =="]
    if not anterior:
        L.append("  Sem o cadastro da análise anterior guardado (o servidor guarda a partir de 17/10/2026, quando o processo "
                 "volta à caixa): comparar pelos itens da CIA.")
    else:
        a, b = _ficha_comparar(anterior), _ficha_comparar(api)
        mud = ["  %s: %s → %s" % (k, a[k], b[k]) for k in b if not k.startswith("_") and a.get(k) != b[k]]
        ma, mb = a["_medidas"], b["_medidas"]
        mud += ["  campo 4, entrou: %s (%s)" % (m, mb[m]) for m in sorted(set(mb) - set(ma))]
        mud += ["  campo 4, saiu: %s (era %s) — conferir se a definidora mudou antes de notificar a ausência" % (m, ma[m])
                for m in sorted(set(ma) - set(mb))]
        mud += ["  campo 4, norma de %s: %s → %s" % (m, ma[m], mb[m]) for m in sorted(set(ma) & set(mb)) if ma[m] != mb[m]]
        L += mud or ["  Nada mudou no cadastro nem no campo 4 desde a análise anterior: a correção, se houve, está nas plantas."]
    return "\n".join(L) + "\n\n"


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
    anteriores = glob.glob(os.path.join(pasta, "anterior-api-*.json"))  # JSON da análise anterior (2.3.23)
    base = max([os.path.getmtime(a) for a in [api_arq, resumo_arq, cia_arq] + anteriores if os.path.exists(a)])
    if not forcar and os.path.exists(saida_txt) and os.path.getmtime(saida_txt) >= base:
        return "em-dia", "já feita"
    with open(api_arq, encoding="utf-8") as fh:
        api = json.load(fh)
    p = converter(api)
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
    if (marcos.get("analise") or 0) >= 2:  # reanálise: o que mudou e as plantas trocadas vêm antes de tudo
        ant = None
        if anteriores:
            try:
                with open(max(anteriores, key=os.path.getmtime), encoding="utf-8") as fh:
                    ant = json.load(fh)
            except (OSError, ValueError):
                pass
        cab += secao_reanalise(api, ant, marcos)
    else:
        cab += ("1ª ANÁLISE: conferência completa do processo (definidora, tabela, normas do campo 4, travas e "
                "o que só a planta responde).\n\n")
    with open(saida_txt, "w", encoding="utf-8") as fh:
        fh.write(cab + cadastro(api) + "\n" + r.stdout + (("\n[erro do check]\n" + r.stderr) if r.returncode else "") + secao_cia(cia_arq, marcos))
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
