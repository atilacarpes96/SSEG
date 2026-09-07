---
name: notificacao-elementos-graficos-separados
description: Modelo de notificação para organização dos elementos gráficos em arquivos PDF — os quatro elementos das alíneas do item 6.3.6.1.2, blocos condicionais de isolamento de riscos, variante enxuta para plantas baixas fragmentadas, dispensa da fachada quando o isolamento é por afastamento, e a ressalva de que a exigência de arquivo único é interpretativa. Uso sob demanda, não é conferência de rotina.
aliases: [elementos-graficos-arquivos, plantas-baixas-separadas, organizacao-pdf-elementos-graficos]
sources: [cowork]
---

# Notificação — organização dos elementos gráficos em arquivos

## ⛔ Uso sob demanda

**Não é conferência de rotina.** Elementos gráficos fragmentados em vários PDFs aparecem com
frequência e **nem sempre são notificados** — é decisão do analista, caso a caso, conforme
atrapalhe ou não a compreensão do projeto. Esta redação só entra quando **o usuário pedir
uma notificação sobre isso**. Não incluir a verificação no pipeline da skill
`ppci-analise-processo` nem sinalizar proativamente no relatório de análise.

## Fundamento conferido (02/09/2026)

**RT de Implantação do SOL-CBMRS, 4ª Edição/2022 (versão corrigida)** — vigência confirmada
na página oficial em 02/09/2026: não há 5ª edição. Texto literal em
[[rt-implantacao-sol-cbmrs]].

- **6.3.6.1.2** define quatro elementos gráficos, um por alínea: **a)** implantação (planta de
  localização) com as edificações e área de risco no lote; **b)** plantas baixas de todos os
  pavimentos e/ou do pavimento tipo, quando couber; **c)** corte de todas as edificações e
  áreas de risco, com as **cotas de altura descendente e ascendente**, e detalhamento do
  isolamento de riscos **quando empregado**; **d)** fachada de todas as laterais, **sempre que
  adotada a técnica de isolamento de riscos por separação de áreas**, indicando os
  distanciamentos entre aberturas e projeções.
- **6.3.6.1.2.1** — "apenas um elemento gráfico por arquivo", em "*.pdf", **exceto as fachadas,
  que vão no mesmo arquivo dos cortes**.

O chapéu do 6.3.6.1.2 remete à coluna "A" da Tabela L.1 do Anexo "L" da RT 05 Parte 1.1/2016
para o conteúdo de cada elemento.

## ⭐ Fachada dispensável quando o isolamento é por afastamento (03/09/2026)

A alínea "d" só exige fachada **"sempre que for adotada a técnica de isolamento de riscos por
separação de áreas"** — a técnica que usa elemento construtivo corta-fogo e distanciamento
entre aberturas (RT 04/2022, itens 5.3.5 a 5.3.10, ver [[rt-04-2022-isolamento-riscos]]). Há
uma **segunda técnica**, o isolamento **por afastamento** (RT 04/2022, item 5.4.1 — distância
mínima de 5 m entre edificações), que **não depende de aberturas** e portanto não aciona a
alínea "d". Quando o processo usa isolamento por afastamento (dado que o usuário informa, a
partir da leitura da planta — não presumir), a fachada é dispensável, e **todos os cortes de
uma mesma edificação podem ser reunidos num único elemento gráfico**, sem a exceção de
6.3.6.1.2.1 sobre juntar fachada e corte, porque não há fachada para juntar.

## ⚠️ A exigência de "arquivo único" é interpretativa — dizer isso

O item 6.3.6.1.2.1 proíbe **mais de um elemento gráfico no mesmo arquivo**. Ele **não diz
literalmente** que um mesmo elemento gráfico não pode ser dividido em vários arquivos. Três
PDFs contendo cada um parte da planta baixa não violam a letra do item.

O fundamento da exigência está na **combinação** com a alínea "b": o elemento gráfico "planta
baixa" é definido como *"plantas baixas de todos os pavimentos da edificação"* — no plural e
como conjunto. Apresentá-lo fracionado entrega pedaços do elemento, não o elemento.

Nível de certeza a usar: **"a interpretação mais adequada é..."**, não "o item X estabelece
expressamente". Se o RT contestar, o argumento que sustenta é o da alínea "b" somada à
dificuldade concreta de compreensão do conjunto — por isso a redação deve **dizer qual é o
prejuízo**, não só apontar a fragmentação. Na prática, as redações aplicadas abaixo usam
"Deverá" (forma imperativa), mantendo esse cuidado apenas como orientação interna de nível de
certeza, não como redação literal a suavizar.

## ⚠️ O que NÃO está na norma (mas entrou na CIA original)

A redação original do usuário descrevia o Arquivo 1 como contendo *"a situação das edificações
no lote e a localização do lote em relação à estrada, representando também o acesso de
viaturas e o dispositivo de recalque — as duas plantas juntas"*.

A alínea "a" do 6.3.6.1.2 **não menciona** planta de situação separada, acesso de viaturas nem
dispositivo de recalque. Isso é **prática de análise**, não texto da alínea. Além disso, o
[[banco-notificacoes-padrao]] registra que o **dispositivo de recalque deve ser representado
em planta baixa** (Tabela L.1 da RT 05 Parte 1.1/2016), não na implantação.

👉 Ao reusar o modelo completo, **não apresentar esse trecho como exigência da alínea "a"**.
Ou se orienta separadamente (com o fundamento próprio de cada medida), ou se omite.

## Modelo completo — reorganização dos arquivos

Usar quando a organização precisa ser reestruturada por inteiro.

> - Oriento o Responsável Técnico a apresentar os elementos gráficos conforme o item
> 6.3.6.1.2 da RT de Implantação do SOL-CBMRS, organizados da seguinte forma:
>   - **Arquivo 1 (Implantação):** implantação (planta de localização), com a representação das
>     edificações e da área de risco de incêndio no lote;
>   - **Arquivo 2 (Planta baixa):** plantas baixas de todos os pavimentos da edificação e/ou
>     planta baixa do pavimento tipo, quando couber;
>   - **Arquivo 3 (Cortes[ e Fachadas]{condicional}):** corte de todas as edificações e áreas
>     de risco de incêndio, com a indicação das cotas de altura descendente e ascendente[, e o
>     detalhamento do isolamento de riscos]{condicional}[, juntamente com a fachada de todas as
>     laterais da edificação, indicando os distanciamentos entre aberturas e
>     projeções]{condicional}.
> - Ressalto que, conforme o item 6.3.6.1.2.1, deverá ser apresentado apenas um elemento
> gráfico por arquivo, em extensão "*.pdf", exceto a representação das fachadas, que deverá
> estar no mesmo arquivo dos cortes.

### Blocos condicionais

Os trechos `{condicional}` **só entram quando o PPCI adota isolamento de riscos** — a alínea
"c" condiciona o detalhamento a "quando empregado" e a alínea "d" a "sempre que for adotada a
técnica de isolamento de riscos por separação de áreas". Sem isolamento, o Arquivo 3 fica só
com os cortes e as cotas de altura, e some a menção às fachadas. **O mesmo vale quando há
isolamento, mas por afastamento** (ver seção ⭐ acima): a menção às fachadas some do mesmo
jeito, porque a condição da alínea "d" não se cumpre.

**Linha de chamada vermelha na implantação** (item 6.3.3.1) é **notificação própria, de
isolamento de riscos**: só se aplica a PPCI único com edificações ou áreas isoladas entre si.
Só andava junto com esta porque no processo original havia isolamento. Não colar por hábito.

### Fecho opcional

> - Destaca-se que, caso sejam identificadas novas inconformidades na representação gráfica e
> na organização das camadas, estas serão destacadas em análise posterior. Recomenda-se
> revisar toda a representação para o atendimento da norma.

Usar quando a reorganização vai gerar reapresentação completa e ainda não houve análise
detalhada do conteúdo gráfico.

## Variante enxuta — só as plantas baixas vieram fragmentadas

Quando implantação e cortes já estão corretos e o problema é apenas a planta baixa dividida:

> - Deverá reapresentar as plantas baixas em arquivo único, contendo todos os pavimentos da
> edificação, tendo em vista que foram apresentadas em arquivos distintos, o que dificulta a
> compreensão do conjunto da edificação. Conforme a alínea "b" do item 6.3.6.1.2 da RT de
> Implantação do SOL-CBMRS, o elemento gráfico compreende as plantas baixas de todos os
> pavimentos da edificação e/ou a planta baixa do pavimento tipo, quando couber, devendo ser
> apresentado apenas um elemento gráfico por arquivo, nos termos do item 6.3.6.1.2.1.

## Redação aplicada — A00024749AA002 (Encruzilhada do Sul, 1ª análise)

Cinco arquivos: implantação (1) e corte/fachada (1) corretos; **planta baixa em três
arquivos** — TÉRREO, PAVIMENTO INFERIOR e PAVIMENTO SUPERIOR. Edificação **sem isolamento de
riscos**, logo os blocos condicionais saem.

> - Deverá reapresentar as plantas baixas em arquivo único, contendo os pavimentos térreo,
> inferior e superior, tendo em vista que foram apresentadas em três arquivos distintos
> ("R00-GABRIELA-21.08.26-002.pdf", "R00-GABRIELA-21.08.26-003.pdf" e
> "R00-GABRIELA-21.08.26-004.pdf"), o que dificulta a compreensão do conjunto da edificação.
> Conforme a alínea "b" do item 6.3.6.1.2 da RT de Implantação do SOL-CBMRS, o elemento
> gráfico compreende as plantas baixas de todos os pavimentos da edificação e/ou a planta
> baixa do pavimento tipo, quando couber, devendo ser apresentado apenas um elemento gráfico
> por arquivo, nos termos do item 6.3.6.1.2.1.

## ⭐ Redação aplicada — A00002419AB001 (BRF, 1ª análise) — lançada no campo 9

Processo grande, multi-edificação, com **isolamento de riscos por afastamento** (dado
informado pelo usuário a partir da leitura da planta — não presumido). Lançado no campo 9
("Demais inconformidades"), não vinculado a item específico de campo 6, por ser orientação
geral que atravessa vários elementos gráficos. Quatro pontos, cada um sua própria fundamento:

**1. Legibilidade das linhas gráficas (várias cores, sem relação com medidas de SCI):**

> - Deverá adequar a configuração das linhas gráficas do PPCI, atualmente apresentadas em
> diversas cores, o que dificulta a identificação das informações. Conforme o item 5.2 da
> RTCBMRS nº 05, Parte 08 de 2016, a cor vermelha deve ser empregada exclusivamente para
> representar as medidas de segurança contra incêndio e informações a elas diretamente
> relacionadas; as demais informações do projeto deverão ser apresentadas em cor distinta, de
> modo a atender a legibilidade exigida pelo item 5.5 da mesma RTCBMRS.

**2. Consolidação dos cortes de uma edificação, com fachada dispensada pelo isolamento por
afastamento** — a edificação "Fábrica de Rações" tinha os cortes espalhados e duplicados em
quatro arquivos (um com corte+fachada, dois só com corte repetido, um só com fachada):

> - Deverá consolidar em um único elemento gráfico os cortes da edificação Fábrica de Rações,
> atualmente fragmentados e com conteúdo repetido nos arquivos "AUX_PI_0942_001.pdf",
> "AUX_PI_0942_002.pdf" e "AUX_PI_0942_004.pdf". A representação da fachada — exigida pela
> alínea "d" do item 6.3.6.1.2 da RT de Implantação do SOL-CBMRS apenas quando adotada a
> técnica de isolamento de riscos por separação de áreas — é dispensável neste processo, cujo
> isolamento de riscos é por afastamento, o que possibilita reunir todos os cortes em um único
> arquivo, conforme a alínea "c" e o item 6.3.6.1.2.1 da mesma RTCBMRS.

**3. Retirar planta baixa de dentro de elemento gráfico "corte"** — orientação geral, **sem
arquivo específico apontado**: nenhum dos 11 arquivos tipo CORTE do processo (AUX_PI_0942_001
a 011) está descrito, nos metadados do SOL, como contendo planta baixa. Se o usuário confirmar
qual arquivo tem esse problema (visto na leitura da planta, que é trabalho dele), a exigência
vira concreta com nome de arquivo:

> - Deverá retirar dos elementos gráficos do tipo "corte" qualquer representação de planta
> baixa, mantendo em cada arquivo apenas o conteúdo próprio do elemento, conforme o item
> 6.3.6.1.2.1 da RT de Implantação do SOL-CBMRS.

**4. Consolidação das plantas baixas de uma edificação inteira** — a "Fábrica de Rações" tinha
seus pavimentos espalhados em **nove arquivos** (005 a 013), com pavimentos partidos em partes
(2º pavto em duas; 4º pavto em três) e pavimentos distintos misturados no mesmo arquivo:

> - Deverá consolidar em um único elemento gráfico as plantas baixas de uma mesma edificação,
> reduzindo consideravelmente o número de pranchas apresentadas. Na edificação destinada à
> Fábrica de Rações, por exemplo, os pavimentos estão fragmentados em nove arquivos
> ("PPCI_PI_0942_005_REV_2.pdf" a "PPCI_PI_0942_013_REV_2.pdf"), com pavimentos divididos em
> partes (2º pavimento em duas partes; 4º pavimento em três partes) e áreas de pavimentos
> distintos reunidas num mesmo arquivo, o que dificulta a organização e apresentação por parte
> do Responsável Técnico e os ritos de análise e vistoria por parte do CBMRS. Conforme a
> alínea "b" do item 6.3.6.1.2 da RT de Implantação do SOL-CBMRS, o elemento gráfico "planta
> baixa" compreende as plantas baixas de todos os pavimentos da edificação, devendo ser
> apresentado apenas um elemento gráfico por arquivo, nos termos do item 6.3.6.1.2.1.

👉 **Como os nomes de arquivo concretos foram obtidos:** lendo a lista completa de elementos
gráficos ativos pela API do processo (`elemGraficos`, campo `tipo` + `descricao` +
`arquivo.nomeArquivo`) — não por extração de PDF nem por leitura de planta. Ver técnica de
leitura da API na skill `sol-cbmrs-navegador`.

## Cuidados de redação

Valem as regras da skill `ppci-notificacao-cia`: nomear os arquivos concretamente (é o que
torna a exigência verificável), dizer o prejuízo (aqui é o que sustenta a interpretação),
escrever "m2" em vez de "m²", e não transcrever requisito que só se verifica em vistoria.
Quando o problema é pontual, usar a variante enxuta em vez do modelo completo. Quando o
problema é orientação geral sem arquivo específico identificado, dizer isso — não inventar
nome de arquivo para "completar" a redação.
