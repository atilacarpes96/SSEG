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
import sys
import tempfile
import threading
import time
import webbrowser
import zipfile

import acesso
import busca
import chrome_devtools
import chat
import claude_local
import espelho
import gasto
import git_sinc
import instalacao
import instalar
import processo
import relato
import sol_entrar
import sseg_app as base

CODIGO = re.compile(r"^A\d{8}[A-Z]{2}\d{3}$")


# ---- cards do Início (2.1.13): estado de cada processo na caixa do analista
REGRAS_CARD = {
    "fila": "Na fila: atribuído, ainda sem distribuição",
    "caixa": "Na caixa: distribuído e sem conclusão",
    "vence": "Na caixa, vence em até N dias (ou já venceu)",
    "fora_prazo": "Fora do prazo: passou do prazo na caixa ou concluído depois dele (últimos N dias)",
    "ct": "CT marcada ou pendente: a minuta ainda sem Finalizado (planilha de CT)",
    "ct_chefia": "CT feita, aguardando a chefia finalizar",
    "recurso": "Recurso para redigir: a minuta ainda sem Finalizado (planilha de recursos)",
    "recurso_chefia": "Recurso redigido, aguardando a chefia decidir e finalizar",
    "meta": "Meta da semana: concluídos desde segunda",
}
CORES_CARD = ["laranja", "azul", "verde", "vermelho", "roxo", "amarelo", "cinza"]
CARDS_PADRAO = [
    {"id": "caixa", "nome": "Na caixa", "cor": "laranja", "regra": "caixa", "dias": 7},
    {"id": "vence", "nome": "Vencem em 3 dias", "cor": "vermelho", "regra": "vence", "dias": 3},
    {"id": "fila", "nome": "Na fila", "cor": "cinza", "regra": "fila", "dias": 7},
    {"id": "fora_prazo", "nome": "Fora do prazo", "cor": "vermelho", "regra": "fora_prazo", "dias": 30},
    {"id": "ct", "nome": "CT marcadas", "cor": "roxo", "regra": "ct", "dias": 7},
    {"id": "ct_chefia", "nome": "CT com a chefia", "cor": "cinza", "regra": "ct_chefia", "dias": 7},
    {"id": "recurso", "nome": "Recursos", "cor": "azul", "regra": "recurso", "dias": 7},
    {"id": "recurso_chefia", "nome": "Recursos com a chefia", "cor": "cinza", "regra": "recurso_chefia", "dias": 7},
    {"id": "meta", "nome": "Meta da semana", "cor": "amarelo", "regra": "meta", "dias": 7},
]


def _tem_servidor():
    """Este PC tem o apelido sseg-servidor no ~/.ssh/config (o mesmo teste do sincronizar.py, sem conectar)."""
    try:
        texto = open(os.path.join(os.path.expanduser("~"), ".ssh", "config"), encoding="utf-8", errors="replace").read()
    except OSError:
        return False
    return bool(re.search(r"^\s*Host\s+(.*\s)?sseg-servidor(\s|$)", texto, re.M | re.I))


def _ler(caminho):
    try:
        with open(caminho, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def estado_caixa(dist, reg, prazo=10, hoje=None):
    """Planilha (distribuicao.json) manda; o marcado à mão (analise.json) só preenche o que ela não tem.
    estado: fila (atribuído, sem distribuição) · caixa (distribuído, sem conclusão) · concluido · sem
    (nenhum dado). Prazo = distribuído + `prazo` dias corridos."""
    import datetime
    hoje = hoje or datetime.date.today()
    g = lambda k: (dist.get(k) or reg.get(k) or "")
    fonte = "planilha" if dist.get("codigo") else ("manual" if any(reg.get(k) for k in ("distribuido", "concluido")) else "")
    e = {"distribuido": g("distribuido"), "concluido": g("concluido"), "resultado": g("resultado"), "protocolo": dist.get("protocolo", ""),
         "tipo": dist.get("tipo", ""), "ct": reg.get("ct", ""), "fonte": fonte, "vence": "", "dias": None, "no_prazo": None}
    if e["distribuido"]:
        d0 = datetime.date.fromisoformat(e["distribuido"])
        e["vence"] = (d0 + datetime.timedelta(days=prazo)).isoformat()
        fim = datetime.date.fromisoformat(e["concluido"]) if e["concluido"] else hoje
        e["dias"] = (fim - d0).days
        e["no_prazo"] = e["dias"] <= prazo
    e["estado"] = "concluido" if e["concluido"] else "caixa" if e["distribuido"] else "fila" if dist.get("codigo") else "sem"
    return e


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
        self._antes_da_pagina = None  # lista enquanto a janela do PC não carregou (web_app liga e solta)

    # ---------------------------------------------------------------- infraestrutura
    def _ligar(self, janela):
        self._janela = janela
        self._antes_da_pagina = []

    def _pagina_carregou(self):
        guardado, self._antes_da_pagina = self._antes_da_pagina or [], None
        for js in guardado:
            try:
                self._janela.evaluate_js(js)
            except Exception:  # noqa: BLE001
                pass

    def _emitir(self, funcao, *args):
        """SSEG.<funcao>(args) na janela do PC e em cada tela aberta pelo navegador (espelho)."""
        js = "SSEG.%s(%s)" % (funcao, ", ".join(json.dumps(a, ensure_ascii=False) for a in args))
        if self._janela and self._antes_da_pagina is not None:
            # evaluate_js antes de a página carregar espera por ela até 20 s: era a abertura de 20 s
            # com o espelho ligado (2.2.2). Guarda e manda quando a página carregar.
            self._antes_da_pagina.append(js)
        elif self._janela:
            try:
                self._janela.evaluate_js(js)
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
                "primeira_vez": not base.eh_clone(cfg["clone"]) or not os.path.isdir(cfg["processos"]),
                "instalacao": "--instalacao" in sys.argv or not instalacao.rodando_instalado()}

    # ---------------------------------------------------------------- instalação (2.2.0)
    def instalacao_passos(self):
        """Os passos da tela Instalação, na ordem, cada um com ok e o que falta."""
        cfg, ins, prog, pas = self._cfg(), instalacao.estado(), self.estado_programas(), self.estado_pastas()
        sem_prog = [i["nome"] for i in prog["itens"] if not i["ok"] and "falta entrar" not in i["nome"]]
        srv = self.servidor_acesso(False)
        return [
            {"id": "programa", "titulo": "SSEG instalado neste PC", "ok": ins["aberto_daqui"] and ins["atalho_mesa"],
             "detalhe": "Em %s, com atalho na Área de Trabalho e no Menu Iniciar." % ins["pasta"]
             if ins["frozen"] else "Rodando pelo .py (desenvolvimento).", "acao": "Instalar e reabrir"},
            {"id": "programas", "titulo": "Git, Python, Poppler e Claude Code", "ok": not sem_prog,
             "detalhe": "Falta: " + ", ".join(sem_prog) if sem_prog else "Tudo instalado.", "acao": "Instalar o que falta"},
            {"id": "claude", "titulo": "Entrar no Claude Code", "ok": prog["logado"],
             "detalhe": "Com a sua conta do Claude, pelo navegador, uma vez." if not prog["logado"] else "Logado.",
             "acao": "Entrar"},
            {"id": "pastas", "titulo": "Pasta do SSEG e pasta dos processos", "ok": pas["ok"],
             "detalhe": "%s e %s" % (pas["clone"], pas["processos"]), "acao": "Criar"},
            {"id": "analista", "titulo": "Quem é você", "ok": bool(cfg.get("analista")),
             "detalhe": cfg.get("analista") or "O nome como está na escala.", "acao": "Escolher"},
            {"id": "servidor", "titulo": "Servidor (opcional)", "ok": bool(srv["quem"]), "opcional": True,
             "detalhe": ("Conectado como %s." % srv["quem"]["analista"]) if srv["quem"]
             else "Guarda os seus processos e prepara a caixa. Peça o acesso ao administrador.", "acao": "Pedir acesso"},
        ]

    def instalacao_programa(self):
        """Copia o .exe para a pasta de programas, cria os atalhos e reabre de lá (esta janela fecha)."""
        destino = instalacao.instalar(lambda l: self._log(l))
        if destino and not instalacao.rodando_instalado():
            instalacao.reabrir_instalado(base.ambiente_limpo())
            self._log("Abrindo o SSEG instalado; esta janela fecha. O arquivo baixado pode ir para a lixeira.")
            if self._janela:
                threading.Timer(1.5, self._janela.destroy).start()
            return {"reabrindo": True}
        return {"reabrindo": False}

    # ---------------------------------------------------------------- barra de estado
    def estado_programas(self):
        achados = instalar.localizar()
        self._claude = achados.get("claude")
        logado = bool(self._claude) and instalar.claude_logado(self._claude)
        itens, quebrado = [], []
        for chave, nome, _id in instalar.PROGRAMAS:
            ok = bool(achados.get(chave))
            erro = instalar.roda(chave, achados[chave]) if ok else None  # existe, mas roda? (2.3.6)
            if erro:
                quebrado.append(nome + ": " + erro)
            extra = (" — " + erro) if erro else "" if chave != "claude" or not ok else (" (logado)" if logado else " (falta entrar)")
            itens.append({"nome": nome + extra, "ok": ok and not erro and (chave != "claude" or logado)})
        falta = instalar.faltando(achados)
        return {"ok": not falta and not quebrado and logado, "falta": bool(falta), "logado": logado,
                "quebrado": quebrado, "itens": itens}

    def estado_pastas(self):
        cfg = self._cfg()
        clone_ok, proc_ok = base.eh_clone(cfg["clone"]), os.path.isdir(cfg["processos"])
        # operante (2.3.6): o clone tem os scripts e a pasta dos processos aceita gravar
        problemas = []
        if clone_ok and not os.path.isfile(os.path.join(cfg["clone"], "sseg", "scripts", "sseg.py")):
            problemas.append("o clone não tem sseg/scripts/sseg.py")
        if proc_ok:
            teste = os.path.join(cfg["processos"], ".sseg-teste-gravacao")
            try:
                with open(teste, "w") as fh:
                    fh.write("ok")
                os.remove(teste)
            except OSError as e:
                problemas.append("não consigo gravar na pasta dos processos (%s)" % e.strerror)
        if not clone_ok:
            problemas.append("a pasta do SSEG não é um clone do Git")
        if not proc_ok:
            problemas.append("a pasta dos processos não existe")
        return {"ok": not problemas, "clone": cfg["clone"], "processos": cfg["processos"],
                "clone_ok": clone_ok, "processos_ok": proc_ok, "problemas": problemas}

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
            out.append(dict(estado_caixa(_ler(os.path.join(p, "distribuicao.json")), _ler(reg), self._cfg().get("prazo_caixa", 10)),
                            codigo=n, quando=quando, arquivos=len(arqs), analise=os.path.exists(reg),
                            cts=_ler(os.path.join(p, "ct.json")).get("itens") or [],
                            recursos=_ler(os.path.join(p, "recurso.json")).get("itens") or [],
                            cia=any(re.match(r"CIA \d+", os.path.basename(a)) for a in arqs)))
        out.sort(key=lambda x: -x["quando"])
        return out  # todos: os cards contam tudo; a tabela mostra os 30 primeiros sem filtro

    def processo_situacao(self, codigo, campos):
        """Janela do processo: distribuído, concluído, resultado e CT à mão (quando a planilha não tem)."""
        livres = {k: v for k, v in (campos or {}).items() if k in ("distribuido", "concluido", "resultado", "ct")}
        pasta = self._pasta_proc(codigo)
        try:
            d = self._reg().situacao(pasta, **livres)
        except ValueError as e:
            raise RuntimeError(str(e))
        return estado_caixa(_ler(os.path.join(pasta, "distribuicao.json")), d, self._cfg().get("prazo_caixa", 10))

    def cards(self, lista=None):
        """Cards do Início (2.1.13): sem argumento lê; com a lista, grava. [] volta ao padrão."""
        cfg = self._cfg()
        if lista is not None:
            if not isinstance(lista, list) or len(lista) > 24:
                raise RuntimeError("Lista de cards inválida.")
            limpa = []
            for c in lista:
                if not isinstance(c, dict) or c.get("regra") not in REGRAS_CARD:
                    raise RuntimeError("Card com regra desconhecida.")
                limpa.append({"id": str(c.get("id") or secrets.token_hex(3))[:16], "nome": str(c.get("nome") or "")[:40],
                              "cor": c.get("cor") if c.get("cor") in CORES_CARD else "cinza", "regra": c["regra"],
                              "dias": max(1, min(365, int(c.get("dias") or 7)))})
            if limpa:
                cfg["cards"] = limpa
            else:
                cfg.pop("cards", None)
            base.gravar_config(cfg)
        # card salvo com regra que saiu (aguardando, cia, ca e no_prazo, tiradas na 2.2.2) some sozinho
        salvos = [c for c in cfg.get("cards") or [] if c.get("regra") in REGRAS_CARD]
        return {"cards": salvos or CARDS_PADRAO, "padrao": CARDS_PADRAO, "regras": REGRAS_CARD,
                "cores": CORES_CARD, "prazo": cfg.get("prazo_caixa", 10), **self._meta(cfg)}

    # ---------------------------------------------------------------- analista e escala (2.1.15)
    def _escala(self, forcar=False):
        """escala.json do servidor (horas de cada analista por dia, da planilha Escala Análise), guardado ao
        lado da config. Velho de 6 h, busca de novo por trás e devolve o que tem; só espera a busca se ainda
        não há arquivo ou se `forcar`. Sem servidor neste PC, fica com o que tiver (ou nada)."""
        arq = os.path.join(os.path.dirname(base.arquivo_config()), "escala.json")
        try:
            velho = time.time() - os.path.getmtime(arq) > 6 * 3600
        except OSError:
            velho = None
        tentou = getattr(self, "_escala_tentou", 0)
        if (forcar or (velho is not False and time.time() - tentou > 600)) and _tem_servidor():
            self._escala_tentou = time.time()
            if forcar or velho is None:
                self._buscar_escala(arq)
            else:
                threading.Thread(target=self._buscar_escala, args=(arq,), daemon=True).start()
        return _ler(arq)

    def _buscar_escala(self, arq):
        try:
            d = acesso.chamar_json("escala")  # a porta devolve só a linha do analista (o admin recebe tudo)
            if isinstance(d, dict) and isinstance(d.get("horas"), dict):
                with open(arq + ".tmp", "w", encoding="utf-8") as fh:
                    json.dump(d, fh, ensure_ascii=False)
                os.replace(arq + ".tmp", arq)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
            pass

    def _meta(self, cfg):
        """Meta da semana: pela escala (horas de seg. a dom. ÷ 6, meio arredonda para cima, × PPCI por período)
        quando há analista escolhido e a linha dele na escala; senão, o número digitado."""
        import datetime
        ppp = cfg.get("ppci_por_periodo", 2)
        info = {"fonte": "manual", "por_periodo": ppp, "auto": cfg.get("meta_auto", True), "analista": cfg.get("analista", ""),
                "manual": cfg.get("meta_semana", 10)}
        if info["auto"] and info["analista"]:
            esc = self._escala()
            horas = (esc.get("horas") or {}).get(info["analista"])
            if horas is not None:
                hoje = datetime.date.today()
                seg = hoje - datetime.timedelta(days=hoje.weekday())
                h = sum(float(horas.get((seg + datetime.timedelta(days=i)).isoformat(), 0)) for i in range(7))
                per = int(h / 6 + 0.5)
                info.update(fonte="escala", horas=h, periodos=per, gerado=esc.get("gerado", ""))
                return {"meta": per * ppp, "meta_info": info}
            info["sem_escala"] = True
        return {"meta": cfg.get("meta_semana", 10), "meta_info": info}

    def analista(self, nome=None):
        """Quem usa este PC (o nome como está na escala). Sem argumento, só lê; devolve também os nomes da escala."""
        cfg = self._cfg()
        if nome is not None:
            nome = re.sub(r"\s+", " ", str(nome)).strip()[:60]
            if not nome:
                raise RuntimeError("Escolha ou escreva o seu nome.")
            cfg["analista"] = nome
            base.gravar_config(cfg)
        esc = self._escala(forcar=nome is None and not cfg.get("analista"))
        return {"analista": cfg.get("analista", ""), "nomes": sorted(esc.get("horas") or {}), "gerado": esc.get("gerado", "")}

    # ---------------------------------------------------------------- tela Quadro (2.1.14)
    def _quadro(self):
        """quadro.py mora em sseg/scripts; no .exe vem empacotado (--hidden-import quadro)."""
        try:
            import quadro
        except ImportError:
            import sys
            sys.path.insert(0, os.path.join(self._clone(), "sseg", "scripts"))
            import quadro
        return quadro, self._cfg()["processos"]

    def quadro(self):
        """Tarefas soltas (quadro.json). Os processos a tela tira da lista de processos()."""
        q, raiz = self._quadro()
        r = {"cartoes": q.ler(raiz)["cartoes"], "colunas": q.COLUNAS, "nomes": q.NOMES, "secao": None, "erro_secao": ""}
        if self._cfg().get("servidor_quem") and acesso.tem_apelido():  # Quadro da seção (2.3.0), pelo servidor
            try:
                s = acesso.chamar_json("quadro", timeout=20)
                r.update(secao=s.get("cartoes") or [], eu=s.get("eu", ""), admin=s.get("admin", False))
            except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as e:
                r["erro_secao"] = str(e)[:200]
        return r

    def quadro_secao(self, acao, *args):
        """adicionar(titulo, coluna) · pegar(id) · soltar(id) · alterar(id, campos) · remover(id) · restaurar(cartao, pos)."""
        pedido = json.dumps({"acao": acao, "args": list(args)}, ensure_ascii=False).encode("utf-8")
        return acesso.chamar_json("quadro-mexer", entrada=pedido, timeout=20)

    def quadro_mexer(self, acao, *args):
        """adicionar(titulo, coluna) · alterar(id, campos) · remover(id) · restaurar(cartao, pos)."""
        q, raiz = self._quadro()
        try:
            if acao == "adicionar":
                return q.adicionar(raiz, args[0], "", args[1] if len(args) > 1 else "afazer")
            if acao == "alterar":
                livres = {k: v for k, v in (args[1] or {}).items() if k in ("coluna", "titulo", "checklist")}
                return q.alterar(raiz, args[0], **livres)
            if acao == "remover":
                return q.remover(raiz, args[0])
            if acao == "restaurar":
                return q.restaurar(raiz, args[0], args[1] if len(args) > 1 else None)
        except ValueError as e:
            raise RuntimeError(str(e))
        raise RuntimeError("ação inválida: %s" % acao)

    def meta_semana(self, valor=None, auto=None, por_periodo=None):
        """Meta de processos fechados por semana (card do Início): o número à mão, se vem da escala e
        quantos PPCI por período de 6 h. Sem argumento, só lê."""
        cfg = self._cfg()
        if valor is not None:
            n = int(valor)
            if not 1 <= n <= 200:
                raise RuntimeError("Meta entre 1 e 200.")
            cfg["meta_semana"] = n
        if auto is not None:
            cfg["meta_auto"] = bool(auto)
        if por_periodo is not None:
            n = int(por_periodo)
            if not 1 <= n <= 20:
                raise RuntimeError("PPCI por período entre 1 e 20.")
            cfg["ppci_por_periodo"] = n
        if (valor, auto, por_periodo) != (None, None, None):
            base.gravar_config(cfg)
        return self._meta(cfg)

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
        d["caixa"] = estado_caixa(_ler(os.path.join(pasta, "distribuicao.json")), d["analise"], self._cfg().get("prazo_caixa", 10))
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

    # ---------------------------------------------------------------- vários analistas no servidor (2.2.0)
    def servidor_acesso(self, testar=False):
        """Como este PC está com o servidor: chave, apelido e, com testar, quem o servidor diz que somos."""
        cfg = self._cfg()
        r = {"analista": cfg.get("analista", ""), "chave": bool(acesso.chave_publica()), "apelido": acesso.tem_apelido(),
             "quem": cfg.get("servidor_quem") or None, "erro": ""}
        if testar and r["apelido"]:
            try:
                r["quem"] = acesso.chamar_json("quem-sou")
                cfg["servidor_quem"] = r["quem"]
            except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as e:
                r["quem"], r["erro"] = None, str(e)
                cfg.pop("servidor_quem", None)
            base.gravar_config(cfg)
        return r

    def servidor_pedir_acesso(self):
        """Cria chave e apelido se faltarem e devolve o código de acesso para mandar ao administrador."""
        cfg = self._cfg()
        if not cfg.get("analista"):
            raise RuntimeError("Escolha antes quem você é (Configuração → Analista): o código leva o seu nome.")
        for f in acesso.preparar():
            self._log("Servidor: " + f)
        return {"codigo": acesso.mensagem_acesso(cfg["analista"])}

    def servidor_analistas(self):
        return acesso.chamar_json("analistas")

    def servidor_ler_codigo(self, texto):
        return acesso.ler_codigo(texto)

    def servidor_autorizar(self, texto, nome=None):
        pedido = acesso.ler_codigo(texto)
        if nome:
            pedido["analista"] = re.sub(r"\s+", " ", nome).strip()
        r = acesso.chamar_json("autorizar", entrada=json.dumps(pedido, ensure_ascii=False).encode("utf-8"))
        self._log("Servidor: acesso liberado para %s." % r.get("analista"))
        return self.servidor_analistas()

    def servidor_revogar(self, nome):
        acesso.chamar_json("revogar", nome)
        self._log("Servidor: acesso de %s retirado." % nome)
        return self.servidor_analistas()

    def servidor_planejar(self):
        return json.loads(self._sseg_py("sincronizar", "--json"))

    def servidor_conferir(self):
        """Para o chip (2.3.4): o plano, só lendo, resumido em números. Script puro, sem Claude.
        novos = processos que descem e ainda não têm pasta neste PC (chegaram na caixa)."""
        p = self.servidor_planejar()
        cods = lambda lst: {k.split("/", 1)[0] if "/" in k else k[:-3] for k in lst}
        desce = cods(p["desce"])
        pasta = self._cfg().get("processos") or ""
        novos = sorted(c for c in desce if not os.path.isdir(os.path.join(pasta, c)))
        return {"sobe": len(p["sobe"]), "desce": len(p["desce"]), "conflito": len(p["conflito"]),
                "processos_descem": len(desce), "novos": novos}

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

    # ---------------------------------------------------------------- Chrome para o Claude (DevTools MCP)
    def _claude_exe(self):
        return self._claude or instalar.localizar().get("claude")

    def chrome_conferir(self):
        return chrome_devtools.conferir()

    def chrome_registrar(self):
        chrome_devtools.registrar(self._claude_exe())
        self._log("✓ Chrome DevTools registrado no Claude Code (vale para as próximas conversas).")
        return chrome_devtools.conferir()

    def chrome_remover(self):
        self._log(chrome_devtools.remover(self._claude_exe()))
        return chrome_devtools.conferir()

    def chrome_inspect(self):
        chrome_devtools.abrir_inspect()
        self._log("Abri chrome://inspect no Chrome: ligue a depuração remota e depois clique em Conferir.")

    def chrome_testar(self):
        self._log("Testando o Chrome DevTools (se o Chrome pedir, clique em Permitir)…")
        ok, msg = chrome_devtools.testar()
        self._log(("✓ " if ok else "✗ ") + msg)
        return {"ok": ok, "msg": msg, "passos": chrome_devtools.conferir()}

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
                with open(tmp, "rb") as fh:
                    acesso.chamar("relato", ident, entrada=fh.read(), timeout=120)
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
