---
name: pasta-print-ppci-local
description: A pasta local "print ppci" no PC do usuário — caminho, estrutura, convenção de nomes dos arquivos por análise, para que serve, o que a página do SOL registra e a limitação de exclusão de arquivos
sources: [cowork]
---

# Pasta local "print ppci" — histórico do memorial por processo

> A **rotina** de arquivamento e comparação vive na skill `ppci-analise-processo`; a
> geração do PDF da página, na skill `sol-cbmrs-navegador`. Este doc é o **fato do setup**.

## Caminho

`C:\Users\55519\Desktop\Carpes\print ppci\`

No PC do usuário — não sincronizado neste projeto. Acesso via device bridge quando o PC
estiver conectado.

## Estrutura e nomes

- Uma subpasta por processo, nomeada com o número do processo no SOL (ex.: `A00049589AA001`).
- **`N.pdf`** = cópia da página da Nª Análise (`1.pdf` = 1ª Análise, `2.pdf` = 2ª Análise…).
  O número reflete o rótulo "Nª Análise" que aparece no próprio print, **não** a ordem de
  criação — pasta nova cujo primeiro arquivo já é a 2ª Análise vai como `2.pdf`.
- **`CIA N.pdf`** = Comunicação de Inconformidade gerada naquela análise (padrão adotado em
  01/09/2026; o usuário pode preferir `<processo> CIA.pdf` — confirmar).
- **`N.json`** = registro estruturado da análise, gerado junto com o PDF (padrão novo). É o
  que permite comparar análises sem reler o memorial inteiro.
- Algumas subpastas também guardam PDFs de normas/leis citadas naquele processo.

## Para que serve

É **controle interno**: saber **se o RT alterou algo no memorial de uma análise para a
outra**. Por isso o valor está em ter uma cópia por análise, sempre com os mesmos campos,
permitindo comparação direta.

## O que a página do SOL registra

Página "Análise técnica do licenciamento"
(`solcbm.rs.gov.br/solcbm/adm/#/analise-tecnica/<id>`): identificação dos envolvidos;
localização; características (tipo de edificação, ocupações com carga de incêndio e marcação
de subsolo, áreas, pavimentos, alturas, população, característica construtiva); medidas de
segurança (medida, norma, inviabilidade técnica, compartimentação); riscos específicos;
elementos gráficos; termo de responsabilidade; pagamentos; demais inconformidades. Cada item
traz seu status **Analisar / Aprovado / Reprovado**.

No painel lateral aparece o número da análise, dias em análise/restantes e — a partir da 2ª —
"Última CIA" e "Última análise por [analista]".

⚠️ Os **textos das inconformidades não aparecem** na cópia da página: ficam na caixa
"Especificar" de cada item (ver [[sol-catalogo-inconformidades-modal]]) e só são impressos
na CIA. Por isso arquivar sempre os dois.

## Limitação de acesso

A pasta não está no GitHub sincronizado do projeto. Não há ferramenta de exclusão no PC do
usuário nesta sessão: se um PDF for salvo solto fora da pasta do processo, o arquivo antigo
permanece após a cópia para o lugar certo — **a exclusão é manual**.
