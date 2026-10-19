# Novidades do SSEG.exe

Cada versão tem uma seção `## <versão>`. O GitHub copia a seção da versão que está saindo para a
página da release (passo "Notas da release" do `.github/workflows/sseg-app.yml`). Escrever para o
analista: o que muda na tela e no dia a dia, sem nome de função.

## 2.6.1

- **Perguntas do Claude com botões.** Quando dá, a pergunta vem com **Sim / Não** (ou Ok / Não, CA / CIA). Você só clica: quando todas do bloco estão marcadas, a resposta vai sozinha e o Claude continua, sem digitar nem mandar.
- **"Conferir na planta" numa lista só.** O que é para você olhar na planta chega num bloco, um item por linha, em vez de uma pergunta por vez.
- **O Claude não pede mais licença para ler** (pasta, SOL, PDF de CIA ou de norma) nem para marcar passo: faz direto. Pergunta só o que é decisão sua ou o que só a planta mostra.
- **Conversa nova já começa sabendo o que a pasta tem.** O programa manda o resumo da pasta junto da primeira mensagem (você não vê): menos chamadas e nada de perguntar a data de protocolo que já está nos Marcos.
- **Salvar processo avisa das pendências abertas**: resolva todas de uma vez, salve assim ou volte.

## 2.6.0

- **Dois botões novos na janela do processo, para o fim da análise.**
  - **Guardar memorial** (antes de lançar a CIA): guarda o memorial como está no SOL agora (`memorial N.pdf`) e o JSON do licenciamento no mesmo instante (`licenciamento N.json`), no servidor e neste PC. É o que vai servir de comparação quando o RT entregar o projeto corrigido. Só lê o SOL.
  - **Salvar processo** (depois de emitir a CIA no SOL): baixa a CIA (`CIA N.pdf`), avisa se não há memorial guardado daquela análise e sincroniza com o servidor e com a pasta dos prints. Nunca sobrescreve uma CIA que você já guardou.
- Falta ainda o botão de **lançar a notificação no SOL** (preencher e parar antes de emitir): vem em outra versão.

## 2.5.7

- **Chat não sai mais com "O Claude Code saiu (código 1)".** Um processo analisado em outro PC guarda uma conversa que não existe neste;
  o chat tentava retomá-la a cada mensagem e falhava, sem ajuda do "tenta de novo". Agora avisa e começa uma conversa nova
  (análise, pendências e passos salvos continuam; só a memória da conversa antiga não vem).

## 2.5.6

- **De hora em hora o programa só traz; o envio é quando um processo termina.** A rodada horária traz as atualizações do GitHub e os arquivos novos do servidor.
  Quando um processo termina (CA ou CIA lançados, ou marcado como concluído), o programa envia sozinho: commit e push no GitHub (com as travas de sempre) e subida dos
  processos ao servidor. Sem janela; só o ponto do chip **Sistema** pulsa de leve. Se algo parar, o motivo fica no texto do chip.
- A primeira rodada horária vem 2 minutos depois de abrir o programa. Para desligar tudo: `"auto_sinc": false` no arquivo de configuração.

## 2.5.5

- (substituída pela 2.5.6) Sincronização automática de hora em hora, com envio junto.

## 2.5.4

- **Botão "Refazer pré-análise" na janela do processo.** Roda o script de pré-análise agora, neste PC, sem Claude (menos de um segundo) e atualiza a tela.
  Serve depois de pôr arquivos na pasta ou quando o aviso diz que o JSON do SOL mudou. Quando o processo ainda não tem pré-análise, o botão a cria.

## 2.5.3

- **Atualizar lê a caixa mesmo quando o programa ainda não sabe que você é administrador.** Antes, num PC onde o "Testar conexão" não tinha rodado,
  o botão só sincronizava e não relia a caixa do SOL; os lançados ficavam no topo.

## 2.5.2

- **Os chips do topo viraram um só.** O chip **Sistema** mostra o pior estado dos cinco (Programas, Pastas, Servidor, SOL e GitHub), com o número de pendências.
  Clique nele para abrir a lista e, em cada item, para abrir a janela de sempre. "Nova versão" continua à parte, porque pede uma ação sua.

## 2.5.1

- **Botão Atualizar no Início.** Lançou CA ou CIA no SOL? Clique em Atualizar: o programa lê a caixa do SOL de novo no servidor, baixa o que mudou
  e reordena a lista. Os processos lançados descem para depois da caixa, com o resultado (CA ou CIA), e o de cima ganha a etiqueta
  **Próximo**, o que tem mais dias em análise no SOL. Antes, o processo lançado ficava no topo até a próxima leitura automática.

## 2.5.0

- **Login do SOL pelo programa.** Em Configuração há um campo novo, "Login do SOL": você digita a matrícula e a senha uma vez e o
  programa grava nos dois lugares (neste PC, no cofre do Windows, e no servidor, para ele entrar sozinho quando a sessão cair).
  Também dá para trocar e apagar ali. A senha não passa pelo chat nem pelo GitHub.
- **Segundo computador do administrador.** No PC novo, "Pedir acesso" com o seu nome; no PC principal, "Liberar acesso" com o código.
  Antes o servidor recusava o nome do administrador.
- Saiu o ponto vermelho ao lado do nome SSEG no topo.
- **Instalação guiada, passo a passo.** A tela Instalação mostra uma barra de progresso e o passo de agora em destaque:
  - o programa faz sozinho o que dá (programa, Git, Python, Poppler, Node.js, Claude Code, pastas e a ligação do Chrome ao Claude), em sequência, com um clique;
  - depois de reabrir pelo instalador, ele continua sozinho;
  - o que depende de você (entrar no Claude, escolher seu nome, ligar a depuração do Chrome, servidor) aparece um de cada vez, com a instrução, e a tela avança sozinha quando você termina.
- **Node.js entra na instalação.** Antes ficava de fora e travava o "Chrome para o Claude"; agora é instalado e o `npx` já funciona sem reabrir o programa.
- **"SOL no servidor" sem conexão.** Quando o PC ainda não foi autorizado no servidor, a janela diz "Sem conexão com o servidor" em vez de "sem senha gravada".

## 2.4.0

- **Visual novo, sóbrio e atual.**
  - Fundo cinza-claro neutro, cartões brancos e texto escuro.
  - O vermelho do CBM fica só como destaque: marca, botão principal e item ativo do menu.
  - Títulos e cabeçalhos de tabela em letra normal, sem maiúsculas vermelhas.
  - Topo com linha fina; menu com o item ativo em destaque suave.
  - Cards da semana com um ponto de cor e o número grande.
  - Campos e botões arredondados; a linha da tabela realça com o mouse.
  - Modo escuro com a paleta nova.
- **Tabelas mais limpas.**
  - Razão social e endereço em letra menor, até 2 linhas, com o nome inteiro no mouse.
  - Cidade escrita normalmente ("Santa Cruz do Sul").
  - A etiqueta "4ª análise" não quebra mais para baixo do código.
  - Na aba Processos, clique no código para abrir no SOL. A tabela cabe na tela sem rolar para o lado.
- **Nome de guerra.** A última análise mostra "Sgt Brito" em vez do nome completo do SOL, também no filtro
  de analista e na cópia para planilha. Quem não é da seção continua com o nome completo.
- Explicações do topo de cada tela mais curtas.

## 2.3.23

- **Aba Processos com busca de verdade.** O "Mais filtros" abre, e os filtros se somam:
  - cidade, bairro e situação da edificação;
  - ocupação: grupo (J), divisão (J-3) ou CNAE em texto, com a opção de olhar só a predominante;
  - faixas de área, altura e população, e período de protocolo;
  - resultado da última análise (CA, CIA, sem análise) e o analista que a fez;
  - número de análises, responsável técnico, com recurso, mudou de situação e só os que têm pasta neste PC.

  A busca de texto passa a achar também nome fantasia, CNPJ, endereço, bairro e RT. Clique no título de
  uma coluna para ordenar. Ocupação e área viraram colunas. "Copiar para planilha" leva a lista filtrada
  inteira para colar no Google Planilhas ou no Excel. Os filtros ficam guardados neste PC.
- **Pré-análise de reanálise** (no servidor, sem trocar o programa):
  - vem primeiro o que interessa: as plantas novas e as substituídas, com o que foi notificado em cada uma;
  - a partir de agora, também o que mudou no cadastro e no campo 4 desde a análise anterior;
  - as conferências do processo inteiro ficam como observação.

  A 1ª análise continua com a conferência completa.
- **Correção no servidor:** quando um processo voltava à caixa para outra análise, ficava o JSON do SOL da
  análise anterior. Agora ele é baixado de novo, e o anterior fica guardado para a comparação.

## 2.3.22

Mudanças a partir da leitura das 4 análises de 16 e 17/10 (conversas guardadas no servidor):

- **O Claude da janela do processo pergunta menos e trava menos.** Ele recebe a lista dos comandos
  prontos, sem precisar rodar "--help" antes de cada um. Também é orientado a olhar primeiro o que a
  pasta já tem e a não improvisar comandos que pedem aprovação (era o que parava a janela).
- **Sem pergunta repetida:** a mesma dúvida, com outras palavras, não vira pendência de novo. A
  resposta vai para a que já existia.
- **Pré-análise com o cadastro do SOL:** ocupações (CNAE, carga, risco), área, alturas, pavimentos,
  população, riscos específicos e as plantas desta análise.
- **Tabela de exigências pronta no check:** a linha da tabela transcrita do PDF, célula a célula, com
  o texto das notas. Quando precisa ver a tabela, o Claude gera a imagem da página certa sozinho, sem
  sujar a pasta do processo e com o texto das normas com acento.
- **Reanálise:** o Claude confere a última CIA e o que mudou; assunto novo vai em "Observações", sem
  pergunta. A conclusão sai curta ("Pode aprovar (CA)"), e "deferir" fica só para recurso, laudo e CT.

## 2.3.21

- **Cor do prazo pelos dias na caixa:** verde até o 7º dia (o comum), laranja do 8º ao 10º e vermelho
  depois do 10º.

## 2.3.20

- **Prazo mais claro no Início.** "Na caixa · faltam 8" (8 dias, não 8 processos) virou
  "Prazo 25/10 · 8 dias". O prazo é o da seção: distribuído + 10 dias corridos. Os "dias no SOL" são
  contados pelo próprio SOL, por isso são outro número. O card diz "prazo mais próximo".

## 2.3.19

- **Número da análise na página do processo**, ao lado do código, como no Início. Vem da planilha de
  distribuição; quando o processo não está nela, vem dos Marcos do SOL. Nas duas telas aparece por
  extenso: "1ª análise", "2ª análise" (antes o Início mostrava "ANÁLISE", "2º").

## 2.3.18

- **Aba nova "Processos"**, com todos os processos do SOL da região (uns 6,8 mil). Dá para buscar por
  código, razão social, cidade ou analista, e filtrar por situação. Cada linha mostra a última análise
  (data, resultado e quem fez) e a data de protocolo. O botão "SOL" leva a aba do SOL em que você já
  entrou até o licenciamento.
- **"Mudaram de situação"**: os processos que mudaram desde a coleta anterior, por exemplo um
  notificado que voltou para análise.
- **Início só com os vivos.** Processo com alvará, extinto ou rascunho no SOL sai da lista (a não ser
  que esteja na sua caixa). Ele continua na aba Processos, e o aviso no título leva até lá.
- A base vem do servidor, que lê o SOL às 8h20, 12h20 e 16h20 nos dias úteis e confere tudo de novo
  a cada duas semanas.

## 2.3.17

- **Botões "SOL: análise" e "SOL: licenciamento" sem login de novo.** Antes abriam aba nova, e aba
  nova do SOL sempre pede login. Agora o programa leva a aba do SOL em que você já entrou direto
  para o processo. Na primeira vez o Chrome pergunta "Permitir": clique. Sem aba do SOL logada (ou
  sem a depuração remota ligada no Chrome), abre em aba nova, como antes, e avisa.
- **Chip "SOL" no topo:** mostra se o servidor está logado no SOL e até que horas, se o login
  automático está travado e quando a caixa foi lida. Clicando: o detalhe e, para o administrador,
  "Ler a caixa agora".
- **Mouse em cima de qualquer chip** mostra primeiro o que ele é e, embaixo, o estado de agora.
- No servidor (sem trocar o programa): as CIAs anteriores dos processos da caixa chegam baixadas e a
  pré-análise traz a última CIA; quando a sessão do SOL cai, o servidor entra sozinho de novo.

## 2.3.16

- O quadro "Pré-análise documental (script)" encolhe numa linha depois de "Mandar ao Claude" e
  reabre com um clique; volta aberto se a pré-análise for refeita. "recolher" encolhe sem mandar.
- O Claude não pede mais a imagem da tabela: quando a contagem de medidas for necessária, ele mesmo
  gera a imagem da página do PDF.
