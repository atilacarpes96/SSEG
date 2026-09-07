---
name: ocupacao-definidora-e-tabelas-exigencias
description: Onde estão as tabelas de exigências (as duas fontes agora transcritas por inteiro no projeto), como as notas entram na contagem e por que o critério (b) para o pipeline, os erros de leitura já cometidos, e os casos Hotel Valler, Spessato e Encruzilhada do Sul
sources: [cowork]
---

# Tabelas de exigências — o que o projeto já tem

> O **procedimento** (como achar a definidora no print, como rotear, como conferir se o RT
> acertou) vive na skill `ppci-analise-processo`. Este doc é **registro**.

## ⭐ As duas fontes estão transcritas no projeto

Em `scripts/dados/tabelas_conferidas.json`:

| Situação de existência | Chave | Conteúdo |
|---|---|---|
| **Existente regularizada** | `rt05_p07_anexo_a` | Anexo A da **RT 05 Parte 07/2025** — Tabela 5, 24 Tabelas 6X e Tabela 7 |
| A construir · existente **não** regularizada | `anexo_b_decreto` | Anexo B do **Decreto 51.803/2014** (consolidado até o Decreto 57.967/2024) — Tabela 5, 24 Tabelas 6X e Tabela 7 |

**Não é mais preciso pedir print de tabela de exigências.** Roteamento e células saem daí.
Continuam exigindo imagem apenas a **Tabela 4** (roteamento) e as **Tabelas 6M.1, 6M.2, 6M.4
e 6M.5**, cujo eixo não é altura (ex.: 6M.1 usa extensão em metros, para túnel).

**Como resolver uma célula:** cada tabela guarda `divisoes` (os blocos de coluna, na ordem) e
`medidas` (a fila inteira de células, 6 por bloco). Índice = `(bloco × 6) + coluna`, com as
colunas em `Térrea | H≤6 | 6<H≤12 | 12<H≤23 | 23<H≤30 | Acima de 30`. A **Tabela 5** é
diferente: as colunas são **por grupo**, não por altura — 10 colunas na RT 05 P07 e 11 no
Anexo B, que traz F-7 em separado. A **Tabela 7** é texto livre, transcrita linha a linha.

O script `scripts/tabelas.py` faz essa resolução pela linha de comando.

## 🔴 A transcrição dá a célula. A NOTA é do analista.

As células vêm com o número da nota colado (`X1`, `X8`, `X4;5`). **A nota decide se a medida
entra na contagem** — e a contagem decide a definidora. Dois tipos:

1. **Nota que restringe a célula a outra divisão do mesmo bloco** — ex.: nota 8 da Tabela 6C,
   "para edificações de Divisão C-3". A medida **sai da contagem** de C-1 e C-2.
2. **Nota que condiciona a medida a um fato do caso concreto** — ex.: "somente para áreas de
   depósitos superiores a 750 m²"; "obrigatório se a edificação estiver afastada mais do que
   20 metros da via pública". A medida **fica na contagem**, mas a condição precisa ser
   verificada no projeto.

⛔ **Por isso o critério (b) do item 5.1.2 para o pipeline.** Chegando no desempate por número
de medidas, apresentar as divisões em disputa, as células com as notas, o **texto integral**
de cada nota e a contagem em cada hipótese — e **perguntar**. Nunca aplicar nota sozinho.

## 🚫 Erros de leitura já cometidos

1. **WebFetch superestimou o F-8**: devolveu 11 medidas, o correto é 10. E **trunca antes dos
   anexos**. Proibido para contagem.
2. **02/09/2026 — leitura de imagem errou na Tabela 6J.1.** Devolveu 7 medidas para J-2/H≤6,
   lendo o **Alarme de Incêndio** como "–" quando é "X". O correto é **8**. Onde o olho erra:
   tabelas com **dois blocos de colunas lado a lado** (I-1/I-2, J-1/J-2, C-1/C-2/C-3).
3. **02/09/2026 — afirmação falsa herdada do projeto.** O projeto dizia que "o PDF consolidado
   do CBMRS não traz o Anexo B" e mandava usar o de `estado.rs.gov.br`. **Falso nas duas
   pontas:** o consolidado traz as Tabelas 4 a 7 completas, e o de `estado.rs.gov.br` é o
   **texto original de 2014**, sem nenhuma menção ao Decreto 53.280/2016.
   **O que escondeu:** os cabeçalhos das tabelas vêm precedidos de **form feed** (`\f`), então
   `grep "^ *TABELA"` não casa e a tabela parece não existir. Remover `\f` antes de procurar.
   **Quase custou caro:** a base do Anexo B ia entrar no projeto na versão de 2014.

**Método:** `pdftotext -layout` sobre o PDF oficial **vigente** — conferir "atualizado até" na
capa antes de confiar. Tendo imagem e PDF, cruzar os dois.

## ✅ Linhas com a nota já aplicada (registro de caso)

Estas ficam nas chaves `linhas` (Anexo B) e `linhas_rt05_p07`. Diferente da transcrição, aqui
a **nota já foi aplicada ao caso concreto** — por isso a contagem pode diferir da contagem
crua de células.

**Anexo B · 6B / B-1 / 6<H≤12 → 12 medidas.** Acesso de Viaturas; Segurança Estrutural;
Compartimentação Horizontal (X¹); CMAR; Saídas; Brigada; Iluminação; Detecção (X⁸); Alarme
(X⁹); Sinalização; Extintores; Hidrantes.

**Anexo B · 6F.3 / F-8 / 6<H≤12 → 10 medidas.** Sem Compartimentação, Plano de Emergência,
Detecção, Chuveiros e Controle de Fumaça.

**Anexo B · 6C / C-2 / Térrea → 12 medidas.** A transcrição marca **13** células; a diferença
é o **Plano de Emergência (X⁸)**, que a nota 8 restringe à Divisão C-3 e portanto **sai** da
contagem de C-2. A Detecção é X⁹ (só depósitos > 750 m²): não verificada a condição, a
contagem cai para **11**. ⭐ É o exemplo vivo de por que a nota não se aplica sozinha.

**Anexo B · 6J.2 / J-3 / Térrea → 12 medidas, todas incondicionais.** Cabeçalho declara
**J-3 = risco médio**.

**RT 05 P07 · 6I.1 / I-1 / H≤6 → 8** e **6J.1 / J-2 / H≤6 → 8** — e **as 8 são as mesmas**.

## Fundamentos registrados

- **Definidora — RT 01/2024, itens 5.1.2 e 5.1.2.1** ✅ conferidos literalmente. Em ocupação
  mista sem isolamento: **(a)** maior grau de risco entre as predominantes; **(b)** havendo
  empate, a que exigir o maior número absoluto de medidas **pelas tabelas do Decreto e, quando
  couber, pela RT 05 Parte 07**. **F-6 é sempre definidora** (5.1.2.1).
  Vizinhos conferidos: **5.1.2.2** (na C-3 tudo é subsidiário, salvo F-6); **5.1.2.3**
  (validade do APPCI é a da predominante de menor validade); **5.1.2.4** (grupo M predominante
  dimensiona individualmente, não se aplicando o 5.1.2).
- **Item 5.1.3** — o roteamento usa a **área total a ser protegida** e a **altura descendente**.
- **Subsidiária — itens 5.2.1 a 5.2.3** ✅ conferidos. Quatro exceções ao 5.2.2: depósito "J"
  acima de 10% da área total ou 1.500 m² (5.2.2.1); reunião de público "F" com lotação acima
  de 500 (5.2.2.2); grupo "M" (5.2.2.3); público externo, sem limiar (5.2.3).
- **Grau de risco** — nas tabelas da RT 05 P07 **vem declarado no cabeçalho da divisão**. Pelo
  Decreto, Tabela 3: acima de 300 até 1.200 MJ/m² = **médio**. As faixas de baixo e alto ainda
  não foram conferidas.
- **RT 02/2014, item 4.20 "Altura da edificação"** ✅ literal: *"a) altura ascendente é a
  medida em metros entre o ponto que caracteriza a saída ao nível da descarga (…) ao ponto
  mais baixo do nível do piso do pavimento mais baixo; b) altura da edificação ou altura
  descendente (…) ao ponto mais alto do piso do último pavimento."*
- **RT 02/2014, item 4.30 "Área do maior pavimento"** ✅ literal: *"Área do maior pavimento da
  edificação, **excluindo o da descarga**."* ⚠️ O item define **área do maior pavimento**; a
  extensão ao **pavimento de maior população** vem do modelo validado do
  [[banco-notificacoes-padrao]] — usar a redação do banco, não paráfrase.

## Caso registrado — Hotel Valler (A00016097AA002)

Duas predominantes, **B-1** (carga 500, definidora declarada) e **F-8** (carga 450), ambas
grau médio → empate no (a). Área 6.233,53 m², altura descendente 9,08 m → **Tabela 6B, coluna
6<H≤12** (Anexo B). ✅ Validado: B-1 exige 12 contra 10 do F-8, e as 12 batem com o campo 4.
Altura descendente 9,08 m com zero subsolos é correta — foi aqui que nasceu a trava do 4.20.

## Caso registrado — Pavilhão Spessato (A00049570AA001), Encantado

PPCI **a construir**, 1.571,7 m², **2 pavimentos com descarga própria em cada um** → alturas
0,00 m e pavimento de maior população zerado, ambos corretos. Três predominantes: C-2 (700),
**C-2 (800, marcada pelo RT)** e J-3 (720), todas médio → empate no (a). Área > 750 m² e
altura 0,00 → **coluna Térrea**, Tabelas **6C** e **6J.2**. J-3 = 12 incondicionais; C-2 = 11.
O campo 4 lista exatamente as 12 do J-3. ⏳ Pendente de validação: a conclusão de que a
definidora seria J-3, e a área do J-3.

## Caso registrado — Encruzilhada do Sul (A00024749AA002)

**Existente regularizada**, protocolo **27/08/2026**, 3.605,26 m², altura descendente 4,85 m,
sem subsolo, construtiva Y, população 470 → **RT 05 P07, coluna H ≤ 6**.

- **F-8 (refeitório do pessoal da indústria)** — validado na planta: atendimento da própria
  população (5.2.1); 470 < 500 → 5.2.2.2 não aciona; não é público externo → 5.2.3 não
  aciona. **Continua subsidiária; o RT acertou.**
- **Depósitos J-2, 471 m²** — 10% de 3.605,26 = 360,53 m². **471 > 360,53** → item **5.2.2.1**:
  deve ser **predominante**. O RT declarou subsidiária → exigência.
- **Definidora:** I-1 e J-2, ambas risco baixo → empate no (a); **8 e 8, as mesmas 8** →
  empate no (b), **inócuo**: o campo 4 é idêntico nas duas hipóteses.
- **Campo 4 bate uma a uma.** A ausência de CMAR, Segurança Estrutural, Compartimentação e
  Plano de Emergência é correta — não existem nas Tabelas 6 da RT 05 P07.
- **Corte:** duas alturas descendentes cotadas (1,26 e 4,85); dois blocos construtivos;
  pavimento inferior e térreo **ambos com saída em nível**, logo os dois são de descarga → o
  campo "pavimento de maior população" (2.001,2 m² / 302, do térreo) está errado pelo 4.30.
  **2 pavimentos acima do solo confirmado correto**, e os níveis superiores são pavimentos.

⏳ Pendente: carga de incêndio do J em branco; distância da edificação à via pública, que
decide se o Acesso de Viatura é exigível pela nota 1.
