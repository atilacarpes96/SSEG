---
name: "ppci-abertura-sessao"
description: "Rotina de abertura quando o usuário diz que vai começar a analisar um PPCI: liberar a pasta Carpes, abrir o SOL-CBMRS no Chrome externo e parar na tela de login."
---

# Abertura de sessão de análise de PPCI

Disparar assim que o usuário abrir uma conversa dizendo que vai começar a analisar um PPCI
("vou analisar um PPCI", "começando outro processo", "abre o SOL"). Executar **sem pedir
confirmação** — a rotina é só preparar o ambiente, não altera nada no processo.

## Passos

0. ⭐ **Carregar TODAS as ferramentas numa única `ToolSearch`**, antes de qualquer outra
   chamada — cada ToolSearch a mais é uma rodada inteira paga (já foram 3 numa abertura):

   ```
   select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,
   mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__javascript_tool,
   mcp__claude-in-chrome__find,mcp__claude-in-chrome__computer,
   mcp__claude-in-chrome__tabs_create_mcp,mcp__remote-devices__device_request_folder_access,
   mcp__remote-devices__device_list_dir,mcp__remote-devices__device_stage_files,
   mcp__remote-devices__device_commit_files,mcp__Google_Drive__read_file_content,SendUserMessage
   ```

   **"Bora pro próximo" / "o próximo da lista":** ler direto a planilha "Distribuição Análise"
   com `mcp__Google_Drive__read_file_content`, fileId
   `1Ps3SbCXKtc6HxBq7HRRGpc8LdaxOYU2RM5pOQgNyIl0`. O próximo é a primeira linha com o nome
   dele e "DATA CONCLUSÃO" em branco. **Não** buscar em conversas antigas, **não** procurar
   o arquivo no Drive e **não** abrir a planilha no Chrome — o ID já está aqui. Só se a
   leitura falhar (arquivo movido), procurar por `title contains 'Distribui'` e avisar para
   atualizar o ID nesta skill.

1. ⭐ **Pedir acesso à pasta de trabalho — primeiro passo, sempre.**

   ```
   device_request_folder_access  ["C:/Users/55519/Desktop/Carpes"]
   reason: ler os PDFs oficiais em Carpes/Normas e a pasta "print ppci" das análises
   ```

   **O consentimento de pasta vale por SESSÃO, não por projeto** — toda conversa nova começa
   sem acesso, por mais que o caminho esteja gravado nos docs. Pedir aqui, no começo, custa um
   clique; descobrir no meio da análise custa a análise parada.

   Pedir **uma vez só** e a **pasta-mãe** `Carpes` (cobre `Normas`, `print ppci`, `Exemplos` e
   `RECURSOS`), nunca subpasta por subpasta. Recusa ou silêncio: seguir sem, pedir os arquivos
   por anexo, e **não repetir o pedido**.

2. Abrir o SOL no **Chrome externo (Claude in Chrome)** — é o navegador padrão do usuário para
   o SOL, e a sessão dele costuma já estar logada. Começar com `tabs_context_mcp` e abrir em
   **aba nova**. Se o site ainda não estiver liberado na extensão, pedir a liberação e repetir
   a chamada.

   ⭐ **Navegar DIRETO pela URL para a caixa de análise do usuário:**
   `https://solcbm.rs.gov.br/solcbm/adm/#/analise-tecnica`

   A caixa de análise dele é **Licenciamento → Análise técnica**. **Nunca chegar lá clicando no
   menu lateral por coordenada de screenshot**: "Distribuição para análise" fica logo acima de
   "Análise técnica", o clique cai nela e o SOL abre o aviso "Ação não autorizada" — já
   aconteceu em várias aberturas. Se precisar do menu, clicar pelo `ref` devolvido por `find`
   ("menu link Análise técnica").

   Na lista, localizar a linha do processo (Razão Social / área / data) e clicar em
   **Analisar**, de preferência pelo `ref` via `find`. A página abre em
   `#/analise-tecnica/<id>` com o código do licenciamento no título — conferir que é o código
   pedido.

   **No Chrome não mexer no zoom** — a página renderiza utilizável como está.

   *Fallback, só se o Chrome externo estiver indisponível:* navegador integrado
   (`Claude_Browser__preview_start`), aí sim com `resize_window` em **1460×1300** (escala
   ≈0,70 num painel de 1022×910; painel diferente: `largura_emulada = largura_do_painel ÷ 0,7`).
   Sem isso a página de análise técnica renderiza grande demais e fica inutilizável.

   **Chrome não respondeu** (`tabs_context_mcp` com erro ou extensão desconectada): tentar
   **uma** vez mais, no máximo. Na segunda falha, avisar e parar — não repetir a chamada em
   sequência (já foram 3 seguidas numa abertura).

3. **Conferir o login por texto, nunca por screenshot:** `javascript_tool` com
   `JSON.stringify({url: location.href, token: !!localStorage.getItem('access_token')})`, ou
   `get_page_text`. Imagem custa muito mais que texto e não traz informação a mais aqui.
   Se cair na tela de login, parar e avisar que a senha é digitada pelo próprio usuário.
   **Nunca preencher senha.**

4. Se o código do processo não veio na mensagem, pedir/aguardar (formato `A00049503AA001`).

## Depois do login

- Mecânica da tela (modal "Reprovar medida", leitura do campo "Especificar", PDF da
  página): `sol-cbmrs-navegador`.
- Pipeline da análise, começando pela ocupação definidora e pela tabela do Anexo B:
  `ppci-analise-processo`.
- Redação das inconformidades: `ppci-notificacao-cia`.
- PDFs das normas: pasta local `Carpes/Normas` — inventário, armadilhas e o que falta estão
  no doc `workflow/pasta-normas-local.md` do projeto. **Não pedir ao usuário PDF que já está
  lá, nem tentar baixar pelo link oficial** — o link não baixa.

## Cuidados

- Nunca digitar senha do usuário no SOE/SOL — parar no login e devolver o controle.
- Não clicar em nada que dispare diálogo nativo do navegador (alert/confirm) — trava a
  sessão de automação.
- Não abrir nem alterar medidas antes de o usuário informar o processo.
- Não gastar um segundo pedido de pasta no meio da sessão — o do passo 1 já cobre tudo.
- Menu lateral do SOL: nunca clicar por coordenada; usar URL direta ou `ref` de `find`.
- **Uma conversa por processo.** Retomada ou ajuste de processo já analisado começa lendo
  `processos/<código>.md` no projeto e a pasta `print ppci\<código>\` — não
  `conversation_search`/`read_conversation` em conversas antigas, que custa várias rodadas
  para reconstruir o que o registro já tem.