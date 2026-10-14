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
import secrets
import shutil
import subprocess
import tempfile
import time
import webbrowser
import zipfile

import busca
import chat
import claude_local
import espelho
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
        self._eventos = []   # últimos eventos do chat (stream-json resumido), para o Reportar bug
        self._hist = {}      # eventos de cada conversa, para a outra tela (celular) montar o chat ao abrir
        self._espelho = None
        self._tunel = None   # SSH de saída até o servidor: o caminho do celular (fase 2)
        self._pasta_web = None

    # ---------------------------------------------------------------- infraestrutura
    def _ligar(self, janela):
        self._janela = janela

    def _emitir(self, funcao, *args):
        """SSEG.<funcao>(args) na janela do PC e em cada tela aberta pelo navegador (espelho)."""
        if self._janela:
            try:
                self._janela.evaluate_js("SSEG.%s(%s)" % (funcao, ", ".join(json.dumps(a, ensure_ascii=False) for a in args)))
            except Exception:  # janela fechando
                pass
        if self._espelho:
            self._espelho.emitir(funcao, args)

    def _log(self, *linhas):
        self._registro.extend(linhas)
        self._emitir("log", list(linhas))

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
            reg = os.path.join(p, "analise.json")
            sit = {}
            if os.path.exists(reg):
                try:
                    with open(reg, encoding="utf-8") as fh:
                        a = json.load(fh)
                    sit = {k: a[k] for k in ("situacao", "prazo", "ct", "fechado_em") if a.get(k)}
                except (OSError, ValueError):
                    pass
            out.append({"codigo": n, "quando": quando, "arquivos": len(arqs),
                        "cia": any(re.match(r"CIA \d+", os.path.basename(a)) for a in arqs),
                        "analise": os.path.exists(reg),
                        # sem situação marcada: em análise se mexido nos últimos 30 dias; senão "parado" (fora dos cards)
                        "situacao": sit.get("situacao") or ("analise" if time.time() - quando < 30 * 86400 else "parado"),
                        "prazo": sit.get("prazo", ""), "ct": sit.get("ct", ""), "fechado_em": sit.get("fechado_em", 0)})
        out.sort(key=lambda x: -x["quando"])
        return out  # todos: os cards contam tudo; a tabela mostra os 30 primeiros sem filtro

    def processo_situacao(self, codigo, campos):
        """Seletor da janela do processo: situacao, prazo, ct (2.1.12)."""
        livres = {k: v for k, v in (campos or {}).items() if k in ("situacao", "prazo", "ct")}
        try:
            d = self._reg().situacao(self._pasta_proc(codigo), **livres)
        except ValueError as e:
            raise RuntimeError(str(e))
        return {k: d.get(k, "") for k in ("situacao", "prazo", "ct", "fechado_em")}

    def meta_semana(self, valor=None):
        """Meta de processos fechados por semana (card do Início). Sem valor, só lê."""
        cfg = self._cfg()
        if valor is not None:
            n = int(valor)
            if not 1 <= n <= 200:
                raise RuntimeError("Meta entre 1 e 200.")
            cfg["meta_semana"] = n
            base.gravar_config(cfg)
        return cfg.get("meta_semana", 10)

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

    def processo_exigencia(self, codigo, texto, medida="", fundamento="", origem="analista"):
        """Do analista entra como texto final; "Pôr na CIA" num bloco do Claude entra como rascunho."""
        origem = "claude" if origem == "claude" else "analista"
        return self._reg().exigencia(self._pasta_proc(codigo), texto, medida, fundamento, origem=origem)

    def processo_perguntas(self, codigo, perguntas):
        """Perguntas de um bloco sseg-perguntas viram pendências (a mesma pergunta não duplica)."""
        reg, pasta = self._reg(), self._pasta_proc(codigo)
        existentes = {re.sub(r"\s+", " ", p["texto"]).strip().lower() for p in reg.ler(pasta)["pendencias"]}
        for q in perguntas or []:
            t = (q.get("texto") or "").strip()
            if t and re.sub(r"\s+", " ", t).lower() not in existentes:
                reg.pendencia(pasta, t, origem="claude")
                existentes.add(re.sub(r"\s+", " ", t).lower())

    def processo_responder(self, codigo, pares):
        """[[texto da pergunta, resposta]]: grava a resposta na pendência e marca como enviada ao Claude."""
        reg, pasta = self._reg(), self._pasta_proc(codigo)
        d = reg.ler(pasta)
        for texto, resp in pares or []:
            alvo = re.sub(r"\s+", " ", texto).strip().lower()
            for p in d["pendencias"]:
                if re.sub(r"\s+", " ", p["texto"]).strip().lower() == alvo:
                    p.update(resposta=resp, enviada=True)
        reg.gravar(pasta, d)

    def norma_pdf(self, rotulo, consulta=""):
        """Bloco sseg-norma: o programa acha o PDF oficial e a página (mecanismo da busca 1.2.2)."""
        nome = busca.pdf_citado(rotulo)
        if not nome:
            raise RuntimeError("Não achei o PDF de \"%s\" em normas/pdf." % rotulo)
        caminho = os.path.join(self._clone(), "sseg", "normas", "pdf", nome)
        pg = busca.pagina(caminho, consulta, rotulo, base.pdftotext())
        base.abrir_pdf(caminho, pg)
        self._log("PDF %s aberto na página %d (pedido: \"%s\") — conferir o item ali antes de citar." % (nome, pg, rotulo[:80]))
        return pg

    def processo_atualizar(self, codigo, colecao, id_, campos):
        """O programa muda resposta/feita da pendência e final/fundamento da exigência. Rascunho não."""
        livres = {"pendencias": {"resposta", "feita", "enviada"}, "exigencias": {"final", "fundamento", "medida", "achado", "pedido"}}[colecao]
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

    def abrir_sol(self, url):
        """No Chrome do analista (é lá que está o login do SOL); sem Chrome, o navegador padrão."""
        if not url.startswith(processo.SOL):
            raise RuntimeError("Endereço fora do SOL.")
        c = sol_entrar.chrome()
        if c:
            subprocess.Popen([c, url], creationflags=base.SEM_JANELA)
        else:
            webbrowser.open(url)

    def abrir_pasta_processo(self, codigo):
        base.abrir(self._pasta_proc(codigo))

    # ---------------------------------------------------------------- chat
    def _cota_ler(self):
        return self._cfg().get("cota")

    def _cota_gravar(self, v):
        cfg = base.ler_config()
        cfg["cota"] = v
        base.gravar_config(cfg)

    def _guardar(self, chave, ev):
        h = self._hist.setdefault(chave, [])
        h.append(ev)
        del h[:-600]

    def chat_historico(self, chave):
        """Eventos desta conversa desde que o programa abriu (a outra tela monta o chat a partir deles)."""
        return list(self._hist.get(chave, []))

    def chat_enviar(self, chave, texto, de=""):
        """chave = código do processo (janela de 3 colunas) ou "fluxo:<id>" (janela de conversa do fluxo).
        de = qual tela mandou: ela já mostrou a mensagem; as outras recebem o evento "eu"."""
        texto = (texto or "").strip()
        if not texto:
            return
        c = self._conversas.get(chave)
        if c is None:
            claude = self._claude or instalar.localizar().get("claude")
            if not claude:
                raise RuntimeError("Falta o Claude Code (Configuração → Programas).")
            links = None
            if chave.startswith("fluxo:"):
                fluxo, pasta, codigo = self._fluxo(chave[6:]), None, None
            else:
                fluxo, pasta, codigo = self._fluxo("analise"), self._pasta_proc(chave), chave
                _, sol = processo.json_do_sol(pasta)
                links = processo.links_sol(sol)
            try:
                subs = claude_local.subagentes(self._clone(), None)
            except Exception:
                subs = []

            def aoevento(ev, chave=chave, pasta=pasta):
                self._eventos.append("%s %s %s" % (time.strftime("%H:%M:%S"), chave, json.dumps(ev, ensure_ascii=False)[:500]))
                del self._eventos[:-400]
                if pasta and ev.get("t") == "fim" and ev.get("tokens"):
                    reg = self._reg()
                    d = reg.ler(pasta)
                    d["chat"]["tokens"] = d["chat"].get("tokens", 0) + ev["tokens"]
                    reg.gravar(pasta, d)
                self._guardar(chave, ev)
                self._emitir("chat", chave, ev)
            c = chat.Conversa(self._clone(), pasta, codigo, fluxo, claude, subs, aoevento,
                              self._reg(), {"ler": self._cota_ler, "gravar": self._cota_gravar}, sol=links)
            self._conversas[chave] = c
        ev = {"t": "eu", "texto": texto, "de": de}
        self._guardar(chave, ev)
        self._emitir("chat", chave, ev)
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

    # ---- Reportar bug com imagem e log. Texto limpo vai à issue (repo público); imagens e log
    # (podem ter dado de processo) vão ao servidor por SSH, fora do git, ou ficam numa pasta do PC.
    def print_janela(self):
        from PIL import ImageGrab
        import io
        j = self._janela
        img = ImageGrab.grab(bbox=(j.x, j.y, j.x + j.width, j.y + j.height), all_screens=True)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    def _log_relato(self):
        cfg = self._cfg()
        partes = ["SSEG.exe %s" % base.VERSAO, "", "== Detalhes ==", *self._registro[-300:], "",
                  "== Conversas (eventos) ==", *self._eventos[-300:], "", "== Erros da tela ==", *self._erros_js[-50:]]
        return relato.limpar("\n".join(partes), [cfg["clone"], cfg["processos"]])

    def relato_enviar(self, descricao, imagens):
        """Monta o .zip (relato.md limpo, log.txt limpo, imagens). Com SSH: ao servidor em ~/sseg-relatos/.
        Sem SSH: numa pasta do PC, que se abre. Devolve {id, onde}."""
        cfg = self._cfg()
        ident = time.strftime("%Y%m%d-%H%M%S")
        tmp = os.path.join(tempfile.gettempdir(), "sseg-relato-%s.zip" % ident)
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("relato.md", self.relato(descricao))
            z.writestr("log.txt", self._log_relato())
            for i, url in enumerate(imagens or [], 1):
                m = re.match(r"data:image/(\w+);base64,(.*)", url or "", re.S)
                if m:
                    z.writestr("imagens/imagem%d.%s" % (i, m.group(1).replace("jpeg", "jpg")), base64.b64decode(m.group(2)))
        if self.estado_servidor()["configurado"]:
            try:
                for cmd in (["ssh", "-o", "BatchMode=yes", "sseg-servidor", "mkdir -p sseg-relatos"],
                            ["scp", "-o", "BatchMode=yes", tmp, "sseg-servidor:sseg-relatos/%s.zip" % ident]):
                    p = subprocess.run(cmd, capture_output=True, text=True, timeout=120, creationflags=base.SEM_JANELA)
                    if p.returncode:
                        raise RuntimeError(p.stderr.strip()[-300:])
                os.remove(tmp)
                self._log("Relato %s com anexos enviado ao servidor (sseg-relatos/)." % ident)
                return {"id": ident, "onde": "servidor"}
            except (OSError, RuntimeError, subprocess.SubprocessError) as e:
                self._log("✗ Não consegui mandar ao servidor (%s); salvei no PC." % e)
        pasta = os.path.join(os.path.expanduser("~"), "Documents", "SSEG-relatos")
        os.makedirs(pasta, exist_ok=True)
        destino = os.path.join(pasta, "relato-%s.zip" % ident)
        shutil.move(tmp, destino)
        base.abrir(pasta)
        self._log("Relato %s salvo em %s: mande o .zip por outro meio (tem imagens; não vai ao GitHub)." % (ident, destino))
        return {"id": ident, "onde": "pc"}

    def abrir_issue(self, descricao, anexo=None):
        cfg = self._cfg()
        corpo = self.relato(descricao)
        if anexo:
            corpo += "\n**Anexos (imagens e log):** relato %s, %s — não vão ao GitHub.\n" % (
                anexo["id"], "no servidor" if anexo["onde"] == "servidor" else "salvos no PC do analista")
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

    # ---------------------------------------------------------------- espelho no celular (2.4)
    def _espelho_obj(self):
        if not self._espelho:
            cfg = base.ler_config()
            if not cfg.get("espelho_chave"):
                cfg["espelho_chave"] = secrets.token_urlsafe(18)
                base.gravar_config(cfg)
            self._espelho = espelho.Espelho(self, self._pasta_web, cfg["espelho_chave"],
                                            porta=int(cfg.get("espelho_porta") or espelho.PORTA))
        return self._espelho

    def _endereco_celular(self):
        """https://<servidor>.<rede>.ts.net, perguntado uma vez ao Tailscale do servidor e guardado."""
        cfg = base.ler_config()
        if cfg.get("espelho_celular"):
            return cfg["espelho_celular"]
        try:
            p = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "sseg-servidor",
                                "tailscale status --json"], capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=30, creationflags=base.SEM_JANELA, stdin=subprocess.DEVNULL)
            nome = (json.loads(p.stdout).get("Self") or {}).get("DNSName", "").rstrip(".")
        except (OSError, ValueError, subprocess.SubprocessError):
            nome = ""
        if not nome:
            return ""
        cfg["espelho_celular"] = "https://" + nome
        base.gravar_config(cfg)
        return cfg["espelho_celular"]

    def espelho_estado(self):
        e, t = self._espelho, self._tunel
        ligado = bool(e and e.ligado)
        cel = base.ler_config().get("espelho_celular", "") if ligado else ""
        return {"ligado": ligado, "url": e.url() if ligado else "", "telas": e.telas if e else 0,
                "tunel": t.estado if t else "desligado", "tunel_erro": t.erro if t else "",
                "celular": cel + "/?chave=" + e.chave if cel else ""}

    def espelho_ligar(self, ligar):
        """Liga ou desliga a página no navegador (127.0.0.1) e, com o servidor configurado, o túnel até ele
        (o caminho do celular). Guarda a escolha para a próxima abertura."""
        e = self._espelho_obj()
        if ligar:
            e.ligar()
            if self.estado_servidor()["configurado"]:
                if not self._tunel:
                    self._tunel = espelho.Tunel(e.porta, aolog=self._log, sem_janela=base.SEM_JANELA)
                self._tunel.ligar()
                self._endereco_celular()
        else:
            if self._tunel:
                self._tunel.desligar()
            e.desligar()
        cfg = base.ler_config()
        cfg["espelho"] = bool(ligar)
        base.gravar_config(cfg)
        self._log("Espelho %s." % ("ligado: " + e.url().split("?")[0] if ligar else "desligado"))
        return self.espelho_estado()

    def abrir_url(self, url):
        if url.startswith("https://") or url.startswith("http://127.0.0.1:"):
            webbrowser.open(url)

    def copiar(self, texto):
        """Reserva do navigator.clipboard: Set-Clipboard com o texto em base64 (acento intacto)."""
        b64 = base64.b64encode(texto.encode("utf-8")).decode()
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Set-Clipboard -Value ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('%s')))" % b64],
                       creationflags=base.SEM_JANELA, timeout=30)
