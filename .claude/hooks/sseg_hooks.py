#!/usr/bin/env python3
"""Hooks do Claude Code para o SSEG: as regras do CLAUDE.md que acontecem sozinhas.

Uso (chamado pelo .claude/settings.json; recebe o JSON do evento na entrada padrão):
    python3 sseg_hooks.py inicio      SessionStart  — git pull e aviso do que mudou
    python3 sseg_hooks.py commit      PreToolUse    — barra commit com dado de processo; roda os testes
    python3 sseg_hooks.py banco       PreToolUse    — protege o texto dos modelos validados do banco
    python3 sseg_hooks.py skill       PostToolUse   — skill mudou: gera o .zip e lembra de instalar
    python3 sseg_hooks.py fim         Stop          — lembra de commit quando há mudança parada

Só biblioteca padrão. Roda no servidor (Linux) e no PC do quartel (Git Bash). Nunca quebra a
sessão: erro interno vira silêncio, nunca bloqueio.
"""
import json, os, re, subprocess, sys, time, zipfile

RAIZ = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BANCO = "sseg/normas/banco-notificacoes-padrao.md"
CODIGO = re.compile(r"A000\d{5}[A-Z]{2}\d{3}")


def git(*args, timeout=20):
    try:
        p = subprocess.run(["git", "-C", RAIZ, *args], capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout.rstrip()
    except Exception:
        return 1, ""


def saida(obj):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(0)


def negar(motivo):
    saida({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                  "permissionDecisionReason": motivo}})


# ------------------------------------------------------------------ SessionStart

def inicio(_):
    antes = git("rev-parse", "HEAD")[1]
    git("pull", "--ff-only", "-q", timeout=30)
    depois = git("rev-parse", "HEAD")[1]
    linhas = []
    if antes and depois and antes != depois:
        log = git("log", "--format=%h %an: %s", f"{antes}..{depois}")[1].splitlines()
        linhas.append(f"git pull trouxe {len(log)} commit(s): " + "; ".join(log[:5]))
        mud = git("diff", "--name-only", antes, depois)[1].splitlines()
        skills = sorted({m.split("/")[2] for m in mud if m.startswith("sseg/skills/")})
        if skills:
            linhas.append("Skills alteradas no repositório: " + ", ".join(skills)
                          + ". Para valerem na conta, rodar a skill sseg-sincronizar-skills (ou instalar o .zip).")
        if "sseg/workflow/instrucoes-projeto-espelho.md" in mud:
            linhas.append("O espelho das Instruções mudou: o campo Instruções do projeto no claude.ai precisa receber o texto novo.")
    pend = [l for l in git("status", "--porcelain")[1].splitlines() if l and not l.startswith("??")]
    if pend:
        linhas.append(f"{len(pend)} arquivo(s) alterado(s) sem commit: " + ", ".join(l[3:] for l in pend[:6]))
    if linhas:
        saida({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "SSEG — " + " | ".join(linhas)}})
    sys.exit(0)


# ------------------------------------------------------------------ PreToolUse: git commit

PROIBIDOS = [
    (re.compile(r"(^|/)sseg/processos/"), "registro de processo (sseg/processos/)"),
    (re.compile(r"print ppci", re.I), "pasta de prints de processo"),
    (re.compile(r"(^|/)CIA \d"), "CIA de processo"),
    (re.compile(r"textos\.json$"), "textos de CIA"),
    (CODIGO, "arquivo com código de processo no nome"),
]


def so_comandos(cmd):
    """Tira heredocs e textos entre aspas: só o que o shell executa como comando conta."""
    cmd = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?.*?\n\1\b", " ", cmd, flags=re.S)
    cmd = re.sub(r"'[^']*'|\"(?:\\.|[^\"\\])*\"", " ", cmd)
    return cmd


def commit(evento):
    cmd = so_comandos((evento.get("tool_input") or {}).get("command", ""))
    git_cmd = r"(?:^|[;&|(]\s*|\bthen\s+|\bdo\s+)git\s+(?:-C\s+\S+\s+)?"
    if not re.search(git_cmd + r"commit\b", cmd):
        sys.exit(0)
    if re.search(git_cmd + r"add\b[^|;&]*(\s-f\b|--force)", cmd):
        negar("CLAUDE.md: nunca `git add -f` — é assim que dado de processo escapa do .gitignore.")
    candidatos = set(git("diff", "--cached", "--name-only")[1].splitlines())
    if re.search(r"\bcommit\b[^|;&]*\s-(a|am|-all)\b", cmd) or re.search(r"\bgit\s+add\b", cmd):
        candidatos |= {l[3:] for l in git("status", "--porcelain")[1].splitlines() if l}
    ruins = [(f, nome) for f in candidatos for rx, nome in PROIBIDOS if rx.search(f)]
    if ruins:
        lista = "; ".join(f"{f} ({n})" for f, n in ruins[:8])
        negar("Commit barrado: dado de processo não vai para o GitHub (CLAUDE.md). Tire do stage: " + lista)
    teste = os.path.join(RAIZ, "sseg", "scripts", "testar.py")
    if os.path.exists(teste):
        try:
            p = subprocess.run([sys.executable, teste, "--rapido"], capture_output=True, text=True, timeout=120, cwd=RAIZ)
        except Exception as e:
            sys.exit(0)
        if p.returncode != 0:
            negar("Commit barrado: os testes do repositório falharam (python3 sseg/scripts/testar.py). "
                  "Corrija antes de commitar:\n" + (p.stdout + p.stderr)[-1500:])
    sys.exit(0)


# ------------------------------------------------------------------ PreToolUse: banco de notificações

def linhas_protegidas(texto):
    """Linhas de modelo ("- ...") antes do Histórico: o texto que a chefia validou."""
    corte = texto.find("## Histórico de correções")
    corpo = texto if corte < 0 else texto[:corte]
    return [l.strip() for l in corpo.splitlines() if re.match(r"^- \S", l.strip())]


def banco(evento):
    ti = evento.get("tool_input") or {}
    caminho = ti.get("file_path") or ti.get("notebook_path") or ""
    if not caminho.replace("\\", "/").endswith(BANCO) or os.environ.get("SSEG_BANCO_LIBERADO") == "1":
        sys.exit(0)
    try:
        atual = open(os.path.join(RAIZ, BANCO), encoding="utf-8").read()
    except Exception:
        sys.exit(0)
    novo = None
    nome = evento.get("tool_name")
    if nome == "Write":
        novo = ti.get("content", "")
    else:
        edits = ti.get("edits") or [{"old_string": ti.get("old_string", ""), "new_string": ti.get("new_string", ""),
                                     "replace_all": ti.get("replace_all", False)}]
        novo = atual
        for e in edits:
            a, b = e.get("old_string", ""), e.get("new_string", "")
            if a and a in novo:
                novo = novo.replace(a, b) if e.get("replace_all") else novo.replace(a, b, 1)
    sumidas = [l for l in linhas_protegidas(atual) if l not in novo]
    if sumidas:
        negar("Banco de notificações: o texto dos modelos validados pela chefia não se altera (regra do próprio "
              "banco). Anote a ressalva em linha própria (\"  > ⚠️ ...\") logo abaixo do modelo. Linha que seria "
              f"alterada: \"{sumidas[0][:160]}\". Se a chefia validou texto novo, o analista libera com "
              "SSEG_BANCO_LIBERADO=1 ou edita à mão.")
    sys.exit(0)


# ------------------------------------------------------------------ PostToolUse: SKILL.md

def skill(evento):
    ti = evento.get("tool_input") or {}
    caminho = (ti.get("file_path") or "").replace("\\", "/")
    m = re.search(r"sseg/skills/([^/]+)/SKILL\.md$", caminho)
    if not m:
        sys.exit(0)
    nome = m.group(1)
    destino = os.path.join(RAIZ, ".skills-zip")
    os.makedirs(destino, exist_ok=True)
    z = os.path.join(destino, nome + ".zip")
    try:
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
            f.write(os.path.join(RAIZ, "sseg", "skills", nome, "SKILL.md"), f"{nome}/SKILL.md")
    except Exception:
        sys.exit(0)
    msg = (f"Skill {nome} mudou no repositório. .zip pronto em .skills-zip/{nome}.zip: instalar na conta "
           "(Configurações > Capacidades > Skills > Substituir) e fazer commit/push do SKILL.md.")
    saida({"systemMessage": msg, "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}})


# ------------------------------------------------------------------ Stop

def fim(_):
    pend = [l[3:] for l in git("status", "--porcelain")[1].splitlines() if l and not l.startswith("??")]
    if not pend:
        sys.exit(0)
    try:
        idade = time.time() - max(os.path.getmtime(os.path.join(RAIZ, p.strip('"'))) for p in pend
                                  if os.path.exists(os.path.join(RAIZ, p.strip('"'))))
    except ValueError:
        sys.exit(0)
    if idade < 20 * 60:
        sys.exit(0)
    saida({"systemMessage": f"SSEG: {len(pend)} arquivo(s) alterado(s) há mais de 20 min sem commit "
                            f"({', '.join(pend[:4])}). O CLAUDE.md pede add, commit e push no fim do trabalho."})


if __name__ == "__main__":
    try:
        evento = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except Exception:
        evento = {}
    acao = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        {"inicio": inicio, "commit": commit, "banco": banco, "skill": skill, "fim": fim}.get(acao, lambda e: sys.exit(0))(evento)
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
