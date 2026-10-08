---
name: plano-servidor-24-7
description: Plano de teste (04/10/2026) para rodar o SSEG num servidor sempre ligado — Oracle Cloud Always Free com Claude Code, arquivos e rotinas; o SOL continua aberto no Windows do trabalho — e os critérios para decidir depois de um mês
sources: [claude-code]
---

# Servidor 24/7 para o SSEG — plano de teste

> **Status (05/10/2026): A1 em produção, Micro de reserva.** A A1.Flex `carpes-24-7`
> (2 OCPU/12 GB, ARM, IP 163.176.190.159) saiu às 08h01 pelo `criar_vm_oracle.py` e foi
> montada no mesmo dia: clone em `~/SSEG` com deploy key própria (`servidor-oracle-a1`),
> Claude Code logado pela assinatura com os conectores do claude.ai (Gmail, Agenda, Drive,
> Docs), `~/rotinas` copiado da Micro, crontab dos dois painéis, sessão tmux `sseg` com
> `--remote-control`. A **AMD Micro** `carpes-24-7-micro` (168.75.105.200) fica ligada de
> reserva, com o crontab apagado para os painéis não rodarem em dobro. Não apagar sem
> decisão do Átila. Teste nº 1 (navegador do SOL) ainda não feito; falta migrar
> `print ppci` e `sseg/processos/` do PC do serviço (passo 7).
>
> **Decisão de 05/10/2026:** a A1 é a principal e única ativa; a Micro fica **desligada** (só
> liga se a A1 falhar, e então `git pull` + conferir o crontab antes). Nunca apagar a A1
> (ARM grátis pode não voltar). Automático em `~/rotinas` (fora do Git): `subir-sessao.sh`
> (`@reboot` religa o tmux `sseg`) e `verificar.sh` (domingo 20h, e também quando uma rotina
> falha em `rodar.sh`): confere tmux, Claude, crontab, disco, memória, repo, falhas e backup;
> resultado em `~/rotinas/logs/verificar.log` (última linha OK ou PROBLEMAS). Backup semanal
> de `~/rotinas` + config do Claude em `~/rotinas/backups/` (guarda 4, só local).
>
> Ideia vinda do vídeo "Como Eu Deixo o Claude Code
> Programando 24/7 sem Pagar por Token" (Carol Tequita, VPS + tmux + Remote Control).
> Versão revisada em 04/10/2026: o SOL fica no Windows do trabalho, não no servidor.

## Por que

1. **Um lugar só.** Hoje o trabalho vive em quatro: PC de casa (clone), PC do serviço
   (`print ppci`, `sseg/processos/`), projeto do Cowork e GitHub. O vaivém de push/pull já
   deixou o clone 3 commits atrás (24/09) e 4 atrás (04/10). No servidor existe uma cópia
   viva; o GitHub vira backup.
2. **Rotinas sem PC ligado.** Preparar a fila e ler os PDFs antes do expediente.
3. **Acesso de qualquer lugar.** Do serviço, de casa ou do celular, pelo app do Claude.

**O que não muda:** a cota. O servidor usa a mesma assinatura Pro. Economia continua vindo
da auditoria de 30/09–03/10 (uma conversa por processo, subagente Haiku, texto do SOL em vez
de screenshot).

## Divisão de papéis

| onde | o que fica lá |
|---|---|
| **Servidor** | clone do SSEG, `sseg/processos/` (fora do Git) com memorial, JSON e CIA de cada processo — **sem plantas**, skills, subagentes, Claude Code, rotinas agendadas |
| **Windows do trabalho** | app do Claude, conversa **Local** de cada processo, `print ppci` com as plantas da hora e o navegador logado no SOL (Claude in Chrome ou navegador integrado) |
| **Casa / celular** | acesso à mesma sessão pelo app do Claude (Remote Control ou SSH) |

Vantagens sobre pôr o SOL no servidor: o acesso ao SOL continua saindo da rede do trabalho
(sem risco de bloqueio a IP de data center), a skill `sol-cbmrs-navegador` não troca de
ferramenta, e o servidor dispensa área de trabalho remota, Chromium e Playwright.

## Ligação entre o servidor e o navegador do trabalho

As ferramentas de navegador funcionam na máquina onde o app do Claude está aberto. Uma
conversa que roda no servidor e é só acompanhada pelo Remote Control **não** alcança o
navegador do trabalho. Dois caminhos, testados nesta ordem:

1. **App do Claude no trabalho em sessão remota por SSH.** A conversa e os arquivos ficam no
   servidor; o app continua no Windows. **Teste nº 1 do plano:** confirmar que, nesse modo,
   o navegador integrado e o Claude in Chrome continuam disponíveis para a conversa. Se sim,
   é o arranjo final.
2. **Se não:** divisão de tarefas. Uma conversa no trabalho roda o `sol-leitor` (Haiku 5.5) e
   grava o resumo do SOL direto na pasta do processo no servidor (por SSH); a análise roda
   no servidor lendo esse resumo. Lançamento no SOL, quando pedido, volta a ser pela
   conversa do trabalho.

### Como fica o dia a dia (decisão do Átila, 08/10/2026)

O caminho 2 virou o arranjo, sem esperar o teste nº 1:

- **Processo no trabalho:** app do Claude → Novo → **Local** → pasta do SSEG, Sonnet 5.5 alto,
  uma conversa por processo (é o "novo chat" do Cowork). Arquivos do SOL e Chrome logado estão
  no PC, então os três subagentes funcionam ali, `sol-leitor` incluído.
- **Ao abrir e ao arquivar o processo:** `sseg.py enviar` leva JSON da API, `<N>.pdf`, CIA e
  memorial para `~/SSEG/sseg/processos/<código>/` no servidor, por SSH (passo na
  `ppci-analise-processo`). **Planta não vai:** só serve na hora e o SOL guarda o original; o
  Átila apaga do PC depois.
- **Servidor ("Oraculo 23-7", Remote Control):** painéis, rotinas, verificação, pedidos do
  "Mudar o painel", e conversas de casa ou do celular — pergunta de norma, notificação avulsa
  e continuação de processo já enviado. No servidor rodam `localizador-normas` e
  `revisor-cia`; `sol-leitor` não (sem Chrome nem login).
- **Leitura autônoma do SOL pelo servidor** continua fora: pede o login do SOE no servidor e
  só entra com autorização expressa e consulta à chefia/PROCERGS (barrado em 06/10/2026).
- Sessão nova no servidor pelo app: hoje o tmux roda `claude --remote-control`, que é uma
  sessão só. Para o botão "Novo" abrir conversa no servidor, trocar por
  `claude remote-control --spawn same-dir` (encerra a sessão em curso; fazer com o Átila).

## A máquina: Oracle Cloud Always Free

| item | valor |
|---|---|
| tipo | VM.Standard.A1.Flex (ARM Ampere) — até 4 OCPU e 24 GB de RAM grátis; 2 OCPU / 12 GB bastam sem navegador |
| disco | até 200 GB grátis |
| sistema | Ubuntu 24.04 (ARM64), sem interface gráfica |
| região | São Paulo ou Vinhedo — **escolhida no cadastro e não muda depois** |
| custo | zero; o cadastro pede cartão só para verificação |

Cuidados:
- A ARM grátis às vezes fica "sem capacidade" na região: tentar de novo em outro horário.
- A Oracle pode recolher máquina grátis ociosa. Rotina diária afasta isso; converter a conta
  para "Pay As You Go" (continua grátis dentro do limite) elimina o risco.

## Montagem (o Claude faz, com o Átila nos passos marcados 👤)

1. 👤 Criar a conta Oracle Cloud e a VM A1, guardar a chave SSH.
2. Atualizar o sistema; firewall só com SSH, por chave.
3. Python 3.12, Poppler (`pdftotext`), Git; clone do SSEG com chave de deploy só deste repo.
4. Claude Code (instalador nativo, tem versão Linux ARM64); 👤 login pela **assinatura**, não
   por API (o link abre no navegador do Átila e o código volta para o terminal).
5. Sessão fixa: `tmux new -s sseg` → `claude` dentro do clone → `/remote-control`.
6. 👤 No Windows do trabalho: chave SSH do trabalho autorizada no servidor, apelido
   `sseg-servidor` no `~/.ssh/config` e teste `ssh sseg-servidor echo ok` (a rede do
   trabalho precisa liberar SSH de saída). Basta para o `sseg.py enviar`; sessão do app por
   SSH deixou de ser necessária (08/10/2026).
7. Levar ao servidor os processos em andamento com `sseg.py enviar`, pasta por pasta (planta
   fica no PC); o original no PC só sai depois de conferido.
8. Rotinas: `cron` chamando `claude --bg` (sessão em segundo plano) no clone. Feito em
   05/10/2026 para os dois painéis (ver "Rotinas em funcionamento").

## Rotinas em funcionamento (06/10/2026)

| rotina | quando | o que faz |
|---|---|---|
| Painel SSEG | todo dia, 6h30 | o script `preparar.sh` faz o trabalho pesado: `git pull`, aplica os pedidos da fila do painel (`sseg/scripts/painel_pedidos.py`, com commit e push) e gera o retrato do repositório (`sseg/scripts/painel.py`). O modelo (Sonnet, ~30 s) só lê a fila e grava o retrato no banco do painel quando ele mudou. Pedido "livre" fica para uma conversa |
| Painel do Dia | dias úteis, 7h47 | agenda, Gmail e Drive pelos conectores, as planilhas da SSEG (`planilhas.py`), os processos em andamento em `sseg/processos/` e o resumo da última verificação do servidor; grava só no banco do painel. Substitui a rotina da nuvem de mesmo nome, desligada em 05/10/2026 |
| Verificação | domingo, 20h, e quando uma rotina falha | `verificar.sh`, sem modelo: sessão tmux, crontab, disco, memória, repo em dia, falhas das rotinas (falha já explicada vai para `logs/reconhecidas.txt` e sai do alarme), skills da conta iguais às do repositório e backup. O resumo vai para o Painel do Dia, que só mostra algo quando há problema |

- Por que `--bg` e não `claude -p`: testado em 05/10/2026, o modo `-p` tem os conectores
  (Gmail, Agenda, Drive), mas **não** as ferramentas dos artifacts (`Artifact`, `ArtifactData`).
  A sessão em segundo plano tem as duas.
- Os prompts, o `rodar.sh` e os logs ficam em `~/rotinas/` no servidor, **fora do repositório**:
  levam endereço dos painéis e dados pessoais da agenda, e o repo é público. Cada execução
  grava uma linha de fim em `~/rotinas/logs/<rotina>.log`; sem essa linha em 30 min, o script
  encerra a sessão e registra as últimas linhas do log.
- O Painel SSEG é compartilhado por link: a rotina dele nunca põe código de processo, nome de
  proprietário ou RT na página. Dado de processo só vai para o Painel do Dia, que é privado.
- Continuam na nuvem, sem pasta: "Escala na agenda" (domingo, 18h) e "Resumo semanal"
  (sexta, 16h).

## Rotinas propostas

| rotina | quando | entrega |
|---|---|---|
| Preparar a fila | dias úteis, 6h30 | lê a planilha de distribuição, cria `<N>.json` dos processos novos |
| Ler os PDFs | logo depois | texto extraído de cada PDF já no servidor, pronto para a análise |
| Manutenção | domingo | norma nova a incorporar (skills da conta x repositório já entrou na Verificação) |

A **triagem da caixa do SOL** não roda sozinha nesta versão, porque o navegador logado fica
no trabalho: vira o primeiro passo da primeira conversa do dia (`ppci-abertura-sessao`).
Regras que valem para as rotinas: nada é lançado no SOL; nenhuma rotina faz login em nada.

**Consulta ao SOL sem o navegador do analista: para o futuro (decisão de 06/10/2026).** Por ora
vale o caminho do navegador logado (`sol-cbmrs-navegador`, subagente `sol-leitor`), que já tem
o fluxo pronto. Mais adiante, a ideia é um acesso só de consulta (licenciamentos, marcos,
recursos, FACT) para o Claude buscar contexto sem o Átila estar com o SOL aberto; lançamento de
análise fica de fora. Antes de implementar: autorização expressa do Átila, conferência com a
chefia ou a PROCERGS de que o acesso automatizado é permitido, senha sempre digitada pelo
Átila e nunca gravada, e revisão da regra acima. Em 06/10/2026 o modo automático do Claude Code
barrou as primeiras tentativas, por isso o tema só volta com essa autorização.
Onde chega o aviso de rotina concluída (arquivo no servidor, e-mail ou mensagem) se decide
no teste.

## O que muda no projeto

| peça | hoje | no servidor |
|---|---|---|
| ambiente | Cowork + Projects | Claude Code no servidor, aberto pelo app (SSH ou Remote Control) |
| navegador do SOL | Claude in Chrome / navegador integrado | o mesmo, no Windows do trabalho |
| arquivos do processo | `print ppci` no PC do serviço + `sseg/processos/` | `sseg/processos/` no servidor (fora do Git, como hoje) — `print ppci` migra para dentro |
| gravação | `device_commit_files`, `project_write` | gravação direta em disco — ajustar `ppci-analise-processo` e `pasta-print-ppci-local` |
| skills e subagentes | plugin da conta + backup em `sseg/skills/` | lidos direto do repositório (`.claude/agents/` já existe) |
| painel SSEG (artifact) | fila "pedidos" lida pelo Cowork | **a verificar:** se o Claude Code do servidor lê a fila; senão, os pedidos vão por mensagem |
| sincronização | push/pull entre máquinas | só o servidor faz commit; outras máquinas só leem |

## Riscos a medir no teste

1. **Navegador numa sessão por SSH** (teste nº 1). Define entre o caminho 1 e o 2 acima.
2. **Rede do trabalho permite SSH de saída** para o servidor. Se bloquear, sobra o Remote
   Control (que não alcança o navegador) e o caminho 2 por outra via de cópia.
3. **Dados de processo em servidor de terceiro.** Os arquivos já estão na nuvem do Cowork;
   avisar o 6º BBM é decisão do Átila.
4. **Latência** da sessão remota a partir do serviço.

## Critérios para decidir depois de um mês

Migrar de vez se: o navegador do trabalho funcionou com a conversa no servidor (caminho 1 ou
2); pelo menos 5 processos reais foram analisados por esse caminho sem voltar para o Cowork;
as rotinas da manhã entregaram na maioria dos dias; e não houve push/pull manual no período.

Voltar para o Cowork se a rede do trabalho bloquear o acesso ao servidor ou se o caminho 2
custar mais rodadas que o fluxo atual. Avaliar VPS paga só se a Oracle grátis falhar por
capacidade ou recolhimento.
