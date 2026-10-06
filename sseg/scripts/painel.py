#!/usr/bin/env python3
"""Gera o retrato do Painel SSEG a partir do repositório, sem modelo de linguagem.

O painel mostra o texto dos próprios arquivos (frontmatter, títulos, listas "Nunca", linhas de
parâmetro), nunca um resumo escrito à mão: o que muda no repositório aparece no painel na
próxima geração, e o que deixa de bater vira item em "divergências".

Uso:
    python3 painel.py --saida <pasta>          # grava um JSON por documento do banco + hashes.json
    python3 painel.py --saida <pasta> --resumo # idem, e imprime as divergências encontradas

Saída: <pasta>/<doc>.json para cada documento da coleção "retrato" do painel (meta, instrucoes,
arquitetura, skills, agentes, docs, rotinas, parametros, divergencias) e <pasta>/hashes.json.
Só biblioteca padrão.
"""
import argparse, datetime, glob, hashlib, json, os, re, subprocess, sys

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SSEG = os.path.join(RAIZ, "sseg")


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return f.read()


def rel(caminho):
    return os.path.relpath(caminho, RAIZ).replace(os.sep, "/")


def git(*args):
    try:
        return subprocess.run(["git", "-C", RAIZ, *args], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


def ultima_mudanca(caminho):
    s = git("log", "-1", "--format=%cs", "--", rel(caminho))
    return s or None


def frontmatter(texto):
    """Devolve (dict, corpo). Entende `chave: valor` com ou sem aspas, uma linha por chave."""
    m = re.match(r"^---\n(.*?)\n---\n?", texto, re.S)
    if not m:
        return {}, texto
    fm = {}
    for linha in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", linha)
        if not mm:
            continue
        v = mm.group(2).strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1].replace('\\"', '"')
        fm[mm.group(1)] = v
    return fm, texto[m.end():]


def secoes(corpo):
    """Lista de (nivel, titulo, texto) para cada título markdown, fora de blocos de código."""
    out, atual, buf, cod = [], (0, "", []), [], False
    linhas = corpo.splitlines()
    tit = [(0, "")]
    blocos = []
    for ln in linhas:
        if ln.strip().startswith("```"):
            cod = not cod
        m = None if cod else re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            blocos.append((tit[-1][0], tit[-1][1], buf))
            tit.append((len(m.group(1)), m.group(2).strip()))
            buf = []
        else:
            buf.append(ln)
    blocos.append((tit[-1][0], tit[-1][1], buf))
    return [(n, t, "\n".join(b).strip()) for n, t, b in blocos]


def primeiro_paragrafo(texto, limite=500):
    for p in re.split(r"\n\s*\n", texto):
        p = p.strip()
        if p and not p.startswith(("#", "|", "```", ">")):
            p = re.sub(r"\s*\n\s*", " ", p)
            return p if len(p) <= limite else p[:limite].rsplit(" ", 1)[0] + "…"
    return ""


def itens_lista(texto):
    itens, atual = [], None
    for ln in texto.splitlines():
        m = re.match(r"^\s*(?:[-*]|\d+\.)\s+(.*)$", ln)
        if m and not ln.startswith("    "):
            if atual:
                itens.append(atual.strip())
            atual = m.group(1)
        elif atual is not None and ln.strip() and not ln.lstrip().startswith(("#", "|")):
            atual += " " + ln.strip()
        elif not ln.strip() and atual:
            itens.append(atual.strip())
            atual = None
    if atual:
        itens.append(atual.strip())
    return itens


def tokens_aprox(texto):
    return round(len(texto) / 3.6)


# ---------------------------------------------------------------- skills e subagentes

def skills():
    out = []
    for arq in sorted(glob.glob(os.path.join(SSEG, "skills", "*", "SKILL.md"))):
        txt = ler(arq)
        fm, corpo = frontmatter(txt)
        sec = secoes(corpo)
        quando = ""
        for n, t, b in sec:
            if re.search(r"quando (disparar|usar)", t, re.I):
                quando = b
                break
        if not quando:
            # skills sem a seção: o primeiro parágrafo depois do título costuma dizer quando usar
            for n, t, b in sec:
                if n == 1:
                    quando = primeiro_paragrafo(b, 700)
                    break
        nunca = []
        for n, t, b in sec:
            if re.match(r"^(nunca|regras|cuidados)$", t.strip(), re.I):
                nunca += itens_lista(b)
        paradas = []
        for ln in corpo.splitlines():
            if "⛔" in ln:
                limpo = re.sub(r"^\s*[-*]?\s*", "", ln).strip()
                if limpo and limpo not in paradas:
                    paradas.append(limpo)
        roteiro = [{"nivel": n, "titulo": t} for n, t, _ in sec if n in (2, 3) and t]
        out.append({
            "nome": fm.get("name") or os.path.basename(os.path.dirname(arq)),
            "pasta": os.path.basename(os.path.dirname(arq)),
            "arquivo": rel(arq),
            "descricao": fm.get("description", ""),
            "quando": quando,
            "roteiro": roteiro,
            "paradas": paradas,
            "nunca": nunca,
            "tamanho_kb": round(len(txt.encode("utf-8")) / 1024, 1),
            "tokens": tokens_aprox(txt),
            "atualizado": ultima_mudanca(arq),
        })
    return out


def agentes():
    out = []
    for arq in sorted(glob.glob(os.path.join(RAIZ, ".claude", "agents", "*.md"))):
        txt = ler(arq)
        fm, corpo = frontmatter(txt)
        out.append({
            "nome": fm.get("name") or os.path.splitext(os.path.basename(arq))[0],
            "modelo": fm.get("model", "(herda)"),
            "ferramentas": fm.get("tools", ""),
            "descricao": fm.get("description", ""),
            "arquivo": rel(arq),
            "atualizado": ultima_mudanca(arq),
        })
    return out


# ---------------------------------------------------------------- docs

def docs():
    out = []
    pastas = [("workflow", os.path.join(SSEG, "workflow", "*.md")), ("normas", os.path.join(SSEG, "normas", "*.md"))]
    for grupo, padrao in pastas:
        for arq in sorted(glob.glob(padrao)):
            txt = ler(arq)
            fm, corpo = frontmatter(txt)
            titulo = ""
            m = re.search(r"^#\s+(.*)$", corpo, re.M)
            if m:
                titulo = m.group(1).strip()
            desc = fm.get("description") or primeiro_paragrafo(corpo[m.end():] if m else corpo, 300)
            out.append({
                "grupo": grupo, "arquivo": rel(arq), "titulo": titulo, "descricao": desc,
                "tamanho_kb": round(len(txt.encode("utf-8")) / 1024, 1), "tokens": tokens_aprox(txt),
                "atualizado": ultima_mudanca(arq),
            })
    return out


# ---------------------------------------------------------------- instruções e arquitetura

MARC_INI = re.compile(r"<!--\s*=+\s*IN[IÍ]CIO DO TEXTO DO CAMPO.*?-->")
MARC_FIM = re.compile(r"<!--\s*=+\s*FIM DO TEXTO DO CAMPO.*?-->")


def instrucoes():
    arq = os.path.join(SSEG, "workflow", "instrucoes-projeto-espelho.md")
    txt = ler(arq)
    a, b = MARC_INI.search(txt), MARC_FIM.search(txt)
    if a and b:
        texto = txt[a.end():b.start()].strip()
    else:
        i = txt.find("## Papel")
        texto = txt[i:].strip() if i >= 0 else ""
    hist = []
    for ln in txt[: a.start() if a else len(txt)].splitlines():
        m = re.match(r"^\|\s*(\d{2}/\d{2}/\d{4})\s*\|\s*(.*?)\s*\|\s*$", ln)
        if m:
            hist.append({"data": m.group(1), "mudanca": m.group(2)})
    return {"arquivo": rel(arq), "texto": texto, "historico": hist[-6:], "marcadores": bool(a and b),
            "tokens": tokens_aprox(texto), "atualizado": ultima_mudanca(arq)}


def arquitetura():
    arq = os.path.join(SSEG, "workflow", "00-arquitetura-do-projeto.md")
    fm, corpo = frontmatter(ler(arq))
    return {"arquivo": rel(arq), "descricao": fm.get("description", ""), "texto": corpo.strip(),
            "atualizado": ultima_mudanca(arq)}


# ---------------------------------------------------------------- rotinas (crontab do servidor)

DIAS = {"0": "domingo", "1": "segunda", "2": "terça", "3": "quarta", "4": "quinta", "5": "sexta", "6": "sábado", "7": "domingo"}


def cron_legivel(expr):
    if expr.startswith("@reboot"):
        return "ao ligar o servidor"
    p = expr.split()
    if len(p) < 5:
        return expr
    mi, h, dm, me, dw = p[:5]
    hora = f"{int(h):02d}h{int(mi):02d}" if mi.isdigit() and h.isdigit() else f"{h}:{mi}"
    if dm == "*" and me == "*":
        if dw == "*":
            return f"todo dia, {hora}"
        if dw == "1-5":
            return f"dias úteis, {hora}"
        if dw in DIAS:
            return f"{DIAS[dw]}, {hora}"
        return f"dias {dw}, {hora}"
    return expr


def rotinas(crontab_txt):
    out, comentario = [], []
    if not crontab_txt:
        return out
    for ln in crontab_txt.splitlines():
        s = ln.strip()
        if not s:
            comentario = []
            continue
        if s.startswith("#"):
            comentario.append(s.lstrip("# ").strip())
            continue
        if re.match(r"^[A-Z_]+=", s):
            continue
        if s.startswith("@"):
            expr, cmd = s.split(None, 1)[0], s.split(None, 1)[1] if " " in s else ""
        else:
            partes = s.split(None, 5)
            expr, cmd = " ".join(partes[:5]), partes[5] if len(partes) > 5 else ""
        cmd_curto = re.sub(r"\s*>>.*$", "", cmd)
        cmd_curto = re.sub(r"\$HOME/|/home/\w+/", "~/", cmd_curto)
        out.append({"quando": cron_legivel(expr), "cron": expr, "comando": cmd_curto,
                    "descricao": " ".join(c for c in comentario if not c.lower().startswith("rotinas do sseg"))})
        comentario = []
    return out


# ---------------------------------------------------------------- parâmetros (linha literal da fonte)

# Cada parâmetro aponta para a linha do arquivo-fonte que o define. Se o texto da fonte mudar e a
# busca deixar de casar, o parâmetro aparece em "divergências" — nunca um valor velho no painel.
PARAMETROS = [
    ("SOL", "Tamanho da caixa “Especificar”", "sseg/skills/sol-cbmrs-navegador/SKILL.md", r"≤ 1\.950 caracteres"),
    ("SOL", "Formato do texto para o SOL", "sseg/skills/ppci-notificacao-cia/SKILL.md", r"come[çc]a com uma \*\*quebra de linha\*\*"),
    ("SOL", "Caixa de análise do analista", "sseg/skills/ppci-abertura-sessao/SKILL.md", r"solcbm\.rs\.gov\.br/solcbm/adm/#/analise-tecnica`"),
    ("SOL", "Lançar no SOL pelo navegador", "sseg/skills/sol-cbmrs-navegador/SKILL.md", r"Lançar pelo navegador só quando o analista pedir"),
    ("Norma", "Depósito J subsidiário vira predominante", "sseg/workflow/instrucoes-projeto-espelho.md", r"depósito grupo J que exceda 10%"),
    ("Norma", "Roteamento da tabela de exigências", "sseg/skills/ppci-analise-processo/SKILL.md", r"^Roteamento: área ≤ 750"),
    ("Norma", "Fonte da tabela pela situação da edificação", "sseg/skills/ppci-analise-processo/SKILL.md", r"Primeiro a \*\*fonte\*\*"),
    ("Norma", "Divisão J pela carga de incêndio", "sseg/skills/ppci-analise-processo/SKILL.md", r"J-2 até 300"),
    ("Vigência", "RT 01/2022 → RT 01/2024", "sseg/workflow/instrucoes-projeto-espelho.md", r"PPCI protocolado até \*\*31/12/2024\*\*"),
    ("Vigência", "RT 17 (hidrantes)", "sseg/workflow/instrucoes-projeto-espelho.md", r"RT 17 Parte 01/2025 \(hidrantes e mangotinhos\) entra em vigor"),
    ("Vigência", "RT 31 (câmaras frigoríficas)", "sseg/normas/banco-notificacoes-padrao.md", r"A IN 056/CBMRS/DSPCI foi revogada"),
    ("Modelo", "Modelo padrão das conversas", "sseg/workflow/politica-modelo-e-custo.md", r"\*\*toda conversa abre em"),
    ("Modelo", "Revisão final da CIA", "sseg/skills/ppci-revisao-cia/SKILL.md", r"Modelo: \*\*"),
    ("Modelo", "Onde modelo leve não entra", "sseg/workflow/politica-modelo-e-custo.md", r"Haiku só como subagente mecânico"),
    ("Rotina", "Meta de produção", "sseg/workflow/modo-de-trabalho-do-analista.md", r"Meta: dois PPCI"),
    ("Rotina", "Tamanho da resposta de rotina", "sseg/workflow/modo-de-trabalho-do-analista.md", r"resposta de rotina com até"),
    ("Rotina", "Próximo da lista", "sseg/skills/ppci-abertura-sessao/SKILL.md", r"Critério do próximo"),
    ("Pastas", "Normas que faltam em normas/pdf/", "sseg/skills/ppci-analise-processo/SKILL.md", r"\*\*Faltam\*\*"),
    ("Pastas", "Pasta do processo", "sseg/skills/ppci-analise-processo/SKILL.md", r"A subpasta do processo fica em"),
]


def linha_literal(arquivo, padrao):
    caminho = os.path.join(RAIZ, arquivo)
    if not os.path.exists(caminho):
        return None
    linhas = ler(caminho).splitlines()
    rx = re.compile(padrao)
    inicio_bloco = lambda s: (not s.strip()) or s.lstrip().startswith(("#", "|", "```", ">")) or re.match(r"^\s*([-*]|\d+\.)\s", s)
    for i, ln in enumerate(linhas):
        if rx.search(ln):
            # o parágrafo inteiro em volta da linha (ou o item de lista), para não cortar a frase
            ini = i
            while ini > 0 and not re.match(r"^\s*([-*]|\d+\.)\s", linhas[ini]) and not inicio_bloco(linhas[ini - 1]):
                ini -= 1
            if ini > 0 and re.match(r"^\s*([-*]|\d+\.)\s", linhas[ini - 1]) and not re.match(r"^\s*([-*]|\d+\.)\s", linhas[ini]):
                ini -= 1
            fim = i
            while fim + 1 < len(linhas) and not inicio_bloco(linhas[fim + 1]):
                fim += 1
            texto = " ".join(l.strip() for l in linhas[ini:fim + 1])
            if len(texto) > 900:
                p = texto.find(rx.search(texto).group(0)) if rx.search(texto) else 0
                a = max(0, p - 300)
                texto = ("…" if a else "") + texto[a:a + 800] + "…"
            return {"linha": ini + 1, "texto": texto}
    return None


def parametros():
    out = []
    for grupo, nome, arquivo, padrao in PARAMETROS:
        achado = linha_literal(arquivo, padrao)
        out.append({"grupo": grupo, "nome": nome, "arquivo": arquivo,
                    "linha": achado["linha"] if achado else None,
                    "texto": achado["texto"] if achado else None})
    return out


# ---------------------------------------------------------------- divergências (conferências automáticas)

NUM = {"duas": 2, "três": 3, "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10}

# Frases que já foram verdade e deixaram de ser. Cada uma diz o que mudou.
DESATUALIZADAS = [
    (r"[Rr]odam só onde há sandbox|[Ss]ó roda no Cowork|feitos para rodar no (ambiente do )?Cowork",
     "Os scripts rodam também no PC do quartel (Python desde 03/10/2026) e no servidor."),
    (r"PC do quartel não tem Python|não está instalado no PC do quartel",
     "Python e Poppler foram instalados no PC do quartel em 03/10/2026 (CLAUDE.md)."),
    (r"sem dependência externa",
     "normas_converter.py, normas_verificador.py e gerar_recortes.py pedem pymupdf, pymupdf4llm, pillow e numpy (CLAUDE.md)."),
    (r"A1\.Flex segue sem vaga|[Pp]rovisório numa VM AMD Micro",
     "A A1.Flex está em produção desde 05/10/2026; a Micro é reserva desligada."),
    (r"cópia de backup das \d+ skills|cópia, não a fonte",
     "Desde 02/10/2026 o repositório é a FONTE das skills; a conta é cópia."),
    (r"O canônico são os docs do Projeto|[Oo] projeto é a versão canônica",
     "CLAUDE.md: o repositório é a fonte; o projeto do claude.ai recebe pelo GitHub sincronizado."),
]

CODIGO = re.compile(r"\bA000\d{5}[A-Z]{2}\d{3}\b")


def arquivos_md_versionados():
    lista = git("ls-files", "*.md").splitlines()
    return [l for l in lista if not l.startswith(("sseg/normas/md/", "sseg/normas/base/"))]


def divergencias(sk, ag):
    achados = []

    def add(tipo, gravidade, titulo, detalhe, onde=None, sugestao=None):
        achados.append({"tipo": tipo, "gravidade": gravidade, "titulo": titulo, "detalhe": detalhe,
                        "onde": onde or [], "sugestao": sugestao or ""})

    md = arquivos_md_versionados()
    textos = {}
    for f in md:
        try:
            textos[f] = ler(os.path.join(RAIZ, f))
        except Exception:
            pass
    n_sk = len(sk)
    n_pdf = len(glob.glob(os.path.join(SSEG, "normas", "pdf", "*.pdf")))
    nomes_docs = {os.path.splitext(os.path.basename(f))[0] for f in git("ls-files").splitlines() if f.endswith(".md")}
    todos = set(git("ls-files").splitlines())

    # 1. contagem de skills escrita nos docs
    for f, t in textos.items():
        for i, ln in enumerate(t.splitlines(), 1):
            for m in re.finditer(r"\b(\d+|duas|três|quatro|cinco|seis|sete|oito|nove|dez) skills\b", ln, re.I):
                v = m.group(1).lower()
                n = int(v) if v.isdigit() else NUM.get(v)
                if n is not None and n != n_sk and not re.search(r"\b(19|20)\d\d\b.*skills", ln[:m.start()][-12:]):
                    add("contagem", "média", f"“{m.group(0)}” — o repositório tem {n_sk}",
                        ln.strip()[:300], [f"{f}:{i}"], f"Trocar por {n_sk} (ou tirar a contagem do texto).")

    # 2. contagem de PDFs
    for f, t in textos.items():
        for i, ln in enumerate(t.splitlines(), 1):
            if "PDF" not in ln and "pdf/" not in ln:
                continue
            for m in re.finditer(r"\((\d{1,2}) em (\d{2}/\d{2}/\d{4})", ln):
                if int(m.group(1)) != n_pdf:
                    add("contagem", "baixa", f"{m.group(1)} PDFs em {m.group(2)} — hoje são {n_pdf}",
                        ln.strip()[:300], [f"{f}:{i}"], f"Atualizar para {n_pdf}.")

    # 3. links [[...]] sem doc e caminhos citados que não existem
    for f, t in textos.items():
        for i, ln in enumerate(t.splitlines(), 1):
            for l in re.findall(r"\[\[([^\]|#]+)", ln):
                l = l.strip()
                if l in nomes_docs:
                    continue
                if CODIGO.fullmatch(l):
                    add("link", "baixa", f"[[{l}]] aponta para registro de processo", "Registros de processo não estão no repositório (sseg/processos/ fica fora do Git).", [f"{f}:{i}"], "Trocar o link por texto sem o código.")
                else:
                    add("link", "média", f"[[{l}]] não existe", ln.strip()[:300], [f"{f}:{i}"], "Criar o doc ou tirar o link.")
            for p in re.findall(r"`((?:sseg/)?(?:workflow|normas|scripts|skills)/[^`\s*<>]+?\.(?:md|json|py))`", ln):
                if "..." in p or "<" in p:
                    continue
                if p not in todos and ("sseg/" + p) not in todos:
                    add("caminho", "média", f"`{p}` não existe no repositório", ln.strip()[:300], [f"{f}:{i}"], "Corrigir o caminho ou tirar a referência.")

    # 4. skills citadas no CLAUDE.md x pastas de sseg/skills
    cl = textos.get("CLAUDE.md", "")
    citadas = set(re.findall(r"\|\s*`([a-z0-9-]+)`\s*(?:\(|\|)", cl)) | set(re.findall(r"`(ppci-[a-z-]+|sol-[a-z-]+|sseg-[a-z-]+|passar-contexto)`", cl))
    pastas = {s["pasta"] for s in sk}
    agentes_nomes = {a["nome"] for a in ag}
    for s in sorted(pastas - citadas):
        add("skills", "baixa", f"Skill {s} não aparece no CLAUDE.md", "O CLAUDE.md lista as skills e quando usar cada uma.", ["CLAUDE.md"], "Acrescentar uma linha na tabela de skills.")
    for s in sorted(citadas - pastas - agentes_nomes):
        add("skills", "média", f"CLAUDE.md cita {s}, que não existe em sseg/skills/", "", ["CLAUDE.md"], "Corrigir o nome ou criar a skill.")

    # 5. skills: frontmatter
    for s in sk:
        if s["nome"] != s["pasta"]:
            add("skills", "média", f"Skill {s['pasta']}: name “{s['nome']}” difere da pasta", "", [s["arquivo"]], "Igualar o name ao nome da pasta.")
        if not s["descricao"]:
            add("skills", "alta", f"Skill {s['pasta']} sem description", "Sem description a skill não dispara.", [s["arquivo"]], "Escrever a description.")
        elif len(s["descricao"]) > 1024:
            add("skills", "média", f"Skill {s['pasta']}: description com {len(s['descricao'])} caracteres", "O limite da conta é 1.024.", [s["arquivo"]], "Encurtar.")

    # 6. modelo dos subagentes: CLAUDE.md x frontmatter
    for a in ag:
        m = re.search(r"`" + re.escape(a["nome"]) + r"`\s*\((\w+)\)", cl)
        if m and m.group(1).lower() != a["modelo"].lower():
            add("subagentes", "média", f"{a['nome']}: CLAUDE.md diz {m.group(1)}, o arquivo diz {a['modelo']}", "", ["CLAUDE.md", a["arquivo"]], "Igualar.")

    # 7. frases que deixaram de ser verdade
    for f, t in textos.items():
        for i, ln in enumerate(t.splitlines(), 1):
            for rx, motivo in DESATUALIZADAS:
                if re.search(rx, ln):
                    add("desatualizado", "média", "Texto que deixou de valer", ln.strip()[:300], [f"{f}:{i}"], motivo)

    # 8. Código de processo citado em doc versionado não é divergência: sem acesso ao SOL o código
    # sozinho não identifica ninguém (decisão do Átila, 06/10/2026). O que não vai para o GitHub é
    # o registro do processo, e isso o hook de commit barra.

    # 9. espelho das Instruções sem marcadores
    ins = textos.get("sseg/workflow/instrucoes-projeto-espelho.md", "")
    if not (MARC_INI.search(ins) and MARC_FIM.search(ins)):
        add("instruções", "alta", "Espelho das Instruções sem os marcadores INÍCIO/FIM", "", ["sseg/workflow/instrucoes-projeto-espelho.md"], "Repor os marcadores.")

    ordem = {"alta": 0, "média": 1, "baixa": 2}
    achados.sort(key=lambda a: (ordem.get(a["gravidade"], 3), a["tipo"], a["titulo"]))
    return achados


# ---------------------------------------------------------------- principal

def gerar(crontab_txt):
    sk, ag = skills(), agentes()
    par = parametros()
    div = divergencias(sk, ag)
    for p in par:
        if not p["texto"]:
            div.insert(0, {"tipo": "parâmetro", "gravidade": "média", "titulo": f"Parâmetro “{p['nome']}” não encontrado",
                           "detalhe": "O texto da fonte mudou e a linha que define o parâmetro não foi achada.",
                           "onde": [p["arquivo"]], "sugestao": "Conferir a fonte e ajustar a busca em scripts/painel.py (PARAMETROS)."})
    dc = docs()
    rot = rotinas(crontab_txt)
    commit = git("log", "-1", "--format=%h|%cs|%an|%s")
    h, d, autor, assunto = (commit.split("|", 3) + ["", "", "", ""])[:4]
    meta = {
        "gerado_em": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "commit": h, "data_commit": d, "autor_commit": autor, "assunto_commit": assunto,
        "contagens": {
            "skills": len(sk), "subagentes": len(ag), "docs_workflow": sum(1 for x in dc if x["grupo"] == "workflow"),
            "docs_normas": sum(1 for x in dc if x["grupo"] == "normas"),
            "pdfs": len(glob.glob(os.path.join(SSEG, "normas", "pdf", "*.pdf"))),
            "tabelas": len(glob.glob(os.path.join(SSEG, "scripts", "dados", "tabelas", "tab-*.json"))),
            "rotinas": len(rot), "divergencias": len(div),
            "divergencias_altas": sum(1 for x in div if x["gravidade"] == "alta"),
        },
    }
    return {
        "meta": meta, "instrucoes": instrucoes(), "arquitetura": arquitetura(),
        "skills": {"lista": sk}, "agentes": {"lista": ag}, "docs": {"lista": dc},
        "rotinas": {"lista": rot}, "parametros": {"lista": par}, "divergencias": {"lista": div},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--saida", required=True)
    ap.add_argument("--crontab", help="arquivo com o crontab; sem ele, tenta `crontab -l`")
    ap.add_argument("--resumo", action="store_true")
    a = ap.parse_args()
    if a.crontab:
        cron = ler(a.crontab) if os.path.exists(a.crontab) else ""
    else:
        try:
            cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=10).stdout
        except Exception:
            cron = ""
    dados = gerar(cron)
    os.makedirs(a.saida, exist_ok=True)
    hashes = {}
    for nome, doc in dados.items():
        corpo = json.dumps(doc, ensure_ascii=False, sort_keys=True)
        if nome != "meta":
            hashes[nome] = hashlib.sha256(corpo.encode("utf-8")).hexdigest()[:16]
        with open(os.path.join(a.saida, nome + ".json"), "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.saida, "hashes.json"), "w") as f:
        json.dump(hashes, f, indent=1, sort_keys=True)
    # o painel lê um documento só (retrato/atual): uma gravação por rotina, uma versão para conferir
    with open(os.path.join(a.saida, "atual.json"), "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, separators=(",", ":"))
    if os.path.getsize(os.path.join(a.saida, "atual.json")) > 250 * 1024:
        print("AVISO: atual.json passou de 250 KB; o banco do painel aceita até 256 KB por documento.", file=sys.stderr)
    tam = {n: round(os.path.getsize(os.path.join(a.saida, n + ".json")) / 1024, 1) for n in dados}
    print(json.dumps({"commit": dados["meta"]["commit"], "tamanho_kb": tam, **dados["meta"]["contagens"]}, ensure_ascii=False))
    if a.resumo:
        for d in dados["divergencias"]["lista"]:
            print(f"[{d['gravidade']}] {d['tipo']}: {d['titulo']} — {', '.join(d['onde'][:3])}")


if __name__ == "__main__":
    main()
