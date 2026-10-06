---
name: "ppci-revisao-cia"
description: "Revisão final da CIA em conversa nova, antes de fechar a análise do PPCI: roda sseg.py revisar-cia e confere cada exigência na fonte primária, com fundamentação reversa. Usar quando o usuário disser \"revisa a CIA do processo A000...\", \"revisão final\" ou colar o lembrete deixado ao atualizar a pasta."
---

# Revisão final da CIA

Roda numa **conversa nova**, depois de "atualizar a pasta" no `ppci-analise-processo`. O motivo
de existir é ler a CIA de fora, sem o raciocínio que a produziu: na mesma conversa o modelo
tende a concordar com o que ele mesmo decidiu. Modelo: **Sonnet 5.5 médio**, escolhido pelo
usuário ao abrir a conversa (decisão de 30/09/2026, validada em teste controlado — ver
`workflow/politica-modelo-e-custo.md`). Durante a análise o próprio analista já confere cada
notificação, então a revisão final é uma segunda leitura, não a primeira defesa. **Opus 5.5 só
em caso realmente necessário:** tese nova sem modelo no banco que o analista não tenha
conferido na fonte, fundamento lido apenas em `normas/md/`, ou divergência entre o Sonnet e o
analista sobre um fundamento. O que pega erro aqui é abrir o PDF, não o esforço. Revisão sem
conferir na fonte primária não conta: foi assim que passou a frase errada sobre CMAR na
RT 05 P07 (registro em `workflow/ocupacao-definidora-e-tabelas-exigencias.md`, erro 5).

## Entrada

Tudo na pasta do processo, `C:\Users\55519\Desktop\Carpes\print ppci\<processo>\`. Pedir acesso
à pasta-mãe `Carpes` uma vez, como na `ppci-abertura-sessao`.

- `CIA <N>.pdf` — a CIA gerada pelo SOL;
- `CIA <N> textos.json` — o texto de cada caixa "Especificar", gravado ao arquivar;
- `<N>.json` — o registro do processo;
- `CIA <N-1>.pdf` — a CIA anterior, da 2ª análise em diante.

Faltando o `textos.json`, seguir sem ele: o script avisa o que deixa de conferir. Não abrir o
SOL só para isso.

**Os arquivos entram no script pelo disco, não pela conversa.** Na conversa entram a saída do
script e, exigência por exigência, só o texto da que estiver sendo julgada (do `textos.json`)
e o trecho do item no PDF da norma. Não abrir `CIA <N>.pdf` nem `<N>.json` inteiros na
conversa: o `textos.json` já tem o texto, e do `<N>.json` basta o campo que a exigência usa.

## 1. Script

Trazer do clone, como na seção "Ferramentas" da `ppci-analise-processo`: `sseg.py`,
`revisar_cia.py`, `tabelas.py`, `dados/indice_normas.json`, `dados/tabelas/` e os PDFs de
`sseg/normas/pdf/` das normas citadas na CIA.

```
python3 sseg/sseg.py revisar-cia --cia "CIA <N>.pdf" --textos "CIA <N> textos.json" \
        --json <N>.json --anterior "CIA <N-1>.pdf" --normas <pasta dos PDFs>
```

Marcas: `XX` corrigir antes de fechar, salvo decisão do analista · `!!` conferir · `??` falta
dado. Desde 05/10/2026 o script também aponta, na seção "Conteúdo de cada caixa", requisito de
instalação transcrito, Decreto citado junto com RT e caixa que não abre com hífen; e dá `XX` para
REITERO em 1ª análise · `OK` de item citado só diz que **o número existe no PDF**, não que o texto diz o que a
CIA afirma.

Sem sandbox (modo Chat): fazer as mesmas conferências à mão — até 1.950 caracteres por caixa,
sem quebra dentro do parágrafo, "campo" x "item", item citado no PDF, versão da norma
pela data de protocolo, medida exigida pela tabela da divisão x campo 4, REITERO x CIA anterior.

## 2. Julgamento, exigência por exigência

1. **Fundamentação reversa:** "se eu fosse o RT, qual dispositivo prova que isso é
   obrigatório?". Abrir o item no PDF (`pdftotext`) e ler o texto dele.
2. **Modelo do banco:** se a redação veio de `normas/banco-notificacoes-padrao.md`, dizer por
   que **este caso é o caso daquele modelo**.
3. **Fase e força:** análise x vistoria; obrigação x faculdade; versão da norma pela data de
   protocolo. **Requisito de instalação transcrito é erro de fase**, mesmo com o item certo: altura
   de montagem, distância do piso ou do acesso, fixação (ex.: "a 1,80 m do piso e a no máximo
   0,20 m do acesso" da sinalização de lotação, item 5.4.2.3.1.1 da RT 12; altura do acionador,
   item 8.7 da RT 18) → cortar o trecho e manter só a citação do item. No teste de 05/10/2026 todos
   os modelos deram esse texto como correto.
4. **Fundamento duplicado:** artigo do Decreto citado junto com item de RT que diz o mesmo → citar
   só o item da RT (ex.: art. 28 do Decreto × itens 5.4.2.3.1 e 5.4.2.3.1.1 da RT 12).
5. **REITERO, alteração ou complementação:** regra da `ppci-notificacao-cia`. REITERO numa 1ª
   análise é sempre erro.
6. **Forma:** cada caixa abre com quebra de linha e "- "; parágrafo numa linha só.
7. **Coerência:** nenhuma exigência desfaz outra da mesma CIA.
8. **Afirmação geral da base** ("não é pendência", "nenhuma tabela tem") que sustente
   exigência ou dispensa: conferir no PDF ou no `tab-*.json`, buscando sem acento, antes de
   aceitar.

Medida exigida pela tabela e ausente no campo 4 (`XX` do script): a nota da célula é do
analista. Mostrar o texto da nota e perguntar, como no critério (b).

## 3. Entrega

1. **Correções**, uma por bloco: campo e item, o problema em uma linha, o texto atual e o texto
   proposto pronto para colar (uma linha contínua por parágrafo, até 1.950 caracteres).
2. **O que está certo:** uma linha só ("demais N exigências conferidas no PDF").
3. **O que depende do analista:** nota de tabela, leitura de planta.

Sem reescrever exigência que está certa. Sem narrar progresso.

## Desculpas que não valem

| Desculpa | Por que não vale |
|---|---|
| "O script deu OK." | O OK só diz que o número existe no PDF, não que o texto diz o que a CIA afirma. |
| "O item citado está certo, então a exigência está certa." | Fase (instalação é vistoria), fundamento duplicado (Decreto + RT) e força (obrigação x faculdade) também são erro. No teste de 05/10/2026 todos os modelos deram como correto um texto com o item certo e o requisito de instalação transcrito. |
| "É só ajuste de redação, não precisa corrigir." | Requisito de vistoria na CIA de análise é erro de fase, não estilo. |
| "Concordo com o analista, ele já conferiu." | A revisão existe para ler de fora. Conferir no PDF do mesmo jeito. |

## Nunca

- Lançar ou alterar texto no SOL nesta conversa sem o usuário pedir.
- Gerar de novo `<N>.pdf` ou `<N>.json`.
- Dar item como conferido só pelo `OK` do script.
- Aplicar nota de tabela sozinho.