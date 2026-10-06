---
name: ppci-minuta-despacho
description: "Redigir ou revisar minuta de despacho de consulta técnica (CT, via FACT) ou de recurso, inclusive a ata da reunião de CT: até 2.000 caracteres, só o que foi tratado na reunião ou alegado no recurso, conclusão prática em cada ponto e sem texto genérico."
---

# Minuta de despacho — consulta técnica (FACT) e recurso

## Quando disparar

"faz a minuta", "ata da CT", "ata da consulta técnica", "despacho do FACT", "despacho do recurso",
"responde o recurso", "resume o que foi tratado na reunião" — ou o usuário cola anotações de uma
reunião de CT ou o texto de um recurso e pede o despacho.

## A regra (orientação do Chefe da SSeg, 05/10/2026)

1. **Até 2.000 caracteres.** É o limite do campo de despacho do recurso e do FACT no SOL. Mirar
   **≤ 1.950** (a margem de segurança da caixa "Especificar", ver `sol-cbmrs-navegador`) e contar
   antes de entregar. Não cabendo, **não espremer nem cortar fundamento**: avisar o analista que o
   caso é de despachar direto com o Chefe da SSeg, que decide outra forma (parte no texto do próprio
   recurso/FACT e o complemento por upload no sistema).
2. **Fidelidade.** Só entra o que foi tratado na reunião (CT) ou o que o recorrente alegou
   (recurso). Nada de tema que não apareceu, recomendação genérica ou explicação da norma que
   ninguém perguntou.
3. **Conclusão prática em cada ponto.** Cada ponto termina dizendo o que fica valendo: o que foi
   orientado, o que deve ser apresentado, o que foi aceito ou não, e por quê. Texto que "fala e
   fala" e não conclui é o defeito apontado.
4. **Sem cara de IA.** Linguagem direta de despacho: frases curtas, voz ativa, sem abertura de
   cortesia, sem resumo final repetindo o que já foi dito, sem listas decorativas, sem adjetivo
   vazio ("robusto", "abrangente", "fundamental"), sem "vale ressaltar", "é importante destacar",
   "cabe salientar". Na dúvida, aplicar a skill `no-ai-slop` só para apontar os padrões.

## Antes de redigir: o que precisa estar na mão

- **CT:** o que foi perguntado, o que foi respondido em cada ponto e o encaminhamento combinado.
  Se o analista só disse "faz a ata", pedir os pontos tratados. **Não reconstruir a reunião por
  dedução** a partir do processo.
- **Recurso:** o texto do recurso (cada alegação) e a decisão do analista em cada uma. **A decisão
  (deferir, indeferir, deferir em parte) é do analista e do Chefe da SSeg**; a IA fundamenta e
  redige a decisão tomada. Sem decisão informada, perguntar.
- Data de protocolo do PPCI, quando o despacho cita norma (vigência por protocolo, como em toda
  CIA).

## Estrutura

**Ata / despacho de CT** — um parágrafo por ponto tratado, nesta ordem: o que foi consultado →
o que foi orientado → fundamento (item conferido, se houver) → o que o RT deve fazer. Fecha com o
encaminhamento em uma frase, se houver.

**Despacho de recurso** — para cada alegação: a alegação em uma frase (palavras do recorrente,
resumidas) → a análise com o item que decide → a conclusão sobre ela. Fecha com a decisão do
conjunto em uma frase.

Fundamento segue a doutrina: item conferido no PDF de `sseg/normas/pdf/`, nunca da extração
automática; banco de notificações primeiro quando o ponto já tem modelo. Citar o item e parar:
não transcrever a norma.

## Entrega

1. O texto pronto para colar, em **um bloco citável**, uma linha contínua por parágrafo e linha em
   branco só entre parágrafos (mesma regra do SOL).
2. Logo abaixo, a contagem: **"N caracteres (limite 2.000)"**. Acima de 1.950, não entregar como
   pronto: dizer o que cortar ou que o caso vai para o Chefe da SSeg.
3. Fundamento conferido (fonte · item · trecho que decide) fora do bloco, para o analista conferir.

## Desculpas que não valem

| Desculpa | Por que não vale |
|---|---|
| "Um parágrafo de contexto ajuda quem vai ler." | Só entra o que foi tratado na reunião ou alegado no recurso. |
| "Passou de 2.000; tiro o fundamento para caber." | Fundamento não se corta. O caso vai para o Chefe da SSeg. |
| "Pela documentação do processo dá para deduzir o que foi tratado na reunião." | Ata não se reconstrói por dedução: pedir os pontos ao analista. |
| "O recurso tem razão; já escrevo deferido." | A decisão é do analista e do Chefe da SSeg; a minuta redige a decisão tomada. |

## Nunca

- Passar de 2.000 caracteres, nem cortar fundamento para caber.
- Acrescentar ponto que não foi tratado na reunião ou alegado no recurso.
- Decidir o recurso pelo analista.
- Fechar parágrafo sem conclusão prática.
- Inventar item de norma ou citar item lido só em `normas/md/`.
