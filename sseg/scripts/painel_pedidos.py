#!/usr/bin/env python3
"""Aplica no repositório os pedidos de troca de texto feitos no Painel SSEG.

Entrada: a pasta com os pedidos pendentes exportados do banco do painel (um JSON por pedido,
nome do arquivo = id do documento), como o ArtifactData grava com `out_dir`.

- Pedido "literal" (Editar num trecho): procura o texto de antes no arquivo indicado, tolerando
  quebra de linha e espaços; se aparecer exatamente uma vez, troca pelo texto de depois.
- Pedido "instrucoes" (texto integral das Instruções): troca o bloco entre os marcadores do
  espelho, se o bloco atual ainda for o que o pedido editou.
- Pedido "livre", ou troca que não casou: fica pendente, com a nota do motivo, para uma
  conversa resolver ("aplica o painel").

Depois faz commit só dos arquivos trocados (confere que nada de sseg/processos/ entrou) e, com
--push, envia. Grava <saida>/respostas.json: [{doc_id, data}] para a rotina atualizar a fila.

Uso:
    python3 painel_pedidos.py --pedidos <pasta> --saida <pasta> [--push] [--simular]
"""
import argparse, datetime, glob, json, os, re, subprocess, sys

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ESPELHO = "sseg/workflow/instrucoes-projeto-espelho.md"
MARC_INI = re.compile(r"<!--\s*=+\s*IN[IÍ]CIO DO TEXTO DO CAMPO.*?-->")
MARC_FIM = re.compile(r"<!--\s*=+\s*FIM DO TEXTO DO CAMPO.*?-->")


def git(*args, check=False):
    p = subprocess.run(["git", "-C", RAIZ, *args], capture_output=True, text=True)
    if check and p.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout.strip()


def padrao_tolerante(texto):
    """Regex que casa o texto mesmo com quebras de linha, recuo, '> ' e espaços diferentes."""
    partes = [re.escape(p) for p in texto.split()]
    return re.compile(r"(?:\s|>)+".join(partes))


def aplicar_literal(p):
    arq, antes, depois = p.get("arquivo", ""), p.get("antes", ""), p.get("depois", "")
    if not arq or not antes.strip():
        return None, "pedido sem arquivo ou sem o texto de antes"
    caminho = os.path.normpath(os.path.join(RAIZ, arq))
    if not caminho.startswith(RAIZ + os.sep) or "/processos/" in caminho.replace(os.sep, "/"):
        return None, f"arquivo fora do alcance: {arq}"
    if not os.path.exists(caminho):
        return None, f"arquivo não existe mais: {arq}"
    txt = open(caminho, encoding="utf-8").read()
    rx = padrao_tolerante(antes)
    achados = list(rx.finditer(txt))
    if len(achados) != 1:
        # frontmatter guarda a description entre aspas, com \" escapado
        esc = antes.replace('"', '\\"')
        if esc != antes:
            achados = list(padrao_tolerante(esc).finditer(txt))
            if len(achados) == 1:
                depois = depois.replace('"', '\\"')
    if len(achados) != 1:
        return None, ("o trecho de antes não foi achado no arquivo (ele mudou depois do pedido?)" if not achados
                      else f"o trecho de antes aparece {len(achados)} vezes; precisa de conversa para escolher")
    m = achados[0]
    novo = txt[:m.start()] + depois.strip() + txt[m.end():]
    return (caminho, novo), None


def aplicar_instrucoes(p):
    caminho = os.path.join(RAIZ, ESPELHO)
    txt = open(caminho, encoding="utf-8").read()
    a, b = MARC_INI.search(txt), MARC_FIM.search(txt)
    if not (a and b):
        return None, "espelho sem os marcadores INÍCIO/FIM"
    atual = txt[a.end():b.start()].strip()
    norm = lambda s: re.sub(r"\s+", " ", s or "").strip()
    if norm(atual) != norm(p.get("antes", "")):
        return None, "o texto das Instruções mudou depois do pedido; precisa de conversa para juntar as duas versões"
    novo = txt[:a.end()] + "\n\n" + p.get("depois", "").strip() + "\n\n" + txt[b.start():]
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    linha_hist = f"| {hoje} | Edição pelo Painel SSEG: {p.get('resumo') or 'texto integral editado'} Falta colar no campo do projeto |"
    # acrescenta a linha no fim da tabela de Histórico
    novo = re.sub(r"(\n\|[^\n]*\|\n)(?=\n## )", lambda m: m.group(1) + linha_hist + "\n", novo, count=1)
    return (caminho, novo), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pedidos", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--simular", action="store_true", help="não grava nem faz commit")
    a = ap.parse_args()
    os.makedirs(a.saida, exist_ok=True)
    agora = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    trocas, respostas, por_arquivo = {}, [], {}
    arquivos = sorted(glob.glob(os.path.join(a.pedidos, "**", "*.json"), recursive=True))
    for f in arquivos:
        try:
            p = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            continue
        p = p.get("data", p) if isinstance(p, dict) else {}
        if (p.get("status") or "pendente") != "pendente":
            continue
        doc_id = os.path.splitext(os.path.basename(f))[0]
        tipo = p.get("tipo") or "livre"
        if tipo == "literal":
            r, motivo = aplicar_literal(p)
        elif tipo == "instrucoes":
            r, motivo = aplicar_instrucoes(p)
        else:
            r, motivo = None, "pedido livre: precisa de conversa (“aplica o painel”)"
        if r:
            caminho, novo = r
            # dois pedidos no mesmo arquivo: aplica sobre o texto já trocado
            if caminho in trocas:
                p2 = dict(p)
                base = trocas[caminho]
                rx = padrao_tolerante(p.get("antes", ""))
                ach = list(rx.finditer(base))
                if len(ach) == 1 and tipo == "literal":
                    novo = base[:ach[0].start()] + p.get("depois", "").strip() + base[ach[0].end():]
                else:
                    respostas.append({"doc_id": doc_id, "data": {"nota": "conflita com outro pedido no mesmo arquivo; precisa de conversa", "triadoEm": agora}})
                    continue
            trocas[caminho] = novo
            por_arquivo.setdefault(caminho, []).append((doc_id, p))
        else:
            respostas.append({"doc_id": doc_id, "data": {"nota": motivo, "triadoEm": agora}})

    commit = ""
    if trocas and not a.simular:
        for caminho, novo in trocas.items():
            with open(caminho, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(novo)
        rels = [os.path.relpath(c, RAIZ) for c in trocas]
        git("add", "--", *rels, check=True)
        staged = git("diff", "--cached", "--name-only").splitlines()
        proibidos = [s for s in staged if s.startswith("sseg/processos/") or re.search(r"A000\d{5}[A-Z]{2}\d{3}", s)]
        extras = [s for s in staged if s not in rels]
        if proibidos or extras:
            git("reset", "-q")
            print(f"ERRO: staged inesperado {proibidos + extras}; nada foi commitado", file=sys.stderr)
            sys.exit(2)
        n = sum(len(v) for v in por_arquivo.values())
        git("commit", "-q", "-m", f"Painel SSEG: {n} pedido(s) de troca de texto aplicado(s)\n\n" +
            "\n".join(f"- {p.get('alvo','')} ({os.path.relpath(c, RAIZ)})" for c, v in por_arquivo.items() for _, p in v), check=True)
        commit = git("rev-parse", "--short", "HEAD")
        if a.push:
            git("pull", "--rebase", "-q")
            git("push", "-q")
    for caminho, lista in por_arquivo.items():
        relc = os.path.relpath(caminho, RAIZ)
        for doc_id, p in lista:
            extra = ""
            if relc.startswith("sseg/skills/"):
                extra = " A skill mudou no repositório: reinstalar na conta (sseg-sincronizar-skills) para valer no claude.ai."
            if relc == ESPELHO:
                extra = " Falta colar o texto novo no campo Instruções do projeto no claude.ai."
            txt = (f"Aplicado em {relc}" + (f", commit {commit}" if commit else " (simulação)") + "." + extra)
            respostas.append({"doc_id": doc_id, "data": {"status": "aplicado" if commit else "pendente",
                              "resposta": txt, "aplicadoEm": agora if commit else None}})
    json.dump(respostas, open(os.path.join(a.saida, "respostas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"pedidos_lidos": len(arquivos), "aplicados": sum(len(v) for v in por_arquivo.values()) if commit else 0,
                      "para_conversa": sum(1 for r in respostas if "nota" in r["data"]), "commit": commit}, ensure_ascii=False))


if __name__ == "__main__":
    main()
