---
name: analise-laudo-inviabilidade-tecnica
description: Registro do caso Hotel Valler (medida compensatória proposta no laudo sem linha no campo 4), a redação de referência usada, e o regime normativo do laudo de inviabilidade técnica
sources: [cowork]
---

# Laudo de inviabilidade técnica — registro de caso

> O **procedimento** de análise (o que verificar: representação, coerência com a planta,
> correspondência com o campo 4) vive na skill `ppci-analise-processo`, seção 7. Este doc é
> **registro**.

## Fatos fixados

- O laudo que chega junto com o processo para análise **já foi aprovado pela chefia** — o
  analista, nesta fase, **não** reavalia se a medida compensatória é juridicamente
  admissível ou tem respaldo normativo em abstrato. Isso foi decidido antes.
- O campo **"4. Medidas de segurança"** do SOL tem as colunas: `Medida de segurança | Norma |
  Inviabilidade técnica | Compartimentação`. A medida que sofre a inviabilidade aparece
  marcada na coluna **Inviabilidade técnica** (ex.: "Possui parcial" para Saída de
  Emergência); as demais ficam "Não".
- **Regime normativo do laudo e das medidas compensatórias:** RT 05 Parte 07/2025,
  item 5.6 "Da inviabilidade técnica e das medidas compensatórias" (subitens 5.6.1 a 5.6.6,
  com diretrizes de aprovação em anexo). ⚠️ Item obtido por extração automática — **conferir
  o número exato no PDF oficial antes de citá-lo em CIA**.
- Para checar representação e coerência é necessário o conteúdo gráfico real (planta baixa,
  cortes). O print do SOL só lista nome/tipo/data/status dos arquivos — pedir os PDFs.

## Caso registrado — Hotel Valler (A00016097AA002)

O laudo propôs **Plano de Emergência com simulados a cada 4 meses** como medida
compensatória, mas o Plano de Emergência **não consta no campo 4** — e não consta
corretamente, porque a Tabela 6B do Anexo B do Decreto 51.803/2014 **não exige** Plano de
Emergência para a divisão B-1 na faixa 6 < H ≤ 12 m (ver
[[ocupacao-definidora-e-tabelas-exigencias]]). Ou seja: a obrigatoriedade decorre
exclusivamente da medida compensatória proposta no laudo.

Notificado pelo usuário com a opção do SOL "Ausência de marcação no campo 'Medidas de
Segurança' do item 'Plano de Emergência'" + especificação livre.

**Redação de referência para o campo "Especificar"** (usada em análise real, ainda não
validada pela chefia — ponto de partida):

> - Deverá incluir a medida de segurança "Plano de Emergência" no campo "4. Medidas de
> Segurança", tendo em vista que o Laudo de Inviabilidade Técnica apresentado a propõe como
> medida compensatória e ela não consta lançada no processo. Registra-se que, para a divisão
> B-1 na faixa de altura 6 < H ≤ 12 m, o Plano de Emergência não é medida exigida pela
> Tabela 6B do Anexo B do Decreto nº 51.803/2014, decorrendo sua obrigatoriedade, neste
> caso, da própria medida compensatória proposta no laudo.

## Por que essa redação precisa ser explícita

A opção padrão do SOL traz fundamento genérico embutido — "exigida conforme a legislação e
regulamentação aplicáveis" — que **contradiz** o caso concreto quando a exigência nasce do
laudo e não da tabela do Decreto. Sem a correção no campo "Especificar", o RT contestaria
com razão.
