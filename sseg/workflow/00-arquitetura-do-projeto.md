---
name: 00-arquitetura-do-projeto
description: Mapa de onde cada coisa mora neste projeto — Instruções, as 7 skills, docs de norma e docs de workflow — e a regra para decidir onde registrar algo novo
sources: [cowork]
---

# Como este projeto está organizado

Quatro camadas, cada uma com um papel. Registrar cada coisa na camada certa é o que evita
regra duplicada divergindo com o tempo.

| Camada | Onde | Carrega quando | Serve para |
|---|---|---|---|
| **Instruções** | campo "Instruções" do projeto | sempre, toda conversa, Chat e Cowork | doutrina inegociável e travas de erro |
| **Skills** | skills instaladas | quando a `description` casa com o pedido | procedimento: o passo a passo do que fazer |
| **`normas/`** | docs do projeto | busca semântica, quando o assunto aparece | conhecimento: texto das RTs, tabelas, banco de notificações |
| **`workflow/`** | docs do projeto | busca semântica | registro: casos concretos, catálogos, fatos do setup |

Visão de tudo isso numa página, com a fila de pedidos de alteração: Painel SSEG
(ver `workflow/painel-do-projeto.md`). O painel é um retrato; a fonte continua sendo cada camada.

## O que está nas Instruções (sempre ativo)

Papel e ordem de raciocínio · proporção do esforço · ordem de entrega · hierarquia das fontes ·
vigência por data de protocolo · proibição de alucinação normativa e fundamentação reversa ·
não presumir · obrigação × faculdade × recomendação · divisão de trabalho com o usuário · as
quatro travas de erro (altura, contagem de medidas, sugestões do SOL, definição antes de
geometria) · escopo de processo · onde procurar primeiro. Texto exato em
`workflow/instrucoes-projeto-espelho.md`.

## As skills (7, em 02/10/2026)

Ficam na conta do Claude; cópia de backup em `sseg/skills/` do repositório.

- **`ppci-abertura-sessao`** — abrir a sessão: pedir a pasta `Carpes` uma vez, abrir o SOL no
  Chrome direto na caixa Análise técnica, parar no login; "o próximo da lista" pela planilha
  Distribuição Análise (o de mais dias em análise).
- **`ppci-analise-processo`** — pipeline do print à CIA: data de protocolo, registro pela API,
  `sseg.py check`, definidora, tabela de exigências, planta × memorial, normas do campo 4,
  população e laudo, comparação com a análise anterior; "atualizar a pasta" no fim.
- **`ppci-notificacao-cia`** — redigir e revisar inconformidades: banco primeiro, estrutura
  padrão, REITERO, cláusula de salvaguarda, corte do que é de vistoria, checklist de revisão.
- **`sol-cbmrs-navegador`** — operar o SOL: ler o processo pela API, lançar no campo "Outros"
  só quando pedido, limite da caixa "Especificar", PDF da página.
- **`ppci-revisao-cia`** — revisão final da CIA em conversa nova: `sseg.py revisar-cia` e
  fundamentação reversa de cada exigência no PDF oficial.
- **`ppci-incorporar-norma`** — norma nova na base: PDF, conversão anydoc, transcrição
  comentada e todos os índices dependentes, no projeto e no clone.
- **`passar-contexto`** — bloco de passagem para continuar o trabalho em outra conversa.

## Os scripts

`scripts/sseg.py`, `scripts/tabelas.py` + `scripts/dados/`. Rodam só onde há sandbox (Cowork).
Fazem o trabalho determinístico — roteamento de tabela, conferência de normas, travas de
consistência, render/PDF da página, diff entre análises, revisão da CIA — e nunca criam
fundamento nem contam medidas por extração de PDF. Sem sandbox, o passo a passo escrito nas
skills produz o mesmo resultado.

## Onde registrar algo novo

- É uma **regra que vale sempre**, mesmo sem gatilho? → Instruções (e o espelho).
- É um **passo a passo** de uma tarefa específica? → skill (e a cópia em `sseg/skills/`).
- É **conteúdo de norma** (item, tabela, modelo de notificação validado)? → `normas/`.
- É um **caso concreto**, uma leitura conferida à mão, um catálogo de tela, um fato do
  setup do usuário? → `workflow/`.
- É **preferência de como trabalhar** (formato, navegador, modelo)? → memória do projeto.

Uma linha de tabela de exigências lida na imagem entra em **dois** lugares: o registro em
`workflow/ocupacao-definidora-e-tabelas-exigencias.md` e o dado legível por máquina em
`scripts/dados/tabelas/` (o arquivo do grupo; `tabelas_conferidas.json` é a origem).
