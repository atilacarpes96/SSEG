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
├── processos/   🚫 NÃO versionado desde 27/09/2026 (dados de cliente) — ver abaixo
├── scripts/     sseg.py, tabelas.py, gerar_recortes.py
│   └── dados/   indice_normas.json, tabelas_conferidas.json
│       └── tabelas/   os 30 recortes por grupo
├── skills/      FONTE das skills PPCI (a conta de cada analista recebe cópia instalada)
└── workflow/    como o trabalho é conduzido
```

As três camadas de `normas/` e o que cada uma pode fundamentar estão no `sseg/normas/README.md`.

## 🔴 Dados de processo não vão para o GitHub (regra de 27/09/2026)

Em 27/09/2026 constatou-se que o repositório estava **público** (clone anônimo funcionou) e que
`sseg/processos/` expunha dados reais dos processos: razão social, CNPJ, endereço, nome do RT e
do responsável pelo uso e as inconformidades de cada CIA. Contraria a regra do projeto de que
documento de PPCI não sai da máquina.

**Regra:**

- **Nada que identifique processo, cliente, RT ou responsável vai para o repo**: `processos/`,
  `print ppci`, CIA, JSON da API do SOL, plantas. O repo guarda só o que é reutilizável:
  normas, banco de modelos, scripts, tabelas, skills e workflow.
- `sseg/processos/` está no `.gitignore`. Os registros continuam **no projeto do Claude**
  (privado), que é onde as skills os leem (`processos/<código>.md`).
- **Cópia de arquivo dos registros: pasta "SSEG - Processos (privado)" no Google Drive**
  do Átila, não compartilhada.
- **O repositório é público, por decisão do Átila (02/10/2026):** os processos saíram do repo,
  e o que fica nele (normas, modelos, scripts, skills, workflow) pode ser público.
- Exemplo em doc de norma, workflow ou banco (ex.: "caso Encruzilhada do Sul") pode citar
  cidade e tipo de ocupação; **não** razão social, CNPJ, endereço nem nome de pessoa.

Os arquivos antigos continuam no **histórico** do git mesmo depois de removidos e, com o repo
público, podem ser lidos por quem abrir commits antigos. Apagar do histórico exige
`git filter-repo` e só se faz se o Átila decidir.

## ⚠️ O projeto anda na frente do repo — sincronizar os dois (24/09/2026)

Os docs são editados **no projeto do Claude** (`project_write`) ao longo das análises, e o repo
só recebe o que for gravado no clone e enviado por push. Em 24/09/2026 o GitHub estava parado
no commit de 15/09/2026 enquanto o projeto tinha uma semana de trabalho a mais: 8 registros de
processo ausentes, `sseg.py`, índices, transcrições e duas correções de tabela só no projeto.

**Regra (revista em 05/10/2026):** o **repositório é a fonte** — é o que o `CLAUDE.md` manda desde
que o projeto do claude.ai passou a receber o GitHub como *synced source*. No Claude Code, grava-se
direto no clone; no Cowork, grava-se no clone (`device_commit_files`) e o push é do PC. Doc gravado
só no projeto (`project_write`) fica fora do repositório e se perde na próxima sincronização.
*Histórico:* de 24/09 a 02/10/2026 a regra era a inversa (o projeto era o canônico), porque o
clone vivia atrasado; o atraso acabou quando o servidor passou a ter a cópia viva.

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

Avisos de `LF will be replaced by CRLF` (ou, depois do `.gitattributes`, `CRLF will be replaced by LF`) são normais no Windows e não quebram nada.

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

## ⭐ Skills: o GitHub é a fonte única (decisão de 02/10/2026)

**Exceção à regra de que o projeto é o canônico:** para as **skills**, a fonte é
`sseg/skills/<nome>/SKILL.md` no repo. A skill instalada na conta é cópia — antes era o
contrário (a conta valia, o repo era backup), e o colega que dava `git pull` não recebia nada.

**Por que o pull não basta:** skill de conta só muda quando o analista salva o cartão de
revisão. Nenhum `git pull` instala skill. Por isso o fluxo tem dois lados:

- **Quem muda a skill:** grava o `SKILL.md` completo em `sseg/skills/<nome>/` no mesmo passo
  (LF), e dá commit e push do PC.
- **Quem recebe:** dá `git pull` e diz "atualiza as skills pelo repositório" (skill
  `sseg-sincronizar-skills`). O Claude compara cada `SKILL.md` do clone com o da conta e
  apresenta um cartão de revisão por skill diferente; o analista salva.

**Fim de linha:** o repo tem `.gitattributes` com `* text=auto eol=lf` desde 02/10/2026. No PC
(Windows, `autocrlf`) estava tudo certo; o problema era o `git` rodado pelo shell do Cowork, que
via os arquivos CRLF do Windows e acusava ~100 arquivos "modificados" sem mudança nenhuma. Com o
`.gitattributes`, o Cowork passa a enxergar só as mudanças reais.

**Git pelo shell do Cowork:** só com `--no-optional-locks` e só leitura (`status`, `log`, `diff`).
`pull`/`add`/`commit` de lá deixam `.git/index.lock`, que a sessão não consegue apagar sem
permissão de exclusão — aconteceu em 02/10/2026 e travaria o próximo commit no PC.

## O que NÃO está versionado

- **Os registros de processo (`processos/`)** — desde 27/09/2026, por conter dados de
  cliente. Ficam no projeto do Claude e na pasta do Drive (ver a regra acima).
- **As memórias do Claude** — o que vale para o trabalho vira doc aqui.
- **Os prints de `Carpes\print ppci`** — ver [[pasta-print-ppci-local]].
- **O campo "Instruções" do projeto** — tem espelho em [[instrucoes-projeto-espelho]], que
  precisa ser editado junto com o campo.

✅ Os **PDFs oficiais** passaram a ser versionados em `sseg/normas/pdf/` em 15/09/2026 — antes
só existiam na pasta local. ✅ As **skills** também, em `sseg/skills/` — e desde 02/10/2026 o
repo é a **fonte** delas (ver a seção acima).

## Levantar o projeto em outra máquina

1. `git clone` do repo.
2. Criar/abrir um Projeto no Claude e apontar a *synced source* para ele, ou subir `sseg/`
   como base de conhecimento.
3. Colar em "Instruções" o texto inteiro de [[instrucoes-projeto-espelho]].
4. Instalar as skills na conta com a skill `sseg-sincronizar-skills` (cartões de revisão a
   partir de `sseg/skills/`).
5. Para rodar os scripts: **Python 3** e **Poppler** no PATH (instalados no PC do quartel em
   03/10/2026; passo a passo no `CLAUDE.md`).
6. As normas vêm junto agora; os prints e os registros de processo ficam de fora (os
   registros estão no Drive, pasta "SSEG - Processos (privado)").

O passo a passo detalhado está no `README.md` da raiz do repo.
