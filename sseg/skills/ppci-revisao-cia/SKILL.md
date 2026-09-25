---
name: "ppci-revisao-cia"
description: "Revisão final da CIA em conversa nova, antes de fechar a análise do PPCI: roda sseg.py revisar-cia e confere cada exigência na fonte primária, com fundamentação reversa. Usar quando o usuário disser \"revisa a CIA do processo A000...\", \"revisão final\" ou colar o lembrete deixado ao atualizar a pasta."
---

# Revisão final da CIA

Roda numa **conversa nova**, depois de "atualizar a pasta" no `ppci-analise-processo`. O motivo
de existir é ler a CIA de fora, sem o raciocínio que a produziu: na mesma conversa o modelo
tende a concordar com o que ele mesmo decidiu. Esforço recomendado: Opus alto, escolhido pelo
usuário ao abrir a conversa. Revisão sem conferir na fonte primária não conta: foi assim que
passou a frase errada sobre CMAR na RT 05 P07 (registro em
`workflow/ocupacao-definidora-e-tabelas-exigencias.md`, erro 5).

## Entrada

Tudo na pasta do processo, `C:\Users\55519\Desktop\Carpes\print ppci\<processo>\`. Pedir acesso
à pasta-mãe `Carpes` uma vez, como na `ppci-abertura-sessao`.

- `CIA <N>.pdf` — a CIA gerada pelo SOL;
- `CIA <N> textos.json` — o texto de cada caixa "Especificar", gravado ao arquivar;
- `<N>.json` — o registro do processo;
- `CIA <N-1>.pdf` — a CIA anterior, da 2ª análise em diante.

Faltando o `textos.json`, seguir sem ele: o script avisa o que deixa de conferir. Não abrir o
SOL só para isso.

## 1. Script

Trazer do clone, como na seção "Ferramentas" da `ppci-analise-processo`: `sseg.py`,
`revisar_cia.py`, `tabelas.py`, `dados/indice_normas.json`, `dados/tabelas/` e os PDFs de
`sseg/normas/pdf/` das normas citadas na CIA.

```
python3 sseg/sseg.py revisar-cia --cia "CIA <N>.pdf" --textos "CIA <N> textos.json" \
        --json <N>.json --anterior "CIA <N-1>.pdf" --normas <pasta dos PDFs>
```

Marcas: `XX` corrigir antes de fechar, salvo decisão do analista · `!!` conferir · `??` falta
dado · `OK` de item citado só diz que **o número existe no PDF**, não que o texto diz o que a
CIA afirma.

Sem sandbox (modo Chat): fazer as mesmas conferências à mão — até 1.950 caracteres por caixa,
"m2", sem quebra dentro do parágrafo, "campo" x "item", item citado no PDF, versão da norma
pela data de protocolo, medida exigida pela tabela da divisão x campo 4, REITERO x CIA anterior.

## 2. Julgamento, exigência por exigência

1. **Fundamentação reversa:** "se eu fosse o RT, qual dispositivo prova que isso é
   obrigatório?". Abrir o item no PDF (`pdftotext`) e ler o texto dele.
2. **Modelo do banco:** se a redação veio de `normas/banco-notificacoes-padrao.md`, dizer por
   que **este caso é o caso daquele modelo**.
3. **Fase e força:** análise x vistoria; obrigação x faculdade; versão da norma pela data de
   protocolo.
4. **REITERO, alteração ou complementação:** regra da `ppci-notificacao-cia`.
5. **Coerência:** nenhuma exigência desfaz outra da mesma CIA.
6. **Afirmação geral da base** ("não é pendência", "nenhuma tabela tem") que sustente
   exigência ou dispensa: conferir no PDF ou no `tab-*.json`, buscando sem acento, antes de
   aceitar.

Medida exigida pela tabela e ausente no campo 4 (`XX` do script): a nota da célula é do
analista. Mostrar o texto da nota e perguntar, como no critério (b).

## 3. Entrega

1. **Correções**, uma por bloco: campo e item, o problema em uma linha, o texto atual e o texto
   proposto pronto para colar (uma linha contínua por parágrafo, até 1.950 caracteres, "m2").
2. **O que está certo:** uma linha só ("demais N exigências conferidas no PDF").
3. **O que depende do analista:** nota de tabela, leitura de planta.

Sem reescrever exigência que está certa. Sem narrar progresso.

## Nunca

- Lançar ou alterar texto no SOL nesta conversa sem o usuário pedir.
- Gerar de novo `<N>.pdf` ou `<N>.json`.
- Dar item como conferido só pelo `OK` do script.
- Aplicar nota de tabela sozinho.
