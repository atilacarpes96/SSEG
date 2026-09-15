---
name: pasta-normas-local
description: A pasta local "Normas" no PC do usuário — caminho, inventário conferido arquivo a arquivo, procedimento de leitura (stage + pdftotext), armadilhas e o que ainda falta lá. É a PRIMEIRA fonte de PDF de norma; os links oficiais não são baixáveis pelo sandbox. Traz também a regra de pedir o acesso à pasta no início da sessão
sources: [cowork]
---

# Pasta local "Normas" — fonte primária dos PDFs

> Fato do setup, registrado em **09/09/2026**, depois de o usuário apontar que o pipeline
> insistia em link/download em vez de usar esta pasta. Atualizado em **11/09/2026** (IN 45).

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
- **Baixar o PDF por `curl`/`wget`/Python é proibido** neste ambiente quando o WebFetch não
  entrega. Não existe caminho de download alternativo.

Ou seja: **o link nunca vira PDF em mãos**. O PDF em mãos vem da pasta local — e, na falta
dele lá, do arquivo que o usuário anexar.

## ⭐ Procedimento (é este, não pedir o PDF ao usuário)

1. `device_list_dir` em `C:\Users\55519\Desktop\Carpes\Normas` — conferir se o arquivo existe
   e a data.
2. `device_stage_files` com o(s) arquivo(s) **que aquele passo precisa** (não a pasta toda).
   Cai em `/mnt/user-data/uploads/Carpes/Normas/`.
3. Extrair:
   - **uma coluna** → `pdftotext -layout <arquivo>.pdf - | tr -d '\f'`
   - **duas colunas** → `pdftotext <arquivo>.pdf - | tr -d '\f'` (**sem** `-layout`)
   O form feed sai **antes** de qualquer `grep "TABELA"`, senão a tabela "não existe".
4. Só pedir arquivo ao usuário quando a norma **não estiver** na pasta (lista abaixo).

Validado: staging + `pdftotext` funcionam; `pdftotext`, `pdfinfo` e `qpdf` estão instalados
no sandbox.

## Inventário conferido — 09/09/2026, atualizado em 11/09/2026

Versão lida da capa e do Art. 2º de cada arquivo, um a um.

| Arquivo | Norma | Versão / vigência na capa | Bate com o índice? |
|---|---|---|---|
| `DECRETO51803.pdf` (109 p.) | Decreto 51.803/2014 | **atualizado até o Decreto 57.967, de 27/12/2024** | ✅ é o consolidado certo |
| **`IN45.pdf`** (3 p.) ⭐ novo em 11/09/2026 | **IN 045/CBMRS/DSPCI/2023** — corredor enclausurado | **2023** — assinada 26/04/2023, DOE 81 de **27/04/2023**, Art. 7º: vigor na publicação; revoga a IN 025/2020 | ✅ íntegra transcrita |
| `RT CBMRS 01 – Diretrizes Básicas de Segurança Contra Incêndio.pdf` (23 p.) | RT 01 | **2024** — Art. 2º: vigor em **01/01/2025**, revoga a RT 01 de 12/04/2022 | ✅ |
| `RT CBMRS 02 – Termos e Definições.pdf` (25 p.) | RT 02 | **2014** — 19/12/2014, DOE 037 de 25/02/2015 | ✅ |
| `RT CBMRS 04 – Isolamento de Riscos.pdf` (35 p.) | RT 04 | **2022** — 12/04/2022, vigor 60 dias após publicação | ✅ |
| `RTCBMRS 5 parte 1 - 1 2016 - ppci na forma completa.pdf` (62 p.) | RT 05 Parte 1.1 | **2016** — vigor na publicação; revoga a Parte 01 de 14/03/2016 | ✅ |
| `RT 05 Parte 07.pdf` (55 p.) | RT 05 Parte 07 | **2025** — Art. 2º: **1º de fevereiro de 2025** | ✅ confirma a correção de 02/09 |
| `RT10.pdf` (9 p.) | RT 10 | **2024** — Art. 2º: **07/04/2025** | ✅ |
| `RT11.pdf` (37 p.) ⚠️ duas colunas no corpo | RT 11 Parte 01 | **2016** — vigor **19/09/2016**, DOE 146 de 02/08/2016 | ✅ 5.12.1.2 transcrito em 11/09/2026 |
| `RT12.pdf` (41 p.) | RT 12 | **2021** — Art. 2º: **01/01/2022** | ✅ |
| `RT14.pdf` (11 p.) | RT 14 | **2016** — 11/04/2016, DOE 077 de 26/04/2016, vigor 30 dias após | ✅ |
| `RT17.pdf` (46 p.) | RT 17 Parte 01 | **2025** — Art. 2º: **1º de janeiro de 2027** | ✅ |
| `RT18.pdf` (10 p.) ⚠️ duas colunas | RT 18 | **2025** — assinada 20/05/2025, Art. 2º: **1º de novembro de 2025** | ✅ seção 8 e 9.3/9.4 transcritas do PDF |
| `RTISOL.pdf` (15 p.) ⚠️ duas colunas | ⚠️ **RT de Implantação do SOL-CBMRS** | **4ª Edição/2022** — DOE 178 de 15/09/2022, vigor **19/09/2022** | ⚠️ ver abaixo |

## ⚠️ Armadilhas desta pasta

1. **`RTISOL.pdf` não é "isolamento de riscos".** É a **RT de Implantação do SOL**. Isolamento
   de riscos é o `RT CBMRS 04`. Abrir `RTISOL.pdf` procurando afastamento entre edificações
   dá em nada — e pior, dá a impressão de que a RT 04 não está na pasta.
2. **Arquivos de duas colunas: `RTISOL.pdf`, `RT18.pdf` e o corpo da `RT11.pdf`.**
   `pdftotext -layout` **intercala as duas colunas na mesma linha** e embaralha a ordem dos
   itens — na RT 18 o 8.1 sai depois do 8.2 e o 9.3 aparece no meio do 8.5; na RT 11 o texto
   do 5.12.1.2 sai colado ao do 5.12.1.3. **Nesses, usar `pdftotext` sem `-layout`** para item
   de texto; nas **tabelas dos anexos da RT 11**, aí sim `-layout`. Regra geral: se a numeração
   sair fora de ordem, é duas colunas.
3. **`RTISOL.pdf` parece ser a 4ª Ed./2022 original, não a "versão corrigida"** (o arquivo
   citado em [[rt-implantacao-sol-cbmrs]] é o publicado em out/2024). Sem marcação de
   "corrigida" na capa. Antes de citar item novo do SOL em CIA, conferir contra o PDF do link
   ou pedir o arquivo corrigido ao usuário.
4. **Nome do arquivo não é fonte.** A versão sai da **capa e do Art. 2º**, sempre — foi assim
   que se pegou o item 1 e a data de 19/09/2022.
5. **`IN45.pdf` é coluna única e só 3 páginas** — `-layout` funciona bem nele. Não confundir o
   número da IN com item de norma: é **Instrução Normativa 045/2023**, com artigos e incisos
   romanos, não uma RT.

## O que NÃO está na pasta (11/09/2026)

Precisa de anexo do usuário ou de outra fonte:

- **LC 14.376/2013** — e o índice já registra que o PDF acessível está consolidado só até a
  LC 14.924/2016.
- **RT 05 Parte 06/2025** (fiscalização) · **RT 05 Parte 08/2016** (simbologia)
- **RT 09/2025** (CMAR) · **RT 13/2025** (iluminação) · **RT 15 Parte 01/2023** (brigada) ·
  **RT 16/2017** (hidrante urbano)
- RT 03/2016 e as RTs de ocupações específicas (20, 21, 22, 23, 31, 32)
- **IN 025/2020** (corredor enclausurado, revogada — mas é a aplicável a PPCI protocolado até
  26/04/2023) e **IN 056/2024** (câmaras frigoríficas/amônia)

📌 **RT 13/2025 (iluminação) é a mais sentida das que faltam** — é medida corrente no campo 4
e o doc dela no projeto não tem item transcrito.

✅ **RT 18/2025 entrou em 09/09/2026** e o erro de citação registrado (8.1 "a" × 8.3) está
agora conferido no PDF em mãos, com dois itens novos que faltavam: **8.2.4** (ático de casa de
máquinas/reservatório — acionador *recomendado*) e **9.4.1/9.4.2**.

✅ **IN 045/2023 entrou em 11/09/2026** — íntegra transcrita em
[[in-045-2023-corredor-enclausurado]]: Art. 1º (incisos I a XVI, §§ 1º e 2º) e Arts. 2º a 7º.
Na mesma leitura foi conferido o **item 5.12.1.2 da RT 11**, que é o regime do corredor de
**descarga** — o Art. 6º da IN exclui esse caso.

## Sincronizar

Ao mudar esta lista, mudar também a coluna de PDF local em [[00-indice-normativo]] e o campo
`pdf_local` de `scripts/dados/indice_normas.json`.
