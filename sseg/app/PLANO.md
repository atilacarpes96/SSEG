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
  - [ ] conferir se o registro grava o esforço; se não, mostrar o esforço com que o botão abriu a conversa (o statusline recebe `effort` e `model` — mas só no terminal)
  - [ ] decidir os alertas: fluxo pesado rodando em modelo leve; norma citada sem o PDF aberto
  - [ ] opcional: o mesmo recibo por conversa no botão Gasto
- Laya (Central de Voz) como triagem de demanda: **descartado** em 12/10/2026 — os botões já escolhem fluxo e modelo sem erro, e 15% de erro mandaria análise para modelo leve

## Versão 2.0 a 2.3 — o programa vira a mesa de análise (aprovado pelo Átila em 12/10/2026)

Decisões dele: interface em HTML; checklist preenchido pelos dois (analista e Claude); medidas na
ordem do SOL. PSPCI fica fora (não cai na caixa do analista). Nenhuma skill nova: cada uma ganha
uma seção curta "Quando chamada pelo SSEG.exe" (entra/sai em JSON) e as regras ficam num lugar só.
Testes no PC do trabalho (SSH, Sincronizar processos, Abrir SOL) ficam para quando o Átila tiver acesso.

### 2.0 — Interface (pywebview + HTML no WebView2 do Windows; continua um .exe só; a lógica atual fica igual)

- [x] Casca pywebview com a ponte Python ↔ JS (`web_app.py`, `web/index.html`, `api.py`; `--classico` ou falta de WebView2 abre a janela Tk). Prévia aprovada pelo Átila e publicada como 2.0.0 em 12/10/2026
- [x] Barra de estado no alto: Programas, Pastas, Servidor, GitHub (com contador). Discreta quando está ok; o clique abre uma janelinha só daquele assunto
- [x] Tela principal = trabalho: Iniciar conversa (botões de demanda) + Processos em andamento
- [x] Menu lateral que recolhe (☰): Início, Buscar normas, Configuração, Ajuda (Reportar bug, Procurar atualização)
- [x] Configuração: Programas, Instalar o que falta, Entrar no Claude Code, Atalho Abrir SOL, Tampermonkey, Pastas. Abre na primeira vez ou quando falta algo
- [x] Quadro de log sai da frente e vira "Detalhes"
- [ ] Rodapé — gasto por processo em % da janela de 5 h ("A000…: ≈18% das 5 h"), sempre como estimativa (≈): o statusline grava o uso da janela num arquivo e o programa atribui o aumento ao processo aberto; nas chamadas do próprio programa (`claude -p --output-format json`), tokens → % pela proporção medida
  - [x] campo confirmado no PC (12/10/2026, Claude Code 2.1.296): o statusline recebe `rate_limits.five_hour.used_percentage` (inteiro 0–100, degraus de 1%) e `resets_at` (época Unix, s); também `seven_day`, `effort`, `model`, `session_id`, `transcript_path`. **Só no Claude Code de terminal** — o app de desktop não roda statusline. Degrau de 1% zera processo curto: somar tokens do processo e calibrar tokens→% pela variação do %
- [ ] Rodapé — subagentes como caranguejinhos (desenho próprio): cor = modelo (Haiku verde, Sonnet azul, Opus laranja), tamanho = esforço, animado enquanto trabalha, acena e sai ao terminar; mouse em cima: nome, tarefa, tempo. Substituem os botões Subagentes e Gasto

### Janela do processo — desenho fechado com o Átila em 12/10/2026 (substitui o 2.1–2.3 anterior nestes pontos)

Continuam valendo: Anexo L, laudo/compensatórias (modelo leve só separa), rascunho × texto final,
[PDF] montado pelo programa, skills sem duplicar.

- **Três colunas, sem terminal:** Chat | Checklist | CIA em construção
  - **Chat:** a conversa com o Claude dentro do programa, respostas formatadas. Por baixo, `claude -p --input-format stream-json --output-format stream-json` (mesmo login, pasta do SSEG, modelo e esforço de "Analisar processo"), sessão contínua (processo vivo ou `--resume`)
  - **Checklist:** os 16 passos do fluxo (como o plugin checklist-ppci) + medidas do SOL na ordem do SOL com os itens do Anexo L + compensatórias do laudo. Pendências que surgem no chat entram aqui, cada uma com o campo da resposta (ex.: as perguntas do Claude; "falta ver a fita reflexiva nas rampas")
  - **CIA:** exigências em construção, editáveis pelo analista (texto final = o que ele salvou)
  - O Claude escreve nas colunas, não só no chat: comando do `sseg.py` grava pendências e exigências no `analise.json` e a janela atualiza na hora
- **Abrir o processo não dispara nada:** a janela carrega pasta, JSON da API e checklist e espera; o Claude só trabalha quando o analista pede ("roda o check", "lê o laudo")
- **Caranguejos = indicador de lugar:** aparecem onde o trabalho acontece — na caixa do item (redator), no botão Revisar CIA, na medida (leitura do laudo), na mensagem do chat (subagente). Fila: o próximo espera cinza no seu botão. Cor = modelo (Haiku verde, Sonnet azul, Opus laranja), tamanho = esforço, mouse: "redigindo item 3 · Sonnet · 12 s"; ao terminar acena e sai. Eventos: `tool_use`/`tool_result` de Task/Agent no stream-json + chamadas do próprio programa. Se ficar confuso, depois um resumo no rodapé
- **Rodapé:** ≈% das 5 h por processo (`rate_limits.five_hour`, confirmado)

#### 2.1 — janela de 3 colunas
- [x] Chat em stream-json dentro do programa (`chat.py`): sobe só na 1ª mensagem, sessão no `analise.json` (`--resume`), respostas em markdown, ferramentas numa linha discreta. Permissões sem perguntar: ler, procurar, subagentes e `python sseg/scripts/*`, `pdftotext`/`pdftoppm`, `git status/log/diff`; edição só com `acceptEdits` na pasta do SSEG e na do processo; o resto volta como "negado" no chat. Ler o SOL pelo Chrome não roda nesta janela (ainda)
- [x] Checklist: 16 passos (`workflow/checklist-analise.json`) + medidas do SOL na ordem do SOL com o Anexo L (`workflow/anexo-l.json`) + pendências do chat com campo de resposta e "Mandar respostas ao Claude"
- [x] CIA: ✗ no item vira exigência; rascunho do Claude à parte, texto final salvo pelo analista, contador de 2.000, ordem, "copiar a CIA" (só o final)
- [x] `sseg.py analise --pasta <processo> pendencia|exigencia|passo|ver` grava no `analise.json` (`scripts/analise_registro.py`); a janela relê a cada 2 s
- [x] Caranguejo da conversa (Task/Agent no stream: cor do modelo do subagente, acena ao terminar) e ≈% das 5 h do processo no rodapé (`rate_limit_event`)
- [x] **Nenhum fluxo abre terminal** (pedido do Átila, 12/10/2026 — o programa vai para a seção e muita gente não usa terminal): "Analisar processo" da grade pede o código e abre a janela de 3 colunas; os outros fluxos abrem uma janela de conversa do programa (mesma identidade), com a mensagem sugerida no campo e nada rodando até o envio. Terminal e "Copiar o prompt" ficam no ⋯ (avançado)
- [x] **Resposta visual em todas as janelas** (regra do Átila, 12/10/2026): markdown renderizado com tabelas de verdade (tudo escapado; HTML do modelo nunca passa) e blocos ```sseg-*``` com JSON que o programa desenha — `sseg-status` (selo), `sseg-dados` (cartões), `sseg-definidora` (hipóteses), `sseg-perguntas` (campos + "Mandar respostas"; viram pendências sem duplicar), `sseg-exigencia` (contador e "Pôr na CIA" como rascunho), `sseg-norma` ([PDF] pelo programa). Bloco inválido vira texto. Ensinado no prompt de sistema da janela (`chat.GUIA_VISUAL`). Claro e escuro
- [x] **Links do SOL na janela do processo** (2.1.1): "Licenciamento no SOL" (`#/licenciamento/consulta/<id>`, o id interno do `api-<id>.json`; sem ele, a consulta) e "Análise técnica no SOL" (`#/analise-tecnica/<id>` só se o JSON trouxer `idAnaliseTecnica` — o id da análise é outro; sem ele, a caixa). Abrem no Chrome (login do SOL). Os mesmos links vão no prompt de sistema da conversa
- [ ] Janela própria de cada fluxo (Começar o dia, Revisar CIA, Minuta/despacho, Incorporar norma, Notificação avulsa, Pergunta de norma) — o tipo de cada uma o Átila fecha com a sessão do PC
- [x] Prévia aprovada: o Átila mandou largar como oficial (2.1.0, 12/10/2026)
- [ ] Teste no PC com processo real: permissões do `claude -p` no Windows, `python` no PATH, sessão retomada

#### 2.2 — redator na caixa do item
- [ ] Achado curto → `claude -p` redige (banco, normas comentadas, `ppci-notificacao-cia`) → texto + fundamento; [PDF] pelo programa; contador de 2.000; rascunho × texto final; caranguejo sobre a caixa e fila

#### 2.3 — esteira Revisar → Lançar → Arquivar
- [ ] Cada etapa com o seu caranguejo; frase do que faz; feitas com ✓ e tempo; Lançar no SOL só depois do "pode lançar", com a lista do que vai ser colado. Absorve os itens 2 a 5 da 1.2

### Ideia a amadurecer — "Ponte SOL" (pedido do Átila, 12/10/2026; NÃO construir sem confirmar)

O Claude ler o SOL por comando, sem print e sem navegar, gastando menos token:
- script do Tampermonkey nas páginas do solcbm abre uma ponte com um servidor local do SSEG.exe (localhost), como o `sseg.py receber` já faz; o programa ou o Claude pede ("ler licenciamento 239812", "listar arquivos", "baixar arquivo X") e a **própria aba logada** faz o fetch na API e devolve o JSON para a pasta do processo — o token da sessão nunca sai do navegador
- comandos `sseg.py sol ler|arquivos|baixar --id <id>`; na conversa entra só o resumo filtrado, não o JSON inteiro
- **só leitura** no começo; escrita (lançar inconformidade) só depois, com o "lança" do analista e a tela de conferência da esteira 2.3, e as regras da `sol-cbmrs-navegador` (2.000 caracteres, campo "Outros")
- substitui aos poucos o `sol-leitor` e os prints; medir o ganho pelo Gasto
- **Antes de construir:** confirmar com o Átila. Pela decisão de 06/10/2026 (consulta ao SOL fora do navegador barrada; acesso automatizado só com autorização expressa e, de preferência, consulta à chefia/PROCERGS), levar a ideia à chefia/PROCERGS antes — mesmo sendo a aba logada do analista que chama a API. Depois, testar só leitura num processo real

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
