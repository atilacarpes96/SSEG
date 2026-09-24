---
name: repo-github-backup
description: O repositório atilacarpes96/SSEG como backup versionado do projeto — estrutura, o que está e o que NÃO está versionado, como atualizar (PowerShell, do PC) e as armadilhas que já custaram retrabalho
sources: [cowork]
---

# Repositório SSEG — backup do projeto

> Completado em **15/09/2026**, commit `233ce1a`. Objetivo declarado: **backup de tudo que
> está no projeto do Claude**, para poder rodar o projeto em outra máquina.

## Onde

| | |
|---|---|
| Remoto | `atilacarpes96/SSEG`, branch `main` |
| Clone no PC do quartel | `C:\Users\55519\Desktop\Carpes\SSEG` |
| Sincronização | o projeto do Claude tem o repo como *synced source* |

**Os documentos ficam numa subpasta `sseg/` dentro do repo**, não na raiz.

```
sseg/
├── normas/      transcrições comentadas e o índice normativo
│   ├── pdf/     os PDFs oficiais — fonte de citação
│   └── md/      conversões do anydoc — índice de busca, NÃO fundamenta
├── processos/   registro por processo (<CÓDIGO>.md)
├── scripts/     sseg.py, tabelas.py, gerar_recortes.py
│   └── dados/   indice_normas.json, tabelas_conferidas.json
│       └── tabelas/   os 30 recortes por grupo
├── skills/      cópia das skills PPCI da conta do Claude
└── workflow/    como o trabalho é conduzido
```

As três camadas de `normas/` e o que cada uma pode fundamentar estão no `sseg/normas/README.md`.

## ⚠️ O projeto anda na frente do repo — sincronizar os dois (24/09/2026)

Os docs são editados **no projeto do Claude** (`project_write`) ao longo das análises, e o repo
só recebe o que for gravado no clone e enviado por push. Em 24/09/2026 o GitHub estava parado
no commit de 15/09/2026 enquanto o projeto tinha uma semana de trabalho a mais: 8 registros de
processo ausentes, `sseg.py`, índices, transcrições e duas correções de tabela só no projeto.

**Regra:** ao fim de sessão que alterou doc do projeto, gravar os mesmos arquivos no clone e
dar push. **O projeto é a versão canônica** — nunca usar o arquivo do clone como base para
editar um doc que existe no projeto.

## ⭐ Como atualizar — PowerShell, do PC

**O push não sai do ambiente do Cowork:** o proxy recusa o repositório por ele não estar no
conjunto autorizado da sessão. Tentado várias vezes em 15/09/2026, por git e por API. O Cowork
grava os arquivos no clone; o envio é do PC. (Leitura funciona: `git clone` público do repo
roda no Cowork, útil para comparar o que está no GitHub.)

```powershell
cd C:\Users\55519\Desktop\Carpes\SSEG
git pull
git add -A
git commit -m "<o que mudou>"
git push
```

`git add -A` pega arquivo novo, alterado, apagado e pasta nova — não precisa listar nada.

⚠️ **O PC usa PowerShell, não Prompt de Comando.** Sintaxe de `cmd` não roda ali: nada de
`cd /d`, `del a b` (é `Remove-Item a, b`) ou `rmdir /s /q` (é `Remove-Item -Recurse -Force`).
E `echo x > arquivo` no PowerShell grava com BOM — para `.gitignore`, usar
`Set-Content -Path .gitignore -Value "..." -Encoding ascii`, senão o git ignora a primeira linha.

✅ **Login e identidade, resolvidos em 15/09/2026:** o login do GitHub foi feito pela janela que
o Git abre no primeiro push, e a identidade está configurada como `--global`
(`atilacarpes@icloud.com` / `Atila Carpes`). Antes disso todo commit morria em
*"Author identity unknown"* — e o `git push` respondia *"Everything up-to-date"*, porque commit
nenhum tinha sido criado. Se voltar a aparecer, é identidade, não autenticação.

Avisos de `LF will be replaced by CRLF` são normais no Windows e não quebram nada.

## 🚫 Upload pelo site: como se perde a estrutura

Em 15/09/2026 a pasta `SSEG` inteira foi arrastada para a tela de upload do GitHub estando
dentro de `sseg/`, e o resultado foi **`sseg/SSEG/`** — uma duplicata aninhada de 84 arquivos,
com o `.bundle` e o `.zip` de anexo junto, enquanto as pastas originais continuavam com os
arquivos velhos. Corrigido por `git pull` + `Remove-Item -Recurse -Force sseg\SSEG` + commit.

Duas lições: **upload nunca apaga** (arquivo que mudou de lugar fica duplicado) e a pasta de
destino é a que está aberta na hora. Preferir sempre os comandos.

A pasta `Claude outputs`, que aparece no clone quando se baixa anexo do chat, está no
`.gitignore` — sem isso o `git add -A` sobe bundle e zip.

## Os arquivos de `scripts/dados/tabelas/` são derivados

Os 28 `tab-b-*.json` / `tab-rt05-*.json`, mais `linhas-conferidas.json` e `tab-00-indice.json`,
são **recortes do `tabelas_conferidas.json`** — existem para ler um grupo por vez em vez dos
~180 KB inteiros.

**A fonte é o `tabelas_conferidas.json`.** Corrigindo uma célula, corrigir lá e rodar
`python3 scripts/gerar_recortes.py` (`--conferir` compara sem gravar). Editar só o recorte não
adianta: a próxima geração sobrescreve.

🔴 **Já aconteceu (corrigido em 24/09/2026):** as linhas "Chuveiros Automáticos" da 6C
(16/09/2026) e "Alarme de Incêndio" da 6A (21/09/2026), no Anexo B, foram acrescentadas **só nos
recortes** `tab-b-C.json` e `tab-b-A.json`. Passadas para a fonte (chave `_correcoes_na_fonte`
do `tabelas_conferidas.json`) e recortes regenerados.

## O que NÃO está versionado

- **As memórias do Claude** — o que vale para o trabalho vira doc aqui.
- **Os prints de `Carpes\print ppci`** — ver [[pasta-print-ppci-local]].
- **O campo "Instruções" do projeto** — tem espelho em [[instrucoes-projeto-espelho]], que
  precisa ser editado junto com o campo.

✅ Os **PDFs oficiais** passaram a ser versionados em `sseg/normas/pdf/` em 15/09/2026 — antes
só existiam na pasta local. ✅ As **skills** também, em `sseg/skills/`; a cópia do repo é
backup, a que vale é a da conta, então ao editar uma skill, atualizar a cópia daqui.

## Levantar o projeto em outra máquina

1. `git clone` do repo.
2. Criar/abrir um Projeto no Claude e apontar a *synced source* para ele, ou subir `sseg/`
   como base de conhecimento.
3. Colar em "Instruções" o texto inteiro de [[instrucoes-projeto-espelho]].
4. Recriar as skills a partir de `sseg/skills/`.
5. Para rodar os scripts: **Python 3** (não está instalado no PC do quartel — eles foram
   feitos para rodar no ambiente do Cowork).
6. As normas vêm junto agora; só os prints de processo ficam de fora.

O passo a passo detalhado está no `README.md` da raiz do repo.
