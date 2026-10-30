#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
porta.py — a porta do servidor para os PCs dos analistas (SSEG multiusuário, 2.2.0).

Todo SSEG.exe fala com o servidor por um comando só:
    ssh sseg-servidor python3 SSEG/sseg/scripts/porta.py <ação> [args]

QUEM É QUEM
  - Admin (o Átila): chave sem restrição no ~/.ssh/authorized_keys. A porta roda como ele pediu.
  - Analista: chave com `command="python3 .../porta.py --analista '<nome>'",restrict`. O SSH
    ignora o comando que o PC pediu, roda a porta com o nome do analista e entrega o pedido em
    SSH_ORIGINAL_COMMAND. O analista não tem shell: só as ações abaixo, e só nos processos dele.
O cadastro fica em ~/sseg-acesso/analistas.json (fora do Git: tem nome de militar e chave).

DE QUEM É O PROCESSO (o "responsável")
  1. <código>/distribuicao.json, campo "analista" (a planilha Distribuição Análise manda);
  2. senão, processos/.responsaveis.json (quem mandou primeiro, ou o admin com `atribuir`);
  3. senão, o admin (as pastas antigas, de antes do multiusuário, são do Átila).
Cada analista lista, recebe e entrega só os processos dele. O distribuicao.json nunca sobe do PC:
quem grava é o servidor.

AÇÕES
  quem-sou                                → {"analista", "papel"}
  listar | receber | entregar             → as mesmas do sincronizar.py, filtradas pelo responsável
  meus                                    → os códigos dele, um por linha (Painel do Dia)
  quadro                                  → o Quadro da seção (~/sseg-quadro/quadro.json); ao admin, também o
                                            quadro "Programa" (~/sseg-quadro/programa/: relatos, avisos dos scripts)
  quadro-mexer                            → stdin {"acao", "args"}: adicionar, pegar, soltar, alterar,
                                            remover, restaurar. Todos criam, pegam e comentam; mover,
                                            editar e excluir só quem criou, quem pegou ou o admin.
                                            Com "onde": "programa", o quadro do Programa (só o admin)
  escala                                  → a linha do analista no escala.json (o admin recebe tudo)
  relato <id>                             → guarda o .zip do stdin em ~/sseg-relatos/<analista>-<id>.zip e (2.6.3)
                                            põe um cartão no Quadro da seção, para o administrador ver na hora
  relatos                                 → os relatos dele (o admin vê todos), com o andamento: recebido,
                                            trabalhando ou pronto, e a resposta para o analista
  sol                                     → (2.3.17) a sessão do SOL no Chromium do servidor, só lendo:
                                            {"chrome", "logado", "exp", "senha", "trava", "ultimo_login",
                                            "caixa_lida_em", "caixa_total"}. Nunca devolve token nem senha
  banco <consulta>                        → (28/10/2026) stdin {parâmetros}: resumo, opcoes, mapa, pesquisa,
                                            processo ou cias no solcbm.db (sol_consulta.py), para a aba Processos
  sol-caixa                     (admin)   → roda a leitura da caixa agora (sol_caixa.py, com o login
                                            automático se a sessão caiu) → {"rc", "saida"}
  analistas                     (admin)   → lista dos cadastrados
  autorizar                     (admin)   → stdin {"analista", "chave"}: cadastra e libera a chave; com o
                                            nome do próprio admin, a chave entra como OUTRO PC dele (admin-chave)
  admin-chave                   (admin)   → stdin {"chave", "rotulo"}: mais um PC do administrador (sem restrição)
  sol-congelar <código>         (admin)   → memorial e JSON do licenciamento como estão agora (sol_snapshot.py; só lê o SOL)
  sol-salvar <código> [--ca]    (admin)   → depois da emissão: baixa a CIA e grava CIA <N>.pdf; --ca só confere o CA (sol_snapshot.py)
  sol-senha-gravar              (admin)   → stdin {"matricula", "senha"}: grava o login do SOL do servidor
  sol-senha-apagar              (admin)   → remove a senha do SOL do servidor
  revogar <nome>                (admin)   → tira a chave e o cadastro
  atribuir <código> <nome>      (admin)   → muda o responsável de um processo fora da planilha
"""

import datetime
import json
import os
import re
import shlex
import sys
import tempfile
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import sincronizar as sc  # noqa: E402 — manifesto, pacote e lista do que pode ir são os mesmos
import quadro as qd  # noqa: E402 — o Quadro da seção tem o formato do quadro do PC

ACESSO = os.path.expanduser("~/sseg-acesso/analistas.json")
CHAVES = os.path.expanduser("~/.ssh/authorized_keys")
ESCALA = os.path.expanduser("~/sseg-escala/escala.json")
RELATOS = os.path.expanduser("~/sseg-relatos")
QUADRO = os.path.expanduser("~/sseg-quadro")
ADMIN_PADRAO = "Sd Carpes"
SO_SERVIDOR = ("distribuicao.json", "ct.json", "recurso.json")  # o PC recebe, mas nunca sobe
MARCA = "sseg-analista:"              # comentário da linha no authorized_keys
CHAVE_OK = re.compile(r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp\d+) [A-Za-z0-9+/=]{40,}$")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()


def nome_ok(s):
    return bool(re.fullmatch(r"[\w .-]{2,40}", s or "", re.U))


# ----------------------------------------------------------------------------- cadastro

def ler_acesso(caminho=None):
    try:
        with open(caminho or ACESSO, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        d = {}
    d.setdefault("admin", ADMIN_PADRAO)
    d.setdefault("analistas", {})
    return d


def _gravar_json(caminho, d):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".porta-", suffix=".json", dir=os.path.dirname(caminho))
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, caminho)


def linha_chave(analista, chave, script):
    """Linha do authorized_keys: só a porta, com o nome do analista, sem shell nem túnel."""
    cmd = "python3 %s --analista %s" % (script, shlex.quote(analista))
    return 'command="%s",restrict %s %s%s' % (cmd.replace('"', '\\"'), chave, MARCA, norm(analista).replace(" ", "_"))


def _reescrever_chaves(acesso, caminho, script):
    """Mantém as linhas que não são de analista (a do admin) e regrava as dos cadastrados."""
    try:
        velhas = open(caminho, encoding="utf-8").read().splitlines()
    except OSError:
        velhas = []
    fica = [l for l in velhas if MARCA not in l]
    novas = [linha_chave(nome, a["chave"], script) for nome, a in sorted(acesso["analistas"].items())]
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    tmp = caminho + ".porta-tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(fica + novas) + "\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, caminho)


# -------------------------------------------------------------------------- responsável

def responsavel(raiz, cod, acesso, resp=None):
    try:
        with open(os.path.join(raiz, cod, "distribuicao.json"), encoding="utf-8") as fh:
            a = json.load(fh).get("analista")
        if a:
            return a
    except (OSError, ValueError, AttributeError):
        pass
    if resp is None:
        resp = _ler_resp(raiz)
    if resp.get(cod):
        return resp[cod]
    # pasta criada só por CT/recurso de outro analista (ct_recursos.py, 2.3.0): sem dono, não é do admin;
    # quem vê é o ME do item (meu() confere os envolvidos)
    try:
        so_ct = set(os.listdir(os.path.join(raiz, cod))) <= {"ct.json", "recurso.json"}
    except OSError:
        so_ct = False
    return "" if so_ct else acesso["admin"]


def envolvidos(raiz, cod):
    """Analistas (normalizados) dos itens abertos em ct.json e recurso.json da pasta."""
    nomes = set()
    for arq in ("ct.json", "recurso.json"):
        try:
            with open(os.path.join(raiz, cod, arq), encoding="utf-8") as fh:
                nomes |= {norm(it.get("analista")) for it in json.load(fh).get("itens") or [] if it.get("analista")}
        except (OSError, ValueError, AttributeError):
            pass
    return nomes


def _ler_resp(raiz):
    try:
        with open(os.path.join(raiz, ".responsaveis.json"), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _cod(chave):
    return chave.split("/", 1)[0] if "/" in chave else chave[:-3]


# ------------------------------------------------------------------------------- ações

class Porta:
    def __init__(self, analista=None, raiz=None, acesso=ACESSO, chaves=CHAVES, escala=ESCALA, relatos=RELATOS, quadro=QUADRO):
        self.raiz, self.quadro_raiz = raiz or sc.RAIZ_SERVIDOR, quadro
        self.arq_acesso, self.arq_chaves, self.arq_escala, self.relatos = acesso, chaves, escala, relatos
        self.acesso = ler_acesso(acesso)
        self.admin = analista is None
        self.analista = self.acesso["admin"] if self.admin else analista
        if not self.admin and norm(analista) not in {norm(n) for n in self.acesso["analistas"]}:
            raise SystemExit("analista não cadastrado: %s" % analista)

    def _caixa_admin(self):
        """Códigos da última leitura da caixa do SOL no servidor (.caixa/caixa.json). O login do SOL do servidor é o do
        admin: o que está ali está na caixa dele, mesmo que a planilha dê o processo a outro (2.7.8, caso de 30/10/2026:
        PPCI de analista afastado redistribuído no SOL; a planilha ainda tinha o nome dele e o processo não descia)."""
        if not hasattr(self, "_caixa"):
            try:
                with open(os.path.join(self.raiz, ".caixa", "caixa.json"), encoding="utf-8") as fh:
                    self._caixa = {it.get("codigo") for it in json.load(fh).get("itens") or []}
            except (OSError, ValueError, AttributeError):
                self._caixa = set()
        return self._caixa

    def _passou_pela_caixa(self, cod):
        """2.7.11: o processo saiu da caixa do admin (CA/CIA lançado) depois da distribuição da planilha ao outro: o
        sol-caixa.json (só a leitura da caixa do servidor grava) é desta rodada, então continua do admin, que precisa
        receber o saiu_em e os Marcos novos. Antes, ao sair da caixa, o processo voltava a ser do outro e travava."""
        try:
            with open(os.path.join(self.raiz, cod, "sol-caixa.json"), encoding="utf-8") as fh:
                lido = json.load(fh).get("lido_em") or ""
        except (OSError, ValueError, AttributeError):
            return False
        try:
            with open(os.path.join(self.raiz, cod, "distribuicao.json"), encoding="utf-8") as fh:
                dist = json.load(fh).get("distribuido") or ""
        except (OSError, ValueError, AttributeError):
            dist = ""
        return bool(lido) and lido >= dist

    def meu(self, cod, resp=None):
        """Responsável pelo processo, ou ME de uma CT ou recurso em aberto nele (2.3.0)."""
        if norm(responsavel(self.raiz, cod, self.acesso, resp)) == norm(self.analista):
            return True
        if self.admin and (cod in self._caixa_admin() or self._passou_pela_caixa(cod)):
            return True
        return norm(self.analista) in envolvidos(self.raiz, cod)

    def quem_sou(self):
        return {"analista": self.analista, "papel": "admin" if self.admin else "analista"}

    def listar(self):
        resp = _ler_resp(self.raiz)
        return {k: v for k, v in sc.manifesto(self.raiz, self.raiz).items() if self.meu(_cod(k), resp)}

    def meus(self):
        """Códigos das pastas de que este analista é o responsável (o Painel do Dia usa no lugar do ls)."""
        resp = _ler_resp(self.raiz)
        return sorted(c for c in os.listdir(self.raiz) if sc.CODIGO.match(c) and os.path.isdir(os.path.join(self.raiz, c))
                      and self.meu(c, resp)) if os.path.isdir(self.raiz) else []

    def receber(self, dados):
        """Grava só o que é do analista (ou processo novo, que passa a ser dele). distribuicao.json não sobe."""
        resp = _ler_resp(self.raiz)
        novos = []

        def destino(k):
            cod = _cod(k)
            if k.split("/")[-1] in SO_SERVIDOR:
                return None
            existe = os.path.isdir(os.path.join(self.raiz, cod)) or os.path.isfile(os.path.join(self.raiz, cod + ".md"))
            if existe and not self.meu(cod, resp):
                return None
            if not existe and cod not in resp:
                resp[cod] = self.analista
                novos.append(cod)
            return os.path.join(self.raiz, *k.split("/"))
        feitas = sc.desempacotar(dados, destino)
        if novos:
            _gravar_json(os.path.join(self.raiz, ".responsaveis.json"), resp)
        return feitas

    def entregar(self, chaves):
        resp = _ler_resp(self.raiz)
        ok = {k: os.path.join(self.raiz, *k.split("/")) for k in chaves
              if sc.chave_valida(k) and self.meu(_cod(k), resp)}
        return sc.empacotar({k: c for k, c in ok.items() if os.path.isfile(c)})

    def escala(self):
        try:
            with open(self.arq_escala, encoding="utf-8") as fh:
                d = json.load(fh)
        except (OSError, ValueError):
            return {}
        if self.admin:
            return d
        horas = {n: h for n, h in (d.get("horas") or {}).items() if norm(n) == norm(self.analista)}
        return dict(d, horas=horas)

    def relato(self, ident, dados):
        if not re.fullmatch(r"[\w-]{1,40}", ident or ""):
            raise SystemExit("id de relato inválido")
        os.makedirs(self.relatos, exist_ok=True)
        nome = "%s-%s.zip" % (norm(self.analista).replace(" ", "_"), ident)
        with open(os.path.join(self.relatos, nome), "wb") as fh:
            fh.write(dados)
        try:  # 2.6.3: cartão com a 1ª linha do relato (o texto já vem limpo do PC); 2.6.10: no quadro do Programa (admin)
            import io
            import zipfile
            with zipfile.ZipFile(io.BytesIO(dados)) as z:
                txt = z.read("relato.md").decode("utf-8", "replace")
            linha = next((l.strip() for l in txt.split("**O que aconteceu**", 1)[-1].splitlines() if l.strip()), "")
            qd.adicionar(self.programa_raiz, ("Relato de %s: %s" % (self.analista, linha))[:200],
                         origem="Reportar ao Claude do SSEG.exe — ~/sseg-relatos/%s" % nome, autor=self.analista)
        except Exception:  # noqa: BLE001 — o relato já está guardado; o cartão é aviso
            pass
        return {"ok": True, "arquivo": nome}

    def relatos_lista(self):
        """Os relatos deste analista (admin: todos), do mais novo ao mais velho. Na pasta ~/sseg-relatos/<nome>/,
        quem trabalha no relato deixa estado.txt (trabalhando|pronto) e resposta.txt (o que dizer ao analista)."""
        if not os.path.isdir(self.relatos):
            return {"relatos": []}
        meu = norm(self.analista).replace(" ", "_") + "-"
        out = []
        for z in sorted((n for n in os.listdir(self.relatos) if n.endswith(".zip")), key=lambda n: n[-19:], reverse=True):
            if not (self.admin or z.startswith(meu)):
                continue
            pasta = os.path.join(self.relatos, z[:-4])

            def ler(n):
                try:
                    with open(os.path.join(pasta, n), encoding="utf-8", errors="replace") as fh:
                        return fh.read().strip()
                except OSError:
                    return ""
            out.append({"id": z[-19:-4], "arquivo": z, "estado": ler("estado.txt") or "recebido",
                        "resposta": ler("resposta.txt")[:2000]})
            if len(out) >= 20:
                break
        return {"relatos": out}

    # --- Quadro da seção (2.3.0)
    @property
    def programa_raiz(self):
        """Quadro do Programa (2.6.10, pedido do Átila): o que é de arrumar o SSEG (relatos, avisos dos scripts) é do
        administrador, não da seção."""
        return os.path.join(self.quadro_raiz, "programa")

    def quadro(self):
        r = {"cartoes": qd.ler(self.quadro_raiz)["cartoes"], "eu": self.analista, "admin": self.admin}
        if self.admin:
            r["programa"] = qd.ler(self.programa_raiz)["cartoes"]
        return r

    def _pode(self, c):
        return self.admin or norm(self.analista) in (norm(c.get("autor")), norm(c.get("pegou")))

    def quadro_mexer(self, pedido):
        acao, args = pedido.get("acao"), list(pedido.get("args") or [])
        if pedido.get("onde") == "programa":
            if not self.admin:
                raise SystemExit("o quadro do Programa é só do administrador")
            try:
                if acao == "adicionar":
                    return qd.adicionar(self.programa_raiz, args[0], "", args[1] if len(args) > 1 else "afazer", autor=self.analista)
                if acao == "alterar":
                    campos = {k: v for k, v in (args[1] if len(args) > 1 else {}).items()
                              if k in ("coluna", "titulo", "checklist", "feito_texto", "pegou")}
                    return qd.alterar(self.programa_raiz, args[0], **campos)
                if acao == "remover":
                    return qd.remover(self.programa_raiz, args[0])
                if acao == "restaurar":
                    return qd.restaurar(self.programa_raiz, args[0] if isinstance(args[0], dict) else {}, args[1] if len(args) > 1 else None)
            except ValueError as e:
                raise SystemExit(str(e))
            raise SystemExit("ação do quadro desconhecida: %s" % acao)
        cartao = lambda: qd._achar(qd.ler(self.quadro_raiz), args[0])  # noqa: E731
        try:
            if acao == "adicionar":
                return qd.adicionar(self.quadro_raiz, args[0], "", args[1] if len(args) > 1 else "afazer", autor=self.analista)
            if acao == "pegar":
                c = cartao()
                if c.get("pegou") and not self._pode(c):
                    raise SystemExit("%s já pegou essa tarefa" % c["pegou"])
                return qd.alterar(self.quadro_raiz, args[0], pegou=self.analista)
            if acao == "soltar":
                if not self._pode(cartao()):
                    raise SystemExit("só quem pegou solta a tarefa")
                return qd.alterar(self.quadro_raiz, args[0], pegou="")
            if acao == "alterar":
                campos = {k: v for k, v in (args[1] if len(args) > 1 else {}).items()
                          if k in ("coluna", "titulo", "checklist", "feito_texto", "pegou")}  # pegou = responsável (2.3.13)
                if not self._pode(cartao()):
                    raise SystemExit("só quem criou ou pegou a tarefa mexe nela (pegue antes)")
                return qd.alterar(self.quadro_raiz, args[0], **campos)
            if acao == "remover":
                if not self._pode(cartao()):
                    raise SystemExit("só quem criou ou pegou a tarefa exclui")
                return qd.remover(self.quadro_raiz, args[0])
            if acao == "restaurar":
                c = args[0] if isinstance(args[0], dict) else {}
                if not self._pode(c):
                    raise SystemExit("só quem criou ou pegou a tarefa desfaz")
                return qd.restaurar(self.quadro_raiz, c, args[1] if len(args) > 1 else None)
        except ValueError as e:
            raise SystemExit(str(e))
        raise SystemExit("ação do quadro desconhecida: %s" % acao)

    # --- SOL no servidor (2.3.17): o chip do SSEG.exe
    def sol(self):
        import sol_caixa
        import sol_senha
        r = {"chrome": False, "logado": False, "exp": None, "senha": bool(sol_senha.ler()),
             "trava": sol_senha._ler_texto(sol_senha.TRAVA), "ultimo_login": sol_senha._ler_texto(sol_senha.ULTIMO),
             "caixa_lida_em": "", "caixa_total": None}
        try:
            with open(os.path.join(sol_caixa.PROCESSOS, ".caixa", "caixa.json"), encoding="utf-8") as fh:
                c = json.load(fh)
            r["caixa_lida_em"], r["caixa_total"] = c.get("lido_em", ""), c.get("total")
        except (OSError, ValueError):
            pass
        try:
            aba = sol_caixa.aba_do_sol()
            if aba:
                s = aba.avaliar(sol_caixa.SESSAO)
                r.update(chrome=True, logado=bool(s.get("logado")), exp=s.get("exp"))
        except (OSError, RuntimeError, ValueError):
            pass
        return r

    def base(self, gerado_em=""):
        """Índice da base do SOL (sol_base.py) para a aba Processos. Igual ao que o PC já tem: só avisa.
        Vai comprimido (uns 7 mil processos, 2 MB em texto)."""
        import base64
        import gzip
        import sol_base
        try:
            with open(sol_base.INDICE, "rb") as fh:
                bruto = fh.read()
        except OSError:
            return {"vazio": True}
        g = json.loads(bruto).get("gerado_em", "")
        if gerado_em and gerado_em == g:
            return {"igual": True, "gerado_em": g}
        return {"gerado_em": g, "gz": base64.b64encode(gzip.compress(bruto)).decode()}

    def banco(self, consulta, params):
        """(28/10/2026) Aba Processos: painel, pesquisa, ficha e busca nas CIAs, no solcbm.db (sol_consulta.py).
        Todo analista vê a base inteira, como no índice."""
        import sol_consulta
        try:
            return sol_consulta.consultar(consulta, params)
        except (RuntimeError, ValueError, KeyError) as e:
            return {"erro": str(e)}

    def sol_caixa(self):
        self._so_admin()
        import contextlib
        import io
        import sol_caixa
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            rc = sol_caixa.levantar()
        return {"rc": rc, "saida": saida.getvalue()[-4000:]}

    # --- admin
    def _so_admin(self):
        if not self.admin:
            raise SystemExit("só o administrador do servidor")

    def analistas(self):
        self._so_admin()
        return {"admin": self.acesso["admin"],
                "analistas": [{"analista": n, "desde": a.get("desde", ""), "chave": a["chave"][:24] + "…" + a["chave"][-8:]}
                              for n, a in sorted(self.acesso["analistas"].items())]}

    def autorizar(self, pedido, script):
        self._so_admin()
        nome, chave = (pedido.get("analista") or "").strip(), " ".join((pedido.get("chave") or "").split()[:2])
        if not nome_ok(nome):
            raise SystemExit("nome de analista inválido")
        if not CHAVE_OK.match(chave):
            raise SystemExit("chave pública inválida")
        if norm(nome) == norm(self.acesso["admin"]):
            return self.admin_chave({"chave": chave, "rotulo": pedido.get("rotulo") or "pc"})
        for n, a in self.acesso["analistas"].items():
            if a["chave"] == chave and norm(n) != norm(nome):
                raise SystemExit("essa chave já é de %s" % n)
        self.acesso["analistas"] = {n: a for n, a in self.acesso["analistas"].items() if norm(n) != norm(nome)}
        self.acesso["analistas"][nome] = {"chave": chave, "desde": datetime.date.today().isoformat()}
        _gravar_json(self.arq_acesso, self.acesso)
        _reescrever_chaves(self.acesso, self.arq_chaves, script)
        return {"ok": True, "analista": nome}

    def admin_chave(self, pedido):
        """Mais um PC do administrador: a chave entra no authorized_keys SEM restrição (como a primeira dele).
        Fica fora do cadastro dos analistas e sobrevive ao _reescrever_chaves (que só mexe nas linhas com MARCA)."""
        self._so_admin()
        chave = " ".join((pedido.get("chave") or "").split()[:2])
        rotulo = re.sub(r"[^\w.-]", "-", str(pedido.get("rotulo") or "pc"))[:30] or "pc"
        if not CHAVE_OK.match(chave):
            raise SystemExit("chave pública inválida")
        try:
            velhas = open(self.arq_chaves, encoding="utf-8").read().splitlines()
        except OSError:
            velhas = []
        corpo = chave.split()[1]
        if any(corpo in l for l in velhas):
            return {"ok": True, "ja_estava": True}
        os.makedirs(os.path.dirname(self.arq_chaves), exist_ok=True)
        if os.path.exists(self.arq_chaves):
            import shutil
            shutil.copy2(self.arq_chaves, self.arq_chaves + ".bak-porta")
        tmp = self.arq_chaves + ".porta-tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write("\n".join(velhas + ["%s sseg-admin-%s" % (chave, rotulo)]) + "\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.arq_chaves)
        return {"ok": True, "ja_estava": False}

    def sol_snapshot(self, acao, codigo, refazer=False, ca=False):
        self._so_admin()
        import sol_snapshot
        try:
            return sol_snapshot.congelar(codigo, refazer) if acao == "congelar" else sol_snapshot.salvar(codigo, resultado="CA" if ca else "CIA")
        except (ValueError, RuntimeError, PermissionError, OSError) as e:
            return {"ok": False, "arquivos": [], "avisos": [str(e)]}

    def sol_senha_gravar(self, d):
        self._so_admin()
        import sol_senha
        try:
            sol_senha.salvar(d.get("matricula"), d.get("senha"))
        except ValueError as e:
            raise SystemExit(str(e))
        return {"ok": True, "matricula": str(d.get("matricula")).strip()}

    def sol_senha_apagar(self):
        self._so_admin()
        import sol_senha
        sol_senha.remover()
        return {"ok": True}

    def revogar(self, nome, script):
        self._so_admin()
        antes = len(self.acesso["analistas"])
        self.acesso["analistas"] = {n: a for n, a in self.acesso["analistas"].items() if norm(n) != norm(nome)}
        if len(self.acesso["analistas"]) == antes:
            raise SystemExit("não há analista %s" % nome)
        _gravar_json(self.arq_acesso, self.acesso)
        _reescrever_chaves(self.acesso, self.arq_chaves, script)
        return {"ok": True}

    def atribuir(self, cod, nome):
        self._so_admin()
        if not sc.CODIGO.match(cod or ""):
            raise SystemExit("código inválido")
        validos = {norm(n): n for n in list(self.acesso["analistas"]) + [self.acesso["admin"]]}
        if norm(nome) not in validos:
            raise SystemExit("analista não cadastrado: %s" % nome)
        resp = _ler_resp(self.raiz)
        resp[cod] = validos[norm(nome)]
        _gravar_json(os.path.join(self.raiz, ".responsaveis.json"), resp)
        return {"ok": True, "codigo": cod, "analista": resp[cod],
                "aviso": "a planilha manda: se o código estiver nela, vale o analista da planilha"
                if os.path.isfile(os.path.join(self.raiz, cod, "distribuicao.json")) else ""}


def executar(porta, args, entrada, script):
    """args = [ação, ...]. Devolve bytes para o stdout."""
    acao = (args or ["quem-sou"])[0].replace("remoto-", "")  # aceita os nomes do sincronizar.py
    resto = args[1:]
    if acao == "quem-sou":
        r = porta.quem_sou()
    elif acao == "listar":
        r = porta.listar()
    elif acao == "meus":
        return "".join(c + "\n" for c in porta.meus()).encode("utf-8")
    elif acao == "receber":
        r = porta.receber(entrada())
    elif acao == "entregar":
        return porta.entregar(json.loads(entrada() or b"[]"))
    elif acao == "quadro":
        r = porta.quadro()
    elif acao == "quadro-mexer":
        r = porta.quadro_mexer(json.loads(entrada() or b"{}"))
    elif acao == "escala":
        r = porta.escala()
    elif acao == "relato" and resto:
        r = porta.relato(resto[0], entrada())
    elif acao == "relatos":
        r = porta.relatos_lista()
    elif acao == "sol":
        r = porta.sol()
    elif acao == "base":
        r = porta.base(resto[0] if resto else "")
    elif acao == "banco" and resto:
        r = porta.banco(resto[0], json.loads(entrada() or b"{}"))
    elif acao == "sol-caixa":
        r = porta.sol_caixa()
    elif acao == "analistas":
        r = porta.analistas()
    elif acao == "autorizar":
        r = porta.autorizar(json.loads(entrada() or b"{}"), script)
    elif acao == "admin-chave":
        r = porta.admin_chave(json.loads(entrada() or b"{}"))
    elif acao in ("sol-congelar", "sol-salvar") and resto:
        r = porta.sol_snapshot(acao.split("-")[1] if acao == "sol-salvar" else "congelar", resto[0], "--refazer" in resto, "--ca" in resto)
    elif acao == "sol-senha-gravar":
        r = porta.sol_senha_gravar(json.loads(entrada() or b"{}"))
    elif acao == "sol-senha-apagar":
        r = porta.sol_senha_apagar()
    elif acao == "revogar" and resto:
        r = porta.revogar(" ".join(resto), script)
    elif acao == "atribuir" and len(resto) >= 2:
        r = porta.atribuir(resto[0], " ".join(resto[1:]))
    else:
        raise SystemExit("ação desconhecida: %s" % " ".join(args))
    return json.dumps(r, ensure_ascii=False).encode("utf-8")


def pedido(argv, original=""):
    """(analista, args). Com chave de analista, o SSH roda `porta.py --analista <nome>` e o pedido do
    PC ("python3 .../porta.py <ação> ...") chega em SSH_ORIGINAL_COMMAND."""
    if argv[:1] != ["--analista"]:
        return None, argv
    try:
        p = shlex.split(original or "")
    except ValueError:
        p = []
    if p[:1] == ["python3"]:
        p = p[1:]
    return argv[1], (p[1:] if p and p[0].endswith("porta.py") else [])


def main(argv):
    analista, args = pedido(argv, os.environ.get("SSH_ORIGINAL_COMMAND", ""))
    script = os.path.join("SSEG", "sseg", "scripts", "porta.py")  # relativo ao ~ do servidor
    sys.stdout.buffer.write(executar(Porta(analista), args, lambda: sys.stdin.buffer.read(), script))


if __name__ == "__main__":
    main(sys.argv[1:])
