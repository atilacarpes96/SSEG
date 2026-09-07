# RT CBMRS nº 05, Parte 07/2025 — Edificações e Áreas de Risco de Incêndio Existentes

Última verificação: **02/09/2026** — vigência, definições e seção 6.2 conferidas na transcrição literal do PDF oficial. Ver [[00-indice-normativo]].

## Identificação
- **Norma:** Resolução Técnica CBMRS nº 05, Parte 07/2025 (versão corrigida) — "Processo de Segurança Contra Incêndio: Edificações e Áreas de Risco de Incêndio Existentes"
- **Vigência: 1º de fevereiro de 2025** (Art. 2º, conferido em 02/09/2026). ⚠️ O índice do projeto registrava 01/01/2025 — **corrigido**.
- **Hierarquia:** nível 3 (RT do CBMRS) — categoria "Procedimentos Administrativos e Técnicos"
- **Link oficial:** https://www.bombeiros.rs.gov.br/upload/arquivos/202502/19184504-resolucao-tecnica-cbmrs-n-05-parte-07-2025-versao-corrigida.pdf

## Regra de aplicação

- **"existente regularizada"** → medidas exigidas por **esta RT (05, Parte 07/2025)**;
- **"existente não regularizada"** ou **"a construir"** → **Decreto 51.803/2014**, Anexo B ([[decreto-51803-2014]]).

⚠️ As duas fontes têm tabelas com numeração e colunas parecidas, mas **não são a mesma tabela**. Nunca reaproveitar linha do Anexo B como se fosse da RT 05 P07.

## ✅ Definições e comprovação de existência (transcrição literal, 02/09/2026)

**Item 4.1, alínea "c" — existente regularizada:** *"é aquela detentora de habite-se ou projeto protocolado na Prefeitura Municipal ou PPCI/PSPCI protocolado no CBMRS ou documentação emitida por órgão público que comprove sua existência, com área e atividade da época, **até 26 de dezembro de 2013**, nos termos desta Resolução Técnica."*

**Item 6.2.1** — ⚠️ **não é o que o projeto registrava.** O texto é a lista de documentos:

> "São consideradas edificações e áreas de risco de incêndio existentes regularizadas, as que
> possuam **um dos seguintes documentos, emitidos até 26 de dezembro de 2013**: **a)**
> habite-se; **b)** projeto protocolado na Prefeitura Municipal; **c)** PPCI na forma completa
> ou PSPCI, protocolado no CBMRS; **d)** quaisquer documentos expedidos por órgãos públicos,
> constando área e atividade da época; **e)** Certidão de Preservação do Imóvel [...]"

**Item 6.2.2** — existentes **não** regularizadas: já construídas, que não cumprem os requisitos acima, desde que comprovem a existência do prédio no endereço anteriormente a 26/12/2013 por registros fotográficos, documentos históricos, quaisquer documentos públicos ou outros registros mediante aprovação do CBMRS.

**Item 6.2.1.2.1** — é **aqui** que estão os requisitos de equivalência do documento comprobatório: **a)** mesma área total construída ou superior à apresentada no PPCI; **b)** atividade equivalente à divisão da ocupação apresentada no PPCI; **c)** mesmo endereço ou equivalente ao apresentado no PPCI; **d)** declaração de que as informações das alíneas "a", "b" e "c" estão comprovadas junto àquele órgão até 26 de dezembro de 2013.

🚫 **Correção a fazer no [[banco-notificacoes-padrao]]:** o modelo registrado cita o **item 6.2.1** para os requisitos de "mesma área / ocupação equivalente / mesmo endereço / coincidência do período de construção". O item correto é o **6.2.1.2.1**. Conferir antes de reusar o modelo.

**Item 6.1.3** — para edificações já licenciadas à luz da LC 14.376/2013, o disposto nesta RT não poderá mais ser empregado caso a edificação deixe de se enquadrar como existente regularizada ou não regularizada. O protocolo de novo PPCI configura **novo marco temporal** para aplicação da legislação (RT 05, Parte 01).

## Estrutura das tabelas de exigências (Anexo A)

| Tabela | Aplicação |
|---|---|
| 4 | Roteamento das edificações existentes |
| 5 | Área ≤ 750 m² **e** altura ≤ 12 m (divisões F-11 e F-12 até 1.500 m²) |
| 6A a 6M | Área > 750 m² **ou** altura > 12 m, subdivididas por grupo/divisão |
| 7 | Subsolos ocupados (nota geral "a" das Tabelas 6 remete a ela) |

Colunas de altura: `Térrea | H ≤ 6 | 6 < H ≤ 12 | 12 < H ≤ 23 | 23 < H ≤ 30 | Acima de 30`.

Subdivisões confirmadas: **6I.1** (I-1 e I-2), **6I.2** (I-3), **6J.1** (J-1 e J-2), **6J.2** (J-3 e J-4) — cada divisão em bloco de colunas próprio.

### ⭐ Duas diferenças relevantes em relação ao Anexo B do Decreto

1. **Menos linhas de medida.** As Tabelas 6 desta RT trazem 12 linhas: Acesso de Viatura na Edificação, Compartimentação Horizontal (áreas), Saídas de Emergência, Plano de Emergência, Brigada de Incêndio, Iluminação de Emergência, Detecção de Incêndio, Alarme de Incêndio, Sinalização de Emergência, Extintores, Hidrantes e Mangotinhos, Chuveiros Automáticos. **Não há linha de Segurança Estrutural em Incêndio, CMAR, Compartimentação Vertical nem Controle de Fumaça** — a ausência dessas medidas no campo 4 de uma existente regularizada **não é pendência**.
2. **O grau de risco vem declarado no cabeçalho da divisão** — "I-1 (risco baixo)", "I-2 (risco médio)", "J-1 (material incombustível)", "J-2 (risco baixo)". Resolve direto o critério (a) do item 5.1.2 da RT 01/2024.

As linhas já lidas estão registradas em [[ocupacao-definidora-e-tabelas-exigencias]] e em `scripts/dados/tabelas_conferidas.json` (chave `linhas_rt05_p07`).

## Notas de uso

Vigência, item 4.1 "c", itens 6.1.3, 6.2.1, 6.2.1.2.1, 6.2.2 e as Tabelas 6I.1/6J.1 conferidos na transcrição literal (`pdftotext -layout`) do PDF oficial em 02/09/2026. **A extração por WebFetch trunca antes dos anexos** — usar o PDF em mãos. Restante ainda não conferido item a item.
