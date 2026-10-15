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
import base64, json, os, py_compile, subprocess, sys, tempfile, glob

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
        p = subprocess.run([PY, hook, "banco"], input=json.dumps(ev), capture_output=True, text=True, encoding="utf-8", timeout=30, cwd=RAIZ,
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
    # 11b. porta do servidor (SSEG multiusuário, 2.2.0): cada analista só vê os processos dele
    import porta as pt
    with tempfile.TemporaryDirectory() as d:
        raiz, acesso, chaves = os.path.join(d, "proc"), os.path.join(d, "acesso.json"), os.path.join(d, "authorized_keys")
        os.makedirs(raiz)
        open(chaves, "w").write("ssh-ed25519 AAAAadmin atila@casa\n")
        k_fulano = "ssh-ed25519 " + "A" * 68
        P = lambda nome=None: pt.Porta(nome, raiz=raiz, acesso=acesso, chaves=chaves, escala=os.path.join(d, "esc.json"), relatos=os.path.join(d, "rel"))
        adm = P()
        adm.autorizar({"analista": "Sgt Fulano", "chave": k_fulano + " fulano@pc"}, "SSEG/sseg/scripts/porta.py")
        linhas = open(chaves).read().splitlines()
        def g(caminho, texto):
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            open(caminho, "w", encoding="utf-8").write(texto)
        g(os.path.join(raiz, "A00000001AA001", "1.json"), "antigo do admin")
        g(os.path.join(raiz, "A00000002AA001", "distribuicao.json"), json.dumps({"analista": "Sgt Fulano"}))
        g(os.path.join(raiz, "A00000002AA001", "1.json"), "do fulano")
        ful = P("Sgt Fulano")
        caso("porta: chave do analista só roda a porta, com o nome dele; a do admin fica igual",
             linhas[0] == "ssh-ed25519 AAAAadmin atila@casa" and len(linhas) == 2 and linhas[1].startswith('command="python3 SSEG/sseg/scripts/porta.py --analista \'Sgt Fulano\'",restrict ssh-ed25519 ')
             and ful.quem_sou() == {"analista": "Sgt Fulano", "papel": "analista"}, str(linhas))
        caso("porta: cada um lista só o seu (pasta antiga é do admin; planilha manda)",
             set(ful.listar()) == {"A00000002AA001/1.json", "A00000002AA001/distribuicao.json"}
             and ful.meus() == ["A00000002AA001"] and adm.meus() == ["A00000001AA001"]
             and set(adm.listar()) == {"A00000001AA001/1.json"}, str((ful.listar(), adm.listar())))
        pacote = sc.empacotar({"A00000001AA001/1.json": os.path.join(d, "acesso.json"),   # de outro: recusa
                               "A00000002AA001/distribuicao.json": os.path.join(d, "acesso.json"),  # só o servidor grava
                               "A00000003AA001/CIA 1.pdf": os.path.join(raiz, "A00000002AA001", "1.json")})  # novo: vira dele
        feitas = ful.receber(pacote)
        caso("porta: recebe só o que é dele, processo novo passa a ser dele, distribuicao.json não sobe",
             feitas == ["A00000003AA001/CIA 1.pdf"] and open(os.path.join(raiz, "A00000001AA001", "1.json")).read() == "antigo do admin"
             and "A00000003AA001/CIA 1.pdf" in P("Sgt Fulano").listar() and "A00000003AA001/CIA 1.pdf" not in adm.listar(), str(feitas))
        import tarfile as _tf
        import io as _io
        nomes = _tf.open(fileobj=_io.BytesIO(ful.entregar(["A00000001AA001/1.json", "A00000002AA001/1.json"]))).getnames()
        recusas = []
        for f in (lambda: P("Sgt Estranho"), lambda: ful.analistas(), lambda: ful.autorizar({"analista": "X Y", "chave": k_fulano}, "p"),
                  lambda: adm.autorizar({"analista": "Sd Outro", "chave": "ssh-ed25519 curta"}, "p"),
                  lambda: adm.autorizar({"analista": "Sd Outro", "chave": k_fulano}, "p")):
            try:
                f()
            except SystemExit:
                recusas.append(1)
        caso("porta: entrega só o dele; recusa nome fora do cadastro, ação de admin, chave inválida ou de outro",
             nomes == ["A00000002AA001/1.json"] and len(recusas) == 5, str((nomes, recusas)))
        adm.atribuir("A00000001AA001", "sgt fulano")
        adm.revogar("Sgt Fulano", "p")
        caso("porta: admin atribui processo e revoga (a linha do analista sai, a do admin fica)",
             pt.responsavel(raiz, "A00000001AA001", pt.ler_acesso(acesso)) == "Sgt Fulano"
             and open(chaves).read().splitlines() == ["ssh-ed25519 AAAAadmin atila@casa"])
        caso("porta: pedido do analista vem do SSH_ORIGINAL_COMMAND; sem ele, nada; nomes do sincronizar valem",
             pt.pedido(["--analista", "Sgt Fulano"], "python3 SSEG/sseg/scripts/porta.py relato 2026-1") == ("Sgt Fulano", ["relato", "2026-1"])
             and pt.pedido(["--analista", "Sgt Fulano"], "bash -i") == ("Sgt Fulano", [])
             and pt.pedido(["listar"]) == (None, ["listar"])
             and json.loads(pt.executar(adm, ["remoto-listar"], lambda: b"", "p")) == adm.listar())
    # 11c. pedido de acesso (2.2.1): mensagem pronta para o servidor 24/7; o "Liberar acesso" lê a mensagem inteira
    sys.path.insert(0, os.path.join(AQUI, "..", "app"))
    import acesso as _ac
    _pub = _ac.chave_publica
    _ac.chave_publica = lambda: "ssh-ed25519 " + "B" * 68 + " sseg"
    try:
        _m = _ac.mensagem_acesso("Sgt Magalhães")
        caso("acesso: mensagem traz o comando da porta e o código; ler_codigo acha o código nela",
             "porta.py autorizar <<'FIM'" in _m and _ac.ler_codigo(_m) == {"analista": "Sgt Magalhães", "chave": "ssh-ed25519 " + "B" * 68}
             and _ac.ler_codigo(_m.replace(chr(10), " ")) == _ac.ler_codigo(_m), _m[-200:])
    finally:
        _ac.chave_publica = _pub
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
    # 15. janela do processo (SSEG.exe 2.1): registro, checklist + Anexo L, leitura do stream do chat
    import analise_registro as reg
    import processo, chat
    with tempfile.TemporaryDirectory() as tmp:
        pasta = os.path.join(tmp, "A00012345AA001")
        reg.pendencia(pasta, "falta ver a fita reflexiva")
        e = reg.exigencia(pasta, "- Deverá ...", "Saída de Emergência", "RT 11/2016, item 5.4.2")
        d = reg.ler(pasta)
        caso("analise.json: exigência do Claude entra só como rascunho",
             e["rascunho"] and not e["final"] and not reg.texto_cia(d), str(e))
        reg.atualizar(pasta, "exigencias", e["id"], final="- Deverá (editado)")
        caso("analise.json: CIA lê só o texto final", [x["final"] for x in reg.texto_cia(reg.ler(pasta))] == ["- Deverá (editado)"])
        # 2.1.13: caixa marcada à mão (quando a planilha não tem o processo)
        reg.situacao(pasta, distribuido="2026-10-01", concluido="2026-10-09", resultado="cia", ct="2026-10-15")
        d = reg.ler(pasta)
        marcou = (d["distribuido"], d["concluido"], d["resultado"], d["ct"]) == ("2026-10-01", "2026-10-09", "CIA", "2026-10-15")
        reg.situacao(pasta, concluido="", ct="")
        d = reg.ler(pasta)
        limpou = "concluido" not in d and "ct" not in d and d["distribuido"] == "2026-10-01"
        recusa = []
        for ruim in ({"resultado": "aprovado"}, {"distribuido": "01/10/2026"}, {"prazo": "2026-10-20"}):
            try:
                reg.situacao(pasta, **ruim)
            except ValueError:
                recusa.append(ruim)
        caso("analise.json: distribuído, concluído, resultado e CT à mão (vazio apaga, inválido recusado)",
             marcou and limpou and len(recusa) == 3 and reg.ler(pasta)["exigencias"], str(d))
        json.dump({"especSeguranca": {"laudo": {"txtClob": "laudo"}, "medidas": [
            {"tipo": {"nome": "Sinalização de Emergência"}, "norma": {"nome": "RT 12"}, "inviabilidade": "NAO_POSSUI"},
            {"tipo": {"nome": "Saída de Emergência"}, "norma": {"nome": "RT 11"}, "inviabilidade": "POSSUI_PARCIAL"},
            {"tipo": {"nome": "Hidrante Urbano"}, "norma": {"nome": "RT 16"}, "inviabilidade": "NAO_POSSUI"}]}},
            open(os.path.join(pasta, "api-1.json"), "w", encoding="utf-8"))
        m = processo.montar(RAIZ, pasta)
        nomes = [x["nome"] for x in m["medidas"]]
        sai = m["medidas"][1]
        caso("janela do processo: 16 passos, medidas na ordem do SOL, Anexo L e compensatória",
             len(m["passos"]) == 16 and nomes == ["Sinalização de Emergência", "Saída de Emergência", "Hidrante Urbano"]
             and m["medidas"][0]["tabela"] == "L.2" and m["medidas"][0]["nota"] and sai["tabela"] == "L.1"
             and any(i.startswith("Planta: i)") for i in sai["itens"]) and sai["itens"][-1].startswith("Compensatórias")
             and m["medidas"][2]["itens"] == ["Memorial descritivo", "Planta: localização"], str([(x["nome"], x["tabela"], len(x["itens"])) for x in m["medidas"]]))
        caso("janela do processo: laudo do SOL sai sem HTML (<p>, &nbsp;)",
             processo.texto_do_html("<p>Rampas:</p><p>&nbsp;</p><p>A edifica&ccedil;&atilde;o</p>") == "Rampas:\n\nA edificação")
        evs = []
        c = chat.Conversa(RAIZ, pasta, "A00012345AA001", {"modelo": "claude-sonnet-5-5", "esforco": "high"}, "claude",
                          [{"nome": "localizador-normas", "modelo": "claude-haiku-5-5"}], evs.append, reg,
                          {"ler": lambda: {"u": 0.20, "resets": 9}, "gravar": lambda v: None})
        for linha in [{"type": "system", "subtype": "init", "session_id": "s1"},
                      {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "t1", "name": "Task", "input": {"subagent_type": "localizador-normas", "description": "RT 11"}}]}},
                      {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1"}]}},
                      {"type": "rate_limit_event", "rate_limit_info": {"unifiedWindows": {"five_hour": {"utilization": 0.23, "resetsAt": 9}}}},
                      {"type": "assistant", "message": {"content": [{"type": "text", "text": "ok"}]}},
                      {"type": "result", "usage": {"input_tokens": 5, "output_tokens": 7}}]:
            c._evento(linha)
        tipos = [x["t"] for x in evs]
        caso("chat: subagente vira caranguejo (início e fim), cota por processo e sessão guardada",
             tipos == ["sub_ini", "sub_fim", "cota", "texto", "fim"] and evs[0]["modelo"] == "claude-haiku-5-5"
             and abs(evs[2]["processo"] - 3.0) < 0.01 and reg.ler(pasta)["chat"]["sessao"] == "s1", str(evs))
    import re as _re
    blocos = _re.findall(r"```(sseg-[a-z]+)\n(.*?)\n```", chat.GUIA_VISUAL, _re.S)
    def _json_ok(b):
        try:
            json.loads(b)
            return True
        except ValueError:
            return False
    caso("chat: os 6 blocos visuais ensinados ao Claude são JSON válido",
         {t for t, _ in blocos} == {"sseg-status", "sseg-dados", "sseg-definidora", "sseg-perguntas", "sseg-exigencia", "sseg-norma"}
         and all(_json_ok(b) for _, b in blocos), str([t for t, b in blocos if not _json_ok(b)]))
    # 15b. planilha "Distribuição Análise" → <código>/distribuicao.json → estado na caixa (2.1.13)
    import distribuicao as dist, datetime as _dt, io, zipfile as _zp
    import api as _api
    def _xlsx(linhas):
        def cel(ref, v):
            return '<c r="%s" t="inlineStr"><is><t>%s</t></is></c>' % (ref, v) if isinstance(v, str) else '<c r="%s"><v>%s</v></c>' % (ref, v)
        rows = "".join('<row r="%d">%s</row>' % (i + 1, "".join(cel(chr(65 + j) + str(i + 1), v) for j, v in enumerate(r) if v != ""))
                       for i, r in enumerate(linhas))
        ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
        b = io.BytesIO()
        with _zp.ZipFile(b, "w") as z:
            z.writestr("xl/workbook.xml", '<workbook %s><sheets><sheet name="CARPES" sheetId="1" r:id="rId1"/><sheet name="ANÁLISE" sheetId="2" r:id="rId2"/></sheets></workbook>' % ns)
            z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Target="worksheets/sheet2.xml"/></Relationships>')
            z.writestr("xl/worksheets/sheet1.xml", '<worksheet %s><sheetData/></worksheet>' % ns)
            z.writestr("xl/worksheets/sheet2.xml", '<worksheet %s><sheetData>%s</sheetData></worksheet>' % (ns, rows))
        return b.getvalue()
    X = _xlsx([["LICENCIAMENTO", "METRAGEM", "OCUPAÇÃO", "ANÁLISE/ REAN", "PROTOCOLO", "DIAS", "DISTRIBUIÇÃO", "ANALISTA", "DIAS EM ANÁLISE", "DATA CONCLUSÃO", "CIA / CA"],
               ["A00011111AA001", 500, "A-2", "ANÁLISE", 46290, "", 46292, "ÁTILA CARPES", "", 46296, "CIA"],
               ["A00011111AA001", 500, "A-2", "2º", 46300, "", 46301, "ÁTILA CARPES", "", "", ""],  # reanálise: vale a de baixo
               ["A00022222AA001", 900, "F-6", "ANÁLISE", 46300, "", "", "ÁTILA CARPES", "", "", ""],  # na fila
               ["A00033333AA001", 900, "I-1", "ANÁLISE", 46200, "", 46201, "ÁTILA CARPES", "", 46215, "CA"],  # concluída há mais de 30 dias
               ["A00044444AA001", 900, "D-1", "ANÁLISE", 46300, "", 46301, "OUTRO ANALISTA", "", "", ""]])
    regs = dist.registros(dist.linhas_da_aba(X), "carpes")
    por = {r["codigo"]: r for r in regs}
    caso("distribuicao: aba ANÁLISE (não a do analista), datas do Excel, só o analista, reanálise vale a última",
         set(por) == {"A00011111AA001", "A00022222AA001", "A00033333AA001"} and por["A00011111AA001"]["tipo"] == "2º"
         and por["A00011111AA001"]["distribuido"] == "2026-10-06" and por["A00022222AA001"]["distribuido"] == ""
         and por["A00033333AA001"]["resultado"] == "CA", str(regs))
    with tempfile.TemporaryDirectory() as tmp:
        c1 = dist.gravar(tmp, regs, 30, _dt.date(2026, 10, 13))
        c2 = dist.gravar(tmp, regs, 30, _dt.date(2026, 10, 13))
        caso("distribuicao: cria pasta do que está na fila ou na caixa, não da conclusão antiga; repetir não regrava",
             sorted(c1["criadas"]) == ["A00011111AA001", "A00022222AA001"] and not os.path.exists(os.path.join(tmp, "A00033333AA001"))
             and c2["iguais"] == 2 and not c2["criadas"] and not c2["atualizadas"], str(c1) + str(c2))
    todos = {r["codigo"]: r for r in dist.registros(dist.linhas_da_aba(X), None, ["Sd Carpes", "Sgt Magalhães", "Sd Fulano"])}
    caso("distribuicao: sem analista vêm todos; nome da planilha vira o da escala quando um só casa",
         set(todos) == {"A00011111AA001", "A00022222AA001", "A00033333AA001", "A00044444AA001"}
         and todos["A00011111AA001"]["analista"] == "Sd Carpes" and todos["A00044444AA001"]["analista"] == "OUTRO ANALISTA"
         and todos["A00011111AA001"]["analista_planilha"] == "ÁTILA CARPES", str(todos))
    with tempfile.TemporaryDirectory() as tmp:
        dist.gravar(tmp, [todos["A00011111AA001"]], 30, _dt.date(2026, 10, 13))
        open(os.path.join(tmp, "A00011111AA001", "CIA 1.pdf"), "w").write("cia do Carpes")
        passou = dict(todos["A00011111AA001"], analista="Sgt Magalhães")
        c = dist.gravar(tmp, [passou], 30, _dt.date(2026, 10, 14))
        dj = json.load(open(os.path.join(tmp, "A00011111AA001", "distribuicao.json"), encoding="utf-8"))
        import porta as _pt
        ac = {"admin": "Sd Carpes", "analistas": {"Sgt Magalhães": {"chave": "x"}}}
        caso("distribuicao: processo que troca de analista fica na mesma pasta, com quem já passou, e vai ao novo responsável",
             c["atualizadas"] == ["A00011111AA001"] and dj["analista"] == "Sgt Magalhães" and dj["analistas_anteriores"] == ["Sd Carpes"]
             and _pt.responsavel(tmp, "A00011111AA001", ac) == "Sgt Magalhães"
             and os.path.exists(os.path.join(tmp, "A00011111AA001", "CIA 1.pdf")), str(dj))
    E = lambda dd, rr, h: _api.estado_caixa(dd, rr, 10, _dt.date(*h))
    e1 = E({"codigo": "x", "distribuido": "2026-10-06"}, {}, (2026, 10, 13))
    e2 = E({"codigo": "x", "distribuido": "2026-10-01"}, {}, (2026, 10, 13))
    e3 = E({"codigo": "x", "distribuido": "2026-10-01", "concluido": "2026-10-09", "resultado": "CIA"}, {"concluido": "2026-10-20"}, (2026, 10, 13))
    e4 = E({"codigo": "x"}, {}, (2026, 10, 13))
    e5 = E({}, {"distribuido": "2026-09-20", "concluido": "2026-10-05"}, (2026, 10, 13))
    e6 = E({}, {}, (2026, 10, 13))
    caso("caixa: 10 dias corridos da distribuição; planilha manda no manual; fila sem prazo; manual fora do prazo",
         (e1["estado"], e1["vence"], e1["no_prazo"]) == ("caixa", "2026-10-16", True) and (e2["estado"], e2["no_prazo"]) == ("caixa", False)
         and (e3["estado"], e3["concluido"], e3["dias"], e3["no_prazo"]) == ("concluido", "2026-10-09", 8, True)
         and (e4["estado"], e4["vence"]) == ("fila", "") and (e5["fonte"], e5["dias"], e5["no_prazo"]) == ("manual", 15, False)
         and e6["estado"] == "sem", str([e1, e2, e3, e4, e5, e6]))
    # 15b2. CT e recursos (2.3.0): planilhas → <código>/ct.json e recurso.json; a porta mostra a pasta ao ME
    import ct_recursos as ctr
    CT = [["", "", "", ""], ["Cadastro", "", "", "", "", "", "", "Agendamento", "", "", "", "", "Minuta", "", "Chefe da SSeg", ""],
          ["PPCI", "Documento", "", "Fact", "Data Solicitação", "Nome", "QSO", "ME", "Objeto da CT", "Data", "Hora", "Modalidade", "Finalizado", "", "Data da Inclusão no Sistema", "Finalizado"],
          ["A00011111AA001", "CT SOL", "", "F1", "46290", "x", "x", "2° Sgt Fulano", "CT", "46300", "0.375", "Virtual", "0", "", "", "0"],    # marcada
          ["A00022222AA001", "CT SOL", "", "F2", "46290", "x", "x", "Sd Carpes", "CT", "46301", "14:00", "Presencial", "1", "", "", "0"],  # chefia
          ["A00033333AA001", "CT SOL", "", "F3", "46290", "x", "x", "Sd Carpes", "CT", "46301", "14:00", "Presencial", "1", "", "46302", "1"],  # ok: sai
          ["-", "CT SOL", "", "F4", "46290", "x", "x", "Sd Carpes", "CT", "", "", "", "0", "", "", "0"]]  # sem código: fora
    REC = [["", ""], ["Cadastro", "", "", "", "", "", "", "", "Minuta", "", "", "", "", "Solução", "", "", "", "Finalização", ""],
           ["", "PPCI", "Documento", "Data para Distribuição", "Município", "Pelotão", "Vistoriantes", "", "ME Rascunho", "Objeto do Recurso", "Data", "Finalizado", "", "ME Resp.", "Decisâo", "Data", "", "Data inclusão sistema", "Finalizado"],
           ["1", "A00022222AA001 ", "Rec 1ª - Análise", "46304", "Lajeado", "", "", "", "Sd Carpes", "rec", "", "0.0", "", "Cap X", "", "", "", "", "0.0"],
           ["2", "A00044444AA001", "Rec 2ª - Análise", "46300", "Colinas", "", "", "", "2º Sgt Fulano", "rec", "46301", "1.0", "", "Cap Y", "", "", "", "", "0.0"],
           ["3", "A00055555AA001", "Rec 1ª - Análise", "46200", "x", "", "", "", "Sd Carpes", "rec", "46201", "1.0", "", "Cap Y", "Deferido", "46210", "", "46210", "1.0"]]
    kn = ["Sd Carpes", "Sgt Fulano"]
    cts, recs = ctr.ler_ct(CT, kn), ctr.ler_recursos(REC, kn)
    caso("ct_recursos: CT marcada (minuta) e com a chefia; finalizada pela chefia sai; nome e hora arrumados",
         set(cts) == {"A00011111AA001", "A00022222AA001"} and cts["A00011111AA001"][0]["estado"] == "minuta"
         and cts["A00011111AA001"][0]["analista"] == "Sgt Fulano" and cts["A00011111AA001"][0]["hora"] == "09:00"
         and cts["A00022222AA001"][0]["estado"] == "chefia" and cts["A00011111AA001"][0]["data"] == "2026-10-05", str(cts))
    caso("ct_recursos: recurso para redigir e com a chefia; finalizado sai; código com espaço vale",
         set(recs) == {"A00022222AA001", "A00044444AA001"} and recs["A00022222AA001"][0]["estado"] == "minuta"
         and recs["A00044444AA001"][0]["estado"] == "chefia" and recs["A00044444AA001"][0]["tipo"] == "Rec 2ª - Análise", str(recs))
    with tempfile.TemporaryDirectory() as tmp:
        ctr.gravar(tmp, "ct", cts)
        c2 = ctr.gravar(tmp, "ct", {"A00011111AA001": cts["A00011111AA001"]})  # a do 22222 foi finalizada
        zerado = json.load(open(os.path.join(tmp, "A00022222AA001", "ct.json"), encoding="utf-8"))
        import porta as _pt2
        os.makedirs(os.path.join(tmp, "A00044444AA001"))
        ctr.gravar(tmp, "recurso", recs)
        json.dump({"analista": "Sd Carpes"}, open(os.path.join(tmp, "A00044444AA001", "distribuicao.json"), "w", encoding="utf-8"))
        ac = {"admin": "Sd Carpes", "analistas": {"Sgt Fulano": {"chave": "x"}}}
        open(os.path.join(tmp, "acesso.json"), "w", encoding="utf-8").write(json.dumps(ac))
        ful = _pt2.Porta("Sgt Fulano", raiz=tmp, acesso=os.path.join(tmp, "acesso.json"))
        caso("ct_recursos: o que foi finalizado vira {itens: []} (desce ao PC); o ME do recurso vê a pasta de outro analista",
             c2 == {"gravados": 0, "zerados": 1, "iguais": 1} and zerado["itens"] == []
             and "A00044444AA001" in ful.meus() and "A00011111AA001" in ful.meus() and "A00022222AA001" not in ful.meus(), str((c2, ful.meus())))
    # 15b3. Quadro da seção (2.3.0): todos criam e pegam; mover, editar e excluir só quem criou, pegou ou o admin
    with tempfile.TemporaryDirectory() as tmp:
        ac = os.path.join(tmp, "acesso.json")
        open(ac, "w", encoding="utf-8").write(json.dumps({"admin": "Sd Carpes", "analistas": {"Sgt Fulano": {"chave": "x"}, "Sd Beltrano": {"chave": "y"}}}))
        Q = lambda n=None: _pt2.Porta(n, raiz=tmp, acesso=ac, quadro=os.path.join(tmp, "q"))
        ful, bel, adm = Q("Sgt Fulano"), Q("Sd Beltrano"), Q()
        c = ful.quadro_mexer({"acao": "adicionar", "args": ["Responder ofício da prefeitura"]})
        barrou = []
        for f in (lambda: bel.quadro_mexer({"acao": "alterar", "args": [c["id"], {"coluna": "feito"}]}),
                  lambda: bel.quadro_mexer({"acao": "remover", "args": [c["id"]]})):
            try:
                f()
            except SystemExit:
                barrou.append(1)
        bel.quadro_mexer({"acao": "pegar", "args": [c["id"]]})
        bel.quadro_mexer({"acao": "alterar", "args": [c["id"], {"coluna": "fazendo"}]})
        bel.quadro_mexer({"acao": "alterar", "args": [c["id"], {"coluna": "feito", "feito_texto": "Enviado ao Pel"}]})
        try:
            Q("Sgt Fulano").quadro_mexer({"acao": "soltar", "args": [c["id"]]})  # quem criou pode soltar
            solto = True
        except SystemExit:
            solto = False
        fim = adm.quadro()["cartoes"][0]
        caso("quadro da seção: outro analista não mexe sem pegar; pega, move, conta o que fez; início e fim marcados",
             len(barrou) == 2 and fim["autor"] == "Sgt Fulano" and fim["coluna"] == "feito" and fim["feito_texto"] == "Enviado ao Pel"
             and fim.get("inicio") and fim.get("fim") and solto and "pegou" not in fim, str(fim))
    # 15c. tela Quadro (2.1.14): tarefas soltas em quadro.json
    import quadro as qd
    with tempfile.TemporaryDirectory() as tmp:
        c = qd.adicionar(tmp, "  Conferir   o log da rotina ", "conversa: cards")
        dup = qd.adicionar(tmp, "conferir o log da rotina", "outra")
        qd.alterar(tmp, c["id"], coluna="fazendo", checklist=[{"texto": "abrir o log", "feito": True}, {"texto": " "}])
        r = qd.remover(tmp, c["id"])
        vazio = qd.ler(tmp)["cartoes"] == []
        qd.restaurar(tmp, r["cartao"], r["pos"])
        d = qd.ler(tmp)["cartoes"]
        recusa = []
        for f in (lambda: qd.adicionar(tmp, "   "), lambda: qd.alterar(tmp, c["id"], coluna="lixo"), lambda: qd.alterar(tmp, "nao-existe", titulo="x")):
            try:
                f()
            except ValueError:
                recusa.append(1)
        caso("quadro: adiciona sem duplicar, move, checklist, exclui e desfaz; inválido recusado",
             c["titulo"] == "Conferir o log da rotina" and dup["id"] == c["id"] and vazio and len(d) == 1
             and d[0]["coluna"] == "fazendo" and d[0]["checklist"] == [{"texto": "abrir o log", "feito": True}] and len(recusa) == 3, str(d))
    # 15d. escala → meta da semana (2.1.15): horas da tabela de cima, 2 PPCI por período de 6 h
    import escala as esc
    serie = lambda d: (d - _dt.date(1899, 12, 30)).days
    dias = [_dt.date(2026, 10, 1) + _dt.timedelta(days=i) for i in range(31)]
    linhas = [["", "", "", 2026], ["", "", "", "outubro"], ["", "", "", 177],
              ["", "Sd Fulano", "", *([6, 12, 0, 0, 9] * 6 + [6])], ["", "Sgt Beltrano", ""] + [0] * 31,
              ["", "", "", *([1] * 31)], ["", "", "", *[serie(d) for d in dias]],
              ["", "Sd Fulano", "", *(["M", "SV", "F", "F", "9T"] * 6 + ["M"])]]
    h = esc.horas_da_aba([[str(v) for v in l] for l in linhas])
    m19 = esc.meta_da_semana(h["Sd Fulano"], _dt.date(2026, 10, 19))  # 19 a 25/10: 0+9+6+12+0+0+9 = 36 h
    m_meio = esc.meta_da_semana({"2026-10-19": 9}, _dt.date(2026, 10, 19))  # 9 h = 1,5 período → 2
    caso("escala: horas por dia da tabela de cima (não a de códigos), folga fica fora; 36 h = 6 períodos = 12 PPCI; 9 h arredonda para 2",
         set(h) == {"Sd Fulano", "Sgt Beltrano"} and h["Sgt Beltrano"] == {} and h["Sd Fulano"]["2026-10-02"] == 12
         and "2026-10-03" not in h["Sd Fulano"] and (m19["horas"], m19["periodos"], m19["meta"]) == (36, 6, 12)
         and m_meio["periodos"] == 2, str(h.get("Sd Fulano")) + str(m19))
    with tempfile.TemporaryDirectory() as tmp:
        velho = (_base_cfg := __import__("sseg_app")).arquivo_config, _base_cfg.ler_config, _api._tem_servidor
        try:
            hoje = _dt.date.today(); seg = hoje - _dt.timedelta(days=hoje.weekday())
            with open(os.path.join(tmp, "escala.json"), "w", encoding="utf-8") as fh:
                json.dump({"gerado": "2026-10-14T18:00:00", "horas": {"Sd Fulano": {seg.isoformat(): 12, (seg + _dt.timedelta(days=2)).isoformat(): 6}}}, fh)
            _base_cfg.arquivo_config = lambda: os.path.join(tmp, "config.json")
            _api._tem_servidor = lambda: False
            cfgs = [{"analista": "Sd Fulano"}, {"analista": "Sd Fulano", "meta_auto": False, "meta_semana": 7},
                    {"analista": "Sd Outro", "meta_semana": 5}, {}]
            res = []
            for c in cfgs:
                _base_cfg.ler_config = lambda c=c: dict(c, clone=RAIZ, processos=tmp)
                res.append(_api.Api().cards())
            caso("meta: pela escala do analista escolhido; à mão quando desligada, nome fora da escala ou sem analista",
                 (res[0]["meta"], res[0]["meta_info"]["fonte"], res[0]["meta_info"]["periodos"]) == (6, "escala", 3)
                 and (res[1]["meta"], res[1]["meta_info"]["fonte"]) == (7, "manual")
                 and (res[2]["meta"], res[2]["meta_info"].get("sem_escala")) == (5, True) and res[3]["meta"] == 10, str(res))
        finally:
            _base_cfg.arquivo_config, _base_cfg.ler_config, _api._tem_servidor = velho
    # 16. Reportar bug com imagem e log: o .zip leva texto e log limpos; imagens só no zip (nunca na issue)
    import api as _api, sseg_app as _base, zipfile as _zip
    with tempfile.TemporaryDirectory() as tmp:
        velho = (_base.ler_config, _base.abrir, os.environ.get("HOME"), os.environ.get("USERPROFILE"))
        try:
            _base.ler_config = lambda: {"clone": RAIZ, "processos": os.path.join(tmp, "proc")}
            _base.abrir = lambda c: None
            os.environ["HOME"] = os.environ["USERPROFILE"] = tmp
            a = _api.Api()
            a._registro = ["abri A00012345AA001 em %s" % os.path.join(tmp, "proc", "A00012345AA001")]
            a._eventos = ['{"t": "texto", "texto": "processo A00012345AA001"}']
            r = a.relato_enviar("caiu ao salvar", ["data:image/png;base64," + base64.b64encode(b"\x89PNG fake").decode()])
            z = _zip.ZipFile(os.path.join(tmp, "Documents", "SSEG-relatos", "relato-%s.zip" % r["id"]))
            log, nomes = z.read("log.txt").decode("utf-8"), z.namelist()
            z.close()  # aberto, o Windows não deixa apagar a pasta temporária
            caso("Reportar bug: zip com relato, log limpo e imagem, salvo no PC sem SSH",
                 r["onde"] == "pc" and set(nomes) == {"relato.md", "log.txt", "imagens/imagem1.png"}
                 and "A00012345AA001" not in log and tmp not in log, str(nomes) + log[:200])
        finally:
            _base.ler_config, _base.abrir = velho[0], velho[1]
            for k, v in (("HOME", velho[2]), ("USERPROFILE", velho[3])):
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    # 17. a página da interface (web/index.html): funções essenciais presentes e JavaScript válido
    import re as _re2, shutil as _sh
    pag = open(os.path.join(RAIZ, "sseg", "app", "web", "index.html"), encoding="utf-8").read()
    js = _re2.search(r"<script>(.*)</script>", pag, _re2.S).group(1)
    essenciais = ["abrirProcesso", "renderProcesso", "pintarChecklist", "pintarCIA", "abrirConversa", "chatEnviar",
                  "resposta", "caranguejo", "iniciarFluxo", "telaGit", "telaServidor"]
    falta = [f for f in essenciais if not _re2.search(r"function %s\(" % f, js)]
    caso("interface: funções essenciais presentes na página", not falta, str(falta))
    if _sh.which("node"):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
            fh.write(js)
        p_ = subprocess.run(["node", "--check", fh.name], capture_output=True, text=True)
        os.remove(fh.name)
        caso("interface: JavaScript da página sem erro de sintaxe (node --check)", p_.returncode == 0, p_.stderr[-400:])
    caso("interface: a janela do PC não se acha no celular (a marca vem só do espelho, não do endereço)",
         '<meta name="sseg-espelho"' not in pag and "location.protocol" not in js)
    caso("interface: ponte do espelho (celular) presente na página",
         "const ESPELHO" in js and "chat_historico" in js and 'data-col="cia"' in pag and "max-width: 700px" in pag)
    # 18. espelho no celular (2.4): sem a chave não entra; com ela, chama o mesmo Api e recebe os eventos
    import espelho as _esp, http.client as _hc, socket as _so, time as _t
    with _so.socket() as s_:
        s_.bind(("127.0.0.1", 0))
        porta = s_.getsockname()[1]

    class _ApiFalsa:
        def soma(self, a, b):
            return a + b

        def escolher_pasta(self):
            return "não devia"
    e_ = _esp.Espelho(_ApiFalsa(), os.path.join(RAIZ, "sseg", "app", "web"), "chave-teste", porta=porta)
    e_.ligar()
    try:
        def _pedir(metodo, caminho, corpo=None, cab=None):
            c_ = _hc.HTTPConnection("127.0.0.1", porta, timeout=10)
            c_.request(metodo, caminho, body=corpo, headers=cab or {})
            r_ = c_.getresponse()
            dados = r_.read()
            c_.close()
            return r_.status, dict(r_.getheaders()), dados
        st_sem, _, _ = _pedir("GET", "/")
        st_errada, _, _ = _pedir("GET", "/?chave=outra")
        st_ok, cab_ok, _ = _pedir("GET", "/?chave=chave-teste")
        cookie = (cab_ok.get("Set-Cookie") or "").split(";")[0]
        st_pag, _, pag_ = _pedir("GET", "/", cab={"Cookie": cookie})
        caso("espelho: sem a chave não entra; com ela vira cookie e abre a página",
             st_sem == 403 and st_errada == 403 and st_ok == 303 and st_pag == 200 and b'name="sseg-espelho"' in pag_,
             "%s %s %s %s" % (st_sem, st_errada, st_ok, st_pag))
        j = {"Cookie": cookie, "X-SSEG": "1", "Content-Type": "application/json"}
        st_api, _, r_api = _pedir("POST", "/api/soma", "[2, 3]", j)
        st_sem_cab, _, _ = _pedir("POST", "/api/soma", "[2, 3]", {"Cookie": cookie})
        st_pc, _, _ = _pedir("POST", "/api/escolher_pasta", "[]", j)
        st_priv, _, _ = _pedir("POST", "/api/__init__", "[]", j)
        c_ = _hc.HTTPConnection("127.0.0.1", porta, timeout=10)  # recusa e pedido seguinte na MESMA conexão
        c_.request("POST", "/api/escolher_pasta", body="[1, 2]", headers=j); r_ = c_.getresponse(); r_.read()
        c_.request("POST", "/api/soma", body="[4, 5]", headers=j); r2_ = c_.getresponse(); seguinte = r2_.status, r2_.read()
        c_.close()
        caso("espelho: depois de uma recusa, o pedido seguinte na mesma conexão chega inteiro",
             r_.status == 404 and seguinte[0] == 200 and json.loads(seguinte[1])["r"] == 9, str(seguinte))
        caso("espelho: chama o Api; sem X-SSEG, método só da janela ou privado, não",
             st_api == 200 and json.loads(r_api)["r"] == 5 and st_sem_cab == 403 and st_pc == 404 and st_priv == 404,
             "%s %s %s %s" % (st_api, st_sem_cab, st_pc, st_priv))
        c_ = _hc.HTTPConnection("127.0.0.1", porta, timeout=10)
        c_.request("GET", "/eventos", headers={"Cookie": cookie})
        r_ = c_.getresponse()
        r_.fp.readline(); r_.fp.readline()  # ": ok" e a linha em branco
        for _ in range(50):
            if e_.telas:
                break
            _t.sleep(0.05)
        e_.emitir("chat", ["A00012345AA001", {"t": "eu", "texto": "roda o check", "de": "x"}])
        linha = r_.fp.readline().decode("utf-8")
        c_.close()
        caso("espelho: evento empurrado à janela chega ao navegador (SSE)",
             linha.startswith("data: ") and json.loads(linha[6:]) == {"f": "chat", "a": ["A00012345AA001", {"t": "eu", "texto": "roda o check", "de": "x"}]},
             linha[:200])
    finally:
        e_.desligar()
    cmd_t = _esp.Tunel(8765).comando()
    caso("espelho: o túnel só prende a porta em 127.0.0.1 do servidor e cai se não conseguir",
         "127.0.0.1:8765:127.0.0.1:8765" in cmd_t and "ExitOnForwardFailure=yes" in cmd_t and "BatchMode=yes" in cmd_t
         and cmd_t[-1] == "sseg-servidor", " ".join(cmd_t))
    pdfs = set(os.listdir(os.path.join(RAIZ, "sseg", "normas", "pdf")))
    mapa = set(busca.PDF_RT.values()) | set(busca.PDF_RT5.values()) | {p for _, p in busca.PDF_COMENTADA}
    caso("busca: todo PDF do mapa existe em normas/pdf", mapa <= pdfs, str(sorted(mapa - pdfs)))
    r = busca.buscar(busca.carregar(RAIZ), 'extintor "5 m"')
    caso("busca: modelo do banco liga ao PDF da RT 14", r[0].get("pdf") == "sseg/normas/pdf/RT14.pdf", str(r[0].get("pdf")))
    if shutil.which("pdftotext"):
        pg = busca.pagina(os.path.join(RAIZ, r[0]["pdf"]), 'extintor "5 m"', r[0]["texto"])
        caso("busca: PDF abre na página do item 5.2.10 da RT 14", pg == 5, str(pg))
    print(f"testar.py: {oks} ok, {len(falhas)} falha(s)")
    for f in falhas:
        print("FALHA", f)
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
