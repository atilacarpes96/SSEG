# SSEG — Análises de PPCI (CBMRS/RS)

Fonte versionada do projeto **"SSEG - Análises"** do Claude: assistente técnico-normativo de
Segurança Contra Incêndio e Pânico para análise de PPCI, classificação de ocupações, cálculo
populacional, fiscalização e elaboração/revisão de notificações no âmbito do CBMRS/RS.

## Como o projeto funciona

![Fluxograma do SSEG: o analista trabalha no PC com o Claude Code, que lê o SOL pelo Chrome; skills, normas e documentos vão e voltam pelo GitHub; os arquivos do processo vão direto do PC ao servidor por SSH, nunca pelo GitHub; o servidor gera o Painel SSEG toda manhã.](sseg/painel/fluxograma.svg)

O analista decide; o Claude pesquisa, confere a norma no PDF oficial e redige. O GitHub (este repositório,
público) guarda skills, normas e documentos, para todos os analistas terem a mesma versão. Dados de processo
nunca passam por aqui: vão do PC direto ao servidor próprio. Este repositório é só a parte versionável do
projeto inteiro, e o fluxograma acima é o mesmo do Painel SSEG, que o servidor gera toda manhã.

O objetivo deste repositório é **poder levantar o projeto inteiro em outra máquina**: tudo que
está na base de conhecimento do projeto está em `sseg/`. Desde 02/10/2026 o repositório é a
**fonte** (skills, docs, scripts); o projeto do claude.ai e a conta de cada analista recebem cópia.

## Estrutura

```
CLAUDE.md        regras para o Claude Code (carrega o espelho das Instruções)
.claude/agents/  subagentes do Claude Code (localizador-normas, sol-leitor, revisor-cia)
sseg/
├── normas/      transcrições das normas, índice normativo, banco de notificações
│   ├── pdf/     os PDFs oficiais — o que se cita
│   ├── md/      conversão automática (anydoc) — só localiza, não fundamenta
│   └── base/    conversão verificada contra o PDF (normas_converter + normas_verificador)
├── painel/      página do Painel SSEG (o conteúdo vem de scripts/painel.py)
├── processos/   registro por processo analisado — SÓ LOCAL, fora do Git (ver abaixo)
├── scripts/     sseg.py, tabelas.py, painel.py e os demais (ver "Scripts")
│   ├── dados/   indice_normas.json, tabelas_conferidas.json
│   │   └── tabelas/   os recortes por grupo de ocupação
│   └── servidor/      criação e montagem do servidor 24/7
├── skills/      as skills PPCI — FONTE; a conta de cada analista recebe cópia
└── workflow/    como o trabalho é conduzido (arquitetura, travas, políticas)
```

## ⚠️ Dados de processo não entram no repositório

Este repositório é **público**. Registros de processo e dados de cliente — `sseg/processos/`,
CIA, JSON do SOL, plantas, prints — **não vão para o GitHub**:

- `sseg/processos/` está no `.gitignore`. Pode existir no clone local, mas nunca é enviado.
- Não usar `git add -f` nem tirar a pasta do `.gitignore`.
- Prints e plantas ficam fora do clone (ex.: `Carpes\print ppci`).
- Cada analista guarda seus registros numa pasta própria, fora do repo.

Regra também em `CLAUDE.md`, para o Claude de quem clonar.

## Levantar o projeto em outra máquina

1. **Clonar** este repositório.
2. **Criar um Projeto no Claude** e subir `sseg/` como base de conhecimento — ou apontar a
   *synced source* do projeto para este repo.
3. **Instruções do projeto:** colar no campo "Instruções" o texto inteiro de
   `sseg/workflow/instrucoes-projeto-espelho.md` (da seção `## Papel` em diante). Esse arquivo
   é o espelho do campo; ao mudar um, mudar o outro.
4. **Skills:** instalar na conta as skills de `sseg/skills/` com a skill
   `sseg-sincronizar-skills` (ou um `.zip` com `<nome>/SKILL.md` em Configurações > Capacidades >
   Skills). O repositório é a fonte; a da conta é cópia.
5. **Ler primeiro** `sseg/workflow/00-arquitetura-do-projeto.md`.
6. **Scripts:** Python 3 e Poppler (`pdftotext`, `pdftoppm`) no PATH. `sseg.py`, `tabelas.py`
   e `painel.py` só usam a biblioteca padrão; `normas_converter.py`, `normas_verificador.py` e
   `gerar_recortes.py` pedem `pip install pymupdf pymupdf4llm pillow numpy`. Rodam no Cowork, no
   PC do quartel (instalado em 03/10/2026, ver `CLAUDE.md`) e no servidor.

O que **não** vem no repo: os prints de `Carpes\print ppci`, os registros de processo e as
memórias do Claude. Os PDFs oficiais vêm (`sseg/normas/pdf/`). Ver
`sseg/workflow/repo-github-backup.md`.

## Scripts

```bash
cd sseg/scripts

# roteamento e leitura das tabelas de exigências
python3 tabelas.py rota    --situacao "existente regularizada" --area 3605.26 --altura 4.85
python3 tabelas.py linha   --fonte rt05 --tabela 6I.1 --divisao "I-1" --coluna "H<=6"
python3 tabelas.py divisao --fonte b --divisao "J-3"
python3 tabelas.py notas   --fonte b --tabela 6C

# apoio à análise (check do memorial, travas, render, diff)
python3 sseg.py --help

# regenerar os recortes de dados/tabelas/ a partir de tabelas_conferidas.json
python3 gerar_recortes.py
python3 gerar_recortes.py --conferir   # só compara; código 1 se divergir

# Painel SSEG: retrato do repositório + divergências automáticas (sem modelo)
python3 painel.py --saida /tmp/retrato --resumo
python3 painel_pedidos.py --pedidos <pasta> --saida <pasta> --simular   # trocas de texto da fila
```

⚠️ **Os scripts dependem do caminho, não só do arquivo.** `sseg.py` e `tabelas.py` montam o
caminho dos dados como `<pasta do script>/dados/...`: os dois JSON têm de estar em
`scripts/dados/` com os nomes `indice_normas.json` e `tabelas_conferidas.json`.

⚠️ **A fonte das tabelas é `dados/tabelas_conferidas.json`.** Os arquivos de `dados/tabelas/`
são recortes derivados, para ler um grupo de cada vez em vez dos ~180 KB inteiros. Corrigindo
uma célula, corrigir na fonte e rodar `gerar_recortes.py` — editar só o recorte não adianta,
a próxima geração sobrescreve. A exceção histórica era o `tab-00-indice.json`, hoje também
gerado a partir da fonte.

⚠️ **Contagem de medidas nunca sai de extração automática de PDF.** A transcrição serve para
localizar a tabela e a coluna; a contagem sai da imagem da tabela, lida célula a célula, e
quem aplica a nota ao caso concreto é o analista.
