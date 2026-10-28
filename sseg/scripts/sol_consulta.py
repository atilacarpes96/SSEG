#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sol_consulta.py — consultas prontas ao solcbm.db (sol_banco.py), sem modelo (zero token).

As mesmas telas da Consulta SOLCBM do Sgt Magalhães, como funções que devolvem JSON. Quem usa:
  - o SSEG.exe, pela porta do servidor: `porta.py banco <consulta>` com os parâmetros em JSON no stdin
    (aba Processos: painel, pesquisa, ficha do processo e busca nas CIAs);
  - o Claude do servidor, pela linha de comando, em vez de abrir os JSON da base (economiza token).

CONSULTAS
  resumo                       → números do painel: situação, grupo, município, ano de criação
  opcoes                       → valores dos filtros (municípios, situações, grupos, divisões...)
  mapa      {filtros}          → [[id, lat, lng, situação, número, razão social], ...]
  pesquisa  {filtros, pagina}  → {total, tamanho, linhas}; filtros: q, cidade, situacao, grupo, divisao,
                                 risco, analista, edificacao, criacao_de, criacao_ate, area_min, area_max,
                                 com_cia, vivos, numeros (lista de códigos), ordem, sentido
  processo  {id | numero}      → a ficha: processo, ocupações, medidas, envolvidos, análises, elementos,
                                 CIAs, marcos, boletos, laudos, áreas e riscos especiais
  cias      {q, cidade, analista, de, ate, pagina} → CIAs que contêm o trecho, com o trecho destacado

USO
  python3 sseg/scripts/sol_consulta.py pesquisa '{"divisao": "F-6", "com_cia": 1}'
  python3 sseg/scripts/sol_consulta.py processo '{"numero": "A000XXXXXAA001"}'
  python3 sseg/scripts/sol_consulta.py cias '{"q": "barra antipanico"}'
"""

import json
import os
import re
import sqlite3
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from sol_banco import BASE, sem_acento  # noqa: E402

BANCO = os.path.join(BASE, "solcbm.db")
ENCERRADAS = ("ALVARA_VIGENTE", "ALVARA_VENCIDO", "EXTINGUIDO", "RASCUNHO")
TAM_PESQUISA, TAM_CIAS = 100, 20
ORDEM = {"numero": "numero", "situacao": "situacao", "cidade": "cidade", "razao": "razao_social", "divisao": "divisao",
         "area": "area_construida", "criacao": "data_criacao", "cias": "qtd_cia", "analista": "ultimo_analista",
         "marco": "data_ultimo_marco"}


def abrir(banco=None):
    banco = banco or BANCO
    if not os.path.exists(banco):
        raise RuntimeError("O banco do SOL ainda não foi montado no servidor (sol_banco.py).")
    con = sqlite3.connect("file:%s?mode=ro" % banco, uri=True)
    con.row_factory = sqlite3.Row
    return con


def _dicts(cur):
    return [dict(r) for r in cur]


def _filtros(p):
    """WHERE da pesquisa e do mapa, com parâmetros."""
    w, a = ["presente_ultima_lista = 1"], []
    for palavra in sem_acento(p.get("q") or "").split():
        w.append("busca LIKE ?")
        a.append("%" + palavra + "%")
    for campo, coluna in (("cidade", "cidade"), ("situacao", "situacao"), ("grupo", "grupo_ocupacao"), ("divisao", "divisao"),
                          ("risco", "grau_risco"), ("analista", "ultimo_analista"), ("edificacao", "edificacao")):
        if p.get(campo):
            w.append("%s = ?" % coluna)
            a.append(p[campo])
    if p.get("criacao_de"):
        w.append("data_criacao >= ?")
        a.append(p["criacao_de"])
    if p.get("criacao_ate"):
        w.append("data_criacao <= ?")
        a.append(p["criacao_ate"] + " 99")
    for campo, op in (("area_min", ">="), ("area_max", "<=")):
        try:
            v = float(str(p.get(campo)).replace(",", "."))
        except (TypeError, ValueError):
            continue
        w.append("area_construida %s ?" % op)
        a.append(v)
    if str(p.get("com_cia") or "") in ("1", "True", "true"):
        w.append("qtd_cia > 0")
    if str(p.get("vivos") or "") in ("1", "True", "true"):
        w.append("situacao NOT IN (%s)" % ",".join("?" * len(ENCERRADAS)))
        a.extend(ENCERRADAS)
    if p.get("numeros"):
        w.append("numero IN (%s)" % ",".join("?" * len(p["numeros"])))
        a.extend(p["numeros"])
    return " AND ".join(w), a


def resumo(con, p=None):
    um = lambda sql, *a: con.execute(sql, a).fetchone()[0]
    grupos = lambda sql: [{"chave": r[0], "n": r[1]} for r in con.execute(sql)]
    meta = dict(con.execute("SELECT chave, valor FROM sol_meta").fetchall())
    return {
        "na_lista": um("SELECT count(*) FROM sol_lista WHERE presente_ultima_lista = 1"),
        "coletados": um("SELECT count(*) FROM processos WHERE presente_ultima_lista = 1"),
        "cias": um("SELECT count(*) FROM cias WHERE texto IS NOT NULL"),
        "processos_com_cia": um("SELECT count(*) FROM processos WHERE qtd_cia > 0 AND presente_ultima_lista = 1"),
        "area_total": um("SELECT coalesce(sum(area_construida), 0) FROM processos WHERE presente_ultima_lista = 1"),
        "ultima_coleta": um("SELECT max(coletado_em) FROM sol_estado"), "gerado_em": meta.get("gerado_em"),
        "por_situacao": grupos("SELECT situacao, count(*) FROM processos WHERE presente_ultima_lista = 1 GROUP BY 1 ORDER BY 2 DESC"),
        "por_grupo": [{"chave": r[0], "descricao": r[1], "n": r[2]} for r in con.execute(
            "SELECT grupo_ocupacao, max(grupo_ocupacao_descricao), count(*) FROM processos WHERE presente_ultima_lista = 1 "
            "AND grupo_ocupacao IS NOT NULL GROUP BY 1 ORDER BY 3 DESC")],
        "por_cidade": grupos("SELECT cidade, count(*) FROM processos WHERE presente_ultima_lista = 1 GROUP BY 1 ORDER BY 2 DESC LIMIT 15"),
        "por_ano": grupos("SELECT substr(data_criacao, 1, 4), count(*) FROM processos WHERE presente_ultima_lista = 1 "
                          "AND data_criacao IS NOT NULL GROUP BY 1 ORDER BY 1"),
    }


def opcoes(con, p=None):
    lst = lambda col: [r[0] for r in con.execute("SELECT DISTINCT %s FROM processos WHERE %s IS NOT NULL AND %s <> '' "
                                                 "AND presente_ultima_lista = 1 ORDER BY 1" % (col, col, col))]
    return {"cidade": lst("cidade"), "situacao": lst("situacao"), "divisao": lst("divisao"), "risco": lst("grau_risco"),
            "analista": lst("ultimo_analista"), "edificacao": lst("edificacao"),
            "grupo": [{"valor": r[0], "descricao": r[1]} for r in con.execute(
                "SELECT grupo_ocupacao, max(grupo_ocupacao_descricao) FROM processos WHERE grupo_ocupacao IS NOT NULL "
                "GROUP BY 1 ORDER BY 1")]}


def mapa(con, p=None):
    w, a = _filtros(p or {})
    return [list(r) for r in con.execute(
        "SELECT id, coalesce(latitude_mapa, latitude_endereco), coalesce(longitude_mapa, longitude_endereco), situacao, numero, "
        "razao_social FROM processos WHERE %s AND coalesce(latitude_mapa, latitude_endereco) IS NOT NULL" % w, a)]


def pesquisa(con, p=None):
    p = p or {}
    w, a = _filtros(p)
    col = ORDEM.get(p.get("ordem") or "", "numero")
    sentido = "ASC" if p.get("sentido") == "asc" else "DESC"
    pagina = int(p.get("pagina") or 0)
    total = con.execute("SELECT count(*) FROM processos WHERE " + w, a).fetchone()[0]
    linhas = _dicts(con.execute(
        "SELECT id, numero, situacao, cidade, razao_social, nome_fantasia, logradouro, numero_endereco, bairro, divisao, "
        "grau_risco, area_construida, altura_ascendente, altura_descendente, populacao_total, data_criacao, qtd_cia, "
        "ultimo_analista, ultimo_marco, data_ultimo_marco, latitude_mapa, longitude_mapa FROM processos WHERE %s "
        "ORDER BY %s IS NULL, %s %s, numero DESC LIMIT %d OFFSET %d" % (w, col, col, sentido, TAM_PESQUISA, pagina * TAM_PESQUISA), a))
    return {"total": total, "tamanho": TAM_PESQUISA, "pagina": pagina, "linhas": linhas}


def processo(con, p):
    if p.get("numero"):
        r = con.execute("SELECT id FROM processos WHERE numero = ?", (p["numero"],)).fetchone()
        if not r:
            raise RuntimeError("Processo %s não está na base do SOL." % p["numero"])
        pid = r[0]
    else:
        pid = int(p["id"])
    x = con.execute("SELECT * FROM processos WHERE id = ?", (pid,)).fetchone()
    if not x:
        raise RuntimeError("Processo %s não está na base do SOL." % pid)
    x = dict(x)
    x.pop("busca", None)
    de = lambda t, ordem="rowid": _dicts(con.execute("SELECT * FROM %s WHERE id_licenciamento = ? ORDER BY %s" % (t, ordem), (pid,)))
    cias = de("cias", "data_conclusao DESC")
    for c in cias:
        c.pop("busca", None)
    return {"processo": x, "ocupacoes": de("ocupacoes"), "medidas": de("medidas"), "envolvidos": de("envolvidos"),
            "analises": de("analises", "data_hora DESC"), "elementos": de("elementos_graficos", "numero_analise DESC, data_inclusao DESC"),
            "cias": cias, "marcos": de("marcos", "data_hora DESC"), "boletos": de("boletos", "data_emissao DESC"),
            "laudos": de("laudos"), "areas": de("areas_memorial"), "riscos": de("riscos_especiais")}


def _trechos(texto, busca, termo, n=3, folga=110):
    """Até n trechos em volta do termo. busca = sem_acento do texto com espaços juntos: mesmas posições."""
    t = re.sub(r"\s+", " ", texto or "")
    out, i = [], 0
    while len(out) < n:
        j = busca.find(termo, i)
        if j < 0:
            break
        out.append({"antes": ("…" if j > folga else "") + t[max(0, j - folga):j], "achado": t[j:j + len(termo)],
                    "depois": t[j + len(termo):j + len(termo) + folga] + ("…" if j + len(termo) + folga < len(t) else "")})
        i = j + len(termo)
    return out


def cias(con, p):
    termo = re.sub(r"\s+", " ", sem_acento(p.get("q") or "")).strip()
    if len(termo) < 3:
        return {"aviso": "Digite pelo menos 3 letras.", "total": 0, "processos": 0, "por_ano": [], "linhas": []}
    w, a = ["c.busca LIKE ?"], ["%" + termo + "%"]
    if p.get("cidade"):
        w.append("p.cidade = ?")
        a.append(p["cidade"])
    if p.get("analista"):
        w.append("c.analista = ?")
        a.append(p["analista"])
    if p.get("de"):
        w.append("c.data_conclusao >= ?")
        a.append(p["de"])
    if p.get("ate"):
        w.append("c.data_conclusao <= ?")
        a.append(p["ate"] + " 99")
    base = "FROM cias c JOIN processos p ON p.id = c.id_licenciamento WHERE " + " AND ".join(w)
    total, procs = con.execute("SELECT count(*), count(DISTINCT c.id_licenciamento) " + base, a).fetchone()
    pagina = int(p.get("pagina") or 0)
    linhas = []
    for r in con.execute("SELECT c.id_licenciamento, c.id_arquivo, p.numero, p.razao_social, p.cidade, p.divisao, c.data_conclusao, "
                         "c.analista, c.texto, c.busca %s ORDER BY c.data_conclusao DESC LIMIT %d OFFSET %d"
                         % (base, TAM_CIAS, pagina * TAM_CIAS), a):
        d = dict(r)
        d["trechos"] = _trechos(d.pop("texto"), d.pop("busca"), termo)
        linhas.append(d)
    por_ano = [{"chave": r[0], "n": r[1]} for r in con.execute("SELECT substr(c.data_conclusao, 1, 4), count(*) %s GROUP BY 1 ORDER BY 1" % base, a)]
    return {"total": total, "processos": procs, "por_ano": por_ano, "pagina": pagina, "tamanho": TAM_CIAS, "linhas": linhas}


CONSULTAS = {"resumo": resumo, "opcoes": opcoes, "mapa": mapa, "pesquisa": pesquisa, "processo": processo, "cias": cias}


def consultar(nome, params=None, banco=None):
    if nome not in CONSULTAS:
        raise RuntimeError("consulta desconhecida: %s (há %s)" % (nome, ", ".join(CONSULTAS)))
    con = abrir(banco)
    try:
        return CONSULTAS[nome](con, params or {})
    finally:
        con.close()


def main(argv):
    if not argv or argv[0] not in CONSULTAS:
        print(__doc__)
        return 1
    r = consultar(argv[0], json.loads(argv[1]) if len(argv) > 1 else {})
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
