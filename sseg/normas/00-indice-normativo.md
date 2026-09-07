# Índice de Bases Normativas — SCI/CBMRS/RS

Última verificação/atualização: **02/09/2026** — grande rodada de conferência contra os PDFs oficiais.

Ponto de partida para qualquer análise de PPCI, fiscalização ou notificação. Lista as bases normativas incorporadas, seu status de vigência, e para onde ir primeiro ao montar uma notificação.

**Primeira parada ao montar uma notificação:** [[banco-notificacoes-padrao]] — ~80 modelos validados pela chefia. Se o problema já tem modelo lá, use direto.

Fonte oficial para pesquisa própria: **www.bombeiros.rs.gov.br**.

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

## Hierarquia adotada

1. Lei Complementar Estadual · 2. Decreto Estadual · 3. Resoluções Técnicas do CBMRS · 4. Instruções Normativas / Notas Técnicas · 5. Consultas Técnicas · 6. ABNT citadas/incorporadas · 7. Literatura e normas de outros estados (subsidiárias).

⭐ **Qual citar quando os dois dizem o mesmo:** havendo **artigo do Decreto e item de RT com o mesmo conteúdo, citar apenas o item da RT** — a notificação sai pelo campo 4, organizado pela norma que o RT usou. O Decreto fica quando não há item de RT equivalente (art. 27, memorial de capacidade de lotação; Tabela 3 do Anexo "A", grau de risco).

## Legislação estadual

| Norma | Nº / Data | Status | Doc |
|---|---|---|---|
| Lei Complementar | LC 14.376, de 26/12/2013 ("Lei Kiss") | Vigente. Consolidação indicada pelo CBMRS: até a **LC 16.280/2025**. ⚠️ Ver limitação abaixo. | [[lei-complementar-14376-2013]] |
| Decreto regulamentador | Decreto nº 51.803, de 10/09/2014 | Vigente, **consolidado até o Decreto nº 57.967/2024** ✅. **Anexo B transcrito** ⭐. Arts. 27-29 conferidos. | [[decreto-51803-2014]] |

## Resoluções Técnicas — Procedimentos administrativos e técnicos

| RT | Título | Vigência | Doc |
|---|---|---|---|
| RT Implantação do SOL-CBMRS (4ª Ed./2022, corrigida) | Sistema Online de Licenciamento | ✅ **não há 5ª edição** (conferido em 02/09/2026) | [[rt-implantacao-sol-cbmrs]] ⭐ elementos gráficos transcritos |
| RT 01/2024 | Diretrizes Básicas | **01/01/2025** ⭐ itens 3.4, 4.3.1, 4.3.3, 5.1.2, 5.1.3, 5.2.1-5.2.3 literais | [[rt-01-2024-diretrizes-basicas]] |
| RT 01/2022 | Diretrizes Básicas — anterior | até **31/12/2024** | (em [[rt-01-2024-diretrizes-basicas]]) |
| RT 02/2014 | Terminologia | — ⭐ itens 4.20 e 4.30 literais | [[rt-02-2014-termos-definicoes]] |
| RT 04/2022 | Isolamento de Riscos | — | [[rt-04-2022-isolamento-riscos]] |
| RT 05, Parte 1.1/2016 | PPCI na forma completa | — ⭐ **Anexo "L" lido integralmente** | [[rt-05-parte01-1-2016-ppci-completo]] |
| RT 05, Parte 06/2025 | Fiscalização e Penalidades | — | [[rt-05-parte-06-2025-fiscalizacao]] |
| RT 05, Parte 07/2025 | Edificações e Áreas Existentes | **01/02/2025** ⭐ **Anexo A transcrito**; itens 4.1"c", 5.4, 5.5, 6.2.1 e 6.2.1.2.1 conferidos | [[rt-05-parte07-2025-edificacoes-existentes]] |
| RT 05, Parte 08/2016 | Simbologia | — | [[rt-05-parte08-2016-simbologia]] |

## Resoluções Técnicas — Medidas de segurança contra incêndio

| RT | Medida | Vigência | Doc |
|---|---|---|---|
| RT 09/2025 | CMAR | 01/11/2025 | [[rt-09-2025-cmar]] |
| RT 10/2024 | Acesso de Viaturas | ✅ **07/04/2025** ⭐ 5.1.2 (via) e **5.1.3 (pórtico)** literais | [[rt-10-2024-acesso-viaturas]] |
| RT 11, Parte 01/2016 | Saídas de Emergência | 19/09/2016 ⭐ a mais densa; **Anexo "D" transcrito**; 5.5.4.9 e 5.5.4.10 literais | [[rt-11-parte01-2016-saidas-emergencia]] |
| RT 12/2021 | Sinalização de Emergência | 01/01/2022 ⭐ item 5.4.2.3 (lotação máxima) literal | [[rt-12-2021-sinalizacao-emergencia]] |
| RT 13/2025 | Iluminação de Emergência | 07/04/2025 | [[rt-13-2025-iluminacao-emergencia]] |
| RT 14/2016 | Extintores | 26/05/2016 | [[rt-14-2016-extintores]] |
| RT 15, Parte 01/2023 | Brigada de Incêndio | ~15/10/2023 ⚠️ aproximada, não conferida | [[rt-15-parte01-2023-brigada-incendio]] |
| RT 16/2017 | Hidrante Urbano | ~16/07/2017 ⚠️ aproximada, não conferida | [[rt-16-2017-hidrantes-urbanos]] |
| RT 17, Parte 01/2025 | Hidrantes e Mangotinhos | **01/01/2027** (Art. 2º). Item **2.2**: facultativa para PPCI **já protocolado** | [[rt-17-parte01-2025-hidrantes-mangotinhos]] |
| RT 18/2025 | Detecção e Alarme | ✅ **01/11/2025** confirmado ⭐ **seção 8 (acionadores) transcrita**; itens 9.3 e 9.4 | [[rt-18-2025-deteccao-alarme]] |

## Outras fontes

| Fonte | Conteúdo | Doc |
|---|---|---|
| Normas ABNT citadas | NBR 13714, 17240, 11785, 9050, 13523, 17505-7 | [[abnt-normas-citadas]] |
| ITs de outros estados / IN CBMRS | IT CBPMESP nº 06/2019 e 09/2025 (subsidiárias), IN CBMRS nº 056/2024 | [[fontes-subsidiarias-outros-estados-e-instrucoes]] |
| **Banco de notificações** | ~80 modelos validados pela chefia | [[banco-notificacoes-padrao]] ⭐ consultar primeiro |
| Redações reais e erros registrados | Não validadas | [[divisao-trabalho-notificacao]] |
| Modelo sob demanda | Organização dos elementos gráficos em arquivos | [[notificacao-elementos-graficos-separados]] |

## Scripts

- **`scripts/tabelas.py`** ⭐ — resolve a tabela de exigências nas duas fontes (`rota`, `linha`, `divisao`, `notas`). É o caminho para tabela.
- `scripts/sseg.py` — extração/JSON do processo, render do PDF de arquivo, diff entre análises. ⚠️ O roteamento de tabelas dele é anterior à transcrição e **foi superado pelo `tabelas.py`**.
- `scripts/dados/indice_normas.json` — forma legível por máquina deste índice. **Ao alterar aqui, alterar lá.**

## 🚫 Erros de citação registrados

- **RT 18/2025 — o item 8.1 "a" não é "um acionador por pavimento".** São três dispositivos distintos: **8.1 "a"** = um acionador a no máximo 5 m do **acesso principal**; **8.2** = distância máxima a percorrer de **30 m**; **8.3** = **pelo menos um acionador em cada pavimento**, a no máximo 5 m do acesso às escadas/rampas. Uma CIA saiu em 02/09/2026 citando 8.1 "a" para a exigência por pavimento — corrigida antes da homologação. Ver [[rt-18-2025-deteccao-alarme]].
- **Anexo B do Decreto — fonte errada.** O projeto afirmava que o consolidado do CBMRS não o traz e mandava usar o de `estado.rs.gov.br`, que é o original de 2014. Falso nas duas pontas. Ver [[decreto-51803-2014]].
- **Contagem de medidas — leitura de imagem errou** na Tabela 6J.1 (7 no lugar de 8). Ver [[ocupacao-definidora-e-tabelas-exigencias]].

## ⚠️ Pendências e alertas

- **LC 14.376/2013** — único PDF acessível está consolidado até a LC 14.924/2016; o CBMRS indica até a LC 16.280/2025. **Não usar o texto de 2016 sem confirmar o dispositivo.**
- **Banco de notificações — dois modelos com ressalva anotada ao lado** (texto da chefia preservado): o da "existente regularizada" cita o item **6.2.1** da RT 05 P07, quando os requisitos estão no **6.2.1.2.1**; e o da escala cita o **6.3.6.1.2.2**, que é a **lista de escalas permitidas**.
- **RT 15 P01/2023 e RT 16/2017** — vigências **aproximadas, nunca conferidas**. Não citar data sem confirmar.
- **RT 01/2024 — versões corrigidas** de out/2024, jan/2025 e 08/06/2026: a vigência não muda, mas **não está verificado se a numeração dos itens se manteve**.
- **Demais RTs com mais de uma versão** — datas de transição não levantadas.
- **RT 16 x RT 17** — objetos distintos (urbano x sistema interno); não presumir revogação.

## Próximos passos

Tabela 4 e Tabelas 6M.1/6M.2/6M.4/6M.5 (eixo não é altura); Tabela L.3 do Anexo "L"; Tabela 4 da RT 11; faixas de risco baixo e alto da Tabela 3 do Decreto; RT 03/2016, RT 05 Partes 02 e 03, e as RTs de ocupações específicas (20, 21, 22, 23, 31, 32).

✅ **01/09/2026:** transição RT 01/2022 → RT 01/2024 e fundamento da regra de vigência.
✅ **02/09/2026:** conferência de 12 PDFs oficiais; **Anexo A da RT 05 P07 e Anexo B do Decreto transcritos por inteiro**; Anexo "L", Anexo "D" e seção 8 da RT 18 lidos; correção da fonte do Anexo B.

## Metodologia

Antes de usar qualquer norma como fundamento: (1) checar o [[banco-notificacoes-padrao]]; (2) confirmar a data de protocolo nos **Marcos**; (3) reconferir a vigência na fonte oficial; (4) verificar Nota ou Consulta Técnica posterior; (5) avisar expressamente se a base estiver desatualizada; (6) registrar todo item novo conferido no doc da respectiva norma.
