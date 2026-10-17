# Novidades do SSEG.exe

Cada versão tem uma seção `## <versão>`. O GitHub copia a seção da versão que está saindo para a
página da release (passo "Notas da release" do `.github/workflows/sseg-app.yml`). Escrever para o
analista: o que muda na tela e no dia a dia, sem nome de função.

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
