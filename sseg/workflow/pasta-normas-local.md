---
name: pasta-normas-local
description: Onde estão os PDFs das normas — desde 15/09/2026 em sseg/normas/pdf/ no próprio repositório, e também na pasta local Normas do PC. Inventário conferido arquivo a arquivo, procedimento de leitura (pdftotext), como trazer norma nova do site, armadilhas e o que ainda falta
sources: [cowork]
---

# Onde estão os PDFs das normas

> Fato do setup, registrado em **09/09/2026**, depois de o usuário apontar que o pipeline
> insistia em link/download em vez de usar esta pasta. Atualizado em **11/09/2026** (IN 45),
> em **15/09/2026** (PDFs versionados no repositório), em **22/09/2026** (IT 37/2025) e em
> **24/09/2026** (IN 066/2025 e IN 067/2025).

## ⭐ Primeira parada: `sseg/normas/pdf/`

Os PDFs oficiais estão **dentro do repositório** desde 15/09/2026 (14 arquivos; 17 com a IN 66, a IN 67
e a IT 37, em 24/09/2026), junto com as conversões do anydoc em `sseg/normas/md/`. Em qualquer
máquina com o clone, a norma está em mãos — sem device bridge, sem stage, sem pedir arquivo ao
usuário. Ler direto com `pdftotext`, seguindo as regras de extração abaixo, que continuam
valendo integralmente.

O restante deste doc trata da **pasta local no PC**, que segue existindo com o mesmo conteúdo.
Ela importa para: norma que ainda não foi para o repo, arquivo novo que o usuário acrescentar,
e conferência de versão. **Mudando uma, mudar a outra.**

✅ **24/09/2026:** o `IT37.pdf`, que em 22/09/2026 tinha entrado só na pasta local, foi copiado
para `sseg/normas/pdf/`, com a conversão em `sseg/normas/md/` e em `Carpes\Normas\_md\`.

## Caminho

`C:\Users\55519\Desktop\Carpes\Normas\`

No PC do usuário (`pc-carpes`), acesso pelo device bridge. A pasta **`Carpes` inteira** é a
que se pede — irmãs dela: `print ppci` ([[pasta-print-ppci-local]]), `Exemplos`, `RECURSOS`.

## ⭐ O acesso é POR SESSÃO — pedir na abertura, não no meio da análise

O consentimento de pasta vale para **a sessão**, não para o projeto: **toda conversa nova
começa sem acesso**, mesmo com este doc gravado. Não há como conceder por projeto hoje.

**Consequência prática:** o pedido de acesso entra na **rotina de abertura**, junto com abrir
o SOL — não quando a análise já travou por falta do PDF. Uma aprovação, no começo, cobrindo
`Carpes` inteira:

```
device_request_folder_access  ["C:\\Users\\55519\\Desktop\\Carpes"]
reason: ler os PDFs oficiais em Carpes\Normas e a pasta "print ppci" das análises
```

Pedir **uma vez só** e a pasta-mãe, não subpasta por subpasta — cada pedido gasta um clique
do usuário. Se ele recusar ou não responder, seguir com o que der e pedir os arquivos por
anexo; não repetir o pedido.

## 🚫 Por que não usar os links

Os docs de `normas/` trazem um campo **"Link oficial"** (`bombeiros.rs.gov.br/upload/...`).
Esses links servem para **identificar e citar a fonte**, não para obter o arquivo:

- **WebFetch resume e trunca antes dos anexos** — já registrado no [[00-indice-normativo]].
- 🔴 **WebFetch também INVENTA** (22/09/2026): pedido para transcrever as Tabelas B.1 e B.2 da
  IT 37, devolveu tabelas com faixas e tempos que não existem no PDF — as tabelas originais são
  imagem. Número de tabela nunca sai de WebFetch.
- **Baixar o PDF por `curl`/`wget`/Python não funciona** neste ambiente: o proxy recusa
  `bombeiros.rs.gov.br` (`CONNECT tunnel failed, response 403`, reconfirmado em 24/09/2026). Não
  existe caminho de download alternativo. O visualizador de PDF do Chrome também não é legível
  pela automação (`get_page_text` vazio; screenshot bloqueado).
- 🚫 **Download pelo navegador do app também não chega à pasta** (24/09/2026): `fetch` do PDF na
  página do CBMRS funciona (status 200), mas o clique num link `download` gerado por script não
  gravou arquivo nenhum em `Downloads`.

Ou seja: **o link nunca vira PDF em mãos pelo Claude**. O PDF em mãos vem da pasta local — e, na
falta dele lá, do arquivo que o usuário salvar na pasta ou anexar.

## ⭐ Norma nova que só está no site — o caminho que funcionou (24/09/2026)

1. Achar o link: WebFetch em `bombeiros.rs.gov.br/instrucoes-normativas` (ou a página da
   categoria) lista número, ementa e URL do PDF. **Só a URL** — o texto que o WebFetch devolve do
   PDF não serve.
2. **O usuário baixa e salva em `Carpes\Normas`** (foi assim com a IN 66 e a IN 67). Nome curto,
   no padrão da pasta: `IN66.pdf`, `IN67.pdf`.
3. `device_list_dir` na pasta para confirmar, `device_stage_files` para trazer.
4. Conversão anydoc **no próprio Cowork** — ver "Sincronizar".

## ⭐ Procedimento (é este, não pedir o PDF ao usuário)

1. `device_list_dir` em `C:\Users\55519\Desktop\Carpes\Normas` — conferir se o arquivo existe
   e a data.
2. `device_stage_files` com o(s) arquivo(s) **que aquele passo precisa** (não a pasta toda).
   Cai em `/mnt/user-data/uploads/Carpes/Normas/`.
3. Extrair:
   - **uma coluna** → `pdftotext -layout <arquivo>.pdf - | tr -d '\f'`
   - **duas colunas** → `pdftotext <arquivo>.pdf - | tr -d '\f'` (**sem** `-layout`)
   - **tabela em imagem** → `pdftoppm -f <p> -l <p> -r 110 -png <arquivo>.pdf <prefixo>` e ler a imagem
   O form feed sai **antes** de qualquer `grep "TABELA"`, senão a tabela "não existe".
4. Só pedir arquivo ao usuário quando a norma **não estiver** na pasta (lista abaixo).

Validado: staging + `pdftotext` funcionam; `pdftotext`, `pdftoppm`, `pdfinfo` e `qpdf` estão
instalados no sandbox.

## Inventário conferido — 09/09/2026, atualizado em 11/09/2026, 22/09/2026 e 24/09/2026

Versão lida da capa e do Art. 2º de cada arquivo, um a um.

| Arquivo | Norma | Versão / vigência na capa | Bate com o índice? |
|---|---|---|---|
| `DECRETO51803.pdf` (109 p.) | Decreto 51.803/2014 | **atualizado até o Decreto 57.967, de 27/12/2024** | ✅ é o consolidado certo |
| **`IN45.pdf`** (3 p.) ⭐ novo em 11/09/2026 | **IN 045/CBMRS/DSPCI/2023** — corredor enclausurado | **2023** — assinada 26/04/2023, DOE 81 de **27/04/2023**, Art. 7º: vigor na publicação; revoga a IN 025/2020 | ✅ íntegra transcrita |
| **`IN66.pdf`** (2 p.) ⭐ novo em 24/09/2026 | **IN 066/CBMRS/DSPCI/2025** — saídas de emergência em F-5, F-6, F-11 e F-12 | **2025** — assinada 29/09/2025 (Diretor do DSPCI), DOE 191 de **30/09/2025**, Art. 5º: vigor na publicação; sem cláusula revogatória | ✅ íntegra em [[in-066-2025-saidas-reuniao-publico]] |
| **`IN67.pdf`** (20 p.) ⭐ novo em 24/09/2026 | **IN 067/CBMRS/DSPCI/2025** — Solução Técnica Equivalente (STE) | **2025** — assinada 24/10/2025 (Diretor do DSPCI), DOE 217 de **05/11/2025**, Art. 15: vigor na publicação | ✅ íntegra em [[in-067-2025-solucao-tecnica-equivalente]] |
| **`IT37.pdf`** (11 p.) ⭐ novo em 22/09/2026 | **IT 37/2025 do CBPMESP** — Subestação elétrica | Portaria CCB 003/800/25, DOE-SP **20/03/2025**; em vigor no CBMRS desde 01/07/2025 (página oficial) | ✅ aplicável pela RT 01/2024, 4.8.1 e 4.8.7 — itens conferidos no [[00-indice-normativo]] |
| `RT CBMRS 01 – Diretrizes Básicas de Segurança Contra Incêndio.pdf` (23 p.) | RT 01 | **2024** — Art. 2º: vigor em **01/01/2025**, revoga a RT 01 de 12/04/2022 | ✅ |
| `RT CBMRS 02 – Termos e Definições.pdf` (25 p.) | RT 02 | **2014** — 19/12/2014, DOE 037 de 25/02/2015 | ✅ |
| `RT CBMRS 04 – Isolamento de Riscos.pdf` (35 p.) | RT 04 | **2022** — 12/04/2022, vigor 60 dias após publicação | ✅ |
| `RTCBMRS 5 parte 1 - 1 2016 - ppci na forma completa.pdf` (62 p.) | RT 05 Parte 1.1 | **2016** — vigor na publicação; revoga a Parte 01 de 14/03/2016 | ✅ |
| `RT 05 Parte 07.pdf` (55 p.) | RT 05 Parte 07 | **2025** — Art. 2º: **1º de fevereiro de 2025** | ✅ confirma a correção de 02/09 |
| `RT10.pdf` (9 p.) | RT 10 | **2024** — Art. 2º: **07/04/2025** | ✅ |
| `RT11.pdf` (37 p.) ⚠️ duas colunas no corpo | RT 11 Parte 01 | **2016** — vigor **19/09/2016**, DOE 146 de 02/08/2016 | ✅ 5.12.1.2 transcrito em 11/09/2026; 5.7.3.3.1 conferido em 22/09/2026; **5.4.1.2.2** conferido em 24/09/2026 |
| `RT12.pdf` (41 p.) | RT 12 | **2021** — Art. 2º: **01/01/2022** | ✅ |
| `RT14.pdf` (11 p.) | RT 14 | **2016** — 11/04/2016, DOE 077 de 26/04/2016, vigor 30 dias após | ✅ Tabela 2 e 5.4.5 (sobre rodas) conferidos em 22/09/2026 |
| `RT17.pdf` (46 p.) | RT 17 Parte 01 | **2025** — Art. 2º: **1º de janeiro de 2027** | ✅ nota "f" da Tabela 1 (M-6 → IT 37) conferida em 22/09/2026 |
| `RT18.pdf` (10 p.) ⚠️ duas colunas | RT 18 | **2025** — assinada 20/05/2025, Art. 2º: **1º de novembro de 2025** | ✅ seção 8 e 9.3/9.4 transcritas do PDF |
| `RTISOL.pdf` (15 p.) ⚠️ duas colunas | ⚠️ **RT de Implantação do SOL-CBMRS** | **4ª Edição/2022** — DOE 178 de 15/09/2022, vigor **19/09/2022** | ⚠️ ver abaixo |

## ⚠️ Armadilhas desta pasta

1. **`RTISOL.pdf` não é "isolamento de riscos".** É a **RT de Implantação do SOL**. Isolamento
   de riscos é o `RT CBMRS 04`. Abrir `RTISOL.pdf` procurando afastamento entre edificações
   dá em nada — e pior, dá a impressão de que a RT 04 não está na pasta.
2. **Arquivos de duas colunas: `RTISOL.pdf`, `RT18.pdf`, o corpo da `RT11.pdf` e o corpo da
   `IT37.pdf`.** `pdftotext -layout` **intercala as duas colunas na mesma linha** e embaralha a
   ordem dos itens — na RT 18 o 8.1 sai depois do 8.2 e o 9.3 aparece no meio do 8.5; na RT 11
   o texto do 5.12.1.2 sai colado ao do 5.12.1.3. **Nesses, usar `pdftotext` sem `-layout`**
   para item de texto; nas **tabelas**, aí sim `-layout`. Regra geral: se a numeração sair fora
   de ordem, é duas colunas.
3. **`RTISOL.pdf` parece ser a 4ª Ed./2022 original, não a "versão corrigida"** (o arquivo
   citado em [[rt-implantacao-sol-cbmrs]] é o publicado em out/2024). Sem marcação de
   "corrigida" na capa. Antes de citar item novo do SOL em CIA, conferir contra o PDF do link
   ou pedir o arquivo corrigido ao usuário.
4. **Nome do arquivo não é fonte.** A versão sai da **capa e do Art. 2º**, sempre — foi assim
   que se pegou o item 1 e a data de 19/09/2022.
5. **`IN45.pdf` é coluna única e só 3 páginas** — `-layout` funciona bem nele. Não confundir o
   número da IN com item de norma: é **Instrução Normativa 045/2023**, com artigos e incisos
   romanos, não uma RT.
6. **`IT37.pdf` — as Tabelas B.1 e B.2 (Anexo B, página 11) são IMAGEM.** `pdftotext` devolve
   só o título; a Tabela B.3 sai em texto. Ler renderizando a página:
   `pdftoppm -f 11 -l 11 -r 110 -png IT37.pdf itb` e abrir a imagem.
7. **`IN66.pdf` e `IN67.pdf` são coluna única** — `pdftotext -layout` lê certo. Mas a
   **conversão anydoc** das duas embaralha trechos em **tabelas falsas** (`|...|`): na IN 66, a
   página 2 inteira (§ 3º do Art. 2º a Art. 5º); na IN 67, os Arts. 2º a 5º, 12 a 15 e o quadro
   do Anexo A. O **quadro de parâmetros do Anexo A da IN 67** sai do `pdftotext -layout` com as
   colunas "Critério" e "Parâmetro" intercaladas — ler com atenção ou renderizar a página.

## O que NÃO está na pasta (24/09/2026)

Precisa de anexo do usuário ou de outra fonte:

- **LC 14.376/2013** — e o índice já registra que o PDF acessível está consolidado só até a
  LC 14.924/2016.
- **RT 05 Parte 06/2025** (fiscalização) · **RT 05 Parte 08/2016** (simbologia) ·
  **RT 05 Parte 4B** (construções provisórias)
- **RT 09/2025** (CMAR) · **RT 13/2025** (iluminação) · **RT 15 Parte 01/2023** (brigada) ·
  **RT 16/2017** (hidrante urbano)
- RT 03/2016 e as RTs de ocupações específicas (20, 21, 22, 23, 31, 32)
- **IN 025/2020** (corredor enclausurado, revogada — mas é a aplicável a PPCI protocolado até
  26/04/2023) e **IN 056/2024** (câmaras frigoríficas/amônia)
- **IN 068/2025** (enquadramento F-5, F-6, F-8, F-11, F-12 — conversa com a IN 066) e a
  **Portaria** que regula o Corpo Técnico da STE (IN 067, Art. 8º)
- ITs do CBPMESP aplicáveis por remissão da RT 01/2024 e ainda sem PDF: **IT 08, IT 09, IT 15,
  IT 25**

📌 **RT 13/2025 (iluminação) é a mais sentida das que faltam** — é medida corrente no campo 4
e o doc dela no projeto não tem item transcrito.

✅ **RT 18/2025 entrou em 09/09/2026** e o erro de citação registrado (8.1 "a" × 8.3) está
agora conferido no PDF em mãos, com dois itens novos que faltavam: **8.2.4** (ático de casa de
máquinas/reservatório — acionador *recomendado*) e **9.4.1/9.4.2**.

✅ **IN 045/2023 entrou em 11/09/2026** — íntegra transcrita em
[[in-045-2023-corredor-enclausurado]]: Art. 1º (incisos I a XVI, §§ 1º e 2º) e Arts. 2º a 7º.
Na mesma leitura foi conferido o **item 5.12.1.2 da RT 11**, que é o regime do corredor de
**descarga** — o Art. 6º da IN exclui esse caso.

✅ **IT 37/2025 entrou em 22/09/2026** (caso A00003462AB001) — itens 4.4.2, 4.4.4, 4.4.7,
4.4.9, 4.5, 4.6 e Anexo B conferidos; resumo no [[00-indice-normativo]].

✅ **IN 066/2025 e IN 067/2025 entraram em 24/09/2026** — pasta local **e** repositório
(`pdf/`, `md/`), íntegras em [[in-066-2025-saidas-reuniao-publico]] e
[[in-067-2025-solucao-tecnica-equivalente]]. Na mesma leitura, conferido o **5.4.1.2.2 da RT 11**.

## Sincronizar

Acrescentando uma norma, são **quatro** lugares, sempre juntos:

1. o PDF em `sseg/normas/pdf/` (e na pasta local do PC);
2. a conversão em `sseg/normas/md/`, com `anydoc <arquivo> -o <saida>.md` — com o cabeçalho de
   aviso "NAO E FONTE DE FUNDAMENTO" que os demais `.md` de `md/` têm; e a mesma conversão, sem
   cabeçalho, em `Carpes\Normas\_md\` no PC;
3. a linha correspondente no inventário acima e em [[00-indice-normativo]] — e, sendo norma
   nova com itens conferidos, o doc de transcrição comentada em `normas/`;
4. a entrada em `scripts/dados/indice_normas.json`.

⭐ **anydoc no Cowork (24/09/2026):** o PC não tem shell acessível pelo Claude, mas o anydoc roda
aqui igual: `pip install --break-system-packages firecrawl-anydoc==0.2.4` (mesma versão do PC) e
o wrapper local do usuário, trazido por stage de
`Carpes\RECURSOS\ferramentas-ia\anydoc_cli.py`: `python3 anydoc_cli.py <arquivo> -o <saida>.md`.
O wrapper chama o conversor nativo direto, sem OCR online — a regra de nada sair da máquina
vale para documento de processo; norma pública baixada do site oficial não tem esse problema,
mas o caminho é o mesmo.

⚠️ Correção registrada em 15/09/2026: a versão anterior deste doc mandava atualizar um campo
`pdf_local` no `indice_normas.json`. **Esse campo não existe** — nunca existiu. O que o JSON
tem é o bloco `normas` com título, vigência e observações de cada norma.
