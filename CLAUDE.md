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
- **Nunca `git push --force`** — apagaria o trabalho enviado pelo outro analista.
- Conflito no `pull`: mostrar ao usuário as duas versões e deixar ele escolher.
