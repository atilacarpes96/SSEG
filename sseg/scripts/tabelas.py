#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tabelas.py — resolve a tabela de exigencias a partir de dados/tabelas_conferidas.json.

Substitui o roteamento de tabelas que existia no sseg.py, que so conhecia o Anexo B do
Decreto e nao lia as transcricoes. Agora as DUAS fontes estao transcritas por inteiro:

  existente regularizada          -> rt05_p07_anexo_a   (RT 05 Parte 07/2025, Anexo A)
  a construir / nao regularizada  -> anexo_b_decreto    (Decreto 51.803/2014, Anexo B
                                                        consolidado ate o Dec. 57.967/2024)

O QUE ESTE SCRIPT FAZ
  - escolhe a fonte pela situacao de existencia;
  - roteia por area e altura (Tabela 5 x Tabelas 6X x Tabela 7);
  - acha o bloco da divisao e a coluna de altura, e devolve as celulas;
  - imprime o TEXTO das notas que aparecem nas celulas daquela coluna.

O QUE ESTE SCRIPT NAO FAZ
  - NAO aplica nota. A nota decide se a medida entra na contagem, e a contagem decide a
    definidora: isso e do analista. Por isso o total sai marcado como PROVISORIO e, no
    criterio (b) do item 5.1.2 da RT 01/2024, o pipeline PARA e pergunta ao usuario.

USO
  python3 tabelas.py rota    --situacao "existente regularizada" --area 3605.26 --altura 4.85
  python3 tabelas.py linha   --fonte rt05 --tabela 6I.1 --divisao "I-1" --coluna "H<=6"
  python3 tabelas.py divisao --fonte rt05 --divisao "I-1"        # em que tabela ela esta
  python3 tabelas.py notas   --fonte b    --tabela 6C
"""
import argparse, json, os, re, sys, unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(BASE, "dados", "tabelas_conferidas.json")
COLUNAS = ["Terrea", "H<=6", "6<H<=12", "12<H<=23", "23<H<=30", "H>30"]
FONTES = {"rt05": "rt05_p07_anexo_a", "b": "anexo_b_decreto"}


def sa(s):
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def carrega():
    with open(DADOS, encoding="utf-8") as fh:
        return json.load(fh)


def fonte_por_situacao(situacao):
    s = sa(situacao)
    if "regularizada" in s and "nao" not in s:
        return "rt05", "existente regularizada -> RT 05 Parte 07/2025, Anexo A"
    if s:
        return "b", "%s -> Decreto 51.803/2014, Anexo B" % situacao
    return None, None


def coluna_altura(h):
    if h is None:
        return None
    if h <= 0:
        return "Terrea"
    for lim, nome in ((6, "H<=6"), (12, "6<H<=12"), (23, "12<H<=23"), (30, "23<H<=30")):
        if h <= lim:
            return nome
    return "H>30"


def acha_divisao(d, fkey, divisao):
    """Devolve (tabela, indice_do_bloco, rotulo_do_bloco) onde a divisao aparece."""
    alvo = sa(divisao).replace(" ", "")
    exatos, parciais = [], []
    for tab, t in d[fkey].get("tabelas", {}).items():
        for i, rot in enumerate(t["divisoes"]):
            # o rotulo pode agrupar varias divisoes: "B-1 e B-2", "C-1, C-2 e C-3"
            partes = [sa(p).replace(" ", "") for p in re.split(r",| e ", rot)]
            partes = [re.sub(r"\(.*", "", p) for p in partes if p]
            if alvo in partes:
                exatos.append((tab, i, rot))
            elif any(alvo in p or p.startswith(alvo) for p in partes):
                parciais.append((tab, i, rot))
    return exatos or parciais


def notas_usadas(t, bloco, ci):
    """Numeros de nota que aparecem nas celulas daquela divisao/coluna."""
    nums = set()
    for cs in t["medidas"].values():
        c = cs[bloco * 6 + ci]
        for n in re.findall(r"\d+", c):
            nums.add(n)
    return sorted(nums, key=int)


def texto_das_notas(t, nums):
    out, capt = [], None
    for l in t.get("notas", []):
        m = re.match(r"^(\d+)\s*[-–—]\s*(.*)", l.strip())
        if m:
            capt = m.group(1)
            if capt in nums:
                out.append("  %s - %s" % (capt, m.group(2)))
        elif capt in nums and out and not re.match(r"^(NOTAS|[a-z] [-–—])", l.strip()):
            out[-1] += " " + l.strip()
        elif re.match(r"^NOTAS GERAIS", l.strip()):
            capt = None
    gerais = []
    pega = False
    for l in t.get("notas", []):
        if re.match(r"^NOTAS GERAIS", l.strip()):
            pega = True
            continue
        if pega and l.strip():
            gerais.append("  " + l.strip())
    return out, gerais


def cmd_rota(d, a):
    fkey, expl = fonte_por_situacao(a.situacao)
    print("FONTE")
    if not fkey:
        print("  ?? situacao de existencia nao informada - ela decide a fonte.")
        return
    print("  %s" % expl)
    print("\nROTEAMENTO")
    print("  Area a proteger: %s m2   |   Altura descendente: %s m" % (a.area, a.altura))
    print("  (RT 01/2024, item 5.1.3: roteia pela area total a ser protegida e pela altura descendente)")
    if a.area is None or a.altura is None:
        print("  ?? faltam area e/ou altura.")
        return
    if a.area <= 750 and a.altura <= 12:
        print("  -> TABELA 5 (area <= 750 m2 E altura <= 12 m).")
        print("     Atencao: as colunas da Tabela 5 sao POR GRUPO, nao por altura.")
        t5 = d[FONTES[fkey]].get("tabela_5")
        if t5:
            print("     Colunas: %s" % " | ".join(t5["colunas"]))
    else:
        col = coluna_altura(a.altura)
        print("  -> TABELAS 6X (area > 750 m2 e/ou altura > 12 m), coluna de altura: %s" % col)
        if a.divisao:
            achou = acha_divisao(d, FONTES[fkey], a.divisao)
            if achou:
                for tab, i, rot in achou:
                    print("     divisao %s -> TABELA %s, bloco '%s'" % (a.divisao, tab, rot))
            else:
                print("     ?? divisao '%s' nao localizada nessa fonte." % a.divisao)
        else:
            print("     (informe --divisao para eu apontar a tabela)")
    if a.subsolo:
        print("  !! Ha subsolo ocupado -> ver tambem a TABELA 7 (exigencias ADICIONAIS, somam-se).")


def cmd_linha(d, a):
    fkey = FONTES[a.fonte]
    t = d[fkey]["tabelas"].get(a.tabela)
    if not t:
        print("XX tabela %s nao existe em %s" % (a.tabela, fkey))
        return
    idx = [i for i, r in enumerate(t["divisoes"]) if sa(a.divisao).replace(" ", "") in sa(r).replace(" ", "")]
    if not idx:
        print("XX divisao '%s' nao esta na tabela %s. Blocos: %s" % (a.divisao, a.tabela, t["divisoes"]))
        return
    bloco = idx[0]
    ci = COLUNAS.index(a.coluna)
    exig, nao = [], []
    for m, cs in t["medidas"].items():
        c = cs[bloco * 6 + ci]
        (nao if c == "-" else exig).append((m, c))
    print("%s / %s / %s" % (a.tabela, t["divisoes"][bloco], a.coluna))
    print(t["titulo"])
    print()
    for m, c in exig:
        print("  X  %-52s %s" % (m, c if c != "X" else ""))
    for m, c in nao:
        print("  -  %s" % m)
    print()
    print("  TOTAL DE CELULAS MARCADAS: %d  <-- PROVISORIO" % len(exig))
    nums = notas_usadas(t, bloco, ci)
    if nums:
        esp, ger = texto_das_notas(t, nums)
        print("\n  NOTAS QUE APARECEM NESTA COLUNA (%s):" % ", ".join(nums))
        for l in esp:
            print(l)
        if ger:
            print("\n  NOTAS GERAIS DA TABELA:")
            for l in ger:
                print(l)
        print("\n  !! A NOTA NAO SE APLICA SOZINHA. Nota que restringe a celula a outra divisao")
        print("     EXCLUI a medida da contagem; nota que condiciona a um fato do caso concreto")
        print("     MANTEM a medida, mas a condicao precisa ser verificada no projeto.")
        print("     No criterio (b) do item 5.1.2 da RT 01/2024: PARAR e perguntar ao usuario.")


def cmd_divisao(d, a):
    achou = acha_divisao(d, FONTES[a.fonte], a.divisao)
    if not achou:
        print("XX divisao '%s' nao localizada em %s" % (a.divisao, FONTES[a.fonte]))
        return
    for tab, i, rot in achou:
        print("TABELA %-6s bloco %d: %s" % (tab, i, rot))


def cmd_notas(d, a):
    t = d[FONTES[a.fonte]]["tabelas"].get(a.tabela)
    if not t:
        print("XX tabela nao encontrada")
        return
    print(t["titulo"])
    for l in t.get("notas", []):
        print("  " + l)


def main():
    ap = argparse.ArgumentParser(description="Resolve a tabela de exigencias (as duas fontes).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("rota")
    p.add_argument("--situacao", required=True)
    p.add_argument("--area", type=float)
    p.add_argument("--altura", type=float)
    p.add_argument("--divisao")
    p.add_argument("--subsolo", action="store_true")

    p = sub.add_parser("linha")
    p.add_argument("--fonte", choices=list(FONTES), required=True)
    p.add_argument("--tabela", required=True)
    p.add_argument("--divisao", required=True)
    p.add_argument("--coluna", choices=COLUNAS, required=True)

    p = sub.add_parser("divisao")
    p.add_argument("--fonte", choices=list(FONTES), required=True)
    p.add_argument("--divisao", required=True)

    p = sub.add_parser("notas")
    p.add_argument("--fonte", choices=list(FONTES), required=True)
    p.add_argument("--tabela", required=True)

    a = ap.parse_args()
    d = carrega()
    {"rota": cmd_rota, "linha": cmd_linha, "divisao": cmd_divisao, "notas": cmd_notas}[a.cmd](d, a)


if __name__ == "__main__":
    main()
