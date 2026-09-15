---
name: politica-modelo-e-custo
description: Decisão de 03/09/2026 sobre qual modelo usar em cada tipo de tarefa do SSEG — por que a rota de "modelo leve para tarefa simples" foi avaliada e descartada, e quais são as alavancas de economia que sobraram
sources: [cowork]
---

# Política de modelo e custo

> **Decisão registrada em 03/09/2026.** Motivo do registro: a hipótese "rodar tarefa simples
> em modelo leve para economizar cota" foi levantada, testada e **descartada**. Este doc
> existe para não reabrir a discussão daqui a alguns meses sem o argumento.

## O que motivou

Teste real: geração de uma notificação de ocupação subsidiária "J" que deveria ser
predominante (item 5.2.2.1 da RT 01/2024) — problema que **já tinha modelo validado no
banco**, do caso Encruzilhada do Sul.

- Modelo leve → **resposta errada**.
- Sonnet em esforço médio → resposta tecnicamente correta, mas com o entregável no meio do
  texto (o que gerou a regra de **ordem de entrega**, ver `instrucoes-projeto-espelho`).

## A conclusão: modelo leve não entra em tarefa normativa

A primeira leitura foi que preencher um modelo do banco seria tarefa barata e segura —
"lookup + preenchimento". **Está errado, e é aqui que mora o risco.**

🔴 **A escolha do modelo é mais perigosa que o preenchimento dele.** O trabalho difícil não é
copiar o texto do banco; é decidir que **este caso é o caso daquele modelo** — o depósito é
mesmo grupo "J"? a área total é o denominador certo? aplica 5.2.2.1 ou 5.2.3? Isso é
julgamento, não consulta.

E o modo de falha é o pior possível: o modelo leve copia o template **perfeitamente para o
caso errado**. Sai com item real, português impecável, formato do banco. **Não parece errado**
— e portanto não é pego batendo o olho.

**A assimetria fecha o assunto:** economiza-se talvez 3 a 5x de cota numa tarefa que já é a
barata do fluxo, contra a chance de uma exigência indefensável indo para um Responsável
Técnico com o timbre do CBMRS. O erro não custa token — custa ato administrativo. As travas de
erro das Instruções existem porque isso **já aconteceu**.

## Onde modelo leve ainda serve (e por que não compensa)

Só onde **nenhuma escolha normativa acontece** e o erro aparece na hora:

- abrir o SOL, aplicar o zoom, aguardar o código do processo;
- arquivar e nomear print, gerar o PDF da página;
- rodar `sseg.py` e reportar a saída.

Essas rodadas são minúsculas. A economia é irrelevante — não vale gerenciar troca de modelo
por causa delas.

## As alavancas que sobraram (e valem mais)

1. **Esforço, não modelo.** Baixar o esforço de raciocínio num modelo forte é mais seguro que
   trocar por um modelo fraco: mantém-se a calibragem e o conhecimento, gasta-se menos
   deliberação. Para tarefa de consulta e redação, modelo forte em esforço baixo tende a
   bater modelo leve em esforço alto, com custo parecido.
2. **Contrato de ordem de entrega.** Resposta que começa pelo entregável e não narra progresso
   é mais curta — e output é o que se paga.
3. **Modo avulso.** Conversa aberta só para uma notificação não roda o pipeline de análise
   inteiro. Ver `ppci-notificacao-cia`.
4. **Ler o registro salvo antes de perguntar.** Dado que já está no `<N>.json` do processo não
   se pergunta de novo — custa rodada e faz o usuário repetir o que já informou.
5. **Gravar no projeto uma vez, no fim.** Já registrado em `ppci-analise-processo`: numa
   sessão medida, as chamadas `Projects` foram **37% do tempo de geração**, porque
   `project_write` reescreve o documento inteiro. É o maior desperdício isolado já medido.

## O ganho que compõe

Toda tarefa cara resolvida com modelo forte **e gravada no projeto** vira tarefa barata para
sempre. Foi o que aconteceu com as tabelas em `scripts/dados/tabelas_conferidas.json` e com os
~80 modelos do banco: a notificação do 5.2.2.1 só ficou barata porque alguém pagou a análise
completa no caso Encruzilhada do Sul e registrou a redação.

Critério de gasto, então, não é *"esta tarefa é cara?"* e sim **"esta tarefa vai continuar
cara?"**. Se vai se repetir, paga-se o modelo forte uma vez e grava-se o resultado.

## Se for reabrir

Reabrir só com evidência nova de uma destas duas ordens:

- um mecanismo que torne o erro do modelo leve **visível ao analista antes do lançamento**
  (conferência automática do item citado contra `normas/`, por exemplo); ou
- medição real mostrando que as tarefas classe leve consomem parcela relevante da cota — hoje
  a suspeita é que consomem pouco, e a medição de 02/09/2026 aponta o custo para outro lado
  (geração de documento longo, não escolha de modelo).
