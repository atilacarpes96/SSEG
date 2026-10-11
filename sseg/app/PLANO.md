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
- [x] **2. Travas no git** (1.0.3, 11/10/2026: também barra `--no-verify` no Claude, texto validado do banco e arquivo ignorado forçado; instala sozinho ao abrir o Claude Code no clone)
  - [x] `pre-commit` que chama as regras do `sseg_hooks.py` (arquivo de processo, `add -f`, `testar.py`)
  - [x] instalado e conferido pelo "Criar / conferir pastas"
  - [x] caso no `testar.py`: commit com arquivo de processo é barrado
- [x] **2b. Sincronizar processos com o servidor** (1.0.4, 11/10/2026 — pedido vindo do teste no PC)
  - [x] sobe o que mudou no PC em todos os processos; desce o que está mais novo no servidor (`sseg.py sincronizar` / `sseg.py trazer`)
  - [x] conflito (mudou dos dois lados) não sobrescreve: tela de conferência, o analista escolhe
  - [x] planta não vai nem vem; nada pelo GitHub; apagar não se propaga
  - [x] sem chave SSH ou sem o apelido `sseg-servidor`: diz o que falta
  - [ ] teste do Átila no PC (precisa da chave SSH autorizada)
- [x] **2c. Atualização automática do programa** (1.0.6): confere a versão ao abrir; "Atualizar o programa" baixa, fecha, troca o .exe e reabre. Testado no build numa cópia 0.0.1 numa pasta com espaço
- [x] **3. Sincronizar com o GitHub** (1.1.0, 11/10/2026)
  - [x] tela de conferência: arquivos mudados, o que fica fora (mesmas travas, `sseg_hooks.py conferir`), campo da mensagem
  - [x] confere `user.name` e `user.email` e pede se faltar
  - [x] `pull --ff-only` → commit → push; parou, explica em português; o barrado fica fora do commit e na pasta
  - [x] skill que mudou no pull sai em `.zip` (já existe no 1.0)
- [x] **4. Fonte única dos fluxos**
  - [x] `painel.py --fluxos` gera `sseg/workflow/fluxos.json`: modelo e esforço tirados do texto da política; skill, subagentes e prompt no `painel.py`
  - [x] Painel SSEG: aba Conversas, do mesmo retrato
  - [x] `testar.py`: `fluxos.json` igual ao que a política gera; subagente com nome completo de modelo (o `revisor-cia` estava com o atalho `sonnet`)
- [x] **5. Iniciar conversa**
  - [x] um botão por demanda: Começar o dia, Analisar processo, Revisar CIA, Minuta ou despacho, Incorporar norma, Notificação avulsa, Pergunta de norma
  - [x] "Abrir no terminal": Claude Code na pasta do SSEG com `--model` e `--effort` da política e o prompt (código do processo pedido quando precisa)
  - [x] "Copiar o prompt", para quem usa o app do Claude, dizendo qual modelo escolher
- [x] **6. Subagentes**
  - [x] lista de `.claude/agents/`: nome, modelo, para que serve, em que conversa entra
  - [x] acusa atalho (`haiku` = 4.5, `sonnet`, `opus`) e nome desconhecido
- [x] **7. Gasto**
  - [x] lê `~/.claude/projects/<pasta do SSEG>/**/*.jsonl` (inclui subagentes), cada resposta uma vez
  - [x] hoje, 7 e 30 dias, por dia, por modelo, principal × subagente, as 10 conversas que mais gastaram
  - [x] em tokens (entrada, cache, saída), não em US$
- [x] **9. Reportar bug** (praxe dos apps do Átila): descrição + versão + sistema + fim do quadro, limpos de código de processo, pasta e nome de planta/PDF/CIA; abre issue no GitHub ou copia para a conversa do servidor
- [x] **10. Procurar atualização** no rodapé, com a versão atual, junto do Reportar bug
- [ ] **8. Entrega**
  - [x] versão 1.1.0; o build abre e fotografa cada tela (janela, Subagentes, Gasto, Reportar bug, Iniciar conversa, GitHub) e falha se alguma der erro
  - [x] entrada em `workflow/atualizacoes.md`
  - [ ] teste do Átila no PC (lista abaixo); ajustes

## O que o Átila testa no PC (1.1.0)

Abrir o SSEG.exe 1.0.6 que já está no PC: ele deve oferecer "Atualizar o programa (1.1.0)". É o
teste da atualização automática — clicar e ver se fecha, troca e reabre já na 1.1.0.

1. **Rolagem:** a janela rola com a roda do mouse; quadro e rodapé ficam fixos embaixo.
2. **Programas e Pastas:** tudo ✓ como na 1.0.4 (pasta do SSEG `E:\Atila\bombers\SSEG`).
3. **GitHub → Verificar atualizações → Atualizar agora** (traz o 1.1.0 do repositório: fluxos e subagentes).
4. **Sincronizar processos** (agora com a chave SSH): ver a tela de conferência; conflito, se houver, mostrar antes de escolher; conferir que planta não subiu.
5. **Iniciar conversa:** "Pergunta de norma" → "Abrir no terminal" deve abrir o Claude Code em Haiku 5.5 médio na pasta do SSEG; "Analisar processo" pede o código; "Copiar o prompt" copia.
6. **Subagentes:** três, todos com nome completo de modelo, sem ⚠.
7. **Gasto:** mostra as conversas do Claude Code feitas neste PC na pasta do SSEG (pode estar vazio se este PC usou só o app).
8. **Sincronizar com o GitHub:** com uma mudança pequena de teste (ou sem mudança: deve dizer que está igual); se houver arquivo de processo dentro do clone, ele aparece "fica fora".
9. **Reportar bug:** escrever qualquer coisa e conferir na prévia que não aparece código de processo, pasta nem nome de planta; "Copiar para a conversa" e colar aqui.
10. **Procurar atualização:** deve dizer que já está na mais nova.
