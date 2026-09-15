---
name: ppci-notificacao-cia
description: "Redigir e revisar inconformidades da CIA a partir do banco validado, com checklist de fundamento, escolha da norma a citar, corte do que é de vistoria, REITERO e salvaguarda."
---

# Notificação / inconformidade para a CIA

## Quando disparar

"escreve a notificação", "melhora esse texto", "ficou boa?", "revisa essa exigência",
"como eu notifico isso", CIA, Comunicação de Inconformidade, reprovar medida, campo
"Outros", caixa "Especificar", REITERO, "já tinha notificado isso" — ou o usuário simplesmente
cola um texto de notificação.

## Ordem obrigatória

1. **Banco primeiro.** Consultar `normas/banco-notificacoes-padrao.md` (~80 modelos já
   validados pela chefia, extraídos literalmente de documento real — alta confiabilidade).
   Se o problema já tem modelo, **usar o texto e a norma exatamente como registrados**.
2. **Só então pesquisar do zero** na RT, conferindo o dispositivo no PDF oficial.
3. Nunca começar pela redação. Primeiro o fundamento, depois o texto.

## Divisão de trabalho

Quem identifica a irregularidade na planta é o **usuário**. A IA entra depois: aponta o
dispositivo que fundamenta e propõe o português formal. Mas a IA **deve** recomendar
mudanças em notificações já redigidas quando achar relevante — inclusive nas que o usuário
escreveu por conta própria.

## Estrutura da exigência

Toda notificação responde três coisas: **o que está errado** + **o que deve ser feito** +
**por quê** (fundamento).

```
- Adequar [elemento], devendo [ação específica], conforme [norma/item].
- Apresentar/representar/esclarecer [informação], tendo em vista que [problema
  identificado], conforme [RT/item].
- Deverá [ação], tendo em vista que [problema], observando [dispositivo].
```

Dizer **qual é o problema**, não só a solução. Nomear o objeto (qual medida, qual
compartimento). Evitar jargão interno ("campo 4" → "campo '4. Medidas de Segurança'").
Manter consistência de estilo entre os itens da mesma CIA ("Deverá..." em todos).

## ⭐ Enxugar — a redação para no fundamento

O que está errado + o que fazer + o dispositivo, **e para**. Não acrescentar parágrafo
explicando consequências, antecipando o que o RT poderia fazer errado depois, ou reforçando
conclusões que não são objeto daquela exigência. Duas ou três frases é o tamanho normal.

A regra da **demonstração** (quando a exigência depende de comparação numérica, a conta vai
no texto — número, tabela e coluna) vale para **a conta que sustenta a conclusão notificada**,
nunca como convite para explicar o raciocínio inteiro na CIA.

## ⭐ Fase de análise x vistoria — o que NÃO entra na redação

Na análise se confere o que está **declarado no processo e representado em planta**. Requisito
de **instalação e execução** — altura de montagem, distância do acesso, fixação, material,
acabamento — só se verifica em **vistoria**, e por isso **não se transcreve na CIA de
análise**: cita-se o item e para por aí. O RT lê o item.

Registro (A00024749AA002, 02/09/2026): a notificação da sinalização de lotação máxima saiu
primeiro transcrevendo "instalada a 1,80 m de altura do piso acabado à base e a no máximo
0,20 m do acesso principal" — **o analista cortou**, mantendo a citação do item 5.4.2.3.1.1,
que é quem diz onde instalar. A informação continua acessível pelo item; a exigência fica
concisa e no escopo da fase.

**Briçada de incêndio segue a mesma lógica na análise: conferência meramente documental** —
basta estar prevista no campo de medidas.

## ⭐ Artigo do Decreto x item da RT — qual citar

Quando **o artigo do Decreto e um item de RT específica dizem a mesma coisa, citar apenas o
item da RT**. A notificação sai pelo campo 4, organizado por medida de segurança com a norma
que o Responsável Técnico usou para dimensionar — notificar pela mesma normativa mantém a
exigência dentro do quadro em que ele trabalhou e evita empilhar fundamento redundante.

O Decreto continua sendo o fundamento citado **quando não há item de RT equivalente** (ex.:
art. 27, memorial descritivo da capacidade de lotação; Tabela 3 do Anexo "A", grau de risco
de incêndio pela carga).

## Onde a notificação entra no SOL

Em regra, no campo **"Outros"**, com redação própria. As opções pré-definidas do modal estão
desatualizadas — citam itens que não existem mais nas RTs vigentes. Ver
`sol-cbmrs-navegador` e `workflow/sol-catalogo-inconformidades-modal.md`.

⚠️ Algumas opções de texto fixo do SOL trazem fundamento genérico embutido ("exigida
conforme a legislação e regulamentação aplicáveis") que pode **contradizer o caso
concreto** — quando a exigência nasce do laudo de inviabilidade e não da tabela do Decreto,
o campo "Especificar" precisa corrigir isso, sob pena de o RT contestar com razão.

## Detalhes de forma

- **"campo" x "item":** as seções do processo no SOL são **campos** (campo 3, campo 4);
  "item" só para item de norma.
- **O "²" não sobrevive à geração do PDF da CIA** — "m²" sai como "m". Escrever **"m2"**,
  "MJ/m2" ou "metros quadrados".
- **Sem quebra de linha dentro do parágrafo.** Texto destinado à caixa "Especificar" sai com
  cada item em **uma linha contínua**, e linha em branco **apenas entre um parágrafo e
  outro**. Quebra interna desformata na colagem. Vale para a saída entregue ao usuário, não
  para este arquivo.
- **Linguagem direta.** Ordem direta, primeiro o que fazer e depois o porquê; evitar
  "tendo em vista que", "decorre de", "ressalvadas as hipóteses ali previstas". Texto
  rebuscado faz o RT não entender a exigência. ⚠️ Exceção: **parágrafo de fundamento vindo
  do banco validado pela chefia não se reescreve** — é a frase que o RT reconhece e a que
  sustenta a exigência se houver contestação. Simplificar só o texto de autoria própria.

## REITERO

Usar **apenas** quando a mesma irregularidade já foi objeto de notificação anterior e não
foi adequadamente corrigida — nunca só porque existe nova análise. Distinguir:

- **alteração** — a notificação anterior estava errada ou incompleta;
- **reiteração** — a exigência continua válida e não foi atendida;
- **complementação** — novo elemento revelou outro problema.

## Cláusula de salvaguarda

Usar com cautela, quando o projeto está incompleto/ambíguo ou o uso futuro não está claro:

> Tendo em vista que não ficou claro o que o Responsável Técnico pretende apresentar com o
> projeto, caso sejam incluídas ou identificadas novas ocupações, áreas de risco ou outras
> características não demonstradas nesta análise, poderão ser exigidas novas adequações e
> medidas de segurança contra incêndio nas análises posteriores, inclusive em itens que
> eventualmente já tenham sido considerados atendidos nesta análise.

## Revisar notificação já escrita

Nunca só "melhorar o português". Conferir, nesta ordem:

- [ ] O fundamento citado **existe** e é o **mais específico** para o caso?
- [ ] Havendo artigo do Decreto e item de RT dizendo o mesmo, ficou só o item da RT?
- [ ] A exigência é realmente **obrigatória** — ou é faculdade/recomendação?
- [ ] Diz **qual é o problema**, não apenas a solução?
- [ ] Nomeia o objeto (qual medida, qual compartimento, qual prancha)?
- [ ] Está no escopo da **fase de análise** — sem transcrever requisito de instalação que só
      se verifica em vistoria?
- [ ] Cortou parágrafo explicativo que não é fundamento da própria exigência?
- [ ] A versão da norma corresponde à **data de protocolo** do PPCI?
- [ ] REITERO só foi usado para exigência anterior não atendida?
- [ ] Está proporcional — não exige mais do que a norma determina?
- [ ] É executável — o RT entende o que apresentar?
- [ ] É consistente com as demais exigências da mesma CIA e com as análises anteriores?
- [ ] Evita jargão interno do sistema e escreve "m2" em vez de "m²"?

## Padrão de qualidade

Específica · verificável · fundamentada em dispositivo real · proporcional · executável ·
consistente · **curta**.

## Redações de referência

Modelos **validados pela chefia**: `normas/banco-notificacoes-padrao.md`, organizados por
categoria (ART/RRT, Procuração, Características, Acesso de Viaturas, Alarmes, Extintores,
Hidrantes, Isolamento, Saídas, Riscos Específicos, Elementos Gráficos, Demais).

Redações **usadas em análises reais mas ainda não validadas** (ponto de partida, não
modelo): `workflow/divisao-trabalho-notificacao.md` e
`workflow/analise-laudo-inviabilidade-tecnica.md`.

## Nunca

- Citar item obtido por extração automática de PDF sem conferir no PDF oficial.
- Reaproveitar a citação normativa das opções pré-definidas do SOL.
- Apresentar recomendação técnica como obrigação legal.
- Transcrever na CIA de análise requisito de instalação/execução que só se verifica em
  vistoria — citar o item basta.
- Citar dispositivo que possa desfazer outra exigência da mesma CIA.
- "Atualizar" a citação de um processo antigo para a versão mais recente da RT sem
  confirmar a data de protocolo.
- Criar exigência por analogia quando não localizou o fundamento — dizer que não localizou.