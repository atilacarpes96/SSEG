---
name: politica-modelo-e-custo
description: Decisão de 03/09/2026 sobre qual modelo usar em cada tipo de tarefa do SSEG — por que a rota de "modelo leve para tarefa simples" foi avaliada e descartada, e quais são as alavancas de economia que sobraram (revisada em 06/10/2026 com o teste de 214 execuções: análise de processo e revisão final em Sonnet 5.5 alto; pergunta rápida e notificação avulsa em Sonnet 5.5 médio)
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
**Conversa aberta só para isso** (ex.: "Atualizar projeto com arquivos") abre em Sonnet 5.5
médio; Haiku só como subagente mecânico.

## As alavancas que sobraram (e valem mais)

1. **Conversa curta: uma por processo, uma por tarefa.** Cada mensagem reenvia o histórico
   inteiro, então o fim de uma conversa longa custa muito mais que o começo. Arquivou a CIA,
   a conversa acabou; ajuste posterior abre conversa nova lendo `processos/<N>.md`, não
   buscando em conversa antiga (medição de 25/09/2026, abaixo).
2. **Esforço, não modelo.** Baixar o esforço num modelo forte é mais seguro que trocar por um
   modelo fraco: mantém-se a calibragem e o conhecimento, gasta-se menos deliberação. Desde
   06/10/2026 (testes no fim deste doc): **análise de processo e revisão final da CIA em
   Sonnet 5.5 alto**; **pergunta rápida, notificação avulsa com modelo do banco e sincronização
   em Sonnet 5.5 médio**. Na definidora o médio errou feio 1 vez em 4 e o alto nenhuma; na
   revisão o médio reescreveu texto que estava certo. Esforço máximo não se justifica: no Opus, o alto empatou com o médio (99 × 98)
   custando 34% a mais, e o máximo nem foi medido. O esforço fica o mesmo até o fim da conversa,
   porque trocar no meio pode reiniciar o cache. **Opus 5.5 só em caso realmente necessário**,
   os listados em `ppci-revisao-cia`: tese nova sem modelo no banco que o analista não tenha
   conferido na fonte, fundamento lido apenas em `normas/md/`, ou divergência entre o Sonnet e
   o analista sobre um fundamento. O que pega erro é abrir o PDF, não o esforço. Esforço menor
   reduz o pensamento; texto mais curto se pede no prompt. Haiku não tem ajuste de esforço e
   fica só em subagente mecânico.
   *Histórico:* de 24 a 29/09/2026 o padrão foi Opus 5.5 médio, inclusive na revisão final; de
   30/09 a 05/10/2026, Sonnet 5.5 médio em toda conversa.
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

**Registro — teste de modelos de 05–06/10/2026** (196 execuções no servidor). Onze tarefas do
dia a dia com gabarito conferido no PDF, cada uma em sete arranjos (Haiku; Sonnet 5.5 e Opus 5.5
em esforço baixo, médio e alto), `claude -p` só leitura sobre o mesmo retrato do repositório, e
nota dada às cegas por um juiz (Opus). Custo em US$ é preço de API, usado como medida relativa
de cota.

Todas as tarefas, rodadas 1 e 2 (22 execuções por arranjo):

| Arranjo | Nota | Erros fatais | US$ por execução |
|---|---|---|---|
| Haiku | 67 | 3 | 0,09 |
| Sonnet baixo | 93 | 0 | 0,13 |
| Sonnet médio | 91 | 0 | 0,16 |
| Sonnet alto | 94 | 0 | 0,19 |
| Opus baixo | 94 | 0 | 0,23 |
| Opus médio | 94 | 0 | 0,32 |
| Opus alto | 96 | 0 | 0,41 |

As três difíceis — ocupação definidora com subsidiária J (T01), vigência da câmara frigorífica
(T05) e revisão de CIA com erros plantados (T06) —, antes e depois das correções do commit
`f311f9c` (parada no critério (b) do 5.1.2 nas Instruções, travas novas no `revisar-cia`):

| Arranjo | Antes | Depois: T01 · T05 · T06 | US$ depois |
|---|---|---|---|
| Sonnet baixo | 75 | 86 · 93 · 80 | 0,15 |
| Sonnet médio | 66 | 95 · 93 · 83 | 0,21 |
| Sonnet alto | 79 | 95 · 93 · 100 | 0,32 |
| Opus baixo | 80 | 90 · 93 · 98 | 0,27 |
| Opus médio | 76 | 98 · 96 · 100 | 0,44 |
| Opus alto | 84 | 98 · 100 · 100 | 0,59 |

O que o teste decidiu:

1. **Regra no lugar certo vale mais que modelo maior.** A correção subiu todos os arranjos de
   11 a 24 pontos; trocar de Sonnet para Opus no mesmo esforço, de 3 a 10. Fechar a definidora sozinho caiu de
   9 em 12 execuções para nenhuma; os dois erros plantados que passavam em 9 de 12 revisões
   (requisito de instalação transcrito, Decreto junto com RT) passaram a ser pegos em todas.
2. **Skill não carrega sozinha.** Com a ferramenta de skills disponível, 1 de 77 execuções a
   usou e 10 leram o `SKILL.md`. Regra que tem de valer sempre vai para as Instruções; a skill
   guarda o passo a passo. Foi o que levou o formato da caixa do SOL (quebra de linha e "- ")
   para a "Ordem de entrega": depois da correção, 19 de 24 textos ainda saíam sem o hífen.
3. **Revisão final em Sonnet alto.** Pegou tudo nas duas rodadas; o baixo e o médio declararam
   errado ou reescreveram um texto correto (falso positivo que mexe em fundamento conferido).
4. **Análise de processo em Sonnet alto** (decisão do Átila, 06/10/2026). Nas rodadas 3–4 o
   médio empatou com o alto na definidora (95), mas na validação (registro abaixo) errou feio
   uma vez. O médio fica para pergunta rápida e notificação avulsa com modelo do banco, em que
   todos os arranjos acertaram.
5. **Tarefa mecânica, qualquer modelo.** Altura, JSON do SOL, planilha de CT, localizar trecho
   e norma sem PDF: todos os arranjos tiraram 100, inclusive o Haiku. Haiku segue só em
   subagente mecânico: 3 erros fatais nas tarefas normativas e, em sessão de segundo plano,
   sem modo automático (a rotina trava pedindo permissão), por isso as rotinas rodam em Sonnet.

Duas execuções por célula: diferença de 2 a 3 pontos entre arranjos é ruído. O roteiro, as
tarefas e as notas ficaram no servidor, em `~/rotinas/avaliacao-modelos-2026-10/`, para repetir
quando mudar modelo ou regra.

**Registro — validação de 06/10/2026** (18 execuções). As mesmas três tarefas difíceis, sobre o
repositório com as mudanças do dia (formato do SOL na "Ordem de entrega" e revisão em Sonnet
alto), nos três arranjos que a política usa:

| Arranjo | T01 · T05 · T06 | Média | US$ por execução |
|---|---|---|---|
| Sonnet médio | 55 · 100 · 100 | 85 (1 erro fatal) | 0,20 |
| Sonnet alto | 100 · 96 · 100 | 99 | 0,27 |
| Opus médio | 100 · 100 · 100 | 100 | 0,43 |

- **Hífen resolvido:** nenhum texto para o SOL saiu sem ele (antes da mudança, 19 de 24).
- **Revisão da CIA:** os três arranjos pegaram todos os erros plantados sem mexer no texto
  correto.
- **Sonnet médio na definidora:** numa das duas execuções não reconheceu o empate de risco
  médio entre I-2 e J-3 e citou como fundamento uma tabela que não decide o grau de risco (erro
  fatal pela rubrica). Somando as rodadas depois da correção, o médio teve 1 erro fatal em 4
  execuções da definidora e o alto nenhum; o alto ficou acima do médio nas duas comparações
  (96 × 90 e 99 × 85), custando de 40% a 55% a mais.
