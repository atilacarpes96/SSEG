---
name: repo-github-backup
description: O repositório atilacarpes96/SSEG como backup versionado do projeto — estrutura, clone no PC do quartel, o que está e o que NÃO está versionado, e como levantar o projeto em outra máquina
sources: [cowork]
---

# Repositório SSEG — backup do projeto

> Registrado em **14/09/2026**, quando o repo foi completado. Objetivo declarado: **backup de
> tudo que está no projeto do Claude**, para poder rodar o projeto em outra máquina.

## Onde

| | |
|---|---|
| Remoto | `atilacarpes96/SSEG`, branch `main` |
| Clone no PC do quartel | `C:\Users\55519\Desktop\Carpes\SSEG` |
| Sincronização | o projeto do Claude tem o repo como *synced source* |

**Os documentos ficam numa subpasta `sseg/` dentro do repo**, não na raiz. A raiz tem só o
`README.md` e a `sseg/`.

```
sseg/
├── normas/      transcrições e índice normativo
├── processos/   registro por processo (<CÓDIGO>.md)
├── scripts/     sseg.py, tabelas.py
│   └── dados/   indice_normas.json, tabelas_conferidas.json
│       └── tabelas/   os 30 recortes por grupo
├── skills/      cópia das skills PPCI da conta do Claude
└── workflow/    como o trabalho é conduzido
```

## ⚠️ Os scripts dependem do caminho, não só do arquivo

`sseg.py` (linha 48) e `tabelas.py` (linha 33) montam o caminho dos dados como
`<pasta do script>/dados/...`. Os arquivos **têm de estar em `scripts/dados/`** com os nomes
`indice_normas.json` e `tabelas_conferidas.json`.

Isso já quebrou uma vez: no primeiro envio ao GitHub os dois subiram achatados na raiz de
`scripts/`, como `dados_indice_normas.json` e `dados_tabelas_conferidas.json`, e os scripts
falhavam ao abrir. Corrigido em **15/09/2026**. Ao mexer na estrutura, conferir os dois
caminhos antes de commitar.

## Os arquivos de `scripts/dados/tabelas/` são derivados

Os 28 `tab-b-*.json` / `tab-rt05-*.json`, mais o `linhas-conferidas.json`, são **recortes do
`tabelas_conferidas.json`** — existem para poder ler um grupo de cada vez em vez de carregar
os 191 KB inteiros. O `tab-00-indice.json` é o único escrito à mão (traz o mapa
divisão → arquivo/tabela/bloco e a regra de contagem).

Consequência: **a fonte é o `tabelas_conferidas.json`**. Corrigindo uma célula, corrigir lá e
regerar os recortes — nunca editar só o recorte, que a próxima geração sobrescreve.

## O que NÃO está versionado

- **As memórias do Claude** — o que vale para o trabalho vira doc aqui; o resto é pessoal e
  fica fora de propósito.
- **Os PDFs oficiais** de `Carpes\Normas` e os prints de `Carpes\print ppci` — ver
  [[pasta-normas-local]] e [[pasta-print-ppci-local]]. O repo guarda as **transcrições**, não
  os originais.
- **O campo "Instruções" do projeto** — tem espelho em [[instrucoes-projeto-espelho]], que
  precisa ser editado junto com o campo.

✅ **As skills** (`ppci-analise-processo`, `ppci-notificacao-cia`, `sol-cbmrs-navegador`,
`ppci-abertura-sessao`) passaram a ser versionadas em `sseg/skills/` em **15/09/2026**. A cópia
do repo é backup: a skill que vale é a da conta do Claude, então ao editar uma skill, atualizar
também a cópia daqui.

## Levantar o projeto em outra máquina

1. `git clone` do repo.
2. Criar/abrir um Projeto no Claude e apontar a *synced source* para ele, ou subir `sseg/`
   como base de conhecimento.
3. Colar em "Instruções" o texto inteiro de [[instrucoes-projeto-espelho]].
4. Recriar as skills a partir de `sseg/skills/`.
5. Para rodar os scripts: **Python 3** (não está instalado no PC do quartel — eles foram
   feitos para rodar no ambiente do Cowork).
6. Os PDFs das normas e os prints não vêm no repo: copiar a pasta `Carpes` à parte, ou seguir
   sem eles e transcrever de novo conforme a necessidade.

O passo a passo detalhado está no `README.md` da raiz do repo.

## Estado do login

O login do GitHub no PC do quartel ainda não foi feito — `gh auth login`, ou a janela que o
Git abre no primeiro `push`. Sem isso, commit funciona e push não.
