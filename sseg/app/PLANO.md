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
  - [x] 16/10/2026: `scripts/pre_analise.py` (script, sem Claude) converte o api-<ID>.json do SOL para o formato do `check`, roda o `check` e grava `pre-analise.json` e `pre-analise.txt` na pasta do processo (descem ao PC no sincronizar). O `sol_caixa.py` roda nos processos novos da caixa. Fica de fora: data de protocolo da 1ª análise (aba Marcos) e as compensatórias do laudo
  - [ ] Janela do processo mostrar o `pre-analise.txt` e a skill de análise começar por ele
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
- [x] **2.1.2 — correções do teste real (A00024749AA002, 12/10/2026):**
  - CIA: caixa única por item; com rascunho do Claude e sem final, já vem preenchida ("rascunho do Claude — edite e salve") e salvar vira o final (o rascunho segue guardado); seletor de medida; **"Pedir ao Claude"** manda o texto da caixa como achado e o rascunho volta ao MESMO item (`sseg.py analise rascunho <id> -`), com caranguejo "redigindo…" no item
  - Chat: texto longo pela entrada (heredoc com `-`), sem `cd ... &&`; liberados `cd` e o PowerShell para `python sseg/scripts/*`; comando bloqueado aparece numa linha amigável (detalhe em Detalhes)
  - [PDF]: "Resolução Técnica nº 11/2016" também casa; um `sseg-norma` por norma; o quadro diz qual rótulo abriu qual PDF (o caso RT 11 → RT 04 não se reproduziu aqui: falta o texto do bloco)
  - Reportar bug: imagens (Ctrl+V, arrastar, "Tirar print da janela") e log (Detalhes, eventos das conversas, erros), limpos; o .zip vai ao servidor por SSH (`~/sseg-relatos/`, fora do git) ou fica em Documentos\SSEG-relatos; a issue leva só o texto limpo + o id do relato
- [x] **2.1.3:** botões do SOL abrem pelo Claude, **na aba do SOL do grupo do Claude no Chrome** (o login mora nela; aba nova cai no login). O chat sobe com `--chrome` e pode abrir e LER o SOL (tabs_context, navigate, find, get_page_text, read_page, javascript_tool) quando o analista pedir; clique e formulário não estão liberados (lançar fica para a 2.3). Laudo de inviabilidade sem HTML (`<p>`, `&nbsp;`). Botões do item da CIA não se espremem mais
- [ ] Janela própria de cada fluxo (Começar o dia, Revisar CIA, Minuta/despacho, Incorporar norma, Notificação avulsa, Pergunta de norma) — o tipo de cada uma o Átila fecha com a sessão do PC
- [x] Prévia aprovada: o Átila mandou largar como oficial (2.1.0, 12/10/2026)
- [ ] Teste no PC com processo real: permissões do `claude -p` no Windows, `python` no PATH, sessão retomada

#### 2.2 — redator na caixa do item
- [ ] Achado curto → `claude -p` redige (banco, normas comentadas, `ppci-notificacao-cia`) → texto + fundamento; [PDF] pelo programa; contador de 2.000; rascunho × texto final; caranguejo sobre a caixa e fila

#### 2.3 — esteira Revisar → Lançar → Arquivar
- [ ] Cada etapa com o seu caranguejo; frase do que faz; feitas com ✓ e tempo; Lançar no SOL só depois do "pode lançar", com a lista do que vai ser colado. Absorve os itens 2 a 5 da 1.2

#### 2.4 — Espelho no celular (pedido do Átila, 13/10/2026)
A mesma janela do SSEG.exe do quartel no navegador do celular: o PC faz todo o trabalho (Claude, SOL no Chrome, pastas, plantas), o celular é mais uma tela com toque. Uso: no quartel, ou com o PC do quartel ligado analisando.
- [x] Fase 1 (2.1.4; 2.1.5 corrige a janela do PC, que se achava no celular porque o pywebview também serve por http://127.0.0.1 — a marca agora vem só do espelho.py):
  - o SSEG.exe serve `web/` em 127.0.0.1 (`espelho.py`), com o mesmo `Api` da janela;
  - entra só quem abriu o endereço com a chave gerada no PC (cookie), e os POST exigem o cabeçalho `X-SSEG`;
  - o que o Python empurra para a janela (chat, log) vai também ao navegador por SSE;
  - o chat que começou numa tela aparece na outra (`chat_historico`, evento `eu`);
  - abaixo de 700 px: a janela do processo vira abas (Conversa, Checklist, CIA), o menu fica por cima e os campos têm 16 px (sem o zoom do iPhone);
  - o liga/desliga fica em Configuração → Usar pelo celular, desligado por padrão;
  - escolher pasta, print da janela e atualizar o programa só funcionam na janela do PC;
  - o CI fotografa a página a 500 px, o mínimo do Edge sem janela (`celular-*.png`); conferido também como iPhone 13 (390 px) no servidor.
- [ ] Teste no PC: ligar, "Abrir no navegador deste PC", estreitar a janela do navegador, mandar mensagem por uma tela e ver chegar na outra
- [x] Fase 2, lado do programa (2.1.6):
  - "Usar pelo celular" também abre `ssh -N -R 127.0.0.1:8765:127.0.0.1:8765 sseg-servidor` (`espelho.Tunel`); se cair, tenta de novo a cada 20 s, e fecha junto com a janela;
  - pergunta uma vez ao servidor o endereço `https://….ts.net` (`tailscale status --json`) e mostra o link com a chave e o QR code (qrcode-generator, MIT, em `web/qrcode.js`);
  - mostra o estado do túnel: ativo, conectando, caiu ou porta presa a outro PC.
- [ ] Fase 2, lado do servidor e do celular (o Átila, pelo Claude do PC, 13/10/2026): Tailscale no iPhone e no servidor, na mesma conta; `sudo tailscale serve --bg --https=443 http://127.0.0.1:8765`
- [x] Lado do servidor pronto (13/10/2026): Tailscale no servidor (`carpes-24-7`) e no iPhone; `tailscale serve` publica a 8765 só na tailnet
- [x] 2.1.7, correções do primeiro uso no iPhone (relatadas pela sessão do PC):
  - indicadores quebram em linha e ficam menores;
  - os botões do processo quebram em linha, com rótulos curtos ("SOL: licenciamento", "SOL: análise", "laudo");
  - somem no celular a Nova versão, o "abrir pasta" e o ⋯, porque atualizar o programa derruba o próprio túnel e os outros agem só no PC;
  - o campo de mensagem não fala mais de Ctrl+Enter
- [x] 2.1.8, falar em vez de digitar (pedido do Átila, 13/10/2026):
  - 🎤 ao lado do Enviar, com o reconhecimento de voz do navegador (Safari no iPhone, só em https — o endereço do Tailscale é), em pt-BR;
  - o texto entra no campo e não vai sozinho, porque nome de norma ditado sai torto;
  - Enviar para de ouvir, e o ditado atrasado não volta ao campo;
  - o botão só aparece onde o navegador tem reconhecimento de voz. O teclado do iPhone já tinha o próprio microfone
- [x] 2.1.9: o celular recarrega sozinho quando o PC volta numa versão nova, já que atualizar fecha e reabre o SSEG.exe e a conexão de eventos cai e volta. Endereço: https://carpes-24-7.tailb70285.ts.net (a chave só na primeira vez; depois fica o cookie de 1 ano)
- [x] 2.1.10, do primeiro uso real no iPhone (13/10/2026):
  - aviso que aparece e some, para todo erro e, no celular, para cada mensagem do programa. O rodapé com Detalhes fica escondido no celular e as recusas não davam retorno;
  - "✓ O PC voltou atualizado" depois de o celular recarregar sozinho;
  - espelho: lê o corpo do POST antes de responder. Recusado sem ler, o corpo sobrava na conexão e o pedido seguinte chegava como "[]GET";
  - o programa só anuncia a versão já publicada (releases/latest), não o VERSION do main, que muda uns 10 min antes de o .exe sair
- [x] 2.1.11: botão ↻ no topo, só no celular, e "Recarregar" dentro do aviso de sem conexão. No navegador do app no iPhone não dá para puxar para recarregar (pedido do Átila pela sessão do PC)
- [ ] Teste de ponta a ponta: SSEG.exe do quartel ligado → QR → iPhone no 4G
- [ ] Notas da fase 2 (o desenho original): O PC do quartel fica na rede do governo e o celular no 4G, então eles não se enxergam direto:
  - o SSEG.exe abre `ssh -N -R 127.0.0.1:8765:127.0.0.1:8765 sseg-servidor` (conexão de saída, a mesma do sincronizar; nenhuma porta aberta no PC);
  - o celular chega ao servidor pelo Tailscale (servidor e celular; nada no PC);
  - o Átila instala o Tailscale no servidor pelo terminal, porque é mudança de rede;
  - ícone na tela de início do celular e aviso "PC do quartel desligado ou SSEG fechado";
  - Wi-Fi do quartel na mesma rede do PC: só se a rede deixar, sem contar com isso.
- [ ] No celular, o [PDF] da busca e "abrir pasta" agem no PC. Avaliar mandar o PDF da norma ao celular (é público) e esconder o "abrir pasta"

#### 2.5 — Quadro da semana (pedido do Átila, 13/10/2026)
A ideia vem do Kanban do jotaw1 (fork em github.com/atilacarpes96/kanban-teste-compartilhado): cards
coloridos no topo que contam e filtram, e um quadro de tarefas da semana. Só a ideia vem de lá: o código
é do SSEG, na mesma página e no mesmo `api.py`, sem um segundo servidor.

Fase A — cards no topo do Início (2.1.12)
- [x] Situação do processo no `analise.json`: em análise, aguardando ou fechado, mais o prazo e a data da CT (`analise_registro.situacao`). Fechar grava a data; reabrir apaga
- [x] Seletor na faixa da janela do processo (situação, prazo e CT), que aparece também no celular
- [x] `processos()` devolve situação, prazo, CT e data de fechamento, lidos do `analise.json`
- [x] Cards: Em análise (laranja), Aguardando (azul), Prazo em 7 dias (vermelho), CT marcadas (roxo), Fechados em 7 dias (verde) e Meta da semana. O clique filtra a tabela e o ✕ tira o filtro
- [x] Tabela de processos com a situação na cor do card, o prazo e a CT
- [x] Meta da semana editável pelo próprio card (`meta_semana` na configuração, padrão 10)
- [x] `testar.py`: situação grava e lê; fechar grava a data; reabrir apaga; valor inválido é recusado
- [x] Pasta sem situação marcada e parada há mais de 30 dias aparece como "Parado?" e fica fora dos cards, para as pastas antigas não inflarem o "Em análise"
- [ ] Teste do Átila no PC e no celular: marcar a situação em 2 ou 3 processos reais e conferir os números

Fase A2 — caixa do analista pela planilha e cards editáveis (2.1.13, pedido do Átila em 13/10/2026)
- [x] `scripts/distribuicao.py`: aba ANÁLISE da "Distribuição Análise" (xlsx que a rotina já baixa, lido só com a biblioteca padrão) → `<código>/distribuicao.json` com protocolo, distribuição, conclusão, CIA/CA, tipo, ocupação e área. Cria a pasta do que está na fila ou na caixa e do concluído nos últimos 30 dias
- [x] Estados: **na fila** (atribuído, sem distribuição: o prazo não corre), **na caixa** (prazo de 10 dias corridos da distribuição), **concluído** (CIA ou CA, saiu da caixa). A planilha manda; o marcado à mão na janela do processo só vale para processo fora da planilha
- [x] Janela do processo: da planilha só mostra (distribuído, vence); fora dela, distribuído, concluído, resultado e CT à mão. Saem o seletor e o prazo manual da 2.1.12
- [x] Cards padrão: Na caixa, Vencem em 3 dias, Na fila, Aguardando (CA/CIA), Analisados no prazo (verde), Fora do prazo, CT marcadas, Meta da semana
- [x] "+ card" e ✎ em cada card: nome, cor, regra (10 regras), N dias, meta; mover para a esquerda, excluir, voltar ao padrão. Guardados na configuração do PC (`cards`)
- [x] `testar.py`: leitura da aba ANÁLISE com xlsx de mentira, pastas criadas, regravação só quando muda, estado na caixa e campos manuais
- [x] Rotina do Painel do Dia no servidor: baixa a planilha todo dia útil e roda `distribuicao.py` em `~/SSEG/sseg/processos` (prompt em `~/rotinas/painel-do-dia/prompt.md`, fora do Git)
- [ ] Conferir no dia seguinte: `~/rotinas/logs/painel-do-dia.log` com a linha "distribuicao: …" e as pastas no servidor
- [ ] Teste do Átila: Sincronizar processos no PC → as pastas da fila e da caixa aparecem e os cards batem com a planilha
- [ ] Ordenar cards arrastando (hoje só "← Mover")

Fase B — tela Quadro (2.1.14)
- [x] Tela "Quadro" no menu, com as colunas A fazer, Fazendo, Esperando e Feito
- [x] Os processos entram sozinhos pela caixa: na fila em A fazer, na caixa em Fazendo, concluídos nos últimos 7 dias em Feito; clicar abre o processo
- [x] Tarefas soltas em `quadro.json` na pasta dos processos, fora do Git (`scripts/quadro.py`): título, origem, checklist; a mesma pendência mandada de novo não duplica
- [x] `quadro.json` fica só no PC por enquanto (o Sincronizar processos leva só as pastas A000…)
- [x] Mover: arrastar no PC, ← e → no celular; ✎ edita título e checklist; ✕ exclui com "Desfazer" por 8 s
- [x] Build: `--hidden-import quadro`; o tour fotografa a tela Quadro; `testar.py` cobre o `quadro.py`

Fase B2 — analista e meta pela escala (2.1.15, pedido do Átila em 14/10/2026)
- [x] `scripts/escala.py`: planilha "Escala Análise" (aba por mês) → horas de cada analista por dia, da tabela de horas (a de códigos não é usada: folga, férias e licença já ficam com 0). Grava `~/sseg-escala/escala.json` no servidor, fora do Git (tem nome de militar)
- [x] Rotina do Painel do Dia baixa a escala todo dia útil e roda `escala.py` (prompt em `~/rotinas/painel-do-dia/prompt.md`; cópia anterior em `prompt-antes-escala.md`)
- [x] Analista do PC: "Quem é você?" na primeira abertura (nomes da escala, ou digitado) e seção "Analista" em Configuração. Sem senha: o PC já tem o login do Windows
- [x] Meta da semana = horas de seg. a dom. ÷ 6 (período), meio arredonda para cima, × 2 PPCI por período (ajustável no ✎ do card). Sem escala, nome fora dela ou "Pela escala" desligado: a meta digitada
- [x] O app busca o `escala.json` pelo SSH (só se o PC tem o `sseg-servidor`), por trás, a cada 6 h; guarda ao lado da config
- [x] `testar.py`: horas tiradas da tabela certa, arredondamento, meta pela escala e as três voltas à meta manual
- [ ] Outros analistas: sem ligação com o servidor, a meta é a digitada. Decidir se eles usam o servidor ou se o app lê a planilha direto
- [ ] A caixa (distribuicao.py) ainda filtra "CARPES" fixo no servidor; com outro analista no servidor, passar o nome escolhido

Coluna da CIA com muitas exigências (2.1.16, pedido do Átila em 14/10/2026)
- [x] "▤ Compactar": uma linha por exigência (número, começo do texto, ✓ salva / rascunho / redigindo); clique abre só aquela, "fechar" volta
- [x] "Agrupar por medida" (ligado por padrão): mesma medida junta, na ordem das medidas do SOL, com contagem e salvas; o número continua o da CIA. Agrupado, some o ↑↓ (a ordem da CIA só muda desagrupado)
- [x] Preferência guardada no navegador (PC e celular, cada um a sua)
- [ ] Teste do Átila numa análise com muitas notificações

Chrome para o Claude (2.1.17, pedido do Átila em 14/10/2026)
- [x] Config → "Chrome para o Claude (opcional)": registra o Chrome DevTools MCP no Claude Code (`claude mcp add chrome-devtools-live --scope user -- npx -y chrome-devtools-mcp@latest --autoConnect`) e mostra item por item se funciona: Node 20.19+, Chrome 144+, registro em `~/.claude.json`, depuração remota ligada (DevToolsActivePort + porta atendendo)
- [x] Botões: Registrar, Abrir chrome://inspect (o Chrome não deixa outro programa ligar a depuração), Conferir, Testar conexão (sobe o servidor como o Claude faria e conta as abas; o Chrome pede "Permitir"; não lê título nem endereço) e Remover registro
- [x] Aviso na tela: ligado, o Claude enxerga todas as janelas do perfil do Chrome. A senha do SOL segue sendo do analista
- [ ] Teste do Átila: ligar a depuração, Registrar, Testar conexão e ler uma página do SOL pelo DOM
- [ ] Decidir se a skill sol-cbmrs-navegador passa a preferir o DevTools MCP (rede e console) ao Claude in Chrome

Pendências que sobram das conversas (pedido do Átila, 14/10/2026)
O checklist do plugin "assuntos" é por conversa. O que fica aberto quando ela acaba é pendência: o Claude sugere trabalho ou pessoal e o Átila confirma antes de enviar.
- [x] Trabalho vai ao Quadro do SSEG: `python sseg/scripts/quadro.py adicionar "<texto>" --origem "<conversa>"`
- [x] Pessoal vai ao Painel do Dia (versão 9, 14/10/2026): quadro "Pendências" (coleção `pendencias`) que não some no dia seguinte; "Agenda" cria evento de 30 min pelo conector Google Calendar (só `create_event` liberado à página); "Lembrete", só no iPhone, abre o Atalho "Pendência para Lembrete"; "Feito" tira da lista
- [ ] Átila cria no iPhone o Atalho "Pendência para Lembrete" (Receber texto da Folha de Compartilhamento/entrada → Adicionar Lembrete com o texto) e testa o botão
- [ ] Testar o botão "Agenda" (primeira vez pede permissão do Google Agenda à página)
- [ ] Plugin "assuntos": cada item aberto com trabalho ou pessoal; comando /pendencias mostra a lista para confirmar e o Claude envia (esperar a outra sessão, que mexe no mesmo plugin, terminar)
- [x] Regra no CLAUDE.md global (~/.claude/CLAUDE.md, fora do Git): sugerir trabalho ou pessoal e enviar só depois da confirmação

Fase C — a decidir depois da B
- [ ] Cards próprios ("+ Novo card": nome, cor e filtro)
- [ ] Tarefa com data vai ao Google Agenda
- [ ] Uma frase ditada no 🎤 vira tarefa ("sexta 14h fiscalização na escola X"), interpretada por script, sem IA
- Descartado do Kanban: acesso por Cloudflare com senha (o espelho com Tailscale já faz isso) e as abas E-mails, Reuniões e Log de campanhas (fluxo de agência)

### 2.2 — Vários analistas no servidor (pedido do Átila, 15/10/2026; ordem: multiusuário → instalador → GitHub → convite ao Serafim)

Cada analista entra no servidor com a chave do próprio PC e só vê os processos dele. O analista não ganha
shell: a chave dele só roda a `scripts/porta.py`.

- [x] `scripts/porta.py`: porta única do servidor. Admin (chave sem restrição) = `admin` de `~/sseg-acesso/analistas.json` (fora do Git); analista = linha `command="python3 SSEG/sseg/scripts/porta.py --analista '<nome>'",restrict` no `authorized_keys`, com o pedido do PC em `SSH_ORIGINAL_COMMAND`. Ações: quem-sou, listar/receber/entregar (filtradas), escala (só a linha dele), relato; do admin: analistas, autorizar, revogar, atribuir
- [x] Responsável pelo processo: `distribuicao.json` → `analista` (a planilha manda); senão `processos/.responsaveis.json` (quem mandou primeiro ou `atribuir`); senão o admin (pastas antigas). `distribuicao.json` nunca sobe do PC
- [x] `distribuicao.py` grava `analista` e, sem `--analista`, roda para o admin e todos os cadastrados (casa pela última palavra do nome da escala com a coluna ANALISTA). A rotina do Painel do Dia não muda
- [x] `sincronizar.py` fala com a porta (os nomes `remoto-*` valem nela); servidor ainda sem a porta → cai no `sincronizar.py remoto-*` antigo
- [x] SSEG.exe, Configuração → Servidor: "Pedir acesso" (cria `~/.ssh/sseg_servidor` e o apelido, copia o código `SSEG-ACESSO|<nome>|<chave pública>`), "Testar conexão" (quem-sou). Admin: lista dos analistas, "Retirar acesso" e "Liberar acesso" colando o código. Escala e Reportar bug passam pela porta (`app/acesso.py`)
- [x] `testar.py`: chave do analista só roda a porta; cada um lista/recebe/entrega só o seu; processo novo vira de quem mandou; recusas (nome fora do cadastro, ação de admin, chave inválida ou repetida); atribuir e revogar mantêm a linha do admin
- [x] Teste real no servidor (15/10/2026) com analista de teste: quem-sou, listar vazio, escala só dele, `cat ~/.ssh/authorized_keys` não roda (vira quem-sou), ação de admin recusada, túnel `-R` recusado, envio de processo novo aceito e o do admin recusado; depois revogado e o `authorized_keys` igual ao backup
- [x] Quem saiu da análise sai da escala: `~/sseg-escala/fora.txt` no servidor (um nome por linha, fora do Git), lido pelo `escala.py`. Em 15/10/2026: Sgt Amaral, Sgt Fernanda e Sd Bruna
- [x] Hook do banco (`sseg_hooks.py`): a resposta "deny" sai em UTF-8. No console cp1252 do Windows o "⚠️" quebrava o print e a trava deixava a alteração passar calada (era a falha "hook barra alteração de modelo do banco" do `testar.py`)
- [x] Todos os processos juntos (pedido do Átila, 15/10/2026): sem `--analista`, o `distribuicao.py` cria a pasta de TODOS os processos da planilha, de todos os analistas, uma por código. O `distribuicao.json` leva `analista` (nome da escala quando só um casa pela última palavra; senão, o da planilha), `analista_planilha` e `analistas_anteriores` (quem já passou: o processo troca de mãos e a pasta, com CIA e registro, vai inteira ao novo responsável). Caminho pronto para o entendimento coletivo por notificação: no servidor, um script cruza as CIAs de todas as pastas
- [x] `porta.py meus`: os códigos do responsável, um por linha. O Painel do Dia usa no lugar do `ls` da pasta, para não mostrar os processos dos outros
- [ ] Trocar no prompt do Painel do Dia (`~/rotinas/painel-do-dia/prompt.md`, passo 0d) o `ls .../processos/` por `python3 .../porta.py meus` (depois do pull no servidor)
- [x] **Instalador** (passo 2, 15/10/2026): o mesmo SSEG.exe do release. Aberto de fora da pasta de programas (Downloads), abre na tela **Instalação** (menu ☰): passos na ordem, cada um com ✓/✗ e o seu botão, e "Instalar tudo". 1) copia o .exe para `%LOCALAPPDATA%\Programs\SSEG\`, cria "SSEG" na Área de Trabalho e no Menu Iniciar e reabre de lá (`app/instalacao.py`, sem administrador); 2) Git, Python, Poppler e Claude Code; 3) entrar no Claude Code; 4) pastas; 5) quem é você; 6) servidor (opcional). Os ✗ seguem também nos alertas da barra de cima. A atualização automática troca o .exe onde ele estiver
- [x] 2.2.0 junta a 2.1.17, que não saiu: o build parou porque `VERSION` (2.1.17) não batia com a `VERSAO` do `sseg_app.py` (2.1.16)
- [x] 2.2.1: "Pedir acesso" copia uma mensagem pronta (pedido do Átila, 15/10/2026): o código SSEG-ACESSO e o comando `porta.py autorizar` com o JSON do analista, para colar na conversa do servidor 24/7 e o Claude de lá liberar. O "Liberar acesso" do programa aceita a mensagem inteira
- [x] 2.2.2 (pedido do Átila, 15/10/2026):
  - **Abertura de 22 s → 3 s:** com o espelho ligado, a mensagem "Espelho ligado" ia para a janela antes de a página existir, e o `evaluate_js` do pywebview esperava a página até 20 s. Agora o que sai antes de a página carregar fica guardado e vai quando ela carrega (`Api._antes_da_pagina`). `SSEG_TEMPOS=<arquivo>` anota o tempo de cada etapa da abertura
  - **Ordem dos cards:** arrastar no PC; no ✎, "← Mover" e "Mover →" (celular)
  - **Regras tiradas:** Aguardando, Saiu com CIA, Saiu com CA e Analisados no prazo. Card salvo com elas some sozinho
- [x] **2.3.0 — CT e recursos** (pedido do Átila, 15/10/2026): `scripts/ct_recursos.py` lê, no servidor, a aba Consulta Técnica de "CONSULTAS TÉCNICAS 6°BBM" e a aba Rec. Análise/Vistoria de "OFÍCIOS, INVIABILIDADES, RECURSOS E FACTs 6°BBM" e grava em cada `<código>/` o `ct.json` e o `recurso.json` com o que está aberto: estado "minuta" (o primeiro Finalizado depois do ME sem marcar) ou "chefia" (minuta finalizada, o último Finalizado da linha sem marcar). Todo finalizado sai; a pasta que tinha fica com `{"itens": []}` (apagar não desce ao PC). Analista pelo nome da escala; hora do Excel (0.375) vira 09:00
  - A porta mostra a pasta também a quem é ME de CT ou recurso aberto nela, mesmo com o processo de outro analista. `ct.json` e `recurso.json` nunca sobem do PC
  - Cards novos: "CT marcadas" (regra `ct`: minuta sem Finalizado, mais a CT marcada à mão), "CT com a chefia", "Recursos" e "Recursos com a chefia"; contam só os itens em que o ME é quem usa o PC. Etiquetas na tabela de processos
  - Rotina do Painel do Dia: as planilhas de CT e de ofícios passam a ser baixadas todo dia útil, e o passo 0d roda o `ct_recursos.py`
- [x] **2.3.0 — Quadro da seção** (pedido do Átila, 15/10/2026): `~/sseg-quadro/quadro.json` no servidor, pela porta (`quadro`, `quadro-mexer`). Cartão leva autor, quem pegou, "o que foi feito" e as datas de início (entrou em Fazendo) e fim (entrou em Feito). Todos criam e pegam; mover, editar e excluir só quem criou, quem pegou ou o admin. Na tela Quadro, a nova tarefa escolhe "Seção" ou "Só meu" (o só meu continua no `quadro.json` do PC)
- [x] **2.3.1 — CIA e chat** (pedido do Átila, 16/10/2026):
  - **Copiar por item:** botão "Copiar" em cada exigência (o texto da caixa, no formato do SOL: abre com quebra de linha) e "copiar a medida" no cabeçalho de cada medida, quando agrupado, com as exigências salvas juntas e a contagem contra os 2.000 caracteres — no SOL o lançamento é por medida
  - **Caixa da exigência do tamanho do texto**, sem barra de rolagem; a alça de altura saiu do canto da caixa e foi para baixo do item (duplo clique volta ao tamanho do texto). A altura puxada fica até fechar o processo
  - **Caixa do chat:** abre com 4 linhas, cresce com o texto até 60% da tela e a alça fica **em cima**, porque a caixa cresce para cima
- [x] **2.3.2 — mensagem do commit pronta** (pedido do Átila, 16/10/2026): a tela "Sincronizar com o GitHub" já abre com a mensagem montada pela lista (`git_sinc.sugerir_mensagem`): 1ª linha com as áreas (SSEG.exe com a versão, skill, PDF de norma, normas, scripts, workflow) e um arquivo por linha com novo/apagado/linhas +−. O que fica fora (✗) não entra. O analista confere e acrescenta o porquê
- [x] **2.3.3** (16/10/2026): o build da 2.3.1 e da 2.3.2 falhou na foto da janela — o ResizeObserver das caixas mexia na altura dentro do próprio callback e o Chromium soltava "ResizeObserver loop completed with undelivered notifications", que a foto conta como erro de JS. Agora a altura muda no quadro seguinte (requestAnimationFrame). Na tela Sincronizar, PDF novo em `normas/pdf/` com o mesmo conteúdo de um já versionado sai com ✗ e o nome do outro
- [x] **2.3.4 — chip do Servidor confere de verdade** (pedido do Átila, 16/10/2026: estava verde com processo novo na caixa, porque só olhava se o PC tinha a chave SSH). Ao abrir, a cada 10 min e depois de sincronizar, roda o plano da sincronização (`servidor_conferir` → `sseg.py sincronizar --json`, só leitura, **script, sem Claude**). Verde = iguais; amarelo com número = algo a baixar/enviar/escolher (o número é de processos novos na caixa, se houver; o resto vai no texto ao passar o mouse); vermelho = servidor não respondeu
- [x] **2.3.5** (pedido do Átila, 16/10/2026): "Licenciamento no SOL" e "Análise técnica no SOL" viram link direto para o navegador padrão; não mandam mais pedido ao chat para o Claude abrir pela aba do grupo dele. No espelho, abrem no celular
- [x] **2.3.6 — todos os chips conferem se funcionam** (pedido do Átila, 16/10/2026), por script, sem Claude, ao abrir, a cada 10 min e quando a janela volta ao foco (no máximo 1 vez por minuto). **Programas:** além de achar o executável, roda cada um (`git --version`, `python -c`, `pdftoppm -v` — o Xpdf do Git não passa — e `claude auth status`). **Pastas:** o clone tem `sseg/scripts/sseg.py` e a pasta dos processos aceita gravar (arquivo de teste criado e apagado). **GitHub:** já fazia `fetch`; pendência passa a amarelo, vermelho só se não falou com o GitHub. Ao passar o mouse, cada chip diz o que conferiu e a hora
- [x] **2.3.7 — tela inicial** (pedido do Átila, 16/10/2026): processos em andamento na ordem caixa (há mais dias no topo, pelo distribuído) → saíram com CIA → saíram com CA (os dois pelo mais recente) → o resto; "Iniciar conversa" desce para baixo da tabela, marcada "em revisão e teste"
- [x] **2.3.8** (pedido do Átila, 16/10/2026: "é tudo para facilitar, e não para criar mais camadas"):
  - **Tabela do Início como a caixa do SOL:** colunas Razão social, Ocupação predominante e Área; a caixa ordenada pelos dias em análise do SOL (tag "N dias no SOL", vermelha acima de 30). Fonte: `<código>/sol-caixa.json`, gravado pelo `sol_caixa.py` no servidor a cada leitura; sem ele, o api-<ID>.json e a planilha
  - **Checklist ligado aos scripts:** passo 3 marcado sozinho quando o JSON do SOL está na pasta, passo 4 quando há `pre-analise.txt` mais novo que o JSON (tag "auto", caixa travada). Bloco "Pré-análise documental" com os pontos marcados, "ver tudo" e "Mandar ao Claude" (a conversa segue dela, sem refazer o check)
  - "Análise técnica no SOL" abre direto no processo quando a caixa do SOL deu o idAnalise
- [x] **2.3.9** (16/10/2026): tabela do Início arrumada — razão social quebra em até 2 linhas, ocupação só a sigla (nome inteiro no title), tela inicial até 1.400 px de largura
- [x] **2.3.10** (pedido do Átila, 16/10/2026):
  - **Navegador:** o chat do processo e o subagente sol-leitor usam o Chrome DevTools MCP (`chrome-devtools-live`, todas as abas do Chrome do analista) em vez do Claude in Chrome e do grupo de abas; o chat sobe sem `--chrome`. Só leitura (sem click/fill no chat)
  - **Pendências:** respondida no chat (ou pelo "Mandar respostas" do checklist) = resolvida, sai do topo; as resolvidas ficam recolhidas ("N resolvida(s)", com "reabrir"). Comando novo `sseg.py analise resolver p2 p3` para o Claude fechar as dele
  - **Checklist se atualiza sozinho:** a leitura de 2 s pulava sempre que o cursor estava numa caixa de texto — e o cursor fica na caixa do chat. Agora só pula com o cursor dentro do checklist ou da CIA. O Claude é instruído a marcar o passo assim que ele estiver feito
- [x] **2.3.11** (pedido do Átila, 16/10/2026): passo do checklist e pendência só marcam no quadradinho (a linha era um `<label>`: clique fora do texto, na altura do passo, marcava sem o analista ver e pulava etapa). Quadradinho um pouco maior
- [x] **2.3.12** (pedido do Átila, 16/10/2026: o Claude ainda criava grupo de abas e pedia "Permitir" a cada ação): o chat sobe com `--no-chrome` e `--disallowedTools mcp__claude-in-chrome` — o plugin não existe mais nessa janela, nem para os subagentes; só o DevTools MCP
- [ ] Teste do Átila: baixar o SSEG.exe do release num PC sem SSEG (ou numa conta nova do Windows) e seguir a tela Instalação
- [ ] Publicar: push → `git pull` no servidor ANTES de soltar o .exe novo (o programa avisa "servidor sem a porta" se faltar)
- [ ] Espelho no celular para analista: porta própria por analista (`permitlisten`) e `tailscale serve` de cada uma — depois
- [ ] Quadro (`quadro.json`) e a caixa do SOL (`sol_caixa.py`) por analista — depois

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
