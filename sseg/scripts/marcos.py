#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marcos.py — resumo da aba Marcos do SOL, sem modelo (zero token). SSEG.exe 2.3.13.

Fonte: GET /solcbm/api/v1/adm/licenciamentos/<ID>/marcos (achado em 16/10/2026 no código da página do
SOL, serviço buscaMarcosLicenciamentoPor). Devolve uma lista, a mais nova primeiro, com id, dthMarco
(ms), descricao, visibilidade, arquivo {id, nomeArquivo}, nomeResponsavel, textoComplementar.
O sol_caixa.py baixa para <pasta do processo>/marcos.json; este script grava marcos-resumo.json:

  - protocolo: data de "Número do licenciamento gerado" (decide a versão das RTs; antes o check pedia);
  - analise: nº da análise atual = quantas "Distribuição de análise técnica" houve;
  - analises: cada "Conclusão de análise técnica - CA/CIA", com o PDF e a homologação que veio depois;
  - inviabilidade: cada conclusão de análise de inviabilidade, com o PDF;
  - recursos: todo marco que fala em recurso (o processo TEVE recurso, aberto ou não);
  - novos: descrições que este script ainda não conhece.

GATILHO: recurso e descrição nova ainda não têm formato conhecido (16/10/2026 nenhum processo com
recurso tinha passado por aqui). Quando aparecerem, o resumo marca "gatilho", o sol_caixa.py avisa
e põe um cartão no Quadro da seção, para alguém olhar o marco real e ensinar este script o que fazer
(ex.: deferido/indeferido). CT não aparece nos Marcos: continua vindo do ct.json.

USO
  python3 sseg/scripts/marcos.py --pasta <pasta do processo>     # resume o marcos.json da pasta
"""

import argparse
import datetime
import json
import os
import sys

ARQUIVO, RESUMO = "marcos.json", "marcos-resumo.json"
# (16/10/2026, ensinado com A00029172AA001, A00047947AA001 e A00016321AB001) o resultado do recurso NÃO
# está nos Marcos: vem de GET /licenciamento-historico/<ID> → historicoRecurso[] {data (ms), situacao,
# statusRecurso (INDEFERIDO, DEFERIDO_TOTAL, ...), instancia, tipoRecurso, documento {id} = PDF da decisão,
# arquivoCiaCiv {id} = a CIA contestada}. A consulta técnica (CT) vem de GET /facts/facts-licenciamento/<ID>
# → [{id, dthStatus "dd/mm/aaaa", status}]. O sol_caixa.py grava os dois ao lado do marcos.json.
HISTORICO, FACTS = "historico.json", "facts.json"

# o que já se sabe ler (descrições vistas no A00046788AA001 em 16/10/2026)
CONHECIDOS = {
    "Criação de rascunho de licenciamento", "Aceite de termo de responsabilidade",
    "Finalização dos aceites de termo de responsabilidade da etapa de análise",
    "Emissão de boleto de taxa de análise", "Liquidação de taxa de análise", "Número do licenciamento gerado",
    "Encaminhamento para análise de Inviabilidade Técnica", "Encaminhamento para análise técnica",
    "Distribuição de análise técnica", "Editando licenciamento em CIA", "Ciência de documento de CIA",
    "Ciência de documento de CIA de Inviabilidade Técnica",
    "Ciência de documento de Deferimento de Medidas Compensatórias",
    # vistos nos 3 processos com recurso: o FACT é a CT (detalhe em facts.json); a revisão de endereço é só registro
    "Vinculação de FACT a um licenciamento", "Solicitação de revisão de endereço",
    "Análise de revisão de endereço - Reprovado", "Análise de revisão de endereço - Aprovado",
}
RECURSO_STATUS = {"INDEFERIDO": "indeferido", "DEFERIDO_TOTAL": "deferido", "DEFERIDO_PARCIAL": "deferido em parte"}
RECURSO_TIPO = {"CORRECAO_DE_ANALISE": "correção de análise"}
CONCLUSAO = "Conclusão de análise técnica - "
HOMOLOGACAO = "Homologação de análise técnica - "
INVIAB = "Conclusão de análise de inviabilidade técnica - "


def _data(ms):
    return datetime.datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d") if ms else ""


def _arquivo(m):
    a = m.get("arquivo") or {}
    return a.get("id")


def resumir(marcos):
    ms = sorted(marcos or [], key=lambda m: m.get("dthMarco") or 0)  # do mais velho ao mais novo
    r = {"protocolo": "", "analise": 0, "analises": [], "inviabilidade": [], "recursos": [], "novos": []}
    for m in ms:
        d, desc = _data(m.get("dthMarco")), (m.get("descricao") or "").strip()
        if desc == "Número do licenciamento gerado" and not r["protocolo"]:
            r["protocolo"] = d
        elif desc == "Distribuição de análise técnica":
            r["analise"] += 1
        elif desc.startswith(CONCLUSAO):
            r["analises"].append({"data": d, "resultado": desc[len(CONCLUSAO):], "arquivo": _arquivo(m),
                                  "publico": m.get("visibilidade") == "PUBLICO",
                                  "responsavel": m.get("nomeResponsavel") or "", "homologacao": ""})
        elif desc.startswith(HOMOLOGACAO):
            if r["analises"] and not r["analises"][-1]["homologacao"]:
                r["analises"][-1]["homologacao"] = desc[len(HOMOLOGACAO):]
        elif desc.startswith(INVIAB):
            r["inviabilidade"].append({"data": d, "resultado": desc[len(INVIAB):], "arquivo": _arquivo(m)})
        if "recurso" in desc.lower():
            r["recursos"].append({"data": d, "descricao": desc, "arquivo": _arquivo(m),
                                  "texto": m.get("textoComplementar") or ""})
        elif not (desc in CONHECIDOS or desc.startswith((CONCLUSAO, HOMOLOGACAO, INVIAB))):
            if desc not in [n["descricao"] for n in r["novos"]]:
                r["novos"].append({"data": d, "descricao": desc})
    cias = [a for a in r["analises"] if a["resultado"] == "CIA" and a["arquivo"]]
    r["ultima_cia"] = cias[-1] if cias else None
    r["gatilho"] = bool(r["recursos"] or r["novos"])
    return r


def com_historico(r, historico, facts):
    """Recursos com o resultado (licenciamento-historico) e CTs (facts). Com o histórico lido, recurso deixa de
    ser gatilho: o script já sabe dizer como terminou. Sem ele, fica o que os Marcos dizem e o gatilho."""
    if isinstance(historico, dict):
        rec = []
        for x in historico.get("historicoRecurso") or []:
            st = x.get("statusRecurso") or ""
            tipo = x.get("tipoRecurso") or ""
            rec.append({"data": _data(x.get("data")), "instancia": x.get("instancia"),
                        "tipo": RECURSO_TIPO.get(tipo, tipo.replace("_", " ").lower()),
                        "status": st, "resultado": RECURSO_STATUS.get(st, st.lower().replace("_", " ")),
                        "situacao": x.get("situacao") or "", "pdf": (x.get("documento") or {}).get("id"),
                        "cia_contestada": (x.get("arquivoCiaCiv") or {}).get("id"), "ciencia": x.get("ciencia")})
        r["recursos_marcos"] = len(r["recursos"])
        r["recursos"] = sorted(rec, key=lambda x: x["data"])
        conhecidos = set(RECURSO_STATUS) | {""}
        r["gatilho"] = bool(r["novos"] or any(x["status"] not in conhecidos for x in r["recursos"]))
    if isinstance(facts, list):
        def iso(s):
            p = (s or "").split("/")
            return "-".join(reversed(p)) if len(p) == 3 else ""
        r["facts"] = [{"id": f.get("id"), "data": iso(f.get("dthStatus")), "status": f.get("status") or ""} for f in facts]
    return r


def resumir_pasta(pasta):
    """Lê marcos.json (e historico.json/facts.json, se houver) da pasta e grava marcos-resumo.json.
    Devolve o resumo (ou None sem marcos)."""
    try:
        with open(os.path.join(pasta, ARQUIVO), encoding="utf-8") as fh:
            marcos = json.load(fh)
    except (OSError, ValueError):
        return None

    def ler(nome):
        try:
            with open(os.path.join(pasta, nome), encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return None
    r = com_historico(resumir(marcos), ler(HISTORICO), ler(FACTS))
    # só regrava quando o resumo muda: a pré-analise refaz quando o resumo é mais novo que ela
    try:
        with open(os.path.join(pasta, RESUMO), encoding="utf-8") as fh:
            antes = json.load(fh)
        antes.pop("lido_em", None)
    except (OSError, ValueError):
        antes = None
    if antes != r:
        r["lido_em"] = datetime.date.today().isoformat()
        with open(os.path.join(pasta, RESUMO), "w", encoding="utf-8") as fh:
            json.dump(r, fh, ensure_ascii=False, indent=1)
    return r


def texto(r):
    br = lambda s: "/".join(reversed(s.split("-"))) if s else "?"  # noqa: E731
    L = ["Protocolo: %s · %dª análise" % (br(r["protocolo"]), r["analise"] or 1)]
    for a in r["analises"]:
        L.append("  %s %s%s%s" % (br(a["data"]), a["resultado"], " (PDF %s)" % a["arquivo"] if a["arquivo"] else "",
                                  " → homologação: " + a["homologacao"] if a["homologacao"] else ""))
    for a in r["inviabilidade"]:
        L.append("  %s inviabilidade: %s" % (br(a["data"]), a["resultado"]))
    for a in r["recursos"]:
        if "status" in a:
            L.append("  !! RECURSO %s (%sª instância, %s): %s%s" % (br(a["data"]), a["instancia"] or "?", a["tipo"],
                                                                  a["resultado"].upper(), " · CIA contestada: PDF %s" % a["cia_contestada"] if a["cia_contestada"] else ""))
        else:
            L.append("  !! RECURSO %s: %s" % (br(a["data"]), a["descricao"]))
    for f in r.get("facts") or []:
        L.append("  CT (FACT %s) %s: %s" % (f["id"], br(f["data"]), f["status"].replace("_", " ").lower()))
    for a in r["novos"]:
        L.append("  ?? marco que o script não conhece: %s (%s)" % (a["descricao"], br(a["data"])))
    return "\n".join(L)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pasta", required=True, help="pasta do processo, com o marcos.json")
    a = ap.parse_args()
    r = resumir_pasta(a.pasta)
    print(texto(r) if r else "sem %s em %s" % (ARQUIVO, a.pasta))
