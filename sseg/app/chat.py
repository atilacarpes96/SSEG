# -*- coding: utf-8 -*-
"""
chat.py — a conversa com o Claude dentro da janela do processo (SSEG.exe 2.1), sem terminal.

Por baixo, um `claude -p` vivo em stream-json (mesmo login do Claude Code, pasta do SSEG, modelo
e esforço de "Analisar processo" em fluxos.json). Só sobe na primeira mensagem do analista:
abrir o processo não dispara nada. A sessão fica no analise.json e volta com --resume.

Cada linha do stream vira um evento simples para a tela (aoevento(dict)):
  texto      resposta do Claude (markdown)
  ferramenta o que ele está fazendo ("Lendo sseg/normas/rt-11...") — discreto
  sub_ini    subagente começou (tipo, descrição, modelo)  → caranguejo
  sub_fim    subagente terminou
  cota       uso da janela de 5 h (rate_limit_event) e o ≈% gasto por este processo
  fim        fim da resposta (tokens, negados pela permissão)
  erro       o claude saiu ou falhou
"""

import json
import os
import subprocess
import threading
import time

import gasto

NOVA_JANELA_NAO = 0x08000000 if os.name == "nt" else 0

# Só o que a análise precisa sem perguntar; o resto volta como "negado" e o analista decide.
PERMITIDOS = ["Read", "Grep", "Glob", "Task", "Agent", "TodoWrite",
              "Bash(python sseg/scripts/*)", "Bash(python3 sseg/scripts/*)", "Bash(py sseg/scripts/*)", "Bash(cd *)",
              "PowerShell(python sseg/scripts/*)", "PowerShell(py sseg/scripts/*)", "PowerShell(cd *)",
              # Chrome DevTools MCP (2.3.10, pedido do Átila): o Chrome do analista inteiro, TODAS as abas — usa a
              # aba do SOL em que ele já entrou. Só ler: sem click/fill/press (lançar no SOL não roda nesta janela).
              "mcp__chrome-devtools-live__list_pages", "mcp__chrome-devtools-live__select_page",
              "mcp__chrome-devtools-live__navigate_page", "mcp__chrome-devtools-live__new_page",
              "mcp__chrome-devtools-live__wait_for", "mcp__chrome-devtools-live__take_snapshot",
              "mcp__chrome-devtools-live__evaluate_script", "mcp__chrome-devtools-live__list_network_requests",
              "mcp__chrome-devtools-live__get_network_request",
              "Bash(pdftotext *)", "Bash(pdftoppm *)", "PowerShell(pdftotext *)", "PowerShell(pdftoppm *)",
              "Bash(git status*)", "Bash(git log*)", "Bash(git diff*)"]

INSTRUCOES = """Você está na janela do processo {codigo} do programa SSEG.exe (não no terminal). Pasta do processo: {pasta}

Regras desta janela:
- Abrir a janela não é pedido. Faça só o que o analista pedir em cada mensagem; não rode o fluxo inteiro sozinho.
- O analista vê três colunas: este chat, o checklist e a CIA em construção. Escreva nelas pelo sseg.py. A pasta atual JÁ é a do SSEG: rode direto `python sseg/scripts/sseg.py ...`, sem `cd ... &&`. Texto com quebra de linha, aspas ou $ vai SEMPRE pela entrada (heredoc com "-"), nunca dentro da linha de comando:
  - exigência nova para a CIA (o FIM fica sozinho na linha, sem espaço antes):
```
python sseg/scripts/sseg.py analise --pasta "{pasta}" exigencia - --medida "<nome da medida como no SOL>" --fundamento "RT xx/aaaa, item y" <<'FIM'

- Deverá ...
FIM
```
  - rascunho para um item que o analista te pediu ("Pedir ao Claude" na coluna CIA, com o id do item, ex.: e3) — grave NO MESMO item, não crie outro:
```
python sseg/scripts/sseg.py analise --pasta "{pasta}" rascunho e3 - --medida "<medida, se o item não tiver>" --fundamento "RT xx/aaaa, item y" <<'FIM'

- Deverá ...
FIM
```
  - pendência que NÃO é pergunta (algo a ver na planta, dado que falta): `python sseg/scripts/sseg.py analise --pasta "{pasta}" pendencia "texto curto"` — uma por comando; diga também no chat.
  - passo do checklist concluído: `python sseg/scripts/sseg.py analise --pasta "{pasta}" passo N` — vários de uma vez: `passo 1 3 4 5` (os 16 passos estão em sseg/workflow/checklist-analise.json). Marque o passo LOGO que ele estiver feito (ex.: data de protocolo confirmada → passo 2), sem esperar o fim.
  - PDF do SOL (CIA anterior, laudo, qualquer `arquivo/<id>`): o texto da CIA não sai da API, só do PDF. Baixe com evaluate_script + filePath "{pasta}\\sol-arquivo-<id>.b64.json", devolvendo {{"status": r.status, "n": bytes, "b64": base64}} de `GET /solcbm/api/v1/adm/arquivo/<id>`; depois `python sseg/scripts/sseg.py analise --pasta "{pasta}" sol-pdf <id> --nome cia` (grava cia-<id>.pdf, o .txt e cia-ultima.txt e apaga o intermediário) e leia o .txt com Read. O id do PDF da última CIA e a data de protocolo já estão em marcos-resumo.json na pasta (ultima_cia.arquivo, protocolo), quando o servidor leu os Marcos: leia com Read antes de procurar no SOL.
- Comandos: só os que já rodam sem aprovação (sseg.py, pdftotext, pdftoppm, git status/log/diff). Esta janela não tem onde o analista aprovar: o resto é negado e o trabalho para. Então: um comando por chamada, sem `&&`, `;`, `|` nem laço `for`; nada de `python -c` ou script solto (JSON e texto se leem com Read; pasta se lista com Glob); se faltar uma rotina, diga ao analista qual faltou em vez de improvisar. Nunca crie arquivo temporário na pasta do SSEG.
  - pendência resolvida no chat (a sua ou uma que o analista respondeu): `python sseg/scripts/sseg.py analise --pasta "{pasta}" resolver p2 p3` — ela sai do topo do checklist.
  - o que o analista já salvou: `python sseg/scripts/sseg.py analise --pasta "{pasta}" ver`.
  Exigência e rascunho entram como rascunho; o texto final é o que o analista salvar, e você nunca o reescreve: se achar problema num texto salvo, aponte e sugira.
- Respostas curtas, em markdown simples (títulos, listas, negrito). O analista lê numa janela.
- SOL: pelo Chrome DevTools MCP (ferramentas mcp__chrome-devtools-live__*), que enxerga TODAS as abas do Chrome do analista — não use o Claude in Chrome nem grupo de abas. Comece com list_pages, escolha a aba do solcbm.rs.gov.br em que ele já entrou (select_page) e navegue nela (navigate_page); só abra aba nova (new_page) se não houver nenhuma do SOL, e então peça ao analista para entrar (a senha é sempre ele quem digita). Se list_pages der tempo esgotado, peça ao analista para clicar em "Permitir" no aviso do Chrome e tente de novo. Ler pela API com evaluate_script (fetch com o token do sessionStorage, como na skill sol-cbmrs-navegador) e trazer só o resumo; onde a skill falar em tabs_context_mcp/javascript_tool/grupo do Claude, use o equivalente daqui. Leitura pesada ao subagente sol-leitor. Nunca lançar, salvar ou mudar nada no SOL nesta janela."""

INSTRUCOES_FLUXO = """Você está na janela "{titulo}" do programa SSEG.exe (não no terminal). O analista conversa numa janela e pode não estar acostumado com terminal.

Regras desta janela:
- Faça só o que o analista pedir em cada mensagem.{skill}
- Respostas curtas, em markdown simples (títulos, listas, negrito); texto de notificação em bloco citável, no formato da caixa do SOL.
- Use os scripts sempre como `python sseg/scripts/...`, a partir da pasta do SSEG.
- SOL: pelo Chrome DevTools MCP (ferramentas mcp__chrome-devtools-live__*), que enxerga TODAS as abas do Chrome do analista — não use o Claude in Chrome nem grupo de abas. Comece com list_pages, escolha a aba do solcbm.rs.gov.br em que ele já entrou (select_page) e navegue nela (navigate_page); só abra aba nova (new_page) se não houver nenhuma do SOL, e então peça ao analista para entrar (a senha é sempre ele quem digita). Se list_pages der tempo esgotado, peça ao analista para clicar em "Permitir" no aviso do Chrome e tente de novo. Ler pela API com evaluate_script (fetch com o token do sessionStorage, como na skill sol-cbmrs-navegador) e trazer só o resumo; onde a skill falar em tabs_context_mcp/javascript_tool/grupo do Claude, use o equivalente daqui. Leitura pesada ao subagente sol-leitor. Nunca lançar, salvar ou mudar nada no SOL nesta janela."""


GUIA_VISUAL = """
Como responder nesta janela (o analista não é do terminal; o programa desenha a resposta):
- Veredito primeiro. Nada de tabela em caracteres (+---+, │) nem texto de terminal: use tabela markdown (| a | b |) ou um bloco do SSEG.
- Perguntas ao analista vão SEMPRE num bloco sseg-perguntas (nunca soltas no texto).
- Blocos do SSEG: cerca ``` com o tipo e, dentro, só JSON válido. O programa desenha; você não escreve HTML. Use quando couber:
```sseg-status
{"estado": "parado", "texto": "Parado: preciso de você", "processo": "A00012345AA001", "criterio": "critério (b) do 5.1.2"}
```
(estado: parado | concluido | aguardando)
```sseg-dados
{"itens": [{"rotulo": "Área", "valor": "3.605,26 m²"}, {"rotulo": "Altura", "valor": "4,85 m"}, {"rotulo": "População", "valor": "470"}, {"rotulo": "Protocolo", "valor": "27/08/2026"}]}
```
```sseg-definidora
{"titulo": "Definidora: empate no (a), I-1 marcada pelo RT", "hipoteses": [{"ocupacao": "I-1", "nota": "risco baixo", "tabela": "6I.1", "medidas": 8, "efeito": "nenhum", "ok": true}], "conclusao": "As 8 medidas são as mesmas nas duas: a definidora não muda o campo 4.", "norma": {"rotulo": "RT 01/2024, item 5.1.2", "consulta": "definidora"}}
```
```sseg-perguntas
{"perguntas": [{"id": "q1", "texto": "Qual a data de protocolo?", "dica": "ex.: 27/08/2026"}]}
```
```sseg-exigencia
{"medida": "Saída de Emergência", "texto": "\\n- Deverá ...", "fundamento": "RT 11/2016, item 5.4.2"}
```
```sseg-norma
{"rotulo": "RT 11/2016, item 5.4.2", "consulta": "largura porta"}
```
- O botão "Pôr na CIA" do sseg-exigencia põe o texto como rascunho; o texto final continua sendo o que o analista salvar.
- O [PDF] do sseg-norma é montado pelo programa: você não precisa abrir PDF para isso. Um bloco por norma, e o "rotulo" com UMA norma só (o programa abre o PDF da primeira que achar no rótulo)."""


def instrucoes_fluxo(fluxo):
    skill = ("\n- Quando o pedido for deste tipo de trabalho, siga a skill %s (sseg/skills/%s/SKILL.md)."
             % (fluxo["skill"], fluxo["skill"])) if fluxo.get("skill") else ""
    return INSTRUCOES_FLUXO.format(titulo=fluxo["titulo"], skill=skill) + GUIA_VISUAL


class Conversa:
    def __init__(self, clone, pasta, codigo, fluxo, claude, subagentes, aoevento, registro, cota_global, sol=None):
        """pasta/codigo None: conversa de um fluxo sem processo (sessão só na memória, sem analise.json)."""
        self.clone, self.pasta, self.codigo, self.fluxo, self.claude = clone, pasta, codigo, fluxo, claude
        self.sessao = None
        self.sol = sol
        self.modelos = {a["nome"]: a["modelo"] for a in subagentes}
        self.aoevento, self.registro = aoevento, registro
        self.cota_global = cota_global   # {"ler": fn, "gravar": fn} — última utilização vista neste PC
        self.proc = None
        self.subs = {}                   # tool_use_id → {tipo, inicio}
        self.ocupado = False
        self._trava = threading.Lock()

    # ------------------------------------------------------------ processo do claude
    def _comando(self):
        cmd = [self.claude, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
               "--model", self.fluxo["modelo"], "--effort", self.fluxo["esforco"],
               "--permission-mode", "acceptEdits"] + (["--add-dir", self.pasta] if self.pasta else []) + [
               "--allowedTools", *PERMITIDOS,
               # o plugin Claude in Chrome fica bloqueado de vez (também para os subagentes): ele cria grupo de abas
               # e pede "Permitir" a cada ação; a memória antiga do PC ainda mandava usá-lo (2.3.12)
               "--no-chrome", "--disallowedTools", "mcp__claude-in-chrome",
               "--append-system-prompt", INSTRUCOES.format(codigo=self.codigo, pasta=self.pasta) + self._sol_txt() + GUIA_VISUAL if self.pasta
               else instrucoes_fluxo(self.fluxo)]
        sessao = self.registro.ler(self.pasta)["chat"].get("sessao") if self.pasta else self.sessao
        if sessao:
            cmd += ["--resume", sessao]
        return cmd

    def _sol_txt(self):
        if not self.sol:
            return ""
        t = "\n- No SOL: o licenciamento está em %s" % self.sol["licenciamento"]
        if not self.sol.get("id"):
            t += " (o id interno ainda não é conhecido: não há api-<id>.json na pasta)"
        t += "; a análise técnica, em %s%s." % (self.sol["analise"], "" if self.sol.get("analise_direta")
                                                 else " (a caixa: o analista clica em Analisar na linha do processo)")
        return t

    def _subir(self):
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("_PYI_", "_MEIPASS"))}
        env["PYTHONUTF8"] = "1"
        self.proc = subprocess.Popen(self._comando(), cwd=self.clone, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                                     bufsize=1, creationflags=NOVA_JANELA_NAO, env=env)
        threading.Thread(target=self._ler, daemon=True).start()
        threading.Thread(target=self._ler_erros, daemon=True).start()

    def enviar(self, texto):
        with self._trava:
            if self.proc is None or self.proc.poll() is not None:
                self._subir()
            self.ocupado = True
            msg = {"type": "user", "message": {"role": "user", "content": texto}}
            self.proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
            self.proc.stdin.flush()

    def parar(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin.close()
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()

    # ------------------------------------------------------------ leitura do stream
    def _ler_erros(self):
        for linha in self.proc.stderr:
            if linha.strip():
                self.aoevento({"t": "aviso", "texto": linha.strip()[:400]})

    def _ler(self):
        proc = self.proc
        for linha in proc.stdout:
            try:
                d = json.loads(linha)
            except ValueError:
                continue
            try:
                self._evento(d)
            except Exception as e:  # um evento estranho não derruba a conversa
                self.aoevento({"t": "aviso", "texto": "evento não entendido: %s" % e})
        self.ocupado = False
        rc = proc.wait()
        if rc:
            self.aoevento({"t": "erro", "texto": "O Claude Code saiu (código %s). Confira em Configuração se ele "
                                                 "está instalado e logado; a próxima mensagem tenta de novo." % rc})

    def _evento(self, d):
        t = d.get("type")
        if t == "system" and d.get("subtype") == "init" and d.get("session_id"):
            if d["session_id"] != self.sessao:
                gasto.anotar_conversa(d["session_id"], self.fluxo, self.codigo)
            self.sessao = d["session_id"]
            if not self.pasta:
                return
            reg = self.registro.ler(self.pasta)
            if reg["chat"].get("sessao") != d["session_id"]:
                reg["chat"]["sessao"] = d["session_id"]
                self.registro.gravar(self.pasta, reg)
        elif t == "assistant":
            for c in d["message"].get("content", []):
                if c.get("type") == "text" and c.get("text", "").strip():
                    self.aoevento({"t": "texto", "texto": c["text"]})
                elif c.get("type") == "tool_use":
                    self._ferramenta(c)
        elif t == "user":
            conteudo = d.get("message", {}).get("content", [])
            for c in conteudo if isinstance(conteudo, list) else []:
                if c.get("type") == "tool_result" and c.get("tool_use_id") in self.subs:
                    s = self.subs.pop(c["tool_use_id"])
                    self.aoevento({"t": "sub_fim", "id": c["tool_use_id"], "segundos": round(time.time() - s["inicio"])})
                elif c.get("type") == "tool_result":
                    self.aoevento({"t": "pronto"})  # a janela relê o analise.json (o sseg.py pode ter escrito)
        elif t == "rate_limit_event":
            self._cota(d.get("rate_limit_info") or {})
        elif t == "result":
            self.ocupado = False
            u = d.get("usage") or {}
            negados = [{"ferramenta": x.get("tool_name", ""),
                        "resumo": str((x.get("tool_input") or {}).get("command") or (x.get("tool_input") or {}).get("file_path") or "")[:90],
                        "detalhe": json.dumps(x.get("tool_input", {}), ensure_ascii=False)[:600]}
                       for x in d.get("permission_denials") or []]
            self.aoevento({"t": "fim", "erro": d.get("is_error", False), "negados": negados,
                           "tokens": sum(u.get(k, 0) or 0 for k in ("input_tokens", "output_tokens",
                                                                    "cache_creation_input_tokens")),
                           "texto": d.get("result", "") if d.get("is_error") else ""})

    def _ferramenta(self, c):
        nome, ent = c.get("name", ""), c.get("input") or {}
        if nome in ("Task", "Agent"):
            tipo = ent.get("subagent_type") or "general-purpose"
            self.subs[c["id"]] = {"tipo": tipo, "inicio": time.time()}
            self.aoevento({"t": "sub_ini", "id": c["id"], "tipo": tipo, "desc": ent.get("description", ""),
                           "modelo": self.modelos.get(tipo, self.fluxo["modelo"])})
            return
        alvo = ent.get("file_path") or ent.get("pattern") or ent.get("command") or ent.get("path") or ""
        rotulo = {"Read": "Lendo", "Grep": "Procurando", "Glob": "Listando", "Bash": "Rodando",
                  "Edit": "Editando", "Write": "Gravando", "TodoWrite": "Organizando"}.get(nome, nome)
        alvo = str(alvo).replace(self.clone, "").replace("\\", "/").lstrip("/")
        self.aoevento({"t": "ferramenta", "texto": "%s %s" % (rotulo, alvo[:140])})

    def _cota(self, info):
        jan = (info.get("unifiedWindows") or {}).get("five_hour") or {}
        u, reinicia = jan.get("utilization"), jan.get("resetsAt")
        if u is None:
            return
        antes = self.cota_global["ler"]() or {}
        if not self.pasta:
            self.cota_global["gravar"]({"u": u, "resets": reinicia})
            self.aoevento({"t": "cota", "janela": round(u * 100), "processo": None, "reinicia": reinicia})
            return
        reg = self.registro.ler(self.pasta)
        gasto = reg["chat"].get("pct_5h", 0.0)
        if antes.get("resets") == reinicia and u >= antes.get("u", 0):
            gasto += u - antes.get("u", 0)
        elif antes.get("resets") != reinicia and antes:
            gasto += u  # janela nova: tudo o que está nela é desde o reinício
        reg["chat"]["pct_5h"] = round(gasto, 4)
        self.registro.gravar(self.pasta, reg)
        self.cota_global["gravar"]({"u": u, "resets": reinicia})
        self.aoevento({"t": "cota", "janela": round(u * 100), "processo": round(gasto * 100, 1), "reinicia": reinicia})
