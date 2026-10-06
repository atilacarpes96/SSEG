# Regras do repositório SSEG para o Claude

Este repositório é **público** e compartilhado entre analistas (cada um com seu próprio Claude).

## O que este projeto é

Assistente técnico-normativo de Segurança Contra Incêndio e Pânico do CBMRS/RS: análise de
PPCI no SOL-CBMRS, classificação de ocupações, cálculo populacional, fiscalização e redação de
notificações da CIA. Usuário: Sd Carpes (Átila), analista do 6º BBM. Responder em português.

## Doutrina (sempre ativa)

As regras de raciocínio, entrega, hierarquia das fontes, vigência por data de protocolo,
proibição de alucinação normativa e as travas de erro são as **Instruções do projeto**, cujo
texto único está no espelho abaixo. Não copiar esse texto para cá: o espelho é a fonte, e cópia
a mais já divergiu antes. Os caminhos citados nele (`normas/`, `workflow/`) são relativos a
`sseg/`.

@sseg/workflow/instrucoes-projeto-espelho.md

## Mapa — onde cada coisa mora

| O quê | Onde | Ler quando |
|---|---|---|
| Arquitetura e onde registrar algo novo | `sseg/workflow/00-arquitetura-do-projeto.md` | dúvida sobre onde gravar |
| Lições de análises anteriores | `sseg/workflow/casos-referencia.md` | ao começar um processo |
| Banco de ~80 notificações validadas | `sseg/normas/banco-notificacoes-padrao.md` | antes de redigir qualquer notificação |
| Índice normativo e vigência | `sseg/normas/00-indice-normativo.md` | antes de citar norma |
| Transcrição comentada de cada norma | `sseg/normas/<rt>.md` | quando o assunto é daquela norma |
| Busca literal (provisório, nunca fundamenta) | `sseg/normas/md/` | só para localizar trecho |
| PDF oficial (fundamenta) | `sseg/normas/pdf/` | sempre antes de citar item na CIA |
| Tabelas de exigências conferidas | `sseg/scripts/dados/` (fonte: `tabelas_conferidas.json`) | roteamento de tabela |
| Política de modelo e custo | `sseg/workflow/politica-modelo-e-custo.md` | antes de delegar a subagente |
| Registro local dos processos | `sseg/processos/` (fora do Git) | processo em andamento |
| Prints, CIA, JSON do SOL | `C:\Users\55519\Desktop\Carpes\print ppci\<processo>\` | análise e revisão |

Ler só o arquivo de que a tarefa precisa — não abrir a base inteira.

## Skills

As skills PPCI estão em `sseg/skills/<nome>/SKILL.md`. Quando o pedido casar com uma delas,
**ler o SKILL.md inteiro antes de começar** e seguir o passo a passo:

| Pedido do usuário | Skill |
|---|---|
| "vou começar a analisar um PPCI", "o próximo da lista" | `ppci-abertura-sessao` |
| código de processo A000... ou print de processo | `ppci-analise-processo` |
| redigir ou revisar uma notificação | `ppci-notificacao-cia` |
| minuta ou ata de consulta técnica (FACT), despacho de recurso | `ppci-minuta-despacho` |
| ler o processo pela API, lançar no campo "Outros", PDF da página | `sol-cbmrs-navegador` |
| "revisa a CIA", "revisão final" | `ppci-revisao-cia` (pelo subagente `revisor-cia`) |
| norma nova para a base | `ppci-incorporar-norma` |
| levar uma skill da conta ao repo, ou o contrário | `sseg-sincronizar-skills` |
| "passa o contexto", "vou continuar na outra conversa" | `passar-contexto` |

As skills foram escritas para o Cowork. No Claude Code, traduzir:

- `device_bash`, `device_stage_files`, `device_commit_files` → o terminal e os arquivos locais;
  não há nada a copiar entre nuvem e PC.
- "gravar no projeto" / `project_write` / `Projects` → gravar o arquivo em `sseg/` neste clone.
  O repositório é a fonte; o projeto do claude.ai recebe pelo GitHub sincronizado.
- "trazer os scripts do clone" → rodar direto de `sseg/scripts/`.
- Chrome (SOL): usar a integração do Claude in Chrome com o Claude Code. A senha do SOL é
  sempre digitada pelo usuário.

## Subagentes (`.claude/agents/`)

A divisão segue `sseg/workflow/politica-modelo-e-custo.md`: **modelo leve só onde nenhuma
escolha normativa acontece.** Escolher modelo do banco, enquadrar ocupação, decidir se uma
exigência procede — isso fica no agente principal, nunca no subagente leve.

- `localizador-normas` (Haiku) — devolve trechos literais com arquivo e linha/página. Não
  conclui, não diz que algo "não existe": a decisão é do principal.
- `sol-leitor` (Haiku) — lê páginas do SOL no Chrome e devolve só o resumo pedido (vários
  processos, todas as abas). Só navega e lê: nunca analisa, reprova, salva ou distribui.
- `revisor-cia` (Sonnet) — revisão final da CIA de fora do raciocínio que a produziu, conforme
  `ppci-revisao-cia`. Opus só nos casos que a skill lista.

## Hooks (`.claude/settings.json`, desde 05/10/2026)

Regras deste arquivo que acontecem sozinhas no Claude Code (`.claude/hooks/sseg_hooks.py`):

- **Ao abrir a sessão:** `git pull`; avisa se vieram skills ou Instruções novas e se há mudança sem commit.
- **Antes de `git commit`:** barra o add forçado e arquivo de processo (`sseg/processos/`, CIA, `textos.json`,
  código A000... no nome) e roda `python3 sseg/scripts/testar.py`; teste falhando, o commit não sai.
- **Antes de editar o banco de notificações:** barra a alteração do texto de um modelo validado
  (a ressalva vai em linha própria). Mudança validada pela chefia: `SSEG_BANCO_LIBERADO=1`.
- **Depois de editar um `SKILL.md`:** gera `.skills-zip/<nome>.zip` e lembra de instalar na conta.
- **No fim do turno:** lembra de commit quando há mudança parada há mais de 20 minutos.

Revisar ou desligar em `/hooks`.

## Pré-requisitos no PC

Python 3 e Poppler (`pdftotext`, `pdftoppm`) no PATH — sem eles, os scripts e a conferência no
PDF não rodam. `sseg.py` só usa a biblioteca padrão; `normas_converter.py`,
`normas_verificador.py` e `gerar_recortes.py` pedem `pip install pymupdf pymupdf4llm pillow numpy`.

No Windows (instalado no PC do quartel em 03/10/2026):

- `winget install -e --id Python.Python.3.12 --scope user` e `winget install -e --id oschwartz10612.Poppler`.
- `python3` cai no atalho da Microsoft Store: copiar `python.exe` como `python3.exe` na pasta do Python.
- O `pdftotext` que vem com o Git é Xpdf (sem acento, sem `pdftoppm`) e fica antes no PATH do
  Git Bash: pôr a pasta `bin` do Poppler e a do Python no início do PATH em `~/.bashrc`.
- `setx PYTHONUTF8 1`: sem isso o verificador lê a saída UTF-8 do `pdftotext` como cp1252 e quebra.
- Teste: converter um PDF de `normas/pdf/` com `normas_converter.py` e comparar com `normas/base/`.

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
- **Claude Code no PC:** git roda normalmente no terminal local — `pull`, `add`, `commit` e
  `push` podem ser feitos pelo próprio Claude, sempre com a conferência do `git status` acima.
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
- No Claude Code não há `propose_skills`: o analista sobe a skill em claude.ai > Configurações >
  Capacidades > Skills > Substituir, com um `.zip` contendo `<nome>/SKILL.md`. **Não gerar o zip
  com `Compress-Archive`** (Windows PowerShell 5.1): grava o caminho com `\` e o claude.ai
  recusa com "Zip file contains path with invalid characters" (03/10/2026). Usar Python:
  `zipfile.ZipFile("<nome>.zip","w").write("sseg/skills/<nome>/SKILL.md", "<nome>/SKILL.md")`.
