#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
instalar.py — confere e instala no PC (Windows) o que o SSEG precisa, sem o analista abrir o
PowerShell. Usado pelo SSEG.exe; roda sozinho no build do GitHub como teste num Windows limpo.

Programas: Git, Python 3.12, Poppler (pdftotext, pdftoppm) e Claude Code de linha de comando.
Instala pelo winget no modo do usuário (sem administrador; se o pacote não aceitar, tenta o
modo padrão) e o Claude Code pelo instalador oficial (https://claude.ai/install.ps1).

Depois faz os ajustes do CLAUDE.md ("Pré-requisitos no PC") que antes eram à mão:
  - python3.exe ao lado do python.exe (o "python3" do Windows cai no atalho da Store);
  - PATH do usuário com Python, Poppler e Claude Code;
  - no ~/.bashrc do Git Bash, Poppler e Python ANTES do /usr/bin do Git (o pdftotext do Git é
    Xpdf, sem acento) — num bloco marcado que o programa reescreve;
  - PYTHONUTF8=1 (sem isso o verificador lê o pdftotext como cp1252 e quebra).

O login do Claude Code é do analista: `abrir_login()` abre a janela do `claude auth login`.

USO (teste)
  python instalar.py --conferir      # mostra o que achou; sai 1 se faltar algo
  python instalar.py --instalar      # instala o que falta, ajusta e confere
"""

import glob
import json
import os
import re
import shutil
import subprocess
import sys

NO_WINDOWS = os.name == "nt"
SEM_JANELA = 0x08000000 if NO_WINDOWS else 0
NOVA_JANELA = 0x00000010 if NO_WINDOWS else 0

PROGRAMAS = [
    # chave, nome na tela, id do winget (None = instalador próprio)
    ("git", "Git", "Git.Git"),
    ("python", "Python", "Python.Python.3.12"),
    ("poppler", "Poppler", "oschwartz10612.Poppler"),
    ("claude", "Claude Code", None),
]
BAIXAR_A_MAO = {
    "git": "https://git-scm.com/download/win",
    "python": "https://www.python.org/downloads/windows/",
    "poppler": "https://github.com/oschwartz10612/poppler-windows/releases",
    "claude": "PowerShell: irm https://claude.ai/install.ps1 | iex",
}
INICIO_BLOCO, FIM_BLOCO = "# >>> SSEG (programa) >>>", "# <<< SSEG (programa) <<<"


# ------------------------------------------------------------------------- localizar

def _env(nome):
    return os.environ.get(nome) or ""


def _primeiro(*padroes):
    for p in padroes:
        achados = sorted(glob.glob(p, recursive=True), reverse=True)  # versão mais nova primeiro
        if achados:
            return achados[0]
    return None


def localizar(which=shutil.which):
    """{chave: caminho do executável ou None}."""
    loc, pf, casa = _env("LOCALAPPDATA"), _env("ProgramFiles"), os.path.expanduser("~")
    j = os.path.join
    py = next((c for c in (which("python"), which("python3"))
               if c and "WindowsApps" not in c), None)  # atalho da Microsoft Store não é Python
    exe = ".exe" if NO_WINDOWS else ""
    return {
        "git": which("git") or _primeiro(j(loc, "Programs", "Git", "cmd", "git" + exe),
                                         j(pf, "Git", "cmd", "git" + exe)),
        "python": py or _primeiro(j(loc, "Programs", "Python", "Python3*", "python" + exe),
                                  j(pf, "Python3*", "python" + exe)),
        "poppler": which("pdftoppm") or _primeiro(
            j(loc, "Microsoft", "WinGet", "Packages", "oschwartz10612.Poppler*", "**", "bin", "pdftoppm" + exe)),
        "claude": which("claude") or _primeiro(j(casa, ".local", "bin", "claude" + exe)),
    }


# Teste de que o programa RODA, não só existe (2.3.6): comando curto e o que a saída precisa ter.
# pdftoppm -v: o Poppler responde "pdftoppm version"; o Xpdf que vem com o Git não tem pdftoppm.
TESTE = {"git": (["--version"], "git version"), "python": (["-c", "import sys; print(sys.version)"], ""),
         "poppler": (["-v"], "pdftoppm version")}


def roda(chave, exe):
    """None se rodou; senão o motivo, curto."""
    if chave not in TESTE:
        return None
    args, espera = TESTE[chave]
    try:
        p = subprocess.run([exe, *args], capture_output=True, text=True, timeout=20, encoding="utf-8",
                           errors="replace", creationflags=SEM_JANELA, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as e:
        return "não abriu (%s)" % e.__class__.__name__
    saida = p.stdout + p.stderr
    if espera and espera not in saida:
        return "não respondeu como esperado: " + (saida.strip().splitlines() or ["(sem saída)"])[0][:120]
    if not espera and p.returncode:
        return "saiu com erro %d" % p.returncode
    return None


def faltando(achados):
    return [k for k, _n, _i in PROGRAMAS if not achados.get(k)]


# ----------------------------------------------------------------- ajustes de ambiente

def caminho_bash(p):
    """C:\\Users\\x\\bin → /c/Users/x/bin (Git Bash)."""
    m = re.match(r"^([A-Za-z]):[\\/](.*)$", p)
    return ("/%s/%s" % (m.group(1).lower(), m.group(2).replace("\\", "/"))).rstrip("/") if m else p.replace("\\", "/")


def juntar_path(atual, novos):
    """Põe `novos` na frente do PATH, sem repetir o que já está lá."""
    chave = lambda p: p.lower().replace("/", "\\").rstrip("\\")  # noqa: E731 — o winget grava com "/"
    partes = [p for p in atual.split(os.pathsep) if p]
    baixo = [chave(p) for p in partes]
    frente = [n for n in novos if n and chave(n) not in baixo]
    return os.pathsep.join(frente + partes)


def bloco_bashrc(texto, pastas):
    """Reescreve o bloco do programa no ~/.bashrc; o resto do arquivo fica como estava."""
    bloco = "%s\nexport PATH=\"%s:$PATH\"\nexport PYTHONUTF8=1\n%s\n" % (
        INICIO_BLOCO, ":".join(caminho_bash(p) for p in pastas), FIM_BLOCO)
    if INICIO_BLOCO in texto and FIM_BLOCO in texto:
        return re.sub(re.escape(INICIO_BLOCO) + r".*?" + re.escape(FIM_BLOCO) + r"\n?", lambda _m: bloco, texto, flags=re.S)
    return texto + ("" if not texto or texto.endswith("\n") else "\n") + bloco


def _registro_usuario(nome, valor=None):
    """Lê (valor=None) ou grava uma variável de ambiente do usuário (HKCU\\Environment)."""
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as k:
        if valor is None:
            try:
                return winreg.QueryValueEx(k, nome)[0]
            except FileNotFoundError:
                return ""
        winreg.SetValueEx(k, nome, 0, winreg.REG_EXPAND_SZ, valor)


def _avisar_windows():
    """Outros programas abertos depois disso já enxergam o PATH novo."""
    import ctypes
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x1A, 0, "Environment", 0x2, 5000, None)


def ajustar(achados, escrever=print):
    pastas = []
    if achados.get("python"):
        d = os.path.dirname(achados["python"])
        py3 = os.path.join(d, "python3.exe" if NO_WINDOWS else "python3")
        if NO_WINDOWS and not os.path.exists(py3):
            shutil.copy2(achados["python"], py3)
            escrever("✓ python3.exe criado ao lado do python.exe")
        pastas += [d, os.path.join(d, "Scripts")]
    if achados.get("poppler"):
        pastas.append(os.path.dirname(achados["poppler"]))
    if achados.get("claude"):
        pastas.append(os.path.dirname(achados["claude"]))
    if achados.get("git"):
        pastas.append(os.path.dirname(achados["git"]))

    os.environ["PATH"] = juntar_path(os.environ.get("PATH", ""), pastas)
    os.environ["PYTHONUTF8"] = "1"
    if NO_WINDOWS:
        antes = _registro_usuario("Path")
        depois = juntar_path(antes, pastas)
        if depois != antes:
            _registro_usuario("Path", depois)
            escrever("✓ PATH do usuário atualizado")
        if _registro_usuario("PYTHONUTF8") != "1":
            _registro_usuario("PYTHONUTF8", "1")
            escrever("✓ PYTHONUTF8=1")
        _avisar_windows()
    # Git Bash: Poppler e Python antes do /usr/bin do Git
    frente = [p for p in pastas if achados.get("poppler") and p == os.path.dirname(achados["poppler"])]
    frente += [p for p in pastas if achados.get("python") and p == os.path.dirname(achados["python"])]
    if frente:
        rc = os.path.join(os.path.expanduser("~"), ".bashrc")
        try:
            texto = open(rc, encoding="utf-8").read()
        except OSError:
            texto = ""
        novo = bloco_bashrc(texto, frente)
        if novo != texto:
            with open(rc, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(novo)
            escrever("✓ ~/.bashrc: Poppler e Python antes do pdftotext do Git")


# ------------------------------------------------------------------------- instalar

def _rodar(cmd, escrever):
    """Roda mostrando as linhas úteis (sem as barras de progresso do winget)."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=SEM_JANELA)
    for bruto in p.stdout:
        pedacos = [s.strip() for s in bruto.decode("utf-8", "replace").split("\r") if s.strip()]
        linha = pedacos[-1] if pedacos else ""
        if linha and not re.search(r"[█▒]|^[-\\|/]$|^\d+(\.\d+)? [KMG]B / ", linha):
            escrever("   " + linha[:160])
    return p.wait()


def instalar(escrever=print):
    """Instala o que falta e ajusta o ambiente. Devolve o que ainda falta no fim."""
    achados = localizar()
    falta = faltando(achados)
    if not falta:
        escrever("✓ Todos os programas já estão instalados.")
    winget = shutil.which("winget")
    for chave, nome, wid in PROGRAMAS:
        if chave not in falta:
            continue
        escrever("→ Instalando %s…" % nome)
        if wid:
            if not winget:
                escrever("✗ Sem o winget neste PC. Baixe %s em %s" % (nome, BAIXAR_A_MAO[chave]))
                continue
            base = [winget, "install", "-e", "--id", wid, "--silent",
                    "--accept-source-agreements", "--accept-package-agreements", "--disable-interactivity"]
            rc = _rodar(base + ["--scope", "user"], escrever)
            if rc:
                escrever("   modo do usuário não aceito; tentando o modo padrão (pode pedir confirmação do Windows)")
                rc = _rodar(base, escrever)
        else:
            rc = _rodar(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                         "irm https://claude.ai/install.ps1 | iex"], escrever)
        escrever("✓ %s instalado" % nome if rc == 0 else "✗ %s não instalou (código %s)" % (nome, rc))
    achados = localizar()
    ajustar(achados, escrever)
    resto = faltando(achados)
    for k in resto:
        escrever("✗ Ainda falta %s. Baixar à mão: %s" % (dict((c, n) for c, n, _ in PROGRAMAS)[k], BAIXAR_A_MAO[k]))
    return resto


# ---------------------------------------------------------------------- Claude Code

def claude_logado(claude):
    try:
        p = subprocess.run([claude, "auth", "status"], capture_output=True, text=True, timeout=30,
                           encoding="utf-8", errors="replace", creationflags=SEM_JANELA)
        return bool(json.loads(p.stdout).get("loggedIn"))
    except (OSError, ValueError, subprocess.SubprocessError):
        return False


def abrir_login(claude):
    """Janela própria: o analista vê o link e entra pelo navegador."""
    subprocess.Popen([claude, "auth", "login"], creationflags=NOVA_JANELA)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # console do Windows é cp1252: "✓" quebraria
    if "--instalar" in sys.argv:
        resto = instalar()
    else:
        resto = faltando(localizar())
    print(json.dumps(localizar(), indent=2, ensure_ascii=False))
    sys.exit(1 if resto else 0)
