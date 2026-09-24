---
name: "ppci-incorporar-norma"
description: "Incorporar norma nova (RT, IN, IT, decreto) à base do projeto SSEG: PDF, conversão anydoc, transcrição comentada e todos os índices e arquivos dependentes, com gravação no projeto e no clone do repositório."
---

# Incorporar norma nova à base do SSEG

Use quando o usuário pedir para "adicionar a IN/RT/IT X na base", "fazer o praxe do anydoc" ou algo parecido. Faça o roteiro inteiro sem pedir confirmação a cada passo.

## 0. Onde está a verdade

- **O canônico são os docs do Projeto** (lidos com `project_read`). O clone do PC (`C:\Users\55519\Desktop\Carpes\SSEG`) e o GitHub costumam estar atrasados. Nunca use a cópia do clone como base para editar um doc que já existe no projeto.
- Peça acesso à pasta `C:\Users\55519\Desktop\Carpes` (uma vez, a pasta-mãe) se a sessão ainda não tiver.

## 1. Obter o PDF

1. Veja se já está em `Carpes\Normas` (`device_list_dir`).
2. Se não estiver: achar a URL com WebFetch na página de listagem do CBMRS (ex.: `bombeiros.rs.gov.br/instrucoes-normativas`). **Só a URL**: o texto que o WebFetch devolve de PDF não serve, porque resume e já inventou tabela.
3. `curl`/`wget` estão bloqueados pelo proxy (403), e download pelo navegador do app não grava arquivo. **Peça ao usuário para salvar o PDF em `Carpes\Normas`** com nome curto no padrão da pasta (`IN66.pdf`, `RT13.pdf`).
4. `device_stage_files` do PDF. A versão sai da **capa e do artigo de vigência**, nunca do nome do arquivo.

## 2. Converter com o anydoc (no Cowork)

```bash
pip install --break-system-packages -q firecrawl-anydoc==0.2.4   # mesma versão do PC
# stage de Carpes\RECURSOS\ferramentas-ia\anydoc_cli.py
python3 anydoc_cli.py <arquivo>.pdf -o <arquivo>.md
```

- Código de saída: 0 ok · 1 falha · 2 uso errado · 3 PDF escaneado (avisar quais páginas pedem OCR; nunca usar OCR online).
- Versão do repo (`sseg/normas/md/`): prefixar o **cabeçalho de aviso** "ARQUIVO GERADO POR EXTRACAO AUTOMATICA (anydoc) - NAO E FONTE DE FUNDAMENTO", copiado de um `.md` já existente em `md/` (ex.: `IN45.md`).
- Versão local (`Carpes\Normas\_md\`): a mesma conversão, sem cabeçalho.
- Registrar onde o anydoc embaralhou (tabelas falsas `|...|`, títulos errados).

## 3. Ler e conferir o texto

- Coluna única: `pdftotext -layout <pdf> - | tr -d '\f'`. Duas colunas: `pdftotext` **sem** `-layout`. Tabela em imagem: `pdftoppm -r 110 -png` e ler a imagem.
- Ler o texto **inteiro**. Conferir identificação (número, ementa, quem assina, DOE, data de vigência, cláusula revogatória) e todo dispositivo que for transcrito.
- Se a norma remete a item de outra norma (ex.: "item 5.4.1.2.2 da RT 11"), conferir esse item no PDF também.
- Verificar na listagem oficial se há norma **posterior sobre o mesmo tema** (pode revogar ou conversar com esta). Se o PDF dela não estiver em mãos, marcar como não conferida.

## 4. Arquivos a criar ou atualizar (todos, na mesma sessão)

| # | Arquivo | O que muda |
|---|---|---|
| 1 | `sseg/normas/pdf/<ARQ>.pdf` | PDF novo |
| 2 | `sseg/normas/md/<ARQ>.md` + `Carpes\Normas\_md\<ARQ>.md` | conversões anydoc |
| 3 | `normas/<sigla-num-ano-assunto>.md` (novo) | transcrição comentada: identificação, texto conferido, quadro de aplicação, relação com a norma complementada, **aparentes conflitos nomeados**, armadilhas (vigência por protocolo, condições, faculdade × obrigação), reflexo na análise (campo 4, planta, CIA), notas sobre a conversão anydoc |
| 4 | `normas/00-indice-normativo.md` | linha "Última verificação"; contagem de PDFs na tabela de camadas; linha em **Datas de transição**; linha na tabela da categoria (RTs, Instruções Normativas, etc.); pendências novas; linha ✅ em Próximos passos |
| 5 | `workflow/pasta-normas-local.md` | cabeçalho de datas; linha no **Inventário**; armadilha de extração, se houver; "O que NÃO está na pasta"; linha ✅ |
| 6 | `scripts/dados/indice_normas.json` | `_atualizado_em`; contagem de PDFs em `_onde_estao_as_normas`; entrada em `normas` (titulo, vigente_desde, publicada_em, complementa, conferido_em, obs); se for citável no campo 4, apelido em `medida_para_norma` |
| 7 | doc da norma complementada (ex.: `normas/rt-11-...md`) | seção do item complementado + remissão cruzada |
| 8 | `normas/fontes-subsidiarias-outros-estados-e-instrucoes.md` | resumo curto, se for IN ou IT |
| 9 | `sseg/normas/README.md` (só no repo) | contagem de PDFs, se citada |

Depois de mexer no JSON: `python3 -c "import json; json.load(open(...))"`. Se adicionar apelido em `medida_para_norma`, conferir no `_canon_norma` do `scripts/sseg.py` se a citação por extenso casa, e registrar o que acontece.

## 5. Gravar

1. **Projeto:** `project_write` com `local_path` (arquivo dentro do diretório de trabalho) para cada doc de `normas/`, `workflow/` e `scripts/dados/`. PDFs e `md/` não vão como doc do projeto.
2. **PC:** copiar para `/mnt/user-data/outputs/...` e `device_commit_files` para o clone (`Carpes\SSEG\sseg\...`) e para `Carpes\Normas\_md\`.
3. **Push:** é do PC, no PowerShell (o proxy do Cowork recusa o push):

```powershell
cd C:\Users\55519\Desktop\Carpes\SSEG
git pull
git add -A
git commit -m "Normas: <norma> incorporada (PDF, md, transcricao, indices)"
git push
```

Se o clone estiver atrasado, pedir o `git pull` **antes** de gravar nele, para o pull não recusar por alteração local.

## 6. Fora do alcance da IA: avisar o usuário

- **Instruções do Projeto** citam a contagem de PDFs em `normas/pdf/`. Atualizar na interface do Projeto e no espelho `workflow/instrucoes-projeto-espelho.md`.

## 7. Resposta final

Entregável no topo: o que entrou (norma, vigência, doc criado) e o comando de push. Depois, em bloco separado: pendências (norma relacionada não conferida, portaria ausente, conflito aparente) e onde o anydoc falhou. Sem narrar o progresso.