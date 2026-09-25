---
name: ocupacao-definidora-e-tabelas-exigencias
description: Onde estão as tabelas de exigências (agora fatiadas por grupo, uma consulta = um arquivo pequeno), como as notas entram na contagem e por que o critério (b) para o pipeline, os erros de leitura já cometidos, e os casos Hotel Valler, Spessato, Encruzilhada do Sul e Condomínio Residencial do Parque
sources: [cowork]
---

# Tabelas de exigências — o que o projeto já tem

> O **procedimento** (como achar a definidora no print, como rotear, como conferir se o RT
> acertou) vive na skill `ppci-analise-processo`. Este doc é **registro**.

## ⭐ Estrutura nova (08/09/2026) — ler só o arquivo do grupo

Antes, as duas fontes viviam num único doc, `scripts/dados/tabelas_conferidas.json`. Toda
análise carregava 48 tabelas para consultar uma. Agora estão **fatiadas em
`scripts/dados/tabelas/`**, 30 arquivos:

| Arquivo | Conteúdo |
|---|---|
| `tab-00-indice.json` | **Ler primeiro.** Mapa `divisão → {arquivo, tabela, bloco}` nas duas fontes, colunas válidas, regra de contagem, aviso das notas, linhas de medida por fonte |
| `tab-b-<GRUPO>.json` | Tabelas 6X do **Anexo B do Decreto** daquele grupo (A…M). Ex.: `tab-b-C.json` = 6C; `tab-b-J.json` = 6J.1 + 6J.2 |
| `tab-rt05-<GRUPO>.json` | Idem para o **Anexo A da RT 05 Parte 07/2025** |
| `tab-b-tabela5.json` · `tab-b-tabela7.json` | Tabela 5 e Tabela 7 do Anexo B |
| `tab-rt05-tabela5.json` · `tab-rt05-tabela7.json` | Idem RT 05 P07 |
| `linhas-conferidas.json` | As linhas com a **nota já aplicada** ao caso, os grupos por tabela e os erros de leitura registrados |

**Consulta típica:** `tab-00-indice.json` → o mapa aponta o arquivo → abrir só ele. Uma
conferência de C-2 lê o índice + `tab-b-C.json`, e nada mais.

`scripts/dados/tabelas_conferidas.json` **continua no projeto, intacto, como origem** —
🚫 **não abrir em análise.** É ele o custo que a fatiação veio eliminar.

Validação da migração (08/09/2026): `json.load` nos 30 arquivos; comprimento de cada linha
de medida = 6 × nº de blocos; conjunto de tabelas por fonte idêntico ao original (24 + 24);
comparação célula a célula com o original, **zero diferença**. `scripts/tabelas.py` foi
atualizado para a estrutura nova e conferido contra a antiga em 351 chamadas, com saída
idêntica nos 48 códigos de divisão reais.

| Situação de existência | Prefixo | Fonte |
|---|---|---|
| **Existente regularizada** | `tab-rt05-*` | Anexo A da **RT 05 Parte 07/2025** |
| A construir · existente **não** regularizada | `tab-b-*` | Anexo B do **Decreto 51.803/2014** (consolidado até o Dec. 57.967/2024) |

**Como resolver uma célula:** cada tabela guarda `divisoes` (os blocos de coluna, na ordem) e
`medidas` (a fila inteira de células, 6 por bloco). Índice = `(bloco × 6) + coluna`, com as
colunas em `Térrea | H≤6 | 6<H≤12 | 12<H≤23 | 23<H≤30 | Acima de 30`. A **Tabela 5** é
diferente: as colunas são **por grupo**, não por altura — 10 colunas na RT 05 P07 e 11 no
Anexo B, que traz F-7 em separado. A **Tabela 7** é texto livre, transcrita linha a linha.

O script `scripts/tabelas.py` faz essa resolução pela linha de comando.

Continuam exigindo imagem apenas a **Tabela 4** (roteamento) e as **Tabelas 6M.1, 6M.2, 6M.4
e 6M.5**, cujo eixo não é altura (ex.: 6M.1 usa extensão em metros, para túnel).

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
4. **Linhas perdidas pelo parser no Anexo B:** "Chuveiros Automáticos" da 6C (achado em
   16/09/2026, nota 10 órfã) e "Alarme de Incêndio" da 6A (21/09/2026, nota 3 órfã). Sinal
   comum: **nota específica que não aparece em nenhuma célula**. As duas foram conferidas no PDF
   e estão na fonte (`tabelas_conferidas.json`, chave `_correcoes_na_fonte`) desde 24/09/2026.
5. **24/09/2026 — generalização falsa sobre a RT 05 P07.** A base dizia que as tabelas dessa
   RT não têm Segurança Estrutural, CMAR, Compartimentação Vertical nem Controle de Fumaça, e
   que a falta delas no campo 4 não é pendência. Vale para as 6I e 6J, as únicas conferidas no
   texto; a Tabela 5, a 6F.3, a 6L.1, a 6M.1 e a 6C desmentem, e o CMAR é exigido para F-5/F-6
   e L. Achado ao conferir o gabarito de um teste de modelos contra os `tab-rt05-*.json` e o
   PDF. Corrigido em [[rt-05-parte07-2025-edificacoes-existentes]] e na skill
   `ppci-analise-processo`. Sinal comum com o item 3: afirmação geral que ninguém conferiu na
   norma inteira. Nos JSON os nomes estão sem acento (`Seguranca`, `Fumaca`, CMAR por
   extenso): buscar sem acento.

**Método:** `pdftotext -layout` sobre o PDF oficial **vigente** — conferir "atualizado até" na
capa antes de confiar. Tendo imagem e PDF, cruzar os dois.

## ✅ Linhas com a nota já aplicada (registro de caso)

Estão em `scripts/dados/tabelas/linhas-conferidas.json`, chaves `linhas` (Anexo B) e
`linhas_rt05_p07`. Diferente da transcrição, aqui a **nota já foi aplicada ao caso concreto** —
por isso a contagem pode diferir da contagem crua de células.

**Anexo B · 6B / B-1 / 6<H≤12 → 12 medidas.** Acesso de Viaturas; Segurança Estrutural;
Compartimentação Horizontal (X¹); CMAR; Saídas; Brigada; Iluminação; Detecção (X⁸); Alarme
(X⁹); Sinalização; Extintores; Hidrantes.

**Anexo B · 6F.3 / F-8 / 6<H≤12 → 10 medidas.** Sem Compartimentação, Plano de Emergência,
Detecção, Chuveiros e Controle de Fumaça.

**Anexo B · 6C / C-2 / Térrea → 12 células, 11 incondicionais.** A transcrição marca **13**
células; a diferença é o **Plano de Emergência (X⁸)**, que a nota 8 restringe à Divisão C-3 e
portanto **sai** da contagem de C-2. Das 12 restantes, a Detecção é X⁹ (só depósitos > 750 m²):
não verificada a condição, a contagem aplicável cai para **11**. ⭐ É o exemplo vivo de por que
a nota não se aplica sozinha.

**Anexo B · 6J.2 / J-3 / Térrea → 12 medidas, todas incondicionais.** Cabeçalho declara
**J-3 = risco médio**.

**RT 05 P07 · 6I.1 / I-1 / H≤6 → 8** e **6J.1 / J-2 / H≤6 → 8** — e **as 8 são as mesmas**.

**Anexo B · 6I.1 / I-2 / 12<H≤23 → 12 medidas, todas incondicionais.** Acesso de Viaturas;
Segurança Estrutural; **Compartimentação Vertical**; CMAR; Saídas de Emergência; Plano de
Emergência; Brigada; Iluminação; Alarme; Sinalização; Extintores; Hidrantes. Não exigidas:
Detecção, Chuveiros Automáticos, Controle de Fumaça. **Compartimentação Horizontal não é linha
da Tabela 6I.1** — só existe para I-3 (Tabela 6I.2). Caso: A00031079AA002.

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
  não foram conferidas. ✅ Confirmado com caso concreto: 300 MJ/m² exatos = **baixo** (não
  entra no médio, que só começa acima de 300) — foi o que decidiu a definidora sem empate no
  caso A00031079AA002 (I-2 = 1000 MJ/m² médio × A-2 = 300 e G-1 = 200, ambas baixo).
- **RT 02/2014, item 4.20 "Altura da edificação"** ✅ literal: *"a) altura ascendente é a
  medida em metros entre o ponto que caracteriza a saída ao nível da descarga (…) ao ponto
  mais baixo do nível do piso do pavimento mais baixo; b) altura da edificação ou altura
  descendente (…) ao ponto mais alto do piso do último pavimento."*
- **RT 02/2014, item 4.30 "Área do maior pavimento"** ✅ literal: *"Área do maior pavimento da
  edificação, **excluindo o da descarga**."* ⚠️ O item define **área do maior pavimento**; a
  extensão ao **pavimento de maior população** vem do modelo validado do
  [[banco-notificacoes-padrao]] — usar a redação do banco, não paráfrase.
- **Nota geral "c" da Tabela 6C (Anexo B)** ✅ literal: *"Para edificações sem ventilação
  natural (janelas) exige-se controle de fumaça."* ⚠️ **Não é regra de subsolo** — subsolo é a
  nota geral "a", que remete à Tabela 7. A "c" alcança a edificação inteira. A mesma redação
  está na nota geral "g" da Tabela 5, também para edificação. Antes de exigir, conferir as
  aberturas em planta: havendo janelas, a nota não aciona.

## Caso registrado — Hotel Valler (A00016097AA002)

Duas predominantes, **B-1** (carga 500, definidora declarada) e **F-8** (carga 450), ambas
grau médio → empate no (a). Área 6.233,53 m², altura descendente 9,08 m → **Tabela 6B, coluna
6<H≤12** (Anexo B). ✅ Validado: B-1 exige 12 contra 10 do F-8, e as 12 batem com o campo 4.
Altura descendente 9,08 m com zero subsolos é correta — foi aqui que nasceu a trava do 4.20.

## Caso registrado — Pavilhão Spessato (A00049570AA001), Encantado ✅ ENCERRADO

PPCI **a construir**, 1.571,7 m², **2 pavimentos com descarga própria em cada um** → alturas
0,00 m e pavimento de maior população zerado, ambos corretos. Área > 750 m² e altura 0,00 →
**coluna Térrea**.

**1ª Análise (CIA de 01/09/2026), 4 inconformidades:** ocupação J deveria ser a definidora
(5.1.2 "b"); discriminar a área de cada ocupação no campo 3; norma da Compartimentação
Horizontal era IT 08, devia ser **IT 09** (Tabela 2 da RT 01/2024 — IT 08 é Segurança
Estrutural); representar ocupação, área e população por compartimento na planta baixa.

**2ª Análise (08/09/2026) — aprovada.** O RT **retirou a ocupação J-1 a J-4 do campo 3 e o
depósito da representação** (o analista confirmou: não haverá depósito), acrescentou **F-8
Restaurantes como subsidiária** (as três copas), corrigiu a norma para IT 09, substituiu a
planta baixa e **retirou o Plano de Emergência** do campo 4 sem ter sido notificado.

⭐ **A retirada do Plano de Emergência estava certa** — nota 8 da 6C o restringe à C-3. Foi a
consequência correta da mudança de definidora: **J-3/Térrea = 12 incondicionais; C-2/Térrea =
11**, e a diferença entre as duas listas é exatamente o Plano de Emergência. Definidora final:
**C-2 "Lojas de departamentos ou magazines"**, 800 MJ/m², risco médio. Campo 4 com 11 medidas,
batendo uma a uma. Detecção (X⁹) não exigível: sem área de depósito declarada.

**Planta conferida (as duas versões diferiam APENAS no rótulo "C-2/J-3" → "C-2"):** Térreo I
785,85 m² / 155 pessoas (sala 751,73 m² C-2 = 150 + copa 5,15 m² F-8 = 5); Térreo II 785,85 m²
/ 159 pessoas (sala 743,00 m² C-2 = 149 + copas 4,13 e 5,15 m² F-8 = 5 + 5). Total 1.571,70 m²
e **314 pessoas**, fechando com o campo 3. Densidades implícitas: **C-2 = 1 pessoa / 5 m²**,
F-8 = 1 pessoa / m². **20 aberturas de 3,00 × 1,50 m** → há ventilação natural, nota geral "c"
não aciona, Controle de Fumaça corretamente fora do campo 4.

⚠️ O memorial de cálculo do SOL exibia só 14,43 m² / 15 pessoas (as três copas F-8) contra os
314 declarados — **não é erro do projetista**, é a limitação de campos do SOL; a população se
confere pela tabela "Geral" do campo 3 e pela planta. Não notificar.

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

## Caso registrado — Condomínio Edifício Residencial do Parque (A00031079AA002), Estrela ✅ ENCERRADO

Existente **não regularizada** (construção entre 27/04/1997 e 26/12/2013), protocolo
**15/11/2025** (marco "Número do licenciamento gerado"), 3.439,11 m², altura descendente
18,5 m, 7 pavimentos acima do solo, sem subsolo → **Tabela 6I.1, coluna 12<H≤23** (Anexo B —
não regularizada).

Três predominantes sem isolamento: A-2 (carga 300, risco baixo), I-2 (carga 1000, risco médio,
definidora), G-1 (carga 200, risco baixo). Sem empate no critério (a) — I-2 vence isolada.

**1ª Análise (CIA de 18/03/2026)**, 6 pendências: adequar nº de pavimentos (áreas técnicas não
contam); representar Acesso de Viaturas em planta; retirar marcação "sim" de Compartimentação
Horizontal; CMAR e Iluminação com norma desatualizada; apresentar inclinação da rampa da saída
da padaria (5%–8,33%, item 5.6.3.1 da RT 11 P01/2016 c/c NBR 9050 6.6.2.1).

**2ª Análise (11/09/2026) — enviada como CA para homologação.** As 6 pendências corrigidas: 7
pavimentos (reservatório fora da contagem, RT 02/2014 item 4.20/4.30); Implantação nova com
símbolos "AV" nos dois acessos à via pública; CMAR → RT 09/2025, Iluminação → RT 13/2025
(ambas já vigentes na data de protocolo); rampa da padaria corrigida (confirmado pelo usuário);
Compartimentação Horizontal sem mais o "sim".

⭐ **Achado sobre a tela de análise técnica do SOL, campo 4 — coluna rotulada "Inviabilidade
técnica":** os valores não são "Sim/Não" nem status de posse física da medida. **"Possui
total" / "Possui parcial" = grau de INVIABILIDADE TÉCNICA reconhecida** (vinculado ao laudo de
inviabilidade deferido), não "medida totalmente implantada". Neste caso, Compartimentação
Vertical (exigida pela Tabela 6I.1 para I-2/12<H≤23) aparecia como "Possui total" mesmo o laudo
deferido dizendo expressamente que a edificação "não possui" a medida implantada — a marcação
estava certa, o rótulo da coluna é que confunde. Compartimentação Horizontal recebeu o mesmo
tratamento (a RT trocou "sim" por essa marcação), ainda que o laudo, para essa medida
especificamente, argumente **não exigibilidade por área** e não peça inviabilidade — o usuário
confirmou que essa troca resolveu a pendência da CIA anterior mesmo assim. **Confirmar esse
significado com o usuário a cada novo caso** — a tela não expõe o detalhe por leitura de texto
(`get_page_text`), só abrindo o formulário completo do lançamento, que os tools de navegador
não acessaram neste caso (o dropdown do botão "Analisar" só oferece Aprovar/Reprovar).

## Padrão que se repete em ocupação mista C + J

Nos dois casos com depósito (Spessato e Encruzilhada), a divisão do grupo **J venceu ou
tenderia a vencer o critério (b)**, porque as tabelas 6J trazem Plano de Emergência
incondicional onde a 6C o restringe à C-3. Vale como primeira hipótese de trabalho — **nunca
como conclusão**: a contagem se refaz em cada caso, com as notas lidas.
