# normas/base — normas convertidas e verificadas

Markdown das 19 normas de `normas/pdf/`, gerado por `scripts/normas_converter.py` e conferido contra o PDF por `scripts/normas_verificador.py` (02/10/2026). Resultado por norma em `verificacao.json`.

O texto segue a ordem do PDF. Cada página começa com `<!-- pág N -->`, e o número de página é a posição no arquivo, não o número impresso. Item numerado vem em **negrito**, texto riscado (revogado) vem entre `~~ ~~` e expoente de nota sai como X¹. Figuras e células desenhadas viram imagens em `img/`, com o texto da figura em comentário.

## As 6 checagens do verificador
1. Mesmas palavras do PDF (PyMuPDF), descontados cabeçalho e rodapé repetidos.
2. Mesmo número de X e traços por página.
3. Itens em sequência válida, e todo item do PDF presente.
4. Cada parágrafo é um trecho contínuo do PDF (referências: pdftotext e leitura geométrica).
5. Riscado igual ao do pymupdf4llm (detector independente).
6. Nenhuma página com tinta sem texto (glifo vetorial ou imagem) sem figura no md.

## Resultado: 17 de 19 passam nas 6
- **Lei Complementar 14.376** e **RT 05 Parte 1.1**: só a checagem 4 acusa. É lista ou campo de formulário que o conversor juntou num parágrafo. Conferi na imagem: nenhuma palavra perdida, ordem correta.
- **Páginas com tabela girada** (RT 05 Parte 1.1, págs. 44–48, Anexo L): a checagem 4 não se aplica. O texto está todo lá, mas a estrutura das colunas só existe na imagem da página inteira, que vai no md.

## Cuidados
- Célula marcada "célula sem texto no PDF — ver imagem": o conteúdo existe só como desenho, por exemplo o X¹ da Tabela 6F.3 do Decreto, pág. 80. Abra a imagem.
- Conversão nova: rodar os dois scripts e só aceitar com `APROVADO: true` ou com a falha conferida na imagem.
