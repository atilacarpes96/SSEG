# Regras do repositório SSEG para o Claude

Este repositório é **público** e compartilhado entre analistas (cada um com seu próprio Claude).

## Dados de processo nunca vão para o GitHub

- Registros de processo e dados de cliente — `sseg/processos/`, CIA, JSON do SOL, plantas,
  prints, qualquer arquivo com código de processo (A000...) ou dado de proprietário/RT —
  **não entram em commit**.
- `sseg/processos/` está no `.gitignore`. Pode gravar ali localmente; nunca usar `git add -f`,
  nunca remover a linha do `.gitignore`, nunca mover esses dados para outra pasta versionada.
- Antes de todo `git commit`, rodar `git status` e conferir que nenhum desses arquivos aparece.
  Se aparecer, parar e avisar o usuário.

## Trabalho a dois

- Começar a sessão com `git pull`; terminar com `git add` → `git commit` → `git push`.
- Claude no Cowork (shell da nuvem sobre a pasta do PC): o push não sai dali — o Claude grava
  no clone e o usuário faz `pull`/`commit`/`push` no PowerShell. Nesse shell, `git` só com
  `--no-optional-locks` e nunca `pull`/`add`/`commit`: o comando deixa `.git/index.lock` que a
  sessão não consegue apagar, e o próximo commit no PC trava.
- **Nunca `git push --force`** — apagaria o trabalho enviado pelo outro analista.
- Conflito no `pull`: mostrar ao usuário as duas versões e deixar ele escolher.

## Skills: o GitHub é a fonte única

- As skills PPCI vivem em `sseg/skills/<nome>/SKILL.md`. **O repositório é a fonte**; a skill
  instalada na conta de cada analista é cópia.
- Ao mudar uma skill: gravar o `SKILL.md` completo em `sseg/skills/<nome>/` **no mesmo passo**
  (fim de linha LF) e lembrar o usuário de dar commit e push. Mudou na conta e não no repo =
  o outro analista não recebe.
- Depois de um `git pull` que traga mudança em `sseg/skills/`: rodar a skill
  `sseg-sincronizar-skills`. O pull sozinho **não instala** nada na conta — a skill só vale
  quando o analista salva o cartão de revisão.
- Nunca sobrescrever a pasta do repo com a versão da conta, nem o contrário, sem mostrar a
  diferença ao usuário e deixar ele escolher.
