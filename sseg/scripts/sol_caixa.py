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
  4. grava sseg/processos/.caixa/caixa.json (o que tem na caixa, o que é novo, quando leu).
A pasta sseg/processos/ não vai ao GitHub (.gitignore) e desce ao PC pelo `sseg.py sincronizar`.

O QUE NÃO FAZ
-------------
  - Não entra no SOL, não digita senha, não clica em nada: só lê com a sessão aberta.
  - Não decide nada da análise: a pré-análise é outra rotina, que lê estes arquivos.
  - Não sobrescreve api-<ID>.json que já existe (use --forcar).

Os campos de cada item de `pendentes` ainda não foram vistos com processo na caixa (13 e
14/10/2026 ela estava vazia): o primeiro item lido fica cru em .caixa/item-exemplo.json e o id
e o código são procurados pelos nomes prováveis. Conferir e fixar quando houver processo.

USO (no servidor)
---
  python3 sseg/scripts/sol_caixa.py            # levanta e imprime um resumo
  python3 sseg/scripts/sol_caixa.py --sessao   # só diz se está logado e até quando
Saída: 0 ok · 2 sessão caída (entrar de novo pelo celular) · 3 Chrome do servidor fora do ar
"""

import argparse
import base64
import json
import os
import socket
import struct
import sys
import time
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
PROCESSOS = os.path.normpath(os.path.join(AQUI, "..", "processos"))
DEPURACAO = "http://127.0.0.1:9222"
API = "/solcbm/api/v1/adm/analise-tecnica"
LICENCIAMENTO = "/solcbm/api/v1/adm/licenciamentos"


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
    sol = [p for p in paginas if p.get("type") == "page" and "solcbm.rs.gov.br" in p.get("url", "")]
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


def buscar(aba, caminho):
    r = aba.avaliar(BUSCAR % json.dumps(caminho))
    if r["status"] in (401, 403):
        raise PermissionError("SOL respondeu %s em %s" % (r["status"], caminho))
    if r["status"] != 200:
        raise RuntimeError("SOL respondeu %s em %s: %s" % (r["status"], caminho, r["corpo"][:200]))
    return json.loads(r["corpo"])


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


def levantar(forcar=False):
    aba = aba_do_sol()
    if aba is None:
        print("Chrome do servidor fora do ar ou sem aba do SOL: rode ~/rotinas/sol-chrome.sh iniciar.")
        return 3
    s = aba.avaliar(SESSAO)
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
    resumo = []
    for it in itens:
        ident = _achar(it, "licenciamento.id", "idLicenciamento", "licenciamentoId")
        codigo = _achar(it, "licenciamento.numero", "numeroLicenciamento", "numero", "codigo")
        linha = {"id": ident, "id_analise": _achar(it, "id", "idAnaliseTecnica"), "codigo": codigo, "novo": False}
        if ident and codigo:
            pasta = os.path.join(PROCESSOS, str(codigo))
            arq = os.path.join(pasta, "api-%s.json" % ident)
            if forcar or not os.path.exists(arq):
                d = buscar(aba, "%s/%s" % (LICENCIAMENTO, ident))
                codigo_api = d.get("numero")
                if codigo_api and codigo_api != codigo:  # o item da caixa mentiu: vale o do SOL
                    linha["aviso"] = "código do item %s, do licenciamento %s" % (codigo, codigo_api)
                    codigo = linha["codigo"] = codigo_api
                    pasta = os.path.join(PROCESSOS, str(codigo))
                    arq = os.path.join(pasta, "api-%s.json" % ident)
                os.makedirs(pasta, exist_ok=True)
                with open(arq, "w", encoding="utf-8") as fh:
                    json.dump(d, fh, ensure_ascii=False)
                linha["novo"] = True
        else:
            linha["erro"] = "id ou código não achados no item (ver .caixa/item-exemplo.json)"
        resumo.append(linha)
    agora = time.strftime("%Y-%m-%d %H:%M")
    with open(os.path.join(caixa, "caixa.json"), "w", encoding="utf-8") as fh:
        json.dump({"lido_em": agora, "total": len(itens), "itens": resumo}, fh, ensure_ascii=False, indent=1)
    novos = [r["codigo"] for r in resumo if r["novo"]]
    print("%s · caixa: %d · novos baixados: %d%s" % (agora, len(itens), len(novos),
                                                     (" (" + ", ".join(map(str, novos)) + ")") if novos else ""))
    for r in resumo:
        if r.get("erro"):
            print("  ✗", r["erro"])
        if r.get("aviso"):
            print("  !", r["aviso"])
    return 0


def sessao():
    aba = aba_do_sol()
    if aba is None:
        print("Chrome do servidor fora do ar ou sem aba do SOL.")
        return 3
    s = aba.avaliar(SESSAO)
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
