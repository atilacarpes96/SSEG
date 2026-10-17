# -*- coding: utf-8 -*-
"""
sol_aba.py — os botões "SOL: análise" e "SOL: licenciamento" levam à aba do SOL em que o analista
já entrou (2.3.17), sem abrir aba nova.

Por quê: o SOL guarda o login no sessionStorage, que é de cada aba. Aba nova = tela de login, por
mais certo que seja o link. Então o programa acha no Chrome do analista a aba do SOL que está
logada, troca só o que vem depois do "#" (o SOL muda de tela sem recarregar, a sessão continua) e
traz a aba para a frente.

Caminho: a depuração remota que o analista já ligou para o Chrome DevTools MCP
(chrome://inspect/#remote-debugging). O endereço sai do DevToolsActivePort da pasta do perfil
(chrome_devtools.porta_depuracao). O Chrome pede "Permitir" a cada conexão nova: a conexão fica
aberta enquanto o programa roda, para pedir uma vez só.

O que NÃO faz: não digita senha, não clica, não lê nada da página além de "está logada?".
Sem aba logada (ou sem depuração), quem chama abre o link do jeito antigo.
"""

import base64
import json
import os
import socket
import struct
import threading

import chrome_devtools

SOL = "solcbm.rs.gov.br/solcbm/adm"

LOGADA = r"""(() => {
  const t = sessionStorage.getItem("access_token") || localStorage.getItem("access_token");
  try { return !!t && JSON.parse(atob(t.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))).exp > Date.now() / 1000; }
  catch (e) { return false; }
})()"""


class Conexao:
    """WebSocket mínimo (biblioteca padrão) com o endpoint de navegador do Chrome."""

    def __init__(self, porta, caminho, timeout=90):
        self.s = socket.create_connection(("127.0.0.1", porta), timeout=timeout)  # o "Permitir" segura o aperto de mão
        chave = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(("GET %s HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % (caminho, porta, chave)).encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            parte = self.s.recv(4096)
            if not parte:
                raise OSError("o Chrome fechou a conexão (Permitir recusado?)")
            buf += parte
        if b" 101 " not in buf.split(b"\r\n", 1)[0]:
            raise OSError("o Chrome recusou a conexão: " + buf.split(b"\r\n", 1)[0].decode("latin-1"))
        self.buf = buf.split(b"\r\n\r\n", 1)[1]
        self.n = 0
        self.s.settimeout(20)

    def _ler(self, n):
        while len(self.buf) < n:
            parte = self.s.recv(65536)
            if not parte:
                raise OSError("conexão com o Chrome caiu")
            self.buf += parte
        r, self.buf = self.buf[:n], self.buf[n:]
        return r

    def _enviar(self, txt):
        d = txt.encode()
        m = os.urandom(4)
        n = len(d)
        cab = bytes([0x81, 0x80 | n]) if n < 126 else (bytes([0x81, 0x80 | 126]) + struct.pack(">H", n) if n < 65536
                                                       else bytes([0x81, 0x80 | 127]) + struct.pack(">Q", n))
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
            if op == 8:
                raise OSError("o Chrome encerrou a conexão")
            if op in (0, 1):
                partes.append(dado)
                if b1 & 0x80:
                    return json.loads(b"".join(partes).decode())

    def pedir(self, metodo, params=None, sessao=None):
        self.n += 1
        m = {"id": self.n, "method": metodo, "params": params or {}}
        if sessao:
            m["sessionId"] = sessao
        self._enviar(json.dumps(m))
        while True:  # eventos no meio do caminho são ignorados
            r = self._receber()
            if r.get("id") == self.n:
                if "error" in r:
                    raise RuntimeError(r["error"].get("message", "erro do Chrome"))
                return r.get("result", {})

    def fechar(self):
        try:
            self.s.close()
        except OSError:
            pass


_CONEXAO = None
_TRAVA = threading.Lock()


def _caminho():
    """Caminho do WebSocket do navegador: 2ª linha do DevToolsActivePort."""
    with open(os.path.join(chrome_devtools.pasta_perfil(), "DevToolsActivePort"), encoding="utf-8") as fh:
        linhas = fh.read().split()
    return linhas[1] if len(linhas) > 1 else "/devtools/browser"


def _conectar():
    global _CONEXAO
    if _CONEXAO is None:
        porta, atende = chrome_devtools.porta_depuracao()
        if not atende:
            raise OSError("depuração remota desligada no Chrome")
        _CONEXAO = Conexao(porta, _caminho())
    return _CONEXAO


def _ir(c, url):
    """Acha a aba do SOL logada, troca o "#" e a traz para a frente. (True, msg) ou (False, motivo)."""
    destino = url.split("#", 1)[1] if "#" in url else "/"
    abas = [t for t in c.pedir("Target.getTargets")["targetInfos"] if t.get("type") == "page" and SOL in t.get("url", "")]
    if not abas:
        return False, "nenhuma aba do SOL aberta no Chrome"
    for t in abas:
        sessao = c.pedir("Target.attachToTarget", {"targetId": t["targetId"], "flatten": True})["sessionId"]
        try:
            logada = c.pedir("Runtime.evaluate", {"expression": LOGADA, "returnByValue": True}, sessao)["result"].get("value")
            if not logada:
                continue
            c.pedir("Runtime.evaluate", {"expression": "location.hash = %s" % json.dumps(destino)}, sessao)
            c.pedir("Target.activateTarget", {"targetId": t["targetId"]})
            c.pedir("Page.bringToFront", {}, sessao)
            return True, "aberto na aba do SOL em que você já entrou"
        finally:
            try:
                c.pedir("Target.detachFromTarget", {"sessionId": sessao})
            except (OSError, RuntimeError):
                pass
    return False, "a aba do SOL aberta não está logada"


def abrir(url):
    """(True, msg) se levou a aba logada ao endereço; (False, motivo) para quem chama abrir do jeito antigo."""
    global _CONEXAO
    with _TRAVA:
        for tentativa in (1, 2):  # a conexão guardada pode ter caído (Chrome fechado e aberto de novo)
            try:
                return _ir(_conectar(), url)
            except (OSError, RuntimeError, ValueError, KeyError) as e:
                if _CONEXAO:
                    _CONEXAO.fechar()
                _CONEXAO = None
                if tentativa == 2:
                    return False, str(e)
