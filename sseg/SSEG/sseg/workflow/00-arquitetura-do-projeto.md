---
name: 00-arquitetura-do-projeto
description: Mapa de onde cada coisa mora neste projeto — Instruções, skills, docs de norma e docs de workflow — e a regra para decidir onde registrar algo novo
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

## O que está nas Instruções (sempre ativo)

Papel e ordem de raciocínio · hierarquia das fontes · vigência por data de protocolo ·
proibição de alucinação normativa e fundamentação reversa · não presumir · obrigação ×
faculdade × recomendação · divisão de trabalho com o usuário · as quatro travas de erro
(altura, contagem de medidas, sugestões do SOL, definição antes de geometria) · escopo de
processo · onde procurar primeiro.

## As skills

- **`ppci-analise-processo`** — pipeline do print à CIA: arquivar, extrair o registro
  estruturado, conferir definidora, rotear a tabela do Anexo B, conferir normas do campo 4,
  analisar laudo de inviabilidade, comparar com a análise anterior.
- **`ppci-notificacao-cia`** — redigir e revisar inconformidades: banco primeiro, estrutura
  padrão, REITERO, cláusula de salvaguarda, checklist de revisão.
- **`sol-cbmrs-navegador`** — operar o SOL: zoom, modal "Reprovar medida", leitura do
  "Especificar", geração do PDF da página.

## Os scripts

`scripts/sseg.py` + `scripts/dados/`. Rodam só onde há sandbox (Cowork). Fazem o trabalho
determinístico — roteamento de tabela, conferência de normas, travas de consistência,
render/PDF da página, diff entre análises — e nunca criam fundamento nem contam medidas por
extração de PDF. Sem sandbox, o passo a passo escrito nas skills produz o mesmo resultado.

## Onde registrar algo novo

- É uma **regra que vale sempre**, mesmo sem gatilho? → Instruções.
- É um **passo a passo** de uma tarefa específica? → skill.
- É **conteúdo de norma** (item, tabela, modelo de notificação validado)? → `normas/`.
- É um **caso concreto**, uma leitura conferida à mão, um catálogo de tela, um fato do
  setup do usuário? → `workflow/`.

Uma linha de tabela do Anexo B lida na imagem entra em **dois** lugares: o registro em
`workflow/ocupacao-definidora-e-tabelas-exigencias.md` e o dado legível por máquina em
`scripts/dados/tabelas_conferidas.json`.
