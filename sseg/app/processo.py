# -*- coding: utf-8 -*-
"""
processo.py — monta a janela do processo (SSEG.exe 2.1): checklist do fluxo, medidas do SOL com
os itens do Anexo L e o registro analise.json. Só lê a pasta do processo; não chama o Claude
(abrir o processo não dispara nada — decisão do Átila, 12/10/2026).

Fontes únicas, no clone: sseg/workflow/checklist-analise.json (os 16 passos),
sseg/workflow/anexo-l.json (RT 05 Parte 1.1, Anexo L) e o JSON da API do SOL na pasta do processo.
"""

import glob
import html
import json
import os
import re
import sys
import unicodedata


def _registro(clone):
    """analise_registro.py mora em sseg/scripts (o sseg.py usa o mesmo); no .exe, vem empacotado."""
    try:
        import analise_registro
    except ImportError:
        sys.path.insert(0, os.path.join(clone, "sseg", "scripts"))
        import analise_registro
    return analise_registro


def _norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _ler_json(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return json.load(fh)


def json_do_sol(pasta):
    """O JSON da API com especSeguranca (api-<id>.json ou <N>.json), o mais novo."""
    candidatos = sorted(glob.glob(os.path.join(pasta, "*.json")), key=os.path.getmtime, reverse=True)
    for c in candidatos:
        if os.path.basename(c) == "analise.json" or os.path.basename(c).startswith("."):
            continue
        try:
            d = _ler_json(c)
        except (OSError, ValueError):
            continue
        if isinstance(d, dict) and isinstance(d.get("especSeguranca"), dict):
            return c, d
    return None, None


SOL = "https://solcbm.rs.gov.br/solcbm/adm/#/"


def links_sol(sol, id_analise=None):
    """Rotas das skills: licenciamento pelo id interno do SOL (o "id" do api-<id>.json, não o A000...).
    A análise técnica tem id próprio: sem ele no JSON, vai para a caixa (#/analise-tecnica)."""
    lic = sol.get("id") if sol and ("numero" in sol or "envolvidos" in sol) else None
    an = (sol.get("idAnaliseTecnica") if sol else None) or id_analise  # id_analise: da caixa do SOL (sol-caixa.json)
    return {"id": lic,
            "licenciamento": SOL + ("licenciamento/consulta/%s" % lic if lic else "licenciamento"),
            "analise": SOL + ("analise-tecnica/%s" % an if an else "analise-tecnica"),
            "analise_direta": bool(an)}


def texto_do_html(t):
    """O laudo vem do SOL em HTML (<p>, &nbsp;): vira texto corrido, um parágrafo por linha."""
    t = re.sub(r"(?i)<br\s*/?>|</p\s*>|</div\s*>|</li\s*>", "\n", t or "")
    t = re.sub(r"(?i)<li[^>]*>", "- ", t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t)).replace("\xa0", " ")
    linhas = [re.sub(r"[ \t]+", " ", l).strip() for l in t.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(linhas)).strip()


def itens_da_medida(nome, anexo):
    """Memorial sempre; os itens de planta da L.1 (coluna "A") quando a medida é da L.1."""
    n = _norm(nome)
    itens = [anexo["memorial"]]
    tabela = "L.2"
    for linha in sorted(anexo["l1"], key=lambda x: -len(x["chave"])):  # "hidrante urbano" antes de "hidrantes"
        if _norm(linha["chave"]) in n:
            itens += ["Planta: " + i for i in linha["planta"]]
            tabela = "L.1"
            break
    nota = next((t for k, t in anexo.get("notas", {}).items() if k in n), "")
    return tabela, itens, nota


def envolvidos(sol):
    """Itens da seção 1 que o analista pode reprovar, com o nome exato de sol_lancar.itens ("RT: FULANO ..."): ART/RRT vai
    no RT; procuração vai no RU ou no proprietário, que só têm o botão Analisar quando têm procurador (10/11/2026)."""
    env, out = (sol or {}).get("envolvidos") or {}, []
    for tipo, rotulo in (("rts", "RT"), ("rus", "RU"), ("proprietarios", "Proprietário")):
        for p in env.get(tipo) or []:
            if tipo == "rts" or p.get("procurador"):
                out.append("%s: %s" % (rotulo, (p.get("nome") or "").strip()))
    return out


def memorial_pela_pre(texto, medidas, rotulo):
    """Item "Memorial descritivo" que a pré-análise já conferiu (2.14.3, pedido do Átila): a medida está no campo 4 e a
    norma citada bate com o índice na data de protocolo ("OK <medida> — cita ... (bate com o indice)" do sseg.py check).
    Vira marca verde do script; o ✓/✗ do analista manda por cima. Fica de fora a medida com laudo de inviabilidade
    (o memorial dela inclui as compensatórias, que são do analista) e qualquer linha !!/??/XX."""
    sec = re.search(r"== Normas citadas no campo[^\n]*\n(.*?)(?:\n\s*\n|\Z)", texto, re.S)
    if not sec:
        return {}
    ok = {}
    for l in sec.group(1).splitlines():
        m = re.match(r"OK (.+?) — cita (.+?) \(bate com o indice\)", l)
        if m:
            ok[_norm(m.group(1))] = m.group(2)
    data = re.search(r"Data de protocolo: (\d{4}-\d\d-\d\d)", sec.group(1))
    if not data:   # sem a data, a versão da RT não está decidida (vigência por protocolo): não marca nada
        return {}
    out = {}
    for md in medidas:
        cit = ok.get(_norm(md["nome"]))
        if cit and md["inviabilidade"] == "NAO_POSSUI":
            out[md["nome"] + "|" + rotulo] = {
                "estado": "ok", "script": True,
                "nota": "Pré-análise (script): medida no campo 4, cita %s, que bate com o índice na data de protocolo %s." % (cit, data.group(1))}
    return out


def montar(clone, pasta):
    reg = _registro(clone)
    wf = os.path.join(clone, "sseg", "workflow")
    passos = _ler_json(os.path.join(wf, "checklist-analise.json"))["passos"]
    anexo = _ler_json(os.path.join(wf, "anexo-l.json"))
    arq, sol = json_do_sol(pasta)
    medidas, laudo, elementos = [], "", []
    if sol:
        # pranchas ativas, com o nome que o SOL mostra (o mesmo de sol_lancar.itens): a exigência aponta onde está o erro
        elementos = [" ".join(str(e.get("descricao") or "").split()) for e in sol.get("elemGraficos") or [] if e.get("situacao") == "ATIVO"]
        esp = sol["especSeguranca"]
        laudo = texto_do_html((esp.get("laudo") or {}).get("txtClob") or "")
        for m in esp.get("medidas") or []:  # na ordem do SOL
            nome = ((m.get("tipo") or {}).get("nome") or "").strip() or "(medida sem nome)"
            tabela, itens, nota = itens_da_medida(nome, anexo)
            inv = m.get("inviabilidade") or "NAO_POSSUI"
            if inv != "NAO_POSSUI":
                itens.append("Compensatórias do laudo representadas em planta")
            medidas.append({"nome": nome, "norma": re.sub(r"\s+", " ", ((m.get("norma") or {}).get("nome") or "")).strip(),
                            "inviabilidade": inv, "tabela": tabela, "itens": itens, "nota": nota})
    arquivos = sorted(os.listdir(pasta)) if os.path.isdir(pasta) else []
    try:
        sc = _ler_json(os.path.join(pasta, "sol-caixa.json"))
    except (OSError, ValueError):
        sc = {}
    # Passos que um script já fez (2.3.8): marcados sozinhos, com a origem. O analista não refaz.
    auto, pre, auto_itens = {}, None, {}
    if arq:
        auto["3"] = "JSON do SOL na pasta (%s)" % os.path.basename(arq)
    pa = os.path.join(pasta, "pre-analise.txt")
    if os.path.exists(pa):
        with open(pa, encoding="utf-8") as fh:
            texto = fh.read()
        velha = bool(arq) and os.path.getmtime(pa) < os.path.getmtime(arq)
        pre = {"texto": texto, "velha": velha, "data": int(os.path.getmtime(pa)),
               "marcas": [l for l in texto.splitlines() if l.startswith(("XX", "!!", "??"))]}
        if not velha:
            auto["4"] = "pré-análise documental (script, sem Claude): pre-analise.txt"
            auto_itens = memorial_pela_pre(texto, medidas, anexo["memorial"])
        # 2.13.8 (pedido do Átila): resumo dos scripts e da IA local (documentos, camadas, palpites), feito antes de
        # abrir o processo; vai ao chat junto com a pré-análise no passo 2
        ri = os.path.join(pasta, "resumo-ia.md")
        if os.path.exists(ri):
            with open(ri, encoding="utf-8") as fh:
                pre["resumo_ia"] = fh.read()
    return {"auto": auto, "auto_itens": auto_itens, "pre_analise": pre,"codigo": os.path.basename(os.path.normpath(pasta)), "pasta": pasta, "json_sol": arq and os.path.basename(arq),
            "passos": passos, "medidas": medidas, "elementos": elementos, "envolvidos": envolvidos(sol), "laudo": laudo, "compensatoria": anexo.get("compensatoria", ""),
            "cias": [a for a in arquivos if re.match(r"CIA \d+", a)], "analise": reg.ler(pasta), "sol": links_sol(sol, sc.get("id_analise"))}
