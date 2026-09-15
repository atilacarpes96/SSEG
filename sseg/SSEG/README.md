# SSEG — Análises de PPCI (CBMRS/RS)

Backup versionado do projeto **"SSEG - Análises"** do Claude: assistente técnico-normativo de
Segurança Contra Incêndio e Pânico para análise de PPCI, classificação de ocupações, cálculo
populacional, fiscalização e elaboração/revisão de notificações no âmbito do CBMRS/RS.

O objetivo deste repositório é **poder levantar o projeto inteiro em outra máquina**: tudo que
está na base de conhecimento do projeto está em `sseg/`.

## Estrutura

```
sseg/
├── normas/      transcrições das normas e o índice normativo (00-indice-normativo.md)
├── processos/   registro por processo analisado (<CÓDIGO>.md)
├── scripts/     sseg.py, tabelas.py, gerar_recortes.py
│   └── dados/   indice_normas.json, tabelas_conferidas.json
│       └── tabelas/   os 30 recortes por grupo de ocupação
├── skills/      cópia de backup das 4 skills PPCI da conta do Claude
└── workflow/    como o trabalho é conduzido (arquitetura, travas, políticas)
```

## Levantar o projeto em outra máquina

1. **Clonar** este repositório.
2. **Criar um Projeto no Claude** e subir `sseg/` como base de conhecimento — ou apontar a
   *synced source* do projeto para este repo.
3. **Instruções do projeto:** colar no campo "Instruções" o texto inteiro de
   `sseg/workflow/instrucoes-projeto-espelho.md` (da seção `## Papel` em diante). Esse arquivo
   é o espelho do campo; ao mudar um, mudar o outro.
4. **Skills:** recriar as 4 de `sseg/skills/` na conta do Claude
   (`ppci-abertura-sessao`, `ppci-analise-processo`, `ppci-notificacao-cia`,
   `sol-cbmrs-navegador`). A cópia daqui é backup — a que vale é a da conta.
5. **Ler primeiro** `sseg/workflow/00-arquitetura-do-projeto.md`.
6. **Scripts:** precisam de **Python 3**, sem dependência externa. Foram feitos para rodar no
   ambiente do Cowork; o PC do quartel não tem Python instalado.

O que **não** vem no repo: os PDFs oficiais de `Carpes\Normas`, os prints de
`Carpes\print ppci` e as memórias do Claude. O repo guarda as **transcrições**, não os
originais — copiar a pasta `Carpes` à parte, ou transcrever de novo conforme a necessidade.
Ver `sseg/workflow/repo-github-backup.md`.

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
