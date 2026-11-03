---
name: it-25-2025-parte4-armazenamento-fracionado
description: IT 25/2025 do CBPMESP, Parte 4 — Armazenamento fracionado de líquidos igníferos (recipientes ≤ 450 L, tanques portáteis ≤ 2.500 L, IBC ≤ 3.000 L). Norma do RS por remissão da RT 01/2024, 4.5.1; em vigor no CBMRS desde 01/07/2025. Modalidades (itens 42 a 47), quantidades máximas (Tabelas 4.5 a 4.12), contenção e drenagem (37), extintores do M-2 (47.7.3) e linhas de espuma/resfriamento acima de 20 m³ (47.7 a 47.9)
sources: [claude-code]
---

# IT 25/2025 (CBPMESP) — Líquidos igníferos — Parte 4: Armazenamento Fracionado

✅ **Íntegra lida no PDF oficial** (`normas/pdf/IT25P4.pdf`, 59 p.), baixado da página Instruções Técnicas do site do CBMRS em 03/11/2026. Corpo em **duas colunas** (págs. 2 a 27): ler com `pdftotext` **sem** `-layout`. Págs. 28 a 34 são tabelas de chuveiros; 35 a 59, figuras (árvores de decisão e leiautes). Conversão verificada em `normas/base/IT25P4.md` (`APROVADO: true`). Ver [[00-indice-normativo]].

## Identificação e vigência no RS

- **Instrução Técnica n.º 25/2025** do Corpo de Bombeiros da PMESP — "Líquidos igníferos (inflamáveis e combustíveis)" — **Parte 4 – Armazenamento Fracionado**. "Atualizada pela Portaria nº CCB 003/800/25 publicada no Diário Oficial do Estado, de 20 de março de 2025" (pág. 1).
- **Por que vale no RS:** **RT 01/2024, item 4.5.1** — "As instalações de produção, armazenamento, manipulação e distribuição de líquidos combustíveis e inflamáveis deverão atender ao disposto na Instrução Técnica n.º 25, do Corpo de Bombeiros da Polícia Militar do Estado de São Paulo - CBPMESP, até a entrada em vigor de Resolução Técnica específica do CBMRS que regule o assunto." (conferido no PDF da RT 01/2024 em 03/11/2026). É **incorporação por citação**: a IT 25 é a norma da medida aqui, **não** referência subsidiária. Ver [[rt-01-2024-diretrizes-basicas]] (seção 4.5).
- **Edição:** o site do CBMRS (bombeiros.rs.gov.br/instrucoes-tecnicas) lista "Instruções Técnicas em vigor no CBMRS a contar de 1º de julho de 2025", entre elas a **IT 25/2025, Partes 1 a 5** (conferido na página em 03/11/2026). **Vigência por protocolo** (RT 01/2024, 3.4 e 4.3.3): PPCI protocolado para 1ª análise **antes de 01/07/2025** pode estar sob a edição anterior da IT 25. ⏳ A edição anterior **não está** no projeto.
- **Numeração contínua entre as Partes:** a Parte 4 vai do item **33 ao 49** e as tabelas são **4.x** (Tabela 4.1 a 4.24, 4.A1, 4.A2, 4.B2). Item 33 a 49 da IT 25 = Parte 4. Remete à **Parte 1** (Tabela 1.5, quantidades mínimas de extintores) e à **Parte 5** (envasamento, manuseio, operações). ⏳ Partes 1, 2, 3 e 5 **não estão** em `normas/pdf/`.

## 33 — Aplicação (literal, pág. 2)

- **33.1** Requisitos para o armazenamento de líquidos igníferos em: tambores ou outros recipientes que não excedam **450 L**; tanques portáteis que não excedam **2.500 L**; recipientes intermediários para granel (IBC) que não excedam **3.000 L** (capacidades individuais).
- **33.2** Aplica-se às transferências eventuais entre recipientes. **33.2.1** Também a recipientes de resgate de até 250 L.
- **33.3** Tanque portátil acima de 2.500 L e IBC acima de 3.000 L → **Parte 2** (tanques).
- **33.4** Não se aplica a: IBC e tanques portáteis em **áreas de processo**; combustível no tanque de veículos, aeronaves, barcos e motores; **bebidas em ocupações comerciais** em recipientes de até 5 L com total até **20 m³**; produtos de consumo com até 50 % de líquido ignífero miscível em água, em recipientes de até 5 L; líquidos sem ponto de ignição (NBR 11341); bebidas destiladas e vinhos em barris ou pipas de madeira. **33.5** Para esses casos, norma brasileira específica ou, na falta, norma internacional.

## 34 — Modalidades de armazenamento (pág. 2–3)

| Modalidade | Onde é permitida | Item | Exigências do próprio item |
|---|---|---|---|
| Armário (gabinete) | qualquer ocupação | **42** | ≤ 450 L por armário (classes I, II, IIIA); conjunto ≤ limite da área controlável (42.2) |
| Área controlável | qualquer ocupação, **exceto M-2** | **43** | Tabelas 4.5 (geral), 4.6 (especiais), 4.7 (comerciais), 4.8 (nº por pavimento); **43.7** |
| Depósito em geral com chuveiros | **só grupo J** | **44** | IT 24 até 6 m; limites do 44.4; **44.7.6** |
| Sala de armazenamento | qualquer ocupação | **45** | ≤ 45 m² por sala; Tabela 4.9; **45.9** |
| Armazenamento externo | qualquer ocupação | **46** | Tabela 4.11; **46.4.7** |
| Armazém de líquidos | ocupação **M-2** | **47** | Tabela 4.12 sem chuveiros; ilimitado com item 48; **47.4** |

Regra de passagem, repetida em cada modalidade (43.3, 44.2, 45.3, 46.2): "Caso os volumes pretendidos ultrapassem os limites estabelecidos, deverá ser aplicado outra modalidade de armazenamento." Acima de tudo isso, **47.1**: excedidos os limites de área controlável, depósito com chuveiros e sala, e sem condição de armazenamento externo → **armazém M-2** ("como ocupação principal ou mista").

**Regras gerais (34.1.x):** líquido instável = classe IA (34.1.2); evacuação pela **IT 11** e contenção/drenagem não podem obstruir as vias de evacuação (34.1.3); "armazenamento protegido" = protegido pelo item 48 (34.1.4); **não armazenar em subsolo**, salvo condição específica da própria norma (34.1.6); 1 m de traves e vigas em área desprotegida (34.1.8).

## Itens que mais aparecem na análise

**Lista de exigências de cada modalidade** (o que conferir no memorial e na planta):

- **43.7** (área controlável) — "Deverá atender as exigências de: recipientes aceitáveis, contenção e drenagem (podendo ser contenção local), ventilação, sistemas elétricos, controle de explosão, separação de materiais incompatíveis e extintores."
- **44.7.6** (depósito J com chuveiros) — a mesma lista do 43.7.
- **45.9** (sala) — "recipientes aceitáveis, contenção e drenagem (podendo ser contenção local), sistemas elétricos, controle de explosão, separação de materiais incompatíveis, extintores, compartimentação e tempo de resistência ao fogo."
- **46.4.7** (externo próximo a edificação) — "recipientes aceitáveis, contenção e drenagem (podendo ser contenção local), sistemas elétricos, controle de explosão" (o texto termina aí, sem ponto).
- **47.4** (armazém M-2) — "recipientes aceitáveis, contenção e drenagem a distância (apenas), compartimentação, tempo requerido de resistência ao fogo, ventilação, sistemas elétricos, controle de explosão, separação de materiais incompatíveis e extintores."

**Construção (36, pág. 5):** TRRF pela IT 08 e **Tabela 4.2**: área de piso ≤ 14 m² → 60 min; ≤ 45 m² → 120 min (paredes internas, tetos e pisos intermediários); armazém de líquidos → 240 min nas paredes internas, 120 ou 240 min nas externas conforme a distância (notas e/f); nota **b/c**: 120 min se só classe IIIB ou se protegido pelo item 48; nota **g**: áreas de apoio < 10 % da área do armazém isentas de TRRF. Portas corta-fogo pela **Tabela 4.3** (parede 60 → porta 60; 120 → 90; 240 → 180), normalmente fechadas (36.2) ou com fechamento automático (36.3), NBR 11742 e 11711 (36.4).

⚠️ **Tabela 4.2, linha 2, está escrita "Área de piso ≤14 m² > 45 m²"** no PDF: pela Tabela 4.9 e pelo 45.1 (sala ≤ 45 m²), a leitura é "> 14 m² e ≤ 45 m²". Erro de digitação do original — citar a linha pelo valor (120 min) e não pelo rótulo.

**Contenção e drenagem (37, págs. 5–6):**

- **37.1** regra: contenção interna + drenagem + contenção externa, com declividade, **sifão corta-fogo** e **válvula de paragem na área externa**, tudo incombustível.
- **37.2** áreas controláveis (43), depósito J com chuveiros (44), salas (45) e externo (46): a contenção **pode ser local** (sem drenagem e contenção externa). **37.3** a contenção local precisa ter o **volume total dos produtos armazenados**, ser incombustível (sem plástico), abranger toda a área e não prejudicar as rotas de fuga.
- **37.5** contenção interna por soleiras/guias/rampas de no mínimo **0,15 m**, canaletas, aberturas para drenagem ou inclinação do piso. **37.8** declividade mínima de **1 %** nos primeiros 15 m.
- **37.10 / Tabela 4.4** distância da bacia de contenção à distância até a divisa e às edificações, pela capacidade da bacia (≤ 1 m³: 1,5 m e 1,5 m … > 11.356 m³: 52,5 m e 18,0 m); bacia subterrânea: 1,0 m.
- **37.13** bacia externa = volume da **maior pilha + 50 % da água de combate**; **37.14** não conta o hidrante de edificação isenta de espuma e resfriamento.
- **37.17** bacia acima de **20 m³** → espuma (linhas, canhões ou câmaras) a **6,5 lpm/m² por 20 min**, salvo só classe IIIB.
- **37.24** saídas e rota de fuga não podem ficar expostas aos sistemas de drenagem.
- **43.10.8** área controlável em ocupação **comercial** isenta de contenção e drenagem até **20 m³**.

**Ventilação (38):** a de depósito em geral pela **IT 15** (38.1). **38.2**: nas modalidades de armazenamento **não pode haver** produção, envase, transferência ou manipulação → Parte 5.

**Elétrica (39):** sala fechada com classe I → **zona 2** (39.2, NBR IEC 60079-10-1). **Explosão (40):** classe IA em recipiente > 5 L → dispositivos de controle de explosão, projeto por CTPI (40.1), salvo sala interna. **Incompatíveis (41):** 6 m, divisória incombustível 500 mm além do material, ou armário (41.2); **oxidantes a 7,5 m** (41.4).

**Armários (42.3 e 42.7–42.11):** construção (aço nº 18 parede dupla 38 mm; madeira compensada 2,5 cm; soleira de 5 cm) e a identificação "ATENÇÃO / INFLAMÁVEL / MANTER LONGE DO FOGO", com letras de 50 mm e 25 mm.

## Quantidades máximas (tabelas lidas no md verificado; conferir na imagem da página antes de contar)

- **Tabela 4.5** (área controlável, ocupações em geral, pág. 12), em litros: IA 150 · IB e IC 450 · IA+IB+IC 450 (IA ≤ 150) · II 450 · IIIA 1.200 · IIIB 50.000. Nota 1: +100 % em armário ou latão de segurança; nota 2: +100 % com chuveiros (NBR 10897 ou NFPA 13); cumulativas; nota 4: IIIB ilimitado com chuveiros projetados pelo item 48.
- **Tabela 4.6** (ocupações especiais — F, H-2, H-3, H-6, D-1, D-2, H-5, E, A-2, A-3, pelo 43.9.1): I e II 40 L · IIIA 250 L · IIIB 450 L. **43.9.2**: acima de 40 L (I + II) ou 250 L (IIIA), só em armário e com total até 700 L.
- **Tabela 4.7** (comerciais C-1, C-2, C-3; pág. 13): sem proteção automática IA 250 L, IB a IIIA 14.250 L por área controlável (no máximo duas, separadas por parede de 60 min), IIIB 57.000 L; com proteção pela IT 23 ou IT 24, 450 L / 28.500 L / ilimitada; pelo item 48, 450 L / 113.500 L por edificação / ilimitada. **43.10.4** acima do térreo: 250 L sem proteção, 500 L com; **43.10.5** nada em subsolo; **43.10.6** recipiente > 20 L fora das áreas acessíveis ao público.
- **Tabela 4.8** (nº de áreas controláveis por pavimento): térreo 100 % / 4 áreas / 1 h; 2º pav. 75 % / 3; 3º 50 % / 2; 4º a 6º 12,5 % / 2 / 2 h; 7º e 8º 5 % / 2 / 2 h; 9º ou acima 5 % / 1 / 2 h; 1º subsolo 75 % / 3 / 1 h; 2º subsolo 50 % / 2; abaixo do 2º subsolo NP.
- **Tabela 4.9** (salas, por m² de piso): ≤ 14 m² sem proteção 85 L/m², com 215; > 14 e ≤ 45 m² sem proteção 170 L/m², com 430.
- **Tabela 4.11** (externo; pág. 17): por classe, volume e altura por pilha e distâncias — entre pilhas 1,5 m; à divisa 15,0 m (I), 7,5 m (II), 3,0 m (III); à via 3,0 m (I) ou 1,5 m (II e III). **46.3.4**: sem unidade de bombeiros, distâncias **duplicadas**; **46.3.5**: até 50 % da capacidade por pilha, reduzidas a 50 % (mínimo 1 m). **46.3.3**: nenhuma pilha a mais de **60 m de via de acesso de 6,0 m**. **46.3.10 / 46.4.6**: isolamento a **15 m**. **46.4.1**: até **4.200 L** junto a edificação da mesma administração, com parede de 120 min e sem aberturas nas distâncias das alíneas a–d.
- **Tabela 4.12** (armazém M-2 sem chuveiros; pág. 19): altura, quantidade por pilha e total por classe e tipo de recipiente (ex.: IB em recipientes 2,2 m / 5.000 L / 20.000 L; IA só em recipientes, 2.500 L). Classes misturadas: soma das proporções ≤ 100 % (47.6.3 e 47.6.4, com exemplo).

## Proteção do armazém e das áreas acima de 20 m³ (47.7 a 47.9)

- **47.7.1.1** "Todas as áreas que armazenem mais que 20 m³ de produtos igníferos (inflamáveis ou combustíveis), devem possuir uma proteção por linhas manuais de espuma e resfriamento." **47.7.1.2** compartimentos de até 20 m³ cada isentam. **47.7.1.3 / 47.7.1.4** chuveiros de água dispensam as linhas de resfriamento; chuveiros de espuma dispensam as linhas de espuma. **47.7.1.5** passou dos limites da IT → chuveiros pelo item 48.
- **47.7.3 Extintores** — **47.7.3.1** "Extintores de incêndio portáteis devem atender aos requisitos da IT 21 e as quantidades mínimas estabelecidas na parte 1 desta IT." **47.7.3.2** acréscimos: **a)** um extintor de no mínimo **40-B** do lado de fora da porta, a **menos de 3,0 m** da área interna de estocagem; **b)** um de **40-B** a **menos de 9,0 m** de qualquer área de armazenamento de classe I ou II, fora da área interna; **c)** exceção: um de **80-B** a **menos de 15,0 m**.
- **Áreas abertas (47.8):** espuma para classes I, II e IIIA acima de 20 m³ não isoladas, **duas linhas em posições opostas, até 60 m** (47.8.1.1); resfriamento para todas as classes acima de 20 m³, qualquer ponto alcançado com mangueira de **60 m** (47.8.2.2); IIIB sozinho isento (47.8.1.2 e 47.8.2.3); hidrante de 65 mm, storz, **a 15 m da área** (47.8.1.4 e 47.8.2.4); reserva de LGE (47.8.1.9 a 47.8.1.14).
- **Áreas internas (47.9):** espuma com qualquer ponto atendido por **uma linha de até 45 m** (47.9.1.1); resfriamento com mangueira de até **30 m** (47.9.2.2); IIIB isento, com a proteção da **Tabela 1.5** (Parte 1) (47.9.1.3 e 47.9.2.4).

**Tabelas de linhas (só imagem no PDF; lidas nas imagens das págs. 20 e 21 em 03/11/2026):**

| Tabela | Volume (m³) | > 20 a 60 | > 60 a 120 | > 120 |
|---|---|---|---|---|
| **4.A1** — linhas de espuma (pág. 20, logo abaixo do título) | vazão (L/min) · linhas · tempo (min) | 200 · 2 · 20 | 400 · 2 · 20 | 400 · 2 · 30 |
| tabela logo abaixo do título **"4.A2"** (pág. 21, 1ª coluna) | vazão · pressão (mca) · linhas · tempo | 300 · 45 · 2 · 60 | 800 · 45 · 2 · 60 | 800 · 45 · 2 · 90 |
| tabela **sem título** (pág. 21, 2ª coluna) | vazão · pressão · linhas · tempo | 250 · 35 · 2 · 60 | 700 · 35 · 2 · 60 | 700 · 35 · 2 · 90 |

⚠️ **Ambiguidade de diagramação — não decidir sozinho.** O título "Tabela 4.B2: Linhas de resfriamento para armazenamento fracionado em áreas fechadas" (pág. 22) está **sem tabela embaixo**, e há uma tabela de resfriamento **sem título** na 2ª coluna da pág. 21, no meio do texto de espuma de áreas internas. Qual das duas tabelas de resfriamento é a **4.A2** (áreas abertas) e qual é a **4.B2** (áreas fechadas) não está claro no PDF. Antes de notificar vazão ou pressão de resfriamento, mostrar as duas ao analista. Hipótese a conferir em outra fonte, como o site do CBPMESP ou a NBR 17505-4: 300/800 L/min a 45 mca = 4.A2, ou o contrário.

## Proteção por chuveiros (48) e demais requisitos (49)

- **48.2** os itens 48.4 a 48.10 não se aplicam a classe IA e a líquidos instáveis. **48.5 / 48.6 / 48.7** escolha da tabela (4.13 a 4.24) pelo tipo de recipiente, arranjo (rack, paletizado, prateleira) e classe, pelas árvores de decisão das Figuras 4.2 a 4.4. **48.6.6** cobertura de chuveiro de teto: 9,3 m² (I, II, IIIA) e 11 m² (IIIB). **48.9.1** suprimento de água para **120 min**.
- **49.1** "O responsável técnico [...] deve observar a NBR 17505, Parte 4, para todos os demais requisitos de armazenamento em recipientes e em tanques portáteis não mencionados na parte 4 desta IT."

## Remissões a outras IT do CBPMESP: como ler no RS

A Parte 4 remete às IT paulistas da medida: **IT 08** (TRRF, 36.1), **IT 09** (compartimentação, Tabela 4.12 nota a), **IT 11** (saídas, 34.1.3), **IT 15** (ventilação, 38.1), **IT 21** (extintores, 47.7.3.1), **IT 23 e IT 24** (chuveiros, 44.1, 48.6.5 e 48.6.6) e **IT 03** (definições, 48.4.5).

⚠️ **Aparente conflito:** no RS a medida tem norma própria. Extintores seguem a **RT 14** e saídas a **RT 11**. Chuveiros seguem a **NBR 10897 e NBR 16981** (RT 01/2024, Tabela 2, item 6). IT 08, IT 09 e IT 15 valem pela Tabela 2 (itens 1, 2 e 4). A IT 25 é a específica do armazenamento de líquidos (RT 01/2024, 4.5.1), mas a remissão que ela faz à IT 21, IT 11, IT 23 ou IT 24 não substitui a norma da medida adotada no RS.

**Interpretação mais adequada (a confirmar pelo analista):** valem os **parâmetros próprios da IT 25**, como o acréscimo de extintores 40-B/80-B do 47.7.3.2, as quantidades, as distâncias e a contenção. Para o dimensionamento geral da medida, vale a norma do RS. Precedente parecido: na IT 37, o "conforme a IT 21" do 4.4.2.4 foi lido no RS pela RT 14 (ver [[00-indice-normativo]], seção da IT 37).

## Reflexo na análise

- **Campo 4:** citar "IT 25 – CBPMESP, Parte 4" para o armazenamento fracionado de líquidos é **regular**, por causa da RT 01/2024, 4.5.1. Não é pendência nem "norma fora do índice".
- **Anexo L da RT 05 P1.1/2016:** o depósito ou a manipulação de líquidos inflamáveis é linha da **Tabela L.3** (riscos específicos). Na análise isso significa identificar e localizar o depósito em planta e representar as medidas que o protegem, conforme a coluna "A" da L.1. Ver [[rt-05-parte01-1-2016-ppci-completo]]. O que a L.3 não manda analisar (ex.: construção do armário, identificação do 42.7, gestão da bacia vazia do 37.11) é responsabilidade do RT, não notificação de análise.
- **Dados que o projeto precisa trazer para fechar a modalidade:** produto, **classe** (IA a IIIB, pela Parte 1), tipo e capacidade do recipiente, volume total por área e modalidade escolhida. Sem isso não dá para escolher a tabela. Notificar a falta desses dados, sem presumir a classe.
- **20 m³ é o limiar que muda tudo:** linhas de espuma e resfriamento (47.7.1.1), espuma na bacia (37.17) e o fim da isenção de contenção em área comercial (43.10.8).

## Armadilhas

1. **Bebida e produto de consumo em loja** (33.4): até 5 L por recipiente e 20 m³ de bebida no total, a Parte 4 não se aplica. Supermercado com bebidas não é automaticamente "depósito de inflamáveis".
2. **Área controlável não serve para M-2** (34, alínea b). M-2 segue o item 47.
3. **Depósito em geral com chuveiros só vale para o grupo J** (34; 44.1).
4. **Subsolo:** a regra é não armazenar (34.1.6). Área controlável no subsolo não pode ter classe I (43.5). Em comercial, nenhuma classe no subsolo (43.10.5). Mesmo assim, a Tabela 4.8 admite 1º e 2º subsolo para áreas controláveis em geral, então conferir a ocupação antes de notificar.
5. **Tabela 4.2, linha 2:** rótulo com erro de digitação (ver acima).
6. **Tabelas 4.A2 e 4.B2:** diagramação ambígua (ver acima).

## Notas sobre a conversão

- `normas/base/IT25P4.md`: APROVADO nas 6 checagens. V3 aponta "saltos" porque a numeração começa no 33, e números que caem no começo de linha ("3.000", "4.2", "4.200") são falsos itens. As Tabelas 4.A1, 4.A2 e 4.B2 **só existem como imagem** (págs. 20–21), e as tabelas 4.13 a 4.24 saem com cabeçalho partido. As quantidades acima foram lidas no md e batidas com a ordem das colunas, mas **contagem e valor para notificar saem da imagem da página**.
- O 33.4 do PDF repete a alínea dos "líquidos que não tenham ponto de ignição" (duas vezes, palavra a palavra). Está assim no original.
