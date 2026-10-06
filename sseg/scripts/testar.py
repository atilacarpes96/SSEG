#!/usr/bin/env python3
"""Testes de regressão dos scripts do SSEG — a "prova" antes do commit.

Roda em poucos segundos, sem rede e sem modelo. O hook de commit (.claude/hooks/sseg_hooks.py)
chama `python3 sseg/scripts/testar.py --rapido` e barra o commit se algum teste falhar.

Cada teste confere um comportamento que já quebrou ou que sustenta uma trava:
- todos os scripts compilam;
- os recortes de tabela batem com tabelas_conferidas.json;
- a Tabela 6I.1 (I-1, H<=6) devolve as 8 medidas com a nota 1 do Acesso de Viatura;
- o revisar-cia aponta os erros que todos os modelos deixaram passar no teste de 05/10/2026;
- o painel.py gera o retrato;
- o painel_pedidos.py casa um trecho quebrado em várias linhas;
- o hook do banco barra a alteração de um modelo validado.
"""
import json, os, py_compile, subprocess, sys, tempfile, glob

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.normpath(os.path.join(AQUI, "..", ".."))
FIX = os.path.join(AQUI, "testes")
PY = sys.executable
falhas, oks = [], 0


def caso(nome, cond, detalhe=""):
    global oks
    if cond:
        oks += 1
    else:
        falhas.append(f"{nome}: {detalhe}"[:600])


def rodar(args, **kw):
    p = subprocess.run([PY, *args], capture_output=True, text=True, timeout=120, cwd=RAIZ, **kw)
    return p.returncode, p.stdout + p.stderr


def main():
    # 1. compilação
    for f in glob.glob(os.path.join(AQUI, "*.py")) + glob.glob(os.path.join(RAIZ, ".claude", "hooks", "*.py")):
        try:
            py_compile.compile(f, doraise=True, cfile=os.path.join(tempfile.gettempdir(), "sseg_pyc_teste"))
        except py_compile.PyCompileError as e:
            caso(f"compila {os.path.basename(f)}", False, str(e))
        else:
            caso("compila", True)
    # 2. recortes x fonte
    rc, out = rodar([os.path.join(AQUI, "gerar_recortes.py"), "--conferir"])
    caso("recortes de tabela iguais à fonte", rc == 0, out[-300:])
    # 3. tabela 6I.1
    rc, out = rodar([os.path.join(AQUI, "tabelas.py"), "linha", "--fonte", "rt05", "--tabela", "6I.1", "--divisao", "I-1", "--coluna", "H<=6"])
    caso("tabela 6I.1 I-1 H<=6", rc == 0 and "TOTAL DE CELULAS MARCADAS: 8" in out and "X1" in out and "20 metros" in out, out[-300:])
    # 4. revisar-cia com os erros plantados
    rc, out = rodar([os.path.join(AQUI, "sseg.py"), "revisar-cia", "--cia", os.path.join(FIX, "cia-teste.txt"),
                     "--textos", os.path.join(FIX, "cia-erros-plantados.json"), "--json", os.path.join(FIX, "processo-1a-analise.json")])
    caso("revisar-cia: requisito de instalação", "requisito de instalação" in out, out[-400:])
    caso("revisar-cia: Decreto junto com RT", "artigo do Decreto junto com item de RT" in out, out[-400:])
    caso("revisar-cia: REITERO em 1ª análise", "REITERO numa 1ª análise" in out, out[-400:])
    caso("revisar-cia: quebra de linha no parágrafo", "quebra de linha dentro do paragrafo" in out, out[-400:])
    # 5. painel.py
    with tempfile.TemporaryDirectory() as d:
        rc, out = rodar([os.path.join(AQUI, "painel.py"), "--saida", d, "--crontab", os.path.join(d, "nada")])
        ok = rc == 0 and os.path.exists(os.path.join(d, "atual.json"))
        if ok:
            r = json.load(open(os.path.join(d, "atual.json"), encoding="utf-8"))
            ok = len(r["skills"]["lista"]) >= 1 and r["instrucoes"]["marcadores"]
        caso("painel.py gera o retrato", ok, out[-300:])
    # 6. painel_pedidos.py (simulação)
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "p"))
        json.dump({"tipo": "literal", "alvo": "teste", "status": "pendente",
                   "arquivo": "sseg/skills/ppci-revisao-cia/SKILL.md",
                   "antes": "Dar item como conferido só pelo `OK` do script.", "depois": "X"},
                  open(os.path.join(d, "p", "t1.json"), "w", encoding="utf-8"), ensure_ascii=False)
        rc, out = rodar([os.path.join(AQUI, "painel_pedidos.py"), "--pedidos", os.path.join(d, "p"), "--saida", d, "--simular"])
        resp = json.load(open(os.path.join(d, "respostas.json"), encoding="utf-8")) if os.path.exists(os.path.join(d, "respostas.json")) else []
        caso("painel_pedidos casa o trecho", rc == 0 and any("simulação" in (r["data"].get("resposta") or "") for r in resp), out[-300:])
    # 7. hook do banco
    hook = os.path.join(RAIZ, ".claude", "hooks", "sseg_hooks.py")
    if os.path.exists(hook):
        banco = open(os.path.join(RAIZ, "sseg", "normas", "banco-notificacoes-padrao.md"), encoding="utf-8").read()
        alvo = next(l for l in banco.splitlines() if l.startswith("- Deverá prever uma unidade extintora"))
        ev = {"tool_name": "Edit", "tool_input": {"file_path": os.path.join(RAIZ, "sseg/normas/banco-notificacoes-padrao.md"),
                                                    "old_string": alvo, "new_string": alvo.replace("Deverá", "Deve")}}
        p = subprocess.run([PY, hook, "banco"], input=json.dumps(ev), capture_output=True, text=True, timeout=30, cwd=RAIZ,
                           env={k: v for k, v in os.environ.items() if k != "SSEG_BANCO_LIBERADO"})
        caso("hook barra alteração de modelo do banco", '"deny"' in p.stdout, p.stdout[-300:])
        ev2 = {"tool_name": "Edit", "tool_input": {"file_path": ev["tool_input"]["file_path"], "old_string": alvo,
                                                     "new_string": alvo + "\n  > ⚠️ ressalva de teste"}}
        p = subprocess.run([PY, hook, "banco"], input=json.dumps(ev2), capture_output=True, text=True, timeout=30, cwd=RAIZ)
        caso("hook deixa anotar ressalva", '"deny"' not in p.stdout, p.stdout[-300:])
    print(f"testar.py: {oks} ok, {len(falhas)} falha(s)")
    for f in falhas:
        print("FALHA", f)
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
