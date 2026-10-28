---
name: base-do-sol-e-aba-processos
description: Como o SSEG coleta todos os processos do SOL, monta o banco SQL no servidor, preenche as pastas com os Marcos, faz a pré-análise antes da caixa e mostra tudo na aba Processos do SSEG.exe (painel, mapa, ficha e busca nas CIAs) — etapa por etapa, sem gastar token
sources: [claude-code]
---

# Base do SOL e aba Processos

Montado em 28/10/2026, a partir da Consulta SOLCBM do Sgt Magalhães (coletor e visualizador dele,
de 17/10/2026). A ideia: o analista não precisa abrir a pasta do processo para saber o que o SOL tem.
A ficha no SSEG.exe mostra tudo, e a pasta fica para o agente de IA.

**Nenhuma etapa usa modelo de IA.** São scripts Python no servidor, sem token. O Claude só entra
depois, para analisar, e lê o resultado pronto em vez de navegar no SOL.

## A cadeia, em sete etapas

```
 SOL (sistema oficial)
   │  1. coleta: sol_base.py, 8h20 · 12h20 · 16h20 dos dias úteis (só leitura)
   ▼
 base do servidor (~/sseg-base-sol/): um JSON por processo + texto de cada CIA
   │  2. banco: sol_banco.py, no fim de cada coleta
   ▼
 solcbm.db (tabelas no formato da Consulta SOLCBM)
   │  3. consultas prontas: sol_consulta.py ──► 6. SSEG.exe, aba Processos
   │                                       └──► 7. Claude do servidor
   ▼
 4. pastas dos processos: Marcos, histórico e resumo
 5. pré-análise antes da caixa (processo distribuído que ainda não chegou)
```

### 1. Coleta (`sol_base.py`)

- Lista todos os PPCI do SOL (~6,9 mil, 7 consultas) e, de cada processo vivo ou que mudou de situação,
  baixa quatro coisas: o licenciamento (memorial, ocupações, medidas, envolvidos, plantas), os Marcos
  (linha do tempo), o histórico (análises, recursos, vistorias) e as informações do processo (laudos,
  PRPCI e vistoria; voltou em 28/10/2026, decisão do Átila).
- Baixa o PDF de cada CIA emitida, guarda só o texto (`pdftotext`) e descarta o PDF.
- Ritmo educado: 0,15 s entre consultas, nova tentativa em erro passageiro, para se o SOL cair.
  A cada 2 semanas (domingo, 3h) faz a coleta completa, inclusive dos encerrados.
- Usa a sessão do Chromium do servidor, com o login automático autorizado pelo Átila em 17/10/2026.
  Coleta autorizada pelo Sgt Magalhães, com a chefia avisada.

### 2. Banco (`sol_banco.py`)

- Transforma a base em tabelas SQL: `processos`, `ocupacoes`, `medidas`, `envolvidos`, `marcos`,
  `analises`, `boletos`, `elementos_graficos`, `laudos`, `areas_memorial`, `riscos_especiais` e `cias`.
- As regras de leitura do JSON do SOL são as do Sgt Magalhães (`scripts/dados/solcbm_visoes.sql`).
  Conferido em 28/10/2026: 40 processos montados pelos dois caminhos deram as 12 tabelas iguais.
- Acrescenta colunas de busca sem acento: "antipanico" acha "antipânico".
- Leva ~3 min e troca o banco de uma vez no fim; quem está consultando nunca vê banco pela metade.

### 3. Consultas prontas (`sol_consulta.py`)

| consulta | devolve |
|---|---|
| `resumo` | números do painel: por situação, grupo de ocupação, município e ano |
| `opcoes` | valores dos filtros |
| `mapa` | ponto de cada edificação |
| `pesquisa` | processos com filtros (texto, município, divisão, risco, área, com CIA…) |
| `processo` | a ficha inteira de um processo |
| `cias` | CIAs que contêm um trecho, com o parágrafo em volta |

O SSEG.exe chama pela porta do servidor (`porta.py banco <consulta>`). Cada resposta leva 1 a 2 s.

### 4. Pastas dos processos

Antes, só os processos da caixa tinham os Marcos na pasta (24 de 486). Agora, depois de cada coleta,
toda pasta que a base conhece recebe `marcos.json`, `historico.json` e `marcos-resumo.json` (data de
protocolo, número da análise, CIAs anteriores, CA, recursos). Se o `sol_caixa.py` leu o processo
depois da base, fica a leitura dele.

### 5. Pré-análise antes da caixa

Processo distribuído ao analista (planilha "Distribuição Análise") e ainda não concluído, que não
chegou à caixa do SOL, recebe `base-api-<ID>.json` (o licenciamento da base) e a pré-análise
documental (`pre_analise.py`): definidora marcada pelo RT, rota da tabela, normas do campo 4, travas.
O nome é diferente do `api-<ID>.json` de propósito: é esse arquivo que faz o `sol_caixa.py` avisar
"processo novo na caixa". Quando o processo chega à caixa, o JSON novo é baixado e a pré-análise refeita.

### 6. SSEG.exe, aba Processos (2.7.0)

Quatro vistas no topo da aba:

- **Painel:** número de processos e de CIAs, área licenciada, mapa de todas as edificações (cor pela
  situação) e gráficos por situação, grupo, município e ano. Clicar numa barra abre a lista filtrada.
- **Lista:** a busca e os filtros de antes, agora com mapa que segue o filtro.
- **Ficha:** clique na linha ou no ponto do mapa. Edificação e ocupações, campo 4, envolvidos com
  contato, análises, recursos e vistoria, inconformidades das plantas, texto de cada CIA, linha do
  tempo dos Marcos, boletos e laudos; atalhos para o SOL, o Google Maps e a pasta do processo.
- **Busca nas CIAs:** trecho em todas as CIAs já emitidas; o resultado abre a ficha naquela CIA.

A lista e o mapa usam o índice que o PC já baixou; painel, ficha e busca perguntam ao servidor.
O mapa vem do OpenStreetMap (Leaflet, incluído no programa).

### 7. Claude do servidor

Em vez de abrir JSON da base, o Claude roda a consulta pronta e lê só a resposta:

```
python3 sseg/scripts/sol_consulta.py processo '{"numero": "A00050053AA001"}'
python3 sseg/scripts/sol_consulta.py cias '{"q": "barra antipanico"}'
python3 sseg/scripts/sol_consulta.py pesquisa '{"divisao": "F-6", "com_cia": 1}'
```

Serve para "como outros analistas notificaram isso?", "esse RT já recebeu CIA por isso antes?",
estatística da seção. É referência de aplicação, nunca fundamento: o item continua sendo conferido
no PDF da norma.

## Dados pessoais

O banco tem CPF, e-mail e telefone dos envolvidos e o pagador dos boletos. O Átila decidiu em
28/10/2026 mostrar tudo na ficha, como a Consulta SOLCBM. Tudo fica no servidor, fora do Git; o PC
recebe só o que a tela pede. Nada disso vai para o repositório (que é público).

## Onde fica cada coisa

| o quê | onde |
|---|---|
| base (JSON e texto das CIAs) | servidor, `~/sseg-base-sol/proc/` e `cia/` |
| banco SQL | servidor, `~/sseg-base-sol/solcbm.db` |
| índice da aba (lista e mapa) | servidor `~/sseg-base-sol/indice.json` → PC `%APPDATA%\SSEG\base-sol.json` |
| scripts | `sseg/scripts/sol_base.py`, `sol_banco.py`, `sol_consulta.py`, `pre_analise.py`, `porta.py` |
| regras de leitura do JSON | `sseg/scripts/dados/solcbm_visoes.sql` |
| tela | `sseg/app/web/index.html` (aba Processos) |
| log das coletas | servidor, `~/rotinas/logs/sol-base.log` |
