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
