---
name: sol-cbmrs-navegador
description: "Operar o SOL-CBMRS no navegador: ler todas as inconformidades de uma vez pela API, lançar notificação no campo \"Outros\", limite de 2.000 caracteres da caixa Especificar, zoom utilizável e geração do PDF da página."
---

# Operar o SOL-CBMRS no navegador

Página de trabalho: `solcbm.rs.gov.br/solcbm/adm/#/analise-tecnica/<id>` — "Análise técnica
do licenciamento".

## ⭐ Ler o processo inteiro pela API (fazer isto ANTES de abrir qualquer modal)

Abrir modal por modal para ler o que já foi lançado é o maior desperdício de cota da análise:
são 3-4 chamadas e um screenshot por item. A página é um SPA Angular que carrega **tudo** de
um único endpoint REST — inclusive os textos da caixa "Especificar", que não estão no DOM.

O endpoint exige Bearer token; o token está no `localStorage` da própria página (`fetch` sem
ele devolve 401 "Token inválido"). Rodar na aba já logada:

```js
const r = await fetch('/solcbm/api/v1/adm/analise-tecnica/<ID>', {
  credentials: 'include',
  headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') }
});
window.__d = await r.text();          // guardar na página, não na conversa
JSON.parse(window.__d).numeroAnalise; // 1 = 1ª Análise
```

O `<ID>` é o número da URL (`#/analise-tecnica/300382`), não o código do processo.

⚠️ **Ler o JSON INTEIRO antes de contar qualquer coisa.** Parar na primeira fatia já fez
concluir "6 ocupações" onde havia **8** — e isso muda a contagem da ocupação definidora.

### Onde ficam os itens e as inconformidades

Tudo pende de `licenciamento` (`L`). Cada item tem `resultado`, com
`resultado.statusResultadoAtec` (`APROVADO` / `REPROVADO` / ausente = Analisar) e
`resultado.justificativas[]`, cada uma com `parametroNcs.valor` (o campo escolhido no modal —
quase sempre `"Outros"`) e `justificativa` (o texto).

| Seção na tela | Caminho |
|---|---|
| 1. Envolvidos | `L.envolvidos.proprietarios[] / .rts[] / .responsaveisUso[]` |
| 3. Características | `L.caracteristica.ocupacoes[]`, `L.caracteristica` |
| 3. Geral / Tipo edif. / Isolamento | `L.caracteristica.resultadoGeral`, `.resultadoTipoEdificacao`, `.resultadoIsolamentoRisco` |
| 4. Medidas | `L.especSeguranca.medidas[]` (nome em `.tipo.nome`) |
| 4. Laudo | `L.especSeguranca.laudo` (texto em `.txtClob`) |
| 5. Riscos específicos | `L.especsRiscos[]` (nome em `.risco.descricao`, texto livre em `.outros`) |
| 6. Elementos gráficos | `L.elemGraficos[]`, filtrar `situacao === 'ATIVO'` |

⚠️ **Chaves que já enganaram — conferir o nome antes de afirmar ausência de dado:**

1. O status é `statusResultadoAtec`, **não** `status`.
2. A inviabilidade técnica da medida é `medidas[].inviabilidade`, com valores `NAO_POSSUI` e
   `POSSUI_PARCIAL` — **não** `inviabilidadeTecnica`. Ler a chave errada devolve `undefined`,
   que já foi interpretado como "inviabilidade não declarada" e quase gerou exigência indevida.
   A tela mostra a coluna "Inviabilidade técnica": na dúvida, olhar.
3. `elemGraficos[].justificativas` existe e vem **vazio** — as justificativas reais estão em
   `.resultado.justificativas`. Um teste `o.justificativas || o.resultado.justificativas`
   falha silenciosamente, porque `[]` é truthy. Concatenar as duas listas.

### Trazer o texto para a conversa — resumir DENTRO da página primeiro

Cada chamada ao `javascript_tool` reenvia a conversa inteira; é isso que pesa, não o tamanho
do JSON. Então **o filtro roda na página e só o resumo vem para a conversa**. Nunca trazer o
objeto bruto `window.__d` em fatias (já foi feito, dezenas de chamadas de 950 caracteres).

Primeira leitura — uma chamada, resumo compacto:

```js
const L = JSON.parse(window.__d).licenciamento, st = o => o?.resultado?.statusResultadoAtec || 'ANALISAR';
const js = o => [...(o?.justificativas||[]), ...(o?.resultado?.justificativas||[])].map(j => j.justificativa.length);
JSON.stringify({
  ocup: L.caracteristica.ocupacoes.map(o => [o.ocupacao?.codigo ?? o.codigo, o.area, o.predominante]),
  med: L.especSeguranca.medidas.map(m => [m.tipo.nome, m.norma?.nome, m.inviabilidade, st(m), js(m)]),
  riscos: L.especsRiscos.map(r => [r.risco.descricao, st(r), js(r)]),
  eg: L.elemGraficos.filter(e => e.situacao === 'ATIVO').map(e => [e.descricao, st(e), js(e)])
})
```

(Conferir os nomes de chave no primeiro processo em que rodar e corrigir aqui se algum vier
`undefined` — ver as armadilhas acima.)

Só depois, **e só o que for usado**, trazer texto integral: o laudo, os campos do campo 3 que
a análise precisa, ou o texto de uma justificativa específica. Aí sim, `window.__md` em fatias
de ~900 caracteres, **várias fatias por `browser_batch`**:

```js
JSON.stringify(window.__md.slice(0, 900))
```

**Conferir gravação** depois de salvar: só status, comprimento e os últimos 40 caracteres de
cada justificativa — nunca o texto inteiro de volta.

## 🔴 Limite de 2.000 caracteres da caixa "Especificar"

A textarea tem **`maxLength = 2000`**. Preencher com o setter nativo **burla o maxlength**, e o
servidor grava **truncando sem avisar**: um texto de 2.685 caracteres foi salvo com 2.442,
terminando num ponto e vírgula solto no meio da frase — e o corte levou junto a exigência mais
próxima de disparar. O erro só apareceu ao ler a CIA gerada.

**Regra:** medir o texto antes de escrever, manter **≤ 1.950 caracteres** por caixa, e **reler
pela API depois de salvar**, conferindo comprimento e final da string.

```js
if (txt.length > 1950) throw new Error('cortar antes de lançar: ' + txt.length);
```

Não cabendo, **enxugar**: cortar a transcrição de listas normativas que o RT lê no próprio item
citado (rol de incisos, requisitos de instalação), preservando fato + ação + fundamento. Não
dividir a mesma exigência entre dois campos.

## Lançar uma notificação (sempre no campo "Outros")

Sequência que funciona, por estado do item:

| Estado atual | Caminho |
|---|---|
| **Analisar** | botão de status → **Reprovar** → modal |
| **Aprovado** | botão verde → **Reprovar** → modal (muda o status — confirmar com o usuário antes) |
| **Reprovado** (acrescentar/editar texto) | botão vermelho → **Editar** → modal com o texto já gravado |

Dentro do modal ("Reprovar medida" / "Reprovar risco" / "Reprovar prancha" / "Reprovar
característica geral"):

1. **Item novo:** clicar no checkbox **"Outros"** — marca e já expande a caixa "Especificar".
2. **Item já reprovado:** entrando por "Editar", "Outros" costuma vir marcado e **já expandido,
   com o texto carregado**. Se estiver colapsado, clicar na **setinha** à esquerda — **nunca no
   checkbox**, que desmarca e faz o texto lançado se perder.
3. Preencher a textarea. Digitar caractere a caractere é lento e erra acentuação; usar o setter
   nativo + evento `input`, que é o que o Angular escuta.

### 🔴 Achar a textarea CERTA — erro já cometido

Filtrar por "visível e vazia" **não basta**: a página tem a textarea do painel "Notas da
análise técnica" (à direita) e a de **"9. Demais inconformidades"** (no fim da página), ambas
visíveis e vazias. Um texto de notificação já foi colado em "Demais inconformidades" por causa
disso — o clique no checkbox "Outros" tinha falhado, então o modal ainda não tinha textarea
alguma, e o seletor pegou a primeira da página.

**Selecionar pelo conteúdo do próprio texto**, que é o critério mais confiável:

```js
const tas = [...document.querySelectorAll('textarea')].filter(t => t.offsetParent);
const ta = tas.filter(t => /trecho conhecido do texto/i.test(t.value))[0];
const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
setter.call(ta, texto);   // acrescentar: ta.value.replace(/\s*$/, '') + '\n\n' + novo
['input','change','blur'].forEach(e => ta.dispatchEvent(new Event(e, {bubbles:true})));
// conferir no MESMO script que as outras textareas continuam vazias
tas.filter(t => t !== ta).map(t => t.value.length);
```

⚠️ `document.querySelector('ngb-modal-window,[role="dialog"],.modal')` **nem sempre contém** a
textarea do modal — já devolveu zero textareas com o modal aberto e preenchido na tela. Étima
para confirmar o título do modal, mas não confiar nela como único caminho.

4. **Conferir antes de salvar, por texto:** no mesmo script do preenchimento, devolver o
   título do modal aberto, o comprimento da textarea preenchida e o comprimento das demais
   (têm de estar como estavam). Screenshot **só** se essa checagem vier ambígua (título não
   encontrado, mais de uma textarea com o texto).
5. Botão **Reprovar** do modal, clicado **por `ref`** obtido com `find` — **nunca por
   coordenada**: o layout reescala entre chamadas e o clique erra em silêncio (já falhou, com o
   modal seguindo aberto e nada salvo).
6. **Confirmar pela API** que gravou: status e comprimento do texto. Toast verde "Item de
   análise editado com sucesso" também serve.

Sair por **Cancelar** sempre que a intenção for apenas ler.

## Ler o texto já lançado numa medida reprovada (sem a API)

O texto **não** está no DOM com o modal fechado, e mesmo com o modal aberto **não aparece
até "Outros" ser expandido** — cada opção tem uma setinha de acordeão, e a caixa
"Especificar" só renderiza quando "Outros" abre.

1. Menu do botão vermelho **"Reprovado"** → **Editar**
2. Expandir **"Outros"** (clicar na setinha)
3. Ler a textarea **"Especificar"**
4. Sair por **Cancelar**

O texto **não se perde** ao entrar em "Editar" — carrega normalmente, só pode estar colapsado.
Para ler vários itens, preferir sempre a API.

## Custo — o que pesa de verdade

Em ordem: **screenshots ≫ leitura de página ≫ texto**. Regras de trabalho:

- Ler pela API, nunca modal a modal.
- Localizar elementos com `find` / `read_page` e clicar por `ref`, não por coordenada obtida de
  screenshot. Screenshot só quando a checagem por texto vier ambígua ou quando a imagem É o
  dado (planta, tabela em imagem). Login, modal aberto e gravação se conferem por JS/API.
- Resumo filtrado na página, texto integral só do que for usado (seção "Trazer o texto").
- Agrupar cliques, esperas e digitação num `browser_batch` único.
- Lançar as inconformidades **em lote**: as referências da página se reaproveitam e se pula o
  ciclo rolar/procurar/fotografar a cada item.
- O layout **reescala** entre chamadas: coordenada capturada num screenshot pode estar errada
  no clique seguinte. Mais um motivo para usar `ref`.

## Zoom (navegador integrado)

A página renderiza grande demais no navegador integrado e **só é utilizável com zoom 0,7**.
No Chrome externo (Claude in Chrome) isso não é necessário.

**Permanente (usar esta):** emular um viewport maior que o painel — a emulação sobrevive a
recarga e navegação. Com painel de 1022×910, `resize_window` com **1460×1300** dá escala
≈0,70. Painel diferente: `largura_emulada = largura_do_painel ÷ 0,7`. Só é desfeito com
`resize_window` no preset "desktop".

**Temporária (evitar):** `document.documentElement.style.zoom='0.7'` por script — some a
cada recarga.

## Modal "Reprovar medida" — as sugestões pré-definidas

Traz o texto de apoio *"Utilize esse espaço para justificar e ajudar o responsável técnico a
preencher corretamente"*, uma lista de inconformidades pré-definidas (checkboxes com citação
normativa) e a opção **"Outros"**. Botões: **Reprovar** e **Cancelar**. Depois de reprovada, a
medida exibe o botão vermelho "Reprovado" com menu **Aprovar / Editar / Limpar**.

🚫 **As sugestões pré-definidas estão desatualizadas** — os itens que citam nem existem mais
nas RTs vigentes. Não usar como fundamento e não reaproveitar as citações. A notificação
vai, em regra, no campo **"Outros"**, com redação própria (ver `ppci-notificacao-cia`). O
catálogo transcrito está em `workflow/sol-catalogo-inconformidades-modal.md`, e serve
**apenas para reconhecer as opções na tela**.

## Comportamentos do sistema que NÃO são pendência

- **Carga de incêndio em branco em ocupação subsidiária:** o SOL só exibe o campo de carga
  quando a ocupação é marcada como **predominante**. Branco em subsidiária é comportamento do
  sistema, não omissão do RT — só notificar quando a ocupação estiver declarada como
  predominante.
- **Área do maior pavimento e população do pavimento de maior população em 0**, em edificação
  de pavimento único: correto — o pavimento único é o de descarga (RT 02/2014, item 4.30).
- **O "²" não sobrevive à geração do PDF da CIA** — "m²" sai como "m", inclusive no cabeçalho
  do próprio SOL ("Área total construída: 748,67 m"). Escrever **"m2"**, "MJ/m2" ou "metros
  quadrados".

## Detalhes de forma

- **"campo" x "item":** as seções do processo no SOL são **campos** (campo 3, campo 4, campo 5);
  "item" só para item de norma. Manter o mesmo número de campo em toda a CIA — riscos
  específicos é o **campo 5**.
- **Sem quebra de linha dentro do parágrafo.** Texto destinado à caixa "Especificar" sai com
  cada item em **uma linha contínua**, e linha em branco **apenas entre um parágrafo e outro**.

## Gerar a cópia em PDF da página

Não há "imprimir em PDF" nas ferramentas do navegador, e captura de tela não vira arquivo.
Caminho que funciona:

1. Ler o processo pela API (acima) — melhor que `get_page_text`, porque traz também os textos
   das inconformidades, que a página não mostra;
2. montar o JSON do processo (modelo em `python3 sseg.py schema`);
3. `python3 sseg.py pdf --json <N>.json --out <N>.pdf` — reproduz as seções, tabelas e os
   selos Aprovado/Reprovado/Analisar em A4;
4. `SendUserFile` + `device_commit_files` para a pasta do processo em
   `C:\Users\55519\Desktop\Carpes\print ppci\<processo>\`.

Sem o script: montar um HTML limpo com as mesmas seções e renderizar com o Chromium do
container (`--headless --disable-gpu --no-sandbox --no-pdf-header-footer --print-to-pdf`).

Alternativa igualmente aceita: o usuário manda o print feito no navegador externo e a IA só
arquiva.

## O que a página registra (e o que não registra)

Registra: identificação dos envolvidos; localização; características (tipo de edificação,
ocupações com carga de incêndio e marcação de subsolo, áreas, pavimentos, alturas,
população, característica construtiva); medidas de segurança (medida, norma, inviabilidade
técnica, compartimentação); riscos específicos; elementos gráficos; termo de
responsabilidade; pagamentos; demais inconformidades. Cada item traz seu status
**Analisar / Aprovado / Reprovado**. No painel lateral: número da análise, dias em
análise/restantes e, da 2ª em diante, "Última CIA" e "Última análise por [analista]".

⚠️ **Não registra os textos das inconformidades** — eles ficam na caixa "Especificar" de
cada item e só são impressos na CIA. Por isso arquivar sempre os dois: `<N>.pdf` e
`CIA <N>.pdf`. Um **backup dos textos** pode ser gerado a qualquer momento a partir da leitura
pela API — útil quando o analista lançou muita coisa e quer salvaguarda antes de fechar a
análise, ou se o sistema cair.

## Cuidados

- Não clicar em nada que dispare diálogo nativo do navegador (alert/confirm) — trava a
  sessão de automação.
- Sair de modais de leitura por **Cancelar**, nunca por Reprovar/Salvar.
- Não usar "Limpar" numa medida sem o usuário pedir: apaga o texto lançado.
- Reprovar item que estava **Aprovado** muda o status — confirmar antes.
- Antes de lançar em prancha, **confirmar qual prancha** é. Duas armadilhas: a legenda do
  desenho e o título no SOL costumam ser parecidos entre si (ex.: "PORTARIA, BALANÇAS E
  ADMINISTRATIVO E SUBESTAÇÃO" x "BALANÇA RODOVIÁRIA / PORTARIA / CENTRAL DE PESAGEM / SALA DE
  MOTORISTAS"); e o campo 6 lista as versões **inativas** com a mesma descrição ("BAIXA" pode
  aparecer 3 vezes) — agir só sobre a de `situacao === 'ATIVO'`.
- O menu lateral do SOL tem itens sem permissão para o analista ("Distribuição para análise")
  que levam a "Ação não autorizada" — clicar por `ref`, não por coordenada.
- O PC do usuário não tem ferramenta de exclusão nesta sessão: PDF salvo no lugar errado
  permanece após a cópia — a exclusão é manual.