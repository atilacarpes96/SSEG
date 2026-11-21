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
    # 10/11/2026: 2.8.17 e 2.8.18 barradas no build porque só o VERSION subiu — o commit não sai mais assim
    _app = os.path.join(RAIZ, "sseg", "app")
    _v = open(os.path.join(_app, "VERSION"), encoding="utf-8").read().strip()
    _src = open(os.path.join(_app, "sseg_app.py"), encoding="utf-8").read()
    _nov = open(os.path.join(_app, "NOVIDADES.md"), encoding="utf-8").read()
    caso("SSEG.exe: VERSION igual à VERSAO do sseg_app.py e com seção em NOVIDADES.md",
         f'VERSAO = "{_v}"' in _src and f"\n## {_v}\n" in _nov, _v)
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
        gravar(os.path.join(ppci, cod, "analise.json"), json.dumps({"exigencias": [{"id": "e1", "final": "a"}, {"id": "e2", "final": "pc"}]}))
        gravar(os.path.join(srv, cod, "analise.json"), json.dumps({"exigencias": [{"id": "e1", "final": "a"}, {"id": "e3", "final": "srv"}]}))
        os.utime(os.path.join(ppci, cod, "analise.json"), (1000000, 1000000))
        dt = sc.detalhar(ppci, Falso(), [cod + "/analise.json", cod + "/CIA 1.pdf"])
        da = dt[cod + "/analise.json"]
        caso("sincronizar: conflito diz o lado mais novo e o que muda (2.7.7)",
             da["mais_novo"] == "servidor" and any("só no PC" in m and "e2" in m for m in da["mudancas"])
             and any("só no servidor" in m and "e3" in m for m in da["mudancas"])
             and "binário" in dt[cod + "/CIA 1.pdf"]["mudancas"][0]
             and open(os.path.join(ppci, cod, "analise.json")).read().find('"pc"') > 0, str(dt))
        os.remove(os.path.join(ppci, cod, "analise.json")); os.remove(os.path.join(srv, cod, "analise.json"))
        r = sc.aplicar(ppci, Falso(), {cod + "/CIA 1.pdf": "servidor"})
        caso("sincronizar: escolha 'servidor' resolve o conflito",
             open(os.path.join(ppci, cod, "CIA 1.pdf")).read() == "cia srv" and not r["conflito_pendente"], str(r))
        # conflito resolvido sozinho (04/11/2026): o lado que só acrescentou fica; senão o mais novo; o outro é guardado
        gravar(os.path.join(ppci, cod, "conversa.jsonl"), "a\n"); gravar(os.path.join(srv, cod, "conversa.jsonl"), "a\n")
        gravar(os.path.join(ppci, cod, "notas.md"), "base"); gravar(os.path.join(srv, cod, "notas.md"), "base")
        sc.aplicar(ppci, Falso())
        gravar(os.path.join(ppci, cod, "conversa.jsonl"), "a\nb\n"); gravar(os.path.join(srv, cod, "conversa.jsonl"), "a\nc\nb\n")
        gravar(os.path.join(ppci, cod, "notas.md"), "versao pc"); gravar(os.path.join(srv, cod, "notas.md"), "versao srv")
        os.utime(os.path.join(srv, cod, "notas.md"), (1000000, 1000000))
        pa = sc.planejar(ppci, Falso())
        ra = sc.aplicar(ppci, Falso())
        bak = os.path.join(clone_proc, "substituidos-sinc")
        guardados = [n for _r, _d, fs in os.walk(bak) for n in fs] if os.path.isdir(bak) else []
        caso("sincronizar: conflito resolvido sozinho (o que só acrescentou, senão o mais novo) e o outro guardado",
             not pa["conflito"] and pa["auto"][cod + "/conversa.jsonl"]["lado"] == "servidor"
             and pa["auto"][cod + "/notas.md"]["lado"] == "pc"
             and open(os.path.join(ppci, cod, "conversa.jsonl")).read() == "a\nc\nb\n"
             and open(os.path.join(srv, cod, "notas.md")).read() == "versao pc"
             and sorted(guardados) == ["pc-%s__conversa.jsonl" % cod, "servidor-%s__notas.md" % cod]
             and not ra["conflito_pendente"], str((pa, ra, guardados)))
        l0, lp, ls = ('{"t": "eu", "texto": "%s", "em": "%s"}' % x for x in (("oi", "1"), ("pc", "3"), ("srv", "2")))
        gravar(os.path.join(ppci, cod, "conversa.jsonl"), l0 + "\n" + lp + "\n")
        gravar(os.path.join(srv, cod, "conversa.jsonl"), l0 + "\n" + ls + "\n")
        rj = sc.aplicar(ppci, Falso())
        caso("sincronizar: conversa continuada nos dois PCs junta as mensagens pela hora (2.8.13)",
             open(os.path.join(srv, cod, "conversa.jsonl")).read() == "\n".join([l0, ls, lp]) + "\n"
             and open(os.path.join(ppci, cod, "conversa.jsonl")).read() == "\n".join([l0, ls, lp]) + "\n", str(rj))
        # arquivo aberto no PC (Windows não deixa trocar): os outros descem, ele fica para a próxima (relato de 20/10/2026)
        gravar(os.path.join(srv, cod, "memorial SOL 2.pdf"), "print novo")
        gravar(os.path.join(srv, cod, "memorial SOL 2.txt"), "texto novo")
        gravar(os.path.join(ppci, cod, ".analise-abc.json"), "temporário")
        _rep = sc.os.replace
        def _travado(a, b):
            if b.endswith("memorial SOL 2.pdf"):
                raise PermissionError(13, "Acesso negado")
            return _rep(a, b)
        sc.os.replace = _travado
        try:
            import time as _t
            _sl0, _t.sleep = _t.sleep, (lambda s: None)
            rp = sc.aplicar(ppci, Falso())
        finally:
            sc.os.replace, _t.sleep = _rep, _sl0
        caso("sincronizar: arquivo aberto no PC não derruba o resto e volta na próxima; temporário escondido não sobe",
             rp["presos"] == [cod + "/memorial SOL 2.pdf"] and cod + "/memorial SOL 2.txt" in rp["desceu"]
             and not os.path.exists(os.path.join(ppci, cod, "memorial SOL 2.pdf.sseg-tmp"))
             and cod + "/memorial SOL 2.pdf" in sc.comparar(sc.manifesto(ppci, clone_proc), Falso().listar(), sc._ler_base())["desce"]
             and not os.path.exists(os.path.join(srv, cod, ".analise-abc.json")), str(rp))
        sc.aplicar(ppci, Falso())
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
        g(os.path.join(raiz, ".caixa", "caixa.json"), json.dumps({"itens": [{"codigo": "A00000002AA001"}]}))
        caso("porta: processo do outro pela planilha que está na caixa do SOL do servidor desce ao admin (2.7.8)",
             P().meu("A00000002AA001") and ful.meu("A00000002AA001") and not ful.meu("A00000001AA001"))
        os.remove(os.path.join(raiz, ".caixa", "caixa.json"))
        g(os.path.join(raiz, "A00000002AA001", "sol-caixa.json"), json.dumps({"lido_em": "2026-10-30", "saiu_em": "2026-10-30"}))
        caso("porta: saiu da caixa do admin depois da distribuição ao outro: continua descendo ao admin (2.7.11)",
             P().meu("A00000002AA001"))
        os.remove(os.path.join(raiz, "A00000002AA001", "sol-caixa.json"))
        import api as _api_m
        dist_o = {"analista": "Sd Riccardi", "distribuido": "2026-09-28", "tipo": "7º"}
        caso("caixa: PPCI do outro na minha caixa do SOL é meu; linha aberta mantém o prazo da planilha, concluída não conta (2.7.8, 2.13.6)",
             _api_m._dist_minha(dist_o, "Sd Carpes", {"lido_em": "2026-10-30"}, "2026-10-30") == (dist_o, True)
             and _api_m._dist_minha(dict(dist_o, concluido="2026-10-01"), "Sd Carpes", {"lido_em": "2026-10-30"}, "2026-10-30") == ({}, True)
             and _api_m._dist_minha(dist_o, "Sd Carpes", {"lido_em": "2026-10-29"}, "2026-10-30") == (dist_o, False)
             and _api_m._dist_minha(dist_o, "Sd Riccardi", {}, "2026-10-30") == (dist_o, True)
             and _api_m._dist_minha(dist_o, "Sd Carpes", {"lido_em": "2026-10-30", "saiu_em": "2026-10-30"}, "2026-10-30") == ({}, True))
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
        cart = pt.qd.ler(os.path.join(d, "quadro", "programa"))["cartoes"]
        secao_vazia = not pt.qd.ler(os.path.join(d, "quadro"))["cartoes"]
        ve_prog = ("programa" in R().quadro(), "programa" in R("Sgt Fulano").quadro())
        try:
            R("Sgt Fulano").quadro_mexer({"acao": "adicionar", "args": ["x"], "onde": "programa"})
            mexe = True
        except SystemExit:
            mexe = False
        caso("porta: relato guarda o .zip, vira cartão no quadro do Programa (só o admin vê e mexe; a seção fica limpa) e aparece com o andamento só para quem mandou e o admin",
             r["ok"] and len(cart) == 1 and secao_vazia and ve_prog == (True, False) and not mexe and "Sgt Fulano" in cart[0]["titulo"] and "Atualizar" in cart[0]["titulo"]
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
        cod_c = "A00000005AA001"
        os.makedirs(os.path.join(d, cod_c))
        open(os.path.join(d, cod_c, "marcos-resumo.json"), "w").write(json.dumps({"analise": 8}))
        a_c = _api.Api.__new__(_api.Api)
        a_c._cfg = lambda: {"processos": d}
        a_c._reg = lambda: __import__("analise_registro")
        a_c._marcar_concluido(cod_c, "CA")
        cc = json.load(open(os.path.join(d, cod_c, "analise.json"))).get("conclusao") or {}
        caso("concluir: grava CA e o nº da análise dos Marcos (o botão vira 'Processo concluído') (2.7.10)",
             cc.get("resultado") == "CA" and cc.get("analise") == 8 and cc.get("em"), str(cc))
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
        # 2.8.9: reanálise que entrou e saiu da caixa antes da planilha do dia seguinte (linha da planilha = análise anterior)
        e3 = _api.estado_caixa({"codigo": "A1", "distribuido": "2026-07-29", "concluido": "2026-07-30", "resultado": "CIA"}, {})
        w("marcos-resumo.json", {"analises": [{"data": "2026-07-30", "resultado": "CIA"}, {"data": "2026-10-19", "resultado": "CA"}]})
        e4 = _api._saiu_da_caixa(dict(e3), d)
        w("sol-caixa.json", {"id": 1, "saiu_em": "2026-07-30"})   # saída antiga: a planilha já sabe
        e5 = _api._saiu_da_caixa(dict(e3), d)
        caso("app: reanálise concluída no dia, com a planilha ainda na análise anterior, conta pela saída do SOL (2.8.9)",
             (e4["estado"], e4["concluido"], e4["resultado"], e4["distribuido"]) == ("concluido", "2026-10-19", "CA", "")
             and (e5["concluido"], e5["distribuido"]) == ("2026-07-30", "2026-07-29"), str((e4, e5)))
        caso("app: nº da análise da planilha lido para comparar com os Marcos (2.8.12)",
             [_api._n_analise(t) for t in ("ANÁLISE", "Analise", "2º", "3", "", None)] == [1, 1, 2, 3, 0, 0])
    # 2.8.11: conversa do processo gravada em conversa.jsonl e devolvida ao reabrir o programa
    with tempfile.TemporaryDirectory() as d:
        a1 = _api.Api.__new__(_api.Api)
        a1._hist, a1._pasta_proc = {}, (lambda c: os.path.join(d, c))
        os.makedirs(os.path.join(d, "A1"))
        a1._guardar("A1", {"t": "eu", "texto": "oi", "de": "x", "minis": ["data:image/jpeg;base64,AAA"]})
        a1._guardar("A1", {"t": "cota", "janela": 3})
        a1._guardar("A1", {"t": "texto", "texto": "resposta"})
        a1._guardar("fluxo:analise", {"t": "texto", "texto": "não grava"})
        a2 = _api.Api.__new__(_api.Api)
        a2._hist, a2._pasta_proc = {}, a1._pasta_proc
        h = a2.chat_historico("A1")
        linhas = [json.loads(l) for l in open(os.path.join(d, "A1", "conversa.jsonl"), encoding="utf-8")]
        caso("app: conversa do processo vai para conversa.jsonl (sem cota, sem os prints) e volta ao reabrir (2.8.11)",
             [e["t"] for e in h] == ["eu", "texto", "fim"] and linhas[0].get("prints") == 1 and "minis" not in linhas[0]
             and all("em" in l for l in linhas) and len(linhas) == 2 and __import__("enviar").selecionar(["conversa.jsonl"])[0] == ["conversa.jsonl"],
             str((h, linhas)))
        ant = a2._conversa_anterior("A1")
        a1._guardar("A1", {"t": "texto", "texto": "x" * 3000})
        curto = a2._conversa_anterior("A1", limite=3040)
        caso("app: conversa salva vai como contexto da conversa nova em outro PC (2.8.13)",
             "<conversa_anterior>" in ant and ant.index("[Analista") < ant.index("[Claude") and "resposta" in ant
             and "não grava" not in ant and "só o final" in curto and "[Analista" not in curto
             and a2._conversa_anterior("A2") == "", ant + curto[:300])
    # 2.8.14: PDF na conversa vai como documento e fica cópia na pasta (o mesmo PDF não duplica)
    import chat as _chat
    _pdfb = base64.b64encode(b"%PDF-1.4 teste").decode()
    _it = _chat.imagens([{"url": "data:application/pdf;base64," + _pdfb, "nome": "Laudo: final.pdf"}])
    with tempfile.TemporaryDirectory() as d:
        c1 = _api.Api._guardar_pdfs(d, _it); c2 = _api.Api._guardar_pdfs(d, _it)
        caso("app: PDF na conversa vai como documento e a cópia na pasta não duplica (2.8.14)",
             _chat.bloco(_it[0])["type"] == "document" and _it[0]["nome"] == "Laudo_ final.pdf" and c1 == c2
             and os.listdir(d) == ["anexo Laudo_ final.pdf"], str((_it[0]["nome"], c1, c2, os.listdir(d))))
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
    car_a = {"licenciamento": {"envolvidos": {}, "caracteristica": {"id": 5, "ocupacoes": [{"id": 8, "cnae": {"divisao": "J-4", "descricao": "Depósitos"}}]},
             "localizacao": {"isolamentoRisco": True}, "elemGraficos": [], "especsRiscos": [], "especSeguranca": {"medidas": []}}}
    caso("Lançar no SOL: \"Característica - …\" da coluna CIA cai no campo 3 (geral; tipo e isolamento quando nomeados)",
         [(_sl.achar(car_a, n) or {}).get("tipo") for n in ("Característica - Ocupação: Depósitos de mercadorias", "Características gerais",
          "Característica - Tipo de edificação", "Característica - Isolamento de risco", "Ocupação J-4")]
         == ["GERAL", "GERAL", "TIPO_EDIFICACAO", "ISOLAMENTO_RISCO", "OCUPACAO"])
    rt_a = {"licenciamento": {"envolvidos": {"rts": [{"id": 3, "nome": "Fulano de Tal"}]}, "caracteristica": {"id": 5, "ocupacoes": []},
            "elemGraficos": [], "especsRiscos": [], "especSeguranca": {"medidas": []}}}
    caso("Lançar no SOL: 'ART/RRT' e 'Responsável Técnico' da coluna CIA vão ao item 'RT: <nome>' (09/11/2026)",
         [(_sl.achar(rt_a, n) or {}).get("tipo") for n in ("ART/RRT", "ART", "RRT de execução", "Responsável Técnico", "Artigo 5")]
         == ["RT", "RT", "RT", "RT", None])
    # seletor "medida" da CIA no SSEG.exe (10/11/2026): os itens da seção 1 saem com o nome que o lançador acha no SOL
    sys.path.insert(0, os.path.join(RAIZ, "sseg", "app"))
    import processo as _proc
    env_a = {"licenciamento": {"envolvidos": {
        "rts": [{"id": 3, "nome": "FULANO DE TAL "}, {"id": 4, "nome": "Ana Souza"}],
        "rus": [{"id": 6, "nome": "Beltrano", "procurador": {"nome": "P"}}, {"id": 7, "nome": "Sem Procurador"}],
        "proprietarios": [{"idLicenciamentoProprietario": 8, "nome": "Empresa X", "procurador": {"nome": "P"}}]},
        "caracteristica": {"id": 5, "ocupacoes": []}, "elemGraficos": [], "especsRiscos": [], "especSeguranca": {"medidas": []}}}
    sel = _proc.envolvidos(env_a["licenciamento"])
    caso("CIA do SSEG.exe: seletor oferece 'RT: <nome>' e RU/Proprietário com procurador, e cada um casa no SOL (10/11/2026)",
         sel == ["RT: FULANO DE TAL", "RT: Ana Souza", "RU: Beltrano", "Proprietário: Empresa X"]
         and [(_sl.achar(env_a, n) or {}).get("id") for n in sel] == [3, 4, 6, 8], str(sel))
    pre_t = ("== Normas citadas no campo '4. Medidas de seguranca' ==\nData de protocolo: 2026-11-10\n"
             "OK Iluminação de Emergência — cita Resolução Técnica CBMRS nº 13 / 2025 (bate com o indice).\n"
             "OK Saída de Emergência — cita Resolução Técnica nº 11/2016 (bate com o indice).\n"
             "!! Extintores de Incêndio — cita RT 14/2009 (nao bate com o indice).\n\n== Travas ==\nOK Brigada de Incêndio — cita X (bate com o indice).\n")
    meds_t = [{"nome": n, "inviabilidade": i} for n, i in (("Iluminação de Emergência", "NAO_POSSUI"), ("Saída de Emergência", "POSSUI_PARCIAL"),
                                                           ("Extintores de Incêndio", "NAO_POSSUI"), ("Brigada de Incêndio", "NAO_POSSUI"))]
    mp = _proc.memorial_pela_pre(pre_t, meds_t, "Memorial descritivo")
    caso("Checklist: 'Memorial descritivo' verde pelo script só com norma OK, sem laudo e com data de protocolo (2.14.3)",
         list(mp) == ["Iluminação de Emergência|Memorial descritivo"] and mp[list(mp)[0]]["script"]
         and _proc.memorial_pela_pre(pre_t.replace("2026-11-10", ""), meds_t, "Memorial descritivo") == {}, str(mp))
    med_a ={"licenciamento": {"envolvidos": {}, "caracteristica": {"id": 5, "ocupacoes": []}, "elemGraficos": [], "especsRiscos": [],
             "especSeguranca": {"id": 9, "medidas": [{"id": 1, "tipo": {"nome": "Sinalização de Emergência"}, "resultado": None}]}}}
    caso("Lançar no SOL: 'Geral' vai à Característica geral; medida fora do campo 4 vai a 'Adicionar correções' (30/10/2026)",
         [(_sl.achar(med_a, n) or {}).get("tipo") for n in ("Geral", "Compartimentação Horizontal", "Sinalização de Emergência")]
         == ["GERAL", "MEDIDA_SEGURANCA_OUTRA", "MEDIDA_SEGURANCA"]
         and _sl.achar(med_a, "Compartimentação Horizontal")["id"] == 9
         and "MEDIDA_SEGURANCA_OUTRA" not in {i["tipo"] for i in _sl.a_aprovar(med_a, [], True)})
    ap_a = {"licenciamento": {"envolvidos": {}, "caracteristica": {"id": 5, "ocupacoes": []}, "elemGraficos": [], "especsRiscos": [],
            "especSeguranca": {"medidas": [{"id": 1, "tipo": {"nome": "Extintores"}, "resultado": None},
                                           {"id": 2, "tipo": {"nome": "Alarme"}, "resultado": {"statusResultadoAtec": "REPROVADO"}},
                                           {"id": 3, "tipo": {"nome": "Saídas"}, "resultado": {"statusResultadoAtec": "APROVADO"}}]}}}
    caso("Aprovar tudo (sem notificação): Reprovado também entra; Aprovado fica; com notificação, Reprovado fica",
         {i["nome"] for i in _sl.a_aprovar(ap_a, [], True)} == {"Tipo de edificação", "Característica geral", "Extintores", "Alarme"}
         and {i["nome"] for i in _sl.a_aprovar(ap_a, [])} == {"Tipo de edificação", "Característica geral", "Extintores"})
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
    f4 = SOLFalso()
    L4 = f4.ana["licenciamento"]
    L4["especSeguranca"]["medidas"].append({"id": 12, "tipo": {"nome": "Extintores", "chaveNC": "analise.medidas.ext"}, "resultado": None})
    L4["envolvidos"] = {"rus": [{"id": 40, "nome": "Sem procurador", "resultado": None}],
                        "proprietarios": [{"id": 41, "idLicenciamentoProprietario": 4100, "nome": "Dono", "procurador": {"id": 1}, "resultado": None}]}
    L4["elemGraficos"] = [{"id": 60, "descricao": "planta", "situacao": "ATIVO", "resultado": None},
                          {"id": 61, "descricao": "velha", "situacao": "INATIVO", "resultado": None}]
    L4["caracteristica"].update(resultadoGeral={"statusResultadoAtec": "APROVADO"})
    nomes = [i["nome"] for i in _sl.a_aprovar(f4.ana, ["planta"])]
    caso("Lançar no SOL: aprova só o que está em Analisar, sem exigência; RU sem procurador e inativo ficam fora; proprietário pelo idLicenciamentoProprietario",
         nomes == ["Proprietário: Dono", "Tipo de edificação", "Extintores"]
         and [i["id"] for i in _sl.itens(f4.ana) if i["tipo"] == "PROPRIETARIO"] == [4100], str(nomes))
    caso("Lançar no SOL: leitura de volta diferente avisa; demais inconformidades por PUT texto; acima de 2.000 não grava",
         not r2["ok"] and r2["conferido"] is False and r3["ok"] and put and put[0]["tipo"] == "text/plain"
         and put[0]["url"].endswith("/77/inconformidade") and "2001" in erro, str((r2, r3, erro)))
    # 11b3d. revisão final pela coluna CIA (2.6.5): antes de lançar, sem PDF da CIA
    import revisar_cia as _rc, argparse as _ap
    with tempfile.TemporaryDirectory() as d:
        json.dump({"versao": 1, "exigencias": [{"id": "e1", "medida": "Saída de Emergência", "final": "\n- REITERO: largura da porta."},
                                                {"id": "e2", "medida": "Saída de Emergência", "final": ""}]},
                  open(os.path.join(d, "analise.json"), "w", encoding="utf-8"))
        json.dump({"analise": 1, "data_protocolo": "2026-09-01", "medidas": []}, open(os.path.join(d, "pre-analise.json"), "w"))
        saida = _rc.revisar(_ap.Namespace(cia=None, pasta=d, textos=None, json=None, anterior=None, normas=None)).texto()
    caso("revisar-cia --pasta: lê as exigências salvas da coluna CIA (uma caixa por medida) e acusa REITERO em 1ª análise",
         "coluna CIA do SSEG.exe" in saida and "REITERO numa 1ª análise" in saida and "Sem --textos" not in saida, saida[:800])
    # 11b3e. revisão final: Aplicar troca o texto final e guarda o anterior; Ignorar só registra (2.6.7)
    import api as _api2, sseg_app as _base2
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "proc", "A00012345AA001"))
        json.dump({"versao": 1, "exigencias": [{"id": "e1", "medida": "Saída", "final": "\n- velho"}, {"id": "e2", "final": "\n- fica"}]},
                  open(os.path.join(d, "proc", "A00012345AA001", "analise.json"), "w", encoding="utf-8"))
        _v = _base2.ler_config
        try:
            _base2.ler_config = lambda: {"clone": RAIZ, "processos": os.path.join(d, "proc")}
            a = _api2.Api()
            a1 = a.processo_aplicar_revisao("A00012345AA001", "e1", "\n- novo", "RT 11, item 5.4.2")
            a2 = a.processo_aplicar_revisao("A00012345AA001", "e2", "\n- outro", "", True)
        finally:
            _base2.ler_config = _v
    caso("revisão final: Aplicar troca o texto final e guarda o anterior; Ignorar não mexe no texto",
         (a1["final"], a1["final_antes_revisao"], a1["fundamento"]) == ("\n- novo", "\n- velho", "RT 11, item 5.4.2")
         and a1["revisao"].startswith("aplicada") and a2["final"] == "\n- fica" and a2["revisao"].startswith("ignorada"), str((a1, a2)))
    # 11b3f. PPCI de outro analista não aparece (2.6.10): vale o analista da planilha, pela última palavra do nome
    caso("app: processo é meu pelo analista da planilha; sem planilha ou sem nome no PC, conta como meu",
         _api._e_meu({"analista": "Sd Carpes"}, "SD CARPES") and not _api._e_meu({"analista": "Sgt Magalhães"}, "Sd Carpes")
         and _api._e_meu({"analista": "Sgt Magalhaes"}, "Sgt Magalhães") and _api._e_meu({}, "Sd Carpes") and _api._e_meu({"analista": "Sgt X"}, ""))
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
        # 2.7.3: descartar tira o rascunho do Claude, nunca o texto salvo pelo analista
        e2 = reg.exigencia(pasta, "- Deverá (errado)", "Abafamento", "RT 22/2023, item B.16.1")
        msg = reg.descartar(pasta, [e["id"], e2["id"], "e99"])
        ids = [x["id"] for x in reg.ler(pasta)["exigencias"]]
        caso("analise descartar: sai o rascunho, fica o item salvo, id inexistente avisado",
             ids == [e["id"]] and "NÃO descartado" in msg and "e99" in msg, msg)
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
        # 2.14.0: resultado do que foi batido no chat (verde/vermelho/amarelo), pelos códigos P<n> e M<medida>.<item>
        k_sai, _r = reg.chave_de(pasta, "m2.1")
        reg.visto(pasta, k_sai, "ver", "olhar a largura na planta")
        reg.visto(pasta, reg.chave_de(pasta, "P6")[0], "ok", "sem empate")
        recusa_v = []
        for ruim in (lambda: reg.chave_de(pasta, "M9.9"), lambda: reg.visto(pasta, k_sai, "talvez")):
            try:
                ruim()
            except ValueError:
                recusa_v.append(1)
        vv = reg.ler(pasta)["vistos"]
        reg.visto(pasta, k_sai, "ia", "Parece cumprida", palpite=2)
        vv["ia"] = reg.ler(pasta)["vistos"][k_sai]
        reg.visto(pasta, "passo:6", None)
        caso("checklist: o Claude marca conforme / falta ver pelo código; código ou estado inválido recusado; vazio apaga",
             k_sai == "Saída de Emergência|Memorial descritivo" and vv[k_sai]["estado"] == "ver" and vv["passo:6"]["nota"] == "sem empate"
             and len(recusa_v) == 2 and vv["ia"]["estado"] == "ia" and vv["ia"]["palpite"] == 2 and "passo:6" not in reg.ler(pasta)["vistos"] and reg.ler(pasta)["exigencias"], str(vv))
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
    caso("chat: os 8 blocos visuais ensinados ao Claude são JSON válido",
         {t for t, _ in blocos} == {"sseg-status", "sseg-dados", "sseg-definidora", "sseg-perguntas", "sseg-exigencia", "sseg-norma", "sseg-revisao",
                                    "sseg-palpites"}
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
    cit = {"RT de Implantação do SOL-CBMRS, itens 6.3.2 (alínea d) e 6.3.3.1": "RTISOL.pdf",
           "RT 22/2023, item B.6.2.1": "RT22.pdf", "RT 05 Parte 08/2016": "RT05P08.pdf"}
    caso("busca: RT de Implantação (sem número), RT 22 e RT 05 Parte 08 achadas em normas/pdf (2.7.6)",
         all(busca.pdf_citado(t) == p for t, p in cit.items()), str({t: busca.pdf_citado(t) for t in cit}))
    if shutil.which("pdftotext"):
        pg = busca.pagina(os.path.join(RAIZ, r[0]["pdf"]), 'extintor "5 m"', r[0]["texto"])
        caso("busca: PDF abre na página do item 5.2.10 da RT 14", pg == 5, str(pg))
        # 2.8.0: link de item no texto — página em que o item abre a linha (fora do sumário), com o assunto
        rt01 = os.path.join(RAIZ, "sseg", "normas", "pdf", busca.PDF_RT["1"])
        alvo = {"5.2.2 · RT 01/2024": 21, "4.3.1 · RT 01/2024": 7, "Tabela 2 · RT 01/2024": 8}
        achou = {r: busca.pagina_item(rt01, r)[0] for r in alvo}
        caso("link de item: 5.2.2, 4.3.1 e Tabela 2 da RT 01/2024 abrem na página do título do item", achou == alvo, str(achou))
        pg, ass = busca.pagina_item(os.path.join(RAIZ, "sseg", "normas", "pdf", busca.PDF_RT["2"]), "4.20 · RT 02/2014")
        caso("link de item: 4.20 da RT 02 abre na pág. 4 com o assunto 'Altura da edificação'",
             pg == 4 and ass.startswith("Altura da edifica"), "%d %r" % (pg, ass))
        pg, _a = busca.pagina_item(os.path.join(RAIZ, "sseg", "normas", "pdf", "DECRETO51803.pdf"), "Art. 5º · Decreto 51.803/2014")
        caso("link de item: o número do Decreto (51.803) não é lido como item", pg >= 1 and "51.803" not in _a, str(pg))
    st = busca.norma_status("5.2.2.1 · RT 01/2022", RAIZ)
    caso("link de item: RT 01/2022 citada abre o PDF de 2024 com aviso de versão", st["pdf"] and "2022" in (st["aviso"] or ""), str(st))
    caso("link de item: RT 01/2024 citada sem aviso", busca.norma_status("5.2.2 · RT 01/2024", RAIZ)["aviso"] is None)
    caso("link de item: norma sem PDF (RT 13, IT 08) vem marcada para incorporar",
         busca.norma_status("5.1 · RT 13/2025", RAIZ)["pdf"] is None and busca.norma_status("IT 08", RAIZ)["pdf"] is None)
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
    with tempfile.TemporaryDirectory() as _tn:
        json.dump({"analista_planilha": "FULANO DE TAL CARPES"}, open(os.path.join(_tn, "distribuicao.json"), "w"))
        json.dump([{"tela": "Análise técnica", "texto": "Minha nota.", "nomeUsuarioSoe": "Fulano de Tal Carpes", "dthAlteracao": 1786470602385},
                   {"tela": "Análise técnica", "texto": "Conferir a escada.", "nomeUsuarioSoe": "Cap Chefe", "dthAlteracao": 1795000000000}],
                  open(os.path.join(_tn, "notas.json"), "w"))
        _sn = pa_m.secao_notas(_tn)
        json.dump([], open(os.path.join(_tn, "notas.json"), "w"))
        _sv = pa_m.secao_notas(_tn)
    caso("pré-análise: notas da análise técnica do SOL — nota de outra pessoa vira !!, a do analista não (19/11/2026)",
         "!! NOTA de Cap Chefe" in _sn and "Conferir a escada." in _sn and "nota sua, Fulano" in _sn
         and not any(l.startswith("!!") and "Fulano" in l for l in _sn.splitlines()) and "nenhuma" in _sv, _sn)
    api_a ={"caracteristica": {"populacaoTotal": 60, "ocupacoes": [{"ocupacao": "PREDOMINANTE", "cnae": {"divisao": "J"}}]},
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
    # 21. sol_base.py --pastas (28/10/2026): Marcos da base vão às pastas; o que o sol_caixa leu depois fica
    import sol_base as sb_m
    with tempfile.TemporaryDirectory() as tmp:
        base, procs = os.path.join(tmp, "base"), os.path.join(tmp, "processos")
        os.makedirs(os.path.join(base, "proc"))
        sb_m.BASE, sb_m.LISTA = base, os.path.join(base, "lista.json")
        marco = [{"id": 1, "dthMarco": 1790000000000, "descricao": "Número do licenciamento gerado"}]
        json.dump({"7": {"numero": "A00000001AA001"}, "8": {"numero": "A00000002AA001"}}, open(sb_m.LISTA, "w"))
        lic7 = {"id": 7, "numero": "A00000001AA001", "caracteristica": {"areaConstruida": 120, "ocupacoes": [
            {"ocupacao": "PREDOMINANTE", "determinaSeguranca": True, "cnae": {"divisao": "C-1"}}]}}
        for k in ("7", "8"):
            json.dump({"coletado_em": "2026-10-28 12:20", "marcos": marco, "historico": {"historicoRecurso": []},
                       "licenciamento": lic7 if k == "7" else None}, open(os.path.join(base, "proc", k + ".json"), "w"))
        for c in ("A00000001AA001", "A00000002AA001", "A00000003AA001"):
            os.makedirs(os.path.join(procs, c))
        json.dump({"codigo": "A00000001AA001", "distribuido": "2026-10-27"},  # na fila: pré-análise antes da caixa
                  open(os.path.join(procs, "A00000001AA001", "distribuicao.json"), "w"))
        caixa = os.path.join(procs, "A00000002AA001", "marcos.json")
        json.dump([{"id": 2, "descricao": "lido pela caixa"}], open(caixa, "w"))
        os.utime(caixa, (sb_m._quando("2026-10-28 12:30"),) * 2)
        n1, n2 = sb_m.preencher_pastas(procs), sb_m.preencher_pastas(procs)
        p1 = os.path.join(procs, "A00000001AA001")
        caso("sol_base --pastas: copia Marcos e histórico, faz o resumo, não regrava e respeita a leitura da caixa",
             n1 == 1 and n2 == 0 and os.path.exists(os.path.join(p1, "marcos-resumo.json"))
             and os.path.exists(os.path.join(p1, "historico.json"))
             and json.load(open(caixa))[0]["id"] == 2 and not os.listdir(os.path.join(procs, "A00000003AA001")),
             f"{n1} {n2} {os.listdir(p1)}")
        pa_txt = os.path.join(p1, "pre-analise.txt")
        os.remove(pa_txt)  # 2ª rodada, Marcos da pasta mais novos que a base: a pré-análise sai mesmo assim
        sb_m.preencher_pastas(procs)
        caso("sol_base --pastas: distribuído sem caixa ganha base-api-<ID>.json e pré-análise, sem api-<ID>.json",
             os.path.exists(os.path.join(p1, "base-api-7.json")) and not glob.glob(os.path.join(p1, "api-*.json"))
             and os.path.exists(pa_txt) and "antes de o processo chegar à caixa" in open(pa_txt, encoding="utf-8").read(),
             f"{os.listdir(p1)}")
    # 22. sol_banco.py + sol_consulta.py (28/10/2026): a base vira tabelas e as consultas da aba Processos respondem
    import sol_banco, sol_consulta
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "proc"))
        os.makedirs(os.path.join(tmp, "cia"))
        json.dump({"9": {"id": 9, "numero": "A00000009AA001", "situacao": "NCA", "cidade": "SANTA CRUZ DO SUL", "razao": "Loja Teste",
                         "endereco": "Rua A 1", "presente": True}}, open(os.path.join(tmp, "lista.json"), "w"))
        lic = {"id": 9, "numero": "A00000009AA001", "situacao": "NCA", "dataCriacao": "02/10/2026 - 10:00",
               "localizacao": {"latitudeMapa": -29.7, "longitudeMapa": -52.4, "cidade": {"nome": "SANTA CRUZ DO SUL"}},
               "caracteristica": {"areaConstruida": 350.5, "ocupacoes": [{"ocupacao": "PREDOMINANTE", "cnae": {"divisao": "C-2"}}]},
               "especSeguranca": {"medidas": [{"tipo": {"nome": "Extintores"}, "norma": {"nome": "RT 14/2016"}}]}}
        marcos = [{"id": 1, "dthMarco": 1790000000000, "descricao": "Conclusão de análise técnica - CIA", "nomeResponsavel": "FULANO",
                   "arquivo": {"id": 77, "nomeArquivo": "cia.pdf"}}]
        json.dump({"coletado_em": "2026-10-28 12:20", "licenciamento": lic, "marcos": marcos, "historico": {}, "informacoes": {}},
                  open(os.path.join(tmp, "proc", "9.json"), "w", encoding="utf-8"))
        open(os.path.join(tmp, "cia", "77.txt"), "w", encoding="utf-8").write("- Instalar barra\nantipânico nas portas da saída.\f")
        n, _s = sol_banco.montar(tmp)
        db = os.path.join(tmp, "solcbm.db")
        f = sol_consulta.consultar("processo", {"numero": "A00000009AA001"}, db)
        c = sol_consulta.consultar("cias", {"q": "barra antipanico"}, db)
        p = sol_consulta.consultar("pesquisa", {"q": "loja", "com_cia": 1}, db)
        caso("sol_banco/sol_consulta: ficha, medidas, CIA achada sem acento e pesquisa",
             n == 1 and f["processo"]["area_construida"] == 350.5 and f["medidas"][0]["medida"] == "Extintores"
             and c["total"] == 1 and c["linhas"][0]["trechos"][0]["achado"] == "barra antipânico" and p["total"] == 1
             and sol_consulta.consultar("mapa", {}, db)[0][1] == -29.7, f"{n} {c} {p['total']}")
    # 22. palpite da IA local (2.9.0): só o que é do script, sem Ollama. O rótulo nunca passa de "fraco" fora do tipo
    # texto, conflito e contraprova que falha viram inconclusivo, e sem IA no PC o item fica na fila (nunca "não sei").
    import palpite_local as pl_m, sincronizar as _sinc
    r_ = lambda *vs: [{"veredito": v, "evidencia": ""} for v in vs]
    c_ = lambda v: {"veredito": v, "evidencia": ""}
    caso("palpite: rótulo firme só em texto, igual nos três recortes e com 'não cumpriu' na planta anterior; o título diz o porquê",
         pl_m.conclusao("texto", r_("nao_cumpriu", "nao_cumpriu", "nao_cumpriu"), c_("nao_cumpriu"))["motivo"] == "continua_igual"
         and pl_m.conclusao("texto", r_("nao_cumpriu", "nao_cumpriu", "nao_cumpriu"), c_("nao_cumpriu"))["classe"] == "ambar"
         and pl_m.conclusao("texto", r_("nao_cumpriu", "nao_cumpriu", "nao_cumpriu"), c_("nao_cumpriu"))["veredito"] == "nao_cumpriu"
         and pl_m.conclusao("texto", r_("cumpriu", "cumpriu", "cumpriu"), c_("nao_cumpriu"))["classe"] == "verde"
         and pl_m.conclusao("desenho", r_("cumpriu", "cumpriu", "cumpriu"), c_("nao_cumpriu"))["motivo"] == "tipo_fraco"
         and pl_m.conclusao("texto", r_("cumpriu", "cumpriu", "cumpriu"), None)["titulo"].startswith("Palpite fraco (Cumpriu): sem a planta anterior"))
    _lt = lambda v, lido: {"veredito": v, "comparacao": "minimo", "exigido": 1.2, "lido": lido}
    _ok = pl_m.conclusao("texto", r_("cumpriu", "cumpriu", "cumpriu"), c_("nao_cumpriu"), _lt("cumpriu", 1.4))
    _dis = pl_m.conclusao("texto", r_("cumpriu", "cumpriu", "cumpriu"), c_("nao_cumpriu"), _lt("nao_cumpriu", 0.9))
    _sem = pl_m.conclusao("texto", r_("cumpriu", "cumpriu", "cumpriu"), None, _lt("nao_sei", None))
    caso("palpite: com número, verde só quando a conta com a cota lida concorda; discordância e cota não lida ficam âmbar",
         _ok["classe"] == "verde" and "1,4 m" in _ok["titulo"] and "1,2 m" in _ok["titulo"] and _ok["motivo"] == "conta_confirma"
         and _dis["classe"] == "ambar" and not _dis["veredito"] and _dis["motivo"] == "conta_discorda" and "0,9 m" in _dis["titulo"]
         and _sem["classe"] == "ambar" and _sem["motivo"] == "conta_sem_leitura", str((_ok, _dis, _sem)))
    _cor = pl_m.conclusao("texto", r_("cumpriu", "cumpriu", "cumpriu"), c_("nao_cumpriu"), _lt("cumpriu", 1.4),
                          "Os corredores de circulação na área de copa e lavanderia deverão ter no mínimo 1,10 m de largura.")
    _por = pl_m.conclusao("texto", r_("cumpriu", "cumpriu", "cumpriu"), c_("nao_cumpriu"), _lt("cumpriu", 1.4),
                          "A porta da sala deverá ter vão livre mínimo de 1,20 m.")
    _vrm = pl_m.conclusao("texto", r_("nao_cumpriu", "nao_cumpriu", "nao_cumpriu"), c_("nao_cumpriu"), _lt("nao_cumpriu", 0.9),
                          "O corredor de circulação deverá ter largura mínima de 1,20 m.")
    caso("palpite: largura de corredor/circulação nunca fica verde (vale o trecho mais estreito; caso da copa, 19/11/2026); "
         "porta continua verde e 'não cumprida' nunca é vermelho (replay 21/11/2026: 8 de 8 errados)",
         _cor["classe"] == "ambar" and _cor["motivo"] == "trecho_estreito" and not _cor["veredito"] and "1,4 m" in _cor["explicacao"]
         and _por["classe"] == "verde" and _vrm["classe"] == "ambar" and _vrm["veredito"] == "nao_cumpriu", str((_cor, _por, _vrm)))
    _bruto = '{"veredito": "nao_cumpriu", "evidencia": "Na imagem, a rampa est\\u00e1 cotada com \'i=5%\' e 3,74 que corresponde'
    _orig = pl_m._ollama
    pl_m._ollama = lambda *a, **k: {"message": {"content": _bruto}}
    try:
        _cort = pl_m.perguntar("p", "o", b"x")
    finally:
        pl_m._ollama = _orig
    caso("palpite: resposta cortada pelo teto aproveita o veredito em vez de falhar o item",
         _cort["veredito"] == "nao_cumpriu" and _cort["evidencia"].endswith("[cortado]"), str(_cort))
    pl_m._spans["/x/teste.pdf"] = {1: [(100, 100, "Nº 39", "extintores"), (500, 500, "Nº39", "saida"), (900, 100, "39", "base")]}
    _fic, _sai = pl_m.filtro_camada("/x/teste.pdf", 1, [(102, 98), (898, 101)], "39", "sinalizacao")
    _ext, _ = pl_m.filtro_camada("/x/teste.pdf", 1, [(102, 98)], "39", "extintores")
    pl_m._spans.pop("/x/teste.pdf")
    caso("palpite: número de ordem filtrado pela camada (placa nº 39 ≠ extintor nº 39; 19/11/2026)",
         pl_m.tipo_do_numero("A sinalização nº 39 esta indicando o lado contrario", "39") == ("39", "sinalizacao")
         and pl_m.tipo_do_numero("corrimãos na rampa próximo da placa S14 n°16.", "16") == ("16", "sinalizacao")
         and pl_m.tipo_do_numero("placa na porta próxima ao extintor de incêndio nº 03;", "03") == ("3", "extintores")
         and pl_m.tipo_do_numero("área de 48.16 m2", "16") == ("16", None)
         and pl_m.rotulo_de_numero("P- nº39", "39") and not pl_m.rotulo_de_numero("ATÉ A SAÍDA=39,95m", "39")
         and _fic == [(500, 500)] and sorted(_sai) == ["base", "extintores"] and _ext == [(102, 98)],
         str((_fic, _sai, _ext)))
    caso("palpite: a conta compara o número lido (cm vira m; taxa por área arredonda para baixo; sem leitura = não sei)",
         pl_m.numerico({"comparacao": "minimo", "exigido": 1.2, "valor_no_elemento": 110, "area_m2": None})["veredito"] == "nao_cumpriu"
         and pl_m.numerico({"comparacao": "minimo", "exigido": 120, "valor_no_elemento": 1.2, "area_m2": None})["veredito"] == "cumpriu"
         and pl_m.numerico({"comparacao": "taxa_pessoas_por_m2", "exigido": 1, "valor_no_elemento": 34, "area_m2": 34.72})["veredito"] == "cumpriu"
         and pl_m.numerico({"comparacao": "minimo", "exigido": 1.2, "valor_no_elemento": None, "area_m2": None})["veredito"] == "nao_sei"
         and pl_m.com_numero({"tipo": "texto", "exigencia": "largura mínima de 1,20 m"}) and not pl_m.com_numero({"tipo": "desenho", "exigencia": "1,20 m"}))
    with tempfile.TemporaryDirectory() as _d2:
        os.makedirs(os.path.join(_d2, pl_m.SUB))
        def _pdf(nome, ws):
            arq = os.path.join(_d2, pl_m.SUB, nome)
            open(arq, "w").close()
            with open(arq + ".bbox.json", "w", encoding="utf-8") as fh:
                json.dump({"ws": {"1": [[w, x, y, x + 20, y + 8, w] for w, x, y in ws]}, "tam": {"1": [2000, 1400]}}, fh)
        _fixo = [("parede%d" % i, 100 + 40 * i, 100 + 30 * i) for i in range(30)]
        _pdf("antes.pdf", _fixo + [("0,80", 1500, 300), ("data", 1800, 1300), ("rev0", 1820, 1300)])
        _pdf("nova.pdf", _fixo + [("1,20", 1500, 300), ("p2", 1510, 320), ("lx", 1490, 310), ("data2", 1800, 1300), ("rev1", 1820, 1300), ("folha2", 1840, 1310)])
        _r = {"pdf": "nova.pdf", "pagina": 1, "caixa": [100, 100, 460, 460], "prancha": "Térreo",
              "antes": {"pdf": "antes.pdf", "pagina": 1, "caixa": [100, 100, 460, 460]}}
        _mud = pl_m.recortes_mudanca(_d2, [_r])
        _orig = pl_m.perguntar
        pl_m.perguntar = lambda texto, onde, png: {"veredito": "cumpriu", "evidencia": "porta 1,20", "segundos": 1}
        _orig_rec = pl_m.recorte
        pl_m.recorte = lambda *a, **k: b"png"
        try:
            _sc = pl_m._segunda_chance(_d2, {"exigencia": "x"}, [_r], "pergunta")
            _sem = pl_m._segunda_chance(_d2, {"exigencia": "x"}, [dict(_r, antes=None)], "pergunta")
        finally:
            pl_m.perguntar, pl_m.recorte = _orig, _orig_rec
    caso("palpite: segunda chance recorta onde a planta mudou (fora o carimbo) e sai sempre fraca",
         len(_mud) == 1 and _mud[0]["caixa"][0] <= 1500 <= _mud[0]["caixa"][2] and _mud[0]["caixa"][1] <= 300 <= _mud[0]["caixa"][3]
         and _sc["rotulo"]["classe"] == "ambar" and _sc["rotulo"]["veredito"] == "cumpriu"
         and _sc["rotulo"]["motivo"] == "segunda_chance_mudanca" and _sc["segunda"]["recortes"] == _mud and _sem == {},
         str((_mud, _sc.get("rotulo"))))
    with tempfile.TemporaryDirectory() as _d3:
        os.makedirs(os.path.join(_d3, pl_m.SUB))
        def _pdf3(nome, paginas):
            arq = os.path.join(_d3, pl_m.SUB, nome)
            open(arq, "w").close()
            with open(arq + ".bbox.json", "w", encoding="utf-8") as fh:
                json.dump({"ws": {str(k): [[w, x, y, x + 20, y + 8, w] for w, x, y in ws] for k, ws in enumerate(paginas, 1)},
                           "tam": {str(k): [2000, 1400] for k in range(1, len(paginas) + 1)}}, fh)
        _sala = [("sala%d" % i, 100 + 40 * i, 100 + 30 * i) for i in range(30)]
        _carta = [("prefeito%d" % i, 100 + 40 * i, 100) for i in range(30)]
        _pdf3("nova.pdf", [_sala])
        _pdf3("oficio.pdf", [_carta])                                             # tipo "planta" errado no SOL
        _pdf3("plantas2.pdf", [_carta, [(w, x + 50, y + 20) for w, x, y in _sala]])  # a certa: página 2, deslocada
        _pdf3("refeita.pdf", [[(w, 1900 - x, 1300 - y) for w, x, y in _sala]])   # mesmo texto, desenho refeito
        _pl = lambda arq, i, tipo: {"arquivo": arq, "id": i, "lado": "antes", "tipo": tipo, "descricao": "planta", "tem": True, "nome": arq}
        _nova = {"arquivo": "nova.pdf", "id": 9, "lado": "depois", "tipo": "PLANTA", "descricao": "planta", "tem": True, "nome": "nova"}
        _wn, _t = pl_m.palavras(os.path.join(_d3, pl_m.SUB, "nova.pdf"))
        _esc = pl_m.anterior_da_pagina(_d3, [_nova, _pl("oficio.pdf", 3, "PLANTA"), _pl("plantas2.pdf", 2, "OUTRO")], _nova, 1, _wn[1])
        _nada = pl_m.anterior_da_pagina(_d3, [_nova, _pl("oficio.pdf", 3, "PLANTA")], _nova, 1, _wn[1])
        _wa, _t = pl_m.palavras(os.path.join(_d3, pl_m.SUB, "plantas2.pdf"))
        _wr, _t = pl_m.palavras(os.path.join(_d3, pl_m.SUB, "refeita.pdf"))
        _ok = pl_m.alinhou(pl_m.mudancas(_wa[2], _wn[1])[0], _wn[1])
        _torto = pl_m.alinhou(pl_m.mudancas(_wr[1], _wn[1])[0], _wn[1])
    caso("palpite: a planta anterior é a página de texto parecido (não o ofício do mesmo tipo) e, sem alinhar, não há contraprova",
         _esc[0] and _esc[0]["arquivo"] == "plantas2.pdf" and _esc[1] == 2 and _nada == (None, None) and _ok and not _torto,
         str((_esc[0] and _esc[0]["arquivo"], _esc[1], _nada, _ok, _torto)))
    caso("palpite: dica de cotas só lista o escrito no recorte e o limite (placa S1 300x150 não é porta; porta só em exigência de porta; 'mais de 2,20 m' é condição)",
         pl_m.limite_exigencia("A porta deverá ter luz mínima de 1,00 m, vão livre (2 UP).") == ("largura", 1.0)
         and pl_m.limite_exigencia("caminhamento máximo de 30 m até a saída") == ("distancia", 30.0)
         and pl_m.limite_exigencia("Rampa com mais de 2,20 m de largura deve ter corrimão intermediário.") is None
         and pl_m.limite_exigencia("Cotar a largura da rampa.") is None
         and pl_m.cotas_escritas("largura", ["P1 80x210", "S1 300x150", "PORTA 0,90 x 2,10"], porta=True) == [0.8, 0.9]
         and "0,80; 0,90" in pl_m.dica_cotas({"exigencia": "a porta deverá ter luz mínima de 1,00 m"}, ["P1 80x210", "P2 0,90x2,10"], "Prancha X")
         and pl_m.dica_cotas({"exigencia": "a escada deverá ter largura mínima de 1,10 m"}, ["P1 80x210", "P2 0,90x2,10"], "Prancha X") == ""
         and "1,20" in pl_m.dica_cotas({"exigencia": "a escada deverá ter largura mínima de 1,10 m"}, ["L = 1,20"], "Prancha X")
         and pl_m.dica_cotas({"exigencia": "largura mínima de 1,10 m"}, ["sem cota"], "Prancha X") == "")
    caso("palpite: recorte que muda a resposta, 'não sei' e 'cumpriu' na planta anterior saem como inconclusivo, sem veredito",
         all(x["titulo"].startswith("Inconclusivo:") and not x["veredito"] and x["motivo"] for x in (
             pl_m.conclusao("texto", r_("cumpriu", "nao_cumpriu", "cumpriu"), c_("nao_cumpriu")),
             pl_m.conclusao("texto", r_("nao_sei", "nao_sei", "nao_sei"), c_("nao_cumpriu")),
             pl_m.conclusao("texto", r_("cumpriu", "cumpriu", "cumpriu"), c_("cumpriu")))))
    caso("palpite: recortes que discordam viram 'não sei' (nunca 'cumpriu')",
         pl_m.agregar(r_("cumpriu", "nao_cumpriu")) == "nao_sei" and pl_m.agregar(r_("cumpriu", "nao_sei")) == "cumpriu"
         and pl_m.agregar(r_("nao_sei", "nao_sei")) == "nao_sei")
    _cia = ("O PPCI apresentou as seguintes inconformidades em relação às normas aplicáveis:\n\nMedidas de Segurança\n"
            "Saída de Emergência\n      1. Outros\n              - REITERO: a distância máxima a percorrer continua acima de 10 m,\n"
            "              conforme a planta.\nElementos Gráficos\nPlanta Baixa\n      1. Outros\n              - Inconformidades já citadas acima.\n\n"
            "O PPCI deverá ser encaminhado para nova análise.\n")
    ex_ = pl_m.partir(_cia)
    caso("palpite: a CIA vira exigências numeradas, com a seção e a prancha",
         len(ex_) == 2 and ex_[0][0] == "Saída de Emergência" and ex_[0][2].endswith("conforme a planta.")
         and ex_[1][:2] == ("Elementos Gráficos", "Planta Baixa"), str(ex_))
    # 17/11/2026: CIAs de outro analista (Sgt Magalhães) davam 0 exigências — texto sem "- ", texto na linha do
    # "1. Outros" e opção pronta do SOL no próprio item
    _cia2 = ("apresentou as seguintes inconformidades\n\nMedidas de Segurança\n\nSaída de Emergência\n\n"
             "            1. Outros\n               Deverá haver patamares em ambos os lados\n               do vão de porta.\n"
             "Hidrantes e Mangotinhos\n           1. Outros Deverá adequar o volume\n              da reserva técnica.\n"
             "Correções Adicionais\n            1. Ausência de marcação no campo do item “Extintores\n               de incêndio”.\n")
    ex2_ = pl_m.partir(_cia2)
    caso("palpite: a CIA sem hífen, com o texto na linha do '1. Outros' e com opção pronta do SOL também vira exigências",
         [x[2] for x in ex2_] == ["Deverá haver patamares em ambos os lados do vão de porta.",
                                 "Deverá adequar o volume da reserva técnica.",
                                 "Ausência de marcação no campo do item “Extintores de incêndio”."], str(ex2_))
    ws_ = [("dist.", 10, 100, 30, 108, "Dist."), ("max.", 32, 100, 50, 108, "máx."), ("a", 52, 100, 56, 108, "a"),
           ("percorrer", 58, 100, 95, 108, "percorrer"), ("4", 5, 105, 9, 113, "4"), ("ate", 10, 106, 22, 114, "até"),
           ("a", 24, 106, 28, 114, "a"), ("saida", 30, 106, 50, 114, "saída"), ("=", 52, 106, 56, 114, "="), ("15,48", 58, 106, 80, 114, "15,48")]
    caso("palpite: o termo é achado com quebra de linha e um rótulo do desenho no meio (e sem acento)",
         len(pl_m.ocorrencias(ws_, "Dist. máx. a percorrer até a saída")) == 1 and not pl_m.ocorrencias(ws_, "até o hidrante"))
    caso("palpite: palpites.json sobe ao servidor com a pasta; a trava e o temporário não",
         _sinc.chave_valida("A00000001AA001/palpites.json") and not _sinc.chave_valida("A00000001AA001/.palpites.lock")
         and not _sinc.chave_valida("A00000001AA001/.palpites-123.json"))

    def _pdf(linhas, w=900, h=700):
        """PDF mínimo de uma página, com texto em posições dadas (x, y a partir do topo)."""
        txt = "BT /F1 9 Tf " + " ".join("1 0 0 1 %d %d Tm (%s) Tj" % (x, h - y, t) for x, y, t in linhas) + " ET"
        objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>" % (w, h)).encode(),
                ("<< /Length %d >>\nstream\n%s\nendstream" % (len(txt.encode("latin-1")), txt)).encode("latin-1"),
                b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
        out, offs = b"%PDF-1.4\n", []
        for i, o in enumerate(objs, 1):
            offs.append(len(out))
            out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
        x = len(out)
        out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
        return out + b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)
    with tempfile.TemporaryDirectory() as tmp:
        pasta = os.path.join(tmp, "A00000001AA001")
        os.makedirs(os.path.join(pasta, "plantas"))
        for n_ in ("cia-100.txt", "cia-200.txt", "cia-ultima.txt"):
            open(os.path.join(pasta, n_), "w", encoding="utf-8").write(_cia)
        eg = lambda sit, ident, nome, tipo, desc: {"situacao": sit, "tipo": tipo, "descricao": desc, "arquivo": {"id": ident, "nomeArquivo": nome}}
        json.dump({"numero": "A00000001AA001", "elemGraficos": [
            eg("INATIVO", 50, "R00.pdf", "PLANTA_BAIXA", "Planta Baixa"),      # anterior à penúltima CIA: fora
            eg("INATIVO", 150, "R01.pdf", "PLANTA_BAIXA", "Planta Baixa"),     # a que a última CIA analisou
            eg("ATIVO", 250, "R02.pdf", "PLANTA_BAIXA", "Planta Baixa"),       # reenviada
            eg("ATIVO", 120, "IMPL.pdf", "IMPLANTACAO", "Implantação")]},     # ativa e não reenviada
            open(os.path.join(pasta, "api-1.json"), "w", encoding="utf-8"))
        pls = {p["id"]: p for p in pl_m.plantas(pasta)}
        caso("palpite: pranchas da reanálise (reenviada, não reenviada, a que a última CIA analisou; a mais antiga fica fora)",
             sorted(pls) == [120, 150, 250] and pls[150]["lado"] == "antes" and pls[120]["nao_reenviada"] and not pls[250]["nao_reenviada"]
             and pls[250]["arquivo"] == "Planta Baixa (250).pdf" and pls[150]["arquivo"] == "anterior - Planta Baixa (150).pdf"
             and pls[120]["arquivo"] == "Implantação (120).pdf" and not pls[250]["tem"], str(pls))
        caso("elementos gráficos: nome do arquivo como o SOL mostra, sem caractere proibido e sem repetir o tipo",
             pl_m.nome_no_sol("depois", "PLANTA_BAIXA", "Pavilhão", "x.pdf", 7) == "Planta baixa - Pavilhão (7).pdf"
             and pl_m.nome_no_sol("depois", "CORTE", "Corte AA", "x.pdf", 8) == "Corte AA (8).pdf"
             and pl_m.nome_no_sol("depois", "IMPLANTACAO", "Situação/Localização: 1?", "x.pdf", 9) == "Implantação - Situação Localização 1 (9).pdf"
             and pl_m.nome_no_sol("antes", "FACHADA", "", "FACH_R01.pdf", 5) == "anterior - Fachada - FACH_R01 (5).pdf")
        cur_ = [{"n": 1, "tipo": "texto", "esperado": "distância máxima a percorrer de no máximo 10 m", "termo": "Dist. max. a percorrer", "prancha": "planta baixa"},
                {"n": 2, "tipo": "remissiva"}]
        d0 = pl_m.preparar(pasta, cur_)
        caso("palpite: sem a planta na pasta o item fica sem palpite e diz qual falta",
             d0["itens"][0]["estado"] == "sem_palpite" and "Falta baixar" in d0["itens"][0]["motivo"] and d0["itens"][1]["motivo"].startswith("Remete"),
             str(d0["itens"][0]))
        try:
            pl_m.preparar(pasta, [{"n": 1, "tipo": "texto", "termo": "x"}])
            sem_valor = False
        except RuntimeError:
            sem_valor = True
        caso("palpite: exigência de texto sem o valor esperado não é aceita (sem valor, sem palpite)", sem_valor)
        if pl_m.tem_poppler():
            comuns = [(60 + 70 * (i % 10), 60 + 40 * (i // 10), "AMB%02d" % i) for i in range(30)]
            open(os.path.join(pasta, "plantas", "antes-150-R01.pdf"), "wb").write(
                _pdf(comuns + [(300, 400, "Dist. max. a percorrer"), (300, 411, "= 13,76 m")]))
            open(os.path.join(pasta, "plantas", "depois-250-R02.pdf"), "wb").write(
                _pdf(comuns + [(300, 400, "Dist. max. a percorrer"), (300, 411, "= 15,48 m")]))
            d1 = pl_m.preparar(pasta, [])  # a classificação gravada vale: só os recortes são refeitos
            it1 = d1["itens"][0]
            caso("palpite: com as plantas, recorte na nova, contraprova na anterior e o texto que entrou e saiu no trecho",
                 it1["estado"] == "fila" and len(it1["recortes"]) == 1 and it1["recortes"][0]["antes"]["pdf"] == "antes-150-R01.pdf"
                 and any("entrou no texto: 15,48" in f and "saiu do texto: 13,76" in f for f in it1["fatos"]), str(it1)[:500])
            caso("palpite: o recorte sai do PDF como imagem (PNG para a IA, JPEG para a tela)",
                 pl_m.recorte(os.path.join(pasta, "plantas", "depois-250-R02.pdf"), 1, it1["recortes"][0]["caixa"], 60).startswith(b"\x89PNG")
                 and pl_m.recorte_tela(pasta, it1["recortes"][0]).startswith(b"\xff\xd8"))
            _oll, pl_m.OLLAMA = pl_m.OLLAMA, "http://127.0.0.1:9"
            feitos_, motivo_ = pl_m.rodar(pasta, aviso=lambda *_: None)
            pl_m.OLLAMA = _oll
            caso("palpite: sem Ollama neste PC nada roda e o item continua na fila (não vira 'não sei')",
                 feitos_ == 0 and "não está ligada" in motivo_ and pl_m.ler(pasta)["itens"][0]["estado"] == "fila", motivo_)
            pl_m.responder(pasta, {"1": {"resposta": "nao_cumpriu", "nota": "continua 15,48 m"}, "2": {"resposta": "talvez"}})
            # 2.14.5: imagem junto da resposta — gravada na pasta, sobe no Sincronizar, fica se a resposta muda sem imagem
            _png = "data:image/png;base64," + base64.b64encode(b"\x89PNG\r\n\x1a\nteste").decode()
            pl_m.responder(pasta, {"1": {"resposta": "nao_cumpriu", "nota": "x", "imagens": [_png, "data:text/html;base64,PGI+"]}})
            _c1 = pl_m.ler(pasta)["itens"][0]["conferencia"]
            pl_m.responder(pasta, {"1": {"resposta": "nao_cumpriu", "nota": "continua 15,48 m"}})
            caso("palpite: imagem da conferência gravada (só imagem), vai no Sincronizar e fica quando a resposta muda sem ela",
                 _c1["imagens"] == ["conferencia-n1-1.png"] and pl_m.imagem_conferencia(pasta, "conferencia-n1-1.png").startswith(b"\x89PNG")
                 and pl_m.ler(pasta)["itens"][0]["conferencia"]["imagens"] == ["conferencia-n1-1.png"]
                 and _sinc.chave_valida("A00000001AA001/conferencia-n1-1.png") and not _sinc.chave_valida("A00000001AA001/x.png"),
                 str(_c1.get("imagens")))
            try:
                pl_m.imagem_conferencia(pasta, "../palpites.json"); _fura = True
            except RuntimeError:
                _fura = False
            caso("palpite: imagem da conferência não lê fora do padrão de nome", not _fura)
            d2 = pl_m.preparar(pasta, [])
            caso("palpite: a conferência do analista fica gravada no item e sobrevive a preparar de novo",
                 d2["itens"][0]["conferencia"]["resposta"] == "nao_cumpriu" and "conferencia" not in d2["itens"][1]
                 and d2["itens"][0]["tipo"] == "texto" and not pl_m.valido(pasta), str(d2["itens"][0].get("conferencia")))
            # 2.12.0: prancha baixada com o nome antigo continua valendo e passa para o nome do SOL, com o palpites.json junto
            caso("elementos gráficos: prancha de nome antigo é achada pelo id", pl_m.plantas(pasta)[1]["arquivo"] == "depois-250-R02.pdf"
                 and [(g["rotulo"], [i["tem"] for i in g["itens"]]) for g in pl_m.elementos(pasta)] == [("Planta baixa", [True]), ("Implantação", [False])])
            _nren = pl_m.nomes_do_sol(pasta)
            _dren = json.dumps(pl_m.ler(pasta), ensure_ascii=False)
            caso("elementos gráficos: renomeia para o nome do SOL, leva o cache ao lado e acerta o palpites.json",
                 _nren == 2 and os.path.exists(os.path.join(pasta, "plantas", "Planta Baixa (250).pdf"))
                 and os.path.exists(os.path.join(pasta, "plantas", "Planta Baixa (250).pdf.bbox.json"))
                 and "depois-250" not in _dren and "antes-150" not in _dren and "anterior - Planta Baixa (150).pdf" in _dren
                 and pl_m.recorte_tela(pasta, pl_m.ler(pasta)["itens"][0]["recortes"][0]).startswith(b"\xff\xd8"), _dren[:300])
            open(os.path.join(pasta, "cia-300.txt"), "w", encoding="utf-8").write(_cia)
            caso("palpite: CIA nova depois dos palpites marca o arquivo como antigo", "CIA anterior" in pl_m.valido(pasta), pl_m.valido(pasta))
        _pedidos = []
        _rb = pl_m.baixar_plantas(pasta, lambda i: _pedidos.append(i) or b"%PDF-1.4 teste", ("depois",))
        caso("elementos gráficos: o botão baixa só as ativas que faltam, já com o nome do SOL",
             _pedidos == [120] and not _rb["falhas"] and os.path.exists(os.path.join(pasta, "plantas", "Implantação (120).pdf")), str((_pedidos, _rb)))
    _ins = _chat.INSTRUCOES.format(codigo="A00000001AA001", pasta="P")
    caso("palpite: a conversa só prepara com a linha [IA local], grava pelo sseg.py e apresenta com o bloco azul",
         # 14/11/2026: o heredoc com JSON foi barrado na janela ("brace with quote character"); o argumento entre aspas simples passa
         'palpite --pasta "P" preparar \'[{"n": 1, "tipo": "texto"' in _ins and "<<'FIM'\n[{" not in _ins and "[IA local]" in _ins
         and "```sseg-palpites" in _chat.GUIA_VISUAL and '"sseg-palpites"' in js and "perguntas azul" in js and "linhaIALocal" in js)
    # 22c. classificação pela IA local (2.13.8): o termo que a IA propõe só vale se está escrito na prancha nova; senão
    # vale uma palavra da própria exigência que apareça em poucos lugares; sem nenhuma, a exigência fica com o motivo
    _pal_orig, _oll_orig = pl_m.palavras, pl_m._ollama
    pl_m.palavras = lambda pdf: ({1: [("moega", 10, 10, 20, 20, "MOEGA"), ("moega", 30, 30, 40, 40, "MOEGA"), ("mesma", 70, 70, 80, 80, "MESMA"), ("sala", 50, 50, 60, 60, "SALA")] + [("rampa", 9, i, 9, i, "RAMPA") for i in range(20)]}, {1: (600, 600)})
    _todas = [{"lado": "depois", "tem": True, "descricao": "PPCI", "nome": "x.pdf", "arquivo": "x.pdf"}]
    try:
        _c1 = pl_m._termo_valido("P", _todas, {"tipo": "ausencia", "termo": "VIATURA", "termo_antes": "", "prancha": "", "motivo": ""},
                                 "O número de ordem deve ficar na mesma camada; deverá informar ocupação, área e população da MOEGA e da RAMPA")
        _c2 = pl_m._termo_valido("P", _todas, {"tipo": "desenho", "termo": "PATAMAR", "termo_antes": "", "prancha": "", "motivo": ""},
                                 "patamares nos dois lados das portas")
        _c3 = pl_m._termo_valido("P", _todas, {"tipo": "fora_da_planta", "termo": "ART", "termo_antes": "", "prancha": "", "motivo": "x"}, "ART")
        pl_m._ollama = lambda caminho, dados=None, timeout=900: {"message": {"content": json.dumps(
            {"tipo": "texto", "esperado": "", "termo": "SALA", "termo_antes": "", "prancha": "", "motivo": ""})}}
        pl_m.exigencias, _ex_orig = (lambda p: [("Elementos Gráficos", "PPCI", "Cotar a sala")]), pl_m.exigencias
        pl_m.plantas, _pl_orig = (lambda p: _todas), pl_m.plantas
        try:
            _cl = pl_m.classificar("P")
        finally:
            pl_m.exigencias, pl_m.plantas = _ex_orig, _pl_orig
    finally:
        pl_m.palavras, pl_m._ollama = _pal_orig, _oll_orig
    caso("palpite (2.13.8): termo que não está na planta é trocado por palavra da exigência que está; sem nenhuma, fica o motivo",
         _c1["termo"] == "MOEGA" and not _c2["termo"] and _c2["motivo"] and _c3["termo"] == "ART"
         and _cl == [{"tipo": "ausencia", "esperado": "Cotar a sala", "termo": "SALA", "termo_antes": "", "prancha": "", "motivo": "", "n": 1}],
         str((_c1, _c2, _cl)))
    caso("palpite (2.13.8): o programa chama 'auto' (a IA local classifica) e a conversa só apresenta",
         hasattr(pl_m, "automatico") and '"auto" if hasattr(self._palpite(), "automatico")' in open(os.path.join(RAIZ, "sseg", "app", "api.py"), encoding="utf-8").read()
         and "[IA local] em andamento" in _chat.INSTRUCOES and "[IA local] em andamento" in js)
    import resumo_ia as ri_m
    with tempfile.TemporaryDirectory() as _t:
        open(os.path.join(_t, "documentos-ia.md"), "w", encoding="utf-8").write(
            "## Cada documento × SOL\n\n### 1-ART.pdf (1 pág.)\n\n- ✓ **RT FULANO**: nome encontrado\n- ✗ **área**: documento 100 m² × SOL 120 m²\n")
        open(os.path.join(_t, "camadas.txt"), "w", encoding="utf-8").write(
            "CAMADAS\nACHADOS:\n[campo 4] Camada de Alarme e a medida não está marcada no campo 4.\nOBSERVAÇÕES (fracas):\n- [x] cor\n")
        json.dump({"itens": [{"n": 1, "rotulo": {"titulo": "Palpite: Cumpriu"}}, {"n": 2, "estado": "fila"}]},
                  open(os.path.join(_t, "palpites.json"), "w", encoding="utf-8"))
        _ri = ri_m.gravar(_t)
    caso("resumo-ia (2.13.8): divergência de documento e achado de camada no amarelo, palpite no azul, sem as observações fracas",
         "1-ART.pdf: área: documento 100 m² × SOL 120 m²" in _ri and "[campo 4] Camada de Alarme" in _ri and "cor" not in _ri
         and "nº 1: Palpite: Cumpriu" in _ri and "nº 2: na fila" in _ri and _ri.index("AMARELA") < _ri.index("AZUL"), _ri)
    # 22b. prancha com o texto convertido em desenho (17/11/2026): comparação do valor sem IA; com PyMuPDF, a cota
    # sintética (traços curtos ao lado de uma linha longa) é achada e o palpite sai com uma leitura de mentira
    import cotas_desenho as cd_m
    caso("cotas desenhadas: o valor esperado sai do texto em metros (sem 'P3', 'A-2' nem '1/50'; milhar e cm/mm)",
         cd_m.valores("porta P3 de no mínimo 1,10 m e 90 cm") == [1.1, 0.9] and cd_m.valores("A-2 com 1.496,51 m²") == [1496.51]
         and cd_m.valores("escala 1/50") == [] and cd_m.valores("largura 2.400 mm") == [2.4] and cd_m.valores("altura 12,15m") == [12.15])
    caso("cotas desenhadas: a leitura bate pelos algarismos (12,15 = 1215 cm; '|' é o 1) e não por aproximação",
         cd_m.bate("12|5", 12.15) and cd_m.bate("1215", 12.15) and cd_m.bate("12,15", 12.15) and not cd_m.bate("1,25", 12.15)
         and not cd_m.bate("1215", 12.5) and cd_m.bate("120", 1.2) and not cd_m.bate("9", 0.9) and not cd_m.bate("", 1.2))
    _cert, _conf = cd_m.procurar([{"id": "a", "a": "1215", "b": "12|5"}, {"id": "b", "a": "1,25", "b": "1215"}, {"id": "c", "a": "Sala"}], [12.15])
    caso("cotas desenhadas: as duas leituras iguais contam; só uma igual vai para conferir",
         [x["id"] for x in _cert] == ["a"] and [x["id"] for x in _conf] == ["b"])
    try:
        import pymupdf as _fz
    except ImportError:
        _fz = None
    if _fz and pl_m.tem_poppler():
        def _pdf_cota(arq, x0=300, y0=300):
            doc = _fz.open()
            pg = doc.new_page(width=600, height=600)
            for i in range(14):  # "número": zigue-zague de traços curtos, 26 x 6 pt
                pg.draw_line((x0 + 2 * i, y0 + (6 if i % 2 else 0)), (x0 + 2 * i + 2, y0 + (0 if i % 2 else 6)), width=0.3)
            pg.draw_line((x0 - 40, y0 + 9), (x0 + 70, y0 + 9), width=0.3)   # linha de cota logo abaixo
            pg.draw_line((50, 50), (50, 500), width=0.3)                      # linha qualquer, longe
            doc.save(arq)
        with tempfile.TemporaryDirectory() as tmp:
            pasta = os.path.join(tmp, "A00000002AA001")
            os.makedirs(os.path.join(pasta, "plantas"))
            _cia2 = ("apresentou as seguintes inconformidades\nElementos Gráficos\nCorte\n            - Informar a altura de 12,15 m.\n"
                     "O PPCI deverá ser encaminhado para nova análise\n")
            for n_ in ("cia-100.txt", "cia-200.txt", "cia-ultima.txt"):
                open(os.path.join(pasta, n_), "w", encoding="utf-8").write(_cia2)
            json.dump({"elemGraficos": [{"situacao": "INATIVO", "tipo": "CORTE", "descricao": "Corte", "arquivo": {"id": 150, "nomeArquivo": "C0.pdf"}},
                                        {"situacao": "ATIVO", "tipo": "CORTE", "descricao": "Corte", "arquivo": {"id": 250, "nomeArquivo": "C1.pdf"}}]},
                      open(os.path.join(pasta, "api-1.json"), "w", encoding="utf-8"))
            _pdf_cota(os.path.join(pasta, "plantas", "Corte (250).pdf"))
            _pdf_cota(os.path.join(pasta, "plantas", "anterior - Corte (150).pdf"), 200, 200)
            with _fz.open(os.path.join(pasta, "plantas", "Corte (250).pdf")) as _doc:
                _cs = cd_m.candidatos(_doc[0])
                _png = cd_m.imagem(_doc[0], _cs[0]) if _cs else b""
            caso("cotas desenhadas: a cota feita de traços é achada pela linha ao lado e recortada como PNG",
                 len(_cs) == 1 and abs(_cs[0]["ang"]) < 1 and _png.startswith(b"\x89PNG"), str(_cs))
            d3 = pl_m.preparar(pasta, [{"n": 1, "tipo": "texto", "esperado": "altura de 12,15 m", "motivo": "texto em desenho"}])
            it3 = d3["itens"][0]
            caso("cotas desenhadas: sem palavra no PDF a exigência de valor vai para a leitura de cotas, com a anterior",
                 it3["estado"] == "fila" and it3["cotas"][0]["pdf"] == "Corte (250).pdf" and it3["cotas"][0]["antes"]["pdf"] == "anterior - Corte (150).pdf"
                 and "convertido em desenho" in it3["fatos"][0] and not it3["motivo"], str(it3)[:400])
            _lidos = {}
            def _falso(png, _n=[0]):
                _n[0] += 1
                _lidos[_n[0]] = png[:4]
                return "1215" if _n[0] <= 2 else "Sala"   # nova: 1215 nas duas leituras; anterior: palavra
            _orig = (pl_m.ia_local, pl_m._transcrever)
            pl_m.ia_local, pl_m._transcrever = (lambda: (True, "")), _falso
            try:
                pl_m.rodar(pasta, aviso=lambda *_: None)
            finally:
                pl_m.ia_local, pl_m._transcrever = _orig
            it4 = pl_m.ler(pasta)["itens"][0]
            caso("cotas desenhadas: valor achado na nova e não na anterior sai, no máximo, como palpite fraco, com o recorte",
                 it4["estado"] == "pronto" and it4["rotulo"]["titulo"].startswith("Palpite fraco (Cumpriu):") and it4["controle"]["veredito"] == "nao_cumpriu"
                 and len(it4["recortes"]) == 1 and it4["recortes"][0]["antes"] and len(_lidos) == 3, str(it4)[:500])
            d5 = pl_m.preparar(pasta, [])
            caso("cotas desenhadas: preparar de novo mantém o palpite e os recortes; a leitura fica em cache ao lado do PDF",
                 d5["itens"][0]["estado"] == "pronto" and len(d5["itens"][0]["recortes"]) == 1
                 and os.path.exists(os.path.join(pasta, "plantas", "Corte (250).pdf.cotas.json")))
    # 23. camadas das pranchas (sem IA, sem PyMuPDF: a conferência recebe o inventário já lido do PDF)
    import camadas as cm_m
    caso("camadas: nomes de camada viram medida (prefixo, sigla, abreviação, erro de digitação)",
         cm_m.medida_da_camada("PI-EXT")[0] == "extintores" and cm_m.medida_da_camada("MED. SEG. ISOL. RISCO")[0] == "isolamento"
         and cm_m.medida_da_camada("PI- BARRA AINTI-PÂNICO")[0] == "saida" and cm_m.medida_da_camada("Incêndio_hidrante")[0] == "hidrantes"
         and cm_m.medida_da_camada("HIDRANTE URBANO")[0] == "hidrante_urbano" and cm_m.medida_da_camada("PI - ARQUITETURA")[0] == "base"
         and cm_m.medida_da_camada("EXT-DMP") == ("extintores", True) and cm_m.medida_da_camada("01 - SOS")[0] == "sinalizacao")
    _med = [{"chave": "extintores", "nome": "Extintores de Incêndio", "laudo": False},
            {"chave": "saida", "nome": "Saída de Emergência", "laudo": False},
            {"chave": "alarme", "nome": "Alarme de Incêndio", "laudo": False},
            {"chave": "deteccao", "nome": "Detecção de Incêndio", "laudo": False}]
    _inv = {"camadas": ["PI-EXT", "PI-SAIDA", "PI-DETECCAO", "ARQ"], "por_camada": {
        "PI-EXT": {"tracos": 50, "vermelho": 50, "texto": "PQS 2-A:20-B:C · DMP= 20m · ALM-1 · ALM-2 · ALM-3"},
        "PI-SAIDA": {"tracos": 30, "vermelho": 5, "texto": "1,20 · D-1 · 40 pessoas"},
        "PI-DETECCAO": {"tracos": 10, "vermelho": 10, "texto": ""},
        "ARQ": {"tracos": 900, "vermelho": 0, "texto": "Sala 45,20m² · Depósito 30,00m² · " + "NOTA GERAL " * 150}}}
    _r = cm_m.conferir(_med, [("Térreo", _inv, "PLANTA_BAIXA")])
    _it = {f["item"] for f in _r["fatos"]}
    _n2 = next((f["texto"] for f in _r["fatos"] if f["item"] == "nota02"), "")
    caso("camadas: alarme sem camada (com o texto dele na de extintores), mistura, cor, L.2 sem laudo e Nota 02",
         {"sem_camada", "mistura", "cor", "fora_coluna_A", "nota02"} <= _it and "sem área" in _n2 and "ARQ" in _n2
         and any("Alarme" in f["texto"] and "PI-EXT" in f["texto"] for f in _r["fatos"] if f["item"] == "sem_camada"), str(_r["fatos"]))
    _r = cm_m.conferir([dict(_med[3], laudo=True)], [("Térreo", _inv, "PLANTA_BAIXA"), ("2º pav", {"camadas": []}, "PLANTA_BAIXA"),
                                                     ("Termo", {"camadas": []}, "CORTE")])
    caso("camadas: detecção de laudo de inviabilidade não é 'fora da coluna A'; planta baixa sem camadas é dita, corte não",
         "fora_coluna_A" not in {f["item"] for f in _r["fatos"]}
         and [f["texto"][:6] for f in _r["fatos"] if f["item"] == "sem_camadas"] == ["2º pav"], str(_r["fatos"]))
    _inv2 = {"camadas": ["EXTINTORES", "EXT-NUMERO", "EXT-DMP"], "por_camada": {n: {"tracos": 30, "vermelho": 30, "texto": ""}
                                                                                for n in ("EXTINTORES", "EXT-NUMERO", "EXT-DMP")}}
    def _pav(n):  # "6 EXTINTORES" muda por pavimento; "EXTINTORES" é a legenda, igual em todas
        return {"camadas": ["6 EXTINTORES", "EXTINTORES"], "por_camada": {
            "6 EXTINTORES": {"tracos": 10 + n, "vermelho": 10 + n, "texto": "EXT %d" % n},
            "EXTINTORES": {"tracos": 39, "vermelho": 0, "texto": "PQS"}}}
    _r3 = cm_m.conferir(_med[:1], [("P%d" % n, _pav(n), "PLANTA_BAIXA") for n in range(3)])
    caso("camadas: camada idêntica em 3 pranchas é legenda (51398): não conta como segunda camada nem pela cor",
         not [f for f in _r3["fatos"] if f["item"] in ("varias_camadas", "cor")], str(_r3["fatos"]))
    # 2.15.0: texto em desenho; a IA local transcreve a camada da saída e o script confere (sem Ollama no teste)
    _fi = cm_m.conferir_ia([("Térreo", ["N.º 01", "S12", "1,20", "0,80", "DIST. MAX. A PERCORRER 27,5 m"]),
                            ("Pav. 2", ["SALA 01", "F-8", "A= 32,80 m²", "26 PESSOAS", "1,10"])])
    caso("camadas + IA local: o texto transcrito passa pelas mesmas regras (Nota 02 o que falta; Nota 01 sem distância)",
         [f["item"] for f in _fi] == ["ia_nota02", "ia_nota02", "ia_sem_distancia"] and all(f["ia"] for f in _fi)
         and _fi[0]["texto"].endswith("Não achou: ocupação, área, população.") and "1,20" in _fi[0]["texto"]
         and _fi[1]["texto"].endswith("Achou largura, ocupação, área e população.")
         and not cm_m.observacao(_fi[0]) and "LIDO PELA IA LOCAL" in cm_m.relatorio({"fatos": _fi, "camadas": {}}), str(_fi))
    try:
        _fz = cm_m.tem_pymupdf()
    except RuntimeError:
        _fz = None
    if _fz:
        _tmpd = tempfile.mkdtemp()
        _doc = _fz.open()
        _pg = _doc.new_page(width=2000, height=1400)
        _oc_s, _oc_a = _doc.add_ocg("SAIDA DE EMERGENCIA"), _doc.add_ocg("ARQUITETURA")
        _pg.insert_text((100, 100), "1,20", oc=_oc_s)
        _pg.draw_line((100, 120), (300, 120), oc=_oc_s)
        _pg.insert_text((1800, 1300), "SALA", oc=_oc_a)
        _pdfc = os.path.join(_tmpd, "pb.pdf")
        _doc.save(_pdfc)
        _ims = cm_m.imagens_da_camada(_pdfc, "saida")
        caso("camadas + IA local: só a camada da saída, recortada onde ela desenha, vai em imagem; sem a camada, nada",
             len(_ims) == 1 and _ims[0][:4] == b"\x89PNG" and cm_m.imagens_da_camada(_pdfc, "alarme") == [], str(len(_ims)))
        shutil.rmtree(_tmpd, ignore_errors=True)
    caso("camadas: número de ordem lido do texto (RT 05 P08 Anexo A) sem pegar capacidade, ocupação nem norma",
         cm_m.numeros("02 · A-03 · ALM- 1 · EXT- 85 · 09 - 2° PAV. · H 10 - TIPO 3 · HIDRANTE 04 · SHSC T3 Nº 05 · "
                      "N° 75, 76 · 2A/20BC · 4-A:40-B:C · 20.000 L · 6 KG · RTCBMRS n° 22/2023 · EXTINTOR Nº 01= 18,50 M")
         == [2, 3, 1, 85, 9, 10, 4, 5, 75, 76]
         and cm_m.numeros("E-1 · E5 · EXT- 7", "extintores") == [7]
         # 17/11/2026: agente colado ao número (49678) e lista do pavimento tipo (49433); cota "2,50" não
         and cm_m.numeros("E01-PQS · E04 - PQS · EXT 02 CO2 · N48,50,52,54 · 2,50 · 1,20,30 · 02 AP") == [1, 4, 2, 48, 50, 52, 54])

    import documentos as _doc
    _api_d = {"envolvidos": {"rts": [{"nome": "RT X", "arquivo": {"id": 1, "nomeArquivo": "art.pdf"}, "arquivos": [{"id": 1, "nomeArquivo": "art.pdf"}]}],
                             "rus": [{"nome": "RU Y", "arquivo": None, "arquivos": [], "procurador": {"nome": "RT X", "arquivo": {"id": 2, "nomeArquivo": "proc.pdf"}}}],
                             "proprietarios": [{"nome": "P Z", "procurador": {"nome": "RT X", "arquivo": {"id": 3, "nomeArquivo": "proc2.pdf"}}}]}}
    caso("documentos: ART do RT e procurações dos envolvidos, sem repetir arquivo (17/11/2026)",
         [(x["id"], x["papel"]) for x in _doc.lista(_api_d)] == [(1, "RT"), (2, "Procuração (responsável pelo uso)"), (3, "Procuração (proprietário)")]
         and bool(_doc.CARIMBO.search("Assinado utilizando o(s) seguinte(s) selo(s) do gov.br")),
         str(_doc.lista(_api_d)))
    try:
        import pyhanko  # noqa: F401
        with tempfile.TemporaryDirectory() as _t:
            _p0 = os.path.join(_t, "sem.pdf")
            open(_p0, "wb").write(_pdf([(50, 50, "PROCURACAO")]))
            _p1 = os.path.join(_t, "quebrada.pdf")   # campo de assinatura sem certificado legível (como a do 49826)
            open(_p1, "wb").write(_pdf([(50, 50, "PROCURACAO"), (50, 80, "/ByteRange [0 1 2 3]")]))
            # sem pdfsig no PATH (o PC Windows): o pyHanko responde
            caso("documentos: sem o pdfsig (PC Windows), o pyHanko lê o certificado; campo quebrado não vira 'sem assinatura'",
                 _doc._pyhanko(_p0) == [] and _doc._pyhanko(_p1) == [{"nome": "", "quando": "", "integra": False}])
    except ImportError:
        pass

    def _pb(ext, fora=""):
        return {"camadas": ["EXT", ""], "por_camada": {"EXT": {"tracos": 40, "vermelho": 40, "texto": ext},
                                                        "": {"tracos": 5, "vermelho": 0, "texto": fora},
                                                        "ARQ": {"tracos": 9, "vermelho": 0, "texto": "SALA " * 120}}}
    _m_ext = [{"chave": "extintores", "nome": "Extintores de Incêndio", "laudo": False}]
    _o = cm_m.conferir(_m_ext, [("Térreo", _pb("01 · PQS · 02 · 02 · 05"), "PLANTA_BAIXA"),
                                ("Implantação", _pb("01"), "IMPLANTACAO"),
                                ("Portaria", _pb("PQS ABC · 4-A:40-B:C"), "PLANTA_BAIXA"),
                                ("Guarita", _pb("", "EXT- 06 · E-1"), "PLANTA_BAIXA")])
    _ot = {f["item"]: f["texto"] for f in _o["fatos"] if f["grupo"].startswith("RT 05 P08")}
    caso("camadas: número de ordem repetido, buraco, sem número e fora da camada; implantação não conta",
         _ot.get("ordem_repetido") == "Extintores: número de ordem repetido: 02 (2 vezes em Térreo)."
         and "não aparece 03–04" in _ot.get("ordem_buraco", "")
         and "Portaria" in _ot.get("ordem_sem_numero", "")
         and _ot.get("ordem_fora_da_camada", "").endswith('Guarita · "fora de camada" (1).'), str(_ot))
    _r = cm_m.conferir(_med[:1], [("Térreo", _inv2, "PLANTA_BAIXA")])
    caso("camadas: a mesma medida em duas camadas é dita; a camada de distância dela não conta",
         [f["texto"] for f in _r["fatos"] if f["item"] == "varias_camadas"] == ['Extintores em 2 camadas (Térreo): "EXTINTORES"; "EXT-NUMERO".']
         and cm_m.observacao({"item": "cor", "texto": ""}) and not cm_m.observacao({"item": "nota02", "texto": ""})
         and cm_m.observacao({"item": "sem_camada", "texto": "Acesso de viaturas (campo 4): ..."})
         and not cm_m.observacao({"item": "sem_camada", "texto": "Alarme (campo 4): ..."}),
         str(_r["fatos"]))
    _r = cm_m.conferir([], [("Térreo", _inv, "PLANTA_BAIXA")])
    caso("camadas: sem o campo 4 no JSON, nada de 'medida não marcada'", {f["item"] for f in _r["fatos"]} >= {"sem_campo4"}
         and "camada_sem_medida" not in {f["item"] for f in _r["fatos"]}, str(_r["fatos"]))
    _r = cm_m.conferir(_med[:2], [("Térreo", {"camadas": ["PI-EXT", "PI-SAIDA"], "por_camada": {
        "PI-EXT": {"tracos": 50, "vermelho": 50, "texto": ""}, "PI-SAIDA": {"tracos": 40, "vermelho": 40, "texto": ""}}}, "PLANTA_BAIXA")])
    caso("camadas: texto convertido em desenho vira 'conferir na planta', nunca 'sem área/população' nem 'sem DMP'",
         {f["item"] for f in _r["fatos"]} == {"ilegivel"}, str(_r["fatos"]))
    caso("camadas: ocupação entre parênteses sem hífen conta; folha A1 solta não",
         cm_m.sinais("ESCRITÓRIO (D1) · 4 pessoas")["ocupacao"] == 1 and cm_m.sinais("FOLHA A1")["ocupacao"] == 0)
    print(f"testar.py: {oks} ok, {len(falhas)} falha(s)")
    for f in falhas:
        print("FALHA", f)
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
