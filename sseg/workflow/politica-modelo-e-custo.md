---
name: politica-modelo-e-custo
description: Decisão de 03/09/2026 sobre qual modelo usar em cada tipo de tarefa do SSEG — por que a rota de "modelo leve para tarefa simples" foi avaliada e descartada, e quais são as alavancas de economia que sobraram (revisada em 25/09/2026)
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

## Onde modelo leve ainda serve

Só onde **nenhuma escolha normativa acontece** e o erro aparece na hora:

- abrir o SOL, aguardar o código do processo;
- arquivar e nomear print, gerar o PDF da página;
- rodar `sseg.py` e reportar a saída;
- conversa só de sincronização (copiar arquivos do clone para o projeto, `git pull`/push).

Dentro de uma conversa de análise essas rodadas são minúsculas e não vale trocar de modelo.
Mas **conversa aberta só para isso** (ex.: "Atualizar projeto com arquivos") pode abrir em
Sonnet ou Haiku.

## As alavancas que sobraram (e valem mais)

1. **Conversa curta: uma por processo, uma por tarefa.** Cada mensagem reenvia o histórico
   inteiro, então o fim de uma conversa longa custa muito mais que o começo. Arquivou a CIA,
   a conversa acabou; ajuste posterior abre conversa nova lendo `processos/<N>.md`, não
   buscando em conversa antiga (medição de 25/09/2026, abaixo).
2. **Esforço, não modelo.** Baixar o esforço num modelo forte é mais seguro que trocar por um
   modelo fraco: mantém-se a calibragem e o conhecimento, gasta-se menos deliberação. Desde o
   Opus 5.5 (24/09/2026), **toda conversa de análise abre em Opus médio**, o padrão do modelo,
   que a Anthropic mede como igual ou melhor que o Opus 5 em alto. O esforço fica o mesmo até
   o fim da conversa, porque trocar no meio pode reiniciar o cache. **A revisão final da CIA
   também roda em Opus médio** (25/09/2026) — ela acontece em todo processo, não é tarefa
   rara; alto só quando a CIA tiver fundamento lido só em `normas/md/`, tese nova sem modelo
   no banco ou mais de ~10 exigências (`ppci-revisao-cia`). Alto em conversa própria de tarefa
   rara e de erro caro, como incorporar norma. Esforço menor reduz o pensamento; texto mais
   curto se pede no prompt. Haiku não tem ajuste de esforço.
3. **Menos rodadas no navegador.** Da API do SOL, só o resumo filtrado dentro da página vem
   para a conversa, nunca o JSON bruto em fatias; login, modal e gravação se conferem por
   JS/API, não por screenshot (`sol-cbmrs-navegador`). Todas as ferramentas numa única
   `ToolSearch` na abertura; planilha de distribuição lida direto pelo ID
   (`ppci-abertura-sessao`).
4. **Contrato de ordem de entrega.** Resposta que começa pelo entregável e não narra progresso
   é mais curta — e output é o que se paga.
5. **Modo avulso.** Conversa aberta só para uma notificação não roda o pipeline de análise
   inteiro. Ver `ppci-notificacao-cia`.
6. **Ler o registro salvo antes de perguntar.** Dado que já está no `<N>.json` do processo não
   se pergunta de novo — custa rodada e faz o usuário repetir o que já informou.
7. **Gravar no projeto uma vez, no fim.** Já registrado em `ppci-analise-processo`: numa
   sessão medida, as chamadas `Projects` foram **37% do tempo de geração**, porque
   `project_write` reescreve o documento inteiro. Idem para a sincronização clone → projeto:
   uma vez, com a lista completa (em 24–25/09 os mesmos 6 arquivos foram copiados duas vezes).
   O projeto já tem o repositório como fonte sincronizada do GitHub — conferir se a cópia
   manual ainda é necessária depois do push.

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

**Registro — teste de 24/09/2026** (doc "Novas regras do Claude — adaptação SSEG"): com a base
em mãos, Haiku, Sonnet baixo e Sonnet médio copiaram uma nota errada (item 5.2.2.1); Opus em
qualquer esforço e Sonnet alto apontaram o erro, e o Opus baixo custou pouco menos que o
Sonnet alto. Isso reforça esta decisão. Nenhum modelo pegou o erro do CMAR na RT 05 P07, que só
aparece no PDF: a trava continua sendo conferir no PDF, não trocar de modelo.

**Registro — revisão de 25/09/2026** (semana com 74% da cota usada até sexta, 69% dela no
Cowork). Revisão das 15 conversas de 22 a 25/09 apontou o gasto em rodadas, não em modelo:
conversa de análise aberta o dia inteiro (07:28–17:58); JSON da API trazido em dezenas de
fatias de 950 caracteres; screenshot para confirmar login; 3 `ToolSearch` separados e 2 buscas
em conversa antiga só para achar a planilha de distribuição; 3 `tabs_context` seguidos com o
Chrome fora; `device_commit_files` um arquivo por chamada; revisão final sempre em Opus alto;
sincronização clone → projeto repetida. Correções aplicadas nas skills `ppci-abertura-sessao`,
`sol-cbmrs-navegador`, `ppci-analise-processo` e `ppci-revisao-cia`.
