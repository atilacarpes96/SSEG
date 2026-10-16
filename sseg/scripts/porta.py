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
  quadro                                  → o Quadro da seção (~/sseg-quadro/quadro.json)
  quadro-mexer                            → stdin {"acao", "args"}: adicionar, pegar, soltar, alterar,
                                            remover, restaurar. Todos criam, pegam e comentam; mover,
                                            editar e excluir só quem criou, quem pegou ou o admin
  escala                                  → a linha do analista no escala.json (o admin recebe tudo)
  relato <id>                             → guarda o .zip do stdin em ~/sseg-relatos/<analista>-<id>.zip
  analistas                     (admin)   → lista dos cadastrados
  autorizar                     (admin)   → stdin {"analista", "chave"}: cadastra e libera a chave
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

    def meu(self, cod, resp=None):
        """Responsável pelo processo, ou ME de uma CT ou recurso em aberto nele (2.3.0)."""
        if norm(responsavel(self.raiz, cod, self.acesso, resp)) == norm(self.analista):
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
        return {"ok": True, "arquivo": nome}

    # --- Quadro da seção (2.3.0)
    def quadro(self):
        return {"cartoes": qd.ler(self.quadro_raiz)["cartoes"], "eu": self.analista, "admin": self.admin}

    def _pode(self, c):
        return self.admin or norm(self.analista) in (norm(c.get("autor")), norm(c.get("pegou")))

    def quadro_mexer(self, pedido):
        acao, args = pedido.get("acao"), list(pedido.get("args") or [])
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
            raise SystemExit("esse é o administrador: ele já entra com a chave dele")
        for n, a in self.acesso["analistas"].items():
            if a["chave"] == chave and norm(n) != norm(nome):
                raise SystemExit("essa chave já é de %s" % n)
        self.acesso["analistas"] = {n: a for n, a in self.acesso["analistas"].items() if norm(n) != norm(nome)}
        self.acesso["analistas"][nome] = {"chave": chave, "desde": datetime.date.today().isoformat()}
        _gravar_json(self.arq_acesso, self.acesso)
        _reescrever_chaves(self.acesso, self.arq_chaves, script)
        return {"ok": True, "analista": nome}

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
    elif acao == "analistas":
        r = porta.analistas()
    elif acao == "autorizar":
        r = porta.autorizar(json.loads(entrada() or b"{}"), script)
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
