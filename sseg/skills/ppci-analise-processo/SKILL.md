---
name: "ppci-analise-processo"
description: "Pipeline completo de análise de PPCI no SOL-CBMRS: do print à CIA, com conferência de definidora, tabela de exigências, normas e laudo."
---

# Análise de processo PPCI (SOL-CBMRS)

Fluxo completo do que fazer quando chega um processo para análise. A doutrina normativa
(hierarquia de fontes, vigência, proibição de alucinação, não presumir) está nas Instruções
do projeto e vale sempre — esta skill é o **procedimento**.

## Quando disparar

Print PPCI, memorial ou PDF da análise técnica anexado · código de processo `A00…` ·
"1ª/2ª análise" · "campo 4" · ocupação definidora/predominante · carga de incêndio ·
altura ascendente/descendente · Tabela 5/6B/6F.3/Anexo B · laudo de inviabilidade ·
medida compensatória · "confere esse processo pra mim".

## Autonomia

**Rodar o pipeline inteiro sem pedir confirmação a cada etapa** e entregar um relatório
único, separando: (a) o que está conforme, (b) o que vira exigência, (c) o que depende de
decisão ou de dado que só o usuário tem.

**Duas exceções param o pipeline. Nas duas: perguntar e esperar.**

⛔ **1. Dúvida de enquadramento de ocupação.** Dúvida sobre a divisão de uma ocupação, sobre
se uma subsidiária vira predominante (itens 5.2.2.1, 5.2.2.2 ou 5.2.3 da RT 01/2024) ou sobre
a área de um ambiente → **parar e perguntar**, que o usuário lê a planta baixa e responde.

⛔ **2. Critério (b) do item 5.1.2 — desempate por número de medidas.** Sempre que a definidora
depender de contar medidas, **parar e perguntar antes de concluir**. O motivo é as **notas**:
é a nota colada na célula (X¹, X⁸, X⁹…) que decide se aquela medida entra ou não na contagem
da divisão, e portanto quem vence o desempate. A transcrição das tabelas no projeto dá a
célula; **quem aplica a nota ao caso concreto é o analista**.

**O que apresentar ao parar no critério (b)** — sem concluir nada:
- as divisões em disputa, com tabela e coluna de cada uma;
- a lista de células de cada divisão, com o número da nota colado;
- o **texto integral** de cada nota que aparece nessas células;
- quanto dá a contagem em cada hipótese (nota aplicável ou não), e o que isso muda.

Mesma disciplina fora do desempate: nota que condiciona a medida a um fato do caso concreto
(ex.: "obrigatório se a edificação estiver afastada mais do que 20 metros da via pública")
**nunca** se resolve sozinha — apontar a condição e perguntar.

## ⏱️ Custo — as regras que mais economizam

Medição de uma sessão real (02/09/2026, 147 rodadas): a **execução** das ferramentas custou
~2 s por rodada e é irrelevante. O custo está na **geração**, dominada por duas coisas —
**datilografar documento longo** e **carregar arquivo grande no contexto**.

1. 🚫 **Nunca abrir `scripts/dados/tabelas_conferidas.json`.** É a origem, com as 48 tabelas
   juntas; foi fatiado justamente para não ser lido. Usar `scripts/dados/tabelas/` (passo 5).
2. **Gravar no projeto UMA VEZ, no fim.** `project_write` substitui o documento inteiro — não
   existe patch. Reescrever 3 mil palavras porque duas frases mudaram foi o maior desperdício
   da sessão. Acumular e gravar em bloco no final. **Exceção: dado errado na base** (uma
   contagem, uma vigência, uma fonte) — esse se corrige na hora, porque contamina a CIA.
3. ⭐ **`<N>.pdf` e `<N>.json` da análise só quando o usuário pedir para "atualizar a pasta".**
   Gerar no começo obriga a gerar de novo no fim, com os status finais — é crédito gasto duas
   vezes (regra do usuário, 24/09/2026). Durante a análise, trabalhar pela leitura da API do
   SOL, sem gerar arquivo. Ler os arquivos das análises ANTERIORES (`1.json`, `CIA 1.pdf`)
   continua sendo o primeiro passo.
4. **Trazer os PDFs das normas da pasta local no início** — `Carpes\Normas`, ver a seção
   "Ler os PDFs das normas" — e extrair todos de uma vez com `pdftotext -layout`.
5. **Entregar a leva inteira de inconformidades**, revisar no fim, e só então gravar.
6. **Delegar tarefa mecânica a subagente com modelo leve** (Haiku/Sonnet), que não consome o
   contexto principal: extrair texto de planta, montar o `<N>.json`, comparar duas análises,
   resolver célula de tabela, gerar PDF. O modelo forte fica para enquadramento de ocupação,
   aplicação de nota, escolha de definidora e redação de notificação.

7. **Da API do SOL, trazer só o resumo filtrado na página** (receita em
   `sol-cbmrs-navegador`, "Trazer o texto para a conversa"). Nunca o JSON bruto em fatias.
8. **`device_commit_files` com todos os arquivos numa chamada só** (`1.pdf`, `1.json`,
   `CIA 1.pdf`, `CIA 1 textos.json`), não um por chamada.

Manter: **ler a página pela API ou com `get_page_text`, não com screenshot** — screenshot só
quando a imagem É o dado (planta, corte, tabela em imagem) ou para conferir a textarea antes
de salvar. Não pedir `screenshot` no mesmo `browser_batch` que um `scroll`: volta duplicado.
E **não pedir confirmação** nos passos de rotina já definidos (abrir o SOL, zoom, aguardar o
código).

## Ordem de apresentação do relatório

A conferência das **normas do campo 4 vem depois da ocupação definidora**, nunca antes —
tanto no raciocínio quanto na ordem em que o relatório é escrito.

Veredito primeiro, em até 5 linhas ou uma tabela. Fundamentação só quando a conclusão vira
exigência, ou quando o usuário pedir, no formato: fonte · item · trecho literal que decide
(até 3 linhas) · aplicação em uma frase. Texto integral do item só se pedido.
**Não recapitular o que já foi dito em turno anterior** — referenciar e seguir.

## 📖 Ler os PDFs das normas

### ⭐ De onde vem o arquivo: a pasta local, não o link

**`C:\Users\55519\Desktop\Carpes\Normas\`** é a fonte primária. Inventário conferido, versão
de cada arquivo e o que falta lá: doc `workflow/pasta-normas-local.md` do projeto.

```
device_list_dir  C:\Users\55519\Desktop\Carpes\Normas      (confere se o arquivo está lá)
device_stage_files <só os arquivos daquele passo>          -> /mnt/user-data/uploads/Carpes/Normas/
pdftotext -layout <arquivo>.pdf - | tr -d '\f'
```

🚫 **O campo "Link oficial" dos docs de norma serve para citar a fonte, não para obter o
arquivo.** WebFetch resume e trunca antes dos anexos, e baixar por `curl`/`wget`/Python não é
permitido neste ambiente. O link nunca vira PDF em mãos.

🚫 **Não pedir ao usuário PDF de norma que já está na pasta.** Pedir só o que a lista de
faltantes do doc indica. Na pasta (09/09/2026): Decreto 51.803 consolidado, RT 01/2024,
RT 02/2014, RT 04/2022, RT 05 P1.1/2016, RT 05 P07/2025, RT 10/2024, RT 11 P01/2016,
RT 12/2021, RT 14/2016, RT 17 P01/2025 e a RT de Implantação do SOL. **Faltam**: LC 14.376,
RT 05 P06, RT 05 P08, RT 09, RT 13, RT 15, RT 16 e **RT 18** (essa já custou erro de citação).

⚠️ **`RTISOL.pdf` é a RT de Implantação do SOL, não "isolamento de riscos"** — isolamento é o
`RT CBMRS 04`. E é arquivo de duas colunas: `-layout` intercala as colunas na mesma linha.

### Método

**`pdftotext -layout` sobre o PDF em mãos é o método bom.** Preserva o alinhamento das
colunas, lê os anexos e as tabelas inteiras, e é transcrição, não resumo.

🚫 **WebFetch não serve para tabela nem para anexo**: trunca antes dos anexos e resume o que
lê. Serve só para localizar em que item está o assunto.

⚠️ **Remover o form feed antes de procurar tabela.** Os cabeçalhos vêm precedidos de `\f`
(quebra de página), então `grep "^ *TABELA"` **não casa** e a tabela parece não existir. Foi
esse detalhe que sustentou por meses a afirmação falsa de que "o PDF consolidado do CBMRS não
traz o Anexo B" — traz, completo. Lavar com `.replace("\\f", " ")` antes de grepar ou parsear.

⚠️ **Conferir a versão na capa e no Art. 2º, nunca pelo nome do arquivo.** O PDF do Anexo B em
`estado.rs.gov.br` é o **texto original de 2014** e não menciona o Decreto 53.280/2016. O do
site do CBMRS é o **consolidado até o Decreto 57.967/2024**. São diferentes nas células.
Procurar "atualizado até" e contar menções a decretos alteradores antes de usar.

## Ferramentas

Os scripts vivem no projeto, em `scripts/`. No Cowork, antes de usar, trazer para o disco —
**de preferência do clone local** (`Carpes\SSEG\sseg\scripts\` via `device_stage_files`), que
não passa o arquivo pelo contexto:

```
Carpes\SSEG\sseg\scripts\sseg.py                           -> sseg/sseg.py
Carpes\SSEG\sseg\scripts\tabelas.py                        -> sseg/tabelas.py
Carpes\SSEG\sseg\scripts\dados\tabelas\tab-00-indice.json  -> sseg/dados/tabelas/
Carpes\SSEG\sseg\scripts\dados\tabelas\<arquivo do grupo>  -> sseg/dados/tabelas/
Carpes\SSEG\sseg\scripts\dados\indice_normas.json          -> sseg/dados/indice_normas.json
python3 sseg/sseg.py schema | check | pdf | diff
python3 sseg/tabelas.py rota | linha | divisao | notas
```

Sem o clone, `project_read scripts/...` (carrega o arquivo no contexto — mais caro).

**Sem sandbox (modo Chat) os scripts não rodam** — executar os mesmos passos manualmente,
lendo os JSON diretamente.

## Passo a passo

### 1. Identificar

Perguntar o número do processo se não vier. A subpasta do processo fica em
`C:\Users\55519\Desktop\Carpes\print ppci\<processo>\`.

⭐ **Antes de perguntar qualquer coisa ao usuário, abrir a pasta do processo.** `1.json` e
`CIA 1.pdf` costumam responder metade das dúvidas de uma reanálise — inclusive as confirmações
que o próprio analista já deu em turnos anteriores (altura, pavimento de descarga, área de
ambiente). Perguntar o que a pasta já tem é retrabalho.

### 1.1 Arquivar — SÓ quando o usuário pedir "atualizar a pasta"

🚫 **Não gerar `<N>.pdf` nem `<N>.json` no começo da análise.** Os status ainda vão mudar, e o
arquivo teria de ser gerado de novo no fim. Quando o usuário pedir, gerar os dois com os
status finais (ver `sol-cbmrs-navegador`, "Gerar a cópia em PDF da página").

Nomear pelo **rótulo "Nª Análise" do próprio print**: `1.pdf`, `2.pdf`… e `CIA 1.pdf`,
`CIA 2.pdf`. Pasta nova cujo primeiro arquivo já é a 2ª Análise vai como `2.pdf`.

Junto com os dois, gravar **`CIA <N> textos.json`**: o texto de cada caixa "Especificar" lido
pela API (`resultado.justificativas[].justificativa` de cada item reprovado, ver
`sol-cbmrs-navegador`), no formato `[{"campo": "4", "item": "<nome>", "texto": "..."}]`.
É a entrada da revisão final.

⭐ **Depois de arquivar, lembrar a revisão final em uma linha, sem rodá-la aqui:**

> Revisão final: abra uma conversa nova em Opus médio e cole "revisa a CIA do processo <código>".

Trocar "médio" por "alto" no lembrete só nos casos que a `ppci-revisao-cia` lista (fundamento
só de `normas/md/`, tese nova sem modelo no banco, mais de ~10 exigências).

⭐ **Depois de arquivar, esta conversa acabou.** Ajuste posterior no mesmo processo (pedido
do capitão, CIA gerada a conferir) vai em **conversa nova**, que começa lendo
`processos/<código>.md` e a pasta do processo. Continuar na conversa longa reenvia o
histórico inteiro a cada mensagem — foi o maior gasto medido em 24–25/09/2026 (uma
conversa aberta das 07:28 às 17:58).

A revisão rende mais lida de fora, sem o raciocínio que produziu a CIA (skill
`ppci-revisao-cia`). Se o usuário preferir revisar aqui mesmo, seguir a mesma skill.

### 1.2 Data de protocolo — onde achar (não perguntar antes de olhar)

**Não está na tela da análise técnica.** Sai da aba **"Consultar licenciamento" → "Marcos"**,
no marco **"Número do licenciamento gerado"**. A mesma aba traz a linha do tempo inteira,
inclusive o **deferimento do laudo de inviabilidade** — registrar no JSON.

### 2. Extrair o registro estruturado

Ler a página pela API e montar o registro do processo (em arquivo de trabalho no container,
se precisar). É o que torna a comparação entre análises barata. Nunca preencher campo que não
está no print. **Gravar `<N>.json` na pasta só no passo 1.1, quando pedido.**

### 3. Rodar as conferências

`sseg.py check`: definidora → rota da tabela → normas do campo 4 → travas → laudo x campo 4.
Marcadores: `OK` · `!!` atenção · `XX` exigência · `??` falta dado. Ler como **insumo**.

### 3.1 Checagens de praxe do campo 3 (rodar sempre, sem esperar o usuário pedir)

⭐ **Pavimento de maior população (área e população).** Pela RT 02/2014, item 4.30, o pavimento
de descarga é desconsiderado. Edificação **térrea / pavimento único** (ou com descarga própria
em cada pavimento) → os dois valores devem ser **0**. Se vierem preenchidos (ex.: área total e
população total repetidas), **notificar em "Geral" do campo 3** com o modelo do banco
(item 4.30), dizendo os valores declarados e que o pavimento único é o de descarga. Zerado em
pavimento único é correto — não notificar.

⭐ **Divisão J declarada x carga calculada em planta.** Quando houver depósito, conferir a nota
de cálculo da carga de incêndio na planta contra a Tabela 1 do Decreto: J-2 até 300, J-3 acima
de 300 até 1.200, J-4 acima de 1.200 MJ/m². Já houve RT que calculou 1.000,89 MJ/m² e rotulou
"J-4" (A00049887AA001) — a divisão decide definidora e reserva técnica de hidrantes. Levar a
divergência ao usuário antes de notificar com base na divisão rotulada.

### 4. Ocupação definidora

No print, a coluna **"Medidas de segurança contra incêndio?"** marca **"Sim"** na ocupação que
o RT declarou definidora. O papel do analista é **conferir se a escolha está correta**.

RT 01/2024, item 5.1.2 — ocupação mista sem isolamento: **(a)** maior grau de risco entre as
predominantes; **(b)** havendo empate, a que exigir o **maior número absoluto de medidas**.
Item 5.1.2.1: **F-6 é sempre definidora**. Item **5.1.3**: o roteamento usa a **área total a
ser protegida** e a **altura descendente**. Grau de risco pela Tabela 3 do Decreto (>300 até
1.200 MJ/m² = médio) — nas tabelas da RT 05 P07 ele **vem declarado no cabeçalho da divisão**.

⛔ **Chegou no critério (b): parar e perguntar.** Ver "Autonomia", exceção 2.

⚠️ **Empate pode ser inócuo.** Se as duas linhas exigirem o mesmo número **e as mesmas
medidas**, tanto faz qual é a definidora: o campo 4 é idêntico e **não há o que notificar**.
Apresentar isso ao parar.

Antes de aceitar a lista de ocupações, testar as quatro portas de saída do item 5.2.2:
depósito "J" acima de 10% da área total ou 1.500 m² (5.2.2.1); reunião de público "F" com
lotação acima de 500 (5.2.2.2); grupo "M" (5.2.2.3); e ambiente destinado prioritariamente a
**público externo**, que vira principal sem limiar (5.2.3).

### 5. Tabela de exigências

Primeiro a **fonte**: "existente regularizada" → **RT 05 Parte 07/2025, Anexo A** (vigente
desde 01/02/2025). "Existente não regularizada" ou "a construir" → **Decreto 51.803/2014,
Anexo B**.

⭐ **As duas estão transcritas no projeto, fatiadas por grupo**, em `scripts/dados/tabelas/`.
**Não pedir print de tabela de exigências.** A consulta são dois arquivos pequenos:

1. `tab-00-indice.json` — mapa `divisão → {arquivo, tabela, bloco}` nas duas fontes, colunas
   válidas, regra de contagem, aviso das notas, linhas de medida por fonte;
2. o arquivo que o mapa apontar: `tab-b-<GRUPO>.json` (Anexo B) ou `tab-rt05-<GRUPO>.json`
   (RT 05 P07). Ex.: C-2 → `tab-b-C.json`; J-3 → `tab-b-J.json`. Tabela 5 e Tabela 7 têm
   arquivo próprio: `tab-b-tabela5.json`, `tab-b-tabela7.json` e os `tab-rt05-*` equivalentes.

As linhas com a **nota já aplicada** a um caso concreto estão em `linhas-conferidas.json`, na
mesma pasta, junto com os erros de leitura registrados.

Cada tabela guarda `divisoes` (blocos de coluna na ordem) e `medidas` (fila de células, 6 por
bloco): índice = `(bloco * 6) + coluna`. `scripts/tabelas.py` resolve isso pela linha de
comando.

🔴 **As células vêm com as notas coladas (X¹, X⁸, X⁴ʾ⁵) e a nota NÃO se aplica sozinha.**
Sempre ler o texto da nota em `notas` e, se ela decidir alguma coisa, levar ao usuário.

Ainda exigem imagem: **Tabela 4** (roteamento) e **6M.1, 6M.2, 6M.4, 6M.5** (eixo em metros de
extensão, não altura).

⚠️ As tabelas da RT 05 P07 têm menos linhas que as 16 do Anexo B do Decreto, e o número varia
por tabela. **A falta de Segurança Estrutural, CMAR, Compartimentação Vertical ou Controle de
Fumaça não é regra geral:** a Tabela 5 exige CMAR para F-5/F-6 e L; a 6F.3 exige CMAR para
F-5/F-6; as duas exigem Controle de Fumaça para F-6 (ver notas); a 6L.1 exige Segurança
Estrutural e CMAR para L-2 e L-3; a 6C tem Compartimentação Vertical para shopping acima de
23 m. A ausência no campo 4 só não é pendência quando **a tabela da divisão** não traz a
linha: conferir no `tab-rt05-<GRUPO>.json` (buscar sem acento).

Roteamento: área ≤ 750 m² **e** altura ≤ 12 m → Tabela 5; senão → Tabelas 6, coluna por
altura (`Térrea | H≤6 | 6<H≤12 | 12<H≤23 | 23<H≤30 | Acima de 30`); subsolo ocupado → Tabela 7.

⚠️ **Nota geral "c" das tabelas do grupo C e nota geral "g" da Tabela 5** — *"para edificações
sem ventilação natural (janelas) exige-se controle de fumaça"* — **não é regra de subsolo**
(subsolo é a nota "a", que remete à Tabela 7): alcança a edificação inteira. Antes de exigir,
conferir as aberturas em planta; havendo janelas, a nota não aciona.

### 6. O que se analisa em planta e o que só se confere em memorial

É o **Anexo "L" da RT 05 Parte 1.1/2016** que responde, e a RT de Implantação (6.3.6.1.2)
remete à **coluna "A"** dele.

- **Tabela L.1 — "pronta resposta": memorial + PLANTA.** Extintores, Alarme, Saídas de
  Emergência, Acesso de Viaturas, Hidrante e Mangotinhos, Isolamento de Riscos, Hidrante
  Urbano.
- **Tabela L.2 — demais: SÓ MEMORIAL.** Sinalização, Iluminação, CMAR, Compartimentação,
  Segurança Estrutural, Chuveiros, Detecção, Controle de Fumaça, SPDA, Brigada, Plano de
  Emergência.
- ⭐ **Duas exceções entre parênteses na L.2:** sinalização **de orientação e salvamento** e
  iluminação **de balizamento** — essas **são** analisadas em planta, pela L.1, linha Saídas de
  Emergência, alínea "i".
- ⭐ **Medida compensatória inverte a regra:** vinda de laudo deferido, **tem que ser
  representada em planta** mesmo estando na L.2.

### 7. Normas do campo 4 (só depois de fechar a definidora)

Conferir cada norma contra `normas/00-indice-normativo.md`, aplicando **vigência por data de
protocolo**. Norma fora do índice: sinalizar, não dar como certa nem errada.

**RT 17 Parte 01/2025** entra em vigor em **01/01/2027** (Art. 2º) e, pelo **item 2.2**, sua
adoção é **facultativa para PPCI já protocolado**. Citar ou não citar **não é pendência**.

**Existente regularizada pode usar a legislação da época**, desde que **especificado no laudo
de inviabilidade e no campo de medidas**. Sem a especificação, vira exigência.

### 8. Memorial de cálculo da população

⚠️ **Não notificar incoerência dos blocos exibidos no SOL.** Faltam campos no sistema para o
RT representar o cálculo — é limitação do SOL, não erro do projetista. A população se confere
pela **tabela "Geral" do campo 3** e pela **planta baixa**, que é leitura do usuário.

### 9. Laudo de inviabilidade técnica

O laudo **já vem deferido** (marco nos Marcos) — nesta fase **não** se reavalia admissibilidade.
Verificar: **representação** nos elementos gráficos; **coerência com a planta**; e
**correspondência com o campo 4** — compensatória **sem linha nenhuma no campo 4** não será
analisada nem cobrada em vistoria → **notificar**.

**Brigada é exceção: na análise a conferência é meramente documental.**

⚠️ Se a compensatória não aparece no campo 4 porque **a tabela não a exige**, a exigibilidade
nasce do **próprio laudo** e o campo "Especificar" precisa dizer isso — a opção padrão do SOL
diria o contrário e o RT contestaria com razão.

⚠️ **Antes de tratar algo como inviabilidade, ver se a norma já DISPENSA.** RT 05 P07, item
**5.4**: para regularizadas **até 28/04/1997** são dispensados (a) adequação das larguras nas
saídas, (b) enclausuramento de escadas e rampas, (c) sistemas hidráulicos sob comando e
automáticos caso não existam (5.4.1 exclui F-6; 5.4.2 exige população compatível e largura
≥ 0,80 m). Item **5.5** faz o análogo entre 28/04/1997 e 26/12/2013. Dispensa legal não precisa
de compensatória.

### 10. Comparação com a análise anterior (da 2ª em diante)

`sseg.py diff` (com um JSON de trabalho no container, não gravado na pasta), ou comparação
campo a campo. Reportar em quatro colunas: **o que mudou · o que não mudou · o que foi
corrigido em resposta à CIA anterior · o que continua irregular**. Os textos das
inconformidades não estão na página — comparar também as CIAs arquivadas. Decidir por
exigência: **reiterar**, **complementar** ou **substituir**. Ver `ppci-notificacao-cia`.

⭐ **Comparar os PDFs das plantas antes de olhar o desenho.** Um `diff` do texto extraído com
`pdftotext -layout` das duas versões mostra na hora se o RT redesenhou ou só trocou um rótulo.
No caso Spessato, a única diferença entre as duas plantas baixas era "(C-2/J-3)" ter virado
"(C-2)", com toda a geometria intacta — isso mudou o veredito e custou uma chamada.

⚠️ **Medida que some do campo 4 sem ter sido notificada não é automaticamente irregular.** Se
a definidora mudou, a lista de exigências muda junto: no Spessato o RT retirou o Plano de
Emergência, e estava certo, porque a nota 8 da 6C o restringe à Divisão C-3. Recontar a tabela
na definidora nova antes de notificar a ausência.

## Nunca

- **Aplicar sozinho uma nota de tabela que decide contagem ou definidora** — parar e perguntar.
- Abrir `scripts/dados/tabelas_conferidas.json` numa análise.
- Contar medidas por resumo automático (WebFetch e afins).
- **Gerar `<N>.pdf` / `<N>.json` da análise sem o usuário pedir para atualizar a pasta.**
- **Pedir ao usuário PDF de norma que já está em `Carpes\Normas`**, ou tentar obter o arquivo
  pelo link oficial — o link não baixa.
- Reescrever um doc do projeto no meio da análise por causa de ajuste de redação — acumular
  e gravar no fim. (Dado errado na base é exceção: corrigir na hora.)
- Notificar o memorial de cálculo da população por incoerência dos blocos do SOL.
- Apontar inversão de altura por geometria aparente (RT 02/2014, item 4.20).
- Presumir dado ausente do print, ou herdar afirmação do projeto sem verificar quando ela
  decide onde procurar.
- Perguntar ao usuário dado que `<N>.json` ou a CIA arquivada já respondem.
- Inferir, sem a planta, se algo "bate" com o desenho — isso é do usuário.
- Misturar dados de processos diferentes.

## Verificação antes de entregar

- [ ] Havendo critério (b) ou nota condicionante, o pipeline **parou e perguntou**?
- [ ] A definidora foi conferida e fechada **antes** da conferência das normas do campo 4?
- [ ] Havendo dúvida de enquadramento de ocupação, o pipeline parou e perguntou?
- [ ] As checagens de praxe do campo 3 (passo 3.1) foram rodadas?
- [ ] A fonte da tabela corresponde à situação de existência (RT 05 P07 x Anexo B)?
- [ ] O texto de cada nota citada foi lido, e não só o número dela?
- [ ] Antes de tratar como inviabilidade, foi checado se 5.4/5.5 da RT 05 P07 já dispensam?
- [ ] Cada `XX` tem dispositivo localizado e conferido, não presumido?
- [ ] O PDF de cada norma citada veio da **pasta local**, com a versão conferida na capa?
- [ ] A data de protocolo saiu dos Marcos, e a versão da norma corresponde a ela?
- [ ] Dados faltantes foram listados em vez de completados?
- [ ] `<N>.pdf` e `<N>.json` **só** foram gerados se o usuário pediu para atualizar a pasta?
- [ ] As atualizações do projeto foram gravadas **em bloco, no fim**?
- [ ] Ao arquivar, `CIA <N> textos.json` foi gravado e a revisão final foi lembrada?