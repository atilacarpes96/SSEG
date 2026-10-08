---
name: atualizacoes
description: O que mudou no SSEG, data a data, e o prompt pronto para cada analista colar no próprio Claude e atualizar o seu lado (skills da conta, campo Instruções, modelo de cada conversa). É a aba Atualizações do Painel SSEG.
---

# Atualizações do SSEG

Uma entrada por leva de mudanças, a mais nova em cima. Cada entrada traz **o que mudou**, em
poucas linhas, e o **prompt para atualizar**: o analista copia e cola numa conversa nova do
próprio Claude, dentro do projeto SSEG (Cowork ou Claude Code), e o Claude faz o resto com ele.

Formato, que o `scripts/painel.py` lê: título `## DD/MM/AAAA — assunto`, o texto do que mudou
e o subtítulo `### Prompt para atualizar` seguido de um bloco de código com o prompt.

## 08/10/2026 — Processo no PC, memorial e CIA no servidor

- **Onde roda a análise:** no PC do trabalho, numa conversa **Local** do app do Claude (Novo → Local → pasta do SSEG), uma por processo. É onde estão o Chrome logado no SOL e os arquivos baixados.
- **Novo comando `sseg.py enviar`:** leva à pasta do processo no servidor os JSON, `<N>.pdf`, a CIA e o memorial, por SSH. Planta baixa não vai: só serve na hora e o SOL guarda o original. A `ppci-analise-processo` passou a chamá-lo ao abrir e ao arquivar o processo.
- **Quem não tem servidor:** nada muda. O envio falha com aviso de uma linha e a análise segue.

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a mudança de 08/10/2026 (processo no PC, memorial no servidor) e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você.
2. Rode a skill sseg-sincronizar-skills no sentido repositório → conta. Deve aparecer como diferente: ppci-analise-processo. No Claude Code, em vez do cartão, gere o .zip com o zipfile do Python, como manda o CLAUDE.md, e me diga onde ficou.
3. Se eu não tenho servidor, me diga em uma linha que o passo "enviar" da skill vai só avisar e seguir.
```

## 08/10/2026 — Haiku 5.5 na pergunta rápida e nos subagentes

- **Modelo de cada conversa:** pergunta rápida, notificação avulsa com modelo do banco e sincronização passam do Sonnet 5.5 médio para o **Haiku 5.5 médio**. Análise de processo e revisão final da CIA continuam em **Sonnet 5.5 alto**.
- **Subagentes do Claude Code:** `localizador-normas` e `sol-leitor` passam do Haiku 4.5 para o Haiku 5.5. No arquivo vai o nome completo, `claude-haiku-5-5`, porque o atalho `haiku` ainda aponta para o 4.5.
- **Motivo:** no teste de 08/10 (66 execuções) o Haiku 5.5 médio tirou 97 nas onze tarefas, sem erro fatal, contra 91 do Sonnet 5.5 médio e 67 do Haiku 4.5. Na definidora e na revisão ficou abaixo do Sonnet alto, por isso essas seguem no Sonnet. Detalhes em `workflow/politica-modelo-e-custo.md`.
- **Skills:** `ppci-analise-processo` e `sol-cbmrs-navegador` só trocaram a menção ao modelo.

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão de 08/10/2026 e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você.
2. Rode a skill sseg-sincronizar-skills no sentido repositório → conta. Devem aparecer como diferentes: ppci-analise-processo e sol-cbmrs-navegador. No Claude Code, em vez do cartão, gere um .zip por skill com o zipfile do Python, como manda o CLAUDE.md, e me diga onde ficaram.
3. Confira em .claude/agents/ que localizador-normas e sol-leitor estão com model: claude-haiku-5-5.
4. Feche com três linhas: análise de processo e revisão final da CIA em Sonnet 5.5 alto; pergunta rápida e notificação avulsa em Haiku 5.5 médio; Haiku 5.5 no máximo não compensa (gasta muito e demora).
```

## 06/10/2026 — Modelo de cada conversa, formato do SOL e minuta de despacho

- **Nova skill `ppci-minuta-despacho`:** ata de consulta técnica (FACT) e despacho de recurso com até 2.000 caracteres, só o que foi tratado ou alegado e conclusão prática em cada ponto (orientação do Chefe da SSeg de 05/10/2026).
- **Instruções:** empate no grau de risco entre predominantes → parar e levar ao analista (RT 01/2024, 5.1.2); texto de notificação já no formato da caixa do SOL (quebra de linha e "- ", cada parágrafo numa linha só).
- **Modelo de cada conversa:** análise de processo e revisão final da CIA em **Sonnet 5.5 alto**, a revisão sempre em conversa nova; pergunta rápida, notificação avulsa com modelo do banco e sincronização em **Sonnet 5.5 médio**. O teste de 214 execuções que embasou está em `workflow/politica-modelo-e-custo.md`.
- **Revisão da CIA:** o `sseg.py revisar-cia` passou a apontar requisito de instalação transcrito (é de vistoria), artigo do Decreto junto com item de RT, REITERO numa 1ª análise e caixa sem hífen; a skill manda declarar certo o texto que está certo, sem reescrever.
- **Skills:** seção "Desculpas que não valem" em `ppci-analise-processo`, `ppci-notificacao-cia`, `ppci-revisao-cia` e `ppci-minuta-despacho`, com os atalhos que os modelos tomaram no teste.
- **Claude Code:** hooks em `.claude/settings.json` (pull ao abrir a sessão; commit barrado com arquivo de processo ou com teste falhando; texto validado do banco protegido) e `python3 sseg/scripts/testar.py`. Precisa de `python3` no PATH.
- **Código de processo:** citar só o código num doc versionado pode; arquivo de processo, CIA, JSON, planta, print e dado de proprietário ou RT continuam fora do GitHub.

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão de 06/10/2026, nesta ordem, e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você.
2. Rode a skill sseg-sincronizar-skills no sentido repositório → conta. Devem aparecer como diferentes ou novas: ppci-analise-processo, ppci-notificacao-cia, ppci-revisao-cia, ppci-incorporar-norma, sol-cbmrs-navegador e a nova ppci-minuta-despacho. No Claude Code, em vez do cartão, gere um .zip por skill com o zipfile do Python, como manda o CLAUDE.md, e me diga onde ficaram.
3. Me entregue, num bloco único para copiar, o texto entre os marcadores INÍCIO e FIM de sseg/workflow/instrucoes-projeto-espelho.md, para eu colar no campo Instruções do projeto no lugar do texto inteiro.
4. Feche com três linhas: análise de processo em Sonnet 5.5 alto; revisão final da CIA em conversa nova com Sonnet 5.5 alto; pergunta rápida e notificação avulsa em Sonnet 5.5 médio.
```
