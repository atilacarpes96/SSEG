#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sol_banco.py — a base do SOL do servidor como banco SQL (solcbm.db), sem modelo e sem consulta ao SOL.

POR QUÊ
-------
O sol_base.py guarda um JSON por processo (~/sseg-base-sol/proc/<id>.json) e um índice resumido. Para a
aba Processos do SSEG.exe (painel com mapa, pesquisa, ficha e busca nas CIAs) e para o Claude do servidor
perguntar "quantos F-6 com CIA citando RT 11?", o mesmo conteúdo precisa estar em tabelas. O formato é o
da Consulta SOLCBM do Sgt Magalhães (esquema 2, de 17/10/2026): as regras de leitura do JSON estão em
dados/solcbm_visoes.sql, copiadas do banco dele, e cada visão vira tabela.

O QUE FAZ
---------
  1. Tabelas brutas: sol_lista (lista.json), sol_bruto (por processo: "informacoes" = licenciamento +
     laudos/vistoria, "marcos", "historico"), sol_cia_texto (cia/<id>.txt, ligado ao marco da CIA) e sol_estado.
  2. Visões de solcbm_visoes.sql gravadas como tabelas: processos, ocupacoes, medidas, envolvidos, marcos,
     analises, boletos, elementos_graficos, laudos, areas_memorial, riscos_especiais e cias.
  3. Colunas de busca sem acento (processos.busca e cias.busca), para "antipanico" achar "antipânico".
  4. Grava em solcbm.db.novo e troca no fim: quem estiver lendo não vê banco pela metade.

Dados pessoais (CPF, e-mail, telefone, pagador de boleto) ficam no banco: o Átila decidiu em 28/10/2026
mostrar tudo na ficha, como a Consulta SOLCBM. O banco fica em ~/sseg-base-sol/, fora do Git.

USO (no servidor; o sol_base.py chama no fim de cada rodada)
---
  python3 sseg/scripts/sol_banco.py
"""

import json
import os
import re
import sqlite3
import sys
import time
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
VISOES = os.path.join(AQUI, "dados", "solcbm_visoes.sql")
BASE = os.path.expanduser("~/sseg-base-sol")
CIA = "Conclusão de análise técnica - CIA"
TABELAS = ["processos", "ocupacoes", "medidas", "envolvidos", "marcos", "analises", "boletos", "elementos_graficos",
           "laudos", "areas_memorial", "riscos_especiais", "cias"]

BRUTAS = """
CREATE TABLE sol_meta (chave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE sol_lista (id INTEGER PRIMARY KEY, numero TEXT, tipo TEXT, situacao TEXT, cidade TEXT, logradouro TEXT,
    numero_endereco TEXT, razao_social TEXT, json TEXT, primeira_vez_em TEXT, situacao_alterada_em TEXT,
    presente_ultima_lista INTEGER DEFAULT 1);
CREATE TABLE sol_bruto (id_licenciamento INTEGER, recurso TEXT, json TEXT, coletado_em TEXT,
    PRIMARY KEY (id_licenciamento, recurso));
CREATE TABLE sol_estado (id_licenciamento INTEGER PRIMARY KEY, situacao_coletada TEXT, coletado_em TEXT, erro TEXT,
    erros_seguidos INTEGER DEFAULT 0);
CREATE TABLE sol_cia_texto (id_arquivo INTEGER PRIMARY KEY, id_licenciamento INTEGER, dth_marco INTEGER,
    nome_arquivo TEXT, texto TEXT, paginas INTEGER, bytes INTEGER, coletado_em TEXT, erro TEXT);
"""


def sem_acento(t):
    t = unicodedata.normalize("NFD", str(t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _ler(arq, padrao):
    try:
        with open(arq, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return padrao


def _brutas(con, base):
    lista, estado = _ler(os.path.join(base, "lista.json"), {}), _ler(os.path.join(base, "estado.json"), {})
    con.executemany("INSERT INTO sol_lista VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [
        (l["id"], l.get("numero"), "PPCI", l.get("situacao"), l.get("cidade"), l.get("endereco"), None, l.get("razao"),
         None, l.get("desde"), l.get("mudou_em") or None, 1 if l.get("presente") else 0) for l in lista.values()])
    con.executemany("INSERT INTO sol_estado VALUES (?,?,?,?,?)", [
        (int(k), e.get("situacao"), e.get("coletado_em"), e.get("erro"), e.get("erros", 0)) for k, e in estado.items()])
    n = 0
    for k in lista:
        d = _ler(os.path.join(base, "proc", k + ".json"), None)
        if not d or not d.get("licenciamento"):
            continue
        quando = d.get("coletado_em")
        info = dict(d.get("informacoes") or {}, licenciamentoDTO=d["licenciamento"])
        con.executemany("INSERT INTO sol_bruto VALUES (?,?,?,?)", [
            (int(k), "informacoes", json.dumps(info, ensure_ascii=False), quando),
            (int(k), "marcos", json.dumps(d.get("marcos") or [], ensure_ascii=False), quando),
            (int(k), "historico", json.dumps(d.get("historico") or {}, ensure_ascii=False), quando)])
        for m in d.get("marcos") or []:
            arq = m.get("arquivo") or {}
            if m.get("descricao") != CIA or not arq.get("id"):
                continue
            texto = None
            try:
                with open(os.path.join(base, "cia", "%s.txt" % arq["id"]), encoding="utf-8", errors="replace") as fh:
                    texto = fh.read()
            except OSError:
                pass
            con.execute("INSERT OR REPLACE INTO sol_cia_texto VALUES (?,?,?,?,?,?,?,?,?)",
                        (arq["id"], int(k), m.get("dthMarco"), arq.get("nomeArquivo"), texto,
                         texto.count("\f") + 1 if texto else None, None, quando, None if texto else "texto ainda não baixado"))
        n += 1
    return n


def _busca(con):
    """Colunas sem acento para a pesquisa: o SQLite não tira acento sozinho."""
    con.execute("ALTER TABLE processos ADD COLUMN busca TEXT")
    extra = {}
    for i, nome, fantasia, doc in con.execute("SELECT id_licenciamento, nome, nome_fantasia, cpf_cnpj FROM envolvidos"):
        extra.setdefault(i, []).extend(x for x in (nome, fantasia, doc) if x)
    linhas = con.execute("SELECT id, numero, razao_social, nome_fantasia, logradouro, numero_endereco, bairro, cidade, "
                         "cpf_cnpj_estabelecimento, responsavel_tecnico, proprietario FROM processos").fetchall()
    con.executemany("UPDATE processos SET busca = ? WHERE id = ?",
                    [(sem_acento(" ".join(str(x) for x in r[1:] + tuple(extra.get(r[0], [])) if x)), r[0]) for r in linhas])
    con.execute("ALTER TABLE cias ADD COLUMN busca TEXT")
    con.executemany("UPDATE cias SET busca = ? WHERE id_arquivo = ?",
                    [(sem_acento(re.sub(r"\s+", " ", t)), a) for a, t in con.execute("SELECT id_arquivo, texto FROM cias WHERE texto IS NOT NULL")])


def montar(base=None, destino=None):
    base = base or BASE
    destino = destino or os.path.join(base, "solcbm.db")
    novo = destino + ".novo"
    for x in (novo, novo + "-journal"):
        if os.path.exists(x):
            os.remove(x)
    inicio = time.time()
    con = sqlite3.connect(novo)
    try:
        con.executescript(BRUTAS)
        con.execute("INSERT INTO sol_meta VALUES ('versao_esquema', '2'), ('gerado_em', ?)", (time.strftime("%Y-%m-%d %H:%M"),))
        n = _brutas(con, base)
        with open(VISOES, encoding="utf-8") as fh:
            con.executescript(fh.read())
        for t in TABELAS:
            con.execute("CREATE TABLE %s AS SELECT * FROM v_%s" % (t, t))
            con.execute("CREATE INDEX ix_%s_id ON %s(%s)" % (t, t, "id" if t == "processos" else "id_licenciamento"))
        for c in ("numero", "cidade", "situacao"):
            con.execute("CREATE INDEX ix_processos_%s ON processos(%s)" % (c, c))
        _busca(con)
        con.commit()
        con.execute("ANALYZE")
        con.commit()
    finally:
        con.close()
    os.replace(novo, destino)
    return n, round(time.time() - inicio, 1)


def main():
    n, s = montar()
    print("Banco: %d processos em %.1f s." % (n, s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
