# normas/base — normas convertidas e verificadas

Markdown das 22 normas de `normas/pdf/`, gerado por `scripts/normas_converter.py` e conferido contra o PDF por `scripts/normas_verificador.py` (02/10/2026). Resultado por norma em `verificacao.json`.

O texto segue a ordem do PDF. Cada página começa com `<!-- pág N -->`, e o número de página é a posição no arquivo, não o número impresso. Item numerado vem em **negrito**, texto riscado (revogado) vem entre `~~ ~~` e expoente de nota sai como X¹. Figuras e células desenhadas viram imagens em `img/`, com o texto da figura em comentário.

## As 6 checagens do verificador
1. Mesmas palavras do PDF (PyMuPDF), descontados cabeçalho e rodapé repetidos.
2. Mesmo número de X e traços por página.
3. Itens em sequência válida, e todo item do PDF presente.
4. Cada parágrafo é um trecho contínuo do PDF (referências: pdftotext e leitura geométrica).
5. Riscado igual ao do pymupdf4llm (detector independente).
6. Nenhuma página com tinta sem texto (glifo vetorial ou imagem) sem figura no md.

## Resultado: 19 de 22 passam nas 6
- **IT 25 Parte 4** (03/11/2026): APROVADO nas 6. V3 mostra "saltos" porque a numeração da Parte 4 começa no item 33, e números como "3.000" e "4.200" no começo de linha parecem itens. As Tabelas 4.A1, 4.A2 e 4.B2 só existem como imagem (págs. 20–21). A transcrição conferida está em `normas/it-25-2025-parte4-armazenamento-fracionado.md`.
- **RT 22** (29/10/2026): APROVADO nas 6. A Tabela 1 do Anexo A sai em linhas partidas (nome da medida em duas linhas): a transcrição conferida está em `normas/rt-22-2023-silos-armazens-graneleiros.md`.
- **RT 05 Parte 08** (16/10/2026): V3 conta o sumário como item e V4 acusa o cabeçalho da pág. 3. Conferido na imagem; os 5.2 e 5.3 tinham "Anexo" partido em parágrafo novo, juntado à mão.
- **Lei Complementar 14.376** e **RT 05 Parte 1.1**: só a checagem 4 acusa. É lista ou campo de formulário que o conversor juntou num parágrafo. Conferi na imagem: nenhuma palavra perdida, ordem correta.
- **Páginas com tabela girada** (RT 05 Parte 1.1, págs. 44–48, Anexo L): a checagem 4 não se aplica. O texto está todo lá, mas a estrutura das colunas só existe na imagem da página inteira, que vai no md.

## Cuidados
- Célula marcada "célula sem texto no PDF — ver imagem": o conteúdo existe só como desenho, por exemplo o X¹ da Tabela 6F.3 do Decreto, pág. 80. Abra a imagem.
- Conversão nova: rodar os dois scripts e só aceitar com `APROVADO: true` ou com a falha conferida na imagem.
