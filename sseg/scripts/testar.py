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
    # 12. programa SSEG 1.1: fluxos em dia com a política, relato sem dado de processo, gasto
    import painel, relato, gasto as gasto_m, claude_local
    gravado = json.load(open(os.path.join(RAIZ, "sseg", "workflow", "fluxos.json"), encoding="utf-8"))
    caso("fluxos.json igual ao que a política gera (rodar: python3 sseg/scripts/painel.py --fluxos)",
         gravado == painel.fluxos() and all(f["modelo"] and f["esforco"] for f in gravado["lista"]))
    caso("subagentes com nome completo de modelo (o atalho 'haiku' é o 4.5)",
         not [a for a in claude_local.subagentes(RAIZ) if a["aviso"]], str(claude_local.subagentes(RAIZ)))
    r = relato.montar("9.9", "erro no A00012345AA001 ao abrir Planta Baixa.pdf",
                      "✓ Pasta dos processos: E:\\X\\PROCESSOS\n✗ CIA 2.pdf\n", [r"E:\X\PROCESSOS"])
    caso("relato de bug sem código, pasta, CIA nem nome de arquivo",
         "A00012345" not in r and "PROCESSOS" not in r and "CIA 2" not in r and ".pdf" not in r.replace("<arquivo .pdf>", ""), r)
    with tempfile.TemporaryDirectory() as d:
        clone = os.path.join(d, "E", "SSEG")
        proj = os.path.join(d, "projects", __import__("re").sub(r"[^A-Za-z0-9]", "-", os.path.abspath(clone)))
        os.makedirs(os.path.join(proj, "s1", "subagents"))
        agora = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        msg = lambda i, mod, n: json.dumps({"type": "assistant", "timestamp": agora, "sessionId": "s1", "message": {  # noqa: E731
            "id": i, "model": mod, "usage": {"input_tokens": n, "output_tokens": n, "cache_read_input_tokens": n}}})
        open(os.path.join(proj, "s1.jsonl"), "w").write("\n".join([msg("a", "claude-sonnet-5-5", 10)] * 3))  # repetido: conta 1
        open(os.path.join(proj, "s1", "subagents", "x.jsonl"), "w").write(msg("b", "claude-haiku-5-5", 5))
        res = gasto_m.resumo(gasto_m.ler(clone, base=os.path.join(d, "projects")))
        caso("gasto: conta cada resposta uma vez e separa subagente",
             res["total"]["respostas"] == 2 and res["total"]["saida"] == 15
             and dict(res["subagentes"]).get("subagente", {}).get("saida") == 5, str(res["total"]))
    # 13. botão Sincronizar com o GitHub: commit + push num "GitHub" local; a CIA fica fora e na pasta
    import git_sinc
    with tempfile.TemporaryDirectory() as d:
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "CLAUDE_PROJECT_DIR"}
        sh = lambda *a, cwd=d: subprocess.run(a, cwd=cwd, capture_output=True, text=True, env=env)  # noqa: E731
        sh("git", "init", "-q", "--bare", "-b", "main", "origem.git")
        sh("git", "clone", "-q", "origem.git", "pc")
        pc = os.path.join(d, "pc")
        os.makedirs(os.path.join(pc, ".claude", "hooks"))
        import shutil
        shutil.copy(hook, os.path.join(pc, ".claude", "hooks"))
        for a in (("config", "user.email", "t@t"), ("config", "user.name", "t")):
            sh("git", *a, cwd=pc)
        open(os.path.join(pc, "leia.md"), "w").write("1")
        sh("git", "add", "-A", cwd=pc); sh("git", "commit", "-q", "-m", "base", cwd=pc); sh("git", "push", "-q", "origin", "HEAD:main", cwd=pc)
        open(os.path.join(pc, "leia.md"), "w").write("2")
        open(os.path.join(pc, "CIA 1.pdf"), "w").write("cia")
        old = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith("GIT_") or k == "CLAUDE_PROJECT_DIR"}
        try:
            info = git_sinc.conferir(pc, PY)
            linhas = git_sinc.sincronizar(pc, "teste do botão", PY)
        finally:
            os.environ.update(old)
        no_github = sh("git", "--git-dir", os.path.join(d, "origem.git"), "show", "main:leia.md").stdout
        arqs = sh("git", "--git-dir", os.path.join(d, "origem.git"), "ls-tree", "--name-only", "main").stdout
        caso("Sincronizar com o GitHub: envia o que mudou, CIA fica fora e na pasta",
             info["barrados"].get("CIA 1.pdf") and no_github == "2" and "CIA" not in arqs
             and os.path.exists(os.path.join(pc, "CIA 1.pdf")), str(linhas) + arqs)
    # 14. busca nas normas e no banco (SSEG.exe 1.2): banco primeiro, número não casa no meio de outro
    import busca
    r = busca.buscar(busca.carregar(RAIZ), 'extintor "5 m"')
    caso("busca: banco primeiro e \"5 m\" não acha \"15 m\"",
         r and r[0]["grupo"] == "banco" and not any("15 m" in x["texto"] and "5 m " not in x["texto"].replace("15 m", "") for x in r)
         and r[0]["copiar"].startswith("Deverá prever uma unidade extintora"), str([(x["grupo"], x["linha"]) for x in r[:5]]))
    r = busca.buscar(busca.carregar(RAIZ), "subsidiaria 10%")
    caso("busca: sem acento acha 5.2.2.1 no banco e na RT 01/2024",
         {x["grupo"] for x in r} >= {"banco", "comentada"} and any("rt-01-2024" in x["arquivo"] for x in r))
    print(f"testar.py: {oks} ok, {len(falhas)} falha(s)")
    for f in falhas:
        print("FALHA", f)
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
