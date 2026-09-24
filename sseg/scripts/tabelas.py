#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tabelas.py — resolve a tabela de exigencias a partir de dados/tabelas/ (indice + arquivos por grupo).

Substitui o roteamento de tabelas que existia no sseg.py, que so conhecia o Anexo B do
Decreto e nao lia as transcricoes. As DUAS fontes estao transcritas por inteiro:

  existente regularizada          -> rt05_p07_anexo_a   (RT 05 Parte 07/2025, Anexo A)
  a construir / nao regularizada  -> anexo_b_decreto    (Decreto 51.803/2014, Anexo B
                                                        consolidado ate o Dec. 57.967/2024)

Ate 02/09/2026 as duas fontes viviam inteiras em dados/tabelas_conferidas.json (48
tabelas), e cada consulta carregava o arquivo inteiro so para ler uma tabela. Em
08/09/2026 os dados foram fatiados em dados/tabelas/: um indice pequeno
(tab-00-indice.json, com o mapa "codigo de divisao -> arquivo/tabela/bloco") mais um
arquivo por fonte+grupo de ocupacao (tab-<fonte>-<grupo>.json) e por Tabela 5 / Tabela 7.
dados/tabelas_conferidas.json continua existindo, intacto, como registro historico e
fonte de conferencia - so nao e mais lido por este script.

O QUE ESTE SCRIPT FAZ
  - le so o indice primeiro, e abre so o(s) arquivo(s) de grupo necessario(s) para a
    consulta pedida - nunca o conjunto inteiro das duas fontes;
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
TABELAS_DIR = os.path.join(BASE, "dados", "tabelas")
INDICE_PATH = os.path.join(TABELAS_DIR, "tab-00-indice.json")
COLUNAS = ["Terrea", "H<=6", "6<H<=12", "12<H<=23", "23<H<=30", "H>30"]
FONTES = {"rt05": "rt05_p07_anexo_a", "b": "anexo_b_decreto"}


def sa(s):
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def carrega_indice():
    with open(INDICE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def carrega_arquivo(nome):
    """Abre UM arquivo de dados/tabelas/ pelo nome (ex.: 'tab-b-C.json'). So esse arquivo
    entra em memoria - nunca as duas fontes inteiras."""
    with open(os.path.join(TABELAS_DIR, nome), encoding="utf-8") as fh:
        return json.load(fh)


def arquivo_da_tabela(fonte, tabela):
    """Deriva o nome do arquivo a abrir a partir do CODIGO da tabela (ex.: '6F.3' -> grupo
    F -> 'tab-<fonte>-F.json'), sem precisar do indice. Vale para toda Tabela 6X."""
    m = re.match(r"^6([A-Za-z])", tabela or "")
    if not m:
        return None
    return "tab-%s-%s.json" % (fonte, m.group(1).upper())


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


def _partes_do_rotulo(rot):
    """Mesma normalizacao do algoritmo original de acha_divisao: separa rotulos agrupados
    por ',' ou ' e ', tira parenteses, normaliza acento/caixa/espaco."""
    partes = [sa(p).replace(" ", "") for p in re.split(r",| e ", rot)]
    return [re.sub(r"\(.*", "", p) for p in partes if p]


def acha_divisao(indice, fkey, divisao):
    """Devolve lista de (tabela, indice_do_bloco, rotulo_do_bloco) onde a divisao aparece
    na fonte fkey ('rt05' ou 'b'). Mesma logica de sempre - exato primeiro, parcial
    (substring/prefixo) so se nao houver exato - so que agora em duas camadas:

    1) Camada rapida: usa o mapa do indice (codigo -> arquivo/tabela/bloco), que ja tem,
       pronto, o mesmo codigo que o algoritmo antigo extraia de cada rotulo (splitando por
       ','/' e ' e cortando parenteses). Cobre o uso normal - abre so o arquivo do(s)
       bloco(s) encontrado(s) para pegar o rotulo completo a exibir.
    2) So se a camada rapida nao achar nada: repete o algoritmo antigo por inteiro,
       varrendo o rotulo cru (texto livre, sem cortar nada alem do parenteses) de cada
       tabela de todos os arquivos de grupo dessa fonte - para nao perder nenhuma busca
       que o script antigo, lendo o arquivo unico, conseguia responder.

    Limite conhecido (testado, nao afeta nenhum codigo de divisao real): o script antigo
    varria as DUAS fontes por inteiro em toda chamada, entao uma busca por um texto que nao
    e codigo de divisao podia, por acidente, "achar" um rotulo so porque esse texto aparece
    no meio da parte descritiva livre do rotulo (ex.: buscar a letra solta "a" tambem
    encontrava "M-3 – Centrais de Comunicação", por causa do "a" dentro de "Centrais" - nada
    a ver com a divisao M-3). Isso so acontece quando a camada rapida ja achou algo por
    codigo; nesse caso ela nao soma esses acertos incidentais de texto livre de OUTROS
    rotulos. Comparado exaustivamente contra o script antigo para os 48 codigos reais de
    divisao das duas fontes (todo bloco de toda tabela) e para toda consulta de rota/linha/
    notas: zero diferenca. A unica diferenca observada foi em buscas deliberadamente por
    letra solta sem hifen/numero (nunca um codigo de divisao valido)."""
    alvo = sa(divisao).replace(" ", "")
    mapa = indice.get("mapa", {}).get(fkey, {})

    exatos, parciais = [], []
    for codigo, entry in mapa.items():
        p = sa(codigo).replace(" ", "")
        if alvo == p:
            exatos.append((entry["arquivo"], entry["tabela"], entry["bloco"]))
        elif alvo in p or p.startswith(alvo):
            parciais.append((entry["arquivo"], entry["tabela"], entry["bloco"]))

    achados_local = exatos or parciais
    if achados_local:
        out, vistos = [], set()
        for arquivo, tab, bloco in achados_local:
            chave = (arquivo, tab, bloco)
            if chave in vistos:
                continue
            vistos.add(chave)
            rot = carrega_arquivo(arquivo)["tabelas"][tab]["divisoes"][bloco]
            out.append((tab, bloco, rot))
        return out

    # fallback completo (identico ao script antigo antes do fatiamento dos dados),
    # varrendo por arquivo de grupo dessa fonte - so acontece se a camada rapida nao
    # achou nada (ex.: busca por texto livre do rotulo, fora do codigo da divisao).
    exatos2, parciais2 = [], []
    padrao_arquivo = re.compile(r"^tab-%s-[A-Za-z]\.json$" % re.escape(fkey))
    for arquivo in indice.get("arquivos", []):
        if not padrao_arquivo.match(arquivo):
            continue
        obj = carrega_arquivo(arquivo)
        for tab, t in obj.get("tabelas", {}).items():
            for i, rot in enumerate(t["divisoes"]):
                partes = _partes_do_rotulo(rot)
                if alvo in partes:
                    exatos2.append((tab, i, rot))
                elif any(alvo in p or p.startswith(alvo) for p in partes):
                    parciais2.append((tab, i, rot))
    return exatos2 or parciais2


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


def cmd_rota(indice, a):
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
        t5_arquivo = "tab-%s-tabela5.json" % fkey
        if os.path.exists(os.path.join(TABELAS_DIR, t5_arquivo)):
            t5 = carrega_arquivo(t5_arquivo)
            print("     Colunas: %s" % " | ".join(t5["colunas"]))
    else:
        col = coluna_altura(a.altura)
        print("  -> TABELAS 6X (area > 750 m2 e/ou altura > 12 m), coluna de altura: %s" % col)
        if a.divisao:
            achou = acha_divisao(indice, fkey, a.divisao)
            if achou:
                for tab, i, rot in achou:
                    print("     divisao %s -> TABELA %s, bloco '%s'" % (a.divisao, tab, rot))
            else:
                print("     ?? divisao '%s' nao localizada nessa fonte." % a.divisao)
        else:
            print("     (informe --divisao para eu apontar a tabela)")
    if a.subsolo:
        print("  !! Ha subsolo ocupado -> ver tambem a TABELA 7 (exigencias ADICIONAIS, somam-se).")


def cmd_linha(indice, a):
    fkey = FONTES[a.fonte]
    arquivo = arquivo_da_tabela(a.fonte, a.tabela)
    t = carrega_arquivo(arquivo)["tabelas"].get(a.tabela) if arquivo and os.path.exists(os.path.join(TABELAS_DIR, arquivo)) else None
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


def cmd_divisao(indice, a):
    achou = acha_divisao(indice, a.fonte, a.divisao)
    if not achou:
        print("XX divisao '%s' nao localizada em %s" % (a.divisao, FONTES[a.fonte]))
        return
    for tab, i, rot in achou:
        print("TABELA %-6s bloco %d: %s" % (tab, i, rot))


def cmd_notas(indice, a):
    arquivo = arquivo_da_tabela(a.fonte, a.tabela)
    t = carrega_arquivo(arquivo)["tabelas"].get(a.tabela) if arquivo and os.path.exists(os.path.join(TABELAS_DIR, arquivo)) else None
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
    indice = carrega_indice()
    {"rota": cmd_rota, "linha": cmd_linha, "divisao": cmd_divisao, "notas": cmd_notas}[a.cmd](indice, a)


if __name__ == "__main__":
    main()
