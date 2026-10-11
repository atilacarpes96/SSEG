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
    for f in (glob.glob(os.path.join(AQUI, "*.py")) + glob.glob(os.path.join(RAIZ, ".claude", "hooks", "*.py"))
              + glob.glob(os.path.join(RAIZ, "sseg", "app", "*.py"))):
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
            atu = (r.get("atualizacoes") or {}).get("lista") or []
            caso("painel.py lê a aba Atualizações com prompt", bool(atu) and bool(atu[0]["prompt"]), str(atu[:1])[:300])
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
    # 8. enviar: planta nunca sai do PC
    sys.path.insert(0, AQUI)
    import enviar
    vai, fica = enviar.selecionar(["1.json", "1.pdf", "CIA 1.pdf", "CIA 1 textos.json", "api-123.json",
                                   "Planta Baixa Térreo.pdf", "prancha 01.pdf", "corte.dwg", "print.png"])
    caso("enviar deixa as plantas no PC", set(fica) == {"Planta Baixa Térreo.pdf", "prancha 01.pdf", "corte.dwg", "print.png"}
         and "CIA 1 textos.json" in vai, f"vai={vai} fica={fica}")
    # 9. programa SSEG: bloco do ~/.bashrc reescrito sem duplicar, resto do arquivo intacto
    sys.path.insert(0, os.path.join(RAIZ, "sseg", "app"))
    import instalar
    b = instalar.bloco_bashrc(instalar.bloco_bashrc("alias ll='ls -l'\n", [r"C:\P\bin"]), [r"D:\Novo"])
    caso("instalar: bloco do .bashrc", b.count(instalar.INICIO_BLOCO) == 1 and "/d/Novo:$PATH" in b
         and "/c/P" not in b and b.startswith("alias ll"), b)
    # 10. pre-commit do git (item 2 do plano do programa): barra em QUALQUER commit, num repo temporário
    if os.path.exists(hook) and not os.environ.get("SSEG_DENTRO_DO_GANCHO"):
        with tempfile.TemporaryDirectory() as d:
            # sem GIT_*: dentro do pre-commit real, GIT_INDEX_FILE apontaria para o índice do SSEG
            env = {k: v for k, v in os.environ.items()
                   if not k.startswith("GIT_") and k not in ("CLAUDE_PROJECT_DIR", "SSEG_BANCO_LIBERADO")}
            env["SSEG_DENTRO_DO_GANCHO"] = "1"

            def g(*a, **kw):
                return subprocess.run(["git", "-C", d, *a], capture_output=True, text=True, env={**env, **kw}).returncode
            os.makedirs(os.path.join(d, ".claude", "hooks"))
            os.makedirs(os.path.join(d, "sseg", "normas"))
            import shutil
            shutil.copy(hook, os.path.join(d, ".claude", "hooks"))
            open(os.path.join(d, ".gitignore"), "w").write("sseg/processos/\n")
            open(os.path.join(d, "sseg", "normas", "banco-notificacoes-padrao.md"), "w", encoding="utf-8").write(
                "- Deverá prever extintor.\n\n## Histórico de correções\n")
            g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
            g("add", "-A"); g("commit", "-q", "-m", "base")
            subprocess.run([PY, os.path.join(d, ".claude", "hooks", "sseg_hooks.py"), "instalar-git"],
                           capture_output=True, env={**env, "CLAUDE_PROJECT_DIR": d}, stdin=subprocess.DEVNULL)
            os.makedirs(os.path.join(d, "sseg", "processos"))
            open(os.path.join(d, "sseg", "processos", "x.md"), "w").write("x")
            g("add", "--force", "sseg/processos/x.md")
            caso("pre-commit barra arquivo forçado de sseg/processos", g("commit", "-q", "-m", "t1") != 0)
            g("restore", "--staged", "sseg/processos/x.md")
            open(os.path.join(d, "CIA 1.pdf"), "w").write("x")
            g("add", "CIA 1.pdf")
            caso("pre-commit barra CIA", g("commit", "-q", "-m", "t2") != 0)
            g("restore", "--staged", "CIA 1.pdf")
            banco_t = os.path.join(d, "sseg", "normas", "banco-notificacoes-padrao.md")
            open(banco_t, "w", encoding="utf-8").write("- Deve prever extintor.\n\n## Histórico de correções\n")
            g("add", "sseg/normas")
            caso("pre-commit barra modelo do banco alterado", g("commit", "-q", "-m", "t3") != 0)
            caso("pre-commit libera banco com SSEG_BANCO_LIBERADO=1",
                 g("commit", "-q", "-m", "t3b", SSEG_BANCO_LIBERADO="1") == 0)
            open(os.path.join(d, "leia.md"), "w").write("ok")
            g("add", "leia.md")
            caso("pre-commit deixa commit normal", g("commit", "-q", "-m", "t4") == 0)
    # 11. sincronizar processos PC <-> servidor (servidor de mentira numa pasta, sem SSH)
    import sincronizar as sc
    with tempfile.TemporaryDirectory() as d:
        ppci, clone_proc, srv = (os.path.join(d, x) for x in ("ppci", "clone_proc", "srv"))
        sc.PROC_CLONE, sc.RAIZ_SERVIDOR, sc.BASE = clone_proc, srv, os.path.join(clone_proc, ".sincronizacao.json")
        for x in (ppci, clone_proc, srv):
            os.makedirs(x)

        class Falso:
            def listar(self):
                return sc.manifesto(srv, srv)

            def receber(self, dados):
                return sc.desempacotar(dados, sc._no_servidor)

            def entregar(self, chaves):
                return sc.empacotar({k: sc._no_servidor(k) for k in chaves if os.path.isfile(sc._no_servidor(k))})

        def gravar(caminho, texto):
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            open(caminho, "w", encoding="utf-8").write(texto)
        cod = "A00012345AA001"
        gravar(os.path.join(ppci, cod, "1.json"), "pc1")
        gravar(os.path.join(ppci, cod, "CIA 1.pdf"), "cia")
        gravar(os.path.join(ppci, cod, "Planta baixa.pdf"), "planta")
        gravar(os.path.join(srv, cod + ".md"), "registro do servidor")
        r = sc.aplicar(ppci, Falso())
        caso("sincronizar: 1ª vez sobe JSON e CIA, desce o registro, planta fica",
             sorted(r["subiu"]) == [cod + "/1.json", cod + "/CIA 1.pdf"] and r["desceu"] == [cod + ".md"]
             and not os.path.exists(os.path.join(srv, cod, "Planta baixa.pdf"))
             and os.path.exists(os.path.join(clone_proc, cod + ".md")), str(r))
        gravar(os.path.join(srv, cod, "1.json"), "srv2")                  # só o servidor mudou
        gravar(os.path.join(ppci, cod, "CIA 1.pdf"), "cia pc")            # os dois mudaram
        gravar(os.path.join(srv, cod, "CIA 1.pdf"), "cia srv")
        p = sc.comparar(sc.manifesto(ppci, clone_proc), Falso().listar(), sc._ler_base())
        caso("sincronizar: plano desce o que mudou só no servidor e acusa o conflito",
             p["desce"] == [cod + "/1.json"] and p["conflito"] == [cod + "/CIA 1.pdf"] and not p["sobe"], str(p))
        r = sc.aplicar(ppci, Falso())
        caso("sincronizar: conflito sem escolha não sobrescreve nenhum lado",
             open(os.path.join(ppci, cod, "CIA 1.pdf")).read() == "cia pc"
             and open(os.path.join(srv, cod, "CIA 1.pdf")).read() == "cia srv"
             and open(os.path.join(ppci, cod, "1.json")).read() == "srv2", str(r))
        r = sc.aplicar(ppci, Falso(), {cod + "/CIA 1.pdf": "servidor"})
        caso("sincronizar: escolha 'servidor' resolve o conflito",
             open(os.path.join(ppci, cod, "CIA 1.pdf")).read() == "cia srv" and not r["conflito_pendente"], str(r))
        os.remove(os.path.join(ppci, cod, "1.json"))
        p = sc.comparar(sc.manifesto(ppci, clone_proc), Falso().listar(), sc._ler_base())
        caso("sincronizar: apagado no PC não volta nem some do servidor",
             p["apagado_pc"] == [cod + "/1.json"] and not p["desce"], str(p))
        caso("sincronizar: chave fora da lista é barrada",
             not sc.chave_valida(cod + "/Planta.pdf") and not sc.chave_valida("../x.json")
             and not sc.chave_valida(cod + "/../../x.json") and sc.chave_valida(cod + "/api-1.json"))
    print(f"testar.py: {oks} ok, {len(falhas)} falha(s)")
    for f in falhas:
        print("FALHA", f)
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
