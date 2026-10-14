# -*- coding: utf-8 -*-
"""
espelho.py — a mesma janela do SSEG.exe no navegador do celular (plano 2.4, "Espelho no celular").

O PC do quartel continua fazendo todo o trabalho; o celular é só mais uma tela do mesmo programa.
O SSEG.exe serve web/ em 127.0.0.1 (nunca na rede do quartel) e o celular chega pelo Tunel abaixo
(SSH de saída até o servidor, que publica só na rede do Tailscale). Cada chamada do celular roda o mesmo método do Api da janela, e o que o Python empurra
para a janela (SSEG.chat, SSEG.log) vai também, por SSE, para quem estiver aberto no navegador.

Só entra quem abriu o endereço com a chave gerada no PC (vira cookie). Os POST exigem o
cabeçalho X-SSEG, que um site de fora não consegue mandar sem pré-verificação de CORS.
"""

import json
import os
import queue
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORTA = 8765
# Métodos que só fazem sentido na janela do PC (diálogo nativo, print da tela, fechar o programa).
SO_NA_JANELA = {"escolher_pasta", "print_janela", "atualizar_programa", "espelho_ligar"}
TIPOS = {".html": "text/html; charset=utf-8", ".png": "image/png", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".ico": "image/x-icon"}
COOKIE = "sseg_chave"


class Espelho:
    def __init__(self, api, pasta_web, chave, porta=PORTA, host="127.0.0.1"):
        self.api, self.pasta_web, self.chave, self.porta, self.host = api, pasta_web, chave, porta, host
        self._filas = set()
        self._trava = threading.Lock()
        self._srv = None

    # ------------------------------------------------------------ ciclo
    @property
    def ligado(self):
        return self._srv is not None

    def url(self):
        return "http://%s:%d/?chave=%s" % (self.host, self.porta, self.chave)

    def ligar(self):
        if self._srv:
            return
        esp = self

        class Tratador(_Tratador):
            espelho = esp
        self._srv = ThreadingHTTPServer((self.host, self.porta), Tratador)
        self._srv.daemon_threads = True
        threading.Thread(target=self._srv.serve_forever, daemon=True).start()

    def desligar(self):
        srv, self._srv = self._srv, None
        if srv:
            srv.shutdown()
            srv.server_close()
        with self._trava:
            for q in self._filas:
                q.put(None)

    # ------------------------------------------------------------ eventos para as telas do navegador
    def emitir(self, funcao, args):
        msg = json.dumps({"f": funcao, "a": list(args)}, ensure_ascii=False, default=str)
        with self._trava:
            for q in self._filas:
                q.put(msg)

    def _assinar(self):
        q = queue.Queue()
        with self._trava:
            self._filas.add(q)
        return q

    def _sair(self, q):
        with self._trava:
            self._filas.discard(q)

    @property
    def telas(self):
        return len(self._filas)


class Tunel:
    """Fase 2: o caminho até o celular. O PC abre uma conexão SSH de SAÍDA para o servidor (a mesma do
    sincronizar processos) e pede que a porta 8765 de lá, só em 127.0.0.1, venha para o espelho daqui.
    No servidor, o `tailscale serve` publica essa porta só na rede privada do Átila (iPhone + servidor).
    Nenhuma porta se abre no PC nem na rede do quartel. Caiu, tenta de novo a cada 20 s."""

    def __init__(self, porta_local, porta_servidor=PORTA, host="sseg-servidor", aolog=None, sem_janela=0):
        self.porta_local, self.porta_servidor, self.host = porta_local, porta_servidor, host
        self.aolog, self.sem_janela = aolog or (lambda *_: None), sem_janela
        self._proc = None
        self._parar = threading.Event()
        self.estado = "desligado"
        self.erro = ""

    def comando(self):
        return ["ssh", "-N", "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes", "-o", "ServerAliveInterval=20",
                "-o", "ServerAliveCountMax=3", "-R", "127.0.0.1:%d:127.0.0.1:%d" % (self.porta_servidor, self.porta_local),
                self.host]

    def ligar(self):
        if self.estado != "desligado":
            return
        self._parar.clear()
        self.estado = "conectando"
        threading.Thread(target=self._manter, daemon=True).start()

    def _manter(self):
        while not self._parar.is_set():
            self.estado = "conectando"
            try:
                self._proc = subprocess.Popen(self.comando(), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                              stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                                              creationflags=self.sem_janela)
            except OSError as e:
                self.estado, self.erro = "erro", "ssh não encontrado (%s)" % e
                self.aolog("✗ Túnel do celular: " + self.erro)
                return
            # sem erro em 4 s, a porta do servidor está presa a este PC
            try:
                self._proc.wait(timeout=4)
            except subprocess.TimeoutExpired:
                self.estado, self.erro = "ativo", ""
                self.aolog("Túnel do celular ativo (servidor → este PC).")
                self._proc.wait()
            if self._parar.is_set():
                break
            err = (self._proc.stderr.read() if self._proc.stderr else "").strip()
            self.erro = err.splitlines()[-1][:200] if err else "conexão caiu"
            if "remote port forwarding failed" in err:
                self.erro = "a porta %d do servidor está presa a outro PC (outro SSEG.exe com o celular ligado)" % self.porta_servidor
            self.estado = "caiu"
            self.aolog("✗ Túnel do celular: %s. Tento de novo em 20 s." % self.erro)
            self._parar.wait(20)
        self.estado = "desligado"

    def desligar(self):
        self._parar.set()
        p = self._proc
        if p and p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        self.estado = "desligado"


class _Tratador(BaseHTTPRequestHandler):
    espelho = None
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # sem barulho no console do .exe
        pass

    # ------------------------------------------------------------ apoio
    def _cookie_ok(self):
        for parte in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = parte.strip().partition("=")
            if k == COOKIE and v == self.espelho.chave:
                return True
        return False

    def _enviar(self, codigo, corpo, tipo="application/json; charset=utf-8", extra=()):
        dados = corpo if isinstance(corpo, bytes) else corpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Cache-Control", "no-store")
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(dados)

    def _negar(self):
        self._enviar(403, "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>"
                          "<p style='font:16px system-ui;padding:24px'>SSEG: abra pelo endereço com a chave "
                          "(no PC: Configuração → Usar pelo celular).</p>", "text/html; charset=utf-8")

    # ------------------------------------------------------------ GET: página, arquivos e eventos
    def do_GET(self):
        u = urlparse(self.path)
        chave = parse_qs(u.query).get("chave", [""])[0]
        if chave:
            if chave != self.espelho.chave:
                return self._negar()
            return self._enviar(303, b"", extra=[("Location", "/"), (
                "Set-Cookie", "%s=%s; Path=/; HttpOnly; SameSite=Strict; Max-Age=31536000" % (COOKIE, chave))])
        if not self._cookie_ok():
            return self._negar()
        if u.path == "/eventos":
            return self._eventos()
        nome = "index.html" if u.path in ("/", "") else u.path.lstrip("/")
        caminho = os.path.normpath(os.path.join(self.espelho.pasta_web, nome))
        if not caminho.startswith(os.path.normpath(self.espelho.pasta_web) + os.sep) or not os.path.isfile(caminho):
            return self._enviar(404, '{"erro": "não encontrado"}')
        with open(caminho, "rb") as fh:
            dados = fh.read()
        if nome == "index.html":  # a marca que põe a página em modo navegador (ver ESPELHO no index.html)
            dados = dados.replace(b"<head>", b'<head>\n<meta name="sseg-espelho" content="1">', 1)
        self._enviar(200, dados, TIPOS.get(os.path.splitext(caminho)[1].lower(), "application/octet-stream"))

    def _eventos(self):
        q = self.espelho._assinar()
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            self.wfile.write(b": ok\n\n")
            self.wfile.flush()
            while True:
                try:
                    msg = q.get(timeout=15)
                except queue.Empty:
                    msg = ""
                if msg is None:
                    break
                self.wfile.write(("data: %s\n\n" % msg).encode("utf-8") if msg else b": ping\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            self.espelho._sair(q)
            self.close_connection = True

    # ------------------------------------------------------------ POST /api/<método>: o mesmo Api da janela
    def do_POST(self):
        u = urlparse(self.path)
        # lê o corpo ANTES de qualquer resposta: recusado sem ler, ele sobrava na conexão (keep-alive) e o
        # próximo pedido chegava como "[]GET ..." (13/10/2026)
        try:
            corpo = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        except ValueError:
            corpo = b""
        if not self._cookie_ok() or self.headers.get("X-SSEG") != "1":
            return self._enviar(403, '{"erro": "sem acesso"}')
        nome = u.path[len("/api/"):] if u.path.startswith("/api/") else ""
        fn = getattr(self.espelho.api, nome, None) if nome.isidentifier() and not nome.startswith("_") else None
        if not callable(fn) or nome in SO_NA_JANELA:
            return self._enviar(404, json.dumps({"erro": "Isto só funciona na janela do PC."}, ensure_ascii=False))
        try:
            args = json.loads(corpo or b"[]")
            r = fn(*args) if isinstance(args, list) else fn(**args)
            self._enviar(200, json.dumps({"r": r}, ensure_ascii=False, default=str))
        except Exception as e:  # o erro volta para a tela, como na janela
            self._enviar(500, json.dumps({"erro": str(e) or e.__class__.__name__}, ensure_ascii=False))
