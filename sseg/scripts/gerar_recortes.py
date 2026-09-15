#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerar_recortes.py — regenera os recortes de dados/tabelas/ a partir de
dados/tabelas_conferidas.json.

A FONTE E SEMPRE dados/tabelas_conferidas.json. Os arquivos de dados/tabelas/ sao
recortes derivados, criados para poder ler um grupo de cada vez em vez de carregar os
~180 KB inteiros. Corrigindo uma celula, corrigir no tabelas_conferidas.json e rodar
este script — nunca editar so o recorte, que a proxima geracao sobrescreve.

USO
  python3 gerar_recortes.py            # grava em dados/tabelas/
  python3 gerar_recortes.py --conferir # so compara, nao grava (codigo 1 se divergir)

Gera 30 arquivos: 12 tab-b-<LETRA>.json + 12 tab-rt05-<LETRA>.json (Tabelas 6X),
tab-<fonte>-tabela5.json e tab-<fonte>-tabela7.json das duas fontes,
linhas-conferidas.json e tab-00-indice.json.
"""
import argparse, collections, json, os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(BASE, "dados", "tabelas_conferidas.json")
OUT = os.path.join(BASE, "dados", "tabelas")
FONTES = collections.OrderedDict([("b", "anexo_b_decreto"), ("rt05", "rt05_p07_anexo_a")])


def divisoes_do_rotulo(rot):
    """'A-2, A-3 e Condominios Residenciais' -> ['A-2', 'A-3']; 'M-3 - Centrais...' -> ['M-3']."""
    out = []
    for p in re.split(r",| e |–|—", rot):
        p = re.sub(r"\(.*", "", p).strip()
        if re.fullmatch(r"[A-M]-\d+", p) or re.fullmatch(r"L\d", p):
            out.append(p)
    return out


def recortes(src):
    """Devolve OrderedDict {nome_do_arquivo: objeto}."""
    docs = collections.OrderedDict()
    mapa = collections.OrderedDict()
    arquivos = []
    for pref, fkey in FONTES.items():
        v = src[fkey]
        grupos = collections.OrderedDict()
        for tab, t in v["tabelas"].items():
            letra = re.match(r"6([A-Z])", tab).group(1)
            grupos.setdefault(letra, collections.OrderedDict())[tab] = t
        mapa[pref] = collections.OrderedDict()
        for letra, tabs in grupos.items():
            nome = "tab-%s-%s.json" % (pref, letra)
            docs[nome] = collections.OrderedDict([
                ("fonte", fkey),
                ("fonte_nome", v["_o_que_e"]),
                ("colunas", src["_colunas_validas"]),
                ("como_ler", v["_como_ler"]),
                ("tabelas", tabs),
            ])
            arquivos.append(nome)
            for tab, t in tabs.items():
                for i, rot in enumerate(t["divisoes"]):
                    for d in divisoes_do_rotulo(rot):
                        mapa[pref][d] = collections.OrderedDict(
                            [("arquivo", nome), ("tabela", tab), ("bloco", i)])
        for n in ("5", "7"):
            nome = "tab-%s-tabela%s.json" % (pref, n)
            docs[nome] = v["tabela_" + n]
            arquivos.append(nome)

    docs["linhas-conferidas.json"] = collections.OrderedDict(
        (k, src[k]) for k in ("linhas", "linhas_rt05_p07", "grupos_por_tabela",
                              "grupos_por_tabela_rt05_p07", "_erro_registrado_leitura_imagem",
                              "_erro_registrado_fonte", "_convencao_de_contagem"))

    docs["tab-00-indice.json"] = collections.OrderedDict([
        ("regra_de_contagem", src["_leia_isto"]),
        ("duas_fontes", src["_duas_fontes"]),
        ("aplicar_as_notas", src["anexo_b_decreto"][u"⚠️_aplicar_as_notas"]),
        ("colunas", src["_colunas_validas"]),
        ("linhas_de_medida_por_fonte", src["_linhas_de_medida_por_fonte"]),
        ("nao_cobertas", collections.OrderedDict([
            ("anexo_b_decreto", src["anexo_b_decreto"]["_nao_cobertas"]),
            ("rt05_p07_anexo_a", src["rt05_p07_anexo_a"]["_nao_cobertas"]),
        ])),
        ("mapa", mapa),
        ("arquivos", sorted(arquivos)),
    ])
    return docs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conferir", action="store_true",
                    help="nao grava; compara com o que ja esta em dados/tabelas/")
    a = ap.parse_args()
    with open(DADOS, encoding="utf-8") as fh:
        src = json.load(fh)
    docs = recortes(src)
    os.makedirs(OUT, exist_ok=True)
    divergiu = []
    for nome, obj in docs.items():
        txt = json.dumps(obj, ensure_ascii=False, indent=1)
        p = os.path.join(OUT, nome)
        if a.conferir:
            atual = open(p, encoding="utf-8").read() if os.path.exists(p) else None
            if atual != txt:
                divergiu.append(nome)
        else:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(txt)
    if a.conferir:
        print("DIVERGEM: %s" % ", ".join(divergiu) if divergiu else "OK - %d arquivos iguais" % len(docs))
        sys.exit(1 if divergiu else 0)
    print("%d arquivos gravados em %s" % (len(docs), OUT))


if __name__ == "__main__":
    main()
