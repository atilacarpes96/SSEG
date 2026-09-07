---
name: verificacao-normas-print-cia
description: Ponteiro — a rotina de conferir as normas do campo 4 do print PPCI virou a seção 6 da skill ppci-analise-processo; aqui ficam só as limitações conhecidas dessa conferência
sources: [cowork]
---

# Verificação das normas do campo 4 — limitações conhecidas

> A rotina em si (conferir cada norma citada no campo "4. Medidas de segurança" contra o
> [[00-indice-normativo]], aplicando a vigência por data de protocolo) virou a **seção 6 da
> skill `ppci-analise-processo`**, e roda automaticamente sempre que chega um print. A regra
> de vigência por data de protocolo está nas Instruções do projeto. Restou aqui só o que é
> limitação registrada.

## Limitações

- **A data de protocolo pode não estar visível no print.** Ela é o que decide entre versões
  de uma mesma RT (RT 01/2022 × RT 01/2024). Quando não estiver na página, pedir ao usuário
  ou buscar em outra fonte do processo — **não decidir no escuro**.
- **As datas exatas de transição entre versões de RT ainda não estão registradas no
  projeto.** Sem elas, um caso limítrofe não se resolve internamente: verificar na fonte
  oficial ou com a chefia.
- **RT que não consta do índice do projeto** → sinalizar a divergência, não dar como certa
  nem como errada.
- **RT 17 Parte 01/2025 (hidrantes e mangotinhos)** só é obrigatória a partir de 01/01/2027 —
  hoje é facultativa, então a ausência dela **não é necessariamente pendência**.

## Forma legível por máquina

O índice usado pela conferência automática está em `scripts/dados/indice_normas.json`. Ao
atualizar o [[00-indice-normativo]] (nova RT, data de vigência confirmada, data de transição
descoberta), atualizar **os dois**.
