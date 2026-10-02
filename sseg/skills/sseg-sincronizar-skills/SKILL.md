---
name: sseg-sincronizar-skills
description: Atualizar as skills PPCI da conta a partir de sseg/skills/ do repositório SSEG depois de um git pull, ou levar ao repo uma skill que mudou na conta.
---

# Sincronizar as skills com o repositório SSEG

O repositório (`sseg/skills/<nome>/SKILL.md`) é a **fonte**. A skill instalada na conta é cópia.
`git pull` não instala skill: ela só muda na conta quando o analista salva o cartão de revisão.

## Quando usar

- "atualiza as skills pelo repositório", "sincroniza as skills", "dei pull, atualiza as skills".
- Depois de salvar um cartão de revisão de skill: gravar a cópia no repo (sentido 2).

## Sentido 1 — repo → conta (depois do pull)

1. Na pasta do clone do SSEG, conferir que o pull foi feito: `git --no-optional-locks status -sb`
   e `git log -1`. Se não foi, pedir ao usuário que rode `git pull` no PowerShell e esperar.
2. Para cada pasta de `sseg/skills/`: ler o `SKILL.md` do clone e o da conta (versão instalada:
   na pasta de skills sincronizadas, ex. `~/.claude/skills/synced/*/<nome>/SKILL.md`, ou
   carregando a skill pela ferramenta Skill). Comparar **o corpo** (abaixo do frontmatter) e os
   **valores** de `name` e `description`, ignorando fim de linha, aspas no frontmatter e a
   quebra de linha final: ao salvar o cartão, a conta reescreve o frontmatter (põe aspas,
   tira o `\n` final), e uma comparação byte a byte acusaria diferença falsa.
3. Mostrar uma tabela curta: skill · igual / diferente / nova no repo / só na conta.
4. Para cada skill **diferente ou nova no repo**: chamar `propose_skills` com o `SKILL.md`
   **completo do repo** (até 3 por chamada), `kind: improvement` se a skill existe na conta,
   `new` se não, e no campo `description` **exatamente** o valor do frontmatter do repo (é o
   campo do cartão que vale, não o do texto). O usuário salva cada cartão.
5. Skill que está **só na conta** ou **mais nova na conta**: não sobrescrever. Dizer qual é e
   perguntar se o repo deve receber a versão da conta (sentido 2).
6. Terminar dizendo quantas foram propostas e que só valem depois de salvas.

## Sentido 2 — conta → repo (quando a skill mudou na conta)

1. Gravar em `sseg/skills/<nome>/SKILL.md` do clone o arquivo **como a conta salvou** (copiar o
   da pasta de skills sincronizadas, não o texto do cartão), com fim de linha LF.
2. Conferir com hash (sem CR) que clone e conta ficaram idênticos.
3. Lembrar o usuário: `git add -A`, `git commit`, `git push` no PowerShell. O push não sai
   daqui.

## Regras

- Nunca sobrescrever um lado com o outro sem mostrar a diferença e o usuário escolher.
- Commit e push são do usuário, no PowerShell do PC (o push não sai do Cowork).
- No shell do Cowork, todo `git` vai com `--no-optional-locks`, e nunca `pull`, `add` ou
  `commit` de lá: comando que grava o índice deixa `.git/index.lock`, que a sessão não
  consegue apagar sem permissão de exclusão, e isso trava o próximo commit no PC.
- Nunca mexer em `sseg/processos/` (dados de cliente; fora do GitHub).
- Se `git status` mostrar mudanças não commitadas em `sseg/skills/`, avisar antes de comparar:
  a pasta pode estar à frente do que o outro analista tem.
