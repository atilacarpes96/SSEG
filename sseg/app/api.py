# -*- coding: utf-8 -*-
"""
api.py — a ponte da interface HTML (SSEG.exe 2.0, pywebview) com a lógica que já existia.

Cada método público é chamado pelo JavaScript (window.pywebview.api.<nome>) numa thread própria
e devolve dados simples (dict, list, str). Nada de regra nova aqui: tudo vem dos módulos da 1.x
(instalar, git_sinc, claude_local, busca, gasto, relato, sol_entrar) e das funções de sseg_app.
O quadro da 1.x virou "Detalhes": log() manda a linha para a tela e guarda para o Reportar bug.
"""

import base64
import json
import os
import re
import subprocess
import tempfile
import webbrowser

import busca
import chat
import claude_local
import gasto
import git_sinc
import instalar
import processo
import relato
import sol_entrar
import sseg_app as base

CODIGO = re.compile(r"^A\d{8}[A-Z]{2}\d{3}$")


class Api:
    def __init__(self):
        self._janela = None
        self._registro = []
        self._dados_git = None
        self._erros_js = []
        self._claude = None
        self._conversas = {}

    # ---------------------------------------------------------------- infraestrutura
    def _ligar(self, janela):
        self._janela = janela

    def _log(self, *linhas):
        self._registro.extend(linhas)
        if self._janela:
            try:
                self._janela.evaluate_js("SSEG.log(%s)" % json.dumps(list(linhas)))
            except Exception:  # janela fechando
                pass

    def _cfg(self):
        cfg = base.ler_config()
        casa = os.path.expanduser("~")
        cfg.setdefault("clone", os.path.join(casa, "Documents", "SSEG"))
        cfg.setdefault("processos", os.path.join(casa, "Desktop", "print ppci"))
        return cfg

    def _clone(self):
        return self._cfg()["clone"]

    def erro_js(self, msg):
        """window.onerror da página: vai para o quadro e, no build, para previa-erros.txt."""
        self._erros_js.append(str(msg))
        self._log("✗ erro na tela: " + str(msg)[:300])

    def registro(self):
        return self._registro[-200:]

    # ---------------------------------------------------------------- início
    def inicio(self):
        cfg = self._cfg()
        try:
            fluxos = claude_local.ler_fluxos(cfg["clone"])
        except (OSError, ValueError, KeyError):
            fluxos = []
        return {"versao": base.VERSAO, "painel": base.PAINEL_URL, "config": cfg, "fluxos": fluxos,
                "primeira_vez": not base.eh_clone(cfg["clone"]) or not os.path.isdir(cfg["processos"])}

    # ---------------------------------------------------------------- barra de estado
    def estado_programas(self):
        achados = instalar.localizar()
        self._claude = achados.get("claude")
        logado = bool(self._claude) and instalar.claude_logado(self._claude)
        itens = []
        for chave, nome, _id in instalar.PROGRAMAS:
            ok = bool(achados.get(chave))
            extra = "" if chave != "claude" or not ok else (" (logado)" if logado else " (falta entrar)")
            itens.append({"nome": nome + extra, "ok": ok and (chave != "claude" or logado)})
        falta = instalar.faltando(achados)
        return {"ok": not falta and logado, "falta": bool(falta), "logado": logado, "itens": itens}

    def estado_pastas(self):
        cfg = self._cfg()
        clone_ok, proc_ok = base.eh_clone(cfg["clone"]), os.path.isdir(cfg["processos"])
        return {"ok": clone_ok and proc_ok, "clone": cfg["clone"], "processos": cfg["processos"],
                "clone_ok": clone_ok, "processos_ok": proc_ok}

    def estado_servidor(self):
        """Sem conectar: só confere se este PC tem o apelido sseg-servidor no ~/.ssh/config.
        Quem não tem servidor fica neutro, não em alerta."""
        cfg = os.path.join(os.path.expanduser("~"), ".ssh", "config")
        try:
            texto = open(cfg, encoding="utf-8", errors="replace").read()
        except OSError:
            texto = ""
        tem = bool(re.search(r"^\s*Host\s+(.*\s)?sseg-servidor(\s|$)", texto, re.M | re.I))
        return {"configurado": tem}

    def estado_github(self):
        clone = self._clone()
        if not base.eh_clone(clone):
            return {"ok": False, "erro": "A pasta do SSEG não é um clone (Configuração → Pastas)."}
        try:
            d = base.verificar(clone)
        except RuntimeError as e:
            return {"ok": False, "erro": str(e)}
        self._dados_git = d
        return {"ok": not d["atras"] and not d["sujos"] and not d["frente"], **d}

    def versao_nova(self):
        return base.versao_nova_do_programa()

    # ---------------------------------------------------------------- configuração
    def salvar_pastas(self, clone, processos):
        cfg = self._cfg()
        cfg.update({"clone": clone.strip(), "processos": processos.strip()})
        base.gravar_config(cfg)
        return cfg

    def escolher_pasta(self, atual=""):
        import webview
        r = self._janela.create_file_dialog(webview.FOLDER_DIALOG, directory=atual or "")
        return r[0] if r else None

    def criar_pastas(self, clone, processos):
        self.salvar_pastas(clone, processos)
        linhas = base.preparar_pastas(clone.strip(), processos.strip())
        self._log("— Pastas —", *linhas)
        return linhas

    def instalar_tudo(self):
        resto = instalar.instalar(lambda l: self._log(l))
        return {"resto": resto, **self.estado_programas()}

    def entrar_claude(self):
        claude = self._claude or instalar.localizar().get("claude")
        if not claude:
            raise RuntimeError("Instale o Claude Code antes (\"Instalar o que falta\").")
        instalar.abrir_login(claude)
        self._log("Abri a janela de login: entre pelo navegador e depois clique em \"Conferir\".")

    # ---------------------------------------------------------------- conversas e processos
    def prompt(self, fluxo_id, codigo=""):
        f = self._fluxo(fluxo_id)
        return claude_local.montar_prompt(f, codigo)

    def _fluxo(self, fluxo_id):
        for f in claude_local.ler_fluxos(self._clone()):
            if f["id"] == fluxo_id:
                return f
        raise RuntimeError("Tipo de conversa desconhecido: " + fluxo_id)

    def abrir_conversa(self, fluxo_id, codigo=""):
        f = self._fluxo(fluxo_id)
        p = claude_local.montar_prompt(f, codigo)
        claude = self._claude or instalar.localizar().get("claude")
        if not claude:
            raise RuntimeError("Falta o Claude Code (Configuração → Programas).")
        claude_local.iniciar(self._clone(), f, p, claude)
        self._log("— Conversa — %s aberta (%s)." % (f["titulo"], f["modelo_texto"]))

    def processos(self):
        """Pastas de processo (A000…) na pasta dos processos, a mais mexida primeiro. Só lê nomes e datas."""
        raiz = self._cfg()["processos"]
        out = []
        try:
            nomes = os.listdir(raiz)
        except OSError:
            return out
        for n in nomes:
            p = os.path.join(raiz, n)
            if not (os.path.isdir(p) and CODIGO.match(n)):
                continue
            arqs = [os.path.join(p, a) for a in os.listdir(p)]
            quando = max([os.path.getmtime(a) for a in arqs] + [os.path.getmtime(p)])
            out.append({"codigo": n, "quando": quando, "arquivos": len(arqs),
                        "cia": any(re.match(r"CIA \d+", os.path.basename(a)) for a in arqs),
                        "analise": os.path.exists(os.path.join(p, "analise.json"))})
        out.sort(key=lambda x: -x["quando"])
        return out[:30]

    def abrir_processo(self, codigo):
        if not CODIGO.match(codigo):
            raise RuntimeError("Código inválido.")
        base.abrir(os.path.join(self._cfg()["processos"], codigo))

    def abrir_pasta(self, qual):
        base.abrir(self._cfg()[qual])

    # ---------------------------------------------------------------- janela do processo (2.1)
    def _pasta_proc(self, codigo):
        if not CODIGO.match(codigo or ""):
            raise RuntimeError("Código de processo no formato A00012345AA001.")
        return os.path.join(self._cfg()["processos"], codigo)

    def _reg(self):
        return processo._registro(self._clone())

    def processo_abrir(self, codigo):
        """Só lê: pasta, JSON do SOL, checklist e analise.json. Não sobe o Claude."""
        pasta = self._pasta_proc(codigo)
        if not os.path.isdir(pasta):
            raise RuntimeError("Não há pasta %s na pasta dos processos." % codigo)
        d = processo.montar(self._clone(), pasta)
        c = self._conversas.get(codigo)
        d["ocupado"] = bool(c and c.ocupado)
        return d

    def processo_registro(self, codigo):
        return self._reg().ler(self._pasta_proc(codigo))

    def processo_marcar(self, codigo, grupo, chave, valor):
        if grupo not in ("passos", "itens"):
            raise RuntimeError("grupo inválido")
        return self._reg().marcar(self._pasta_proc(codigo), grupo, chave, valor)

    def processo_pendencia(self, codigo, texto):
        return self._reg().pendencia(self._pasta_proc(codigo), texto, origem="analista")

    def processo_exigencia(self, codigo, texto, medida="", fundamento=""):
        return self._reg().exigencia(self._pasta_proc(codigo), texto, medida, fundamento, origem="analista")

    def processo_atualizar(self, codigo, colecao, id_, campos):
        """O programa muda resposta/feita da pendência e final/fundamento da exigência. Rascunho não."""
        livres = {"pendencias": {"resposta", "feita", "enviada"}, "exigencias": {"final", "fundamento", "medida"}}[colecao]
        campos = {k: v for k, v in (campos or {}).items() if k in livres}
        return self._reg().atualizar(self._pasta_proc(codigo), colecao, id_, **campos)

    def processo_remover(self, codigo, colecao, id_):
        self._reg().remover(self._pasta_proc(codigo), colecao, id_)

    def processo_mover(self, codigo, id_, delta):
        reg = self._reg()
        pasta = self._pasta_proc(codigo)
        d = reg.ler(pasta)
        ex = d["exigencias"]
        i = next((k for k, e in enumerate(ex) if e["id"] == id_), None)
        j = None if i is None else i + int(delta)
        if i is not None and 0 <= j < len(ex):
            ex[i], ex[j] = ex[j], ex[i]
            reg.gravar(pasta, d)
        return d

    def processo_laudo(self, codigo):
        return processo.montar(self._clone(), self._pasta_proc(codigo))["laudo"]

    def abrir_pasta_processo(self, codigo):
        base.abrir(self._pasta_proc(codigo))

    # ---------------------------------------------------------------- chat
    def _cota_ler(self):
        return self._cfg().get("cota")

    def _cota_gravar(self, v):
        cfg = base.ler_config()
        cfg["cota"] = v
        base.gravar_config(cfg)

    def chat_enviar(self, chave, texto):
        """chave = código do processo (janela de 3 colunas) ou "fluxo:<id>" (janela de conversa do fluxo)."""
        texto = (texto or "").strip()
        if not texto:
            return
        c = self._conversas.get(chave)
        if c is None:
            claude = self._claude or instalar.localizar().get("claude")
            if not claude:
                raise RuntimeError("Falta o Claude Code (Configuração → Programas).")
            if chave.startswith("fluxo:"):
                fluxo, pasta, codigo = self._fluxo(chave[6:]), None, None
            else:
                fluxo, pasta, codigo = self._fluxo("analise"), self._pasta_proc(chave), chave
            try:
                subs = claude_local.subagentes(self._clone(), None)
            except Exception:
                subs = []

            def aoevento(ev, chave=chave, pasta=pasta):
                if pasta and ev.get("t") == "fim" and ev.get("tokens"):
                    reg = self._reg()
                    d = reg.ler(pasta)
                    d["chat"]["tokens"] = d["chat"].get("tokens", 0) + ev["tokens"]
                    reg.gravar(pasta, d)
                if self._janela:
                    try:
                        self._janela.evaluate_js("SSEG.chat(%s, %s)" % (json.dumps(chave), json.dumps(ev, ensure_ascii=False)))
                    except Exception:
                        pass
            c = chat.Conversa(self._clone(), pasta, codigo, fluxo, claude, subs, aoevento,
                              self._reg(), {"ler": self._cota_ler, "gravar": self._cota_gravar})
            self._conversas[chave] = c
        c.enviar(texto)

    def processo_criar(self, codigo):
        """Pasta do processo na pasta dos processos (para abrir a janela de um processo novo)."""
        pasta = self._pasta_proc(codigo.strip().upper())
        os.makedirs(pasta, exist_ok=True)
        return codigo.strip().upper()

    def chat_parar(self, codigo):
        c = self._conversas.pop(codigo, None)
        if c:
            c.parar()

    # ---------------------------------------------------------------- busca
    def buscar(self, consulta):
        clone = self._clone()
        res = busca.buscar(busca.carregar(clone), consulta)
        for r in res:
            r["tem_pdf"] = bool(r.get("pdf")) and os.path.isfile(os.path.join(clone, r["pdf"]))
        return {"grupos": dict(busca.GRUPOS), "resultados": res}

    def ver_pdf(self, pdf, consulta, texto):
        caminho = os.path.join(self._clone(), pdf)
        pg = busca.pagina(caminho, consulta, texto, base.pdftotext())
        base.abrir_pdf(caminho, pg)
        self._log("PDF %s aberto na página %d — conferir o item ali antes de citar." % (os.path.basename(pdf), pg))
        return pg

    # ---------------------------------------------------------------- GitHub
    def git_conferir(self):
        py = instalar.localizar().get("python")
        info = git_sinc.conferir(self._clone(), py)
        info["itens"] = [{"cod": c, "arquivo": a, "fora": info["barrados"].get(a)} for c, a in info["itens"]]
        return info

    def git_sincronizar(self, mensagem, nome="", email=""):
        py = instalar.localizar().get("python")
        linhas = git_sinc.sincronizar(self._clone(), mensagem, py, nome, email)
        self._log("— GitHub —", *linhas)
        return linhas

    def git_atualizar(self):
        clone = self._clone()
        d = self._dados_git or base.verificar(clone)
        out = base.atualizar(clone)
        linhas = ["— Atualizado —", out.splitlines()[-1] if out else "ok"]
        if d["skills"]:
            pasta = base.zipar_skills(clone, d["skills"])
            linhas.append("Skills em .zip na pasta que abriu: suba cada uma em claude.ai > Configurações > "
                          "Capacidades > Skills > Substituir.")
            base.abrir(pasta)
        self._dados_git = None
        self._log(*linhas)
        return linhas

    # ---------------------------------------------------------------- servidor (processos por SSH)
    def _sseg_py(self, *args):
        cfg = self._cfg()
        py = instalar.localizar().get("python")
        script = os.path.join(cfg["clone"], "sseg", "scripts", "sseg.py")
        if not py or not os.path.exists(script):
            raise RuntimeError("Falta o Python ou o SSEG nesta pasta (Configuração).")
        p = subprocess.run([py, script, *args, "--pasta", cfg["processos"]], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900, creationflags=base.SEM_JANELA,
                           stdin=subprocess.DEVNULL, env={**os.environ, "PYTHONUTF8": "1"})
        if p.returncode:
            erro = (p.stderr or p.stdout).strip()
            if "invalid choice" in erro:
                raise RuntimeError("O SSEG desta pasta está desatualizado: atualize pelo GitHub (barra de cima).")
            raise RuntimeError(erro[-1500:])
        return p.stdout

    def servidor_planejar(self):
        return json.loads(self._sseg_py("sincronizar", "--json"))

    def servidor_aplicar(self, escolhas):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
            json.dump(escolhas or {}, fh)
        try:
            saida = self._sseg_py("sincronizar", "--escolhas", fh.name)
        finally:
            os.remove(fh.name)
        linhas = saida.strip().splitlines()
        self._log("— Processos —", *linhas)
        return linhas

    # ---------------------------------------------------------------- SOL sem teclado
    def sol_atalho(self):
        lnk = sol_entrar.instalar_atalho()
        self._log("✓ Atalho criado: " + lnk, *sol_entrar.conferir())
        return sol_entrar.conferir()

    def sol_tampermonkey(self):
        sol_entrar.abrir_tampermonkey()
        return {"script": sol_entrar.script_js(), "passos": sol_entrar.PASSOS}

    def sol_conferir(self):
        return sol_entrar.conferir()

    # ---------------------------------------------------------------- ajuda
    def subagentes(self):
        return claude_local.subagentes(self._clone(), claude_local.ler_fluxos(self._clone()))

    def gasto(self):
        return gasto.texto(gasto.resumo(gasto.ler(self._clone(), dias=30)), 30)

    def relato(self, descricao):
        cfg = self._cfg()
        return relato.montar(base.VERSAO, descricao, "\n".join(self._registro), [cfg["clone"], cfg["processos"]])

    def abrir_issue(self, descricao):
        cfg = self._cfg()
        corpo = self.relato(descricao)
        primeira = descricao.strip().splitlines()[0][:80] if descricao.strip() else "Bug no SSEG.exe " + base.VERSAO
        titulo = relato.limpar(primeira, [cfg["clone"], cfg["processos"]])
        webbrowser.open(relato.url_issue(base.REPO, "[SSEG.exe %s] %s" % (base.VERSAO, titulo), corpo))
        self._log("Abri a página de nova issue no GitHub: confira e clique em \"Submit new issue\".")

    def atualizar_programa(self):
        base.atualizar_programa()
        self._log("Baixado. Fechando para trocar o programa; ele abre de novo sozinho.")
        if self._janela:
            import threading
            threading.Timer(1.2, self._janela.destroy).start()

    def abrir_url(self, url):
        if url.startswith("https://"):
            webbrowser.open(url)

    def copiar(self, texto):
        """Reserva do navigator.clipboard: Set-Clipboard com o texto em base64 (acento intacto)."""
        b64 = base64.b64encode(texto.encode("utf-8")).decode()
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Set-Clipboard -Value ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('%s')))" % b64],
                       creationflags=base.SEM_JANELA, timeout=30)
