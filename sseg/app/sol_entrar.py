# -*- coding: utf-8 -*-
"""
sol_entrar.py — instala o "SOL Entrar" (sseg/ferramentas/sol-entrar/) pelo SSEG.exe.

Entrar no SOL sem teclado, com a matrícula e a senha que o Chrome já guarda: o atalho "Abrir SOL"
da Área de Trabalho abre o login e dá o clique que libera o preenchimento; o script do
Tampermonkey preenche a organização e clica em Entrar depois de 5 s (cancelável). A senha não
passa por aqui nem fica em arquivo nenhum. Opcional, para quem clicar no botão (autorizado pelo
Átila em 12/10/2026).

O programa não instala extensão do Chrome: abre a página do Tampermonkey, copia o script e
mostra os passos.
"""

import os
import shutil
import subprocess
import sys

ARQUIVOS = ["abrir-sol.ps1", "Abrir SOL.bat"]
SCRIPT = "sol-entrar.user.js"
TAMPERMONKEY_URL = "https://chromewebstore.google.com/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo"
PASSOS = [
    "Na página que abriu no Chrome: \"Usar no Chrome\" → \"Adicionar extensão\".",
    "Em chrome://extensions: ligue o \"Modo do desenvolvedor\" (canto de cima, à direita). Depois, "
    "em \"Detalhes\" do Tampermonkey, ligue \"Permitir scripts de usuário\".",
    "Ícone do Tampermonkey (quebra-cabeça na barra) → \"Criar novo script\" → apague o que vier, "
    "cole (o script já está copiado: botão direito → Colar) e salve em Arquivo → Salvar.",
]
SEM_JANELA = 0x08000000 if os.name == "nt" else 0


def origem():
    """Pasta com os arquivos: dentro do .exe (add-data) ou no clone, rodando pelo .py."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, "sol-entrar")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ferramentas", "sol-entrar")


def pasta_destino():
    return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "SSEG", "sol-entrar")


def chrome():
    for v in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        c = os.path.join(os.environ.get(v, ""), "Google", "Chrome", "Application", "chrome.exe")
        if os.path.isfile(c):
            return c
    return None


def _ps(comando):
    p = subprocess.run(["powershell", "-NoProfile", "-Command", comando], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", creationflags=SEM_JANELA, timeout=60)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout).strip()[-400:])
    return p.stdout.strip()


def area_de_trabalho():
    """A Área de Trabalho de verdade (com OneDrive ela não fica em ~/Desktop)."""
    if os.name != "nt":
        return os.path.join(os.path.expanduser("~"), "Desktop")
    return _ps("[Console]::OutputEncoding=[Text.Encoding]::UTF8; [Environment]::GetFolderPath('Desktop')")


def atalho():
    return os.path.join(area_de_trabalho(), "Abrir SOL.lnk")


def instalar_atalho():
    """Copia o .ps1 e o .bat para a pasta do usuário e cria "Abrir SOL" na Área de Trabalho
    (ícone do Chrome, janela minimizada). Devolve o caminho do atalho."""
    if not chrome():
        raise RuntimeError("Chrome não encontrado neste PC. O SOL Entrar usa a senha salva no Chrome.")
    destino = pasta_destino()
    os.makedirs(destino, exist_ok=True)
    for nome in ARQUIVOS:
        shutil.copyfile(os.path.join(origem(), nome), os.path.join(destino, nome))
    lnk = atalho()
    q = lambda s: s.replace("'", "''")  # noqa: E731
    _ps("$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%s'); $s.TargetPath = '%s'; "
        "$s.WorkingDirectory = '%s'; $s.WindowStyle = 7; $s.IconLocation = '%s,0'; "
        "$s.Description = 'Abre o SOL e entra com a senha salva no Chrome'; $s.Save()"
        % (q(lnk), q(os.path.join(destino, "Abrir SOL.bat")), q(destino), q(chrome())))
    if not os.path.isfile(lnk):
        raise RuntimeError("O atalho não foi criado em " + lnk)
    return lnk


def conferir():
    """Linhas para o quadro: o atalho existe? e o que depende do analista."""
    try:
        ok = os.path.isfile(atalho()) and all(os.path.isfile(os.path.join(pasta_destino(), n)) for n in ARQUIVOS)
    except (OSError, RuntimeError, subprocess.SubprocessError):
        ok = False
    return [
        ("✓ " if ok else "✗ ") + "Atalho \"Abrir SOL\" na Área de Trabalho" + ("" if ok else " (não encontrado)"),
        "  A senha precisa estar salva no Chrome (entre uma vez digitando e salve). No PC do trabalho, "
        "o Chrome logado na mesma conta Google, com a sincronização de senhas ligada.",
        "  O script do Tampermonkey fica no Chrome: o programa não confere se ele está instalado.",
    ]


def script_js():
    with open(os.path.join(origem(), SCRIPT), encoding="utf-8-sig") as fh:
        return fh.read()


def abrir_tampermonkey():
    if os.environ.get("SSEG_TESTE_FOTO"):  # foto do build: não abre o Chrome por cima da janela
        return
    c = chrome()
    if c:
        subprocess.Popen([c, TAMPERMONKEY_URL])
    else:
        import webbrowser
        webbrowser.open(TAMPERMONKEY_URL)
