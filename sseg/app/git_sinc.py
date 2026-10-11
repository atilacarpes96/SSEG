# -*- coding: utf-8 -*-
"""
git_sinc.py — o botão "Sincronizar com o GitHub" do SSEG.exe (item 3 do PLANO.md).

Um botão só, com conferência antes: o que mudou, o que fica fora por ser dado de processo
(as mesmas travas do pre-commit, por `sseg_hooks.py conferir`) e a mensagem do commit.
Ordem: fetch → pull --ff-only (se o GitHub estiver à frente) → add (sem -f; o barrado sai) →
commit (passa pelo pre-commit) → push. Nunca --force. Parou em qualquer passo: explica e não
desfaz o trabalho do analista.
"""

import json
import os
import subprocess

SEM_JANELA = 0x08000000 if os.name == "nt" else 0


def _git(clone, *args, timeout=180):
    p = subprocess.run(["git", "-C", clone, *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, creationflags=SEM_JANELA, stdin=subprocess.DEVNULL)
    return p.returncode, (p.stdout + p.stderr).strip()


def _status(clone):
    """[(código, arquivo)] do que mudou, inclusive arquivo novo (o .gitignore já tira o que é ignorado)."""
    _, out = _git(clone, "-c", "core.quotepath=off", "status", "--porcelain", "-uall")
    itens = []
    for linha in out.splitlines():
        if len(linha) > 3:
            arq = linha[3:].split(" -> ")[-1].strip('"')
            itens.append((linha[:2].strip() or "?", arq))
    return itens


def conferir(clone, python):
    """Tudo o que a tela de conferência mostra."""
    itens = _status(clone)
    barrados = {}
    gancho = os.path.join(clone, ".claude", "hooks", "sseg_hooks.py")
    if itens and python and os.path.exists(gancho):
        p = subprocess.run([python, gancho, "conferir"], input=json.dumps([a for _, a in itens]),
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
                           creationflags=SEM_JANELA, env={**os.environ, "CLAUDE_PROJECT_DIR": clone, "PYTHONUTF8": "1"})
        try:
            barrados = json.loads(p.stdout or "{}")
        except ValueError:
            barrados = {}
    _git(clone, "fetch", "--quiet", "origin")
    _, atras = _git(clone, "rev-list", "--count", "HEAD..origin/main")
    _, frente = _git(clone, "rev-list", "--count", "origin/main..HEAD")
    _, nome = _git(clone, "config", "user.name")
    _, email = _git(clone, "config", "user.email")
    return {"itens": itens, "barrados": barrados, "atras": int(atras or 0), "frente": int(frente or 0),
            "nome": nome if "\n" not in nome else "", "email": email if "\n" not in email else ""}


def sincronizar(clone, mensagem, python, nome="", email=""):
    """Executa. Devolve as linhas para o quadro; levanta RuntimeError com a explicação se parar."""
    out = []
    if nome:
        _git(clone, "config", "user.name", nome)
    if email:
        _git(clone, "config", "user.email", email)
    rc, txt = _git(clone, "pull", "--ff-only", "origin", "main", timeout=300)
    if rc:
        raise RuntimeError("Parei antes do commit: o git pull não saiu, nada foi alterado.\n" + txt[-500:] +
                           "\nSe for arquivo seu em conflito com o que chegou do GitHub, abra o Claude Code na "
                           "pasta do SSEG e peça \"faz o pull e me mostra o conflito\".")
    out.append("✓ GitHub trazido para o PC")
    itens = _status(clone)
    if itens:
        if not mensagem.strip():
            raise RuntimeError("Escreva a mensagem do commit (o que mudou, em uma linha).")
        _git(clone, "add", "-A")
        # o que as travas barrariam fica fora do commit, mas continua na pasta
        barrados = conferir_barrados(clone, python)
        if barrados:
            _git(clone, "reset", "-q", "--", *barrados)
            out.append("• ficaram fora do commit (dado de processo): " + ", ".join(barrados))
        rc, txt = _git(clone, "diff", "--cached", "--quiet")
        if rc == 0:
            out.append("• nada a commitar além do que ficou fora")
        else:
            rc, txt = _git(clone, "commit", "-q", "-m", mensagem.strip(), timeout=300)
            if rc:
                _git(clone, "reset", "-q")
                raise RuntimeError("O commit foi barrado pelas travas do SSEG (nada saiu do PC):\n" + txt[-1200:])
            out.append("✓ commit feito: " + mensagem.strip())
    _, frente = _git(clone, "rev-list", "--count", "origin/main..HEAD")
    if int(frente or 0):
        rc, txt = _git(clone, "push", "origin", "HEAD:main", timeout=300)
        if rc:
            raise RuntimeError("O commit ficou no PC, mas o push não saiu:\n" + txt[-500:] +
                               "\nSe for falta de login no GitHub, abra o Claude Code na pasta do SSEG e peça ajuda.")
        out.append("✓ enviado ao GitHub (%s commit(s))" % frente)
    elif not itens:
        out.append("• nada mudou neste PC")
    return out


def conferir_barrados(clone, python):
    """Barrados entre o que está no stage agora — pelo mesmo pre-commit, em modo de consulta."""
    _, staged = _git(clone, "-c", "core.quotepath=off", "diff", "--cached", "--name-only")
    lista = [f for f in staged.splitlines() if f]
    if not lista:
        return []
    gancho = os.path.join(clone, ".claude", "hooks", "sseg_hooks.py")
    if not python or not os.path.exists(gancho):
        return []
    p = subprocess.run([python, gancho, "conferir"], input=json.dumps(lista), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60, creationflags=SEM_JANELA,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": clone, "PYTHONUTF8": "1"})
    try:
        return sorted(json.loads(p.stdout or "{}"))
    except ValueError:
        return []
