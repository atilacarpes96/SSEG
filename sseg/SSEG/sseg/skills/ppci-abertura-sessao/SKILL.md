---
name: ppci-abertura-sessao
description: "Rotina de abertura quando o usuário diz que vai começar a analisar um PPCI: liberar a pasta Carpes, abrir o SOL-CBMRS no Chrome externo e parar na tela de login."
---

# Abertura de sessão de análise de PPCI

Disparar assim que o usuário abrir uma conversa dizendo que vai começar a analisar um PPCI
("vou analisar um PPCI", "começando outro processo", "abre o SOL"). Executar **sem pedir
confirmação** — a rotina é só preparar o ambiente, não altera nada no processo.

## Passos

1. ⭐ **Pedir acesso à pasta de trabalho — primeiro passo, sempre.**

   ```
   device_request_folder_access  ["C:\\Users\\55519\\Desktop\\Carpes"]
   reason: ler os PDFs oficiais em Carpes\Normas e a pasta "print ppci" das análises
   ```

   **O consentimento de pasta vale por SESSÃO, não por projeto** — toda conversa nova começa
   sem acesso, por mais que o caminho esteja gravado nos docs. Pedir aqui, no começo, custa um
   clique; descobrir no meio da análise custa a análise parada.

   Pedir **uma vez só** e a **pasta-mãe** `Carpes` (cobre `Normas`, `print ppci`, `Exemplos` e
   `RECURSOS`), nunca subpasta por subpasta. Recusa ou silêncio: seguir sem, pedir os arquivos
   por anexo, e **não repetir o pedido**.

2. Abrir `https://solcbm.rs.gov.br/solcbm/adm/` no **Chrome externo (Claude in Chrome)** — é o
   navegador padrão do usuário para o SOL, e a sessão dele costuma já estar logada. Começar
   com `tabs_context_mcp` e abrir em **aba nova**. Se o site ainda não estiver liberado na
   extensão, pedir a liberação e repetir a chamada.

   **No Chrome não mexer no zoom** — a página renderiza utilizável como está.

   *Fallback, só se o Chrome externo estiver indisponível:* navegador integrado
   (`Claude_Browser__preview_start`), aí sim com `resize_window` em **1460×1300** (escala
   ≈0,70 num painel de 1022×910; painel diferente: `largura_emulada = largura_do_painel ÷ 0,7`).
   Sem isso a página de análise técnica renderiza grande demais e fica inutilizável.

3. Parar na tela de login e avisar que a senha é digitada pelo próprio usuário.
   **Nunca preencher senha.**

4. Pedir/aguardar o código do processo (formato `A00049503AA001`).

## Depois do login

- Mecânica da tela (modal "Reprovar medida", leitura do campo "Especificar", PDF da
  página): `sol-cbmrs-navegador`.
- Pipeline da análise, começando pela ocupação definidora e pela tabela do Anexo B:
  `ppci-analise-processo`.
- Redação das inconformidades: `ppci-notificacao-cia`.
- PDFs das normas: pasta local `Carpes\Normas` — inventário, armadilhas e o que falta estão
  no doc `workflow/pasta-normas-local.md` do projeto. **Não pedir ao usuário PDF que já está
  lá, nem tentar baixar pelo link oficial** — o link não baixa.

## Cuidados

- Nunca digitar senha do usuário no SOE/SOL — parar no login e devolver o controle.
- Não clicar em nada que dispare diálogo nativo do navegador (alert/confirm) — trava a
  sessão de automação.
- Não abrir nem alterar medidas antes de o usuário informar o processo.
- Não gastar um segundo pedido de pasta no meio da sessão — o do passo 1 já cobre tudo.