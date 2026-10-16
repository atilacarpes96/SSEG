# -*- coding: utf-8 -*-
"""
gasto.py — tokens gastos nas conversas do Claude Code na pasta do SSEG (item 7 do PLANO.md).

Lê os registros que o próprio Claude Code grava no PC (~/.claude/projects/<pasta>/*.jsonl),
só da pasta do SSEG. Conta em TOKENS, não em US$ (o Claude Code não tem preço do Haiku 5.5).
Cada resposta aparece várias vezes no registro (uma por bloco): conta uma vez, pelo id.

  entrada   = tokens novos enviados (input + gravação de cache)
  cache     = tokens relidos do cache (bem mais baratos)
  saída     = tokens escritos pelo modelo (os mais caros)

Gasto por tipo de conversa (16/10/2026, controle interno, fora da janela): o chat anota em
%APPDATA%\\SSEG\\conversas.jsonl a sessão e o botão que a abriu (Analisar processo, Revisar CIA...).
Conversa aberta fora do programa (Claude Code direto, desenvolvimento) aparece como "fora do programa".
  python sseg/app/gasto.py [dias]
"""

import datetime
import glob
import json
import os
import re
from collections import defaultdict


def arquivo_conversas():
    return os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "SSEG", "conversas.jsonl")


def anotar_conversa(sessao, fluxo, codigo=None, arquivo=None):
    """Uma linha por sessão nova do chat. Falha calada: anotar gasto nunca derruba a conversa."""
    try:
        arquivo = arquivo or arquivo_conversas()
        os.makedirs(os.path.dirname(arquivo), exist_ok=True)
        with open(arquivo, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"sessao": sessao, "fluxo": fluxo.get("id"), "processo": codigo,
                                 "modelo": fluxo.get("modelo"), "esforco": fluxo.get("esforco"),
                                 "quando": datetime.datetime.now().astimezone().isoformat(timespec="seconds")},
                                ensure_ascii=False) + "\n")
    except Exception:
        pass


def tipos_das_sessoes(arquivo=None):
    tipos = {}
    try:
        with open(arquivo or arquivo_conversas(), encoding="utf-8") as fh:
            for linha in fh:
                try:
                    d = json.loads(linha)
                except ValueError:
                    continue
                tipos[d.get("sessao")] = d.get("fluxo") or "?"
    except OSError:
        pass
    return tipos


def por_tipo(regs, tipos):
    """[(tipo, soma, nº de conversas)], do que mais gastou para o que menos gastou."""
    grupos = defaultdict(list)
    for r in regs:
        grupos[tipos.get(r["sessao"], "fora do programa")].append(r)
    saida = [(t, _soma(v), len({r["sessao"] for r in v})) for t, v in grupos.items()]
    return sorted(saida, key=lambda x: -(x[1]["entrada"] + 5 * x[1]["saida"]))


def pastas_do_projeto(clone, base=None):
    base = base or os.path.join(os.path.expanduser("~"), ".claude", "projects")
    nome = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(clone))
    return [d for d in glob.glob(os.path.join(base, "*"))
            if os.path.basename(d).lower() == nome.lower() or os.path.basename(d).lower().startswith(nome.lower() + "--")]


def ler(clone, dias=30, base=None):
    limite = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=dias)
    vistos, regs = set(), []
    for pasta in pastas_do_projeto(clone, base):
        for arq in glob.glob(os.path.join(pasta, "**", "*.jsonl"), recursive=True):
            sub_arquivo = os.sep + "subagents" + os.sep in arq
            try:
                fh = open(arq, encoding="utf-8", errors="replace")
            except OSError:
                continue
            with fh:
                for linha in fh:
                    if '"usage"' not in linha:
                        continue
                    try:
                        d = json.loads(linha)
                    except ValueError:
                        continue
                    m = d.get("message") or {}
                    u = m.get("usage")
                    if d.get("type") != "assistant" or not u or m.get("id") in vistos or m.get("model") == "<synthetic>":
                        continue
                    try:
                        ts = datetime.datetime.fromisoformat(d.get("timestamp", "").replace("Z", "+00:00"))
                    except ValueError:
                        continue
                    if ts < limite:
                        continue
                    vistos.add(m.get("id"))
                    sub = bool(d.get("isSidechain")) or sub_arquivo
                    regs.append({
                        "quando": ts.astimezone(), "sessao": d.get("sessionId", "?"), "modelo": m.get("model", "?"),
                        "subagente": (d.get("agentType") or d.get("subagent_type") or "subagente") if sub else None,
                        "entrada": (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0),
                        "cache": u.get("cache_read_input_tokens") or 0, "saida": u.get("output_tokens") or 0,
                    })
    return regs


def _soma(regs):
    t = {"entrada": 0, "cache": 0, "saida": 0, "respostas": 0}
    for r in regs:
        for k in ("entrada", "cache", "saida"):
            t[k] += r[k]
        t["respostas"] += 1
    return t


def resumo(regs):
    hoje = datetime.datetime.now().astimezone().date()
    por = {"dia": defaultdict(list), "modelo": defaultdict(list), "sessao": defaultdict(list), "subagente": defaultdict(list)}
    for r in regs:
        por["dia"][r["quando"].date()].append(r)
        por["modelo"][r["modelo"]].append(r)
        por["sessao"][r["sessao"]].append(r)
        por["subagente"][r["subagente"] or "(conversa principal)"].append(r)
    semana = [r for r in regs if (hoje - r["quando"].date()).days < 7]
    return {
        "total": _soma(regs), "semana": _soma(semana), "hoje": _soma(por["dia"].get(hoje, [])),
        "dias": [(d, _soma(por["dia"][d])) for d in sorted(por["dia"], reverse=True)[:7]],
        "modelos": sorted(((m, _soma(v)) for m, v in por["modelo"].items()), key=lambda x: -x[1]["saida"]),
        "subagentes": sorted(((m, _soma(v)) for m, v in por["subagente"].items()), key=lambda x: -x[1]["saida"]),
        "sessoes": sorted(((s, _soma(v), min(r["quando"] for r in v)) for s, v in por["sessao"].items()),
                          key=lambda x: -(x[1]["entrada"] + x[1]["saida"]))[:10],
    }


def _k(n):
    return "%.1f mi" % (n / 1e6) if n >= 1e6 else ("%.0f mil" % (n / 1e3) if n >= 1e3 else str(n))


def texto(res, dias=30):
    if not res["total"]["respostas"]:
        return "Nenhuma conversa do Claude Code nesta pasta nos últimos %d dias." % dias
    L = []

    def linha(rot, t):
        L.append("%-26s %9s %9s %9s %6d" % (rot[:26], _k(t["entrada"]), _k(t["cache"]), _k(t["saida"]), t["respostas"]))
    L.append("%-26s %9s %9s %9s %6s" % ("", "entrada", "cache", "saída", "resp."))
    linha("Hoje", res["hoje"])
    linha("Últimos 7 dias", res["semana"])
    linha("Últimos %d dias" % dias, res["total"])
    L.append("\nPor dia")
    for d, t in res["dias"]:
        linha(d.strftime("%d/%m"), t)
    L.append("\nPor modelo")
    for m, t in res["modelos"]:
        linha(m, t)
    L.append("\nConversa principal × subagentes")
    for m, t in res["subagentes"]:
        linha(m, t)
    L.append("\nConversas que mais gastaram")
    for s, t, ini in res["sessoes"]:
        linha(ini.strftime("%d/%m %H:%M") + " " + s[:8], t)
    L.append("\nSaída é o que mais pesa no limite; cache relido é barato. Conversa longa reenvia o histórico a "
             "cada mensagem: uma conversa por processo.")
    return "\n".join(L)


def texto_por_tipo(regs, tipos):
    L = ["%-26s %9s %9s %9s %6s %6s" % ("tipo", "entrada", "cache", "saída", "resp.", "conv.")]
    for t, s, n in por_tipo(regs, tipos):
        L.append("%-26s %9s %9s %9s %6d %6d" % (t[:26], _k(s["entrada"]), _k(s["cache"]), _k(s["saida"]),
                                                s["respostas"], n))
    return "\n".join(L)


if __name__ == "__main__":
    import sys
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    clone = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print("Gasto por tipo de conversa, últimos %d dias (%s):" % (dias, arquivo_conversas()))
    print(texto_por_tipo(ler(clone, dias=dias), tipos_das_sessoes()))
