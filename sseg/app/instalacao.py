# -*- coding: utf-8 -*-
"""
instalacao.py — o SSEG.exe baixado vira programa instalado (2.2.0).

O analista baixa um arquivo só (SSEG.exe, do release) e abre de onde estiver (Downloads). A tela
"Instalação" do programa faz o resto, na ordem:
  1. copia o próprio .exe para %LOCALAPPDATA%\\Programs\\SSEG\\SSEG.exe (sem administrador), cria
     os atalhos "SSEG" no Menu Iniciar e na Área de Trabalho e reabre de lá;
  2. Git, Python, Poppler e Claude Code (instalar.py, pelo winget no modo do usuário);
  3. login do Claude Code (a janela é do analista);
  4. pastas: clone do SSEG e pasta dos processos (sseg_app.preparar_pastas);
  5. quem é você (nome da escala);
  6. servidor (opcional): pedir acesso (acesso.py).
A "Atualizar o programa" troca o .exe onde ele estiver, então continua valendo depois de instalado.
"""

import os
import shutil
import subprocess
import sys

SEM_JANELA = 0x08000000 if os.name == "nt" else 0


def pasta_programa():
    return os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "Programs", "SSEG")


def exe_instalado():
    return os.path.join(pasta_programa(), "SSEG.exe")


def _ps(comando):
    p = subprocess.run(["powershell", "-NoProfile", "-Command", comando], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60, creationflags=SEM_JANELA, stdin=subprocess.DEVNULL)
    return (p.stdout or "").strip()


def pastas_de_atalho():
    """Área de Trabalho de verdade (com OneDrive não é ~/Desktop) e o Menu Iniciar do usuário."""
    mesa = _ps("[Console]::OutputEncoding=[Text.Encoding]::UTF8; [Environment]::GetFolderPath('Desktop')") \
        or os.path.join(os.path.expanduser("~"), "Desktop")
    menu = os.path.join(os.environ.get("APPDATA") or "", "Microsoft", "Windows", "Start Menu", "Programs")
    return mesa, menu


def atalhos():
    return [os.path.join(p, "SSEG.lnk") for p in pastas_de_atalho()]


def rodando_instalado():
    """O .exe aberto é o da pasta de programas? Rodando pelo .py, conta como instalado (não há o que copiar)."""
    if not getattr(sys, "frozen", False):
        return True
    return os.path.normcase(os.path.abspath(sys.executable)) == os.path.normcase(exe_instalado())


def estado():
    mesa, menu = atalhos()
    return {"instalado": rodando_instalado() or os.path.isfile(exe_instalado()), "aberto_daqui": rodando_instalado(),
            "pasta": pasta_programa(), "atalho_mesa": os.path.isfile(mesa), "atalho_menu": os.path.isfile(menu),
            "frozen": bool(getattr(sys, "frozen", False))}


def instalar(escrever=print):
    """Copia o .exe e cria os atalhos. Devolve o caminho do .exe instalado (quem chama reabre de lá)."""
    if not getattr(sys, "frozen", False):
        escrever("Rodando pelo .py (desenvolvimento): nada a copiar.")
        return ""
    destino = exe_instalado()
    os.makedirs(pasta_programa(), exist_ok=True)
    if not rodando_instalado():
        try:
            shutil.copyfile(sys.executable, destino + ".novo")
            os.replace(destino + ".novo", destino)
        except PermissionError:
            raise RuntimeError("O SSEG instalado está aberto em outra janela. Feche-o (Fechar tudo) e tente de novo.")
        escrever("✓ Programa em " + destino)
    q = lambda s: s.replace("'", "''")  # noqa: E731
    for lnk in atalhos():
        os.makedirs(os.path.dirname(lnk), exist_ok=True)
        _ps("$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%s'); $s.TargetPath = '%s'; "
            "$s.WorkingDirectory = '%s'; $s.IconLocation = '%s,0'; $s.Description = 'SSEG — análise de PPCI'; $s.Save()"
            % (q(lnk), q(destino), q(pasta_programa()), q(destino)))
        escrever(("✓ Atalho " if os.path.isfile(lnk) else "✗ Atalho não criado: ") + lnk)
    return destino


def reabrir_instalado(ambiente):
    """Abre o .exe instalado (com o ambiente limpo do PyInstaller) e devolve; quem chama fecha esta janela."""
    subprocess.Popen([exe_instalado(), "--instalacao"], cwd=pasta_programa(), env=ambiente,
                     creationflags=0x00000008)  # DETACHED_PROCESS

