---
name: divisao-trabalho-notificacao
description: Redações de notificação usadas em análises reais (não validadas pela chefia), terminologia campo x item, e os erros registrados — inconsistência apontada sem ler a definição normativa, exigência sem a conta, texto alongado com o que é de vistoria, e fundamento invertido na retirada de ocupação "M"
sources: [cowork]
---

# Redações reais e registros — notificação

> As **regras** da divisão de trabalho (o usuário lê a planta, a IA fundamenta e redige; a
> IA sinaliza proativamente o que dá para ver sem a planta) estão nas Instruções do projeto.
> O **procedimento** de redigir e revisar — enxugar, escolher entre artigo do Decreto e item
> de RT, cortar o que é de vistoria, REITERO, salvaguarda — está na skill
> `ppci-notificacao-cia`. Este doc guarda as **redações já usadas** e os **erros
> registrados**.

## ⭐ Terminologia da casa — "campo" x "item"

**As seções do memorial/processo no SOL são CAMPOS**: campo 1, campo 2, campo 3, campo 4…
**"Item" só se usa para item de norma** (item 5.1.2 da RT 01/2024, item 4.20 da RT 02/2014,
Nota 02 do item 6.3.6.1.2.4 da RT de Implantação do SOL).

Vale tanto na conversa quanto **na redação das notificações**: escrever "adequar a norma
indicada no campo 4 do processo", não "no item 4 do processo". Chamar campo de item confunde
o leitor justamente onde a CIA precisa ser precisa, porque na mesma frase costuma haver um
item de norma citado.

## O "²" não sobrevive à geração do PDF da CIA

Na CIA gerada pelo SOL, "m²" sai como "m" (743,00 m², 1.571,7 m² viram "743,00 m" e
"1571,7 m"). Escrever **"m2"**, **"MJ/m2"** ou "metros quadrados" na redação.

## ⚠️ Erro registrado — definição antes de geometria

Já houve exigência indevida por apontar "inversão" nos campos de altura ascendente/
descendente sem conferir o item 4.20 da RT 02/2014 — o preenchimento estava correto.
Raciocinar pela geometria aparente no lugar da definição normativa é fonte de exigência
indevida. **Antes de apontar inconsistência em dado do memorial, ler a definição oficial do
termo na [[rt-02-2014-termos-definicoes]].**

## ⚠️ Erro registrado — exigência sem a demonstração

Na CIA da 1ª análise do A00049570AA001, a notificação da ocupação definidora saiu com o
**critério** (alínea "b" do item 5.1.2 da RT 01/2024: prevalece quem exige mais medidas) mas
**sem a conta** — não dizia que J-3 exige 12 e C-2 exige 11, nem de qual tabela e coluna isso
saiu. O RT lê o critério e não tem como conferir a conclusão.

**Regra:** quando a exigência depende de uma comparação numérica, a comparação vai no texto —
número, tabela e coluna. Enunciar o critério não é fundamentar o resultado.

## ⚠️ Erros registrados na direção oposta — texto que sobra (A00024749AA002, 02/09/2026)

Dois cortes feitos pelo analista sobre redações que a IA entregou longas demais. Os dois
viraram regra na skill `ppci-notificacao-cia`.

1. **Parágrafo que não é fundamento da própria exigência.** A notificação da reclassificação
   do depósito saiu com um segundo parágrafo demonstrando que a definidora continuava sendo a
   I-1 — **cortado**. A conta que sustenta *aquela* exigência (471,00 m2 contra o limite de
   10%) já estava na primeira frase; o resto era prevenção. Se o RT trocar a definidora na
   análise seguinte, vira exigência própria, com a sua própria conta.
   👉 A regra da demonstração vale para **a conta que sustenta a conclusão notificada** — não
   é convite para explicar o raciocínio inteiro na CIA.

2. **Requisito de instalação, que é de vistoria.** A notificação da sinalização de lotação
   máxima saiu transcrevendo "instalada a 1,80 m de altura do piso acabado à base e a no
   máximo 0,20 m do acesso principal" — **cortado**, mantida a citação do item 5.4.2.3.1.1,
   que é quem diz onde instalar.
   👉 Na análise se confere o que está **declarado no processo e representado em planta**.
   Altura de montagem, distância do acesso, fixação, material e acabamento só se verificam em
   **vistoria**: cita-se o item e para por aí. A informação continua acessível pelo item.

## Redações usadas em análises reais

⚠️ **Não validadas pela chefia** — usar como ponto de partida, não como modelo. Modelos
validados ficam em [[banco-notificacoes-padrao]].

**Padronização da representação de compartimentos** (A00016097AA002, 1ª análise) — parte
dos compartimentos com ocupação/área/população e parte sem:

> - Deverá padronizar a apresentação do elemento gráfico em toda a planta baixa, informando
> a ocupação, a área e a população de cada compartimento da edificação e área de risco de
> incêndio, tendo em vista que parte dos compartimentos está representada nesse padrão (a
> exemplo do Auditório, Restaurante, Rouparia, Despensas, Cozinha e Administrativo) e parte
> não apresenta tais informações (a exemplo dos dormitórios, vestiários, circulações e
> demais ambientes), o que impede a verificação do dimensionamento realizado pelo
> Responsável Técnico e a conferência da população total informada no processo. Observar
> Nota 02 do item 6.3.6.1.2.4 da RT de Implantação do SOL-CBMRS.

**Divergência entre campo declarado e planta** (compartimentação marcada como "não" mas
representada):

> - Deverá marcar "sim" no campo de compartimentação da medida de segurança Compartimentação
> Horizontal, tendo em vista que a compartimentação encontra-se representada em planta e o
> campo está declarado como "não", devendo a informação declarada no processo corresponder
> ao que consta no elemento gráfico.

O caso inverso — indicado "sim" sem compartimentação executada — já tem modelo validado no
[[banco-notificacoes-padrao]].

**Ambiente com duas ocupações e áreas não discriminadas** (A00049570AA001, 1ª análise) — a
planta rotula "SALA COMERCIAL — 743,00 m2 (C-2/J-3), 149 pessoas", sem separar a área de cada
divisão. **Não foi localizado dispositivo que vede um ambiente ter duas ocupações** — o
ataque é pela impossibilidade de conferência, em duas frentes:

> - [campo da planta baixa] Deverá representar na planta baixa a ocupação, a área e a
> população de cada compartimento e área de risco de incêndio, tendo em vista que o ambiente
> identificado como "SALA COMERCIAL" está rotulado com área de 743,00 m2, população de 149
> pessoas e duas classificações de ocupação simultâneas ("C-2/J-3"), sem discriminar a área e
> a população correspondentes a cada uma das divisões, o que impede a verificação das
> ocupações declaradas e da população informada no processo. Observar a Nota 02 do item
> 6.3.6.1.2.4 da Resolução Técnica de Implantação do SOL-CBMRS.

> - [campo 3] Deverá discriminar a área correspondente a cada uma das ocupações declaradas no
> campo 3 do processo, tendo em vista que a planta baixa apresenta o ambiente "SALA
> COMERCIAL", com 743,00 m2, classificado simultaneamente como "C-2/J-3", sem indicar a área
> de cada divisão, o que impede a conferência da população total de 314 pessoas informada no
> processo e a correspondência entre as ocupações declaradas e as efetivamente representadas
> em planta. Cada ambiente deve ser classificado conforme a atividade nele efetivamente
> exercida, e todas as ocupações previstas no projeto devem estar descritas no campo 3 do
> processo, observando-se os conceitos de ocupação predominante e ocupação subsidiária dos
> itens 5.1 e 5.2 da RTCBMRS nº 01 de 2024.

⚠️ Decisão do analista nesse caso: **não invocar o item 5.2.2.1** (J vira predominante se
exceder 10% da área total ou 1.500 m²). O RT já declarou o J como predominante; puxar o
limiar abriria a porta para ele reclassificar o depósito como subsidiária e derrubar a
notificação da ocupação definidora. Regra geral que fica: não citar dispositivo que possa
desfazer outra exigência da mesma CIA.

**Norma de referência errada no campo 4** (A00049570AA001, 1ª análise) — Compartimentação
Horizontal citando a IT 08 (que é a de Segurança Estrutural):

> - A norma de referência informada para a medida de segurança Compartimentação Horizontal
> está incorreta. Conforme o item 4.3.1 da RTCBMRS nº 01 de 2024, até a entrada em vigor de
> Resolução Técnica específica deverão ser observadas as Normas Brasileiras e Instruções
> Técnicas dispostas na Tabela 2 da mesma RTCBMRS, em sua edição mais recente. Na Tabela 2, a
> medida Compartimentação Horizontal e Vertical remete à Instrução Técnica nº 09 do Corpo de
> Bombeiros da Polícia Militar do Estado de São Paulo, enquanto a Instrução Técnica nº 08 é a
> norma de referência da medida Segurança Estrutural em Incêndio. Deverá adequar a norma
> indicada no campo 4 do processo para a medida de segurança Compartimentação Horizontal.

### Bloco A00024749AA002 (Encruzilhada do Sul, 1ª análise) — existente regularizada

Redações **na versão final fechada pelo analista** em 02/09/2026.

**Depósito grupo "J" que excede o limiar do item 5.2.2.1** — uso direto do limiar, ao
contrário do caso Spessato: aqui o RT declarou o depósito como subsidiária, então invocar o
5.2.2.1 constrói a exigência em vez de derrubá-la.

> - Deverá reclassificar a ocupação destinada a depósito, declarada no campo 3 como
> subsidiária, para ocupação predominante, tendo em vista que a área de depósito representada
> em planta baixa é de 471,00 m2 e excede 10% da área total construída da edificação, que é
> de 3.605,26 m2. Observar item 5.2.2.1 da RTCBMRS nº 01 de 2024.

**Sinalização de lotação máxima ausente** (campo 4, Sinalização de Emergência):

> - Deverá prever a sinalização de lotação máxima de pessoas para a área de risco de incêndio
> da divisão F-8 declarada no campo 3, tendo em vista que não foi representada nos elementos
> gráficos apresentados. Observar itens 5.4.2.3.1 e 5.4.2.3.1.1 da RTCBMRS nº 12 de 2021, que
> alcançam a divisão F-8 independentemente de ser declarada como ocupação predominante ou
> subsidiária.

**Carga de incêndio de ocupação em branco** (campo 3):

> - Deverá informar no campo 3 do processo a carga de incêndio da ocupação destinada a
> depósito (grupo "J"), apresentada em branco. É a carga de incêndio que define o grau de
> risco de incêndio, conforme a Tabela 3 do Anexo "A" do Decreto Estadual nº 51.803/2014,
> critério da alínea "a" do item 5.1.2 da RTCBMRS nº 01 de 2024 para a definição da ocupação
> definidora, e o sistema registra apenas o grupo "J-1 a J-4", sem discriminar a divisão.

**Memorial descritivo da capacidade de lotação** (campo 4, Saída de Emergência) — usado
também como alavanca para o RT refazer o cálculo populacional na análise seguinte, já que o
memorial de cálculo da população exibido no SOL não é conferível:

> - Deverá apresentar o memorial descritivo da capacidade de lotação, discriminando a
> população máxima a ser registrada no APPCI, tendo em vista a ocupação da divisão F-8
> declarada no campo 3, com carga de incêndio de 450 MJ/m2 e, portanto, grau de risco de
> incêndio médio. Observar art. 27 do Decreto Estadual nº 51.803/2014.

⚠️ O art. 27 do Decreto e os itens 5.4.2.3.1 / 5.4.2.3.1.1 da RT 12/2021 foram obtidos por
extração automática em 02/09/2026 — **conferir a numeração no PDF oficial antes de lançar**.

### ⭐ Bloco A00002419AB001 (BRF Arroio do Meio, 1ª análise) — retirada de ocupação "M" indevida

Central de GLP rotulada em planta como **M-2** e ETE rotulada como **M-3**. O objetivo do
analista: tirar esses ambientes do regime de ocupação e tratá-los como **área técnica** — como
o próprio RT já faz, no mesmo projeto, com as plataformas dos silos e os túneis de serviço.

**O fundamento é o item 5.4 da RTCBMRS nº 01/2024 — Das Áreas Técnicas** (transcrito em
[[rt-01-2024-diretrizes-basicas]]). O 5.4.1 define área técnica pelos três requisitos
cumulativos (destinada exclusivamente a equipamentos · sem permanência humana · acesso restrito
só para manutenção esporádica), e o **5.4.1.1 nomeia expressamente "as centrais de GLP" e os
"túneis e galerias de serviço"** no rol exemplificativo. Enquadrado no 5.4, o ambiente não é
ocupação — logo não se rotula com grupo/divisão em planta.

⚠️ **Erro de fundamento registrado (03/09/2026):** a redação original ancorava a exigência no
**item 5.2.2.3**. O 5.2.2.3 diz o **oposto** do que se quer — é ele que obriga a ocupação "M"
subsidiária a ter medidas dimensionadas individualmente. Ele **pressupõe** que o "M" existe;
não serve para negar a classificação. **A correção é trocar 5.2.2.3 por 5.4.1.1**, mantendo o
resto do texto.

⚠️ **Erro cometido pela IA na mesma conversa, antes de o analista apontar o 5.4:** a IA
afirmou que "área técnica não é categoria normativa" e propôs fundamentar pela tabela de
classificação do Decreto. **Errado** — a busca RAG no projeto não achou o 5.4 porque ele ainda
não estava transcrito, e a IA tratou "não localizei" como "não existe". Regra que fica:
ausência de achado na base do projeto é **lacuna do projeto**, não ausência de norma — antes de
afirmar que um dispositivo não existe, abrir o PDF oficial.

Redações **na versão do analista**, com a única correção do fundamento:

> - Adequar indicação em planta da central de GLP (retirar indicação de ocupação M-2, essa
> ocupação em questão é apenas para "Edificação destinada a produção, manipulação,
> armazenamento e distribuição de líquidos ou gases inflamáveis ou combustíveis"), tendo em
> vista que a central de GLP é expressamente considerada área técnica pelo item 5.4.1.1 da
> RTCBMRS nº 01 de 2024;
> - Dessa forma oriento o RT a retirar a indicação de ocupação M-2 e tratar a central apenas
> como risco específico;

> - Adequar indicação em planta da ETE (retirar indicação de ocupação M-3, essa ocupação em
> questão é apenas para "Central telefônica, centros e estações de comunicação e
> assemelhados"), tendo em vista o disposto no item 5.4.1 da RTCBMRS nº 01 de 2024;
> - Dessa forma oriento o RT a retirar a indicação de ocupação M-3 e tratar a ETE apenas como
> área técnica com uso exclusivo de pessoas treinadas, tal como já adotado para as plataformas
> dos silos e os túneis de serviço neste mesmo projeto;

📌 Na redação original os dois itens tinham **parêntese aberto e não fechado** — sai assim na
CIA. Conferir parênteses e aspas antes de lançar.

📌 Confirmado como fonte da descrição das divisões: **M-3 = "Centrais de Comunicação"** (título
da Tabela 6M.3 do Anexo B do Decreto, em `scripts/dados/tabelas_conferidas.json`). A **Tabela 1
do Anexo "A"** (classificação quanto à ocupação), de onde sai a descrição da M-2, **ainda não
está transcrita no projeto** — conferir no PDF antes de citá-la.

### Área técnica — como a exigência se sustenta

O efeito prático que o analista busca (regime mais brando) **não vem de uma dispensa geral**,
que não existe: vem **medida a medida**, pelas notas das tabelas da própria RT 01/2024 — a nota
que afasta as exigências da RT 11 nas áreas técnicas até 140 m de percurso, e a que admite
acionador manual de alarme unicamente no acesso. Ver [[rt-01-2024-diretrizes-basicas]], seção
5.4 (localização dessas duas notas ⏳ ainda a conferir).

| Plano | Texto | Fundamento |
|---|---|---|
| **Exigência** | "retirar a indicação de ocupação M-2/M-3" | item **5.4.1 / 5.4.1.1** da RT 01/2024 |
| **Orientação** | "oriento o RT a tratar como risco específico / área técnica" | orientação — não cria obrigação |

## O que a IA sinaliza sem acesso à planta

Registro do que já se mostrou útil apontar só com o memorial/print em mãos: item do laudo
com inviabilidade justificada e sem medida compensatória proposta; medida compensatória sem
correspondência no campo 4 (ver [[analise-laudo-inviabilidade-tecnica]]); normas do memorial
divergentes do [[00-indice-normativo]]; inconsistências internas (números que não fecham,
dados faltando); e dados que faltam para uma conclusão — perguntando, nunca presumindo.
