#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sol_base.py — base com todos os processos do SOL que a sessão do servidor enxerga, sem modelo (zero token).

POR QUÊ
-------
A caixa (sol_caixa.py) só traz os processos distribuídos. A aba "Processos" do SSEG.exe mostra
todos, e o Início fica só com os vivos. Coleta liberada em 17/10/2026: o Sgt Magalhães entrou no
projeto e deu o aval, com a chefia já avisada. A lógica é a do coletor dele (ColetaSOLCBM), com a
sessão que o sol_caixa.py já mantém (login automático incluído).

O QUE FAZ
---------
  1. Lista: GET /licenciamentos (criação de 2000 até amanhã, páginas de 1000). Uns 7 mil processos,
     7 consultas. Grava lista.json: situação de cada um, quando apareceu e quando a situação mudou.
  2. Detalhe (3 consultas por processo): /licenciamentos/<id>, /<id>/marcos e
     /licenciamento-historico/<id>, em proc/<id>.json. Quais:
       - normal (8h, 12h, 16h): os vivos ainda não coletados, os que mudaram de situação desde a
         última coleta e os que deram erro (até 3 vezes seguidas);
       - --completo (domingo, a cada 2 semanas): todos os da lista.
     Encerrado (alvará, extinto, rascunho) só é consultado quando muda de situação ou no completo.
  3. CIAs: o texto (pdftotext) de cada "Conclusão de análise técnica - CIA" dos Marcos, em cia/<id>.txt.
     O PDF não fica guardado.
  4. indice.json: uma linha por processo para a aba (código, situação, cidade, razão social,
     protocolo, última análise e quem fez). É o que o porta.py serve ao SSEG.exe.

Fora: "informacoes-processo" (vistoria), por decisão do Átila em 17/10/2026.
Ritmo do sol_caixa.py: 0,15 s entre consultas e nova tentativa em erro passageiro. Sessão recusada no
meio: um login automático (sol_caixa.entrar, que respeita a trava) e segue; recusou de novo, para.
O que já veio fica salvo: a próxima rodada continua dali.

Dados ficam em ~/sseg-base-sol/, fora do Git e fora de sseg/processos/ (não descem ao PC no
sincronizar; o SSEG.exe lê só o indice.json pelo porta.py, com chave autorizada).

USO (no servidor)
---
  python3 sseg/scripts/sol_base.py              # rodada normal
  python3 sseg/scripts/sol_base.py --completo   # consulta todos de novo
  python3 sseg/scripts/sol_base.py --indice     # só refaz o indice.json
  python3 sseg/scripts/sol_base.py --limite 50  # no máximo 50 detalhes (teste)
"""

import argparse
import datetime
import fcntl
import json
import os
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import marcos as mc  # noqa: E402
import sol_caixa as sc  # noqa: E402

BASE = os.path.expanduser("~/sseg-base-sol")
LISTA = os.path.join(BASE, "lista.json")
ESTADO = os.path.join(BASE, "estado.json")
INDICE = os.path.join(BASE, "indice.json")
TAM = 1000
# fora dos vivos: o Início não mostra e a rodada normal não reconsulta enquanto a situação não muda
ENCERRADAS = {"ALVARA_VIGENTE", "ALVARA_VENCIDO", "EXTINGUIDO", "RASCUNHO"}
MAX_ERROS_SEGUIDOS = 15  # acima disso o SOL provavelmente caiu: para (como o coletor do Magalhães)


def agora():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def _ler(arq, padrao):
    try:
        with open(arq, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return padrao


def _gravar(arq, dados):
    os.makedirs(os.path.dirname(arq), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(arq), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(dados, fh, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, arq)


class Sessao:
    """A aba do SOL do servidor, com um login automático por recusa (o sol_caixa.entrar põe a trava se falhar)."""

    def __init__(self):
        self.aba = sc.aba_do_sol()
        if self.aba is None:
            raise SystemExit("Chrome do servidor fora do ar ou sem aba do SOL: rode ~/rotinas/sol-chrome.sh iniciar.")
        if not sc._logar_se_caiu(self.aba)["logado"]:
            raise SystemExit("Sessão do SOL caída e o login automático não entrou.")
        self.consultas = 0

    def _refazer(self):
        s = sc._logar_se_caiu(self.aba)
        if not s["logado"]:
            raise SystemExit("Sessão do SOL caiu no meio e o login automático não entrou: o que veio está salvo.")

    def json(self, caminho):
        for tentativa in (1, 2):
            try:
                self.consultas += 1
                return sc.buscar(self.aba, caminho)
            except PermissionError:
                if tentativa == 2:
                    raise SystemExit("O SOL recusou a sessão de novo depois do login: parei.")
                self._refazer()

    def pdf(self, id_arquivo):
        for tentativa in (1, 2):
            self.consultas += 1
            try:
                r = sc._consultar(self.aba, sc.BAIXAR, "%s/%s" % (sc.ARQUIVO, id_arquivo))
            except PermissionError:
                if tentativa == 2:
                    raise SystemExit("O SOL recusou a sessão de novo depois do login: parei.")
                self._refazer()
                continue
            if r["status"] != 200:
                raise RuntimeError("SOL respondeu %s no arquivo %s" % (r["status"], id_arquivo))
            import base64
            return base64.b64decode(r["b64"])


# ------------------------------------------------------------------ 1. lista

def listar(s):
    fim = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    itens, vistos, pagina, total = [], set(), 0, None
    while True:
        d = s.json("%s?dataInicioCriacao=2000-01-01&dataFimCriacao=%s&tamanho=%d&paginaAtual=%d"
                   % (sc.LICENCIAMENTO, fim, TAM, pagina)) or {}
        lote = d.get("lista") or []
        total = d.get("total", total)
        for x in lote:
            if x.get("id") is not None and x["id"] not in vistos:
                vistos.add(x["id"])
                itens.append(x)
        pagina += 1
        if not lote or len(lote) < TAM or (total and len(itens) >= total):
            break
    if not itens:
        raise SystemExit("A lista do SOL veio vazia: nada mudado na base.")
    return itens, total


def guardar_lista(itens):
    """lista.json = {id: linha}. Marca quem é novo, quem mudou de situação e quem sumiu da lista."""
    antes = _ler(LISTA, {})
    momento, novos, mudaram = agora(), 0, 0
    nova = {}
    for x in itens:
        k = str(x["id"])
        velho = antes.get(k) or {}
        linha = {"id": x["id"], "numero": x.get("numero") or "", "situacao": x.get("situacao") or "",
                 "cidade": x.get("cidade") or "", "razao": (x.get("razaoSocial") or "").strip(),
                 "endereco": " ".join(str(v).strip() for v in (x.get("logradouro"), x.get("numeroEndereco")) if v),
                 "reserva": bool(x.get("reserva")), "presente": True,
                 "desde": velho.get("desde") or momento, "mudou_em": velho.get("mudou_em") or "",
                 "anterior": velho.get("anterior") or ""}
        if not velho:
            novos += 1
        elif velho.get("situacao") != linha["situacao"]:
            mudaram += 1
            linha["mudou_em"], linha["anterior"] = momento, velho.get("situacao") or ""
        nova[k] = linha
    sumiram = 0
    for k, v in antes.items():
        if k not in nova:
            sumiram += 1
            nova[k] = dict(v, presente=False)
    _gravar(LISTA, nova)
    return nova, {"novos": novos, "mudaram": mudaram, "sumiram": sumiram}


# ------------------------------------------------------------------ 2. detalhe

def a_coletar(lista, estado, completo):
    fila = []
    for k, l in lista.items():
        if not l["presente"]:
            continue
        e = estado.get(k) or {}
        if completo:
            fila.append(k)
        elif e.get("erro") and e.get("erros", 0) < 3:
            fila.append(k)
        elif not e.get("coletado_em"):
            if l["situacao"] not in ENCERRADAS:
                fila.append(k)
        elif e.get("situacao") != l["situacao"]:
            fila.append(k)
    # vivos primeiro (os que importam saem antes se a rodada parar no meio), depois do mais novo ao mais velho
    fila.sort(key=lambda k: (lista[k]["situacao"] in ENCERRADAS, -lista[k]["id"]))
    return fila


def _data_sol(t):
    """'28/02/2026 - 12:14' → '2026-02-28'."""
    p = (t or "").split(" ")[0].split("/")
    return "-".join(reversed(p)) if len(p) == 3 else ""


def ficha(lic):
    """Campos de busca da aba Processos (2.3.23), tirados do licenciamento. CPF de pessoa física fica de fora:
    só CNPJ (14 dígitos) entra na busca."""
    lic = lic or {}
    c = lic.get("caracteristica") or {}
    env = lic.get("envolvidos") or {}
    ocup = [{"div": ((o.get("cnae") or {}).get("divisao") or "").strip(), "tipo": (o.get("ocupacao") or "").lower(),
             "cnae": " ".join(((o.get("cnae") or {}).get("descricao") or "").split())[:90]}
            for o in c.get("ocupacoes") or []]
    docs = {(x.get("cpfCnpj") or "") for x in (env.get("proprietarios") or []) + (env.get("estabelecimentos") or [])}
    fantasia = {(x.get("nomeFantasia") or "").strip() for x in (env.get("estabelecimentos") or []) + (env.get("proprietarios") or [])}
    loc = lic.get("localizacao") or {}
    alt = max(float(c.get("alturaDescendente") or 0), float(c.get("alturaAscendente") or 0))
    return {"ocupacoes": ocup, "area": c.get("areaConstruida"), "altura": round(alt, 2),
            "populacao": c.get("populacaoTotal"), "pavimentos": (c.get("pavimAcimaSolo") or 0) + (c.get("pavimAbaixoSolo") or 0),
            "situacao_ed": (c.get("edificacao") or "").replace("_", " ").lower(),
            "cnpj": sorted(d for d in docs if len(d) == 14), "fantasia": sorted(f for f in fantasia if f)[:3],
            "rt": sorted({(x.get("nome") or "").strip() for x in env.get("rts") or [] if x.get("nome")}),
            "bairro": (loc.get("bairro") or "").strip(), "criado": _data_sol(lic.get("dataCriacao"))}


def resumo_do(lic, marcos, historico):
    r = mc.com_historico(mc.resumir(marcos), historico, None)
    ult = r["analises"][-1] if r["analises"] else {}
    return dict(ficha(lic), protocolo=r["protocolo"], analises=len(r["analises"]),
                ultima={"data": ult.get("data", ""), "resultado": ult.get("resultado", ""),
                        "quem": ult.get("responsavel", "")} if ult else None,
                cias=[a["arquivo"] for a in r["analises"] if a["resultado"] == "CIA" and a["arquivo"]],
                recursos=len(r["recursos"]), id_analise=(lic or {}).get("idAnaliseTecnica"))


def refazer_resumos():
    """Recalcula o resumo de cada processo a partir de proc/<id>.json, sem consultar o SOL (campo novo no índice)."""
    estado = _ler(ESTADO, {})
    n = 0
    for k, e in estado.items():
        d = _ler(os.path.join(BASE, "proc", k + ".json"), None)
        if d:
            e["resumo"] = resumo_do(d.get("licenciamento"), d.get("marcos") or [], d.get("historico") or {})
            n += 1
    _gravar(ESTADO, estado)
    return n


def coletar(s, k, linha):
    pid = linha["id"]
    lic = s.json("%s/%s" % (sc.LICENCIAMENTO, pid))
    marcos = s.json("%s/%s/marcos" % (sc.LICENCIAMENTO, pid)) or []
    try:
        historico = s.json("%s/%s" % (sc.HISTORICO, pid)) or {}
    except RuntimeError:  # processo sem histórico de recurso pode responder 404
        historico = {}
    _gravar(os.path.join(BASE, "proc", k + ".json"),
            {"coletado_em": agora(), "licenciamento": lic, "marcos": marcos, "historico": historico})
    return resumo_do(lic, marcos, historico)


def baixar_cias(s, ids):
    feitas = 0
    for a in ids:
        txt = os.path.join(BASE, "cia", "%s.txt" % a)
        if os.path.exists(txt):
            continue
        dados = s.pdf(a)
        if not dados.startswith(b"%PDF"):
            raise RuntimeError("arquivo %s não é PDF" % a)
        os.makedirs(os.path.dirname(txt), exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
            tmp.write(dados)
            tmp.flush()
            subprocess.run(["pdftotext", "-layout", tmp.name, txt + ".tmp"], check=True, timeout=120)
        os.replace(txt + ".tmp", txt)
        feitas += 1
    return feitas


# ------------------------------------------------------------------ 4. índice

def _guerra():
    """Nome completo do SOL → nome de guerra da escala ("CASSIO LUIZ BRITO" → "Sgt Brito"), pela regra do
    distribuicao.nome_conhecido. Quem não é da seção fica com o nome completo (pedido do Átila, 17/10/2026)."""
    import distribuicao
    nomes = list((_ler(os.path.expanduser("~/sseg-escala/escala.json"), {}).get("horas") or {}).keys())
    feitos = {}

    def f(completo):
        if not completo or not nomes:
            return ""
        if completo not in feitos:
            n = distribuicao.nome_conhecido(completo, nomes)
            if n not in nomes:
                # dois nomes de guerra no mesmo nome ("SERGIO PATRICK CARDOZO PENA": Sgt Sérgio, não Sd Patrick, que é
                # o Patrick José de Almeida): vale a palavra que vem primeiro no nome completo
                pal = distribuicao._norm(completo).split()
                cand = [(pal.index(distribuicao._norm(k).split()[-1]), k) for k in nomes
                        if distribuicao._norm(k).split() and distribuicao._norm(k).split()[-1] in pal]
                n = min(cand)[1] if len(cand) > 1 else ""
            feitos[completo] = n
        return feitos[completo]
    return f


def gerar_indice(lista=None, estado=None):
    lista = lista if lista is not None else _ler(LISTA, {})
    estado = estado if estado is not None else _ler(ESTADO, {})
    guerra = _guerra()
    linhas = []
    for k, l in lista.items():
        if not l.get("presente"):
            continue
        r = (estado.get(k) or {}).get("resumo") or {}
        linhas.append({"id": l["id"], "numero": l["numero"], "situacao": l["situacao"], "cidade": l["cidade"],
                       "razao": l["razao"], "endereco": l.get("endereco", ""), "mudou_em": l.get("mudou_em", ""),
                       "anterior": l.get("anterior", ""),
                       **{c: r.get(c) for c in ("ocupacoes", "area", "altura", "populacao", "pavimentos", "situacao_ed",
                                                "cnpj", "fantasia", "rt", "bairro", "criado")},
                       "desde": l.get("desde", ""), "vivo": l["situacao"] not in ENCERRADAS,
                       "protocolo": r.get("protocolo", ""), "analises": r.get("analises"),
                       "ultima": dict(r["ultima"], guerra=guerra(r["ultima"].get("quem"))) if r.get("ultima") else None, "recursos": r.get("recursos"), "id_analise": r.get("id_analise"),
                       "cias": len(r.get("cias") or []), "coletado_em": (estado.get(k) or {}).get("coletado_em", "")})
    linhas.sort(key=lambda x: x["numero"], reverse=True)
    meta = _ler(os.path.join(BASE, "rodada.json"), {})
    _gravar(INDICE, {"gerado_em": agora(), "rodada": meta, "total": len(linhas),
                     "vivos": sum(1 for x in linhas if x["vivo"]), "processos": linhas})
    return len(linhas)


# ------------------------------------------------------------------ rodada

def rodar(completo=False, limite=None):
    os.makedirs(BASE, exist_ok=True)
    trava = open(os.path.join(BASE, ".rodando"), "w")
    try:
        fcntl.flock(trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("Outra rodada da base já está em andamento.")
        return 1
    inicio = time.time()
    meta = {"inicio": agora(), "modo": "completo" if completo else "normal", "fim": "", "resultado": "em andamento"}
    _gravar(os.path.join(BASE, "rodada.json"), meta)
    s = None
    estado = _ler(ESTADO, {})
    feitos = erros = cias = 0
    try:
        s = Sessao()
        itens, total = listar(s)
        lista, mud = guardar_lista(itens)
        print("Lista: %d processos (%s no SOL): %d novos, %d mudaram de situação, %d sumiram."
              % (len(itens), total, mud["novos"], mud["mudaram"], mud["sumiram"]))
        fila = a_coletar(lista, estado, completo)
        if limite:
            fila = fila[:limite]
        print("A consultar: %d processo(s)." % len(fila))
        seguidos = 0
        for i, k in enumerate(fila, 1):
            l = lista[k]
            try:
                r = coletar(s, k, l)
                estado[k] = {"situacao": l["situacao"], "coletado_em": agora(), "resumo": r}
                seguidos = 0
                feitos += 1
            except (RuntimeError, ValueError, KeyError, OSError) as e:
                e0 = estado.get(k) or {}
                estado[k] = dict(e0, erro=str(e)[:200], erros=e0.get("erros", 0) + 1)
                erros += 1
                seguidos += 1
                print("  %s: %s" % (l["numero"] or k, str(e)[:200]))
                if seguidos >= MAX_ERROS_SEGUIDOS:
                    raise SystemExit("%d processos seguidos falharam: o SOL pode estar fora. O que veio está salvo." % seguidos)
                continue
            try:
                cias += baixar_cias(s, r["cias"])
            except (RuntimeError, OSError, subprocess.SubprocessError) as e:
                print("  %s: CIA não lida (%s)" % (l["numero"], str(e)[:150]))
            if i % 50 == 0:
                _gravar(ESTADO, estado)
                if i % 500 == 0:  # a aba Processos vê o andamento sem esperar o fim da rodada
                    gerar_indice(lista, estado)
                gasto = time.time() - inicio
                print("  %d de %d (%d min; faltam ~%d min)" % (i, len(fila), gasto // 60, gasto / i * (len(fila) - i) // 60))
                sys.stdout.flush()
        meta["resultado"] = "concluída"
        return 0
    except SystemExit as e:
        meta["resultado"] = "parou: %s" % e
        print(e)
        return 2
    finally:
        _gravar(ESTADO, estado)
        meta.update(fim=agora(), detalhes=feitos, erros=erros, cias=cias,
                    consultas=s.consultas if s else 0, minutos=round((time.time() - inicio) / 60, 1))
        _gravar(os.path.join(BASE, "rodada.json"), meta)
        n = gerar_indice(estado=estado)
        print("Rodada %s: %d detalhe(s), %d erro(s), %d CIA(s), %d consultas, %.1f min. Índice: %d processos."
              % (meta["resultado"], feitos, erros, cias, meta["consultas"], meta["minutos"], n))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--completo", action="store_true", help="consulta todos os processos da lista")
    ap.add_argument("--indice", action="store_true", help="só refaz o indice.json")
    ap.add_argument("--resumos", action="store_true", help="recalcula os resumos dos proc/*.json (sem SOL) e o índice")
    ap.add_argument("--limite", type=int, help="no máximo N detalhes nesta rodada")
    a = ap.parse_args()
    if a.resumos:
        print("Resumos refeitos: %d." % refazer_resumos())
        a.indice = True
    if a.indice:
        print("Índice: %d processos." % gerar_indice())
        return 0
    return rodar(a.completo, a.limite)


if __name__ == "__main__":
    sys.exit(main())
