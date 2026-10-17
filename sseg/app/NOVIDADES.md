# Novidades do SSEG.exe

Cada versão tem uma seção `## <versão>`. O GitHub copia a seção da versão que está saindo para a
página da release (passo "Notas da release" do `.github/workflows/sseg-app.yml`). Escrever para o
analista: o que muda na tela e no dia a dia, sem nome de função.

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
