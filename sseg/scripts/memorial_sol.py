#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
memorial_sol.py — o "print do memorial": tudo o que a página do licenciamento no SOL mostra, num PDF (2.6.4).

Por quê: o RT corrige o projeto e o SOL passa a mostrar o memorial novo. Para a reanálise (e para o recurso) a
pasta precisa ter o memorial COMO ESTAVA naquela análise, com tudo: envolvidos, localização, características,
ocupações, áreas do memorial, medidas com a norma usada no dimensionamento, inviabilidade, compartimentação,
laudo, riscos específicos, elementos gráficos e o status de cada item. O "Guardar memorial" da 2.6.0 só baixava o
PDF que o RT anexou (que não traz nada disso) e o JSON. Pedido do Átila, 20/10/2026.

Fonte: o JSON do licenciamento (GET /licenciamentos/<ID>, o api-<ID>.json da pasta). Nada é lido da tela.
Script puro: não decide nada da análise. A seção "Dados a verificar" lista o que o analista confere na planta
(fixo) e os pontos que a pré-análise marcou (?? e !! do pre-analise.txt), sem concluir.

Arquivos, na pasta do processo (dentro da lista do enviar.py, sobem ao servidor e descem ao PC):
  memorial SOL <N>.pdf      o print, N = número da análise (marcos-resumo.json)
  memorial SOL <N>.txt      o mesmo em texto, para comparar análises e para o Claude ler sem abrir PDF
  licenciamento <N>.json    o JSON de onde o print saiu (a fonte), se ainda não houver o da análise N
Quem chama: sol_caixa.py (servidor) e caixa_pc.py (PC), quando o processo está na caixa e o print daquela análise
ainda não existe; sol_snapshot.py congelar (botão Guardar memorial), sempre de novo.

USO
  python3 sseg/scripts/memorial_sol.py <pasta do processo> [--api api-<ID>.json] [--forcar]
"""

import argparse
import datetime
import glob
import html
import json
import os
import re
import shutil
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

STATUS = {"APROVADO": "Aprovado", "REPROVADO": "Reprovado"}
INVIAB = {"NAO_POSSUI": "Não", "POSSUI": "Sim", "POSSUI_TOTAL": "Sim, total", "POSSUI_PARCIAL": "Sim, parcial",
          "TOTAL": "Sim, total", "PARCIAL": "Sim, parcial"}

# O que o analista confere na planta e no memorial (fixo; a pré-análise acrescenta os pontos do caso).
CONFERIR = [
    "Área total construída e área a proteger: somatório das áreas da planta (e do documento comprobatório, se existente).",
    "Área de cada ocupação e do memorial (áreas por densidade): o cadastro do SOL não traz a área por ocupação.",
    "Pavimentos acima e abaixo do solo, área do subsolo e uso do subsolo.",
    "Alturas descendente e ascendente: percurso do ocupante até a saída (RT 02/2014, item 4.20).",
    "População total e do pavimento de maior população, sem o pavimento de descarga (RT 02/2014, item 4.30).",
    "Característica construtiva declarada (X, Y ou Z) × o que o corte e o memorial mostram.",
    "Ocupações: atividade de cada ambiente, predominante × subsidiária, carga de incêndio e grau de risco; definidora.",
    "Norma citada em cada medida: vigente na data de protocolo e a que dimensiona aquela medida.",
    "Medidas exigidas pela tabela × medidas do campo 4; inviabilidade e compensatórias do laudo × campo 4 e planta.",
    "Riscos específicos declarados × o que a planta mostra (GLP, caldeira, vasos, inflamáveis…).",
    "Elementos gráficos: todas as plantas, cortes e implantação presentes e legíveis.",
]


def _ler(arq):
    try:
        with open(arq, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _txt(v):
    """Texto limpo de HTML (laudo) e de espaços."""
    if v is None:
        return ""
    s = re.sub(r"<\s*(br|/p|/li|/div)\s*/?>", "\n", str(v), flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", "", s)).replace("\xa0", " ")
    return "\n".join(" ".join(l.split()) for l in s.splitlines()).strip()


def _num(v, casas=2):
    if v in (None, ""):
        return "—"
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    s = ("{:,.%df}" % casas).format(f) if casas else "{:,.0f}".format(f)
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _sim(v):
    if v in (None, ""):
        return "—"
    if isinstance(v, bool):
        return "Sim" if v else "Não"
    return {"SIM": "Sim", "NAO": "Não", "NÃO": "Não", "TRUE": "Sim", "FALSE": "Não"}.get(str(v).upper(), str(v))


def _status(o):
    return STATUS.get(((o or {}).get("resultado") or {}).get("statusResultadoAtec"), "Analisar")


def _justificativas(o):
    o = o or {}
    lista = list(o.get("justificativas") or []) + list((o.get("resultado") or {}).get("justificativas") or [])
    return [j.get("justificativa") for j in lista if (j or {}).get("justificativa")]


def _data_ms(v):
    try:
        return datetime.datetime.fromtimestamp(int(v) / 1000).strftime("%d/%m/%Y")
    except (TypeError, ValueError, OSError):
        return str(v or "—")


def _doc(v):
    s = re.sub(r"\D", "", str(v or ""))
    if len(s) == 11:
        return "%s.%s.%s-%s" % (s[:3], s[3:6], s[6:9], s[9:])
    if len(s) == 14:
        return "%s.%s.%s/%s-%s" % (s[:2], s[2:5], s[5:8], s[8:12], s[12:])
    return str(v or "—")


def montar(api, n=None, protocolo=None, pontos=()):
    """Seções do print: [(título, [blocos])]; bloco = ("kv", [(rótulo, valor)]) | ("tab", cab, linhas) | ("txt", str)."""
    car = api.get("caracteristica") or {}
    esp = api.get("especSeguranca") or {}
    loc = api.get("localizacao") or {}
    env = api.get("envolvidos") or {}
    S = []

    S.append(("Identificação", [("kv", [
        ("Processo", api.get("numero")), ("Análise", "%sª" % n if n else "—"),
        ("Data de protocolo (Marcos)", protocolo or "—"), ("Tipo", api.get("tipo")), ("Fase", api.get("fase")),
        ("Situação no SOL", api.get("situacao")), ("Criado em", api.get("dataCriacao")),
        ("Isenção de taxa", _sim(api.get("isencao"))),
        ("Print gerado em", datetime.datetime.now().strftime("%d/%m/%Y %H:%M") + " (do JSON do licenciamento)")])]))

    linhas = []
    for rot, lst in (("RT", env.get("rts")), ("RU", env.get("rus")), ("Proprietário", env.get("proprietarios"))):
        for p in lst or []:
            proc = (p.get("procurador") or {}).get("nome")
            extra = p.get("tipoResponsabilidadeTecnica") or ""
            arqs = ", ".join(a.get("nomeArquivo") or "" for a in (p.get("arquivos") or []) if a.get("nomeArquivo"))
            linhas.append([rot, (p.get("nome") or "").strip(), _doc(p.get("cpf") or p.get("cpfCnpj")),
                           " · ".join(x for x in (extra, ("procurador: " + proc.strip()) if proc else "", arqs) if x),
                           " / ".join(x for x in (p.get("email"), p.get("telefone")) if x)])
    for e in env.get("estabelecimentos") or []:
        linhas.append(["Estabelecimento" + (" (%s)" % e.get("tipo").lower() if e.get("tipo") else ""),
                       e.get("razaoSocial") or "", _doc(e.get("cpfCnpj")), e.get("nomeFantasia") or "", ""])
    S.append(("Envolvidos", [("tab", ["Papel", "Nome", "CPF/CNPJ", "Detalhe", "Contato"], linhas)]))

    end = loc.get("enderecoLicenciamento") or {}
    S.append(("Localização", [("kv", [
        ("Endereço", ", ".join(str(x) for x in (end.get("logradouro"), end.get("numero"), loc.get("complemento")) if x)),
        ("Bairro", loc.get("bairro")), ("Cidade", "%s/%s" % (end.get("cidade") or loc.get("localidade") or "", end.get("estado") or "")),
        ("CEP", loc.get("cep")), ("Coordenadas", "%s, %s" % (loc.get("latitudeMapa"), loc.get("longitudeMapa"))),
        ("Isolamento de risco declarado", _sim(loc.get("isolamentoRisco"))),
        ("Arquivo do isolamento", (loc.get("arquivo") or {}).get("nomeArquivo") or "—")])]))

    m3, m5 = car.get("m3") or {}, car.get("m5") or {}
    kv = [("Edificação", car.get("edificacao")), ("Período de construção", car.get("periodoConstrucao")),
          ("Regularizada", _sim(car.get("regularizada"))),
          ("Documento comprobatório", (car.get("arquivo") or {}).get("nomeArquivo") or "—"),
          ("Área total construída", _num(car.get("areaConstruida")) + " m²"),
          ("Área a proteger", _num(car.get("areaProtegida")) + " m²"),
          ("Área do subsolo", _num(car.get("areaSubsolo")) + " m²"),
          ("Pavimentos acima do solo", car.get("pavimAcimaSolo")), ("Pavimentos abaixo do solo", car.get("pavimAbaixoSolo")),
          ("Altura descendente", _num(car.get("alturaDescendente")) + " m"),
          ("Altura ascendente", _num(car.get("alturaAscendente")) + " m"),
          ("População total", car.get("populacaoTotal")),
          ("Pavimento de maior população", "%s pessoas · %s m²" % (car.get("populacaoPavimMaior"), _num(car.get("areaMaiorPopulacao")))),
          ("Característica construtiva", car.get("caracteristicaConstrutiva")),
          ("Depósito descoberto de combustíveis", _sim(car.get("depositoDescoberto"))),
          ("Possui afastamento", _sim(car.get("possuiAfastamento"))),
          ("Separação horizontal entre áreas", _sim(car.get("separacaoHorizontalAreas"))),
          ("Separação vertical entre áreas", _sim(car.get("separacaoVerticalAreas"))),
          ("Tempo de resistência ao fogo", car.get("tempoResistenciaFogo") or "—")]
    kv += [("M-3: " + k, v) for k, v in m3.items() if v not in (None, "")]
    kv += [("M-5: " + k, v) for k, v in m5.items() if v not in (None, "")]
    blocos = [("kv", kv)]
    oc = []
    for o in car.get("ocupacoes") or []:
        c = o.get("cnae") or {}
        oc.append([(o.get("ocupacao") or "").capitalize(), c.get("divisao") or "", c.get("cnae") or "",
                   _txt(c.get("descricao")), _num(o.get("cargaIncendio"), 0), (o.get("grauRisco") or "").capitalize(),
                   "Sim" if o.get("determinaSeguranca") else "", _sim(o.get("subsolo")), _status(o)])
    blocos.append(("sub", "Ocupações (a definidora marcada é a do RT, não a que vale)"))
    blocos.append(("tab", ["Tipo", "Divisão", "CNAE", "Descrição", "Carga MJ/m²", "Risco", "Definidora (RT)", "Subsolo", "Status"], oc))
    am = []
    for a in car.get("areasMemorial") or []:
        d = a.get("densidade") or {}
        am.append([a.get("tpArea") or "", _txt(d.get("descricao")), _num(a.get("area")) + " m²", a.get("populacao")])
    if am:
        blocos.append(("sub", "Áreas do memorial (cálculo de população)"))
        blocos.append(("tab", ["Área", "Densidade", "Área", "População"], am))
    for rot, chave in (("Geral", "resultadoGeral"), ("Tipo de edificação", "resultadoTipoEdificacao"),
                       ("Isolamento de risco", "resultadoIsolamentoRisco")):
        if car.get(chave):
            blocos.append(("kv", [("Resultado — " + rot, _status({"resultado": car.get(chave)}))]))
            for t in _justificativas({"resultado": car.get(chave)}):
                blocos.append(("nota", "Notificação (%s): %s" % (rot, t)))
    S.append(("Características", blocos))

    med = []
    notas = []
    for m in esp.get("medidas") or []:
        nome = (m.get("tipo") or {}).get("nome") or "?"
        med.append([nome, (m.get("norma") or {}).get("nome") or "— (sem norma)",
                    INVIAB.get(m.get("inviabilidade"), m.get("inviabilidade") or "—"), _sim(m.get("compartimentacao")), _status(m)])
        notas += [("nota", "Notificação (%s): %s" % (nome, t)) for t in _justificativas(m)]
    blocos = [("tab", ["Medida", "Norma utilizada no dimensionamento", "Inviabilidade", "Compartimentação", "Status"], med)] + notas
    arts = ", ".join(a.get("nomeArquivo") or "" for a in esp.get("arts") or [] if a.get("nomeArquivo"))
    docs = ", ".join(a.get("nomeArquivo") or "" for a in esp.get("docs") or [] if a.get("nomeArquivo"))
    blocos.append(("kv", [("ART/RRT", arts or "—"), ("Outros documentos", docs or "—")]))
    if esp.get("resultadoOutrasMedidas"):
        blocos.append(("kv", [("Resultado — outras medidas", _status({"resultado": esp["resultadoOutrasMedidas"]}))]))
    laudo = _txt((esp.get("laudo") or {}).get("txtClob"))
    blocos.append(("sub", "Laudo de inviabilidade técnica"))
    blocos.append(("txt", laudo or "Sem laudo."))
    S.append(("Medidas de segurança", blocos))

    rs = []
    for r in api.get("especsRiscos") or []:
        tipo = r.get("risco") or r.get("tipo") or {}
        nome = tipo.get("descricao") or tipo.get("nome") if isinstance(tipo, dict) else tipo
        det = "; ".join("%s: %s" % (k, v) for k, v in r.items()
                        if k not in ("id", "risco", "tipo", "resultado", "justificativas", "arquivo") and v not in (None, "", [], {}))
        rs.append([nome or "?", det, _status(r)])
        for t in _justificativas(r):
            rs.append(["", "Notificação: " + t, ""])
    S.append(("Riscos específicos", [("tab", ["Risco", "Dados declarados", "Status"], rs) if rs else ("txt", "Nenhum declarado.")]))

    eg, inativos = [], []
    for e in api.get("elemGraficos") or []:
        linha = [e.get("tipo") or "", _txt(e.get("descricao")), (e.get("arquivo") or {}).get("nomeArquivo") or "",
                 _data_ms(e.get("dthInclusao")), _status(e)]
        if e.get("situacao") == "INATIVO":
            inativos.append(linha[:4] + [_data_ms(e.get("dthExclusao"))])
        else:
            eg.append(linha)
            for t in _justificativas(e):
                eg.append(["", "Notificação: " + t, "", "", ""])
    blocos = [("tab", ["Tipo", "Descrição", "Arquivo", "Incluído", "Status"], eg)]
    if inativos:
        blocos += [("sub", "Substituídos (inativos)"), ("tab", ["Tipo", "Descrição", "Arquivo", "Incluído", "Inativado"], inativos)]
    S.append(("Elementos gráficos", blocos))

    tx = [[b.get("tipo") or "", (b.get("boleto") or {}).get("situacao") or "", _num((b.get("boleto") or {}).get("valorNominal")),
           _data_ms((b.get("boleto") or {}).get("dataPagamento")) if (b.get("boleto") or {}).get("dataPagamento") else "—"]
          for b in api.get("boletosLicenciamento") or []]
    if tx:
        S.append(("Taxas", [("tab", ["Taxa", "Situação", "Valor R$", "Pago em"], tx)]))

    blocos = [("sub", "Conferir na planta e no memorial")] + [("item", c) for c in CONFERIR]
    if pontos:
        blocos += [("sub", "Pontos marcados pela pré-análise (script, sem conclusão)")] + [("item", p) for p in pontos]
    S.append(("Dados a verificar", blocos))
    return S


def _pontos(pasta):
    """Linhas ?? e !! do pre-analise.txt: o que o script não conseguiu fechar ou achou estranho."""
    try:
        with open(os.path.join(pasta, "pre-analise.txt"), encoding="utf-8") as fh:
            linhas = [l.strip()[2:].strip() for l in fh if l.strip()[:2] in ("??", "!!")]
    except OSError:
        return []
    # o resto da linha é instrução para o Claude (como fechar o ponto); no print fica só o ponto
    corte = re.compile(r"(\.|:|—)\s*(Contagem de medidas|So para|Quando|renderizar|sem pedir|O roteamento abaixo).*$")
    return [corte.sub(".", l).rstrip(" .") + "." for l in linhas]


def texto(S):
    out = []
    for tit, blocos in S:
        out += ["", "== %s ==" % tit.upper()]
        for b in blocos:
            if b[0] == "kv":
                out += ["%s: %s" % (k, "—" if v in (None, "") else v) for k, v in b[1]]
            elif b[0] == "tab":
                out.append(" | ".join(b[1]))
                out += [" | ".join("" if c is None else " ".join(str(c).split()) for c in l) for l in b[2]] or ["(nenhum)"]
            elif b[0] == "sub":
                out += ["", "-- %s --" % b[1]]
            elif b[0] == "item":
                out.append("[ ] " + b[1])
            else:
                out.append(b[1])
    return "\n".join(out).strip() + "\n"


CSS = """
@page { size: A4; margin: 12mm 11mm; }
body { font: 10.5px/1.35 Arial, Helvetica, sans-serif; color: #111; }
h1 { font-size: 16px; margin: 0 0 2px; } .sub0 { color: #555; margin: 0 0 8px; }
h2 { font-size: 12.5px; background: #b71c1c; color: #fff; padding: 3px 7px; margin: 12px 0 5px; break-after: avoid; }
h3 { font-size: 11px; margin: 8px 0 3px; color: #b71c1c; break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 2px 0 4px; } tr { break-inside: avoid; }
th, td { border: 1px solid #bbb; padding: 2px 5px; text-align: left; vertical-align: top; }
th { background: #f1f1f1; font-weight: 600; } table.kv td:first-child { width: 34%; color: #444; }
.st-Aprovado { color: #1b5e20; font-weight: 700; } .st-Reprovado { color: #b71c1c; font-weight: 700; } .st-Analisar { color: #8a6d00; font-weight: 700; }
.nota { border-left: 3px solid #b71c1c; padding: 2px 7px; margin: 3px 0; white-space: pre-wrap; background: #fff6f6; }
.txt { white-space: pre-wrap; border: 1px solid #ddd; padding: 6px; } ul { margin: 2px 0 4px 16px; padding: 0; } li { margin: 1px 0; }
"""


def _cel(v):
    s = html.escape("" if v is None else str(v))
    return '<span class="st-%s">%s</span>' % (s, s) if s in ("Aprovado", "Reprovado", "Analisar") else s


def render_html(S, api, n):
    h = ["<!doctype html><html lang='pt-BR'><meta charset='utf-8'><title>Memorial SOL</title><style>%s</style><body>" % CSS,
         "<h1>Memorial do SOL — %s%s</h1>" % (html.escape(str(api.get("numero") or "")), " · %sª análise" % n if n else ""),
         "<p class='sub0'>Tudo o que a página do licenciamento mostra, tirado do JSON do SOL no momento do print. "
         "Uso interno da SSeg/CBMRS.</p>"]
    for tit, blocos in S:
        h.append("<h2>%s</h2>" % html.escape(tit))
        itens = []
        for b in blocos:
            if b[0] != "item" and itens:
                h.append("<ul>%s</ul>" % "".join(itens))
                itens = []
            if b[0] == "kv":
                h.append("<table class='kv'>%s</table>" % "".join(
                    "<tr><td>%s</td><td>%s</td></tr>" % (html.escape(k), _cel("—" if v in (None, "") else v)) for k, v in b[1]))
            elif b[0] == "tab":
                corpo = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % _cel(c) for c in l) for l in b[2]) \
                    or "<tr><td colspan='%d'>(nenhum)</td></tr>" % len(b[1])
                h.append("<table><tr>%s</tr>%s</table>" % ("".join("<th>%s</th>" % html.escape(c) for c in b[1]), corpo))
            elif b[0] == "sub":
                h.append("<h3>%s</h3>" % html.escape(b[1]))
            elif b[0] == "nota":
                h.append("<div class='nota'>%s</div>" % html.escape(b[1]))
            elif b[0] == "item":
                itens.append("<li>☐ %s</li>" % html.escape(b[1]))
            else:
                h.append("<div class='txt'>%s</div>" % html.escape(b[1]))
        if itens:
            h.append("<ul style='list-style:none;margin-left:2px'>%s</ul>" % "".join(itens))
    return "\n".join(h) + "</body></html>"


def gerar(pasta, api_arq=None, forcar=False):
    """Grava memorial SOL <N>.pdf e .txt na pasta. Devolve a lista do que gravou ([] se já existia).
    Sem Chrome/Chromium para o PDF, grava só o .txt e levanta RuntimeError depois (quem chama vira aviso)."""
    if not api_arq:
        apis = sorted(glob.glob(os.path.join(pasta, "api-*.json")), key=os.path.getmtime)
        if not apis:
            raise RuntimeError("sem api-<ID>.json na pasta")
        api_arq = apis[-1]
    api = _ler(api_arq)
    if api.get("licenciamento") and not api.get("numero"):  # formato do `sseg.py receber`
        api = api["licenciamento"]
    if not api.get("numero"):
        raise RuntimeError("JSON do licenciamento sem número: %s" % os.path.basename(api_arq))
    resumo = _ler(os.path.join(pasta, "marcos-resumo.json"))
    n = resumo.get("analise")
    base = os.path.join(pasta, "memorial SOL %s" % (n or "sem-numero"))
    feitos = []
    # o JSON é a fonte (compara análises, o Claude lê, o print sai dele): congelado por análise, como o Guardar
    # memorial faz; o api-<ID>.json é trocado quando o processo volta à caixa. Nunca sobrescreve o que existe.
    lic = os.path.join(pasta, "licenciamento %s.json" % n) if n else ""
    if lic and not os.path.exists(lic):
        shutil.copyfile(api_arq, lic)
        feitos.append(lic)
    if not forcar and os.path.exists(base + ".pdf"):
        return feitos
    prot = resumo.get("protocolo")
    if prot:
        prot = "/".join(reversed(prot.split("-")))
    S = montar(api, n, prot, _pontos(pasta))
    with open(base + ".txt", "w", encoding="utf-8") as fh:
        fh.write("MEMORIAL DO SOL — %s%s\n" % (api.get("numero"), " · %sª análise" % n if n else "") + texto(S))
    feitos.append(base + ".txt")
    import sseg  # gerar_pdf: Chrome/Edge/Chromium sem janela
    tmp = tempfile.mkdtemp(prefix="tmp-memorial-", dir=pasta)  # na pasta: o Chromium snap do servidor não lê o /tmp
    try:
        h = os.path.join(tmp, "memorial.html")
        with open(h, "w", encoding="utf-8") as fh:
            fh.write(render_html(S, api, n))
        try:
            sseg.gerar_pdf(h, os.path.join(tmp, "memorial.pdf"))
        except SystemExit as e:  # o sseg.py avisa por SystemExit
            raise RuntimeError("PDF do memorial não gerado (%s); o .txt ficou na pasta" % str(e).splitlines()[0])
        shutil.move(os.path.join(tmp, "memorial.pdf"), base + ".pdf")
        feitos.append(base + ".pdf")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return feitos


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pasta")
    ap.add_argument("--api")
    ap.add_argument("--forcar", action="store_true")
    a = ap.parse_args()
    for f in gerar(a.pasta, a.api, a.forcar):
        print(f)
