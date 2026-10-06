---
name: ferramentas-candidatas-a-testar
description: Os 15 repositórios de IA levantados como candidatos a testar no projeto PPCI — quais já foram instalados e avaliados, quais continuam sem teste, e o filtro que decide se vale testar
sources: [cowork]
---

# Ferramentas candidatas a testar

> Lista levantada do vídeo `https://youtu.be/McKnT5TwAAo` (nomes conferidos no GitHub a partir
> da transcrição feita com Whisper local + yt-dlp). Registrada como doc em **14/09/2026**.
> O que já está instalado e testado está em [[ferramentas-locais-anydoc-skillspector]].

## Os 15, por bloco

| Bloco | Repositórios |
|---|---|
| Base | DeepSeek Harness · Omarchy · Phone Harness |
| Ambientes de agentes | Herdr · Orca |
| Qualidade e segurança | Codex Loop · **SkillSpector** (NVIDIA) · **No AI Slop** (Peter Yang) |
| Dados | **anydoc** (Firecrawl) · Archify · CRM da Comp.AI |
| Vídeo | Open Montage · Video Use (Browser Use) |
| Grátis e diversão | OmniRoute · Cloud of Tanks |

## Situação em 14/09/2026

| Ferramenta | Situação |
|---|---|
| **anydoc** | instalado e testado — serve para texto de norma e ODT, **não** para tabela de exigências. Ver [[ferramentas-locais-anydoc-skillspector]] |
| **SkillSpector** | instalado — scanner de segurança, rodar antes de instalar skill de terceiro |
| **No AI Slop** | instalado no Claude Code do PC; também existe como skill da conta do Claude |
| Os outros 12 | **sem teste** |

## O filtro antes de testar

A máquina do quartel (`pc-carpes`) — onde roda o SOL e a análise de PPCI — **é fraca**. Não
aguenta ferramenta pesada; o Whisper, por exemplo, roda na outra máquina. Ferramenta leve
(anydoc, a maioria dos harnesses de agente) roda bem nela.

Antes de instalar qualquer uma:

1. **Roda leve?** Se exige GPU ou modelo local grande, não é para o PC do quartel.
2. **Funciona offline e sem admin?** É a restrição da instalação de 14/09/2026.
3. **O dado sai da máquina?** Se manda documento para servidor de terceiro, está fora — a
   regra de nenhum documento de PPCI sair da máquina não abre exceção por ferramenta.
4. **Sendo skill:** passar o `skillspector scan <pasta> --no-llm` antes de instalar.

## Avaliação de 05/10/2026 — repositórios do vídeo "agent-skills" e mais cinco

Filtro aplicado: o SSEG é análise normativa com pouco código, dado de processo não sai da máquina, e a
cota é o recurso escasso (cada token fixo carregado em toda sessão custa em toda rodada).

| Repositório | O que é | Veredito para o SSEG |
|---|---|---|
| `addyosmani/agent-skills` (vídeo) | 25 habilidades de engenharia de software por fase (spec → plan → build → test → review → ship), 4 agentes revisores, hooks | **Ideias adotadas, instalação não.** Adotado: hooks que executam as regras (`.claude/hooks/`), seção "Desculpas que não valem" nas skills (o "Rationalizations" deles), testes antes do commit (`scripts/testar.py`). As skills deles são de desenvolvimento web e carregariam descrições em toda sessão sem uso |
| `obra/superpowers` | Metodologia de desenvolvimento (TDD, debugging sistemático, planos, worktrees) com hook de SessionStart que injeta a skill-mestra | **Não instalar.** Injeção fixa em toda sessão e foco em código. Adotado o princípio "verificação antes de concluir" e o de testar skill com cenário de pressão (é o que o teste de modelos de 05/10/2026 fez) |
| `thedotmack/claude-mem` | Memória automática: hooks capturam toda ferramenta, um modelo comprime e reinjeta nas próximas sessões | **Não instalar.** Gasta cota em segundo plano, guarda tudo (inclusive dado de processo) e reinjeta entre sessões, o que mistura processos. O SSEG já tem memória curada: `processos/<N>.md`, `casos-referencia.md`, Painel |
| `rebelytics/one-skill-to-rule-them-all` (Task Observer) | Meta-skill que registra correções do usuário e propõe melhorias de skill para aprovação | **Ideia boa, instalação adiada.** Precisa de instrução fixa em toda sessão para disparar. O equivalente barato no SSEG: a fila do Painel e o teste de modelos; candidata a rotina semanal no servidor que lê as correções da semana nos transcripts |
| `vercel-labs/skills` | CLI `npx skills` para achar e instalar skills | **Não precisa.** As skills do SSEG são próprias e o repositório já é a fonte |
| `pbakaus/impeccable` | Comandos e detectores de qualidade visual de interface web | **Fora do escopo.** Só serviria para os painéis; a skill de design de artifact já cobre |
