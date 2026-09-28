---
name: casos-referencia
description: Lições anonimizadas das análises de PPCI já feitas — definidora, roteamento de tabelas, campos 3/4/5/6, laudo, decisões de "não notificar" e erros já cometidos. Ler antes de analisar um processo novo.
---

# Casos de referência — lições das análises anteriores

Lições tiradas dos registros de processo, **sem dado de cliente**: sem código de processo,
nome, endereço, CNPJ, RT ou id do SOL. Os registros completos ficam fora do repositório, na
pasta privada de cada analista (ver `CLAUDE.md`).

Cada caso vem identificado pelo **tipo** da edificação. Os números de área e população foram
arredondados ou omitidos quando não mudam a lição.

**Como usar:** estas lições mostram como a norma foi aplicada e o que o analista decidiu. Não
dispensam conferir o dispositivo no PDF oficial antes de citar em CIA (instruções do projeto).
Quando está marcado **⏳ provisório**, o item ainda não foi conferido no PDF.

---

## 1. Definidora (RT 01/2024, item 5.1.2)

**1.1 · Cinco predominantes, todas de grau médio (existente não regularizada, H≤6).**
C-2, D-1, J-3, F-8 e I-2, com I-2 declarada definidora. O critério (a) empata e vai para o (b):
6J.2 = **12**, 6C = 11, 6D = 11, 6F.3 = 10, 6I.1 = 10. **A definidora é a J-3, não a declarada.**
As 12 medidas da J-3 já estavam no campo 4, então a correção era só documental. Mesmo assim, foi
notificada e depois reiterada, com a contagem das tabelas no texto.
- Contagem: na 6C, Plano X⁸ ("somente C-3") sai e Detecção X⁹ ("depósitos > 750 m²") só entra
  se a área de depósito passar de 750 m². Na 6D, Plano X⁷ ("somente D-5") sai.
- ⚠️ Decisão do analista: **não invocar o 5.2.2.1** quando o J já está declarado predominante.
  Puxar o limiar dos 10% abriria porta para o RT reclassificar o depósito como subsidiário e
  derrubar a exigência.

**1.2 · Depósito J subsidiário acima de 10% da área total, sem isolamento.**
O J passa a predominante pelo **5.2.2.1** (sempre enunciar com a condição de 10% / 1.500 m²).
Com J-3 × D-1 empatados em risco médio, fica 6J.2 = 12 × 6D = 11, e a definidora é a J-3.
Notificação em duas partes: reclassificar o J com a carga, e trocar a definidora.

**1.3 · Uma única predominante de risco alto.** J-4 de 3.600 MJ/m², ou J-4 acima de 1.200 MJ/m²,
contra predominantes de risco médio: fecha no critério (a), sem contagem. Grau pela
**Tabela 3 do Anexo A do Decreto**: baixo até 300, médio de 300 a 1.200, alto acima de 1.200 MJ/m².

**1.4 · Empate total que não é pendência.**
- Três predominantes de risco médio na Tabela 5, todas com 5 medidas. A norma não tem terceiro
  critério, então a definidora declarada não se notifica, porque o campo 4 fecha igual.
- C-2 × D-1 com as mesmas 11 medidas na coluna 6<H≤12: empate inócuo. Só volta a importar com
  depósito > 750 m² em C-2 (nota 9 → Detecção), com edificação sem janelas (nota geral "c" da 6C)
  ou se a altura mudar de coluna.
- Uma G-2 de carga 200 perde no critério (a). Dúvida sobre o enquadramento dela no 5.2.3 não
  muda a definidora, **então não parar a análise por isso**.

**1.5 · Grupo M predominante (RT 01/2024, 5.1.2.4).** As medidas do M são individualizadas e o
5.1.2 não se aplica a ele.
- Subestação M-6 com D-1 em edificações isoladas no mesmo lote: M-6 pela **6M.6** (Térrea, 12
  medidas); as D-1 isoladas pela **Tabela 5**, coluna "A, D, E e G". Medidas a mais que as
  edificações adjacentes declaram não se notificam. Fundamento: **RT 01/2024, 4.8.5**.
- Revenda de GLP M-2 descoberta com atendimento coberto: o M-2 pela **6M.2**, coluna
  "Produtos acondicionados — gases até 24.960 kg", dá só as 4 básicas. Segurança Estrutural,
  CMAR e Iluminação são X², "apenas para instalações cobertas". A parte coberta (atendimento C-2)
  vai pela **Tabela 5**, coluna C, e é ela que exige a **Iluminação de Emergência**. A C-2 também
  precisa ser declarada no campo 3.

**1.6 · Ocupação única.** Nada para disputar: a definidora é ela.

## 2. Roteamento das tabelas (Anexo B do Decreto 51.803/2014)

- **Existente não regularizada (1997–2013) e "a construir"** vão pelo **Anexo B**. As dispensas
  5.4/5.5 da RT 05 P07 valem **só para regularizada**. Para não regularizada, a norma vigente
  na data do protocolo se aplica em cheio.
- **Tabela 5:** área ≤ 750 m² e H ≤ 12 m. A F-11 e a F-12 ficam na Tabela 5 até **1.500 m²**.
- A rota usa a **área a ser protegida** (RT 01/2024, 3.7). A **nota 7** da Tabela 5 (Plano de
  Emergência e Hidrantes para F-11/F-12 "acima de 750 m² até 1.500 m²") usa a **área total
  construída**. São duas portas diferentes. Caso real: 730 m² protegidos contra 749 m²
  construídos, com a CIA pedindo para computar áreas cobertas omitidas. Na análise seguinte,
  refazer a contagem antes de qualquer outra coisa.
- A regra de acesso de viaturas dos 20 m é nota das **Tabelas 6**, não da Tabela 5. Viaturas
  declaradas a mais em edificação da Tabela 5 não se notificam.
- **Característica construtiva Z** acrescenta **Controle de Fumaça (IT 15 CBPMESP)** ao campo 4.
  Isso apareceu em dois casos de depósito J predominante.
- G-5 (hangar): a Tabela 5 exige **Brigada** na coluna "A, D, E e G", sem nota restritiva. A
  nota geral "b" da Tabela 5 (drenagem para bacia de contenção à distância, proibição de
  líquidos combustíveis no hangar) é condição de projeto, não medida do campo 4.
- ⚠️ O `sseg.py check` já roteou F-12 de 515 m² para a coluna "Térrea" das Tabelas 6, e está
  errado: a tabela certa é a 5. Aviso do script sobre linha não conferida, nesse caso, não se
  aplica.

## 3. Campo 3 — dados gerais

- **Altura e pavimento de maior população (RT 02/2014, 4.20 e 4.30).**
  - Edificação térrea tem alturas 0 e pavimento de maior população **0/0**, porque o único
    pavimento é o de descarga. Isso está correto, **não notificar**. Quando vem preenchido,
    notificar (modelo do banco).
  - Dois pavimentos, **cada um com descarga própria**: alturas 0 e pavimento de maior população
    0 também estão corretos (confirmar isso com o analista).
  - 1 pavimento, sem subsolo e descendente 0, mas **ascendente 5,5 m** e pavimento de maior
    população preenchido: os dados são internamente inconsistentes. Notificado como **pedido de
    esclarecimento**, porque não se sabe qual dado está certo, e não como correção de um campo
    específico.
  - Altura do memorial divergente da do corte: notificar com cláusula de salvaguarda. Se a
    correção mudar a coluna de altura, refazer a contagem.
- **População do memorial × planta (RT 11 P01/2016, 5.3.6).** Rótulos da planta somando mais
  que o memorial, ou o memorial abaixo do cálculo correto da planta: compatibilizar.
  - Diferença de poucas pessoas em ambientes pequenos que não entram nos blocos do SOL é
    **limitação do SOL**. Não notificar.
  - Arredondamento de blocos do memorial (ex.: 353,73 → 354) também é limitação do SOL.
- **Residencial em edificação mista (RT 01/2024, 4.1 — conferido no PDF).**
  - O 4.1 inteiro é restrito ao **unifamiliar**. **4.1.1:** com acessos independentes para a via
    pública, a área não é computada e a residência não é analisada. **4.1.2:** sem esses acessos,
    fica **A-1** e a área é computada, mas as medidas vão **fora** da residência, que também não
    é analisada nem vistoriada.
  - Mais de uma unidade habitacional no pavimento é **A-2**. O 4.1 não alcança: as medidas
    passam a valer **dentro** da unidade, que é analisada e vistoriada.
  - Nota em prancha citando a RT 05 Parte 03/2025 (PSPCI, item 4.4.1) em processo de PPCI
    completo cita a norma errada. A de PPCI é a RT 01/2024, item 4.1.
- **Carga de incêndio em branco:** o SOL **só mostra o campo de carga em ocupação
  predominante**. Carga em branco de subsidiária não é pendência sozinha. Só entra se a ocupação
  for reclassificada como predominante.
- **Comprovante de existência (não regularizada):** ART anexada no lugar do comprovante não
  prova existência antes de 26/12/2013. Fundamento: RT 05 P07/2025, 6.2.2 (fotos, documentos
  históricos ou públicos).
- **Diferença mínima entre área construída e área a ser protegida** (0,10 m²) sem desconto
  justificado: não foi notificada.

## 4. Campo 4 — medidas e normas

- **Norma ABNT com RT específica vigente (RT 01/2024, 4.3.1 — conferido):** as normas da
  Tabela 2 valem "somente até a entrada em vigor de Resolução Técnica específica". Por isso
  NBR 12693, NBR 10898 e NBR 9077 no campo 4 estão desatualizadas: o correto é RT 14/2016,
  RT 13/2025 e RT 11 P01/2016. Os três textos lançados seguem o mesmo molde.
- **Hidrantes:** NBR 13714 ou RT 17 P01/2025 são as duas regulares até 31/12/2026. Houve um
  erro na base, já desfeito, que dava a RT 17 vigente desde 01/07/2026. Ele teria gerado
  notificação indevida. **Nunca notificar a NBR 13714 antes de 2027.**
  - Se o RT adotou a RT 17, os dispositivos dela valem. **5.2.1 "a"**: hidrante a até 5 m do
    acesso principal. **"b"**: a até 5 m dos acessos às escadas e rampas em todos os
    pavimentos. **"c"**: junto às portas externas, a critério do RT (não é exigência).
  - Reserva técnica pela RT 17, Tabela 1: Tipo 3, 20.001–50.000 m², 1.201–2.000 MJ/m² dá
    **100 m³**. A leitura da redução por chuveiros ("limitada a 25 m³", nota "a") **não foi
    decidida**.
- **Alarme (RT 18/2025, 8.1 "a"):** acionador a mais de 7 m do acesso principal deve ser
  notificado.
- **Extintores:**
  - Risco alto, classe A, com áreas sem cobertura de 15 m: RT 14, Tabela 1. O **5.4.1.14**
    (baterias) é faculdade e entra como sugestão.
  - Extintores sobre rodas em área de transformadores fundamentados na IT 25: fundamento
    errado. Para subestação, o correto é **IT 37, 4.4.2.1 e 4.4.2.4**, com RT 01/2024, 4.8.1 e
    RT 14.
- **Medida que falta:** vai em "Adicionar correções → Outros", com a tabela do Anexo B que a
  exige. Para medida que pode valer em duas colunas de altura, redigir sem altura nem coluna e
  citar as duas tabelas, para não depender da definidora.
- **Medida declarada a mais** (Detecção, Hidrante Urbano, Acesso de Viaturas): não se notifica,
  fica valendo para a vistoria.
- **Saídas — distâncias máximas (RT 11 P01, Tabela 3, notas conferidas):**
  - A **nota F** (140 m em área técnica) exige "locais destinados a equipamentos, sem permanência
    humana e de acesso restrito". Pavimento rotulado "área técnica" mas com ocupação e população
    não se enquadra.
  - Mudar a característica construtiva de Z para Y exige revisar as notas das pranchas que ainda
    dimensionam com +30%.
  - Garagem G-1/G-2 usa a nota N (50/45 m).
- **Saídas — outros:**
  - Porta automática não se submete ao 5.5.4.10 (porta de correr), pelo 5.5.5.1.
  - Escada em leque: 5.7.1.2.
  - Desnível em porta: 5.7.3.3.1 (banco).
  - Rampa de 20%: 5.6.3.1 com NBR 9050 6.6.2.1 (banco).
  - Cálculo populacional: circulação que não é corredor não se desconta (5.3.2, 5.3.4 a 5.3.6).
- **Sinalização de lotação máxima (F predominante):** RT 12/2021, 5.4.2.3.1 e 5.4.2.3.1.1.
  Placa em entrada da edificação foi aceita.

## 5. Laudo de inviabilidade e compensatórias

- A compensatória de laudo deferido **tem que estar representada em planta** e ter
  correspondência no campo 4 (brigadista extra, extintor sobre rodas em "Outras").
- **Compensatória vazia** ("limitação de população" sem número) quando o próprio laudo demonstra
  que as saídas já atendem: o analista decidiu **não notificar**, porque as saídas se sustentam
  pelo cálculo do laudo.
- **Nota de "medida compensatória" em planta sem laudo:** retirar. RT 05 P07, 5.6.1 e 5.6.2.
- Leitura do SOL: a inviabilidade fica em **`medidas[].inviabilidade`** (`NAO_POSSUI` /
  `POSSUI_PARCIAL`). A chave `inviabilidadeTecnica` não existe. Já houve erro de concluir "sem
  laudo" lendo a chave errada.

## 6. Campo 5 — riscos específicos

- **Vaso de pressão:**
  - Declarado e não representado em planta: RT 05 P1.1, **Tabela L.3, item 2 "a" e "b"**.
  - Representado mas sem extintor: tirar a alínea "a" e somar a **RT 01/2024, Tabela 3,
    item 4, nota 1** (extintor entre 3 m e 15 m).
  - Riscos específicos cotados entre 3 e 15 m resolvem.
- **Gerador:**
  - Não declarado: RT 05 P1.1, Tab. L.3, linha "Gerador de Energia Elétrica", e RT 05 P08, 5.5
    (simbologia e legenda).
  - Declarado e com extintor em planta: aprovado.
- **Subestação:**
  - Dados em branco: **RT 01/2024, 4.8.6.1** (tipo, tipo e volume de óleo de **todos** os
    transformadores).
  - Transformador externo acima de 20 m³: IT 37, 4.6.1. Com população fixa, admitem-se sistemas
    manuais e móveis (4.4.7.2, 4.4.9.4).
- **Câmaras frias / compressor de amônia ou fluido inflamável:** IN CBMRS 056/2024, arts. 4º a
  6º (banco).
- **Líquidos combustíveis e inflamáveis:**
  - IT 25 pela RT 01/2024, 4.5.1.
  - Com o I ou o J predominante e mais de **400 L**, é **local de elevado risco** (5.3.1 "a").
    Isso reduz a validade do APPCI para **2 anos** (LC 14.376/2013, art. 10).
  - Em ocupação mista, vale a predominante de menor validade (5.1.2.3).
- **Armazenamento a granel:** RT 01/2024, 4.11. Produto ensacado ou embalado fica fora. Silos e
  graneleiros vão pela RT 22.
- **Fotovoltaico:** RT 23 (Tabela 2 da RT 01/2024, item 18).
- **Observação não notificada:** pelo 4.8.1 e 4.8.2 da RT 01/2024, a 6M.6 vale para subestação
  e instalação de geração "independentemente da área". Sala de gerador ou subestação dentro de
  outra ocupação foi tratada só como risco específico, e a questão ficou em aberto.
- ⏳ Não há dispositivo expresso localizado que obrigue **declarar** risco específico no campo 5:
  a Tab. L.3 manda analisá-lo no memorial.

## 7. Campo 6 — elementos gráficos e ART

- **Só a coluna "A" da Tabela L.1** vai em planta (RTISOL 6.3.6.1.2). Iluminação e placas de
  equipamento em planta são para retirar. Exceções que a L.1 remete de volta: sinalização de
  orientação e salvamento, e iluminação de balizamento.
- **Arquivo errado no elemento** (planta baixa no lugar de corte, foto aérea no lugar de
  implantação): reapresentar, citando a alínea "c" ou "a" do 6.3.6.1.2.
- **Implantação:**
  - Representar todas as edificações do lote.
  - Com isolamento, linha de chamada e hachura vermelha (RTISOL 6.3.3.1; RT 01/2024, 4.3.9 e
    5.1.3).
  - Sem isolamento, cobrir todas as áreas com todas as medidas.
  - Situação e implantação em elemento único: 6.3.6.1.2 "a" e 6.3.6.1.2.1.
- **ART:**
  - Divergência de área não é item de conferência da ART. Vai como **"Sugiro verificar"** no
    campo do RT, sem norma, e a exigência real vai no elemento Implantação.
  - Assinatura do proprietário ou responsável pelo uso e do RT: RTISOL 6.3.6.1.1.5.
  - Documentos de legitimidade de quem assina pela PJ: 6.3.6.1.3.2.
- **Remissão entre campos:** "conforme inconformidade citada no campo X" tem que apontar o campo
  certo. Já saiu "campo 3" para exigência que estava no campo 4.

## 8. Operação do SOL — erros que já aconteceram

- As opções pré-definidas do modal "Reprovar" citam itens superados. **Nunca usar.** Ao abrir o
  modal por "Editar", conferir os checkboxes marcados antes de salvar, porque já apareceu opção
  marcada sem ter sido gravada.
- A caixa "Especificar" tem limite de **2.000 caracteres**. Já saiu CIA truncada: conferir o
  texto salvo pela API.
- O texto vai **sem aspas nem escape de CSV**. Já saiu `";` e `""A""` numa CIA.
- Formatação: começar com quebra de linha, uma notificação por hífen.
- Depois de emitida a CIA, a API devolve todos os itens como "Analisar". É o ciclo novo, não
  perda do que foi lançado.
- Pranchas: baixar por `/solcbm/api/v1/adm/arquivo/<id>` com o token e ler com pdf.js na própria
  página. Isso permite comparar revisão × revisão sem baixar nada.
- **2ª análise:** o RT costuma responder só nas pranchas. Conferir se o arquivo foi de fato
  substituído (mesmo id = não substituído).
- **Taxa de reanálise (RT 05 P05/2025, 5.2.5.1):** reprotocolar em até 30 dias da ciência depois
  da 1ª CIA isenta da primeira taxa de reanálise. Da 2ª CIA em diante, cobra-se sempre.
  ⏳ provisório — lido por resumo, conferir no PDF.
- **Base de tabelas:** a 6C estava sem a linha de Chuveiros Automáticos no JSON (corrigido). O
  sinal do erro foi uma **nota órfã, sem célula**.
