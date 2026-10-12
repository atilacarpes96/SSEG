# Plano do programa SSEG (SSEG.exe) — versão 1.1

Decisões do Átila em 11/10/2026. Marcar `[x]` no mesmo commit em que o item fica pronto.

## Decisões

- **Instalação:** tudo de que o projeto precisa no PC é instalado pelo próprio programa, sem
  o analista abrir o PowerShell: Git, Python 3.12, Poppler e o Claude Code de linha de comando.
  Pelo `winget` com `--scope user` (não pede administrador) e pelo instalador oficial do
  Claude Code. O login do Claude Code continua com o analista: o programa abre e ele entra
  pelo navegador uma vez.
- **GitHub:** um botão só, "Sincronizar": tela de conferência → `pull --ff-only` → commit →
  push. Nunca `--force`, nunca `add -f`.
- **Gasto por conversa e por subagente:** entra nesta versão.
- **Travas do commit** saem do hook do Claude Code e vão para um `pre-commit` do git, para
  valer em qualquer commit (programa, PowerShell ou Claude).
- **Fonte única dos fluxos:** o programa não guarda modelo, esforço ou prompt. Lê
  `sseg/workflow/fluxos.json`, gerado pelo `painel.py`, o mesmo que alimenta o Painel SSEG.

## Itens

- [x] **0. Decisões** (11/10/2026)
- [x] **1. Instalar o que falta** (1.0.2, 11/10/2026 — falta o teste no PC do trabalho, item 8)
  - [x] conferir cada pré-requisito (Git, Python que não seja o atalho da Store, Poppler, Claude Code)
  - [x] botão "Instalar o que falta" com `winget --scope user` e o instalador oficial do Claude Code, com o andamento no quadro
  - [x] ajustes do CLAUDE.md feitos sozinhos: `python3.exe`, PATH com Poppler e Python antes do Git, `PYTHONUTF8=1`
  - [x] PC sem `winget`: dizer o que baixar e onde, sem travar o resto
  - [x] "Entrar no Claude Code": abre o login uma vez e confere que ficou logado
- [x] **2. Travas no git** (1.0.3, 11/10/2026: também barra `--no-verify` no Claude, texto validado do banco e arquivo ignorado forçado; instala sozinho ao abrir o Claude Code no clone)
  - [x] `pre-commit` que chama as regras do `sseg_hooks.py` (arquivo de processo, `add -f`, `testar.py`)
  - [x] instalado e conferido pelo "Criar / conferir pastas"
  - [x] caso no `testar.py`: commit com arquivo de processo é barrado
- [x] **2b. Sincronizar processos com o servidor** (1.0.4, 11/10/2026 — pedido vindo do teste no PC)
  - [x] sobe o que mudou no PC em todos os processos; desce o que está mais novo no servidor (`sseg.py sincronizar` / `sseg.py trazer`)
  - [x] conflito (mudou dos dois lados) não sobrescreve: tela de conferência, o analista escolhe
  - [x] planta não vai nem vem; nada pelo GitHub; apagar não se propaga
  - [x] sem chave SSH ou sem o apelido `sseg-servidor`: diz o que falta
  - [ ] teste do Átila no PC (precisa da chave SSH autorizada)
- [x] **2c. Atualização automática do programa** (1.0.6): confere a versão ao abrir; "Atualizar o programa" baixa, fecha, troca o .exe e reabre. Testado no build numa cópia 0.0.1 numa pasta com espaço
- [x] **3. Sincronizar com o GitHub** (1.1.0, 11/10/2026)
  - [x] tela de conferência: arquivos mudados, o que fica fora (mesmas travas, `sseg_hooks.py conferir`), campo da mensagem
  - [x] confere `user.name` e `user.email` e pede se faltar
  - [x] `pull --ff-only` → commit → push; parou, explica em português; o barrado fica fora do commit e na pasta
  - [x] skill que mudou no pull sai em `.zip` (já existe no 1.0)
- [x] **4. Fonte única dos fluxos**
  - [x] `painel.py --fluxos` gera `sseg/workflow/fluxos.json`: modelo e esforço tirados do texto da política; skill, subagentes e prompt no `painel.py`
  - [x] Painel SSEG: aba Conversas, do mesmo retrato
  - [x] `testar.py`: `fluxos.json` igual ao que a política gera; subagente com nome completo de modelo (o `revisor-cia` estava com o atalho `sonnet`)
- [x] **5. Iniciar conversa**
  - [x] um botão por demanda: Começar o dia, Analisar processo, Revisar CIA, Minuta ou despacho, Incorporar norma, Notificação avulsa, Pergunta de norma
  - [x] "Abrir no terminal": Claude Code na pasta do SSEG com `--model` e `--effort` da política e o prompt (código do processo pedido quando precisa)
  - [x] "Copiar o prompt", para quem usa o app do Claude, dizendo qual modelo escolher
- [x] **6. Subagentes**
  - [x] lista de `.claude/agents/`: nome, modelo, para que serve, em que conversa entra
  - [x] acusa atalho (`haiku` = 4.5, `sonnet`, `opus`) e nome desconhecido
- [x] **7. Gasto**
  - [x] lê `~/.claude/projects/<pasta do SSEG>/**/*.jsonl` (inclui subagentes), cada resposta uma vez
  - [x] hoje, 7 e 30 dias, por dia, por modelo, principal × subagente, as 10 conversas que mais gastaram
  - [x] em tokens (entrada, cache, saída), não em US$
- [x] **9. Reportar bug** (praxe dos apps do Átila): descrição + versão + sistema + fim do quadro, limpos de código de processo, pasta e nome de planta/PDF/CIA; abre issue no GitHub ou copia para a conversa do servidor
- [x] **10. Procurar atualização** no rodapé, com a versão atual, junto do Reportar bug
- [ ] **8. Entrega**
  - [x] versão 1.1.0 (1.1.1: janela cabe em tela de 768 px); o build abre e fotografa cada tela (janela, Subagentes, Gasto, Reportar bug, Iniciar conversa, GitHub) e falha se alguma der erro
  - [x] entrada em `workflow/atualizacoes.md`
  - [ ] teste do Átila no PC (lista abaixo); ajustes

## Versão 1.2 — menos token: o mecânico sai da conversa (decisão de 11/10/2026)

Critério: script onde nenhuma escolha normativa acontece (o mesmo dos subagentes leves).
Escolher modelo do banco, enquadrar ocupação e decidir se a exigência procede ficam com o
Claude. Ler o SOL continua no Chrome do analista. Antes de priorizar 2 a 5, medir com o botão
Gasto em análises reais onde o token vai (início, meio ou fim da conversa).

- [x] **1. Buscar nas normas e no banco** (1.2.0): banco → normas comentadas → texto convertido (marcado "só localiza"), sem acento, todos os termos, número não casa no meio de outro; [copiar] o modelo ou o trecho com arquivo e linha. O trabalho do `localizador-normas` sem token
- [x] **1b. [PDF] em cada resultado** (1.2.2): abre o PDF oficial de `normas/pdf/` no Edge/Chrome, na página provável (item citado + termos, pelo `pdftotext`); modelo do banco liga à primeira norma que cita. Norma sem PDF na pasta fica sem link
- [ ] **2. Pré-análise:** "Analisar processo" roda antes o `sseg.py check` no JSON da pasta do processo e a conversa começa lendo o resumo
- [ ] **3. Arquivar e enviar por botão:** sem rodadas do Claude no fim da conversa
- [ ] **4. Pré-revisão da CIA:** "Revisar CIA" roda antes o `sseg.py revisar-cia` e abre a conversa com o resultado
- [ ] **5. Conferir a caixa do SOL:** colar o texto → 2.000 caracteres, hífen, quebra de linha
- [ ] **6. Medir:** Gasto antes e depois, em análises reais
- [x] **1.2.1 — correção:** "Atualizar o programa" trocava o arquivo, mas o .exe novo abria com "Failed to load Python DLL" (herdava as variáveis do PyInstaller do antigo e procurava a DLL na pasta temporária dele, já apagada). O .bat agora sobe com ambiente limpo, e o teste do build exige que o .exe reaberto escreva a marca (antes, a própria janela de erro contava como "reaberto")

## Versão 1.3 — ideias a amadurecer

- [x] **SOL Entrar no programa** (1.3.0, autorizado pelo Átila em 12/10/2026, opcional): Atalhos → "Atalho Abrir SOL" copia `sseg/ferramentas/sol-entrar/` para `%LOCALAPPDATA%\SSEG\sol-entrar` e cria "Abrir SOL" na Área de Trabalho (ícone do Chrome, minimizado); "Tampermonkey" abre a extensão na Chrome Web Store, copia o script e mostra os 3 passos. A senha fica só no Chrome. O build cria o atalho num Windows limpo
  - [ ] Átila testa no PC do trabalho: atalho → contagem de 5 s → entra

- [ ] **Recibo do turno:** linha discreta no fim de cada resposta do Claude Code com o que foi usado de verdade — modelo, esforço, subagente, norma aberta (`sseg/normas/`, `normas/pdf/`, nome curto: "RT 14", "banco") e script (`sseg.py ...`). Feito por gancho `Stop` no `sseg_hooks.py`, que lê o registro da conversa e mostra a linha só ao analista (`systemMessage`): zero token e sem depender do Claude lembrar. Antes de construir:
  - [ ] testar se o `systemMessage` aparece na conversa Local do app do Claude, além do terminal
  - [ ] conferir se o registro grava o esforço; se não, mostrar o esforço com que o botão abriu a conversa
  - [ ] decidir os alertas: fluxo pesado rodando em modelo leve; norma citada sem o PDF aberto
  - [ ] opcional: o mesmo recibo por conversa no botão Gasto
- Laya (Central de Voz) como triagem de demanda: **descartado** em 12/10/2026 — os botões já escolhem fluxo e modelo sem erro, e 15% de erro mandaria análise para modelo leve

## Versão 2.0 a 2.3 — o programa vira a mesa de análise (aprovado pelo Átila em 12/10/2026)

Decisões dele: interface em HTML; checklist preenchido pelos dois (analista e Claude); medidas na
ordem do SOL. PSPCI fica fora (não cai na caixa do analista). Nenhuma skill nova: cada uma ganha
uma seção curta "Quando chamada pelo SSEG.exe" (entra/sai em JSON) e as regras ficam num lugar só.
Testes no PC do trabalho (SSH, Sincronizar processos, Abrir SOL) ficam para quando o Átila tiver acesso.

### 2.0 — Interface (pywebview + HTML no WebView2 do Windows; continua um .exe só; a lógica atual fica igual)

- [ ] Casca pywebview com a ponte Python ↔ JS para as funções que já existem; build e fotos no CI como hoje — em andamento no ramo `sseg-2.0` (`web_app.py`, `web/index.html`, `api.py`; `--classico` abre a janela Tk). Build do ramo sai como **prévia** (prerelease `app-v2.0.0-previa`), que o programa nunca oferece como atualização; vai para o main quando o Átila aprovar as fotos
- [ ] Barra de estado no alto: Programas, Pastas, Servidor, GitHub (com contador). Discreta quando está ok; o clique abre uma janelinha só daquele assunto
- [ ] Tela principal = trabalho: Iniciar conversa (botões de demanda) + Processos em andamento
- [ ] Menu lateral que recolhe (☰): Início, Buscar normas, Configuração, Ajuda (Reportar bug, Procurar atualização)
- [ ] Configuração: Programas, Instalar o que falta, Entrar no Claude Code, Atalho Abrir SOL, Tampermonkey, Pastas. Abre na primeira vez ou quando falta algo
- [ ] Quadro de log sai da frente e vira "Detalhes"
- [ ] Rodapé — gasto por processo em % da janela de 5 h ("A000…: ≈18% das 5 h"), sempre como estimativa (≈): o statusline grava o uso da janela num arquivo e o programa atribui o aumento ao processo aberto; nas chamadas do próprio programa (`claude -p --output-format json`), tokens → % pela proporção medida
  - [ ] confirmar no PC o campo do statusline (o Claude Code 2.1.296 tem `rate_limits.five_hour` no código; ver se chega ao statusline e em que unidade)
- [ ] Rodapé — subagentes como caranguejinhos (desenho próprio): cor = modelo (Haiku verde, Sonnet azul, Opus laranja), tamanho = esforço, animado enquanto trabalha, acena e sai ao terminar; mouse em cima: nome, tarefa, tempo. Substituem os botões Subagentes e Gasto

### 2.1 — Janela "Análise do processo" (checklist marcado pelo analista)

- [ ] Medidas de `especSeguranca.medidas` do JSON da API, na ordem do SOL
- [ ] Itens de cada medida pelo Anexo L da RT 05 Parte 1.1 (`normas/rt-05-parte01-1-2016-ppci-completo.md`): todas com "Memorial"; as da L.1 ganham os itens de planta da coluna "A" (Saídas: alíneas a) a i) + lotação no grupo F; sinalização de orientação e iluminação de balizamento na alínea i)); as da L.2 só o Memorial
- [ ] Laudo de inviabilidade (`especSeguranca.laudo.txtClob`; cada medida NAO_POSSUI / POSSUI_PARCIAL / POSSUI_TOTAL): um caranguejo leve lê o laudo uma vez e **só separa** as compensatórias por medida (extração, sem decidir); elas viram itens a conferir, inclusive em planta. Se a compensatória cobre o déficit é do analista e do principal (política de modelo). Ver `workflow/analise-laudo-inviabilidade-tecnica.md`
- [ ] Faixa no topo: passos do fluxo (data de protocolo, definidora, tabela, laudo, análise anterior) + link para a pasta do processo
- [ ] Reanálise: começa da CIA anterior; cada item "atendida" ou "REITERO"
- [ ] Coluna "CIA em construção" com as exigências aceitas, na ordem
- [ ] `analise.json` na pasta do processo: vai ao servidor pelo Sincronizar processos, nunca ao GitHub; comando no `sseg.py` para a conversa Local ler e escrever o mesmo arquivo

### 2.2 — Caixa do item com o Claude redigindo junto (começar por saídas de emergência e extintores, testar em processo real)

- [ ] Analista escreve o achado curto ("porta da escada 80 cm"); ao parar de digitar ou por botão, `claude -p` (Sonnet, esforço da política) redige pelo caminho normal (banco, normas comentadas, `ppci-notificacao-cia`) e devolve texto + fundamento ("RT 11, item 5.4.2")
- [ ] O modelo não usa PDF: com o fundamento, o **programa** monta o [PDF] sem token (mecanismo da busca 1.2.2), só para o analista conferir
- [ ] O que o analista escreveu fica; a redação vem como sugestão. Contador de 2.000 caracteres sempre visível
- [ ] **Regra:** cada item guarda "rascunho do Claude" e "texto final" (o que o analista salvou). CIA, revisão e lançamento leem **só o texto final**; o revisor que acha problema num texto editado aponta e sugere, não reescreve. Motivo (Átila): ele editava a notificação, o modelo se confundia na revisão e voltava ao texto antigo
- [ ] Redator como caranguejo azul sobre a caixa; vários itens formam fila visível; o gasto soma no % do processo

### 2.3 — Esteira no fim da análise (absorve os itens 2 a 5 da 1.2)

- [ ] Revisar CIA → Lançar no SOL → Arquivar e enviar, cada etapa com o seu caranguejo
- [ ] Em andamento: animado, com a frase do que faz ("conferindo item 3 de 7 na RT 11"); próximas em cinza; feitas com ✓ e o tempo
- [ ] Lançar no SOL só depois do "pode lançar" do analista, com a lista do que vai ser colado

## O que o Átila testa no PC (1.1.1)

Abrir o SSEG.exe 1.0.6 que já está no PC: ele deve oferecer "Atualizar o programa (1.1.1)". É o
teste da atualização automática — clicar e ver se fecha, troca e reabre já na 1.1.1.

1. **Rolagem:** a janela rola com a roda do mouse; quadro e rodapé ficam fixos embaixo.
2. **Programas e Pastas:** tudo ✓ como na 1.0.4 (pasta do SSEG `E:\Atila\bombers\SSEG`).
3. **GitHub → Verificar atualizações → Atualizar agora** (traz o 1.1.0 do repositório: fluxos e subagentes).
4. **Sincronizar processos** (agora com a chave SSH): ver a tela de conferência; conflito, se houver, mostrar antes de escolher; conferir que planta não subiu.
5. **Iniciar conversa:** "Pergunta de norma" → "Abrir no terminal" deve abrir o Claude Code em Haiku 5.5 médio na pasta do SSEG; "Analisar processo" pede o código; "Copiar o prompt" copia.
6. **Subagentes:** três, todos com nome completo de modelo, sem ⚠.
7. **Gasto:** mostra as conversas do Claude Code feitas neste PC na pasta do SSEG (pode estar vazio se este PC usou só o app).
8. **Sincronizar com o GitHub:** com uma mudança pequena de teste (ou sem mudança: deve dizer que está igual); se houver arquivo de processo dentro do clone, ele aparece "fica fora".
9. **Reportar bug:** escrever qualquer coisa e conferir na prévia que não aparece código de processo, pasta nem nome de planta; "Copiar para a conversa" e colar aqui.
10. **Procurar atualização:** deve dizer que já está na mais nova.
