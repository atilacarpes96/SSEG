---
name: ferramentas-locais-anydoc-skillspector
description: Ferramentas de IA instaladas no PC do quartel em 14/09/2026 — anydoc (documento → Markdown, 100% local), skillspector (scanner de segurança de skills) e a pasta Normas\_md como índice de busca. Caminhos, comandos, códigos de saída, o que cada teste mostrou e onde NÃO confiar na saída
sources: [cowork]
---

# Ferramentas locais — anydoc e skillspector

> Instaladas em **14/09/2026** no PC do quartel (`pc-carpes`), offline, sem direito de
> administrador, com Python 3.12 portátil próprio. Complementa [[pasta-normas-local]].

## Onde ficam

| O quê | Caminho |
|---|---|
| Raiz das ferramentas | `C:\Users\55519\Desktop\Carpes\RECURSOS\ferramentas-ia` |
| Executáveis no PATH do usuário | `...\ferramentas-ia\bin` (`anydoc`, `skillspector`) |
| Skills do Claude Code | `C:\Users\55519\.claude\skills` — `convert-documents-to-markdown`, `no-ai-slop` |
| Índice de normas em Markdown | `C:\Users\55519\Desktop\Carpes\Normas\_md\` |

⚠️ Terminal aberto **antes** da instalação não enxerga o PATH novo — reiniciar o app ou
recarregar o PATH na sessão.

## anydoc — documento em Markdown, 100% local

```
anydoc <arquivo> -o saida.md     # grava
anydoc <arquivo>                 # imprime na tela
```

Aceita PDF, DOC/DOCX, ODT, RTF, XLS/XLSX/ODS, CSV, PPT/PPTX/ODP, EPUB.

**Códigos de saída:** `0` ok · `1` falha · `2` uso errado · `3` PDF com página escaneada —
recusa o arquivo inteiro e lista as páginas que precisam de OCR (caso conhecido: RT 05 Parte
04a, 18 de 108 páginas).

### Onde serve

- **Texto corrido de norma** que só existe em PDF — converter com `-o` e ler só o trecho
  necessário, nunca carregar a norma inteira no contexto.
- **Localizar item/artigo/decreto por número exato** na pasta `Normas\_md\`.
- **Tabela nativa de ODT** (testado no `Relatório ANALISE F7.odt`): texto e estrutura saem
  corretos.

### 🚫 Onde NÃO confiar

1. **Hierarquia de títulos.** Testado na RT CBMRS 02: código 0, texto completo, acentos
   certos — mas **muitas linhas comuns viram `##`**. Localizar por texto ("Art.", "5.1.2"),
   nunca pela estrutura de títulos.
2. **Tabela de exigências em PDF** (RT 05 P07, Anexo B do Decreto): **não é confiável** —
   colunas se desalinham, expoente de nota se solta do X, a tabela vira texto corrido. A
   contagem de medidas continua saindo do banco validado ou da **imagem da tabela**, lida
   célula a célula. Isso não muda a trava de erro nº 2 do projeto.
3. **Busca por conceito.** `Normas\_md\` é índice **literal**: acha o que está escrito com
   aquela palavra exata. Termo que a norma não usa não aparece — a ausência no índice não
   prova a ausência na norma.
4. **Checkbox de ODT.** O marcador de lista `□` do Writer vira `•` na conversão. **Status de
   caixa marcada nunca sai do `.md`** — conferir no arquivo original.
5. **Item extraído continua provisório.** Vale a regra geral do projeto: conferir no PDF
   oficial antes de citar em CIA.

### Regra fixa de privacidade

**Nenhum documento de PPCI** (processo, notificação, dado de cliente) sai da máquina. **Nunca**
usar OCR online (`--ocr hosted`, Firecrawl) — esta versão instalada nem tem a opção. Dando
código 3, avisar quais páginas precisam de OCR e deixar a decisão com o analista.

## skillspector (NVIDIA) — scanner de segurança de skills

```
skillspector scan <pasta> --no-llm
```

Rodar **antes de instalar qualquer skill nova** de terceiro. Avisos de
`required API key is missing` são normais com `--no-llm`. O `no-ai-slop` foi testado:
**0/100, SAFE**.

## Pasta `Normas\_md\`

Todas as normas da pasta `Carpes\Normas` convertidas com o anydoc, como índice de busca
permanente. Os **PDFs originais continuam intactos** e seguem sendo a fonte para citação —
ver [[pasta-normas-local]]. Ao acrescentar uma norma à pasta, converter também para `_md\`.
