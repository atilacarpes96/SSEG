#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sseg_app.py — o programa "SSEG" do PC do analista (Windows), empacotado em SSEG.exe.

FAZ
  - cria e confere as pastas de que o projeto precisa: o clone do repositório (git clone,
    se ainda não existir), a pasta dos processos (print ppci) e `sseg/processos/` no clone;
  - confere e instala Git, Python, Poppler e Claude Code, com os ajustes do CLAUDE.md
    (instalar.py), e abre o login do Claude Code;
  - "Verificar atualizações": compara o clone com o GitHub, mostra o que chegou (commits,
    skills mudadas, última entrada de Atualizações) e oferece o `git pull`; skill mudada sai
    em .zip pronto para subir na conta;
  - "Sincronizar processos": PC <-> servidor por SSH (sseg.py sincronizar), com tela de
    conferência e escolha nos conflitos; planta não vai; nada passa pelo GitHub;
  - confere ao abrir se há versão nova do próprio programa e se atualiza com um botão
    (baixa o .exe novo, fecha, troca e reabre);
  - abre o Painel SSEG, que é o manual.

NÃO FAZ
  - não grava nada de processo no repositório, não dá commit nem push, não força pull;
  - não faz o login do Claude Code pelo analista: só abre a janela dele.

Interface: desde a 2.0, HTML no WebView2 (web_app.py + web/index.html, ponte em api.py);
`--classico` ou falta de WebView2 abre a janela Tk da 1.x, montada em `janela()`.
Lógica sem tkinter no topo (testável no servidor).
Build: .github/workflows/sseg-app.yml (PyInstaller no Windows do GitHub Actions).
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import threading
import urllib.request
import webbrowser
import zipfile

import busca
import claude_local
import gasto
import git_sinc
import instalar
import relato
import sol_entrar

VERSAO = "2.2.1"
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
    out.append(instalar_travas(clone))
    return out


def instalar_travas(clone):
    """pre-commit do git com as travas do CLAUDE.md — a mesma regra do hook do Claude Code."""
    py = instalar.localizar().get("python")
    gancho = os.path.join(clone, ".claude", "hooks", "sseg_hooks.py")
    if not py or not os.path.exists(gancho):
        return "✗ Travas do commit não instaladas: falta o Python (cartão Programas) ou o clone está incompleto"
    p = subprocess.run([py, gancho, "instalar-git"], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=60, creationflags=SEM_JANELA, stdin=subprocess.DEVNULL,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": clone, "PYTHONUTF8": "1"})
    msg = p.stdout.strip() or p.stderr.strip()[-200:] or "travas do commit: sem resposta"
    return ("✓ " if "instalad" in msg and "não" not in msg else "✗ ") + msg


def _versao(t):
    return tuple(int(x) for x in re.findall(r"\d+", t)[:3])


def versao_nova_do_programa():
    """Versão do último SSEG.exe PUBLICADO (releases/latest), se for maior que a deste programa; None se não.
    Não lê o VERSION do main: ele muda no commit, uns 10 min antes de o build publicar o .exe, e aí o
    programa baixava o anterior e pedia de novo (13/10/2026)."""
    try:
        with urllib.request.urlopen("https://github.com/%s/releases/latest" % REPO, timeout=10) as r:
            final = r.geturl()  # .../releases/tag/app-v2.1.9
    except Exception:
        return None
    m = re.search(r"/tag/app-v(\d+\.\d+\.\d+)$", final)
    return m.group(1) if m and _versao(m.group(1)) > _versao(VERSAO) else None


EXE_URL = "https://github.com/%s/releases/latest/download/SSEG.exe" % REPO


def atualizar_programa():
    """Baixa o SSEG.exe novo ao lado do atual e deixa um .bat trocar o arquivo depois que este
    fechar (o Windows não deixa um .exe aberto se sobrescrever) e reabrir. Quem chama fecha a janela."""
    if not getattr(sys, "frozen", False):
        raise RuntimeError("Rodando pelo .py: o programa atualiza junto com o SSEG (\"Atualizar agora\").")
    exe = sys.executable
    novo = exe + ".novo"
    try:
        with urllib.request.urlopen(EXE_URL, timeout=120) as r, open(novo, "wb") as fh:
            shutil.copyfileobj(r, fh)
    except PermissionError:
        raise RuntimeError("Sem permissão para gravar em %s. Mova o SSEG.exe para uma pasta sua "
                           "(Documentos ou Área de Trabalho) e tente de novo." % os.path.dirname(exe))
    with open(novo, "rb") as fh:
        ok = fh.read(2) == b"MZ"
    if not ok or os.path.getsize(novo) < 1_000_000:
        os.remove(novo)
        raise RuntimeError("O download veio incompleto. Tente de novo ou baixe em " + RELEASES_URL)
    bat = os.path.join(os.environ.get("TEMP", os.path.dirname(exe)), "sseg-atualizar.bat")
    # O .exe de arquivo único roda em dois processos e o de fora solta o arquivo por último:
    # em vez de esperar um PID, tenta trocar a cada segundo, por até um minuto.
    script = ("@echo off\r\nset n=0\r\n:troca\r\ntimeout /t 1 /nobreak >nul\r\n"
              'move /y "NOVO" "EXE" >nul 2>&1 && goto abre\r\n'
              "set /a n+=1\r\nif %n% lss 60 goto troca\r\nexit /b 1\r\n"
              ':abre\r\nstart "" "EXE"\r\ndel "%~f0"\r\n')
    with open(bat, "w", encoding="mbcs" if os.name == "nt" else "utf-8", errors="replace") as fh:
        fh.write(script.replace("NOVO", novo).replace("EXE", exe))
    subprocess.Popen(["cmd", "/c", bat], creationflags=SEM_JANELA | 0x00000008,  # DETACHED_PROCESS
                     env=ambiente_limpo())


def ambiente_limpo():
    """Ambiente sem as variáveis do PyInstaller. Herdadas, fazem o .exe novo procurar a
    python312.dll na pasta temporária deste, que some ao fechar ("Failed to load Python DLL")."""
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("_PYI_", "_MEIPASS"))}
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return env


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


def abrir_pdf(caminho, pagina=1):
    """Abre o PDF na página: Edge ou Chrome aceitam #page=N; sem eles, o leitor padrão (página 1)."""
    uri = pathlib.Path(caminho).resolve().as_uri() + "#page=%d" % pagina
    if os.name == "nt":
        pf = [os.environ.get(v, "") for v in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA")]
        for nav in [os.path.join(b, "Microsoft", "Edge", "Application", "msedge.exe") for b in pf] + \
                   [os.path.join(b, "Google", "Chrome", "Application", "chrome.exe") for b in pf]:
            if os.path.isfile(nav):
                subprocess.Popen([nav, uri], env=ambiente_limpo())
                return
        os.startfile(caminho)  # noqa: pylint (só existe no Windows)
    else:
        webbrowser.open(uri)


def pdftotext():
    pop = instalar.localizar().get("poppler")
    nome = "pdftotext.exe" if os.name == "nt" else "pdftotext"
    return os.path.join(os.path.dirname(pop), nome) if pop else nome


# ------------------------------------------------------------------------------ janela

def janela():
    import tkinter as tk
    from tkinter import filedialog, font as tkfont

    raiz = tk.Tk()
    raiz.title("SSEG")
    raiz.configure(bg=FUNDO)
    raiz.minsize(560, 480)
    # cabe em tela de notebook (768 px): desconta a barra de tarefas e a borda da janela
    raiz.geometry("640x%d+40+10" % max(480, min(760, raiz.winfo_screenheight() - 110)))
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

    # embaixo, fixos: o quadro de registro e o rodapé (versão, procurar atualização, reportar bug)
    baixo = tk.Frame(raiz, bg=FUNDO)
    baixo.pack(side="bottom", fill="x", padx=18, pady=(0, 6))
    # no meio, com rolagem: os cartões (a janela não cabe em tela de notebook sem isso)
    meio = tk.Frame(raiz, bg=FUNDO)
    meio.pack(fill="both", expand=True)
    tela = tk.Canvas(meio, bg=FUNDO, highlightthickness=0)
    rolagem = tk.Scrollbar(meio, orient="vertical", command=tela.yview)
    tela.configure(yscrollcommand=rolagem.set)
    rolagem.pack(side="right", fill="y")
    tela.pack(side="left", fill="both", expand=True)
    corpo = tk.Frame(tela, bg=FUNDO)
    item_corpo = tela.create_window((18, 14), window=corpo, anchor="nw")
    corpo.bind("<Configure>", lambda e: tela.configure(scrollregion=(0, 0, e.width + 36, e.height + 20)))
    tela.bind("<Configure>", lambda e: tela.itemconfigure(item_corpo, width=max(e.width - 36, 200)))
    raiz.bind_all("<MouseWheel>", lambda e: str(e.widget).startswith(str(tela))
                  and tela.yview_scroll(int(-e.delta / 120), "units"))

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

    # Programas (Git, Python, Poppler, Claude Code) — primeiro, porque o resto depende deles
    progc = cartao("Programas")
    prog = tk.Label(progc, text="Conferindo…", font=F(10), fg=SUAVE, bg=CARTAO, justify="left", anchor="w")
    prog.pack(fill="x", pady=(0, 8))
    acoes_g = tk.Frame(progc, bg=CARTAO)
    acoes_g.pack(fill="x")
    b_inst = botao(acoes_g, "Instalar o que falta", lambda: rodar(instalar_tudo))
    b_inst.pack(side="left")
    b_login = botao(acoes_g, "Entrar no Claude Code", lambda: rodar(entrar), primario=False)
    b_login.pack(side="left", padx=8)
    b_conf = botao(acoes_g, "Conferir", lambda: rodar(conferir_programas), primario=False)
    b_conf.pack(side="left")

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
    b_sinc = botao(acoes_p, "Sincronizar processos", lambda: rodar(planejar_sinc), primario=False)
    b_sinc.pack(side="left", padx=8)

    # Busca nas normas e no banco — sem gastar token (o trabalho do localizador-normas)
    buscac = cartao("Buscar nas normas e no banco")
    linb = tk.Frame(buscac, bg=CARTAO)
    linb.pack(fill="x")
    consulta = tk.StringVar()
    e_busca = tk.Entry(linb, textvariable=consulta, font=F(11), relief="solid", bd=1)
    e_busca.pack(side="left", fill="x", expand=True, ipady=5)
    e_busca.bind("<Return>", lambda _e: buscar_normas())
    botao(linb, "Buscar", lambda: buscar_normas()).pack(side="left", padx=(8, 0))
    tk.Label(buscac, text='Ex.: extintor "5 m" · pavimento de descarga · subsidiária 10%. Sem acento ou maiúscula; '
                          'todos os termos; frase entre aspas.', font=F(8), fg=SUAVE, bg=CARTAO).pack(anchor="w", pady=(6, 0))

    # Claude: uma conversa por tipo de demanda (modelo e esforço vêm de sseg/workflow/fluxos.json)
    claudec = cartao("Iniciar conversa")
    grade = tk.Frame(claudec, bg=CARTAO)
    grade.pack(fill="x")
    tk.Label(claudec, text="Modelo e esforço vêm da política do SSEG (o mesmo do Painel SSEG).",
             font=F(8), fg=SUAVE, bg=CARTAO).pack(anchor="w", pady=(6, 6))
    acoes_c = tk.Frame(claudec, bg=CARTAO)
    acoes_c.pack(fill="x")
    b_subs = botao(acoes_c, "Subagentes", lambda: rodar(ver_subagentes), primario=False)
    b_subs.pack(side="left")
    b_gasto = botao(acoes_c, "Gasto", lambda: rodar(ver_gasto), primario=False)
    b_gasto.pack(side="left", padx=8)

    # GitHub
    atual = cartao("GitHub")
    st = tk.Label(atual, text="Ainda não verificado.", font=F(10), fg=TEXTO, bg=CARTAO, justify="left", anchor="w")
    st.pack(fill="x", pady=(0, 8))
    acoes_a = tk.Frame(atual, bg=CARTAO)
    acoes_a.pack(fill="x")
    b_verif = botao(acoes_a, "Verificar atualizações", lambda: rodar(verif))
    b_verif.pack(side="left")
    b_atual = botao(acoes_a, "Atualizar agora", lambda: rodar(aplicar))
    b_atual.pack(side="left", padx=8)
    b_git = botao(acoes_a, "Sincronizar com o GitHub", lambda: rodar(conferir_git), primario=False)
    b_git.pack(side="left")
    b_atual.ligar(False)

    # Atalhos
    atal = cartao("Atalhos")
    lin = tk.Frame(atal, bg=CARTAO)
    lin.pack(fill="x")
    botao(lin, "Painel SSEG · manual", lambda: webbrowser.open(PAINEL_URL)).pack(side="left")
    botao(lin, "Pasta dos processos", lambda: abrir(campos["processos"].get()), primario=False).pack(side="left", padx=8)
    botao(lin, "Pasta do SSEG", lambda: abrir(campos["clone"].get()), primario=False).pack(side="left")
    lin_sol = tk.Frame(atal, bg=CARTAO)
    lin_sol.pack(fill="x", pady=(8, 0))
    tk.Label(lin_sol, text="SOL sem teclado (opcional):", font=F(9), fg=SUAVE, bg=CARTAO).pack(side="left")
    botao(lin_sol, "Atalho Abrir SOL", lambda: rodar(criar_atalho_sol), primario=False).pack(side="left", padx=8)
    botao(lin_sol, "Tampermonkey", lambda: passos_tampermonkey(), primario=False).pack(side="left")

    # Registro e rodapé (fixos embaixo)
    reg = tk.Text(baixo, height=5, font=("Consolas", 9), bg="#FBF9F8", fg=TEXTO, relief="solid", bd=1,
                  wrap="word", state="disabled")
    reg.pack(fill="x", pady=(8, 6))
    rod = tk.Frame(baixo, bg=FUNDO)
    rod.pack(fill="x")
    tk.Label(rod, text="SSEG v" + VERSAO, font=F(9, "bold"), fg=TEXTO, bg=FUNDO).pack(side="left")
    b_procurar = botao(rod, "Procurar atualização", lambda: rodar(procurar_versao), primario=False)
    b_procurar.pack(side="left", padx=(10, 0))
    b_bug = botao(rod, "Reportar bug", lambda: reportar_bug(), primario=False)
    b_bug.pack(side="left", padx=8)
    b_prog = botao(rod, "Atualizar o programa", lambda: rodar(trocar_programa))
    # b_prog aparece só quando há versão nova (conferida ao abrir e nos botões de procurar/verificar)
    tk.Label(baixo, text="Ferramenta de uso interno da SSeg — não é sistema oficial do CBMRS.",
             font=F(8), fg=SUAVE, bg=FUNDO).pack(anchor="w", pady=(4, 0))

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
        todos = [b_pastas, b_sinc, b_verif, b_atual, b_inst, b_login, b_conf, b_prog, b_git, b_subs, b_gasto,
                 b_procurar] + estado.get("botoes_fluxo", [])
        for b in todos:
            b.ligar(False)

        def religar():
            for b in todos:
                b.ligar(True)
            b_inst.ligar(estado.get("falta", True))
            b_atual.ligar(bool(estado["dados"] and estado["dados"]["atras"]))

        def trabalho():
            try:
                r = tarefa()
            except Exception as e:  # mostra o erro em vez de fechar o programa
                r = lambda m=str(e): escrever("✗ " + m)  # noqa: E731
            raiz.after(0, lambda: (r and r(), religar()))
        threading.Thread(target=trabalho, daemon=True).start()

    # ---- Sincronizar processos com o servidor (SSH; nada pelo GitHub) — sseg.py sincronizar
    def sseg_py(*args):
        clone, processos = salvar()
        py = instalar.localizar().get("python")
        script = os.path.join(clone, "sseg", "scripts", "sseg.py")
        if not py or not os.path.exists(script):
            raise RuntimeError("Falta o Python (cartão Programas) ou o SSEG nesta pasta (\"Criar / conferir pastas\").")
        p = subprocess.run([py, script, *args, "--pasta", processos], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900, creationflags=SEM_JANELA,
                           stdin=subprocess.DEVNULL, env={**os.environ, "PYTHONUTF8": "1"})
        if p.returncode:
            erro = (p.stderr or p.stdout).strip()
            if "invalid choice" in erro:
                raise RuntimeError("O SSEG desta pasta está desatualizado e ainda não tem esse comando: "
                                   "clique em \"Verificar atualizações\" e depois em \"Atualizar agora\".")
            raise RuntimeError(erro[-1500:])
        return p.stdout

    def planejar_sinc():
        plano = json.loads(sseg_py("sincronizar", "--json"))
        if not (plano["sobe"] or plano["desce"] or plano["conflito"]):
            return lambda: escrever("— Processos — PC e servidor iguais (%d arquivo(s))." % plano["iguais"])
        return lambda: conferencia_sinc(plano)

    def conferencia_sinc(plano):
        """Tela de conferência: o que sobe, o que desce e, nos conflitos, o analista escolhe."""
        jan = tk.Toplevel(raiz)
        jan.title("Sincronizar processos")
        jan.configure(bg=CARTAO)
        jan.transient(raiz)
        jan.grab_set()
        tk.Label(jan, text="SINCRONIZAR PROCESSOS COM O SERVIDOR", font=F(9, "bold"), fg=VERMELHO,
                 bg=CARTAO).pack(anchor="w", padx=16, pady=(12, 2))
        tk.Label(jan, text="Planta não vai nem vem. Nada passa pelo GitHub.", font=F(9), fg=SUAVE,
                 bg=CARTAO).pack(anchor="w", padx=16)
        lista = tk.Frame(jan, bg=CARTAO)
        lista.pack(fill="both", expand=True, padx=16, pady=8)
        for titulo, chaves, seta in (("Sobe para o servidor", plano["sobe"], "↑"),
                                     ("Desce para o PC", plano["desce"], "↓")):
            if chaves:
                tk.Label(lista, text="%s (%d)" % (titulo, len(chaves)), font=F(10, "bold"), fg=TEXTO,
                         bg=CARTAO).pack(anchor="w", pady=(6, 0))
                for k in chaves[:12]:
                    tk.Label(lista, text="  %s %s" % (seta, k), font=F(9), fg=TEXTO, bg=CARTAO).pack(anchor="w")
                if len(chaves) > 12:
                    tk.Label(lista, text="  … e mais %d" % (len(chaves) - 12), font=F(9), fg=SUAVE, bg=CARTAO).pack(anchor="w")
        escolhas = {}
        if plano["conflito"]:
            tk.Label(lista, text="Mudou dos dois lados (%d) — escolha qual fica:" % len(plano["conflito"]),
                     font=F(10, "bold"), fg=VERMELHO_ESC, bg=CARTAO).pack(anchor="w", pady=(10, 2))
            for k in plano["conflito"]:
                lin = tk.Frame(lista, bg=CARTAO)
                lin.pack(fill="x", pady=1)
                tk.Label(lin, text=k, font=F(9), fg=TEXTO, bg=CARTAO).pack(side="left")
                v = tk.StringVar(value="deixar")
                for val, rot in (("deixar", "deixar como está"), ("servidor", "do servidor"), ("pc", "do PC")):
                    tk.Radiobutton(lin, text=rot, variable=v, value=val, font=F(9), bg=CARTAO,
                                   activebackground=CARTAO).pack(side="right")
                escolhas[k] = v
        rod = tk.Frame(jan, bg=CARTAO)
        rod.pack(fill="x", padx=16, pady=(4, 14))

        def confirmar():
            esc = {k: v.get() for k, v in escolhas.items()}
            jan.destroy()
            rodar(lambda: aplicar_sinc(esc))
        botao(rod, "Sincronizar", confirmar).pack(side="left")
        botao(rod, "Cancelar", jan.destroy, primario=False).pack(side="left", padx=8)

    def aplicar_sinc(esc):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
            json.dump(esc, fh)
        try:
            saida = sseg_py("sincronizar", "--escolhas", fh.name)
        finally:
            os.remove(fh.name)
        return lambda: escrever("— Processos —", *saida.strip().splitlines())

    def criar():
        clone, processos = salvar()
        linhas = preparar_pastas(clone, processos)
        return lambda: (escrever("— Pastas —", *linhas), montar_fluxos())

    def mostrar_programas(achados, logado):
        partes = []
        for chave, nome, _id in instalar.PROGRAMAS:
            ok = bool(achados.get(chave))
            extra = "" if chave != "claude" or not ok else (" (logado)" if logado else " (falta entrar)")
            partes.append(("✓ " if ok else "✗ ") + nome + extra)
        falta = instalar.faltando(achados)
        prog.configure(text="   ·   ".join(partes), fg="#2E7D32" if not falta and logado else VERMELHO_ESC)
        estado["claude"] = achados.get("claude")
        estado["falta"] = bool(falta)
        estado["logado"] = logado

    def conferir_programas():
        achados = instalar.localizar()
        logado = bool(achados.get("claude")) and instalar.claude_logado(achados["claude"])
        return lambda: mostrar_programas(achados, logado)

    def instalar_tudo():
        resto = instalar.instalar(lambda l: raiz.after(0, escrever, l))
        achados = instalar.localizar()
        logado = bool(achados.get("claude")) and instalar.claude_logado(achados["claude"])

        def fim():
            mostrar_programas(achados, logado)
            if not resto and not logado:
                escrever("Falta só entrar no Claude Code: clique em \"Entrar no Claude Code\".")
        return fim

    def mostrar_versao(nova):
        if nova and not b_prog.winfo_ismapped():
            b_prog.configure(text="Atualizar o programa (%s)" % nova)
            b_prog.pack(side="left")

    def conferir_versao():
        nova = versao_nova_do_programa()
        return (lambda: (mostrar_versao(nova), escrever("Programa SSEG %s disponível: clique em "
                                                        "\"Atualizar o programa\"." % nova))) if nova else None

    def trocar_programa():
        atualizar_programa()
        return lambda: (escrever("Baixado. Fechando para trocar o programa; ele abre de novo sozinho."),
                        raiz.after(1200, raiz.destroy))

    def entrar():
        if not estado.get("claude"):
            return lambda: escrever("✗ Instale o Claude Code antes (\"Instalar o que falta\").")
        instalar.abrir_login(estado["claude"])
        return lambda: escrever("Abri a janela de login: entre pelo navegador e depois clique em "
                                "\"Conferir\" para confirmar.")

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
                linhas.append("Programa SSEG %s disponível (este é o %s): clique em \"Atualizar o programa\"." % (nova, VERSAO))
                mostrar_versao(nova)
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
            montar_fluxos()
        return mostrar

    # ---- janelas auxiliares
    def dialogo(titulo, subtitulo=""):
        jan = tk.Toplevel(raiz)
        jan.title(titulo)
        jan.configure(bg=CARTAO)
        jan.transient(raiz)
        tk.Label(jan, text=titulo.upper(), font=F(9, "bold"), fg=VERMELHO, bg=CARTAO).pack(anchor="w", padx=16, pady=(12, 2))
        if subtitulo:
            tk.Label(jan, text=subtitulo, font=F(9), fg=SUAVE, bg=CARTAO, justify="left", wraplength=560).pack(anchor="w", padx=16)
        meio_d = tk.Frame(jan, bg=CARTAO)
        meio_d.pack(fill="both", expand=True, padx=16, pady=8)
        rod_d = tk.Frame(jan, bg=CARTAO)
        rod_d.pack(fill="x", padx=16, pady=(4, 14))
        return jan, meio_d, rod_d

    def caixa_texto(pai, texto, altura=18, largura=88):
        caixa = tk.Text(pai, height=altura, width=largura, font=("Consolas", 9), bg="#FBF9F8", fg=TEXTO,
                        relief="solid", bd=1, wrap="none")
        caixa.insert("1.0", texto)
        caixa.configure(state="disabled")
        caixa.pack(fill="both", expand=True)
        return caixa

    def copiar(texto):
        raiz.clipboard_clear()
        raiz.clipboard_append(texto)

    # ---- SOL Entrar (sseg/ferramentas/sol-entrar): atalho + script do Tampermonkey
    def criar_atalho_sol():
        lnk = sol_entrar.instalar_atalho()
        return lambda: escrever("✓ Atalho criado: " + lnk, *sol_entrar.conferir())

    def passos_tampermonkey():
        try:
            copiar(sol_entrar.script_js())
        except OSError as e:
            escrever("✗ Script do SOL Entrar não encontrado: %s" % e)
            return
        sol_entrar.abrir_tampermonkey()
        jan, m, r = dialogo("Tampermonkey (SOL Entrar)", "O script já está copiado. Só com o mouse, no Chrome:")
        for i, t in enumerate(sol_entrar.PASSOS, 1):
            tk.Label(m, text="%d. %s" % (i, t), font=F(10), fg=TEXTO, bg=CARTAO, justify="left",
                     wraplength=540).pack(anchor="w", pady=3)
        tk.Label(m, text="Depois: dois cliques em \"Abrir SOL\" na Área de Trabalho. Aparece uma contagem de 5 s "
                 "no topo da página — clique nela para cancelar.", font=F(9), fg=SUAVE, bg=CARTAO,
                 justify="left", wraplength=540).pack(anchor="w", pady=(8, 0))
        botao(r, "Copiar o script de novo", lambda: (copiar(sol_entrar.script_js()), escrever("Script copiado.")),
              primario=False).pack(side="left")
        botao(r, "Abrir a página de novo", sol_entrar.abrir_tampermonkey, primario=False).pack(side="left", padx=8)
        botao(r, "Fechar", jan.destroy, primario=False).pack(side="left")
        escrever("Script do SOL Entrar copiado; siga os 3 passos da janela.", *sol_entrar.conferir())

    # ---- Busca nas normas e no banco (1.2)
    def ver_pdf(pdf, q, texto):
        """Abre o PDF oficial na página provável do trecho (o pdftotext roda fora da janela)."""
        escrever("Abrindo %s…" % os.path.basename(pdf))

        def trabalho():
            pg = busca.pagina(pdf, q, texto, pdftotext())
            abrir_pdf(pdf, pg)
            return lambda: escrever("PDF aberto na página %d — conferir o item ali antes de citar." % pg)
        rodar(trabalho)

    def buscar_normas():
        q = consulta.get().strip()
        if not q:
            return
        clone = campos["clone"].get().strip()
        res = busca.buscar(busca.carregar(clone), q)
        jan = estado.get("jan_busca")
        if jan is None or not jan.winfo_exists():
            jan, m, r = dialogo("Busca nas normas e no banco", "Localiza; não decide. Antes de usar um modelo do "
                                "banco, diga por que este caso é o caso daquele modelo. Texto convertido só localiza: "
                                "conferir o item no PDF antes de citar.")
            caixa = tk.Text(m, height=26, width=96, font=F(10), bg="#FBF9F8", fg=TEXTO, relief="solid", bd=1, wrap="word")
            caixa.pack(fill="both", expand=True)
            caixa.tag_configure("grupo", font=F(10, "bold"), foreground=VERMELHO, spacing1=10, spacing3=4)
            caixa.tag_configure("onde", font=F(8), foreground=SUAVE, spacing1=8)
            caixa.tag_configure("copiar", font=F(8, "bold"), foreground=VERMELHO_ESC, underline=True)
            caixa.tag_bind("copiar", "<Enter>", lambda _e: caixa.configure(cursor="hand2"))
            caixa.tag_bind("copiar", "<Leave>", lambda _e: caixa.configure(cursor=""))
            botao(r, "Fechar", jan.destroy, primario=False).pack(side="left")
            estado["jan_busca"], estado["caixa_busca"] = jan, caixa
        caixa = estado["caixa_busca"]
        jan.title("Busca: " + q)
        caixa.configure(state="normal")
        caixa.delete("1.0", "end")
        if not res:
            caixa.insert("end", "Nada encontrado para: %s\n\nTente menos termos, ou um sinônimo. Ausência aqui não "
                                "prova ausência na norma: conferir no PDF." % q)
        grupo_atual = None
        for n, x in enumerate(res):
            if x["grupo"] != grupo_atual:
                grupo_atual = x["grupo"]
                caixa.insert("end", dict(busca.GRUPOS)[grupo_atual] + "\n", "grupo")
            caixa.insert("end", "%s — %s:%d   " % (x["secao"] or "(sem seção)", x["arquivo"], x["linha"]), "onde")
            tag = "c%d" % n
            caixa.insert("end", "[copiar]", ("copiar", tag))
            caixa.tag_bind(tag, "<Button-1>", lambda _e, txt=x["copiar"]: (copiar(txt), escrever("Copiado da busca.")))
            pdf = x.get("pdf") and os.path.join(clone, x["pdf"])
            if pdf and os.path.isfile(pdf):
                tag = "p%d" % n
                caixa.insert("end", "   ")
                caixa.insert("end", "[PDF]", ("copiar", tag))
                caixa.tag_bind(tag, "<Button-1>", lambda _e, pdf=pdf, x=x: ver_pdf(pdf, q, x["texto"]))
            caixa.insert("end", "\n" + x["texto"] + "\n")
        if len(res) >= 80:
            caixa.insert("end", "\n(mostrando os 80 primeiros: refine a busca)", "onde")
        caixa.configure(state="disabled")
        jan.lift()

    # ---- Iniciar conversa (item 5) e Subagentes (item 6)
    def montar_fluxos():
        for w in grade.winfo_children():
            w.destroy()
        estado["botoes_fluxo"] = []
        try:
            fluxos = claude_local.ler_fluxos(campos["clone"].get().strip())
        except (OSError, ValueError, KeyError):
            tk.Label(grade, text="Atualize o SSEG desta pasta para ver os tipos de conversa (\"Atualizar agora\").",
                     font=F(9), fg=SUAVE, bg=CARTAO).grid(row=0, column=0, sticky="w")
            return
        estado["fluxos"] = fluxos
        for i, f in enumerate(fluxos):
            b = botao(grade, f["titulo"], lambda f=f: iniciar_fluxo(f), primario=f["grupo"] == "pesado")
            b.grid(row=i // 3, column=i % 3, sticky="ew", padx=(0, 6), pady=3)
            estado["botoes_fluxo"].append(b)
        for c in range(3):
            grade.grid_columnconfigure(c, weight=1)

    def iniciar_fluxo(f):
        sub = "%s · %s%s" % (f["modelo_texto"] or "?", ("skill " + f["skill"]) if f["skill"] else "sem skill",
                            (" · subagentes: " + ", ".join(f["subagentes"])) if f["subagentes"] else "")
        jan, m, r = dialogo(f["titulo"], sub)
        cod = tk.StringVar()
        if f["pede_codigo"]:
            tk.Label(m, text="Código do processo", font=F(9), fg=SUAVE, bg=CARTAO).pack(anchor="w")
            e = tk.Entry(m, textvariable=cod, font=F(11), relief="solid", bd=1, width=22)
            e.pack(anchor="w", ipady=4, pady=(2, 8))
            e.focus_set()
        tk.Label(m, text="Abre o Claude Code numa janela própria, na pasta do SSEG, com o modelo e o esforço da "
                         "política. Para usar o app do Claude: \"Copiar o prompt\" e escolha lá o mesmo modelo.",
                 font=F(9), fg=TEXTO, bg=CARTAO, justify="left", wraplength=520).pack(anchor="w")

        def prompt():
            try:
                return claude_local.montar_prompt(f, cod.get())
            except ValueError as e:
                escrever("✗ " + str(e))
                return None

        def abrir_terminal():
            p = prompt()
            if p is None:
                return
            if not estado.get("claude"):
                escrever("✗ Falta o Claude Code (cartão Programas).")
                return
            claude_local.iniciar(campos["clone"].get().strip(), f, p, estado["claude"])
            escrever("— Conversa — %s aberta (%s)." % (f["titulo"], f["modelo_texto"]))
            jan.destroy()

        def copiar_prompt():
            p = prompt()
            if p is None:
                return
            copiar(p or "")
            escrever("— Conversa — prompt copiado. No app do Claude: Novo → Local → pasta do SSEG → %s, e cole."
                     % f["modelo_texto"])
            jan.destroy()
        botao(r, "Abrir no terminal", abrir_terminal).pack(side="left")
        botao(r, "Copiar o prompt", copiar_prompt, primario=False).pack(side="left", padx=8)
        botao(r, "Cancelar", jan.destroy, primario=False).pack(side="left")

    def ver_subagentes():
        clone, _ = salvar()
        lista = claude_local.subagentes(clone, estado.get("fluxos"))

        def mostrar():
            jan, m, r = dialogo("Subagentes", "Quem chama é a conversa principal, quando a skill manda. Aqui: quem "
                                              "existe, com que modelo, e em que tipo de conversa entra.")
            linhas = []
            for a in lista:
                linhas.append("%s  —  %s%s" % (a["nome"], a["modelo"], ("   ⚠ " + a["aviso"]) if a["aviso"] else ""))
                linhas.append("   usado em: " + (", ".join(a["usado_em"]) or "nenhum tipo de conversa"))
                linhas.append("   " + a["descricao"][:150])
                linhas.append("")
            caixa_texto(m, "\n".join(linhas) or "Nenhum subagente em .claude/agents/.", altura=14)
            botao(r, "Fechar", jan.destroy, primario=False).pack(side="left")
        return mostrar

    # ---- Gasto (item 7)
    def ver_gasto():
        clone, _ = salvar()
        txt = gasto.texto(gasto.resumo(gasto.ler(clone, dias=30)), 30)

        def mostrar():
            jan, m, r = dialogo("Gasto do Claude Code", "Conversas do Claude Code na pasta do SSEG neste PC, em "
                                                        "tokens. Conversas do app do Claude no navegador não entram.")
            caixa_texto(m, txt, altura=24)
            botao(r, "Copiar", lambda: copiar(txt), primario=False).pack(side="left")
            botao(r, "Fechar", jan.destroy, primario=False).pack(side="left", padx=8)
        return mostrar

    # ---- Sincronizar com o GitHub (item 3)
    def conferir_git():
        clone, _ = salvar()
        py = instalar.localizar().get("python")
        info = git_sinc.conferir(clone, py)
        return lambda: tela_git(info, py)

    def tela_git(info, py):
        jan, m, r = dialogo("Sincronizar com o GitHub", "Traz o que chegou, faz o commit do que mudou neste PC e "
                                                        "envia. Dado de processo fica fora. Nunca força nada.")
        linhas = []
        if info["atras"]:
            linhas.append("↓ %d commit(s) no GitHub a trazer" % info["atras"])
        if info["frente"]:
            linhas.append("↑ %d commit(s) deste PC ainda não enviados" % info["frente"])
        for cod, arq in info["itens"][:40]:
            motivo = info["barrados"].get(arq)
            linhas.append(("  ✗ %s  — fica fora: %s" % (arq, motivo)) if motivo else ("  %-2s %s" % (cod, arq)))
        if len(info["itens"]) > 40:
            linhas.append("  … e mais %d" % (len(info["itens"]) - 40))
        if not linhas:
            linhas.append("Nada a fazer: este PC e o GitHub estão iguais.")
        caixa_texto(m, "\n".join(linhas), altura=min(16, len(linhas) + 2))
        campos_g = {}
        if info["itens"]:
            pedir = [("mensagem", "O que mudou (mensagem do commit)", "")]
            if not info["nome"]:
                pedir.append(("nome", "Seu nome (fica registrado no commit)", ""))
            if not info["email"]:
                pedir.append(("email", "Seu e-mail do GitHub", ""))
            for k, rot, val in pedir:
                tk.Label(m, text=rot, font=F(9), fg=SUAVE, bg=CARTAO).pack(anchor="w", pady=(8, 0))
                v = tk.StringVar(value=val)
                tk.Entry(m, textvariable=v, font=F(10), relief="solid", bd=1).pack(fill="x", ipady=4)
                campos_g[k] = v

        def enviar():
            dados = {k: v.get().strip() for k, v in campos_g.items()}
            if info["itens"] and not dados.get("mensagem"):
                escrever("✗ Escreva o que mudou (mensagem do commit).")
                return
            if (not info["nome"] and not dados.get("nome")) or (not info["email"] and not dados.get("email")):
                if info["itens"]:
                    escrever("✗ Falta nome ou e-mail para o commit.")
                    return
            jan.destroy()
            clone = campos["clone"].get().strip()

            def tarefa():
                linhas = git_sinc.sincronizar(clone, dados.get("mensagem", ""), py, dados.get("nome", ""),
                                              dados.get("email", ""))
                return lambda: escrever("— GitHub —", *linhas)
            rodar(tarefa)
        if info["itens"] or info["atras"] or info["frente"]:
            botao(r, "Sincronizar", enviar).pack(side="left")
        botao(r, "Cancelar" if (info["itens"] or info["atras"] or info["frente"]) else "Fechar", jan.destroy,
              primario=False).pack(side="left", padx=8)

    # ---- Procurar atualização e Reportar bug (rodapé)
    def procurar_versao():
        nova = versao_nova_do_programa()
        if nova:
            return lambda: (mostrar_versao(nova), escrever("Programa SSEG %s disponível (este é o %s): clique em "
                                                           "\"Atualizar o programa\"." % (nova, VERSAO)))
        return lambda: escrever("Você já está na versão mais nova do programa (%s)." % VERSAO)

    def reportar_bug():
        jan, m, r = dialogo("Reportar bug", "Vai sem código de processo, sem caminho de pasta e sem nome de "
                                            "planta, PDF ou CIA. Confira abaixo antes de enviar.")
        tk.Label(m, text="O que aconteceu? (o que você clicou, o que esperava, o que apareceu)", font=F(9),
                 fg=SUAVE, bg=CARTAO).pack(anchor="w")
        desc = tk.Text(m, height=5, width=80, font=F(10), relief="solid", bd=1, wrap="word")
        desc.pack(fill="x", pady=(2, 8))
        tk.Label(m, text="Vai junto (versão, sistema e o fim do quadro, já limpos):", font=F(9), fg=SUAVE,
                 bg=CARTAO).pack(anchor="w")
        caminhos = [campos["clone"].get().strip(), campos["processos"].get().strip()]

        def corpo():
            return relato.montar(VERSAO, desc.get("1.0", "end"), reg.get("1.0", "end"), caminhos)
        prev = caixa_texto(m, corpo(), altura=12)

        def atualizar_previa(_e=None):
            prev.configure(state="normal")
            prev.delete("1.0", "end")
            prev.insert("1.0", corpo())
            prev.configure(state="disabled")
        desc.bind("<KeyRelease>", atualizar_previa)

        def issue():
            titulo = relato.limpar(desc.get("1.0", "end").strip().splitlines()[0][:80] if desc.get("1.0", "end").strip()
                                   else "Bug no SSEG.exe " + VERSAO, caminhos)
            webbrowser.open(relato.url_issue(REPO, "[SSEG.exe %s] %s" % (VERSAO, titulo), corpo()))
            escrever("Abri a página de nova issue no GitHub: confira e clique em \"Submit new issue\".")
            jan.destroy()

        def copiar_rel():
            copiar(corpo())
            escrever("Relato copiado: cole na conversa do servidor (Oraculo 23-7).")
            jan.destroy()
        botao(r, "Abrir issue no GitHub", issue).pack(side="left")
        botao(r, "Copiar para a conversa", copiar_rel, primario=False).pack(side="left", padx=8)
        botao(r, "Cancelar", jan.destroy, primario=False).pack(side="left")

    escrever("SSEG %s. Confira as pastas e clique em \"Verificar atualizações\"." % VERSAO)
    montar_fluxos()
    rodar(conferir_programas)
    raiz.after(1500, lambda: rodar(conferir_versao))
    foto = os.environ.get("SSEG_TESTE_FOTO")  # só no build: abre cada tela, fotografa e anota erro
    if foto:
        import traceback
        erros = []
        raiz.report_callback_exception = lambda *a: erros.append("".join(traceback.format_exception(*a)))
        git_falso = {"itens": [("M", "sseg/normas/exemplo.md"), ("??", "CIA 1.pdf")],
                     "barrados": {"CIA 1.pdf": "CIA de processo"}, "atras": 1, "frente": 0, "nome": "", "email": ""}
        passos = [("janela", None), ("busca", lambda: (consulta.set('extintor "5 m"'), buscar_normas())),
                  ("subagentes", lambda: ver_subagentes()()), ("gasto", lambda: ver_gasto()()),
                  ("bug", reportar_bug), ("conversa", lambda: iniciar_fluxo(estado["fluxos"][1])),
                  ("github", lambda: tela_git(git_falso, None)), ("sol", passos_tampermonkey)]

        def passo(i):
            try:
                if passos[i][1]:
                    passos[i][1]()
            except Exception:
                erros.append(passos[i][0] + ": " + traceback.format_exc())
            raiz.after(1500, lambda: fotografar(i))

        def fotografar(i):
            from PIL import ImageGrab
            raiz.update()
            base_f, ext = os.path.splitext(foto)
            ImageGrab.grab().save(foto if i == 0 else "%s-%s%s" % (base_f, passos[i][0], ext))
            for w in raiz.winfo_children():
                if isinstance(w, tk.Toplevel):
                    w.destroy()
            if i + 1 < len(passos):
                passo(i + 1)
            else:
                with open(base_f + "-erros.txt", "w", encoding="utf-8") as fh:
                    fh.write("\n".join(erros))
                raiz.destroy()
        raiz.after(2500, lambda: passo(0))
    raiz.mainloop()


if __name__ == "__main__":
    if os.environ.get("SSEG_TESTE_MARCA"):  # teste do build: prova de que o .exe abriu de verdade
        with open(os.environ["SSEG_TESTE_MARCA"], "a", encoding="utf-8") as fh:
            fh.write(VERSAO + "\n")
    if "--atualizar" in sys.argv:  # sem janela: usado no teste do build
        atualizar_programa()
    elif "--classico" in sys.argv:
        janela()
    else:
        try:  # 2.0: interface HTML no WebView2; sem ele, a janela clássica
            import web_app
            web_app.principal(recurso)
        except Exception as e:  # noqa: BLE001
            if os.environ.get("SSEG_TESTE_FOTO"):
                raise
            sys.stderr.write("Interface nova indisponível (%s); abrindo a clássica.\n" % e)
            janela()
