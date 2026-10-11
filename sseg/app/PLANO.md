# Plano do programa SSEG (SSEG.exe) — versão 1.1

Decisões do Átila em 11/10/2026. Marcar `[x]` no mesmo commit em que o item fica pronto.

## Decisões

- **Instalação:** tudo de que o projeto precisa no PC é instalado pelo próprio programa, sem
  o analista abrir o PowerShell: Git, Python 3.12, Poppler e o Claude Code de linha de comando.
  Pelo `winget` com `--scope user` (não pede administrador) e pelo instalador oficial do
  Claude Code. O login do Claude Code continua com o analista: o programa abre e ele entra
  pelo navegador uma vez.
- **GitHub:** um botão só, "Sincronizar": tela de conferência → `pull --ff-only` → commit →
  push. Nunca `--force`, nunca `add -f`.
- **Gasto por conversa e por subagente:** entra nesta versão.
- **Travas do commit** saem do hook do Claude Code e vão para um `pre-commit` do git, para
  valer em qualquer commit (programa, PowerShell ou Claude).
- **Fonte única dos fluxos:** o programa não guarda modelo, esforço ou prompt. Lê
  `sseg/workflow/fluxos.json`, gerado pelo `painel.py`, o mesmo que alimenta o Painel SSEG.

## Itens

- [x] **0. Decisões** (11/10/2026)
- [x] **1. Instalar o que falta** (1.0.2, 11/10/2026 — falta o teste no PC do trabalho, item 8)
  - [x] conferir cada pré-requisito (Git, Python que não seja o atalho da Store, Poppler, Claude Code)
  - [x] botão "Instalar o que falta" com `winget --scope user` e o instalador oficial do Claude Code, com o andamento no quadro
  - [x] ajustes do CLAUDE.md feitos sozinhos: `python3.exe`, PATH com Poppler e Python antes do Git, `PYTHONUTF8=1`
  - [x] PC sem `winget`: dizer o que baixar e onde, sem travar o resto
  - [x] "Entrar no Claude Code": abre o login uma vez e confere que ficou logado
- [ ] **2. Travas no git**
  - [ ] `pre-commit` que chama as regras do `sseg_hooks.py` (arquivo de processo, `add -f`, `testar.py`)
  - [ ] instalado e conferido pelo "Criar / conferir pastas"
  - [ ] caso no `testar.py`: commit com arquivo de processo é barrado
- [ ] **3. Sincronizar com o GitHub**
  - [ ] tela de conferência: arquivos mudados, o que ficaria barrado, campo da mensagem
  - [ ] confere `user.name` e `user.email` e pede se faltar
  - [ ] `pull --ff-only` → commit → push; conflito e trava explicados em português, nada alterado
  - [ ] skill que mudou no pull sai em `.zip` (já existe no 1.0)
- [ ] **4. Fonte única dos fluxos**
  - [ ] `painel.py` gera `sseg/workflow/fluxos.json`: demanda → skill, modelo, esforço, subagentes, prompt de abertura, pede código?
  - [ ] Painel SSEG lê o mesmo arquivo
  - [ ] `testar.py`: o modelo de cada fluxo bate com `politica-modelo-e-custo.md`
- [ ] **5. Iniciar conversa**
  - [ ] tela de cartões: Analisar processo, Revisar CIA, Notificação avulsa, Pergunta de norma, Minuta/despacho, Incorporar norma
  - [ ] abre o terminal na pasta do SSEG com `claude --model … --effort …` e o prompt
  - [ ] cópia do prompt + modelo a escolher, para quem prefere o app do Claude
- [ ] **6. Subagentes**
  - [ ] lista de `.claude/agents/`: nome, modelo, para que serve
  - [ ] acusa modelo inválido ou atalho velho (`haiku` = 4.5)
  - [ ] quais subagentes cada fluxo usa (vem do `fluxos.json`)
- [ ] **7. Gasto**
  - [ ] lê os registros do Claude Code no PC (`~/.claude/projects/<pasta>/*.jsonl`) só da pasta do SSEG
  - [ ] tokens por conversa, por modelo e por subagente, por dia e por semana
  - [ ] em tokens, não em US$ (o Claude Code não tem preço do Haiku 5.5)
- [ ] **8. Entrega**
  - [ ] versão 1.1.0, foto da janela no build
  - [ ] entrada em `workflow/atualizacoes.md`
  - [ ] teste do Átila no PC do trabalho; ajustes
