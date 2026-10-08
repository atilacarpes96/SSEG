#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sseg_app.py — o programa "SSEG" do PC do analista (Windows), empacotado em SSEG.exe.

FAZ
  - cria e confere as pastas de que o projeto precisa: o clone do repositório (git clone,
    se ainda não existir), a pasta dos processos (print ppci) e `sseg/processos/` no clone;
  - confere os pré-requisitos do CLAUDE.md (Git, Python, Poppler) e diz o comando que falta;
  - "Verificar atualizações": compara o clone com o GitHub, mostra o que chegou (commits,
    skills mudadas, última entrada de Atualizações) e oferece o `git pull`; skill mudada sai
    em .zip pronto para subir na conta;
  - avisa quando há versão nova do próprio programa;
  - abre o Painel SSEG, que é o manual.

NÃO FAZ
  - não grava nada de processo no repositório, não dá commit nem push, não força pull;
  - não instala nada sozinho: mostra o comando e deixa o analista rodar.

Lógica sem tkinter no topo (testável no servidor); a janela só é montada em `janela()`.
Build: .github/workflows/sseg-app.yml (PyInstaller no Windows do GitHub Actions).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import urllib.request
import webbrowser
import zipfile

VERSAO = "1.0.1"
REPO = "atilacarpes96/SSEG"
REPO_URL = "https://github.com/%s.git" % REPO
VERSAO_URL = "https://raw.githubusercontent.com/%s/main/sseg/app/VERSION" % REPO
RELEASES_URL = "https://github.com/%s/releases/latest" % REPO
PAINEL_URL = "https://claude.ai/artifact/7ZJzmqzpqhQU9WrUb4Xtwq"

# Identidade visual do site do CBMRS (bombeiros.rs.gov.br, conferida em 08/10/2026)
VERMELHO, VERMELHO_ESC = "#D93735", "#C32725"
AMARELO, LARANJA = "#FCD733", "#F39431"
FUNDO, CARTAO, TEXTO, SUAVE = "#F6F3F2", "#FFFFFF", "#2B2222", "#6E6262"

SEM_JANELA = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW: git sem piscar console


# ------------------------------------------------------------------------------ lógica

def recurso(nome):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nome)


def arquivo_config():
    base = os.environ.get("APPDATA") or os.path.expanduser("~/.config")
    return os.path.join(base, "SSEG", "config.json")


def ler_config():
    try:
        with open(arquivo_config(), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        casa = os.path.expanduser("~")
        return {"clone": os.path.join(casa, "Documents", "SSEG"),
                "processos": os.path.join(casa, "Desktop", "print ppci")}


def gravar_config(cfg):
    os.makedirs(os.path.dirname(arquivo_config()), exist_ok=True)
    with open(arquivo_config(), "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)


def git(clone, *args, timeout=120):
    p = subprocess.run(["git", "-C", clone, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout, creationflags=SEM_JANELA)
    return p.returncode, (p.stdout + p.stderr).strip()


def eh_clone(clone):
    return os.path.isdir(os.path.join(clone, ".git")) and os.path.isdir(os.path.join(clone, "sseg", "skills"))


def prerequisitos():
    """[(nome, ok, comando para instalar)] — os do CLAUDE.md, 'Pré-requisitos no PC'."""
    py = shutil.which("python3") or shutil.which("python")
    return [
        ("Git", bool(shutil.which("git")), "winget install -e --id Git.Git"),
        ("Python 3", bool(py) and "WindowsApps" not in (py or ""),
         "winget install -e --id Python.Python.3.12 --scope user"),
        ("Poppler (pdftotext, pdftoppm)", bool(shutil.which("pdftoppm")),
         "winget install -e --id oschwartz10612.Poppler"),
    ]


def preparar_pastas(clone, processos):
    """Cria o que falta. Devolve as linhas do relatório."""
    out = []
    os.makedirs(processos, exist_ok=True)
    out.append("✓ Pasta dos processos: %s" % processos)
    if eh_clone(clone):
        out.append("✓ Clone do SSEG já existe: %s" % clone)
    elif os.path.isdir(clone) and os.listdir(clone):
        raise RuntimeError("A pasta %s já tem arquivos e não é o clone do SSEG. Escolha uma pasta vazia "
                           "ou a pasta onde o SSEG já está." % clone)
    else:
        if not shutil.which("git"):
            raise RuntimeError("Falta o Git para baixar o SSEG. No PowerShell: winget install -e --id Git.Git")
        os.makedirs(os.path.dirname(os.path.abspath(clone)), exist_ok=True)
        p = subprocess.run(["git", "clone", REPO_URL, clone], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600, creationflags=SEM_JANELA)
        if p.returncode:
            raise RuntimeError("git clone falhou:\n" + (p.stdout + p.stderr).strip()[-600:])
        out.append("✓ SSEG baixado do GitHub em %s" % clone)
    local = os.path.join(clone, "sseg", "processos")
    os.makedirs(local, exist_ok=True)
    with open(os.path.join(local, "local.json"), "w", encoding="utf-8") as fh:
        json.dump({"print_ppci": os.path.abspath(processos)}, fh, ensure_ascii=False, indent=2)
    out.append("✓ sseg/processos/ (fora do GitHub) com o caminho da pasta dos processos")
    return out


def _versao(t):
    return tuple(int(x) for x in re.findall(r"\d+", t)[:3])


def versao_nova_do_programa():
    """Versão publicada no GitHub, se for maior que a deste programa; None se não."""
    try:
        with urllib.request.urlopen(VERSAO_URL, timeout=10) as r:
            v = r.read().decode("utf-8").strip()
    except Exception:
        return None
    return v if _versao(v) > _versao(VERSAO) else None


def verificar(clone):
    """Busca o GitHub e descreve o que chegaria com o pull. Não altera o clone de trabalho."""
    if not eh_clone(clone):
        raise RuntimeError("A pasta do SSEG não é um clone. Use antes \"Criar / conferir pastas\".")
    rc, out = git(clone, "fetch", "--quiet", "origin")
    if rc:
        raise RuntimeError("Não consegui falar com o GitHub:\n" + out[-400:])
    _, ramo = git(clone, "rev-parse", "--abbrev-ref", "HEAD")
    _, atras = git(clone, "rev-list", "--count", "HEAD..origin/main")
    _, frente = git(clone, "rev-list", "--count", "origin/main..HEAD")
    _, log = git(clone, "log", "--format=%h  %ad  %s", "--date=format:%d/%m", "HEAD..origin/main")
    _, arqs = git(clone, "diff", "--name-only", "HEAD...origin/main")
    _, sujos = git(clone, "status", "--porcelain")
    skills = sorted({m.group(1) for a in arqs.splitlines()
                     for m in [re.match(r"sseg/skills/([^/]+)/SKILL\.md$", a)] if m})
    _, atu = git(clone, "show", "origin/main:sseg/workflow/atualizacoes.md")
    m = re.search(r"^## (\d\d/\d\d/\d{4} — .+)$", atu, re.M)
    return {
        "ramo": ramo, "atras": int(atras or 0), "frente": int(frente or 0),
        "commits": [l for l in log.splitlines() if l.strip()],
        "skills": skills, "instrucoes": "sseg/workflow/instrucoes-projeto-espelho.md" in arqs.splitlines(),
        "sujos": [l for l in sujos.splitlines() if l.strip()],
        "ultima_atualizacao": m.group(1) if m else None,
    }


def atualizar(clone):
    rc, out = git(clone, "pull", "--ff-only", "origin", "main", timeout=300)
    if rc:
        raise RuntimeError("O git pull não saiu (nada foi alterado):\n" + out[-600:] +
                           "\n\nSe for mudança local em conflito, abra o Claude Code na pasta do SSEG e peça "
                           "\"faz o pull e me mostra o conflito\".")
    return out


def zipar_skills(clone, nomes):
    """Um .zip por skill, no formato que o claude.ai aceita (<nome>/SKILL.md, barra normal)."""
    destino = os.path.join(clone, ".skills-zip")
    os.makedirs(destino, exist_ok=True)
    for n in nomes:
        with zipfile.ZipFile(os.path.join(destino, n + ".zip"), "w", zipfile.ZIP_DEFLATED) as z:
            z.write(os.path.join(clone, "sseg", "skills", n, "SKILL.md"), n + "/SKILL.md")
    return destino


def abrir(caminho):
    if os.name == "nt":
        os.startfile(caminho)  # noqa: pylint (só existe no Windows)
    else:
        webbrowser.open("file://" + caminho)


# ------------------------------------------------------------------------------ janela

def janela():
    import tkinter as tk
    from tkinter import filedialog, font as tkfont

    raiz = tk.Tk()
    raiz.title("SSEG")
    raiz.configure(bg=FUNDO)
    raiz.minsize(560, 600)
    try:
        raiz.iconbitmap(recurso("brasao.ico"))
    except tk.TclError:
        pass

    base = "Segoe UI" if "Segoe UI" in tkfont.families() else "Helvetica"
    F = lambda t, w="normal": (base, t, w)  # noqa: E731
    cfg = ler_config()
    estado = {"dados": None}

    # Cabeçalho: brasão + letreiro como no site (branco, amarelo e laranja), faixa vermelha embaixo
    cab = tk.Frame(raiz, bg=CARTAO)
    cab.pack(fill="x")
    try:
        img = tk.PhotoImage(file=recurso("brasao.png")).subsample(4, 4)  # 256 → 64 px
        lb = tk.Label(cab, image=img, bg=CARTAO)
        lb.image = img
        lb.pack(side="left", padx=(18, 12), pady=12)
    except tk.TclError:
        pass
    tit = tk.Frame(cab, bg=CARTAO)
    tit.pack(side="left", pady=12)
    # "SS" amarelo e "EG" laranja colados, como o "CBM" + "RS" do letreiro do site
    letreiro = tk.Canvas(tit, bg=CARTAO, highlightthickness=0, height=42, width=160)
    letreiro.pack(anchor="w")
    a = letreiro.create_text(0, 21, text="SS", anchor="w", font=F(26, "bold"), fill=AMARELO)
    letreiro.create_text(letreiro.bbox(a)[2], 21, text="EG", anchor="w", font=F(26, "bold"), fill=LARANJA)
    tk.Label(tit, text="SEGURANÇA CONTRA INCÊNDIO · CBMRS", font=F(9, "bold"), fg=LARANJA,
             bg=CARTAO).pack(anchor="w")
    tk.Label(cab, text="v" + VERSAO, font=F(9), fg=SUAVE, bg=CARTAO).pack(side="right", anchor="n", padx=14, pady=10)
    tk.Frame(raiz, bg=VERMELHO, height=5).pack(fill="x")

    corpo = tk.Frame(raiz, bg=FUNDO)
    corpo.pack(fill="both", expand=True, padx=18, pady=14)

    def botao(pai, texto, cmd, primario=True):
        cor, hover = (VERMELHO, VERMELHO_ESC) if primario else ("#EDE6E4", "#E2D8D5")
        fg = "#FFFFFF" if primario else TEXTO
        b = tk.Label(pai, text=texto, font=F(10, "bold"), fg=fg, bg=cor, padx=14, pady=7, cursor="hand2")
        b.ativo = True

        def clique(_e):
            if b.ativo:
                cmd()
        b.bind("<Button-1>", clique)
        b.bind("<Enter>", lambda _e: b.ativo and b.configure(bg=hover))
        b.bind("<Leave>", lambda _e: b.configure(bg=cor if b.ativo else "#D9CFCC"))

        def ligar(on):
            b.ativo = on
            b.configure(bg=cor if on else "#D9CFCC", cursor="hand2" if on else "arrow")
        b.ligar = ligar
        return b

    def cartao(titulo):
        c = tk.Frame(corpo, bg=CARTAO, highlightbackground="#E6DCDA", highlightthickness=1)
        c.pack(fill="x", pady=(0, 12))
        tk.Label(c, text=titulo.upper(), font=F(9, "bold"), fg=VERMELHO, bg=CARTAO).pack(anchor="w", padx=14, pady=(10, 4))
        dentro = tk.Frame(c, bg=CARTAO)
        dentro.pack(fill="x", padx=14, pady=(0, 12))
        return dentro

    # Pastas
    pastas = cartao("Pastas")
    campos = {}
    for chave, rotulo in (("clone", "Pasta do SSEG (cópia do GitHub)"), ("processos", "Pasta dos processos (print ppci)")):
        tk.Label(pastas, text=rotulo, font=F(9), fg=SUAVE, bg=CARTAO).pack(anchor="w")
        lin = tk.Frame(pastas, bg=CARTAO)
        lin.pack(fill="x", pady=(2, 8))
        v = tk.StringVar(value=cfg.get(chave, ""))
        tk.Entry(lin, textvariable=v, font=F(10), relief="solid", bd=1).pack(side="left", fill="x", expand=True, ipady=4)

        def escolher(v=v):
            d = filedialog.askdirectory(initialdir=v.get() or os.path.expanduser("~"))
            if d:
                v.set(os.path.normpath(d))
        botao(lin, "Escolher", escolher, primario=False).pack(side="left", padx=(8, 0))
        campos[chave] = v
    acoes_p = tk.Frame(pastas, bg=CARTAO)
    acoes_p.pack(fill="x")
    b_pastas = botao(acoes_p, "Criar / conferir pastas", lambda: rodar(criar))
    b_pastas.pack(side="left")

    # Atualizações
    atual = cartao("Atualizações")
    st = tk.Label(atual, text="Ainda não verificado.", font=F(10), fg=TEXTO, bg=CARTAO, justify="left", anchor="w")
    st.pack(fill="x", pady=(0, 8))
    acoes_a = tk.Frame(atual, bg=CARTAO)
    acoes_a.pack(fill="x")
    b_verif = botao(acoes_a, "Verificar atualizações", lambda: rodar(verif))
    b_verif.pack(side="left")
    b_atual = botao(acoes_a, "Atualizar agora", lambda: rodar(aplicar))
    b_atual.pack(side="left", padx=8)
    b_atual.ligar(False)

    # Atalhos
    atal = cartao("Atalhos")
    lin = tk.Frame(atal, bg=CARTAO)
    lin.pack(fill="x")
    botao(lin, "Painel SSEG · manual", lambda: webbrowser.open(PAINEL_URL)).pack(side="left")
    botao(lin, "Pasta dos processos", lambda: abrir(campos["processos"].get()), primario=False).pack(side="left", padx=8)
    botao(lin, "Pasta do SSEG", lambda: abrir(campos["clone"].get()), primario=False).pack(side="left")

    # Registro
    reg = tk.Text(corpo, height=7, font=("Consolas", 9), bg="#FBF9F8", fg=TEXTO, relief="solid", bd=1,
                  wrap="word", state="disabled")
    reg.pack(fill="both", expand=True)
    tk.Label(raiz, text="Ferramenta de uso interno da SSeg — não é sistema oficial do CBMRS.",
             font=F(8), fg=SUAVE, bg=FUNDO).pack(pady=(0, 8))

    def escrever(*linhas):
        reg.configure(state="normal")
        for l in linhas:
            reg.insert("end", l + "\n")
        reg.see("end")
        reg.configure(state="disabled")

    def salvar():
        cfg.update({k: v.get().strip() for k, v in campos.items()})
        gravar_config(cfg)
        return cfg["clone"], cfg["processos"]

    def rodar(tarefa):
        """Roda fora da janela (git pode demorar) e devolve o resultado na thread da interface."""
        for b in (b_pastas, b_verif, b_atual):
            b.ligar(False)

        def trabalho():
            try:
                r = tarefa()
            except Exception as e:  # mostra o erro em vez de fechar o programa
                r = lambda m=str(e): escrever("✗ " + m)  # noqa: E731
            raiz.after(0, lambda: (r and r(), b_pastas.ligar(True), b_verif.ligar(True),
                                   b_atual.ligar(bool(estado["dados"] and estado["dados"]["atras"]))))
        threading.Thread(target=trabalho, daemon=True).start()

    def criar():
        clone, processos = salvar()
        linhas = preparar_pastas(clone, processos)
        pre = prerequisitos()
        linhas += [("✓ " if ok else "✗ ") + nome + ("" if ok else "  →  no PowerShell: " + cmd) for nome, ok, cmd in pre]
        return lambda: escrever("— Pastas —", *linhas)

    def verif():
        clone, _ = salvar()
        d = verificar(clone)
        nova = versao_nova_do_programa()
        estado["dados"] = d

        def mostrar():
            if d["atras"]:
                st.configure(text="%d atualização(ões) no GitHub esperando. Confira abaixo e clique em "
                                  "\"Atualizar agora\"." % d["atras"], fg=VERMELHO_ESC)
            else:
                st.configure(text="Tudo em dia com o GitHub.", fg="#2E7D32")
            linhas = ["— Atualizações —"] + ["  " + c for c in d["commits"][:15]]
            if len(d["commits"]) > 15:
                linhas.append("  … e mais %d" % (len(d["commits"]) - 15))
            if d["skills"]:
                linhas.append("Skills que mudaram (vão sair em .zip para subir na conta): " + ", ".join(d["skills"]))
            if d["instrucoes"]:
                linhas.append("O campo Instruções mudou: o prompt para atualizar está na aba Atualizações do Painel SSEG.")
            if d["ultima_atualizacao"]:
                linhas.append("Última entrada da aba Atualizações: " + d["ultima_atualizacao"])
            if d["sujos"]:
                linhas.append("Atenção: %d arquivo(s) mudado(s) neste PC sem commit. O pull só sai se não conflitar."
                              % len(d["sujos"]))
            if d["frente"]:
                linhas.append("Este PC tem %d commit(s) que ainda não foram para o GitHub (git push)." % d["frente"])
            if nova:
                linhas.append("Programa SSEG %s disponível (este é o %s): %s" % (nova, VERSAO, RELEASES_URL))
            escrever(*linhas)
        return mostrar

    def aplicar():
        clone, _ = salvar()
        d = estado["dados"] or verificar(clone)
        out = atualizar(clone)
        linhas = ["— Atualizado —", out.splitlines()[-1] if out else "ok"]
        if d["skills"]:
            pasta = zipar_skills(clone, d["skills"])
            linhas.append("Skills em .zip na pasta que abriu: suba cada uma em claude.ai > Configurações > "
                          "Capacidades > Skills > Substituir.")
            abrir(pasta)
        linhas.append("O que fazer em cada mudança: aba Atualizações do Painel SSEG.")
        estado["dados"] = None

        def mostrar():
            st.configure(text="Atualizado. Clique em verificar de novo para conferir.", fg="#2E7D32")
            escrever(*linhas)
        return mostrar

    escrever("SSEG %s. Confira as pastas e clique em \"Verificar atualizações\"." % VERSAO)
    foto = os.environ.get("SSEG_TESTE_FOTO")  # só no build: abre, fotografa a janela e fecha
    if foto:
        def fotografar():
            from PIL import ImageGrab
            raiz.update()
            x, y = raiz.winfo_rootx(), raiz.winfo_rooty()
            ImageGrab.grab((x, y, x + raiz.winfo_width(), y + raiz.winfo_height())).save(foto)
            raiz.destroy()
        raiz.after(2500, fotografar)
    raiz.mainloop()


if __name__ == "__main__":
    janela()
