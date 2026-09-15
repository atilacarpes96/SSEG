# `sseg/normas/` — as três camadas, e o que cada uma pode fundamentar

Esta pasta tem três coisas diferentes. Confundi-las já custou exigência indevida, então a
regra está aqui em cima.

| Camada | Onde | Serve para | **Não** serve para |
|---|---|---|---|
| **PDF oficial** | `pdf/` | **citar em CIA** — é a letra fria da norma | — |
| **Conversão automática** | `md/` | **localizar** item, artigo, palavra | fundamentar exigência |
| **Transcrição comentada** | os `.md` desta pasta | raciocínio, travas, itens já conferidos | substituir o PDF na conferência |

## `pdf/` — os 14 PDFs oficiais

Cópia da pasta local `C:\Users\55519\Desktop\Carpes\Normas`, para que as normas viajem junto
com o repositório em vez de ficarem só numa máquina. **A versão sai da capa e do Art. 2º**,
nunca do nome do arquivo — o inventário conferido arquivo a arquivo está em
`../workflow/pasta-normas-local.md`, com as armadilhas de cada um.

Duas que se repetem e derrubam análise:

- **`RTISOL.pdf` não é "isolamento de riscos"** — é a RT de Implantação do SOL. Isolamento de
  riscos é o `RT CBMRS 04`.
- **Arquivos de duas colunas** (`RTISOL`, `RT18` e o corpo da `RT11`): `pdftotext -layout`
  intercala as colunas e embaralha a ordem dos itens. Nesses, `pdftotext` **sem** `-layout`
  para texto; `-layout` só nas tabelas dos anexos. Se a numeração sair fora de ordem, é
  duas colunas.

Leitura: `pdftotext -layout <arquivo>.pdf - | tr -d '\f'` — o form feed sai **antes** de
qualquer `grep "TABELA"`, senão a tabela "não existe".

## `md/` — conversão do anydoc, índice de busca

Gerada com `anydoc <arquivo> -o <saida>.md`, 100% local. Existe para achar "5.12.1.2" ou
"Art. 31" sem carregar a norma inteira no contexto.

🚫 **Onde não confiar** (testado — ver `../workflow/ferramentas-locais-anydoc-skillspector.md`):

1. **Hierarquia de títulos** — linhas comuns viram `##`. Localizar por texto, nunca pela
   estrutura.
2. **Tabela de exigências** — colunas se desalinham e o expoente da nota se solta do X. A
   contagem de medidas continua saindo da **imagem da tabela**, lida célula a célula, ou do
   `../scripts/dados/tabelas_conferidas.json`.
3. **Busca é literal** — termo que a norma não usa não aparece. Ausência no índice não prova
   ausência na norma.

**Item obtido daqui é provisório:** sinalizar como tal e conferir no PDF de `pdf/` antes de
citar em CIA.

## Sincronizar

Acrescentando uma norma: o PDF entra em `pdf/`, a conversão em `md/` (`anydoc`), e a linha
correspondente muda em `00-indice-normativo.md`, em `../workflow/pasta-normas-local.md` e no
campo `pdf_local` de `../scripts/dados/indice_normas.json`.
