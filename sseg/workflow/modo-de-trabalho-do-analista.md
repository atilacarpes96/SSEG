---
name: modo-de-trabalho-do-analista
description: Como o analista quer o trabalho conduzido — ritmo da sessão, quando revisar o que foi lançado no SOL, tamanho de resposta e a regra de quebra de linha ao colar no SOL. Complementa politica-modelo-e-custo (que trata de custo) e instrucoes-projeto-espelho (que trata da ordem de entrega)
sources: [cowork]
---

# Modo de trabalho do analista

> Preferências registradas ao longo de agosto e setembro de 2026. Estavam só na memória do
> Claude; passaram a doc em 14/09/2026 para viajarem junto com o projeto.
> Custo e escolha de modelo ficam em [[politica-modelo-e-custo]]; ordem de apresentação da
> resposta, em [[instrucoes-projeto-espelho]].

## Ritmo da sessão

- **Meta: dois PPCI analisados por sessão**, dentro da janela de 5 horas. Às vezes o próprio
  workflow consome a cota antes disso — é o problema que [[politica-modelo-e-custo]] ataca.
- **Conversa avulsa é um modo legítimo:** abrir uma conversa só para gerar uma notificação
  específica, sem rodar o pipeline de análise inteiro. Ver `ppci-notificacao-cia`.

## Revisão do que foi lançado

**Revisar as notificações lançadas no SOL só no fim da análise**, não a cada uma que se lança.
Interromper a cada lançamento quebra o ritmo e gasta rodada. A conferência do texto contra o
fundamento continua sendo feita **antes** de lançar cada uma; o que fica para o fim é a
releitura do conjunto.

## Tamanho de resposta

As respostas costumam ser **assertivas, mas extensas demais**. O corte vem antes do envio, não
depois do pedido:

- entregável no topo, em bloco citável;
- fundamento e "como cheguei ali" depois, separados, para poder pular;
- observação lateral rotulada, no fim;
- **sem narração de progresso** ("localizei o modelo...", "vou consultar...").

## ⭐ Redação destinada ao SOL — quebra de linha

Texto que vai ser colado na caixa do SOL (inconformidade, "Especificar") **não pode ter quebra
de linha dentro do parágrafo**: cada item é uma linha contínua, com linha em branco apenas
**entre** parágrafos. Quebra interna vira erro de formatação ao colar.

O limite da caixa é de **2.000 caracteres** — ver a skill `sol-cbmrs-navegador`.

⚠️ As skills (`ppci-analise-processo`, `ppci-notificacao-cia`, `sol-cbmrs-navegador`,
`ppci-abertura-sessao`) ficam na conta do Claude. Desde **15/09/2026** há uma **cópia de
backup** em `sseg/skills/` deste repositório — cópia, não a fonte: editando a skill na conta,
atualizar a cópia. Regra operacional que precise sobreviver: registrar também como doc aqui.

## Terminologia

As seções do memorial/processo no SOL são **"campo"** (campo 2, campo 3, campo 4...).
**"Item"** só para item de norma. Vale também na redação das notificações.
