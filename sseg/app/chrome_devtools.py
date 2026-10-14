# -*- coding: utf-8 -*-
"""
chrome_devtools.py — "Chrome para o Claude" do SSEG.exe: registra o Chrome DevTools MCP (Google) no
Claude Code e mostra, item por item, se o caminho até o Chrome aberto do analista está funcionando.

Para que serve: o Claude ler e operar uma página já aberta e logada (SOL, por exemplo) pelo DOM, console
e rede, sem depender de print. O programa nunca digita senha: quem entra no SOL é o analista.

Como o Chrome aceita isso (Chrome 144 ou mais novo): em chrome://inspect/#remote-debugging o analista
liga a depuração remota; a cada conexão nova o Chrome pergunta "Permitir". O servidor MCP registrado com
`--autoConnect` acha o Chrome pelo arquivo DevToolsActivePort da pasta do perfil.

Cuidado que a tela repete: com isso ligado, o Claude enxerga TODAS as janelas do perfil do Chrome.
"""

import json
import os
import re
import socket
import subprocess
import time

SEM_JANELA = 0x08000000 if os.name == "nt" else 0
NOME = "chrome-devtools-live"
PACOTE = ["npx", "-y", "chrome-devtools-mcp@latest", "--autoConnect"]
CHROME_MINIMO = 144
NODE_MINIMO = (20, 19)
INSPECT = "chrome://inspect/#remote-debugging"


def _rodar(cmd, timeout=30):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout, creationflags=SEM_JANELA, stdin=subprocess.DEVNULL)


def pasta_perfil():
    return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Google", "Chrome", "User Data")


def chrome_exe():
    for v in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        c = os.path.join(os.environ.get(v, ""), "Google", "Chrome", "Application", "chrome.exe")
        if os.path.isfile(c):
            return c
    return None


def versao_chrome():
    """Número principal do Chrome (ex.: 147), lido do registro; None se não achar."""
    if os.name != "nt":
        return None
    try:
        import winreg
        for raiz in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(raiz, r"Software\Google\Chrome\BLBeacon") as k:
                    return int(winreg.QueryValueEx(k, "version")[0].split(".")[0])
            except OSError:
                continue
    except (ImportError, ValueError):
        pass
    return None


def versao_node():
    """(maior, menor) do Node, ou None se não estiver instalado."""
    try:
        p = _rodar(["node", "-v"], 15)
        m = re.match(r"v(\d+)\.(\d+)", p.stdout.strip())
        return (int(m.group(1)), int(m.group(2))) if p.returncode == 0 and m else None
    except (OSError, subprocess.SubprocessError):
        return None


def registrado():
    """Lê ~/.claude.json (escopo de usuário): devolve a entrada do servidor ou None. Sem subprocesso."""
    try:
        with open(os.path.join(os.path.expanduser("~"), ".claude.json"), encoding="utf-8") as fh:
            return (json.load(fh).get("mcpServers") or {}).get(NOME)
    except (OSError, ValueError):
        return None


def porta_depuracao():
    """Porta que o Chrome publicou no DevToolsActivePort e se ela responde. (porta|None, atende)."""
    try:
        with open(os.path.join(pasta_perfil(), "DevToolsActivePort"), encoding="utf-8") as fh:
            porta = int(fh.readline().strip())
    except (OSError, ValueError):
        return None, False
    try:
        with socket.create_connection(("127.0.0.1", porta), timeout=1.5):
            return porta, True
    except OSError:
        return porta, False  # arquivo velho: o Chrome foi fechado ou a depuração foi desligada


def chrome_aberto():
    if os.name != "nt":
        return False
    try:
        return "chrome.exe" in _rodar(["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/NH"], 15).stdout.lower()
    except (OSError, subprocess.SubprocessError):
        return False


def conferir():
    """Lista de passos: [{id, ok, titulo, detalhe}]. Rápida (sem abrir nada no Chrome)."""
    passos = []
    n = versao_node()
    passos.append({"id": "node", "ok": bool(n and n >= NODE_MINIMO),
                   "titulo": "Node.js" + (" %d.%d" % n if n else ""),
                   "detalhe": "" if n and n >= NODE_MINIMO else
                   "Instale o Node.js LTS (nodejs.org). O servidor do Chrome DevTools pede a versão %d.%d ou mais nova." % NODE_MINIMO})
    v = versao_chrome()
    passos.append({"id": "chrome", "ok": bool(v and v >= CHROME_MINIMO),
                   "titulo": "Chrome" + (" %d" % v if v else " não encontrado"),
                   "detalhe": "" if v and v >= CHROME_MINIMO else
                   "Precisa do Chrome %d ou mais novo (menu ⋮ → Ajuda → Sobre o Google Chrome atualiza)." % CHROME_MINIMO})
    reg = registrado()
    certo = bool(reg) and "--autoConnect" in (reg.get("args") or [])
    passos.append({"id": "registro", "ok": certo,
                   "titulo": "Registrado no Claude Code" if certo else "Não registrado no Claude Code",
                   "detalhe": "" if certo else ("O registro existe mas sem --autoConnect: clique em Registrar para refazer."
                                                if reg else "Clique em Registrar.")})
    porta, atende = porta_depuracao()
    aberto = chrome_aberto()
    if atende:
        det, titulo = "", "Depuração remota ligada no Chrome (porta %d)" % porta
    elif not aberto:
        det, titulo = "O Chrome está fechado. Abra o Chrome (com o SOL, por exemplo) e ligue a depuração.", "Chrome fechado"
    else:
        det, titulo = ("Clique em \"Abrir chrome://inspect\", ligue a depuração remota e deixe essa aba do Chrome aberta."
                       "\nAs telas do Chrome ficam acessíveis ao Claude enquanto estiver ligado."), "Depuração remota desligada"
    passos.append({"id": "depuracao", "ok": atende, "titulo": titulo, "detalhe": det})
    return passos


def registrar(claude):
    """claude mcp add (escopo de usuário). Refaz se já existir. Devolve o texto de saída."""
    if not claude:
        raise RuntimeError("Instale o Claude Code antes (\"Instalar o que falta\").")
    if registrado() is not None:
        _rodar([claude, "mcp", "remove", NOME, "--scope", "user"], 60)
    p = _rodar([claude, "mcp", "add", NOME, "--scope", "user", "--"] + PACOTE, 90)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout).strip()[-400:] or "claude mcp add falhou.")
    if registrado() is None:
        raise RuntimeError("O comando rodou, mas o registro não apareceu em ~/.claude.json.")
    return (p.stdout or "").strip()


def remover(claude):
    if not claude:
        raise RuntimeError("Claude Code não encontrado.")
    if registrado() is None:
        return "Nada a remover."
    p = _rodar([claude, "mcp", "remove", NOME, "--scope", "user"], 60)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout).strip()[-400:])
    return "Registro removido."


def abrir_inspect():
    """Abre chrome://inspect/#remote-debugging no Chrome (o Chrome não deixa outro programa ligar isso)."""
    c = chrome_exe()
    if not c:
        raise RuntimeError("Chrome não encontrado neste PC.")
    if os.environ.get("SSEG_TESTE_FOTO"):
        return
    subprocess.Popen([c, INSPECT], creationflags=SEM_JANELA)


def testar(timeout=75):
    """Teste de ponta a ponta: sobe o servidor MCP como o Claude faria, pede a lista de abas e conta.
    O Chrome mostra o "Permitir" nesse momento; o analista tem de clicar. Não lê título nem endereço de aba.
    Devolve (ok, mensagem)."""
    porta, atende = porta_depuracao()
    if not atende:
        return False, "A depuração remota não está ligada no Chrome (veja o último item da lista)."
    try:
        p = subprocess.Popen(PACOTE, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             text=True, encoding="utf-8", errors="replace", creationflags=SEM_JANELA, shell=(os.name == "nt"))
    except OSError as e:
        return False, "Não consegui iniciar o servidor: %s" % e
    import queue
    import threading
    fila = queue.Queue()
    threading.Thread(target=lambda: [fila.put(l) for l in p.stdout], daemon=True).start()
    contador = [0]

    def pedir(metodo, params=None, espera=timeout):
        contador[0] += 1
        i = contador[0]
        p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": i, "method": metodo, "params": params or {}}) + "\n")
        p.stdin.flush()
        fim = time.time() + espera
        while time.time() < fim:
            try:
                m = json.loads(fila.get(timeout=1))
            except queue.Empty:
                continue
            except ValueError:
                continue
            if m.get("id") == i:
                return m
        return None

    try:
        r = pedir("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                 "clientInfo": {"name": "sseg", "version": "1"}}, 60)
        if not r:
            return False, "O servidor do Chrome DevTools não respondeu (Node e internet para baixar o pacote?)."
        p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        p.stdin.flush()
        r = pedir("tools/call", {"name": "list_pages", "arguments": {}})
        if not r:
            return False, "Sem resposta do Chrome em %d s. Se apareceu \"Permitir\" no Chrome, clique e teste de novo." % timeout
        if r.get("error") or r.get("result", {}).get("isError"):
            txt = json.dumps(r.get("error") or r["result"], ensure_ascii=False)[:300]
            return False, "O Chrome recusou ou deu erro: " + txt
        texto = "".join(c.get("text", "") for c in r["result"].get("content", []))
        n = len(re.findall(r"^\d+:", texto, re.M))
        return True, "Funcionando: o Claude enxerga %d aba(s) do seu Chrome." % n
    finally:
        try:
            p.kill()
        except OSError:
            pass
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True, creationflags=SEM_JANELA)
