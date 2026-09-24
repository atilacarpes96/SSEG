# Índice de Bases Normativas — SCI/CBMRS/RS

Última verificação/atualização: **24/09/2026** — **IN 066/2025** (saídas de emergência em F-5, F-6, F-11 e F-12; vigente desde 30/09/2025) e **IN 067/2025** (Solução Técnica Equivalente — STE; vigente desde 05/11/2025) **incorporadas**: PDFs em `normas/pdf/IN66.pdf` e `IN67.pdf`, conversões em `normas/md/`, íntegras conferidas em [[in-066-2025-saidas-reuniao-publico]] e [[in-067-2025-solucao-tecnica-equivalente]]; criada a seção **"Instruções Normativas do CBMRS"** abaixo. Em 22/09/2026: **IT 37/2025 em PDF na pasta local (`IT37.pdf`)**, itens 4.4.2, 4.4.4, 4.4.7, 4.4.9, 4.6 e Anexo B conferidos (Tabelas B.1 e B.2 são **imagem** no PDF). **normas por remissão da RT 01/2024** (Tabela 2 e item 4.8, IT 37 para a M-6) conferidas no PDF e registradas abaixo: IT 08, IT 09, IT 15 e IT 37 do CBPMESP e NBR 15219, 10897/16981 e 5419 citadas no campo 4 **são regulares**. Em 21/09/2026: vigência da **RT 17 P01/2025 reconferida no PDF oficial: 01/01/2027** (a "correção" de 19/09/2026 para 01/07/2026 estava errada; ver "Erros de citação registrados"). Vigências da RT 15 P01 e RT 16 reconferidas em 19/09/2026. PDFs oficiais e conversões vivem no repositório desde 15/09/2026 (`normas/pdf/` e `normas/md/`). Conferência das normas contra os PDFs: 02/09/2026.

Ponto de partida para qualquer análise de PPCI, fiscalização ou notificação. Lista as bases normativas incorporadas, seu status de vigência, e para onde ir primeiro ao montar uma notificação.

**Primeira parada ao montar uma notificação:** [[banco-notificacoes-padrao]] — ~80 modelos validados pela chefia. Se o problema já tem modelo lá, use direto.

Fonte oficial para pesquisa própria: **www.bombeiros.rs.gov.br**.

## ⭐ As normas estão no projeto — três camadas, papéis distintos

Desde **15/09/2026** as normas viajam com o repositório. Não pedir PDF ao usuário sem antes olhar aqui:

| Camada | Onde | Serve para | **Não** serve para |
|---|---|---|---|
| **PDF oficial** | `normas/pdf/` — 17 arquivos (14 + `IN66.pdf`, `IN67.pdf` e `IT37.pdf`, em 24/09/2026) | **citar em CIA** | — |
| **Conversão automática** (anydoc) | `normas/md/` | **localizar** item, artigo, palavra | fundamentar exigência |
| **Transcrição comentada** | os `.md` desta pasta | itens já conferidos, travas, aplicação a casos | substituir o PDF na conferência |

Ordem de consulta: a transcrição comentada primeiro; **faltando a letra do item**, `md/` para achar o trecho e `pdf/` para conferir e citar. Detalhe e armadilhas de cada arquivo em `normas/README.md` e [[pasta-normas-local]].

🔴 **`md/` nunca fundamenta.** É extração automática: hierarquia de título sai errada, tabela de exigências desalinha, expoente de nota se solta do X. Item lido ali é **provisório** — conferir no PDF antes de citar.

## ⭐ As tabelas de exigências estão no projeto — não pedir print

`scripts/dados/tabelas_conferidas.json` traz as **duas fontes transcritas por inteiro**:

| Situação | Chave | Conteúdo |
|---|---|---|
| Existente **regularizada** | `rt05_p07_anexo_a` | Anexo A da RT 05 P07/2025 — Tabela 5, 24 Tabelas 6X, Tabela 7 |
| A construir · existente **não** regularizada | `anexo_b_decreto` | Anexo B do Decreto (consolidado até o Dec. 57.967/2024) — Tabela 5, 24 Tabelas 6X, Tabela 7 |

Resolver com **`scripts/tabelas.py`** (`rota`, `linha`, `divisao`, `notas`). Só continuam exigindo imagem a **Tabela 4** (roteamento) e as **Tabelas 6M.1, 6M.2, 6M.4 e 6M.5**, cujo eixo não é altura. Detalhe em [[ocupacao-definidora-e-tabelas-exigencias]].

🔴 A transcrição dá a **célula com a nota colada**. **A nota é do analista:** no critério (b) do item 5.1.2 da RT 01/2024 o pipeline **para e pergunta**. E não é só na definidora — o item 9.4 da RT 18/2025, por exemplo, remete de volta às **notas das tabelas** para as ressalvas da detecção automática.

## ⭐ Como ler os PDFs oficiais

**`pdftotext -layout` sobre o PDF em mãos é o método bom** — preserva colunas, lê os anexos, é transcrição e não resumo.

🚫 **WebFetch não serve para tabela nem para anexo:** **trunca antes dos anexos** (confirmado na RT 11, na RT 05 P1.1 e no Decreto) e **resume**. Serve só para localizar o assunto.

⚠️ **Remover o form feed antes de procurar tabela.** Os cabeçalhos vêm precedidos de `\f`, então `grep "^ *TABELA"` não casa e o anexo parece não existir. Foi esse detalhe que sustentou a afirmação falsa de que "o consolidado não traz o Anexo B".

⚠️ **Conferir a versão na capa.** O Anexo B em `estado.rs.gov.br` é o **original de 2014**, sem menção ao Decreto 53.280/2016; o do CBMRS é o **consolidado**. As células divergem.

## ⚠️ Regra de vigência por data de protocolo

A versão aplicável é a vigente **na data em que o PPCI foi protocolado para a primeira análise**.

**Onde achar:** aba **"Consultar licenciamento" → "Marcos"**, marco **"Número do licenciamento gerado"**. Não está na tela da análise técnica.

> **RT 01/2024, item 4.3.3** — "Para o emprego das normas de segurança contra incêndios e de procedimentos administrativos deverá ser considerada a última edição publicada, em vigor na data do protocolo do PPCI para a primeira análise."
>
> **RT 01/2024, item 3.4** — "As Resoluções Técnicas, Portarias e Instruções Normativas têm efeito imediato e geral aos PPCI/PSPCI protocolados para primeira análise a partir de sua entrada em vigor."

⭐ **Existente regularizada pode usar a legislação da época** — mas **tem que estar especificado no laudo de inviabilidade e no campo de medidas**. Sem isso, vira exigência.

### Datas de transição conhecidas

| RT | Vigente de | Até |
|---|---|---|
| **RT 01/2022** (de 12/04/2022) | 2022 | **31/12/2024** |
| **RT 01/2024** | **01/01/2025** | vigente |
| **RT 15, Parte 01/2022** (de 01/08/2022) | **29/01/2023** | **14/10/2023** |
| **RT 15, Parte 01/2023** | **15/10/2023** | vigente |
| **ABNT NBR 13714** (hidrantes, pela Tabela 2 da RT 01/2024) | — | **até a entrada em vigor da RT 17 P01** |
| **RT 17, Parte 01/2025** | **01/01/2027** (Art. 2º) — emprego antecipado facultado desde a publicação | — |
| **IT 08, 09, 15, 25 e 37 do CBPMESP, edição 2025** | **01/07/2025** (em vigor no CBMRS, conforme página oficial) | vigente — "edição mais recente" (RT 01/2024, 4.3.1) |
| **IN 045/2023** (corredor enclausurado; revogou a IN 025/2020) | **27/04/2023** | vigente |
| **IN 066/2025** (saídas em F-5, F-6, F-11, F-12) | **30/09/2025** (Art. 5º, na publicação) | vigente — PPCI protocolado antes segue a RT 11 pura |
| **IN 067/2025** (Solução Técnica Equivalente — STE) | **05/11/2025** (Art. 15, na publicação) | vigente |

## Hierarquia adotada

1. Lei Complementar Estadual · 2. Decreto Estadual · 3. Resoluções Técnicas do CBMRS · 4. Instruções Normativas / Notas Técnicas · 5. Consultas Técnicas · 6. ABNT citadas/incorporadas · 7. Literatura e normas de outros estados (subsidiárias).

⚠️ **IT do CBPMESP chamada pela RT 01/2024 não é "subsidiária":** é a norma da medida por remissão expressa (item 4.3.1 + Tabela 2; item 4.8 para a M-6). Subsidiária é a IT usada **sem** essa remissão.

⭐ **Qual citar quando os dois dizem o mesmo:** havendo **artigo do Decreto e item de RT com o mesmo conteúdo, citar apenas o item da RT** — a notificação sai pelo campo 4, organizado pela norma que o RT usou. O Decreto fica quando não há item de RT equivalente (art. 27, memorial de capacidade de lotação; Tabela 3 do Anexo "A", grau de risco).

## ⭐ Normas por remissão da RT 01/2024 — citação regular no campo 4

Conferido em **22/09/2026** no PDF da pasta local (RT 01/2024 com a Nota de Atualização n.º 001/2026). Quando o campo 4 cita uma destas normas para a medida da linha, **está correto — não é pendência nem "norma fora do índice"**. As IT do CBPMESP aqui **não são referência subsidiária**: a própria RT 01/2024 manda aplicá-las.

> **RT 01/2024, item 4.3.1** — "Para a implementação das medidas de segurança contra incêndio previstas no Decreto Estadual n.º 51.803/2014, até a entrada em vigor de Resolução Técnica específica, deverão ser observadas as Normas Brasileiras e Instruções Técnicas dispostas na Tabela 2, em sua edição mais recente."

| Medida | Norma a citar | Dispositivo da RT 01/2024 |
|---|---|---|
| Segurança Estrutural em Incêndio | **IT 08 – CBPMESP** | Tabela 2, item 1 |
| Compartimentação Horizontal e Vertical | **IT 09 – CBPMESP** | Tabela 2, item 2 (nota: não se destina à isenção de outras medidas) |
| CMAR | RT CBMRS 09 (antes, IT 10 – CBPMESP) | Tabela 2, item 3 (Nota de Atualização 001/2026) |
| Controle de Fumaça | **IT 15 – CBPMESP** | Tabela 2, item 4 |
| Hidrantes e Mangotinhos | NBR 13714 até a vigência da RT 17 P01 | Tabela 2, item 5 |
| Chuveiros Automáticos | **ABNT NBR 10897 e NBR 16981** | Tabela 2, item 6 |
| Detecção e Alarme | RT CBMRS 18 (antes, NBR 17240) | Tabela 2, item 7 (Nota de Atualização 001/2026) |
| Iluminação de Emergência | RT CBMRS 13 (antes, NBR 10898) | Tabela 2, item 8 (Nota de Atualização 001/2026) |
| Plano de Emergência | **ABNT NBR 15219** | Tabela 2, item 9 |
| SPDA | **ABNT NBR 5419** | Tabela 2, item 10 |
| M-6: isolamento de risco entre transformadores, sistema de espuma, sistema de resfriamento, **hidrantes** | **IT 37 – CBPMESP (Subestação Elétrica)** | itens **4.8.1** e **4.8.7**; para hidrantes, também a **nota "f" da Tabela 1 do Anexo A da RT 17 P01/2025** |

**Edição.** "Edição mais recente", com a vigência pela data de protocolo. O site do CBMRS ([bombeiros.rs.gov.br/instrucoes-tecnicas](https://www.bombeiros.rs.gov.br/instrucoes-tecnicas)) lista como **"em vigor no CBMRS" desde 01/07/2025**: IT 08/2025 (P1 e P2), IT 09/2025, IT 15/2025 (P1 a P9), IT 25/2025 (P1 a P5) e IT 37/2025.

### M-6 (centrais de energia e subestações) — RT 01/2024, item 4.8

- **4.8.1** — medidas da M-6, "independentemente da área construída, altura, classe de risco de incêndio e da presença ou não de pessoas": **Tabela 6M.6 do Decreto + IT 37 do CBPMESP + a própria RT 01/2024**, até RT específica. É a "RTCBMRS específica" das notas gerais "a" e "b" da 6M.6 que ainda não existe.
- **4.8.2** — a 6M.6 vale para geração, transmissão e distribuição, exceto torres e cabos de transmissão.
- **4.8.3 a 4.8.3.7** — substituição de medidas da M-6 por laudo de inviabilidade (RT 05 P07) com compensatórias; mínimas fixadas para espuma (4.8.3.4) e espuma + resfriamento (4.8.3.5); aprovação pelo Cmt BESCI/Chefe SSeg, sem comissão técnica (4.8.3.7).
- **4.8.4** — escada da M-6 = tipos exigidos para a M-3 (Tabela 4, Anexo C, RT 11 P01).
- **4.8.5** — os itens 4.8.1 a 4.8.4 **não se aplicam às edificações adjacentes**, que seguem a própria ocupação (ex.: sala de comando D-1 isolada → Tabela 5 ou 6D).
- **4.8.6** — M-6 e adjacentes: sempre **PPCI completo**.
- **4.8.6.1** — ⭐ **a planta baixa deve informar o tipo de subestação (IT 37), o tipo de óleo isolante (mineral ou classe "K") e o volume de óleo de todos os transformadores e reatores de potência.** Faltando → notificar com este item.
- **4.8.7** — a IT 37 define os requisitos por tipo de subestação; algumas medidas da 6M.6 não são exigidas ou são substituídas (nota geral "a" da 6M.6 e RT 05 P07).

Caso que originou: A00003462AB001 (SE Santa Cruz 1, CPFL), 22/09/2026.

### IT 37/2025 — o que a análise confere (PDF local, 22/09/2026)

Enquadramento pelo **volume de óleo de cada transformador** (por isso o 4.8.6.1 da RT 01 exige tipo e volume em planta): até 20 m³ mineral / 38 m³ classe K → **4.5**; acima → **4.6**. Subestação externa acima de 20 m³ (**4.6.1**): via de acesso · parede corta-fogo (4.4.4) **ou** afastamentos das Tabelas 1 e 2 · contenção (4.4.5) · extintores portáteis e sobre rodas · sinalização · resfriamento (4.4.7) · espuma, dimensionada para o tanque ou para a bacia, "calculado para o maior volume entre eles".

| Item IT 37 | Texto / valor | Anexo L |
|---|---|---|
| 4.4.2.1 | extintores de pó **sobre rodas 80-B:C** para os conjuntos transformadores e reatores | L.1 — planta |
| 4.4.2.4 | distribuição para **risco alto** "conforme a IT 21" → no RS, RT 14 (Tabela 2: 80-B risco alto = 15 m; **5.4.5.5**: +50% para sobre rodas = 22,5 m) | L.1 — planta |
| 4.4.4.1 | parede corta-fogo **TRRF 120 min**; a) **0,3 m** (altura) e **0,6 m** (comprimento) além de buchas, conservador, válvulas de alívio, radiadores e comutador; b) **0,5 m** livres até o equipamento; c) colapso não atinge equipamentos, edificações ou rotas de fuga; d) não passa calor e chamas | L.1 — planta e corte |
| 4.4.4.2 / Tab. 1 e 2 | parede dispensada se atender afastamentos. Óleo mineral > 20.000 L: **7,6 m** (edif. resistente 2 h) · **15,2 m** (incombustível) · **30,5 m** (combustível); **15,2 m** entre equipamentos. Mineral: medir da **borda interna da contenção** | L.1 — planta e corte |
| 4.4.7.2 e 4.4.9.4 | linhas manuais de resfriamento e espuma **móvel** só com **brigada (população fixa)** | condição de admissibilidade |
| **Tab. B.1** (espuma) | até 60 m³: **200 L/min por linha · 2 linhas · 20 min**; 60 a 120 m³: 400 L/min · 2 linhas · 20 min | L.2 — memorial |
| **Tab. B.2** (resfriamento) | 20 a 60 m³: **250 L/min por linha · 35 mca · 2 linhas · 60 min**; 60 a 120 m³: 700 L/min · 35 mca · 2 · 60 min | L.2 — memorial |
| Tab. B.3 (espuma na bacia) | fixos na parede 4,1 L/min/m2 · 55 min; canhões e linhas manuais **6,5 L/min/m2 · 65 min** | L.2 — memorial |
| 4.4.5 (contenção, separador água/óleo) | — | **não é medida do Anexo L** → responsabilidade do RT |

⚠️ **IT 25 não é fundamento para extintores de transformador** (A00003462AB001): a IT 37 é a específica; ela só remete à IT 25 para a bacia de contenção externa (4.4.5.4 "d").


## Legislação estadual

| Norma | Nº / Data | Status | Doc |
|---|---|---|---|
| Lei Complementar | LC 14.376, de 26/12/2013 ("Lei Kiss") | Vigente. Consolidação indicada pelo CBMRS: até a **LC 16.280/2025**. ⚠️ Ver limitação abaixo. | [[lei-complementar-14376-2013]] |
| Decreto regulamentador | Decreto nº 51.803, de 10/09/2014 | Vigente, **consolidado até o Decreto nº 57.967/2024** ✅. **Anexo B transcrito** ⭐. Arts. 27-29 conferidos. | [[decreto-51803-2014]] |

## Resoluções Técnicas — Procedimentos administrativos e técnicos

| RT | Título | Vigência | Doc |
|---|---|---|---|
| RT Implantação do SOL-CBMRS (4ª Ed./2022, corrigida) | Sistema Online de Licenciamento | ✅ **não há 5ª edição** (conferido em 02/09/2026) | [[rt-implantacao-sol-cbmrs]] ⭐ elementos gráficos transcritos |
| RT 01/2024 | Diretrizes Básicas | **01/01/2025** ⭐ itens 3.4, 4.3.1, 4.3.3, 5.1.2, 5.1.3, 5.2.1-5.2.3 literais; **Tabela 2 e item 4.8 (M-6) conferidos em 22/09/2026**. PDF local com a **Nota de Atualização n.º 001/2026** nas Tabelas 2 e 3 | [[rt-01-2024-diretrizes-basicas]] |
| RT 01/2022 | Diretrizes Básicas — anterior | até **31/12/2024** | (em [[rt-01-2024-diretrizes-basicas]]) |
| RT 02/2014 | Terminologia | — ⭐ itens 4.20 e 4.30 literais | [[rt-02-2014-termos-definicoes]] |
| RT 04/2022 | Isolamento de Riscos | — | [[rt-04-2022-isolamento-riscos]] |
| RT 05, Parte 1.1/2016 | PPCI na forma completa | — ⭐ **Anexo "L" lido integralmente**; complementada pela **IN 067/2025** (STE) | [[rt-05-parte01-1-2016-ppci-completo]] |
| RT 05, Parte 06/2025 | Fiscalização e Penalidades | — | [[rt-05-parte-06-2025-fiscalizacao]] |
| RT 05, Parte 07/2025 | Edificações e Áreas Existentes | **01/02/2025** ⭐ **Anexo A transcrito**; itens 4.1"c", 5.4, 5.5, 6.2.1 e 6.2.1.2.1 conferidos | [[rt-05-parte07-2025-edificacoes-existentes]] |
| RT 05, Parte 08/2016 | Simbologia | — | [[rt-05-parte08-2016-simbologia]] |

## Resoluções Técnicas — Medidas de segurança contra incêndio

| RT | Medida | Vigência | Doc |
|---|---|---|---|
| RT 09/2025 | CMAR | 01/11/2025 | [[rt-09-2025-cmar]] |
| RT 10/2024 | Acesso de Viaturas | ✅ **07/04/2025** ⭐ 5.1.2 (via) e **5.1.3 (pórtico)** literais | [[rt-10-2024-acesso-viaturas]] |
| RT 11, Parte 01/2016 | Saídas de Emergência | 19/09/2016 ⭐ a mais densa; **Anexo "D" transcrito**; 5.5.4.9 e 5.5.4.10 literais; **5.3.6** (população do pavimento = soma dos compartimentos) conferido em 21/09/2026; **5.4.1.2.2** (F-5, F-6, F-11, F-12: mais de uma saída, paredes diversas, 10 m) conferido em 24/09/2026 — **complementado pela IN 066/2025** | [[rt-11-parte01-2016-saidas-emergencia]] |
| RT 12/2021 | Sinalização de Emergência | 01/01/2022 ⭐ item 5.4.2.3 (lotação máxima) literal | [[rt-12-2021-sinalizacao-emergencia]] |
| RT 13/2025 | Iluminação de Emergência | 07/04/2025 | [[rt-13-2025-iluminacao-emergencia]] |
| RT 14/2016 | Extintores | 26/05/2016 | [[rt-14-2016-extintores]] |
| RT 15, Parte 01/2023 | Brigada de Incêndio | ✅ **15/10/2023** — publicada no DOE n.º 180, de 15/09/2023; Art. 2º: 30 dias após a publicação. Revoga a RT 15 P01 de 01/08/2022 (que vigorou de 29/01/2023 a 14/10/2023). ⚠️ Texto do Art. 2º lido em espelho não oficial — conferir no PDF de `normas/pdf/` antes de citar a data em CIA | [[rt-15-parte01-2023-brigada-incendio]] |
| RT 16/2017 | Hidrante Urbano | Publicada no **DOE n.º 092, de 17/05/2017** ✅. ⚠️ **Vigência não conferida** — o Art. 2º não foi lido. **Não citar data.** O "16/07/2017" anterior era suposição de prazo de 60 dias | [[rt-16-2017-hidrantes-urbanos]] |
| RT 17, Parte 01/2025 | Hidrantes e Mangotinhos | ✅ **01/01/2027** (Art. 2º), reconferido em **21/09/2026** no PDF da pasta local e na versão corrigida de 08/06/2026 do site do CBMRS. Publicada no DOE n.º 188, de 25/09/2025; assinada em 22/09/2025. O Art. 2º faculta o emprego antecipado a contar da publicação. Item **2.2**: facultativa para PPCI **já protocolado**, desde que não haja alteração que exija novo PPCI. **Até 31/12/2026, citar NBR 13714 ou RT 17 no campo 4 é regular — nenhuma das duas é pendência** | [[rt-17-parte01-2025-hidrantes-mangotinhos]] |
| RT 18/2025 | Detecção e Alarme | ✅ **01/11/2025** confirmado ⭐ **seção 8 (acionadores) transcrita**; itens 9.3 e 9.4 | [[rt-18-2025-deteccao-alarme]] |

## Instruções Normativas do CBMRS

Norma do RS, **nível 4** (abaixo das RTs), sujeita à regra de vigência por data de protocolo (RT 01/2024, item 3.4 cita expressamente as Instruções Normativas). **Não é fonte subsidiária.** Lista oficial: [bombeiros.rs.gov.br/instrucoes-normativas](https://www.bombeiros.rs.gov.br/instrucoes-normativas).

| IN | Objeto | Vigência | PDF | Doc |
|---|---|---|---|---|
| **IN 045/CBMRS/DSPCI/2023** | Corredor enclausurado como saída de emergência (complementa a RT 11) — Art. 1º, incisos I a XVI; representação em vermelho (Art. 2º). Não se aplica a corredor de **descarga** (Art. 6º → RT 11, 5.12.1.2) | **27/04/2023** (DOE 81); revogou a IN 025/2020 | `IN45.pdf` ✅ | [[in-045-2023-corredor-enclausurado]] |
| **IN 066/CBMRS/DSPCI/2025** ⭐ novo | **Saídas de emergência em F-5, F-6, F-11 e F-12** (complementa o 5.4.1.2.2 da RT 11): duas saídas por **cômodo** acima de 50 pessoas (100 em casa de festas F-12 com brigadistas), mesma parede com **5 m** no recinto; edificação sempre com mais de uma saída para o exterior; F-12 casa de festas até **750 m²** de área total construída pode ter as duas saídas finais na mesma parede, com **10 m** | **30/09/2025** (DOE 191) | `IN66.pdf` ✅ | [[in-066-2025-saidas-reuniao-publico]] |
| **IN 067/CBMRS/DSPCI/2025** ⭐ novo | **Solução Técnica Equivalente (STE)** — complementa a RT 05 P1.1 e a RT de Implantação do SOL: modifica (nunca suprime) medida em edificação a construir ou em novo licenciamento, por **LCLT** (Anexo B) com 8 parâmetros de equivalência (Anexo A); protocolada no upload de **ART/RRT do passo 1**; avaliada pelo **Corpo Técnico** (verificação formal). **Vedada em F-6, baixo risco, PSPCI e evento temporário** (Art. 2º). **Não é medida compensatória** (Art. 1º, § 2º) | **05/11/2025** (DOE 217) | `IN67.pdf` ✅ | [[in-067-2025-solucao-tecnica-equivalente]] |
| IN 056/CBMRS/DSPCI/2024 | Câmaras frigoríficas / amônia | ⚠️ não conferida | ✗ | [[fontes-subsidiarias-outros-estados-e-instrucoes]] |
| IN 068/CBMRS/DSPCI/2025 | Enquadramento nas divisões F-5, F-6, F-8, F-11 e F-12 | DOE 252, de 26/12/2025 — ⚠️ lida só por WebFetch | ✗ | — |

⚠️ **IN 066 × RT 11 — aparente conflito.** O 5.4.1.2.2 exige saídas em **paredes diversas**; a IN admite a **mesma parede** no recinto (5 m) e na F-12 casa de festas até 750 m² (10 m). A IN é posterior, específica e complementar; a leitura adotada está em [[in-066-2025-saidas-reuniao-publico]], com a ressalva sobre a competência do Diretor do DSPCI (Portarias 016/2025 e 054/2025, não conferidas).

## Outras fontes

| Fonte | Conteúdo | Doc |
|---|---|---|
| Normas ABNT citadas | NBR 13714, 17240, 11785, 9050, 13523, 17505-7; **15219, 10897, 16981 e 5419 por remissão da Tabela 2 da RT 01/2024** | [[abnt-normas-citadas]] |
| ITs do CBPMESP | **IT 08, 09, 15 e 37 (edição 2025) aplicáveis por remissão da RT 01/2024 — ver seção acima**; IT CBPMESP nº 06/2019 e 09/2025 como subsidiárias fora dessa remissão. (As IN do CBMRS têm seção própria acima.) | [[fontes-subsidiarias-outros-estados-e-instrucoes]] |
| **Banco de notificações** | ~80 modelos validados pela chefia | [[banco-notificacoes-padrao]] ⭐ consultar primeiro |
| Redações reais e erros registrados | Não validadas | [[divisao-trabalho-notificacao]] |
| Modelo sob demanda | Organização dos elementos gráficos em arquivos | [[notificacao-elementos-graficos-separados]] |

## Scripts

- **`scripts/tabelas.py`** ⭐ — resolve a tabela de exigências nas duas fontes (`rota`, `linha`, `divisao`, `notas`). É o caminho para tabela.
- `scripts/sseg.py` — extração/JSON do processo, render do PDF de arquivo, diff entre análises. ⚠️ O roteamento de tabelas dele é anterior à transcrição e **foi superado pelo `tabelas.py`**. **22/09/2026:** a conferência de normas (`check`) passou a reconhecer isolamento de riscos, isolamento de transformadores, espuma, resfriamento e SPDA, e a casar "Resolução Técnica n.º X" com "RT X" e "Instrução Técnica n.º X – CBPMESP" com "IT X" — antes disso as RT citadas por extenso no SOL não batiam com o índice. ⚠️ O `check` **não normaliza "Instrução Normativa" para "IN"** (lido no código em 24/09/2026): "IN 066/2025" casa, mas "Instrução Normativa n.º 066/CBMRS/DSPCI/2025" por extenso, sozinha na célula, sai como atenção — falso positivo, não pendência. Junto com a RT 11 na mesma célula, casa pela RT. 🐞 **Achado em 24/09/2026:** o `_canon_norma` não tira a **vírgula** — "Resolução Técnica CBMRS n.º 11, Parte 01/2016" (forma comum no SOL) vira `rt11,p01/2016` e **não casa** com `RT 11 Parte 01/2016`. O `check` acusa atenção indevida; é falso positivo. Correção de uma linha (`n = n.replace(",", " ")` antes de colapsar espaços) ainda não aplicada.
- `scripts/dados/indice_normas.json` — forma legível por máquina deste índice. **Ao alterar aqui, alterar lá.**

## 🚫 Erros de citação registrados

- 🔴 **IT 37/2025 — WebFetch INVENTOU as Tabelas B.1 e B.2 (22/09/2026).** Devolveu cinco faixas de volume com tempos de 25 a 90 min que não existem; no PDF as duas tabelas são **imagem** e a extração de texto não as lê. Gerou uma minuta errada de "tempo de espuma insuficiente", descartada antes do lançamento. **Tabela em imagem: renderizar a página (`pdftoppm -r 110 -png`) e ler a imagem.** WebFetch nunca é fonte de número de tabela.
- 🔴 **RT 17, Parte 01/2025 — a "correção" de 19/09/2026 estava errada (desfeita em 21/09/2026).** Em 19/09/2026 o projeto passou a afirmar vigência em **01/07/2026**, dizendo tê-la conferido no PDF oficial. Em 21/09/2026 o Art. 2º foi relido em **duas fontes** — o PDF da pasta local `Carpes\Normas\RT17.pdf` e a **versão corrigida de 08/06/2026** publicada no site do CBMRS — e as duas dizem: *"Esta Resolução Técnica entrará em vigor no dia 1º de janeiro de 2027, revogando as disposições em contrário, ficando facultado ao responsável técnico seu emprego a contar da data de sua publicação."* A Tabela 2 da RT 01/2024 (com a Nota de Atualização n.º 001/2026) corrobora: NBR 13714 "até a entrada em vigor" da RT 17. **Efeito:** PPCI protocolado para 1ª análise até 31/12/2026 pode citar NBR 13714 ou RT 17 — nenhuma das duas é pendência. **Rever os processos de hidrante analisados entre 19/09/2026 e 21/09/2026**: algum pode ter saído com notificação indevida de "norma de hidrantes desatualizada". Caso que revelou o erro: A00049907AA001 (protocolo 10/09/2026, campo 4 com NBR 13714 — regular).
- **RT 18/2025 — o item 8.1 "a" não é "um acionador por pavimento".** São três dispositivos distintos: **8.1 "a"** = um acionador a no máximo 5 m do **acesso principal**; **8.2** = distância máxima a percorrer de **30 m**; **8.3** = **pelo menos um acionador em cada pavimento**, a no máximo 5 m do acesso às escadas/rampas. Uma CIA saiu em 02/09/2026 citando 8.1 "a" para a exigência por pavimento — corrigida antes da homologação. Ver [[rt-18-2025-deteccao-alarme]].
- **Anexo B do Decreto — fonte errada.** O projeto afirmava que o consolidado do CBMRS não o traz e mandava usar o de `estado.rs.gov.br`, que é o original de 2014. Falso nas duas pontas. Ver [[decreto-51803-2014]].
- **Contagem de medidas — leitura de imagem errou** na Tabela 6J.1 (7 no lugar de 8). Ver [[ocupacao-definidora-e-tabelas-exigencias]].

## ⚠️ Pendências e alertas

- **Instruções do Projeto** — em 24/09/2026 o campo já trazia a RT 17 com vigência em **01/01/2027** (a pendência antiga do 01/07/2026 estava resolvida). Faltavam duas mudanças, entregues ao usuário para colar no campo nessa data: a ressalva das **IT do CBPMESP chamadas pela RT 01/2024** (4.3.1 + Tabela 2; 4.8 para a M-6), junto com a posição das **IN do CBMRS**, e a contagem de **PDFs (17)**. O espelho [[instrucoes-projeto-espelho]] já está com o texto novo — **conferir se o campo foi atualizado** antes de dar por encerrado.
- **IN 068/2025** (enquadramento F-5, F-6, F-8, F-11, F-12; DOE 252, de 26/12/2025) — PDF **não está no projeto**. Pela leitura por WebFetch (não confiável) não menciona a IN 066. Conferir no PDF antes de afirmar que as duas convivem.
- **IN 067/2025 — a Portaria que regula o Corpo Técnico** que avalia a STE (Art. 8º) **não está no projeto**; nem a transição para PPCI já em análise em 05/11/2025.
- **LC 14.376/2013** — único PDF acessível está consolidado até a LC 14.924/2016; o CBMRS indica até a LC 16.280/2025. **Não usar o texto de 2016 sem confirmar o dispositivo.**
- **Banco de notificações — dois modelos com ressalva anotada ao lado** (texto da chefia preservado): o da "existente regularizada" cita o item **6.2.1** da RT 05 P07, quando os requisitos estão no **6.2.1.2.1**; e o da escala cita o **6.3.6.1.2.2**, que é a **lista de escalas permitidas**.
- **RT 16/2017 — vigência nunca conferida.** Publicação confirmada (DOE 092, de 17/05/2017); falta ler o **Art. 2º** no PDF oficial para saber o prazo. Não citar data até lá.
- **RT 01/2024 — versões corrigidas** de out/2024, jan/2025 e 08/06/2026: a vigência não muda, mas **não está verificado se a numeração dos itens se manteve**.
- **Demais RTs com mais de uma versão** — datas de transição não levantadas. Caminho: a página **"Legislação Revogada"** do CBMRS lista os pares revogada → revogadora.
- **RT 16 x RT 17** — objetos distintos (urbano x sistema interno); não presumir revogação.
- **Tabela 3 da RT 01/2024** — só a linha 1 (Acesso de Viaturas) foi lida em 22/09/2026; as demais linhas não foram transcritas.

## Próximos passos

Tabela 4 e Tabelas 6M.1/6M.2/6M.4/6M.5 (eixo não é altura); Tabela L.3 do Anexo "L"; Tabela 4 da RT 11; faixas de risco baixo e alto da Tabela 3 do Decreto; RT 03/2016, RT 05 Partes 02 e 03, e as RTs de ocupações específicas (20, 21, 22, 23, 31, 32); demais linhas da Tabela 3 da RT 01/2024; demais IN do CBMRS listadas no site (em especial a IN 068/2025, que conversa com a IN 066).

✅ **01/09/2026:** transição RT 01/2022 → RT 01/2024 e fundamento da regra de vigência.
✅ **02/09/2026:** conferência de 12 PDFs oficiais; **Anexo A da RT 05 P07 e Anexo B do Decreto transcritos por inteiro**; Anexo "L", Anexo "D" e seção 8 da RT 18 lidos; correção da fonte do Anexo B.
✅ **19/09/2026:** **RT 15 P01/2023 confirmada** (15/10/2023) e transição a partir da P01/2022 mapeada; **RT 16/2017** com publicação confirmada e vigência marcada como não conferida. (A alteração da RT 17 para 01/07/2026 feita nesta data foi desfeita em 21/09/2026.)
✅ **21/09/2026:** **RT 17 P01/2025 reconferida — 01/01/2027** (PDF local + versão corrigida de 08/06/2026); Tabela 2 da RT 01/2024 com a Nota de Atualização n.º 001/2026 confirma a NBR 13714 até a entrada em vigor da RT 17; item **5.3.6 da RT 11 P01/2016** conferido.
✅ **22/09/2026:** **Tabela 2 inteira e item 4.8 (M-6/subestações) da RT 01/2024 conferidos no PDF**; IT 08, 09, 15 e 37 do CBPMESP e NBR 15219, 10897/16981 e 5419 registradas como normas por remissão; lista de IT "em vigor no CBMRS" conferida no site oficial; `sseg.py check` atualizado.
✅ **24/09/2026:** **IN 066/2025 e IN 067/2025 incorporadas** — PDFs do site oficial, conversão anydoc, íntegras conferidas no PDF e **5.4.1.2.2 da RT 11** conferido no PDF local; seção de Instruções Normativas criada neste índice.

## Metodologia

Antes de usar qualquer norma como fundamento: (1) checar o [[banco-notificacoes-padrao]]; (2) confirmar a data de protocolo nos **Marcos**; (3) reconferir a vigência na fonte oficial; (4) verificar Nota ou Consulta Técnica posterior; (5) avisar expressamente se a base estiver desatualizada; (6) registrar todo item novo conferido no doc da respectiva norma.
