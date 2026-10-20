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
        gravar(os.path.join(ppci, cod, "sol-caixa.json"), "pc")           # gerado pelo SOL dos dois lados
        gravar(os.path.join(srv, cod, "sol-caixa.json"), "srv")
        p = sc.comparar(sc.manifesto(ppci, clone_proc), Falso().listar(), {})
        caso("sincronizar: arquivo gerado (sol-caixa, marcos, api…) mudado dos dois lados desce sem conflito",
             cod + "/sol-caixa.json" in p["desce"] and cod + "/sol-caixa.json" not in p["conflito"]
             and sc.gerado(cod + "/api-123.json") and sc.gerado("cia-ultima.txt") and not sc.gerado(cod + "/analise.json"), str(p))
        os.remove(os.path.join(ppci, cod, "sol-caixa.json"))
        os.remove(os.path.join(srv, cod, "sol-caixa.json"))
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
    # 11b1. Reportar ao Claude (2.6.3): o relato vira cartão no Quadro da seção e cada um vê só os seus
    with tempfile.TemporaryDirectory() as d:
        import zipfile as _zf, io as _io
        acesso = os.path.join(d, "acesso.json")
        json.dump({"admin": "Sd Carpes", "analistas": {"Sgt Fulano": {"chave": "x"}}}, open(acesso, "w"))
        R = lambda nome=None: pt.Porta(nome, raiz=os.path.join(d, "proc"), acesso=acesso, chaves=os.path.join(d, "k"),
                                       escala=os.path.join(d, "e.json"), relatos=os.path.join(d, "rel"), quadro=os.path.join(d, "quadro"))
        buf = _io.BytesIO()
        with _zf.ZipFile(buf, "w") as z:
            z.writestr("relato.md", "**O que aconteceu**\nO Atualizar não trouxe a caixa\n\n**Programa:** SSEG.exe 9")
        r = R("Sgt Fulano").relato("20261020-080000", buf.getvalue())
        os.makedirs(os.path.join(d, "rel", "sgt_fulano-20261020-080000"))
        open(os.path.join(d, "rel", "sgt_fulano-20261020-080000", "estado.txt"), "w").write("pronto\n")
        meus, adm_l = R("Sgt Fulano").relatos_lista()["relatos"], R().relatos_lista()["relatos"]
        cart = pt.qd.ler(os.path.join(d, "quadro"))["cartoes"]
        caso("porta: relato guarda o .zip, vira cartão no Quadro e aparece com o andamento só para quem mandou e o admin",
             r["ok"] and len(cart) == 1 and "Sgt Fulano" in cart[0]["titulo"] and "Atualizar" in cart[0]["titulo"]
             and [(x["id"], x["estado"]) for x in meus] == [("20261020-080000", "pronto")] and len(adm_l) == 1
             and pt.executar(R("Sgt Fulano"), ["relatos"], lambda: b"", "p").startswith(b'{"relatos"'), str((r, cart, meus)))
    # 11b2. outro PC do administrador e senha do SOL pelo SSEG.exe (2.5.0)
    with tempfile.TemporaryDirectory() as d:
        chaves, acesso = os.path.join(d, "authorized_keys"), os.path.join(d, "acesso.json")
        open(chaves, "w").write("ssh-ed25519 AAAAadmin atila@casa\n")
        k_pc2, k_fulano = "ssh-ed25519 " + "C" * 68, "ssh-ed25519 " + "A" * 68
        P2 = lambda nome=None: pt.Porta(nome, raiz=os.path.join(d, "proc"), acesso=acesso, chaves=chaves,
                                        escala=os.path.join(d, "esc.json"), relatos=os.path.join(d, "rel"))
        adm2 = P2()
        r1 = adm2.autorizar({"analista": "Sd Carpes", "chave": k_pc2 + " carpes-pc2", "rotulo": "pc2"}, "p")   # nome do admin
        r2 = adm2.admin_chave({"chave": k_pc2, "rotulo": "pc2"})
        adm2.autorizar({"analista": "Sgt Fulano", "chave": k_fulano}, "SSEG/sseg/scripts/porta.py")   # regrava as linhas de analista
        linhas = open(chaves).read().splitlines()
        adm2.revogar("Sgt Fulano", "p")
        depois = open(chaves).read().splitlines()
        caso("porta: nome do admin em autorizar vira outro PC dele, sem restrição, uma vez só, e sobrevive ao regravar",
             r1 == {"ok": True, "ja_estava": False} and r2["ja_estava"] and linhas[0] == "ssh-ed25519 AAAAadmin atila@casa"
             and linhas[1].startswith(k_pc2) and linhas[1].endswith("sseg-admin-pc2") and "command=" not in linhas[1]
             and depois == linhas[:2] and "Sd Carpes" not in pt.ler_acesso(acesso)["analistas"], str(linhas))
    with tempfile.TemporaryDirectory() as d:
        import sol_senha as _ss
        _a, _t = _ss.ARQUIVO, _ss.TRAVA
        _ss.PASTA, _ss.ARQUIVO, _ss.TRAVA = d, os.path.join(d, "sol-login.json"), os.path.join(d, "sol-login-falhou")
        try:
            chaves, acesso = os.path.join(d, "ak"), os.path.join(d, "ac.json")
            open(_ss.TRAVA, "w").write("falhou")
            adm3 = pt.Porta(None, raiz=d, acesso=acesso, chaves=chaves, escala=os.path.join(d, "e.json"), relatos=os.path.join(d, "r"))
            r = json.loads(pt.executar(adm3, ["sol-senha-gravar"], lambda: json.dumps({"matricula": " 123 ", "senha": "s3gr3d0"}).encode(), "p"))
            modo = oct(os.stat(_ss.ARQUIVO).st_mode & 0o777)
            gravou = _ss.ler() == {"matricula": "123", "senha": "s3gr3d0"}
            saida = json.dumps(r)
            vazio = []
            try:
                pt.executar(adm3, ["sol-senha-gravar"], lambda: b'{"matricula":"1","senha":""}', "p")
            except SystemExit:
                vazio.append(1)
            adm3.autorizar({"analista": "Sgt Fulano", "chave": k_fulano}, "SSEG/sseg/scripts/porta.py")
            recusa = []
            F = lambda: pt.Porta("Sgt Fulano", raiz=d, acesso=acesso, chaves=chaves, escala=os.path.join(d, "e.json"), relatos=os.path.join(d, "r"))
            for f in (lambda: F().sol_senha_gravar({"matricula": "1", "senha": "x"}),
                      lambda: F().sol_senha_apagar(), lambda: F().admin_chave({"chave": k_pc2})):
                try:
                    f()
                except SystemExit:
                    recusa.append(1)
            pt.executar(adm3, ["sol-senha-apagar"], lambda: b"", "p")
            caso("porta: sol-senha-gravar guarda em 600, solta a trava, nunca devolve a senha; só admin grava/apaga; apagar remove",
                 r == {"ok": True, "matricula": "123"} and (modo == "0o600" or os.name == "nt") and gravou and "s3gr3d0" not in saida  # Windows não tem modo 600
                 and not os.path.exists(_ss.TRAVA) and vazio == [1] and len(recusa) == 3 and _ss.ler() is None,
                 str((r, modo, gravou, vazio, recusa)))
        finally:
            _ss.ARQUIVO, _ss.TRAVA = _a, _t
    # 11b3. processo que saiu da caixa do SOL (2.5.1): desce da lista com o resultado dos Marcos
    sys.path.insert(0, os.path.join(AQUI, "..", "app"))
    import api as _api
    with tempfile.TemporaryDirectory() as d:
        w = lambda n, o: open(os.path.join(d, n), "w", encoding="utf-8").write(json.dumps(o))
        e0 = _api.estado_caixa({"codigo": "A1", "distribuido": "2026-10-10"}, {}, 10, __import__("datetime").date(2026, 10, 19))
        ficou = _api._saiu_da_caixa(dict(e0), d)["estado"]
        w("sol-caixa.json", {"id": 1, "saiu_em": "2026-10-19"})
        w("marcos-resumo.json", {"analises": [{"data": "2026-09-01", "resultado": "CIA"}, {"data": "2026-10-18", "resultado": "CA"}]})
        e1 = _api._saiu_da_caixa(dict(e0), d)
        w("marcos-resumo.json", {"analises": [{"data": "2026-09-01", "resultado": "CIA"}]})   # análise velha: não vale
        e2 = _api._saiu_da_caixa(dict(e0), d)
        caso("app: processo que saiu da caixa vira concluído com o resultado dos Marcos; análise velha não conta; na caixa fica",
             ficou == "caixa" and (e1["estado"], e1["resultado"], e1["concluido"], e1["dias"]) == ("concluido", "CA", "2026-10-19", 9)
             and (e2["estado"], e2["resultado"]) == ("concluido", ""), str((ficou, e1, e2)))
    # 11b3a. print do memorial (2.6.4): norma do dimensionamento, inviabilidade, laudo, notificação e o que verificar
    import memorial_sol as _ms
    api_f = {"numero": "A00012345AA001", "tipo": "PPCI",
             "caracteristica": {"areaConstruida": 1000.5, "alturaDescendente": 7, "caracteristicaConstrutiva": "Z",
                                "ocupacoes": [{"cnae": {"divisao": "C-2", "cnae": "4744-0/99", "descricao": "Loja"}, "cargaIncendio": 800,
                                               "grauRisco": "ALTO", "ocupacao": "PREDOMINANTE", "determinaSeguranca": True}]},
             "especSeguranca": {"medidas": [{"tipo": {"nome": "Saída de Emergência"}, "norma": {"nome": "Resolução Técnica nº 11/2016"},
                                             "inviabilidade": "POSSUI_PARCIAL", "compartimentacao": False,
                                             "resultado": {"statusResultadoAtec": "REPROVADO", "justificativas": [{"justificativa": "Deverá corrigir a largura."}]}}],
                                "laudo": {"txtClob": "<p>Rampa&nbsp;com 10%</p><p>Compensatória: fita</p>"}},
             "elemGraficos": [{"tipo": "CORTE", "descricao": "corte", "situacao": "ATIVO"}, {"tipo": "CORTE", "descricao": "velho", "situacao": "INATIVO"}]}
    t = _ms.texto(_ms.montar(api_f, 2, "01/09/2026", ["Linha não conferida."]))
    caso("memorial SOL: medida com norma, inviabilidade parcial, status, notificação, laudo sem HTML, inativo à parte e o que verificar",
         "Saída de Emergência | Resolução Técnica nº 11/2016 | Sim, parcial | Não | Reprovado" in t and "Deverá corrigir a largura." in t
         and "Rampa com 10%\nCompensatória: fita" in t and "Substituídos" in t and "1.000,50 m²" in t
         and "[ ] Alturas descendente" in t and "[ ] Linha não conferida." in t and "C-2 | 4744-0/99" in t, t[:3000])
    import pre_analise as _pa
    cia_f = ("Elementos Gráficos\n\nPLANTA BAIXA\n\n           1. Outros\n              Corrigir a escada.\n"
             "CBMRS 25/08/2026 14:55:00            Pagina 2 de 3\nCORTE\n              Cotar o pé-direito.\n\nDemais inconformidades\n   x\n")
    ms = lambda d: int(__import__("datetime").datetime.fromisoformat(d).timestamp() * 1000)  # noqa: E731
    api_p = {"elemGraficos": [
        {"tipo": "PLANTA_BAIXA", "descricao": "Planta  baixa", "situacao": "ATIVO", "dthInclusao": ms("2026-08-01")},   # notificada, ficou
        {"tipo": "CORTE", "descricao": "corte", "situacao": "ATIVO", "dthInclusao": ms("2026-09-10")},                  # nova
        {"tipo": "CORTE", "descricao": "CORTE", "situacao": "INATIVO", "dthInclusao": ms("2026-08-01"), "dthExclusao": ms("2026-09-10"),
         "justificativas": [{"justificativa": "Cotar o pé-direito."}]}]}
    pl = {(p["estado"], p["descricao"]) for p in _pa.plantas(api_p, {"analises": [{"data": "2026-08-20", "resultado": "CIA"}]}, cia_f)}
    caso("pré-análise: planta notificada na última CIA e não trocada aparece; a trocada vira nova + substituída; rodapé não é título",
         _pa.notificados_cia(cia_f) == {"PLANTA BAIXA": "Corrigir a escada.", "CORTE": "Cotar o pé-direito."}
         and pl == {("mantido-notificado", "Planta baixa"), ("novo", "corte"), ("substituido", "CORTE")}, str(pl))
    caso("sincronizar: o print do memorial é gerado (vale o do servidor)", sc.gerado("A1/memorial SOL 3.pdf") and not sc.gerado("A1/memorial 3.pdf"))
    # 11b3c. Lançar no SOL (2.6.5): corpo igual ao do botão Reprovar, o que já estava fica, Outros substituído, confere
    import sol_lancar as _sl
    import re
    class SOLFalso:
        def __init__(s, guardar=True):
            s.chamadas, s.guardar = [], guardar
            s.ana = {"id": 77, "status": "EM_ANALISE", "inconformidade": "velha", "licenciamento": {
                "envolvidos": {}, "caracteristica": {"id": 5, "ocupacoes": []}, "elemGraficos": [], "especsRiscos": [],
                "especSeguranca": {"id": 9, "medidas": [{"id": 11, "tipo": {"nome": "Saída de Emergência", "chaveNC": "analise.medidas.saida"},
                    "resultado": {"id": 501, "statusResultadoAtec": "REPROVADO", "justificativas": [
                        {"id": 1, "justificativa": "pronta", "parametroNcs": {"id": 300, "valor": "Largura"}},
                        {"id": 2, "justificativa": "texto velho", "parametroNcs": {"id": 301, "valor": "Outros"}}]}}]}}}
        def avaliar(s, js):
            m = re.search(r'const a = (\{.*?\});\n', js, re.S)
            if m:  # gravação
                a = json.loads(m.group(1)); s.chamadas.append(a)
                if s.guardar and a["url"].endswith("/editar-item"):
                    c = json.loads(a["corpo"]); s.ana["licenciamento"]["especSeguranca"]["medidas"][0]["resultado"] = dict(c, id=501)
                if a["url"].endswith("/inconformidade"):
                    s.ana["inconformidade"] = a["corpo"]
                return {"status": 200, "corpo": "501"}
            url = json.loads(re.search(r'fetch\(("[^"]+")', js).group(1))
            s.chamadas.append({"metodo": "GET", "url": url})
            corpo = [{"id": 301, "chave": "analise.medidas.saida", "valor": "Outros", "ativo": True}] if "/parametro/" in url else s.ana
            return {"status": 200, "corpo": json.dumps(corpo)}
    f = SOLFalso()
    pl = _sl.plano(f, 77, "saida de emergencia", "\n- Novo.")
    r = _sl.lancar(f, 77, "Saída de Emergência", "\n- Novo.")
    post = [c for c in f.chamadas if c["metodo"] == "POST"]
    corpo = json.loads(post[0]["corpo"]) if post else {}
    caso("Lançar no SOL: plano lê o que já está; POST editar-item com a pronta mantida e o Outros novo; confere; nunca conclui",
         (pl["status"], pl["ja_outros"], pl["outras"]) == ("Reprovado", "texto velho", 1) and r["ok"] and len(post) == 1
         and post[0]["url"].endswith("/analise-tecnica/editar-item")
         and (corpo["id"], corpo["idAnaliseTecnica"], corpo["idItemAnalisado"], corpo["tipoItemAnaliseTecnica"], corpo["statusResultadoAtec"]) == (501, 77, 11, "MEDIDA_SEGURANCA", "REPROVADO")
         and [(j["parametroNcs"]["id"], j["justificativa"], j["id"]) for j in corpo["justificativas"]] == [(300, "pronta", None), (301, "\n- Novo.", None)]
         and not any(re.search(r"deferir|indeferir|concluir", c["url"]) for c in f.chamadas), str((pl, r, corpo)))
    f2 = SOLFalso(guardar=False)
    r2 = _sl.lancar(f2, 77, "Saída de Emergência", "\n- Novo.")
    f3 = SOLFalso()
    r3 = _sl.lancar(f3, 77, "Demais inconformidades", "\n- Livre.")
    put = [c for c in f3.chamadas if c["metodo"] == "PUT"]
    erro = ""
    try:
        _sl.lancar(SOLFalso(), 77, "Saída de Emergência", "x" * 2001)
    except ValueError as e:
        erro = str(e)
    caso("Lançar no SOL: leitura de volta diferente avisa; demais inconformidades por PUT texto; acima de 2.000 não grava",
         not r2["ok"] and r2["conferido"] is False and r3["ok"] and put and put[0]["tipo"] == "text/plain"
         and put[0]["url"].endswith("/77/inconformidade") and "2001" in erro, str((r2, r3, erro)))
    # 11b3b. a caixa do SOL manda sobre a planilha (2.6.3; caso de 20/10/2026: distribuídos na véspera sumiram do Início)
    E0 = lambda dist: _api.estado_caixa(dist, {}, 10, __import__("datetime").date(2026, 10, 20))
    S = lambda e, sc, ult="2026-10-20": _api._na_caixa_do_sol(e, sc, ult)
    hoje_sol = {"lido_em": "2026-10-20", "id": 1}
    a = S(E0({"codigo": "A1"}), hoje_sol)                                                         # planilha: na fila
    b = S(E0({"codigo": "A1", "distribuido": "2026-10-15", "concluido": "2026-10-19", "resultado": "CA"}), hoje_sol)
    c = S(E0({"codigo": "A1", "distribuido": "2026-10-15", "concluido": "2026-10-20", "resultado": "CA"}), hoje_sol)
    d_ = S(E0({}), {"lido_em": "2026-10-16"})                                                     # leitura velha
    e_ = S(E0({}), dict(hoje_sol, saiu_em="2026-10-20"))
    f_ = S(E0({"codigo": "A1", "distribuido": "2026-10-19"}), hoje_sol)                           # já na caixa: fica igual
    caso("app: na caixa do SOL vale mais que a planilha atrasada; conclusão no mesmo dia, leitura velha e saída não",
         (a["estado"], a["vence"], a["fonte"]) == ("caixa", "", "sol") and (b["estado"], b["resultado"]) == ("caixa", "")
         and c["estado"] == "concluido" and d_["estado"] == "sem" and e_["estado"] == "sem"
         and (f_["estado"], f_["vence"], f_["fonte"]) == ("caixa", "2026-10-29", "planilha"), str([a, b, c, d_, e_, f_]))
    # 11b4. memorial e CIA congelados (2.6.0): nomes dentro da lista do enviar, código validado, só admin
    import sol_snapshot as _snap
    import enviar as _env
    erros = []
    for c in ("../x", "A123", ""):
        try:
            _snap._pasta(c)
        except ValueError:
            erros.append(1)
    caso("snapshot: nomes memorial N.pdf, licenciamento N.json e CIA N.pdf sobem ao servidor; código estranho é barrado",
         _env.selecionar(["memorial 4.pdf", "licenciamento 4.json", "CIA 4.pdf", "R00-planta.pdf"]) ==
         (["CIA 4.pdf", "licenciamento 4.json", "memorial 4.pdf"], ["R00-planta.pdf"]) and len(erros) == 3,
         str((_env.selecionar(["memorial 4.pdf", "licenciamento 4.json", "CIA 4.pdf"]), erros)))
    adm5 = pt.Porta(None, raiz=tempfile.gettempdir(), acesso=os.devnull, chaves=os.devnull)
    adm5.admin = False
    try:
        adm5.sol_snapshot("congelar", "A00000001AA001")
        barrou = False
    except SystemExit:
        barrou = True
    caso("porta: sol-congelar e sol-salvar são só do administrador", barrou)
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
        arq = os.path.join(d, "conversas.jsonl")
        gasto_m.anotar_conversa("s1", {"id": "analise", "modelo": "claude-sonnet-5-5", "esforco": "high"}, "A00012345AA001", arq)
        tipos = dict((t, s["respostas"]) for t, s, n in gasto_m.por_tipo(gasto_m.ler(clone, base=os.path.join(d, "projects")),
                                                                          gasto_m.tipos_das_sessoes(arq)))
        caso("gasto por tipo: sessão anotada pelo chat vai para o botão que a abriu", tipos == {"analise": 2}, str(tipos))
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
             and "A00044444AA001" in ful.meus() and "A00011111AA001" in ful.meus() and "A00022222AA001" not in ful.meus()
             and "A00011111AA001" not in _pt2.Porta(None, raiz=tmp, acesso=os.path.join(tmp, "acesso.json")).meus(), str((c2, ful.meus())))
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
    # 19. lições das conversas de 16–17/10/2026 (2.3.22): pergunta repetida, linha transcrita, página da tabela
    import analise_registro as ar
    regs = {"pendencias": [{"id": "p4", "texto": "Planta CIA02: os 40,55 m² de depósito de cerveja saíram de 'área técnica'?"},
                           {"id": "p5", "texto": "Planta CIA02: 'circulação – isento' foi vinculada à ocupação real?"},
                           {"id": "p9", "texto": "Qual a data de protocolo da 1ª análise?"}]}
    caso("pendência: a mesma pergunta com outras palavras é reconhecida",
         (ar.parecida(regs, "Os 40,55 m² de depósito de cerveja continuam como 'área técnica / isento'?") or {}).get("id") == "p4"
         and (ar.parecida(regs, "A 'circulação – isento' ainda existe na planta nova?") or {}).get("id") == "p5"
         and ar.parecida(regs, "Os extintores estão a no máximo 20 m (classe A)?") is None)
    import sseg as sseg_m
    tr = sseg_m.linha_transcrita({"situacao_existencia": "a construir"}, "J-1 a J-4", "5", None)
    caso("check: Tabela 5, coluna 'I e J', 5 medidas transcritas do PDF",
         tr is not None and tr["rotulo"] == "I e J" and len(tr["exigidas"]) == 5, str(tr and tr["exigidas"]))
    tr = sseg_m.linha_transcrita({"situacao_existencia": "a construir"}, "C-2", "6C", "H<=6")
    caso("check: 6C/C-2/H<=6 traz as notas 8 e 9 com o texto",
         tr is not None and any(n.startswith("8") for n in tr["notas"]) and any("750" in n for n in tr["notas"]), str(tr and tr["notas"]))
    if shutil.which("pdftotext") and shutil.which("pdftoppm"):
        import normas_pdf
        dec = normas_pdf.achar_pdf("decreto")
        caso("norma: Tabela 5 do Decreto na página 66 e 6J.2 na 99 (não na citação 'Conforme Tabela 5')",
             normas_pdf.pagina_da_tabela(dec, "5")[:1] == [66] and normas_pdf.pagina_da_tabela(dec, "6J.2")[:1] == [99])
        caso("norma: busca sem acento acha 'risco médio' na RT 14",
             any(n == 4 for n, _t in normas_pdf.buscar(normas_pdf.achar_pdf("rt14"), "risco medio")))
    # 20. pré-análise da reanálise (2.3.23): plantas trocadas e o que mudou desde o JSON anterior
    import pre_analise as pa_m
    api_a = {"caracteristica": {"populacaoTotal": 60, "ocupacoes": [{"ocupacao": "PREDOMINANTE", "cnae": {"divisao": "J"}}]},
             "especSeguranca": {"medidas": [{"tipo": {"nome": "Extintores"}, "norma": {"nome": "RT 14/2016"}},
                                            {"tipo": {"nome": "Plano de Emergência"}, "norma": {"nome": "RT 15"}}]}}
    api_b = {"caracteristica": {"populacaoTotal": 81, "ocupacoes": [{"ocupacao": "PREDOMINANTE", "cnae": {"divisao": "J-3"}}]},
             "especSeguranca": {"medidas": [{"tipo": {"nome": "Extintores"}, "norma": {"nome": "RT 14/2016"}}]},
             "elemGraficos": [{"situacao": "INATIVO", "tipo": "PLANTA_BAIXA", "descricao": "CIA01", "dthExclusao": 1790000000000,
                               "justificativas": [{"justificativa": "- Adequar a classificação"}]},
                              {"situacao": "ATIVO", "tipo": "PLANTA_BAIXA", "descricao": "CIA02", "dthInclusao": 1790000000000}]}
    t = pa_m.secao_reanalise(api_b, api_a, {"analise": 3})
    caso("pré-análise da reanálise: planta nova, notificada a substituída, população e medida que saiu",
         "NOVO planta baixa: CIA02" in t and "Adequar a classificação" in t and "População total: 60 → 81" in t
         and "campo 4, saiu: Plano de Emergência" in t, t[-400:])
    print(f"testar.py: {oks} ok, {len(falhas)} falha(s)")
    for f in falhas:
        print("FALHA", f)
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
