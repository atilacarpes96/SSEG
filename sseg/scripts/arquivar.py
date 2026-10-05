#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arquivar.py — "atualizar a pasta" sem o modelo datilografar arquivo.

O QUE FAZ
---------
Hoje, ao arquivar, o modelo reescreve o <N>.json com os status finais e digita o
"CIA <N> textos.json" com o texto de cada caixa Especificar. É documento longo saindo como
texto de resposta (o tipo de token mais caro) e o JSON da API passando pela conversa.

Aqui isso vira trabalho de disco:
  1. `receber` sobe um servidor local de uma requisição só; a página do SOL (já logada) manda
     o JSON da API direto para ele com `fetch`. O JSON nunca passa pela conversa.
  2. `arquivar` lê esse JSON e o registro de trabalho da análise (<N>.json montado no passo 2
     da skill, com o que só o analista decide: definidora, data de protocolo, alturas...),
       - atualiza os STATUS (medidas, riscos, elementos gráficos) a partir da API;
       - grava "CIA <N> textos.json" com o texto exato de cada caixa, lido da API;
       - gera <N>.pdf (render do sseg.py);
       - grava tudo na pasta do processo com os nomes do padrão e imprime um resumo curto.

O QUE NÃO FAZ
-------------
  - Não decide status: copia o que está gravado no SOL.
  - Não inventa item: o que está na API e não casa com o registro de trabalho sai no resumo
    como "sem par", para o analista olhar. Nada é descartado em silêncio.
  - Não sobrescreve arquivo da pasta sem --forcar.

USO (no PC, pelo device_bash)
---
  python sseg.py receber  --saida <pasta temporária>          # espera o POST e grava api-<ID>.json
  python sseg.py arquivar --api api-<ID>.json --trabalho <N>.json --pasta "<print ppci>\\<processo>"
"""

import http.server
import json
import os
import shutil
import tempfile
import time

import sseg

STATUS = {"APROVADO": "Aprovado", "REPROVADO": "Reprovado"}


def _status(o):
    return STATUS.get(((o or {}).get("resultado") or {}).get("statusResultadoAtec"), "Analisar")


def _justificativas(o):
    """Concatena as duas listas: elemGraficos[].justificativas vem vazia e as reais ficam em
    .resultado.justificativas (armadilha 3 do sol-cbmrs-navegador)."""
    o = o or {}
    lista = list(o.get("justificativas") or []) + list((o.get("resultado") or {}).get("justificativas") or [])
    return [j.get("justificativa") for j in lista if (j or {}).get("justificativa")]


# ------------------------------------------------------------------------------- receber

def receber(saida, porta=8765):
    """Servidor de uma requisição: grava o corpo do POST e encerra.

    Responde ao preflight de CORS e de Private Network Access, que o Chrome exige para uma
    página https falar com 127.0.0.1."""
    os.makedirs(saida, exist_ok=True)
    resultado = {}

    class H(http.server.BaseHTTPRequestHandler):
        def _cors(self):
            self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin") or "*")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Private-Network", "true")

        def do_OPTIONS(self):
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_POST(self):
            corpo = self.rfile.read(int(self.headers.get("Content-Length") or 0))
            try:
                d = json.loads(corpo.decode("utf-8"))
                ident = d.get("id") or d.get("idAnaliseTecnica") or "sem-id"
                caminho = os.path.join(saida, "api-%s.json" % ident)
                with open(caminho, "w", encoding="utf-8") as fh:
                    json.dump(d, fh, ensure_ascii=False)
                resultado["arquivo"] = caminho
                self.send_response(200)
            except ValueError as e:
                resultado["erro"] = "corpo não é JSON: %s" % e
                self.send_response(400)
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps(resultado, ensure_ascii=False).encode("utf-8"))

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", porta), H)
    srv.timeout = 5
    print("esperando o SOL em http://127.0.0.1:%d (até 5 min)..." % porta, flush=True)
    limite = time.time() + 300
    while not resultado and time.time() < limite:
        srv.handle_request()   # preflight (OPTIONS) e POST chegam em voltas separadas
    srv.server_close()
    if resultado.get("arquivo"):
        print("gravado: %s" % resultado["arquivo"])
    else:
        print("nada recebido%s" % (": " + resultado["erro"] if resultado.get("erro") else ""))
    return resultado.get("arquivo")


# ------------------------------------------------------------------------------ arquivar

def _casar(lista, chave, nome):
    alvo = sseg._norm(nome)
    for x in lista:
        if sseg._norm(x.get(chave)) == alvo:
            return x
    return None


def montar(api, trabalho):
    """Devolve (registro atualizado, textos, avisos). Não grava nada."""
    L = api["licenciamento"]
    p = json.loads(json.dumps(trabalho))
    avisos, textos = [], []

    if api.get("numeroAnalise"):
        if p.get("analise") and int(p["analise"]) != int(api["numeroAnalise"]):
            avisos.append("registro de trabalho diz %sª análise; o SOL diz %sª — valeu o SOL."
                          % (p["analise"], api["numeroAnalise"]))
        p["analise"] = int(api["numeroAnalise"])

    car = L.get("caracteristica") or {}
    for rot, chave in (("Geral", "resultadoGeral"), ("Tipo de edificação", "resultadoTipoEdificacao"),
                       ("Isolamento de risco", "resultadoIsolamentoRisco")):
        for t in _justificativas({"resultado": car.get(chave)} if car.get(chave) else None):
            textos.append({"campo": "3", "item": rot, "texto": t})

    grupos = (
        ("4", "medidas", "medida", (L.get("especSeguranca") or {}).get("medidas") or [],
         lambda o: ((o.get("tipo") or {}).get("nome"))),
        ("5", "riscos_especificos", "risco", L.get("especsRiscos") or [],
         lambda o: ((o.get("risco") or {}).get("descricao"))),
        ("6", "elementos_graficos", "nome",
         [e for e in (L.get("elemGraficos") or []) if e.get("situacao") == "ATIVO"],
         lambda o: o.get("descricao")),
    )
    for campo, secao, chave, itens, nome_de in grupos:
        registro = p.setdefault(secao, [])
        for o in itens:
            nome = nome_de(o) or "?"
            alvo = _casar(registro, chave, nome)
            st = _status(o)
            if alvo is None:
                avisos.append("campo %s: '%s' está no SOL (%s) e não no registro de trabalho."
                              % (campo, nome, st))
            elif alvo.get("status") != st:
                alvo["status"] = st
            for t in _justificativas(o):
                textos.append({"campo": campo, "item": nome, "texto": t})
        nomes_sol = {sseg._norm(nome_de(o)) for o in itens}
        for x in registro:
            if x.get(chave) and sseg._norm(x.get(chave)) not in nomes_sol:
                avisos.append("campo %s: '%s' está no registro de trabalho e não no SOL."
                              % (campo, x.get(chave)))

    # Rede de segurança: qualquer outra justificativa da API que os caminhos acima não cobrem
    # (demais inconformidades, ocupações...) entra com o caminho, para não sumir.
    cobertos = {id(j) for _c, _s, _k, itens, _n in grupos for o in itens
                for j in (list(o.get("justificativas") or []) +
                          list((o.get("resultado") or {}).get("justificativas") or []))}
    for chave in ("resultadoGeral", "resultadoTipoEdificacao", "resultadoIsolamentoRisco"):
        for j in ((car.get(chave) or {}).get("justificativas") or []):
            cobertos.add(id(j))

    def varrer(o, caminho):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "justificativas" and isinstance(v, list):
                    for j in v:
                        if isinstance(j, dict) and j.get("justificativa") and id(j) not in cobertos:
                            textos.append({"campo": "?", "item": caminho, "texto": j["justificativa"]})
                            avisos.append("justificativa fora dos campos 3-6 em %s — conferir o campo." % caminho)
                else:
                    varrer(v, "%s.%s" % (caminho, k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                varrer(v, "%s[%d]" % (caminho, i))
    varrer(L, "licenciamento")

    for t in textos:
        if len(t["texto"]) > 2000:
            avisos.append("campo %s '%s': %d caracteres, acima do limite de 2.000 da caixa."
                          % (t["campo"], t["item"], len(t["texto"])))
    return p, textos, avisos


def arquivar(api_path, trabalho_path, pasta, forcar=False):
    api = sseg._load(api_path)
    trabalho = sseg._load(trabalho_path)
    p, textos, avisos = montar(api, trabalho)
    n = p.get("analise")
    if not n:
        raise SystemExit("não sei o número da análise (nem no SOL nem no registro de trabalho)")

    nomes = {"json": "%s.json" % n, "pdf": "%s.pdf" % n, "textos": "CIA %s textos.json" % n}
    os.makedirs(pasta, exist_ok=True)
    existentes = [v for v in nomes.values() if os.path.exists(os.path.join(pasta, v))]
    if existentes and not forcar:
        raise SystemExit("já existem na pasta: %s. Use --forcar para substituir." % ", ".join(existentes))

    tmp = tempfile.mkdtemp(prefix="sseg-arquivar-")
    with open(os.path.join(tmp, nomes["json"]), "w", encoding="utf-8") as fh:
        json.dump(p, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(tmp, nomes["textos"]), "w", encoding="utf-8") as fh:
        json.dump(textos, fh, ensure_ascii=False, indent=2)
    html = os.path.join(tmp, "%s.html" % n)
    with open(html, "w", encoding="utf-8") as fh:
        fh.write(sseg.render_html(p))
    sseg.gerar_pdf(html, os.path.join(tmp, nomes["pdf"]))
    for v in nomes.values():
        shutil.copy2(os.path.join(tmp, v), os.path.join(pasta, v))
    shutil.rmtree(tmp, ignore_errors=True)

    cont = {}
    for secao in ("medidas", "riscos_especificos", "elementos_graficos"):
        for x in p.get(secao, []):
            cont[x.get("status")] = cont.get(x.get("status"), 0) + 1
    print("%sª análise de %s arquivada em %s" % (n, p.get("processo"), pasta))
    print("  %s" % ", ".join(nomes.values()))
    print("  status: %s | caixas Especificar: %d" % (
        ", ".join("%s %d" % (k, v) for k, v in sorted(cont.items())), len(textos)))
    for a in avisos:
        print("  ! " + a)
    if not avisos:
        print("  sem divergências entre o SOL e o registro de trabalho")


def args_parser(sp_receber, sp_arquivar):
    sp_receber.add_argument("--saida", required=True)
    sp_receber.add_argument("--porta", type=int, default=8765)
    sp_arquivar.add_argument("--api", required=True, help="JSON da API gravado pelo receber")
    sp_arquivar.add_argument("--trabalho", required=True, help="<N>.json de trabalho da análise")
    sp_arquivar.add_argument("--pasta", required=True, help="pasta do processo em print ppci")
    sp_arquivar.add_argument("--forcar", action="store_true")
