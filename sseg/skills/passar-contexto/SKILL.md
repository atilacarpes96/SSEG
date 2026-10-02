---
name: "passar-contexto"
description: "Gerar um bloco de passagem com todo o contexto da conversa para continuar em outra conversa onde as ferramentas (Chrome, pasta, PC) estão funcionando."
---

# Passar contexto para outra conversa

Usar quando o usuário disser "passa o contexto", "vou continuar na outra conversa", "leva isso pra lá", ou quando uma ferramenta necessária (Claude in Chrome, pasta do PC, device bridge) não estiver disponível nesta conversa e ele tiver outra onde ela funciona.

## Objetivo

Entregar UM bloco de texto, pronto para colar como primeira mensagem na outra conversa, que permita continuar o trabalho sem reler esta conversa e sem perguntar de novo o que já foi decidido.

## Antes de montar

1. Se houver textos finais em arquivo no scratchpad, ler do arquivo — nunca redigitar de memória. O texto colado tem de ser idêntico ao aprovado.
2. Contar caracteres dos textos destinados ao SOL (limite 2.000 na caixa Especificar) e informar a contagem.
3. Separar o que foi DECIDIDO pelo usuário do que foi só SUGERIDO pela IA. Só o decidido entra como decisão.

## Estrutura do bloco (nesta ordem)

1. **Pedido de ação** — uma ou duas frases no imperativo: o que a outra conversa deve fazer primeiro (ex.: conferir X pela API, depois lançar Y). Se lançar no SOL, dizer que é para substituir o texto existente e reler pela API depois de salvar.
2. **Identificação** — código do processo, campo(s) do SOL afetado(s), e onde cada texto vai (campo, linha, "Outros" ou "Demais inconformidades").
3. **Textos finais**, cada um em bloco citado, com a contagem de caracteres ao lado.
4. **Decisões já tomadas pelo usuário (não rediscutir)** — lista curta, incluindo pedidos de terceiros (ex.: orientações do capitão) e o que foi retirado e por quê.
5. **Pendências a conferir** — dados que a outra conversa precisa verificar antes de lançar (ex.: uma data não confirmada), com o que fazer se divergir.
6. **Perguntas em aberto** — o que ainda depende de resposta do usuário.
7. **Fundamentos conferidos** — norma · item · uma linha. Marcar como provisório o que não foi conferido no PDF.
8. **Observações laterais** relevantes para quem continuar.

## Regras

- Escrever em português, sem narração de progresso.
- Usar a terminologia do usuário: "campo" para seções do SOL, "item" para itens de norma; "6º BBM" com ordinal.
- Não incluir código de ferramenta, IDs internos de tool call nem tokens de sessão.
- Não incluir dados pessoais além do necessário ao processo.
- Entregar o bloco no topo da resposta, em um único bloco de código para facilitar copiar no celular. Depois, no máximo uma linha dizendo onde colar.