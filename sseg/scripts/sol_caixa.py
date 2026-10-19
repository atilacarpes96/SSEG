#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sol_caixa.py — levantamento da caixa do SOL no servidor, sem modelo (zero token).

O QUE FAZ
---------
Fala com o Chrome do servidor (~/rotinas/sol-chrome.sh, já logado no SOL pelo analista pelo
celular) pela porta de depuração 127.0.0.1:9222 e, dentro da aba do SOL:
  1. confere a sessão (tokens no sessionStorage, só as datas; o token não sai da página);
  2. lê a caixa: GET /analise-tecnica/pendentes, todas as páginas;
  3. para cada processo que ainda não tem api-<ID>.json na pasta, baixa
     GET /licenciamentos/<ID> (ID do licenciamento, o mesmo JSON que o `sseg.py receber` grava)
     em sseg/processos/<código>/api-<ID>.json;
  4. grava sseg/processos/.caixa/caixa.json (o que tem na caixa, o que é novo, quando leu);
  5. (2.3.13) baixa os Marcos de cada processo (marcos.json + marcos-resumo.json, pelo marcos.py):
     data de protocolo, análises anteriores com o PDF da CIA e recursos. Recurso ou marco novo
     dispara o gatilho: aviso na saída, .caixa/gatilhos.json e cartão no Quadro da seção.
     (17/10/2026) baixa o PDF de cada CIA anterior (GET /arquivo/<id>, ids do marcos-resumo.json)
     e extrai o texto: cia-<id>.pdf, cia-<id>.txt e cia-ultima.txt. Só o que ainda não tem.
Pausa de 0,15 s entre consultas e até 3 tentativas em erro passageiro (5xx, 429, rede), como o
coletor do Sgt Magalhães: o SOL é sistema de produção.
A pasta sseg/processos/ não vai ao GitHub (.gitignore) e desce ao PC pelo `sseg.py sincronizar`.

O QUE NÃO FAZ
-------------
  - Só lê com a sessão aberta. Exceção (17/10/2026, autorizada pelo Átila): sessão caída, recarrega a aba
    e, se o SOE pedir, digita a senha que o Átila gravou com sol_senha.py — uma tentativa por queda;
    falhou, liga a trava (~/sseg-acesso/sol-login-falhou) e avisa no Quadro.
  - Não decide nada da análise: a pré-análise é outra rotina, que lê estes arquivos.
  - Não sobrescreve api-<ID>.json que já existe (use --forcar).

Campos do item de `pendentes` fixados em 16/10/2026 pelo primeiro item real (.caixa/item-exemplo.json):
id = licenciamento, idAnalise = análise técnica, numeroLicenciamento = código. Até ali o id era
procurado em nomes errados e nenhum JSON era baixado. No fim, roda o pre_analise.py nos novos.

USO (no servidor)
---
  python3 sseg/scripts/sol_caixa.py            # levanta e imprime um resumo
  python3 sseg/scripts/sol_caixa.py --sessao   # só diz se está logado e até quando
Saída: 0 ok · 2 sessão caída e sem login automático (entrar pelo celular) · 3 Chrome do servidor fora do ar
"""

import argparse
import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import time
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
PROCESSOS = os.path.normpath(os.path.join(AQUI, "..", "processos"))
DEPURACAO = "http://127.0.0.1:9222"
API = "/solcbm/api/v1/adm/analise-tecnica"
LICENCIAMENTO = "/solcbm/api/v1/adm/licenciamentos"
HISTORICO = "/solcbm/api/v1/adm/licenciamento-historico"
FACTS = "/solcbm/api/v1/adm/facts/facts-licenciamento"
ARQUIVO = "/solcbm/api/v1/adm/arquivo"
PAUSA = 0.15      # segundos entre consultas: o SOL é sistema de produção
TENTATIVAS = 3    # erro passageiro (rede, 429, 5xx): tenta de novo com espera de 1 s, 2 s
LOGIN = os.path.expanduser("~/sseg-acesso/sol-login.json")  # gravado pelo Átila com sol_senha.py
ENTRADA = "https://www.solcbm.rs.gov.br/solcbm/adm/"


# ------------------------------------------------------------------ DevTools (só biblioteca padrão)

class Aba:
    """Uma aba do Chrome pela porta de depuração: avaliar(js) devolve o valor (JSON) do script."""

    def __init__(self, ws_url):
        host, caminho = ws_url[5:].split("/", 1)
        h, porta = host.split(":")
        self.s = socket.create_connection((h, int(porta)), timeout=60)
        chave = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(("GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % (caminho, host, chave)).encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        self.buf = buf.split(b"\r\n\r\n", 1)[1]
        self.n = 0

    def _ler(self, n):
        while len(self.buf) < n:
            self.buf += self.s.recv(65536)
        r, self.buf = self.buf[:n], self.buf[n:]
        return r

    def _enviar(self, txt):
        d = txt.encode()
        m = os.urandom(4)
        n = len(d)
        if n < 126:
            cab = bytes([0x81, 0x80 | n])
        elif n < 65536:
            cab = bytes([0x81, 0x80 | 126]) + struct.pack(">H", n)
        else:
            cab = bytes([0x81, 0x80 | 127]) + struct.pack(">Q", n)
        self.s.sendall(cab + m + bytes(b ^ m[i % 4] for i, b in enumerate(d)))

    def _receber(self):
        partes = []
        while True:
            b1, b2 = self._ler(2)
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._ler(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._ler(8))[0]
            dado = self._ler(n)
            op = b1 & 0x0F
            if op in (1, 0):
                partes.append(dado)
                if b1 & 0x80:
                    return b"".join(partes).decode()

    def avaliar(self, js):
        self.n += 1
        self._enviar(json.dumps({"id": self.n, "method": "Runtime.evaluate",
                                 "params": {"expression": js, "awaitPromise": True, "returnByValue": True}}))
        while True:
            m = json.loads(self._receber())
            if m.get("id") == self.n:
                break
        r = m.get("result", {})
        if r.get("exceptionDetails"):
            raise RuntimeError("Erro na página: " + json.dumps(r["exceptionDetails"], ensure_ascii=False)[:300])
        return json.loads(r["result"]["value"])


def aba_do_sol():
    try:
        paginas = json.load(urllib.request.urlopen(DEPURACAO + "/json/list", timeout=5))
    except OSError:
        return None
    abas = [p for p in paginas if p.get("type") == "page"]
    sol = [p for p in abas if "solcbm.rs.gov.br" in p.get("url", "")]
    # caída, a aba fica na tela do SOE (outro endereço): o Chromium do servidor é só do SOL, vale a 1ª aba
    sol = sol or (abas[:1] if os.path.exists(LOGIN) else [])
    return Aba(sol[0]["webSocketDebuggerUrl"]) if sol else None


# ------------------------------------------------------------------ o que roda dentro da aba

SESSAO = r"""(() => {
  const out = { url: location.hash.replace(/\?.*/, ""), agora: Math.floor(Date.now() / 1000) };
  const t = sessionStorage.getItem("access_token") || localStorage.getItem("access_token");
  if (!t) return JSON.stringify({ ...out, logado: false });
  try {
    const p = JSON.parse(atob(t.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return JSON.stringify({ ...out, logado: p.exp > out.agora, exp: p.exp });
  } catch (e) { return JSON.stringify({ ...out, logado: false }); }
})()"""

BUSCAR = r"""(async () => {
  const tok = sessionStorage.getItem("access_token") || localStorage.getItem("access_token");
  const r = await fetch(%s, { credentials: "include", headers: { Authorization: "Bearer " + tok } });
  return JSON.stringify({ status: r.status, corpo: await r.text() });
})()"""

# o PDF em base64, em blocos (fromCharCode com o arquivo inteiro estoura a pilha)
BAIXAR = r"""(async () => {
  const tok = sessionStorage.getItem("access_token") || localStorage.getItem("access_token");
  const r = await fetch(%s, { credentials: "include", headers: { Authorization: "Bearer " + tok } });
  if (r.status !== 200) return JSON.stringify({ status: r.status, b64: "" });
  const b = new Uint8Array(await r.arrayBuffer());
  let s = "";
  for (let i = 0; i < b.length; i += 32768) s += String.fromCharCode.apply(null, b.subarray(i, i + 32768));
  return JSON.stringify({ status: 200, b64: btoa(s) });
})()"""


def _consultar(aba, js, caminho):
    """Uma consulta na aba, com pausa antes e nova tentativa em erro passageiro. 401/403 não repete."""
    for n in range(TENTATIVAS):
        time.sleep(PAUSA)
        try:
            r = aba.avaliar(js % json.dumps(caminho))
        except RuntimeError as e:  # o fetch falhou dentro da página (rede)
            r = {"status": 0, "corpo": str(e), "b64": ""}
        if r["status"] in (401, 403):
            raise PermissionError("SOL respondeu %s em %s" % (r["status"], caminho))
        if not (r["status"] in (0, 429) or r["status"] >= 500) or n == TENTATIVAS - 1:
            return r
        time.sleep(2 ** n)


def buscar(aba, caminho):
    r = _consultar(aba, BUSCAR, caminho)
    if r["status"] != 200:
        raise RuntimeError("SOL respondeu %s em %s: %s" % (r["status"], caminho, r["corpo"][:200]))
    return json.loads(r["corpo"])


def baixar_cias(aba, codigo, linha):
    """PDF e texto de cada CIA anterior: cia-<id>.pdf, cia-<id>.txt e cia-ultima.txt (os nomes do
    `analise_registro.py sol-pdf`, que o Claude usava no chat). Ids do marcos-resumo.json; só baixa o
    que ainda não tem. Erro vira aviso e não para a caixa: tenta de novo na próxima leitura."""
    import marcos
    pasta = os.path.join(PROCESSOS, str(codigo))
    try:
        with open(os.path.join(pasta, marcos.RESUMO), encoding="utf-8") as fh:
            r = json.load(fh)
    except (OSError, ValueError):
        return
    ids = [a["arquivo"] for a in r.get("analises") or [] if a.get("resultado") == "CIA" and a.get("arquivo")]
    for ident in ids:
        txt = os.path.join(pasta, "cia-%s.txt" % ident)
        if os.path.exists(txt) and os.path.getsize(txt):
            continue
        try:
            d = _consultar(aba, BAIXAR, "%s/%s" % (ARQUIVO, ident))
            if d["status"] != 200:
                raise RuntimeError("SOL respondeu %s" % d["status"])
            dados = base64.b64decode(d["b64"])
            if not dados.startswith(b"%PDF"):
                raise RuntimeError("não veio PDF")
            pdf = os.path.join(pasta, "cia-%s.pdf" % ident)
            with open(pdf, "wb") as fh:
                fh.write(dados)
            subprocess.run(["pdftotext", "-layout", pdf, txt], check=True, timeout=60)
            if not os.path.getsize(txt):
                raise RuntimeError("PDF sem texto (imagem): ler com pdftoppm")
            linha["cias"] = linha.get("cias", 0) + 1
        except PermissionError:  # sessão caída: não é problema desta CIA
            raise
        except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as e:
            linha["aviso"] = "CIA %s: %s" % (ident, e)
    ultima = os.path.join(pasta, "cia-%s.txt" % ids[-1]) if ids else ""
    if ultima and os.path.exists(ultima) and os.path.getsize(ultima):
        destino = os.path.join(pasta, "cia-ultima.txt")
        with open(ultima, "rb") as fh:
            novo = fh.read()
        try:
            with open(destino, "rb") as fh:
                igual = fh.read() == novo
        except OSError:
            igual = False
        if not igual:
            shutil.copyfile(ultima, destino)


# ------------------------------------------------------------------ caixa

def _achar(item, *nomes):
    """Procura o primeiro campo existente, aceitando caminhos com ponto (ex.: licenciamento.numero)."""
    for nome in nomes:
        v = item
        for parte in nome.split("."):
            v = v.get(parte) if isinstance(v, dict) else None
        if v not in (None, ""):
            return v
    return None


def ler_caixa(aba):
    itens, pagina = [], 0
    while True:
        d = buscar(aba, "%s/pendentes?paginaAtual=%d" % (API, pagina))
        lista = d.get("lista") or []
        itens += lista
        total = d.get("total") or 0
        if not lista or len(itens) >= total or pagina > 50:
            return itens
        pagina += 1


QUADRO_SECAO = os.path.expanduser("~/sseg-quadro")


GATILHOS = "gatilhos-quadro.json"  # o gatilhos.json da 2.3.14 marcava como avisado sem o cartão existir


def motivos_marcos(r):
    """Chave curta de cada motivo (o que já foi avisado) → texto para o cartão."""
    import marcos
    m = {}
    br = lambda s: "/".join(reversed((s or "").split("-")))  # noqa: E731
    sem_status = [x for x in r["recursos"] if "status" not in x]
    estranhos = [x for x in r["recursos"] if "status" in x and x["status"] not in marcos.RECURSO_STATUS]
    if sem_status:  # o histórico não veio: só os Marcos, sem o resultado
        u = sem_status[-1]
        m["recurso"] = "recurso sem resultado lido (%d marco%s, último: %s em %s)" % (
            len(sem_status), "s" if len(sem_status) > 1 else "", u["descricao"], br(u["data"]))
    for x in estranhos:  # resultado que o script ainda não conhece
        m["recurso:" + x["status"]] = "recurso com resultado novo: %s (%s)" % (x["status"], br(x["data"]))
    for x in r["novos"]:
        m["novo:" + x["descricao"]] = x["descricao"]
    return m


def marcos_proc(aba, ident, codigo, linha):
    """Baixa os Marcos, grava marcos.json e marcos-resumo.json e dispara o gatilho de recurso/marco novo:
    linha na saída e UM cartão por processo no Quadro da seção (~/sseg-quadro, o mesmo da porta.py; o
    quadro.py cria a pasta). Só depois que o cartão existe o motivo vai a .caixa/gatilhos-quadro.json."""
    import marcos
    pasta = os.path.join(PROCESSOS, str(codigo))
    for nome, caminho, opcional in ((marcos.ARQUIVO, "%s/%s/marcos" % (LICENCIAMENTO, ident), False),
                                    (marcos.HISTORICO, "%s/%s" % (HISTORICO, ident), True),  # resultado dos recursos
                                    (marcos.FACTS, "%s/%s" % (FACTS, ident), True)):         # consultas técnicas (CT)
        try:
            dados = buscar(aba, caminho)
        except RuntimeError as e:
            if not opcional:
                raise
            linha.setdefault("aviso", "%s: %s" % (nome, e))
            continue
        with open(os.path.join(pasta, nome), "w", encoding="utf-8") as fh:
            json.dump(dados, fh, ensure_ascii=False)
    r = marcos.resumir_pasta(pasta)
    if not r or not r["gatilho"]:
        return
    motivos = motivos_marcos(r)
    linha["gatilho"] = list(motivos.values())
    arq = os.path.join(PROCESSOS, ".caixa", GATILHOS)
    try:
        with open(arq, encoding="utf-8") as fh:
            vistos = json.load(fh)
    except (OSError, ValueError):
        vistos = {}
    novos = {k: v for k, v in motivos.items() if k not in vistos.get(str(codigo), [])}
    if not novos:
        return
    import quadro
    textos = [novos.pop("recurso")] if "recurso" in novos else []
    if novos:
        textos.append(("marcos novos: " if len(novos) > 1 else "marco novo: ") + "; ".join(novos.values()))
    titulo = "Ensinar o script dos Marcos: %s — %s" % (codigo, " · ".join(textos))
    quadro.adicionar(QUADRO_SECAO, titulo[:200],
                     origem="gatilho do sol_caixa.py: ver os marcos reais no SOL e dizer o que fazer com eles (marcos.py)",
                     autor="SSEG")
    linha["cartao"] = True
    ja = vistos.setdefault(str(codigo), [])
    ja += [k for k in motivos if k not in ja]
    with open(arq, "w", encoding="utf-8") as fh:
        json.dump(vistos, fh, ensure_ascii=False, indent=1)


# ------------------------------------------------------------------ login automático (17/10/2026)
# Autorizado pelo Átila: com a senha que ele gravou (sol_senha.py), refaz a sessão na MESMA aba do
# Chromium do servidor. Campos do SOE como no coletor do Sgt Magalhães. Uma tentativa por queda.

TELA_LOGIN = r"""(() => {
  const vis = e => e && (e.offsetParent !== null || getComputedStyle(e).position === "fixed");
  const t = sessionStorage.getItem("access_token") || localStorage.getItem("access_token");
  let logado = false;
  try { logado = !!t && JSON.parse(atob(t.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))).exp > Date.now() / 1000; } catch (e) {}
  const erros = [...document.querySelectorAll("[role=alert], .alert, .alert-danger, .ui-messages-error, .ui-growl-message, .text-danger, .invalid-feedback, [class*=erro], [class*=error]")]
    .filter(vis).map(e => e.innerText.trim()).filter(s => s && s.length < 300);
  return JSON.stringify({ sol: location.host.includes("solcbm.rs.gov.br"), logado, form: vis(document.querySelector("#senha")), erros });
})()"""

PREENCHER = r"""(() => {
  const set = (sel, v) => {
    const e = document.querySelector(sel);
    if (!e) return false;
    const p = Object.getPrototypeOf(e), d = Object.getOwnPropertyDescriptor(p, "value");
    d && d.set ? d.set.call(e, v) : (e.value = v);
    e.dispatchEvent(new Event("input", { bubbles: true }));
    e.dispatchEvent(new Event("change", { bubbles: true }));
    return e.value === v;
  };
  const ok = [set("#organizacao", %s), set("#matricula", %s), set("#senha", %s)];
  if (ok.includes(false)) return JSON.stringify({ ok: false, campos: ok });
  document.querySelector("#btnLogonOrganizacao").click();
  return JSON.stringify({ ok: true });
})()"""


def _tela(aba):
    try:
        return aba.avaliar(TELA_LOGIN)
    except (RuntimeError, OSError, ValueError):  # página trocando no meio da leitura
        return {"sol": False, "logado": False, "form": False, "erros": []}


def _falhou(msg):
    """Liga a trava (nada de nova tentativa até o Átila rodar sol_senha.py gravar) e avisa no Quadro."""
    import sol_senha
    with open(sol_senha.TRAVA, "w", encoding="utf-8") as fh:
        fh.write("%s · %s" % (time.strftime("%d/%m/%Y %H:%M"), msg))
    try:
        import quadro
        quadro.adicionar(QUADRO_SECAO, ("Login automático do SOL falhou: %s. Entrar pelo celular e rodar "
                                        "sol_senha.py gravar" % msg)[:200],
                         origem="sol_caixa.py, entrar(): trava ligada, sem nova tentativa", autor="SSEG")
    except Exception as e:  # o aviso no Quadro não pode esconder a falha
        print("  (cartão no Quadro não criado: %s)" % e)
    return False, msg


def entrar(aba):
    """(conseguiu, texto). Recarrega o SOL; se o login do SOE ainda vale, o token volta sem senha.
    Se aparecer o formulário, preenche UMA vez com a senha gravada. Falha liga a trava."""
    import sol_senha
    cred = sol_senha.ler()
    if not cred:
        return False, "sem senha gravada (sol_senha.py gravar)"
    if os.path.exists(sol_senha.TRAVA):
        return False, "trava ligada desde a última falha: " + sol_senha._ler_texto(sol_senha.TRAVA)
    try:  # ?r= muda o endereço: só o "#" não recarregaria a página
        aba.avaliar("(() => { location.href = %s; return '1'; })()" % json.dumps("%s?r=%d#/dashboard" % (ENTRADA, time.time())))
    except (RuntimeError, OSError, ValueError):
        pass
    fim = time.time() + 30
    while True:
        time.sleep(1)
        t = _tela(aba)
        if t["sol"] and t["logado"]:
            return True, "sessão renovada sem senha (o login do SOE ainda valia)"
        if t["form"]:
            break
        if time.time() > fim:
            return False, "o formulário do SOE não apareceu em 30 s (nada preenchido)"
    antes = set(t["erros"])
    time.sleep(1)  # a tela termina de montar
    r = aba.avaliar(PREENCHER % (json.dumps("cbm"), json.dumps(cred["matricula"]), json.dumps(cred["senha"])))
    if not r.get("ok"):
        return _falhou("campos do SOE não preenchidos (%s): a tela mudou?" % r.get("campos"))
    fim = time.time() + 30
    while time.time() < fim:
        time.sleep(1)
        t = _tela(aba)
        if t["sol"] and t["logado"]:
            with open(sol_senha.ULTIMO, "w", encoding="utf-8") as fh:
                fh.write(time.strftime("%d/%m/%Y %H:%M"))
            return True, "sessão refeita por login automático"
        novos = [e for e in t["erros"] if e not in antes]
        if novos and not t["sol"]:
            return _falhou("o SOE recusou: " + novos[0])
    return _falhou("o login não terminou em 30 s")


def _logar_se_caiu(aba):
    """Sessão caída: uma chamada a entrar() e nova conferência. Devolve o SESSAO final."""
    s = aba.avaliar(SESSAO)
    if s["logado"]:
        return s
    # a caixa, a conferência de hora em hora e a base (sol_base.py) usam a mesma aba: um login por vez,
    # e quem esperou confere de novo antes de digitar (o outro pode ter acabado de entrar)
    import fcntl
    with open(os.path.join(os.path.dirname(LOGIN), "sol-entrar.lock"), "w") as trava:
        fcntl.flock(trava, fcntl.LOCK_EX)
        s = aba.avaliar(SESSAO)
        if s["logado"]:
            return s
        return _entrar_e_conferir(aba, s)


def _entrar_e_conferir(aba, s):
    ok, txt = entrar(aba)
    print(("Sessão do SOL: %s." if ok else "Login automático não feito: %s.") % txt)
    return aba.avaliar(SESSAO) if ok else s


def marcar_saida(aba, codigo):
    """Processo que estava na caixa e saiu (CA ou CIA lançados no SOL, 2.5.1): atualiza os Marcos uma vez, para a
    pasta saber o resultado, e grava saiu_em no sol-caixa.json. O SSEG.exe usa isso para descer o processo da lista."""
    arq = os.path.join(PROCESSOS, str(codigo), "sol-caixa.json")
    try:
        with open(arq, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return None
    if d.get("saiu_em"):
        return None
    if d.get("id"):
        try:
            marcos_proc(aba, d["id"], codigo, {})
        except RuntimeError:
            pass  # sem os Marcos o processo desce igual, só sem o resultado
    d["saiu_em"] = time.strftime("%Y-%m-%d")
    with open(arq, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    return d["saiu_em"]


def levantar(forcar=False):
    aba = aba_do_sol()
    if aba is None:
        print("Chrome do servidor fora do ar ou sem aba do SOL: rode ~/rotinas/sol-chrome.sh iniciar.")
        return 3
    s = _logar_se_caiu(aba)
    if not s["logado"]:
        print("Sessão do SOL caída: entre de novo pelo celular.")
        return 2
    caixa = os.path.join(PROCESSOS, ".caixa")
    os.makedirs(caixa, exist_ok=True)
    try:
        itens = ler_caixa(aba)
    except PermissionError as e:
        print("Sessão do SOL recusada (%s): entre de novo pelo celular." % e)
        return 2
    if itens and not os.path.exists(os.path.join(caixa, "item-exemplo.json")):
        with open(os.path.join(caixa, "item-exemplo.json"), "w", encoding="utf-8") as fh:
            json.dump(itens[0], fh, ensure_ascii=False, indent=1)
    try:  # quem já estava na caixa na leitura anterior (2.3.23): quem volta para outra análise baixa o JSON de novo
        with open(os.path.join(caixa, "caixa.json"), encoding="utf-8") as fh:
            estavam = {i.get("codigo") for i in json.load(fh).get("itens") or []}
    except (OSError, ValueError):
        estavam = None
    resumo = []
    for it in itens:
        # Item real (15/10/2026, .caixa/item-exemplo.json): "id" é o do LICENCIAMENTO (bate com o
        # api-<ID>.json) e "idAnalise" o da análise técnica; o código vem em "numeroLicenciamento".
        ident = _achar(it, "id", "licenciamento.id", "idLicenciamento", "licenciamentoId")
        codigo = _achar(it, "numeroLicenciamento", "licenciamento.numero", "numero", "codigo")
        linha = {"id": ident, "id_analise": _achar(it, "idAnalise", "idAnaliseTecnica"), "codigo": codigo, "novo": False}
        if ident and codigo:
            pasta = os.path.join(PROCESSOS, str(codigo))
            arq = os.path.join(pasta, "api-%s.json" % ident)
            # voltou à caixa (outra análise) com o JSON da análise anterior na pasta: baixa o de agora e guarda o
            # velho como anterior-api-<ID>.json, que a pré-análise da reanálise compara (antes ficava o velho)
            voltou = estavam is not None and codigo not in estavam and os.path.exists(arq)
            if forcar or voltou or not os.path.exists(arq):
                d = buscar(aba, "%s/%s" % (LICENCIAMENTO, ident))
                codigo_api = d.get("numero")
                if codigo_api and codigo_api != codigo:  # o item da caixa mentiu: vale o do SOL
                    linha["aviso"] = "código do item %s, do licenciamento %s" % (codigo, codigo_api)
                    codigo = linha["codigo"] = codigo_api
                    pasta = os.path.join(PROCESSOS, str(codigo))
                    arq = os.path.join(pasta, "api-%s.json" % ident)
                os.makedirs(pasta, exist_ok=True)
                if os.path.exists(arq):
                    with open(arq, encoding="utf-8") as fh:
                        velho = json.load(fh)
                    if velho != d:
                        os.replace(arq, os.path.join(pasta, "anterior-api-%s.json" % ident))
                with open(arq, "w", encoding="utf-8") as fh:
                    json.dump(d, fh, ensure_ascii=False)
                linha["novo"] = True
        else:
            linha["erro"] = "id ou código não achados no item (ver .caixa/item-exemplo.json)"
        if codigo:  # o que a tela do SOL mostra, para o SSEG.exe (tabela do Início e link da análise)
            pasta = os.path.join(PROCESSOS, str(codigo))
            os.makedirs(pasta, exist_ok=True)
            with open(os.path.join(pasta, "sol-caixa.json"), "w", encoding="utf-8") as fh:
                json.dump({"lido_em": time.strftime("%Y-%m-%d"), "id": ident, "id_analise": linha["id_analise"],
                           "razao_social": it.get("razaoSocial"), "ocupacao": it.get("ocupacaoPredominante"),
                           "area": it.get("area"), "tipo": it.get("tipo"), "dias_analise": it.get("qtdDiasAnalise"),
                           "solicitacao": it.get("dataSolicitacao"), "prioridade": it.get("prioridade")},
                          fh, ensure_ascii=False, indent=1)
        if ident and codigo:  # Marcos (2.3.13): protocolo, análises, recursos — a cada leitura, porque mudam
            try:
                marcos_proc(aba, ident, codigo, linha)
            except RuntimeError as e:
                linha["aviso"] = "marcos: %s" % e
            baixar_cias(aba, codigo, linha)  # a CIA anterior chega pronta: o Claude não baixa mais no chat
        resumo.append(linha)
    sairam = []
    if estavam is not None and itens:  # caixa vazia na leitura = leitura suspeita: não marca ninguém como saído
        atuais = {r["codigo"] for r in resumo if r.get("codigo")}
        for cod in sorted(c for c in estavam - atuais if c):
            if marcar_saida(aba, cod):
                sairam.append(cod)
    if sairam:
        print("saíram da caixa: %s" % ", ".join(sairam))
    agora = time.strftime("%Y-%m-%d %H:%M")
    with open(os.path.join(caixa, "caixa.json"), "w", encoding="utf-8") as fh:
        json.dump({"lido_em": agora, "total": len(itens), "itens": resumo}, fh, ensure_ascii=False, indent=1)
    novos = [r["codigo"] for r in resumo if r["novo"]]
    # pré-análise documental (script, sem Claude): à força nos que acabaram de chegar; nos outros, só se o
    # JSON ou o marcos-resumo.json mudou desde a última (o pre_analise.py compara as datas dos arquivos)
    import pre_analise
    for c in [r["codigo"] for r in resumo if r.get("codigo")]:
        sit, txt = pre_analise.pre_analisar(c, forcar=c in novos)
        if sit != "em-dia":
            print("  pré-análise %s: %s" % (c, txt))
    cias = sum(r.get("cias", 0) for r in resumo)
    print("%s · caixa: %d · novos baixados: %d%s · CIAs baixadas: %d" % (
        agora, len(itens), len(novos), (" (" + ", ".join(map(str, novos)) + ")") if novos else "", cias))
    for r in resumo:
        if r.get("erro"):
            print("  ✗", r["erro"])
        if r.get("aviso"):
            print("  !", r["aviso"])
        for g in r.get("gatilho") or []:
            print("  !! %s — %s%s" % (r["codigo"], g, " (cartão novo no Quadro da seção)" if r.get("cartao") else " (já avisado)"))
    return 0


def sessao():
    aba = aba_do_sol()
    if aba is None:
        print("Chrome do servidor fora do ar ou sem aba do SOL.")
        return 3
    s = _logar_se_caiu(aba)
    if s["logado"]:
        print("Logado no SOL (%s), token até %s." % (s["url"], time.strftime("%H:%M", time.localtime(s["exp"]))))
        return 0
    print("Sessão do SOL caída (%s)." % s["url"])
    return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sessao", action="store_true", help="só diz se está logado e até quando")
    ap.add_argument("--forcar", action="store_true", help="baixa de novo mesmo se api-<ID>.json existir")
    a = ap.parse_args()
    sys.exit(sessao() if a.sessao else levantar(a.forcar))
