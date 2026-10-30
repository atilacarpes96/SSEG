---
name: atualizacoes
description: O que mudou no SSEG, data a data, e o prompt pronto para cada analista colar no próprio Claude e atualizar o seu lado (skills da conta, campo Instruções, modelo de cada conversa). É a aba Atualizações do Painel SSEG.
---

# Atualizações do SSEG

Uma entrada por leva de mudanças, a mais nova em cima. Cada entrada traz **o que mudou**, em
poucas linhas, e o **prompt para atualizar**: o analista copia e cola numa conversa nova do
próprio Claude, dentro do projeto SSEG (Cowork ou Claude Code), e o Claude faz o resto com ele.

Formato, que o `scripts/painel.py` lê: título `## DD/MM/AAAA — assunto`, o texto do que mudou
e o subtítulo `### Prompt para atualizar` seguido de um bloco de código com o prompt.

## 30/10/2026 — SSEG.exe 2.7.12: Lançar no SOL — "Geral" e "Adicionar correções"

- `sol_lancar.py`: "Geral"/população/campo 3 → Característica geral; medida que não casa com o campo 4 → item `MEDIDA_SEGURANCA_OUTRA` (botão "Adicionar correções", id da especSeguranca, opções `analise.medidas.outros`, lido do código do SOL em 30/10/2026). `api.py`: lançamentos para o mesmo item do SOL são juntados num texto só.

### Prompt para atualizar

```text
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 30/10/2026 — check: linha transcrita da tabela cruzada com o campo 4

- `sseg.py check`/`travas` (e a pré-análise): sem linha conferida em `tabelas_conferidas.json`, cruza a linha **transcrita** do PDF com o campo 4. Medida exigida ausente vira erro; célula com nota vira atenção ("aplicar a nota"); medida do campo 4 fora da linha, atenção. Antes, nesse caso, só dizia "linha não conferida — não dá para cruzar", e uma medida exigida que faltava no campo 4 passou por 4 análises. Pré-análises da caixa refeitas no servidor em 30/10/2026.

### Prompt para atualizar

```text
Atualize o SSEG desta pasta pelo chip GitHub (git pull). Nada a instalar na conta.
```

## 30/10/2026 — SSEG.exe 2.7.11: processo redistribuído e concluído sai da caixa

- `porta.py` e `api.py`: processo que saiu da caixa do SOL depois da distribuição da planilha ao outro analista (`sol-caixa.json` com `saiu_em` e `lido_em` ≥ `distribuido`) continua de quem estava com ele; desce como concluído.

### Prompt para atualizar

```text
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 30/10/2026 — SSEG.exe 2.7.10: botão "Processo concluído" e Início atualizado ao concluir

- Concluir processo grava `conclusao` (data, CIA/CA, nº da análise dos Marcos) em `analise.json`; o botão fica azul, "✓ Processo concluído", até chegar análise nova. Ao concluir, o programa roda o Atualizar do Início.

### Prompt para atualizar

```text
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 30/10/2026 — SSEG.exe 2.7.9: processo redistribuído no SOL desce para quem está com ele

- `porta.py`: o que está na última leitura da caixa do SOL do servidor (`.caixa/caixa.json`) é do admin, mesmo com a planilha dando o processo a outro. `api.py`: na lista, processo da minha caixa do SOL é meu e a distribuição do outro analista (prazo e tipo) não conta.

### Prompt para atualizar

```text
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 30/10/2026 — SSEG.exe 2.7.8: nº da análise para processo fora da planilha

- Lista do Início: sem `distribuicao.json`, a etiqueta "Nª análise" sai de `marcos-resumo.json` (campo `analise`).

### Prompt para atualizar

```text
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 30/10/2026 — SSEG.exe 2.7.7: conflito PC × servidor mostra o mais novo e o que muda

- `sincronizar.py --json` passa a trazer, para cada conflito, a hora de gravação dos dois lados, o lado mais novo e as diferenças (JSON campo a campo; texto linha a linha). A cópia do servidor vem só para comparar; nada é gravado até a escolha. O aviso do chip cita o arquivo.

### Prompt para atualizar

```text
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 30/10/2026 — SSEG.exe 2.7.6: PDF da RT de Implantação do SOL, da RT 22 e da RT 05 Parte 08

- Bloco de norma do chat: "Não achei o PDF" para "RT de Implantação do SOL-CBMRS" (citada sem número), RT 22 e RT 05 Parte 08, com os PDFs em `normas/pdf/`. O mapa de `app/busca.py` passou a reconhecer as três.

### Prompt para atualizar

```text
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 29/10/2026 — SSEG.exe 2.7.5: "Fora do prazo" só para o que está na caixa

- Card "Fora do prazo" e etiqueta da lista: concluído (CA ou CIA lançado) não conta mais; só processo na caixa com o prazo vencido. A 2.7.4 (fim de semana → segunda) foi desfeita: prazo = distribuído + 10 dias corridos.

### Prompt para atualizar

```text
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 29/10/2026 — SSEG.exe 2.7.4: prazo da caixa no fim de semana vai para a segunda

- `estado_caixa` (app/api.py): distribuído + 10 dias corridos; caindo em sábado ou domingo, vence na segunda. Feriado não entra.

### Prompt para atualizar

```text
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 29/10/2026 — SSEG.exe 2.7.3: o Claude descarta o próprio rascunho errado

- **Novo comando:** `sseg.py analise --pasta <processo> descartar e2` tira da coluna CIA um rascunho sem texto final salvo. Item salvo pelo analista não sai (quem exclui é ele, no botão "excluir"). As instruções do chat do SSEG.exe já mandam usar.

### Prompt para atualizar

```text
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 29/10/2026 — SSEG.exe 2.7.2: respostas do checklist e das perguntas do chat

- **Checklist:** a resposta escrita na pendência vai ao Claude com Enter ou pelo botão "Mandar N resposta(s)", que aparece enquanto você digita.
- **Perguntas do chat:** não mandam mais sozinhas no último clique; cada pergunta aceita complemento escrito, há observação geral e o botão "Mandar respostas".

### Prompt para atualizar

```text
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 29/10/2026 — RT 22/2023 (silos e armazéns graneleiros) na base

- **RT 22/2023** (M-5; vigente desde 29/10/2023; revogou a RT 22/2017) em `normas/pdf/RT22.pdf`, com conversão verificada e a transcrição comentada `normas/rt-22-2023-silos-armazens-graneleiros.md`: Tabela 1 do Anexo A lida na imagem (19 medidas, iguais nos três tipos de unidade), Anexo B das medidas próprias do M-5 e o 6.1.1.1 (essas medidas são marcadas no campo 4, não desenhadas).
- **Instruções:** a contagem de PDFs em "Onde procurar primeiro" passa a 21 e a RT22 entra na lista de arquivos de duas colunas.

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão de 29/10/2026 e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você.
2. Me entregue, num bloco único para copiar, o texto entre os marcadores INÍCIO e FIM de sseg/workflow/instrucoes-projeto-espelho.md, para eu colar no campo Instruções do projeto no lugar do texto inteiro.
3. Se eu tiver a pasta Carpes\Normas no PC, copie para ela o sseg/normas/pdf/RT22.pdf e, para Carpes\Normas\_md\, o sseg/normas/base/RT22.md com as imagens RT22-* de base/img.
```

## 28/10/2026 — SSEG.exe 2.7.1: voltar/avançar, Memorial SSEG e caixa da Conversa

- Topo do app com ← → ⟳ (histórico das páginas, Alt+setas e botões do mouse). Na página do processo, "Memorial SOL" sai e entra "Memorial SSEG", que abre a ficha da aba Processos. O print do memorial do SOL fica só na pasta, um por análise. Pedido do Átila.
- Corrige a caixa de mensagem da Conversa estreita: as classes do gráfico de colunas da 2.7.0 batiam com as da janela do processo.

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 28/10/2026 — SSEG.exe 2.7.0: base do SOL em banco SQL, aba Processos com mapa e ficha, pré-análise antes da caixa

- Servidor: `sol_base.py` volta a coletar laudos e vistoria (`informacoes-processo`), preenche os Marcos de todas as pastas de `processos/` (474 de 486) e faz a pré-análise dos distribuídos que ainda não chegaram à caixa (`base-api-<ID>.json`). No fim de cada coleta, `sol_banco.py` monta o `solcbm.db` no formato da Consulta SOLCBM do Sgt Magalhães; `sol_consulta.py` responde por script (zero token), e o `porta.py banco` serve ao SSEG.exe.
- SSEG.exe 2.7.0: aba Processos com Painel (mapa e gráficos), Lista com mapa, Ficha completa do processo e Busca nas CIAs. Pedido do Átila; desenho do Sgt Magalhães.
- `CLAUDE.md`: o Claude consulta a base por `sol_consulta.py`, sem abrir os JSON. Explicação etapa por etapa em `workflow/base-do-sol-e-aba-processos.md`.

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão" e faça git pull no clone. Nada a instalar na conta.
```

## 27/10/2026 — SSEG.exe 2.6.17: lançar no SOL com script do clone atrasado

- `api._sol_lancar()`: se o `sol_lancar.py` do clone não tem o parâmetro que o .exe chama, faz `git_sinc.trazer` e recarrega; sem pull, pede "Sincronizar com o GitHub". Relato do Átila: o .exe 2.6.16 chegou antes do pull horário do clone.

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 27/10/2026 — SSEG.exe 2.6.16: sem notificação, aprovar tudo inclui os Reprovados

- `sol_lancar.a_aprovar/aprovar_restantes(..., reprovados=True)` quando não há nenhuma exigência salva: o Reprovado também vira Aprovado (com `justificativas: []`). Rascunho sem texto salvo deixa de bloquear o "aprovar tudo" (só avisa). Com notificação, nada muda. Pedido do Átila.

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 27/10/2026 — SSEG.exe 2.6.15: característica cai no campo 3 ao lançar

- `sol_lancar.achar`: nome que começa com "Característica" e não casa com nenhum item vai para "Característica geral" (ou "Tipo de edificação" / "Isolamento de risco", quando nomeados). Teste em `testar.py`. Select de medida da exigência ganha os itens fixos do SOL e as pranchas; `chat.py` diz ao Claude os nomes do campo 3. Relato do Átila.

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 27/10/2026 — SSEG.exe 2.6.14: botões da coluna CIA

- Cabeçalho da coluna CIA: "copiar a CIA" vira link pequeno "⧉ copiar" ao lado do título; "revisão final" e "lançar no SOL" viram botões numerados (1 azul contornado, 2 vermelho cheio). Só visual; pedido do Átila.

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 27/10/2026 — SSEG.exe 2.6.13: "Pôr na CIA" só quando o texto não está na coluna

- Bloco `sseg-exigencia` no chat: se o texto (espaços normalizados) já é o rascunho ou o final de alguma exigência, mostra "✓ na CIA, item N"; senão, o botão "Pôr na CIA" (rascunho de item novo). Reavalia a cada recarga do registro. Pedido do Átila: o botão duplicava a exigência que o Claude já tinha gravado com `rascunho`. Instrução do chat (`chat.py`) ajustada.

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 27/10/2026 — SSEG.exe 2.6.12: Concluir processo (CIA/CA), botões do SOL agrupados, prancha na exigência

- Janela do processo: "Guardar memorial" + "Salvar processo" viram **Concluir processo** (modal CIA/CA → `processo_congelar` sem refazer → `processo_salvar(codigo, resultado)`). `sol_snapshot.salvar(..., resultado="CA")` / `porta.py sol-salvar <código> --ca`: confere nos Marcos que a última análise é CA, sem baixar CIA. Os três botões do SOL num grupo com cor por botão. Pré-análise: "ver tudo" vira "Revisar e mandar pro chat".
- Exigência ganha `pranchas` (lista das `elemGraficos` ATIVO, `processo.montar` → `elementos`). No "lançar no SOL", cada prancha marcada vira um grupo com "- Inconformidades já citadas acima." (só a frase padrão, sem listar medidas) (somado ao fim da caixa, se a prancha já tem exigência). Pedido do Átila, 27/10/2026.

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 26/10/2026 — SSEG.exe 2.6.11: prazo da caixa contado como na planilha

- `tagEstado` (web/index.html): a etiqueta da caixa passa de "Prazo 29/10 · 3 dias" para "7 dias · prazo 29/10" (dias corridos desde a distribuição, o número da planilha; depois a data do prazo, "vence hoje" ou "venceu"). Cor sem mudança. Pedido do Átila: o "3 dias" não dizia se era o que faltava ou o que passou.

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 20/10/2026 — SSEG.exe 2.6.10: PPCI só para o seu analista; quadro "Programa" do administrador

- `api.processos()` marca `meu` pelo analista do `distribuicao.json` (última palavra do nome × o analista do PC). Início e Quadro escondem o que não é meu.
- `porta.py`: quadro do Programa em `~/sseg-quadro/programa/`. `quadro` entrega ao admin; `quadro-mexer` com `"onde": "programa"` só admin. Relatos (`porta relato`), gatilhos dos Marcos e falha do login automático (`sol_caixa.py`) vão para lá, não para a seção. Pedido do Átila: "no quadro da seção somente o que for de todos; arrumar o programa fica para o Sd Carpes".

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 20/10/2026 — SSEG.exe 2.6.9: "lançar no SOL" sem CIA aprova tudo, com confirmação

- Sem exigência salva na coluna CIA, o botão "lançar no SOL" lista os itens em "Analisar" (`sol_lancar_aprovar_lista` com notificados vazio), pede confirmação e chama `sol_lancar` só com o aprovar. Exigência com rascunho e sem texto salvo bloqueia. Pedido do Átila.

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 20/10/2026 — SSEG.exe 2.6.8: caixa na ordem da planilha da distribuição

- `distribuicao.py` grava `linha` (posição na aba ANÁLISE). O Início ordena a caixa pela distribuição, depois pela linha, depois pelo protocolo; os "Na caixa do SOL" sem planilha ficam no fim, pelos dias no SOL. Antes a ordem era só pelos dias no SOL (2.3.8/2.5.1). Pedido do Átila com a planilha na mão.

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 20/10/2026 — SSEG.exe 2.6.7: revisão final com Aplicar/Ignorar; revisor sem bloqueio

- Bloco `sseg-revisao` no chat (`chat.GUIA_VISUAL`): uma linha por exigência, com id, veredito ok/corrigir/conferir, problema, fundamento e texto sugerido inteiro. Aplicar chama `api.processo_aplicar_revisao`: troca o `final`, guarda `final_antes_revisao` e marca `revisao`. Ignorar só registra.
- Janela do processo: liberados comandos que só leem (`cat`, `grep`, `head`, `tail`, `ls`, `wc`, `tr`, `pdfinfo`). O agente `revisor-cia` passa a ler com Read e `sseg.py norma --busca/--pagina`, um comando por vez, e entrega por exigência.
- Skill `ppci-revisao-cia`: seção do SSEG.exe atualizada.

### Prompt para atualizar

```
Faça git pull no clone do SSEG. Mudou a skill ppci-revisao-cia (revisão final no SSEG.exe: o analista aplica ou ignora cada sugestão). Rode a skill sseg-sincronizar-skills (ou suba o .zip). Depois atualize o SSEG.exe pelo chip "Nova versão".
```

## 20/10/2026 — SSEG.exe 2.6.6: aprovar o resto no lançamento; revisão final pelo subagente revisor-cia

- **Lançar no SOL** (`sol_lancar.a_aprovar`/`aprovar_restantes`): o que está em "Analisar" e não tem exigência na coluna CIA vira Aprovado, como o botão Aprovar do SOL (`editar-item` com APROVADO). O mapeamento dos itens também mudou:
  - RU e proprietário só entram com procurador (é quando o SOL mostra o botão), e o proprietário usa `idLicenciamentoProprietario`;
  - isolamento de risco só entra quando o RT marcou;
  - no fim, a aba do SOL recarrega.
- **Revisão final:** no SSEG.exe é o subagente `revisor-cia`, na mesma janela, antes de lançar (botão "revisão final"). `sseg.py revisar-cia --pasta` lê as exigências salvas da coluna CIA, sem precisar do PDF. Saiu o fluxo "Revisar CIA" do Início; checklist passo 16 atualizado.
- Skills mudadas: `ppci-revisao-cia` (descrição e seção do SSEG.exe) e `ppci-analise-processo` (lembrete da revisão). Agente `revisor-cia` com a entrada `--pasta`.

### Prompt para atualizar

```
Faça git pull no clone do SSEG. Mudaram as skills ppci-revisao-cia e ppci-analise-processo (revisão final pelo subagente revisor-cia no SSEG.exe). Rode a skill sseg-sincronizar-skills para instalar na minha conta (ou suba os .zip em claude.ai > Configurações > Capacidades > Skills > Substituir). Depois atualize o SSEG.exe pelo chip "Nova versão".
```

## 20/10/2026 — SSEG.exe 2.6.5: "lançar no SOL" pelo programa (sem Claude, sem token)

- Autorizado pelo Átila em 20/10/2026. `scripts/sol_lancar.py` grava no "Outros" de cada item como o botão Reprovar do SOL: `POST /analise-tecnica/editar-item`, com a lista inteira de justificativas (as opções prontas já marcadas ficam). "Demais inconformidades" vai por `PUT …/inconformidade`.
- O formato foi lido do código da própria página do SOL e conferido com leituras reais. Depois de gravar, o programa lê de volta e confere.
- Nunca conclui a análise nem emite a CIA. "Outras medidas" fica de fora: no SOL a ação dela é outra.
- Na janela do processo: coluna CIA → "lançar no SOL" → tela com item, status, texto e avisos → "Lançar os marcados". A exigência fica marcada como lançada.
- Muda o padrão da skill `sol-cbmrs-navegador` só no SSEG.exe: lá, lançar é pelo botão, não pelo navegador do Claude.
- Correção (relato do Sd Carpes, 20/10): `sincronizar.py` não para mais com `PermissionError` quando um arquivo que desce está aberto no Windows; ele fica em `presos` e volta na próxima. Arquivo escondido (`.analise-*.json`, temporário) não sincroniza.

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão". No primeiro uso do "lançar no SOL", lance um item que você ia notificar de qualquer forma e confira na tela do SOL antes de emitir a CIA. Nada a instalar na conta.
```

## 20/10/2026 — SSEG.exe 2.6.4: print do memorial do SOL em cada análise

- `scripts/memorial_sol.py`: do JSON do licenciamento, `memorial SOL <N>.pdf` e `.txt` com tudo o que a página mostra. Inclui a norma de dimensionamento de cada medida, o laudo inteiro e a seção "Dados a verificar" (o que conferir na planta e os pontos `??`/`!!` da pré-análise). Também congela o `licenciamento <N>.json`.
- Roda sozinho uma vez por análise na leitura da caixa (servidor e PC) e no "Guardar memorial". Botão "Memorial SOL" na janela do processo. O `sseg.py resumo` lista os prints, para o Claude comparar a análise anterior com a atual.
- Já gerado para os 11 processos da caixa de 20/10/2026.
- Elementos gráficos (pre_analise.plantas, usado pela pré-análise e pelo print): cada planta sai como nova, mantida, substituída (com o que foi notificado nela) ou **NÃO TROCADA**, quando foi notificada na última CIA e o RT manteve a mesma. Mais a seção "O que mudou desde a análise anterior" (cadastro e campo 4), do `licenciamento <N-1>.json`.

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão". Na janela de um processo da caixa, clique em "Memorial SOL" e confira o print. Nada a instalar na conta.
```

## 20/10/2026 — SSEG.exe 2.6.3: caixa do SOL manda no Início, caixa lida no Chrome de cada analista, "Reportar ao Claude" em todo erro

- **Caixa:** a lista do Início considera "na caixa" o que está na leitura mais recente da caixa do SOL (`sol-caixa.json`), mesmo antes da planilha das 7h47. Caso de 20/10/2026: o Atualizar das 07:47 leu a caixa antes de a planilha gravar os distribuídos do dia 19, e quatro processos sumiram.
- **Analista que não é o administrador:** o Atualizar lê a caixa no Chrome do próprio PC (`scripts/caixa_pc.py`, pela depuração do Chrome DevTools MCP), com JSON, Marcos, CIA anterior e pré-análise. Resolve a caixa do Sgt Magalhães, que só mudava pela planilha e ficava sem razão social.
- **Sincronizar:** arquivo gerado pelo SOL ou pela planilha que mudou dos dois lados desce do servidor sem virar conflito; conflito não segura mais o Atualizar.
- **Erros:** todo aviso de erro traz "Reportar ao Claude" (relato com erro, print e registro; vai ao servidor e vira cartão no Quadro). Ajuda → Meus relatos mostra o andamento.
- **Instalação:** passo do Chrome confere se há Chrome e a versão (144+), endereço copiado para colar, erro com "Tentar de novo", pedido de acesso pelo WhatsApp e a tela avança sozinha quando o administrador libera.
- **Saíram** o atalho "Abrir SOL", o Tampermonkey (`ferramentas/sol-entrar`) e a dependência da extensão Claude in Chrome no programa.

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão". Depois: Configuração → Chrome para o Claude deve estar todo verde (se não, a tela Instalação mostra o passo). Abra o SOL no Chrome, entre, e clique em Atualizar no Início: a sua caixa do SOL tem de aparecer com a razão social. Se tiver o atalho "Abrir SOL" na Área de Trabalho, pode apagar. Nada a instalar na conta.
```

## 19/10/2026 — SSEG.exe 2.6.2: janelas do programa usam a skill do clone, não a da conta

- `chat.py`: a janela do processo passa a apontar `sseg/skills/ppci-analise-processo/SKILL.md`; as janelas de fluxo, o SKILL.md do clone. As duas proíbem as skills da conta (`anthropic-skills:ppci-*` etc.), que só mudam com o upload do .zip.
- Consequência: dentro do SSEG.exe, skill nova vale na próxima rodada de hora em hora, sem upload. O .zip na conta continua só para o claude.ai (site, app, Cowork).

### Prompt para atualizar

```
Atualize o SSEG.exe pelo chip "Nova versão". Nada a instalar na conta.
```

## 19/10/2026 — SSEG.exe 2.6.1 e skill ppci-analise-processo: perguntas com botão, sem pedir licença para ler

Feito depois de revisar o registro das 7 análises de 16 a 19/10 (`analise.json`: 83 a 261 mil tokens; até 23 pendências numa análise, um terço repetida; perguntas sobre o que já estava na pasta).

- **SSEG.exe:** o bloco `sseg-perguntas` aceita `"tipo": "simnao"` e `"opcoes"`; o clique responde e, com o bloco todo marcado, manda sozinho com "Siga.". `"titulo": "Conferir na planta"` agrupa o que é para olhar na planta. Conversa nova de processo recebe o `sseg.py resumo` junto da 1ª mensagem. "Salvar processo" lista as pendências abertas.
- **Skill `ppci-analise-processo`** (seção "Na janela do processo"): perguntas fechadas com botão, um bloco só para a planta, não pedir licença para ler nem para marcar passo, não refazer o resumo.

### Prompt para atualizar

```
Faça git pull no clone do SSEG. Mudou a skill ppci-analise-processo (seção "Na janela do processo do SSEG.exe": perguntas com botão Sim/Não, "Conferir na planta" num bloco só, não pedir licença para ler nem para marcar passo). Rode a skill sseg-sincronizar-skills para instalar a versão nova na minha conta (ou suba o .zip em claude.ai > Configurações > Capacidades > Skills > Substituir). Depois atualize o SSEG.exe pelo chip "Nova versão".
```

## 19/10/2026 — SSEG.exe 2.6.0: Guardar memorial e Salvar processo

- Janela do processo: **Guardar memorial** (`porta.py sol-congelar` → `sol_snapshot.py congelar`: `memorial N.pdf` e `licenciamento N.json`, N = análise em andamento nos Marcos) e **Salvar processo** (`sol-salvar`: baixa a CIA, grava `CIA N.pdf` sem sobrescrever, sincroniza). Só leitura do SOL; só o administrador (a sessão do SOL é dele).
- Os nomes já estavam na lista do `enviar.py`: sobem ao servidor e descem ao PC. As plantas (R00-….pdf) continuam fora.

### Prompt para atualizar

```
Faça git pull no clone do SSEG (e no clone do servidor, se houver). Só código do SSEG.exe e dos scripts do servidor mudou: nenhuma skill nem as Instruções.
```

## 19/10/2026 — SSEG.exe 2.5.6: de hora em hora só traz; envia quando um processo termina

- Rodada horária: `git_sinc.trazer` (pull --ff-only) e `sseg.py trazer` (só desce do servidor). Envio (commit pelas travas + push, e `servidor_aplicar`) só quando `processos()` vê um código novo em "concluído" (referência em `concluidos-vistos.json`, ao lado do config). Desliga com `"auto_sinc": false`.

### Prompt para atualizar

```
Faça git pull no clone do SSEG. Só código do SSEG.exe mudou: nenhuma skill nem as Instruções.
```

## 19/10/2026 — SSEG.exe 2.5.5: sincronização automática de hora em hora

- O SSEG.exe roda sozinho, a cada hora (a primeira, 2 min depois de abrir): GitHub (`git_sinc.sincronizar`: pull --ff-only, add sem -f, commit pelas travas, push) e servidor (`servidor_planejar` → `servidor_aplicar({})`).
  Conflito e arquivo mexido há menos de 10 min ficam para a próxima rodada / para o clique. Desliga com `"auto_sinc": false` no config.

### Prompt para atualizar

```
Faça git pull no clone do SSEG. Só código do SSEG.exe mudou: nenhuma skill nem as Instruções.
```

## 19/10/2026 — SSEG.exe 2.5.4: botão Refazer pré-análise

- Janela do processo: **Refazer pré-análise** chama `pre_analise.py <código> --forcar --pasta <pasta dos processos>` (script novo `--pasta`). Sem modelo.
- A pré-análise lê `api-*.json`, `anterior-api-*.json`, `marcos-resumo.json` e `cia-ultima.txt`. Arquivo solto na pasta (PDF, planta) não entra nela.

### Prompt para atualizar

```
Faça git pull no clone do SSEG. Só código do SSEG.exe e do pre_analise.py mudou: nenhuma skill nem as Instruções.
```

## 19/10/2026 — SSEG.exe 2.5.3: Atualizar relê a caixa sem depender do "Testar conexão"

- O botão Atualizar decidia "sou administrador?" pelo último "Testar conexão"; sem ele, pulava a leitura da caixa. Agora pede ao servidor, que recusa quem não é admin.

### Prompt para atualizar

```
Faça git pull no clone do SSEG. Só a tela do SSEG.exe mudou: nenhuma skill nem as Instruções.
```

## 19/10/2026 — SSEG.exe 2.5.2: chips do topo juntados em um só

- Os chips Programas, Pastas, Servidor, SOL e GitHub ficam dentro de um chip **Sistema**, que mostra o pior estado e abre a lista ao clicar.

### Prompt para atualizar

```
Faça git pull no clone do SSEG. Só a tela do SSEG.exe mudou: nenhuma skill nem as Instruções.
```

## 19/10/2026 — SSEG.exe 2.5.1: botão Atualizar no Início e processo lançado desce da lista

- **Início → Atualizar** (administrador): lê a caixa do SOL agora no servidor, sincroniza e reordena. O de cima da caixa leva a etiqueta "Próximo".
- **Servidor:** `sol_caixa.py` marca `saiu_em` no `sol-caixa.json` do processo que estava na caixa na leitura anterior e não está mais
  (CA ou CIA lançados) e atualiza os Marcos dele uma vez. O app mostra esse processo como concluído, com o resultado dos Marcos, até a planilha de distribuição trazer o concluído.

### Prompt para atualizar

```
Faça git pull no clone do SSEG (e no clone do servidor, se houver). Só código do SSEG.exe e do sol_caixa.py mudou: nenhuma skill nem as Instruções.
```

## 19/10/2026 — SSEG.exe: campo "Login do SOL" e segundo PC do administrador em um clique

- **Configuração → Login do SOL:** matrícula e senha digitadas uma vez no programa. O Gravar manda ao servidor
  (`porta.py sol-senha-gravar`, só admin, pela entrada padrão do SSH, arquivo 600, solta a trava) e guarda a cópia
  deste PC no Gerenciador de Credenciais do Windows (`app/cofre.py`). Apagar remove dos dois. A senha não vai para
  log, chat nem Git.
- **Segundo PC do administrador:** no PC novo, "Pedir acesso" com o nome do próprio administrador; no PC dele, "Liberar
  acesso" com o código. O `porta.py autorizar` com o nome do admin não recusa mais: acrescenta a chave como outro PC
  dele (`admin-chave`, sem restrição, uma vez só, sobrevive ao regravar das chaves de analista).
- **Scripts:** `porta.py` (ações `admin-chave`, `sol-senha-gravar`, `sol-senha-apagar`), `sol_senha.py` (`salvar`, `remover`).

### Prompt para atualizar

```
Faça git pull no clone do SSEG. Mudou só código do SSEG.exe e dos scripts do servidor (nenhuma skill nem as
Instruções). Se o servidor tiver clone próprio, rode git pull lá também. Depois, em Configuração → Login do SOL,
grave a matrícula e a senha (eu digito).
```

## 17/10/2026 — SSEG.exe 2.3.22 e skill ppci-analise-processo: menos pergunta, menos trava, reanálise focada

Feito depois de ler as conversas das 4 análises de 16 e 17/10 (guardadas no servidor, fora do Git).

- **Skill `ppci-analise-processo`:** seção nova "Na janela do processo do SSEG.exe". Pede para ler a
  pasta antes de perguntar (`sseg.py resumo`), para não repetir pergunta e para tratar a reanálise como
  a última CIA mais o que mudou (assunto novo vai em "Observações"). Também fixa o fechamento curto
  ("Pode aprovar (CA)"; deferir é só de recurso, laudo e CT), tira a manutenção do SSEG das pendências
  do processo e manda buscar norma pelo `sseg.py norma` ou pelo `localizador-normas`.
- **Scripts:**
  - `sseg.py resumo` e `sseg.py norma` (página da tabela, busca de trecho, imagem);
  - check com a linha transcrita da tabela e as notas;
  - pendência parecida recusada;
  - pré-análise com o cadastro do SOL.
- **SSEG.exe 2.3.22:** instruções da janela do processo com a lista de comandos e as mesmas regras,
  e o Poppler na frente do PATH.
- **Para guardar as conversas:** `"cleanupPeriodDays": 365` em `%USERPROFILE%\.claude\settings.json`
  (o padrão apaga depois de 30 dias).

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão 2.3.22 (17/10/2026) e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, rode git pull (no Cowork, me peça para rodar no PowerShell).
2. Rode python sseg/scripts/testar.py e me diga o resultado.
3. Me diga para abrir o SSEG.exe e aceitar a "Nova versão" (2.3.22).
4. A skill ppci-analise-processo mudou: gere o .zip com Python (zipfile, caminho ppci-analise-processo/SKILL.md) e me diga para subir em claude.ai > Configurações > Capacidades > Skills > Substituir.
5. Em %USERPROFILE%\.claude\settings.json, acrescente "cleanupPeriodDays": 365 sem apagar o que já está lá.
```

## 16/10/2026 — SSEG.exe 2.3.2 (copiar por item na CIA, commit com mensagem pronta) e RT 05 Parte 08 na base

- **GitHub (2.3.2):** a tela Sincronizar já abre com a mensagem do commit escrita a partir dos arquivos mudados; é só conferir e acrescentar o porquê.

- **CIA:** cada exigência tem "Copiar" (texto pronto para a caixa Especificar do SOL) e, agrupado por medida, cada medida tem "copiar a medida", com a contagem dos 2.000 caracteres. A caixa da exigência abre do tamanho do texto e a alça de altura fica embaixo do item.
- **Chat:** a caixa de escrever abre maior, cresce com o texto e a alça fica em cima.
- **Normas:** a RT 05 Parte 08/2016 (Símbolos Gráficos) entrou em `normas/pdf/RT05P08.pdf`, com conversão verificada e transcrição da Tabela 1 (o que deve constar junto a cada símbolo). PDFs em `normas/pdf/`: 20. **Campo Instruções:** a contagem em "Onde procurar primeiro" passa a "20 em 16/10/2026" e a RT05P08 entra na lista de duas colunas — copiar do espelho.

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão 2.3.2 (16/10/2026) e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você mesmo.
2. Rode python sseg/scripts/testar.py e me diga o resultado.
3. Me diga para abrir o SSEG.exe e aceitar a "Nova versão".
4. Me entregue o texto do campo Instruções de sseg/workflow/instrucoes-projeto-espelho.md (entre os marcadores) para eu colar no projeto: mudou a contagem de PDFs.
5. Copie sseg/normas/pdf/RT05P08.pdf para C:\Users\55519\Desktop\Carpes\Normas e sseg/normas/base/RT05P08.md com as imagens RT05P08-* de base/img para Carpes\Normas\_md.
```

## 15/10/2026 — SSEG.exe 2.3: CT e recursos nos cards, Quadro da seção

- **CT e recursos:** o servidor lê todo dia útil as planilhas de CT e de recursos e marca na pasta de cada processo o que está aberto. Cards novos: CT marcadas (minuta sem Finalizado), CT com a chefia, Recursos (para redigir) e Recursos com a chefia. Quando a chefia finaliza na planilha, sai sozinho. Se o recurso é seu num processo de outro analista, a pasta aparece para você também.
- **Quadro da seção:** na tela Quadro, a tarefa nova pode ser da seção (todos veem) ou só sua. Na da seção: "Pegar" põe o seu nome, e quem criou ou pegou move, edita e escreve o que foi feito; o cartão mostra início e fim.
- **Abre em 3 s** (antes 20 s com o espelho ligado) e os **cards mudam de ordem arrastando** (2.2.2).

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão 2.3 (15/10/2026) e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você mesmo.
2. Rode python sseg/scripts/testar.py e me diga o resultado.
3. Me diga para abrir o SSEG.exe e aceitar a "Nova versão". Os cards de CT e de recursos aparecem em "+ card"; o Quadro da seção, na tela Quadro (precisa do acesso ao servidor: Configuração → Servidor).
```

## 15/10/2026 — SSEG.exe 2.2: instalador e vários analistas no servidor

- **Instalação:** quem baixa o SSEG.exe e abre cai na tela Instalação (menu ☰). Ela põe o programa em `%LOCALAPPDATA%\Programs\SSEG` com atalho na Área de Trabalho e no Menu Iniciar, instala Git, Python, Poppler e Claude Code, faz o login, cria as pastas e pergunta quem é você. Sem administrador e sem PowerShell.
- **Servidor para todos:** Configuração → Servidor → "Pedir acesso" gera um código; mande ao Átila. Liberado, o Sincronizar processos leva e traz só os SEUS processos (a planilha da distribuição diz de quem é cada um). Sua chave só fala com o SSEG no servidor, sem acesso ao resto.
- **Processos de todos numa pasta por código:** quando o processo passa de um analista para outro, a pasta vai inteira ao novo responsável, com o registro de quem já passou.
- **Chrome para o Claude** (Configuração, opcional): o Claude lê a página do SOL já aberta no seu Chrome pelo DOM, sem print.
- **Trava do banco de notificações:** no Windows ela deixava passar alteração no texto validado (erro de acento na mensagem); corrigida.

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão 2.2 (15/10/2026) e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você mesmo.
2. Rode python sseg/scripts/testar.py e me diga o resultado.
3. Me diga para abrir o SSEG.exe e clicar em "Nova versão" (ou baixar em https://github.com/atilacarpes96/SSEG/releases/latest) e depois abrir o menu ☰ → Instalação e resolver o que estiver com ✗.
4. Se eu quiser usar o servidor: Configuração → Servidor → "Pedir acesso" e mandar o código ao Átila.
```

## 12/10/2026 — SSEG.exe 2.1: janela do processo, conversas sem terminal, respostas visuais

- **Janela do processo:** "Analisar processo" (ou "abrir" em Processos em andamento) mostra três colunas — conversa com o Claude dentro do programa, checklist (pendências, os 16 passos e as medidas do SOL com o Anexo L) e CIA em construção. O Claude só começa quando você manda a primeira mensagem.
- **Nenhum fluxo abre terminal:** os outros botões abrem uma janela de conversa do programa, com a mensagem sugerida no campo. Terminal e "Copiar o prompt" ficam no ⋯.
- **Respostas visuais:** tabelas de verdade, selo de status, cartões, tabela da definidora, perguntas com campo de resposta, cartão de exigência com "Pôr na CIA" e [PDF] da norma.
- **CIA:** vale o texto que você salva; o do Claude fica como rascunho, à parte.
- **Novo comando:** `sseg.py analise --pasta <processo> pendencia|exigencia|passo|ver` grava no `analise.json` da pasta do processo (fica fora do GitHub; vai ao servidor pelo Sincronizar processos).

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão 2.1 (12/10/2026) e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você.
2. Rode python sseg/scripts/testar.py e me diga o resultado.
3. Me diga para abrir o SSEG.exe e clicar em "Nova versão" (ou baixar em https://github.com/atilacarpes96/SSEG/releases/latest).
4. Me explique em três linhas a janela do processo: o Claude só começa quando eu escrevo; o texto que vale na CIA é o que eu salvo; o terminal fica no botão ⋯.
```

## 12/10/2026 — SSEG.exe 2.0: interface nova e ganchos que acham o Python

- **SSEG.exe 2.0:** interface nova (HTML, no componente do Edge do Windows). Barra de estado no alto (Programas, Pastas, Servidor, GitHub com contador, Nova versão), menu ☰ (Início, Buscar normas, Configuração, Ajuda), conversas por demanda e processos em andamento na tela inicial, mensagens em "Detalhes" no rodapé. A lógica é a mesma da 1.3; sem o componente do Edge, abre a janela antiga.
- **Busca (1.2.2):** cada resultado tem [PDF], que abre a norma oficial na página do trecho.
- **SOL sem teclado (1.3.0, opcional):** atalho "Abrir SOL" e passos do Tampermonkey, em Configuração.
- **Ganchos do Claude Code:** passam por `.claude/hooks/rodar.sh`, que pula o `python3` da Microsoft Store e liga o UTF-8 (o gancho Stop dava "Python não foi encontrado" no Windows).

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão de 12/10/2026 e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você.
2. Confira que .claude/settings.json chama sh "$CLAUDE_PROJECT_DIR/.claude/hooks/rodar.sh" nos 5 ganchos.
3. Rode python sseg/scripts/testar.py e me diga o resultado.
4. Me diga para abrir o SSEG.exe e clicar em "Nova versão" (ou baixar em https://github.com/atilacarpes96/SSEG/releases/latest).
```

## 11/10/2026 — SSEG.exe 1.1.0 e revisor-cia com nome completo de modelo

- **Subagente `revisor-cia`:** `model: sonnet` passa a `model: claude-sonnet-5-5`. O atalho funcionava, mas a regra é nome completo (o atalho `haiku` ainda aponta para o 4.5) e o `testar.py` agora barra atalho.
- **Programa SSEG.exe 1.1.0:** botão "Sincronizar com o GitHub" (pull, commit e push com conferência; dado de processo fica fora), "Sincronizar processos" com o servidor por SSH, um botão por tipo de conversa (abre o Claude Code com o modelo e o esforço da política), Subagentes, Gasto em tokens, Reportar bug, Procurar atualização e atualização automática do próprio programa.
- **Travas do commit** no pre-commit do git: valem também para commit fora do Claude.
- **Fonte única das conversas:** `workflow/fluxos.json`, gerado da política pelo `painel.py`; aparece na aba Conversas deste painel.

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão de 11/10/2026 e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você.
2. Confira em .claude/agents/revisor-cia.md que está model: claude-sonnet-5-5.
3. Rode python sseg/scripts/testar.py e me diga o resultado.
4. Me diga para baixar o SSEG.exe em https://github.com/atilacarpes96/SSEG/releases/latest (se eu já tenho a 1.0.6, ele mesmo oferece "Atualizar o programa").
```

## 08/10/2026 — Programa SSEG para o PC (SSEG.exe)

- **Novo programa `SSEG.exe`** em https://github.com/atilacarpes96/SSEG/releases/latest: cria a pasta dos processos e baixa o SSEG do GitHub se ainda não estiver no PC, confere Git, Python e Poppler, e o botão **Verificar atualizações** mostra o que mudou no GitHub e faz o `git pull`. Skill que mudou sai em `.zip` pronta para subir na conta. Tem atalho para este Painel.
- Não dá commit nem push e não força nada: se o pull conflitar, ele avisa e não mexe.
- Na primeira vez o Windows avisa que o programa não tem assinatura: Mais informações → Executar assim mesmo.

### Prompt para atualizar

```text
Quero começar a usar o programa SSEG.exe (mudança de 08/10/2026). Me guie, sem rodar nada por mim:
1. Me diga para baixar o SSEG.exe em https://github.com/atilacarpes96/SSEG/releases/latest e abrir (se o Windows avisar, Mais informações > Executar assim mesmo).
2. Me ajude a preencher as duas pastas do programa: onde já está o meu clone do SSEG (confira com git rev-parse --show-toplevel) e a minha pasta dos processos (print ppci).
3. Me peça para clicar em "Criar / conferir pastas" e depois em "Verificar atualizações", e para colar aqui o que aparecer no quadro de baixo se tiver algum ✗.
```

## 08/10/2026 — Processo no PC, memorial e CIA no servidor

- **Onde roda a análise:** no PC do trabalho, numa conversa **Local** do app do Claude (Novo → Local → pasta do SSEG), uma por processo. É onde estão o Chrome logado no SOL e os arquivos baixados.
- **Novo comando `sseg.py enviar`:** leva à pasta do processo no servidor os JSON, `<N>.pdf`, a CIA e o memorial, por SSH. Planta baixa não vai: só serve na hora e o SOL guarda o original. A `ppci-analise-processo` passou a chamá-lo ao abrir e ao arquivar o processo.
- **Quem não tem servidor:** nada muda. O envio falha com aviso de uma linha e a análise segue.

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a mudança de 08/10/2026 (processo no PC, memorial no servidor) e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você.
2. Rode a skill sseg-sincronizar-skills no sentido repositório → conta. Deve aparecer como diferente: ppci-analise-processo. No Claude Code, em vez do cartão, gere o .zip com o zipfile do Python, como manda o CLAUDE.md, e me diga onde ficou.
3. Se eu não tenho servidor, me diga em uma linha que o passo "enviar" da skill vai só avisar e seguir.
```

## 08/10/2026 — Haiku 5.5 na pergunta rápida e nos subagentes

- **Modelo de cada conversa:** pergunta rápida, notificação avulsa com modelo do banco e sincronização passam do Sonnet 5.5 médio para o **Haiku 5.5 médio**. Análise de processo e revisão final da CIA continuam em **Sonnet 5.5 alto**.
- **Subagentes do Claude Code:** `localizador-normas` e `sol-leitor` passam do Haiku 4.5 para o Haiku 5.5. No arquivo vai o nome completo, `claude-haiku-5-5`, porque o atalho `haiku` ainda aponta para o 4.5.
- **Motivo:** no teste de 08/10 (66 execuções) o Haiku 5.5 médio tirou 97 nas onze tarefas, sem erro fatal, contra 91 do Sonnet 5.5 médio e 67 do Haiku 4.5. Na definidora e na revisão ficou abaixo do Sonnet alto, por isso essas seguem no Sonnet. Detalhes em `workflow/politica-modelo-e-custo.md`.
- **Skills:** `ppci-analise-processo` e `sol-cbmrs-navegador` só trocaram a menção ao modelo.

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão de 08/10/2026 e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você.
2. Rode a skill sseg-sincronizar-skills no sentido repositório → conta. Devem aparecer como diferentes: ppci-analise-processo e sol-cbmrs-navegador. No Claude Code, em vez do cartão, gere um .zip por skill com o zipfile do Python, como manda o CLAUDE.md, e me diga onde ficaram.
3. Confira em .claude/agents/ que localizador-normas e sol-leitor estão com model: claude-haiku-5-5.
4. Feche com três linhas: análise de processo e revisão final da CIA em Sonnet 5.5 alto; pergunta rápida e notificação avulsa em Haiku 5.5 médio; Haiku 5.5 no máximo não compensa (gasta muito e demora).
```

## 06/10/2026 — Modelo de cada conversa, formato do SOL e minuta de despacho

- **Nova skill `ppci-minuta-despacho`:** ata de consulta técnica (FACT) e despacho de recurso com até 2.000 caracteres, só o que foi tratado ou alegado e conclusão prática em cada ponto (orientação do Chefe da SSeg de 05/10/2026).
- **Instruções:** empate no grau de risco entre predominantes → parar e levar ao analista (RT 01/2024, 5.1.2); texto de notificação já no formato da caixa do SOL (quebra de linha e "- ", cada parágrafo numa linha só).
- **Modelo de cada conversa:** análise de processo e revisão final da CIA em **Sonnet 5.5 alto**, a revisão sempre em conversa nova; pergunta rápida, notificação avulsa com modelo do banco e sincronização em **Sonnet 5.5 médio**. O teste de 214 execuções que embasou está em `workflow/politica-modelo-e-custo.md`.
- **Revisão da CIA:** o `sseg.py revisar-cia` passou a apontar requisito de instalação transcrito (é de vistoria), artigo do Decreto junto com item de RT, REITERO numa 1ª análise e caixa sem hífen; a skill manda declarar certo o texto que está certo, sem reescrever.
- **Skills:** seção "Desculpas que não valem" em `ppci-analise-processo`, `ppci-notificacao-cia`, `ppci-revisao-cia` e `ppci-minuta-despacho`, com os atalhos que os modelos tomaram no teste.
- **Claude Code:** hooks em `.claude/settings.json` (pull ao abrir a sessão; commit barrado com arquivo de processo ou com teste falhando; texto validado do banco protegido) e `python3 sseg/scripts/testar.py`. Precisa de `python3` no PATH.
- **Código de processo:** citar só o código num doc versionado pode; arquivo de processo, CIA, JSON, planta, print e dado de proprietário ou RT continuam fora do GitHub.

### Prompt para atualizar

```text
Atualize o meu lado do SSEG para a versão de 06/10/2026, nesta ordem, e no fim me diga o que ficou feito e o que depende de mim:
1. Confira se o clone está em dia com o GitHub (git status e git log -1). Se estiver atrás, me peça para rodar git pull no PowerShell; no Claude Code, rode você.
2. Rode a skill sseg-sincronizar-skills no sentido repositório → conta. Devem aparecer como diferentes ou novas: ppci-analise-processo, ppci-notificacao-cia, ppci-revisao-cia, ppci-incorporar-norma, sol-cbmrs-navegador e a nova ppci-minuta-despacho. No Claude Code, em vez do cartão, gere um .zip por skill com o zipfile do Python, como manda o CLAUDE.md, e me diga onde ficaram.
3. Me entregue, num bloco único para copiar, o texto entre os marcadores INÍCIO e FIM de sseg/workflow/instrucoes-projeto-espelho.md, para eu colar no campo Instruções do projeto no lugar do texto inteiro.
4. Feche com três linhas: análise de processo em Sonnet 5.5 alto; revisão final da CIA em conversa nova com Sonnet 5.5 alto; pergunta rápida e notificação avulsa em Sonnet 5.5 médio.
```
