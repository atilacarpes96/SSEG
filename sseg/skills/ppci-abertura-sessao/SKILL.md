---
name: "ppci-abertura-sessao"
description: "Rotina de abertura quando o usuário diz que vai começar a analisar um PPCI: liberar a pasta Carpes, abrir o SOL-CBMRS no Chrome externo e parar na tela de login. Também quando pedir para abrir a consulta técnica (CT) pendente ou marcada para hoje."
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
   `1Ps3SbCXKtc6HxBq7HRRGpc8LdaxOYU2RM5pOQgNyIl0`. Critério do próximo, nesta ordem:
   aba **ANÁLISE** → linhas com o nome dele → "DATA CONCLUSÃO" em branco → a de **maior
   "DIAS EM ANÁLISE"** (a coluna da planilha, não a contagem do SOL). **Não** é a primeira
   linha da lista: o mais antigo vai primeiro, porque nenhum processo deve passar de 10 dias
   na caixa. Empate em dias: a que aparece primeiro na planilha. Dizer na resposta o código e
   quantos dias ele tem. **Não** buscar em conversas antigas, **não** procurar
   o arquivo no Drive e **não** abrir a planilha no Chrome — o ID já está aqui. Só se a
   leitura falhar (arquivo movido), procurar por `title contains 'Distribui'` e avisar para
   atualizar o ID nesta skill.

1. ⭐ **Pedir acesso à pasta de trabalho — primeiro passo, sempre.**

   ```
   device_request_folder_access  ["C:/Users/55519/Desktop/Carpes"]
   reason: ler os PDFs oficiais em Carpes/SSEG/sseg/normas/pdf e a pasta "print ppci" das análises
   ```

   **O consentimento de pasta vale por SESSÃO, não por projeto** — toda conversa nova começa
   sem acesso, por mais que o caminho esteja gravado nos docs. Pedir aqui, no começo, custa um
   clique; descobrir no meio da análise custa a análise parada.

   Pedir **uma vez só** e a **pasta-mãe** `Carpes` (cobre `SSEG\sseg\normas\pdf`, `print ppci`,
   `Normas`, `Exemplos` e `RECURSOS`), nunca subpasta por subpasta. Em casa o projeto está em
   `E:\Atila\bombers\SSEG` (PDFs em `sseg\normas\pdf`). Recusa ou silêncio: seguir sem, pedir os arquivos
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

## Consulta técnica (CT) pendente

"A CT que eu marquei", "a consulta técnica de hoje": o código **não** está na agenda nem na
"Distribuição Análise" — está na planilha **"CONSULTAS TÉCNICAS 6°BBM"**, fileId
`1HlFHKWzCOSPO5FxszNSMOVNDfKDAfs5dNw4lSmAf8_g`, aba "Consulta Técnica".

- `read_file_content` só devolve amostra. Baixar inteira com `download_file_content`
  (`exportMimeType: text/csv`); o resultado é grande e vai para arquivo — filtrar no
  PowerShell (o Python do PC pode não estar no PATH do bash) as linhas com `Sd Carpes`.
- Colunas: A PPCI (código) · D FACT · E data da solicitação · F nome · G telefone · I ME
  (analista) · K/L/M data, hora, modalidade da CT · N minuta finalizada (1/0) · Q finalizado
  pelo Chefe da SSeg (1/0) · S "aguardando há".
- **Pendente do analista** = linha com `Sd Carpes` e N = 0. Linha com N = 1 e Q = 0 espera o
  Chefe da SSeg, não o analista — citar à parte.
- Abrir o projeto pela **Consulta licenciamentos** (caminho na skill `sol-cbmrs-navegador`).
  A CT em si fica em **Consulta FACT** (`#/fact`); "Análise do FACT" e os demais itens de
  FACT dão "sem autorização" no perfil do Átila.
- Registrado em 03/10/2026.

## Depois do login

- Mecânica da tela (modal "Reprovar medida", leitura do campo "Especificar", PDF da
  página): `sol-cbmrs-navegador`.
- Pipeline da análise, começando pela ocupação definidora e pela tabela do Anexo B:
  `ppci-analise-processo`.
- Redação das inconformidades: `ppci-notificacao-cia`.
- PDFs das normas: **`sseg/normas/pdf/`** dentro da pasta do projeto (quartel:
  `C:\Users\55519\Desktop\Carpes\SSEG\sseg\normas\pdf\`; casa:
  `E:\Atila\bombers\SSEG\sseg\normas\pdf\`) — a mesma fonte da `ppci-analise-processo`.
  `Carpes\Normas` é só a entrada de PDF novo, antes de ele ser incorporado
  (`ppci-incorporar-norma`). **Não pedir ao usuário PDF que já está em `sseg/normas/pdf/`,
  nem tentar baixar pelo link oficial** — o link não baixa.

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