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

## 16/10/2026 — SSEG.exe 2.3.1 (copiar por item na CIA) e RT 05 Parte 08 na base

- **CIA:** cada exigência tem "Copiar" (texto pronto para a caixa Especificar do SOL) e, agrupado por medida, cada medida tem "copiar a medida", com a contagem dos 2.000 caracteres. A caixa da exigência abre do tamanho do texto e a alça de altura fica embaixo do item.
- **Chat:** a caixa de escrever abre maior, cresce com o texto e a alça fica em cima.
- **Normas:** a RT 05 Parte 08/2016 (Símbolos Gráficos) entrou em `normas/pdf/RT05P08.pdf`, com conversão verificada e transcrição da Tabela 1 (o que deve constar junto a cada símbolo). PDFs em `normas/pdf/`: 20. **Campo Instruções:** a contagem em "Onde procurar primeiro" passa a "20 em 16/10/2026" e a RT05P08 entra na lista de duas colunas — copiar do espelho.

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão 2.3.1 (16/10/2026) e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você mesmo.
2. Rode python sseg/scripts/testar.py e me diga o resultado.
3. Me diga para abrir o SSEG.exe e aceitar a "Nova versão".
4. Me entregue o texto do campo Instruções de sseg/workflow/instrucoes-projeto-espelho.md (entre os marcadores) para eu colar no projeto: mudou a contagem de PDFs.
5. Copie sseg/normas/pdf/RT05P08.pdf para C:\Users\55519\Desktop\Carpes\Normas e sseg/normas/base/RT05P08.md com as imagens RT05P08-* de base/img para Carpes\Normas\_md.
```

## 15/10/2026 — SSEG.exe 2.3: CT e recursos nos cards, Quadro da seção

- **CT e recursos:** o servidor lê todo dia útil as planilhas de CT e de recursos e marca na pasta de cada processo o que está aberto. Cards novos: CT marcadas (minuta sem Finalizado), CT com a chefia, Recursos (para redigir) e Recursos com a chefia. Quando a chefia finaliza na planilha, sai sozinho. Se o recurso é seu num processo de outro analista, a pasta aparece para você também.
- **Quadro da seção:** na tela Quadro, a tarefa nova pode ser da seção (todos veem) ou só sua. Na da seção: "Pegar" põe o seu nome, e quem criou ou pegou move, edita e escreve o que foi feito; o cartão mostra início e fim.
- **Abre em 3 s** (antes 20 s com o espelho ligado) e os **cards mudam de ordem arrastando** (2.2.2).

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão 2.3 (15/10/2026) e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você mesmo.
2. Rode python sseg/scripts/testar.py e me diga o resultado.
3. Me diga para abrir o SSEG.exe e aceitar a "Nova versão". Os cards de CT e de recursos aparecem em "+ card"; o Quadro da seção, na tela Quadro (precisa do acesso ao servidor: Configuração → Servidor).
```

## 15/10/2026 — SSEG.exe 2.2: instalador e vários analistas no servidor

- **Instalação:** quem baixa o SSEG.exe e abre cai na tela Instalação (menu ☰). Ela põe o programa em `%LOCALAPPDATA%\Programs\SSEG` com atalho na Área de Trabalho e no Menu Iniciar, instala Git, Python, Poppler e Claude Code, faz o login, cria as pastas e pergunta quem é você. Sem administrador e sem PowerShell.
- **Servidor para todos:** Configuração → Servidor → "Pedir acesso" gera um código; mande ao Átila. Liberado, o Sincronizar processos leva e traz só os SEUS processos (a planilha da distribuição diz de quem é cada um). Sua chave só fala com o SSEG no servidor, sem acesso ao resto.
- **Processos de todos numa pasta por código:** quando o processo passa de um analista para outro, a pasta vai inteira ao novo responsável, com o registro de quem já passou.
- **Chrome para o Claude** (Configuração, opcional): o Claude lê a página do SOL já aberta no seu Chrome pelo DOM, sem print.
- **Trava do banco de notificações:** no Windows ela deixava passar alteração no texto validado (erro de acento na mensagem); corrigida.

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão 2.2 (15/10/2026) e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você mesmo.
2. Rode python sseg/scripts/testar.py e me diga o resultado.
3. Me diga para abrir o SSEG.exe e clicar em "Nova versão" (ou baixar em https://github.com/atilacarpes96/SSEG/releases/latest) e depois abrir o menu ☰ → Instalação e resolver o que estiver com ✗.
4. Se eu quiser usar o servidor: Configuração → Servidor → "Pedir acesso" e mandar o código ao Átila.
```

## 12/10/2026 — SSEG.exe 2.1: janela do processo, conversas sem terminal, respostas visuais

- **Janela do processo:** "Analisar processo" (ou "abrir" em Processos em andamento) mostra três colunas — conversa com o Claude dentro do programa, checklist (pendências, os 16 passos e as medidas do SOL com o Anexo L) e CIA em construção. O Claude só começa quando você manda a primeira mensagem.
- **Nenhum fluxo abre terminal:** os outros botões abrem uma janela de conversa do programa, com a mensagem sugerida no campo. Terminal e "Copiar o prompt" ficam no ⋯.
- **Respostas visuais:** tabelas de verdade, selo de status, cartões, tabela da definidora, perguntas com campo de resposta, cartão de exigência com "Pôr na CIA" e [PDF] da norma.
- **CIA:** vale o texto que você salva; o do Claude fica como rascunho, à parte.
- **Novo comando:** `sseg.py analise --pasta <processo> pendencia|exigencia|passo|ver` grava no `analise.json` da pasta do processo (fica fora do GitHub; vai ao servidor pelo Sincronizar processos).

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão 2.1 (12/10/2026) e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você.
2. Rode python sseg/scripts/testar.py e me diga o resultado.
3. Me diga para abrir o SSEG.exe e clicar em "Nova versão" (ou baixar em https://github.com/atilacarpes96/SSEG/releases/latest).
4. Me explique em três linhas a janela do processo: o Claude só começa quando eu escrevo; o texto que vale na CIA é o que eu salvo; o terminal fica no botão ⋯.
```

## 12/10/2026 — SSEG.exe 2.0: interface nova e ganchos que acham o Python

- **SSEG.exe 2.0:** interface nova (HTML, no componente do Edge do Windows). Barra de estado no alto (Programas, Pastas, Servidor, GitHub com contador, Nova versão), menu ☰ (Início, Buscar normas, Configuração, Ajuda), conversas por demanda e processos em andamento na tela inicial, mensagens em "Detalhes" no rodapé. A lógica é a mesma da 1.3; sem o componente do Edge, abre a janela antiga.
- **Busca (1.2.2):** cada resultado tem [PDF], que abre a norma oficial na página do trecho.
- **SOL sem teclado (1.3.0, opcional):** atalho "Abrir SOL" e passos do Tampermonkey, em Configuração.
- **Ganchos do Claude Code:** passam por `.claude/hooks/rodar.sh`, que pula o `python3` da Microsoft Store e liga o UTF-8 (o gancho Stop dava "Python não foi encontrado" no Windows).

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão de 12/10/2026 e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você.
2. Confira que .claude/settings.json chama sh "$CLAUDE_PROJECT_DIR/.claude/hooks/rodar.sh" nos 5 ganchos.
3. Rode python sseg/scripts/testar.py e me diga o resultado.
4. Me diga para abrir o SSEG.exe e clicar em "Nova versão" (ou baixar em https://github.com/atilacarpes96/SSEG/releases/latest).
```

## 11/10/2026 — SSEG.exe 1.1.0 e revisor-cia com nome completo de modelo

- **Subagente `revisor-cia`:** `model: sonnet` passa a `model: claude-sonnet-5-5`. O atalho funcionava, mas a regra é nome completo (o atalho `haiku` ainda aponta para o 4.5) e o `testar.py` agora barra atalho.
- **Programa SSEG.exe 1.1.0:** botão "Sincronizar com o GitHub" (pull, commit e push com conferência; dado de processo fica fora), "Sincronizar processos" com o servidor por SSH, um botão por tipo de conversa (abre o Claude Code com o modelo e o esforço da política), Subagentes, Gasto em tokens, Reportar bug, Procurar atualização e atualização automática do próprio programa.
- **Travas do commit** no pre-commit do git: valem também para commit fora do Claude.
- **Fonte única das conversas:** `workflow/fluxos.json`, gerado da política pelo `painel.py`; aparece na aba Conversas deste painel.

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão de 11/10/2026 e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você.
2. Confira em .claude/agents/revisor-cia.md que está model: claude-sonnet-5-5.
3. Rode python sseg/scripts/testar.py e me diga o resultado.
4. Me diga para baixar o SSEG.exe em https://github.com/atilacarpes96/SSEG/releases/latest (se eu já tenho a 1.0.6, ele mesmo oferece "Atualizar o programa").
```

## 08/10/2026 — Programa SSEG para o PC (SSEG.exe)

- **Novo programa `SSEG.exe`** em https://github.com/atilacarpes96/SSEG/releases/latest: cria a pasta dos processos e baixa o SSEG do GitHub se ainda não estiver no PC, confere Git, Python e Poppler, e o botão **Verificar atualizações** mostra o que mudou no GitHub e faz o `git pull`. Skill que mudou sai em `.zip` pronta para subir na conta. Tem atalho para este Painel.
- Não dá commit nem push e não força nada: se o pull conflitar, ele avisa e não mexe.
- Na primeira vez o Windows avisa que o programa não tem assinatura: Mais informações → Executar assim mesmo.

### Prompt para atualizar

```text
Quero começar a usar o programa SSEG.exe (mudança de 08/10/2026). Me guie, sem rodar nada por mim:
1. Me diga para baixar o SSEG.exe em https://github.com/atilacarpes96/SSEG/releases/latest e abrir (se o Windows avisar, Mais informações > Executar assim mesmo).
2. Me ajude a preencher as duas pastas do programa: onde já está o meu clone do SSEG (confira com git rev-parse --show-toplevel) e a minha pasta dos processos (print ppci).
3. Me peça para clicar em "Criar / conferir pastas" e depois em "Verificar atualizações", e para colar aqui o que aparecer no quadro de baixo se tiver algum ✗.
```

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
