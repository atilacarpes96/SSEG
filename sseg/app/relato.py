# -*- coding: utf-8 -*-
"""
relato.py — "Reportar bug" do SSEG.exe.

Junta versão, sistema, o fim do quadro do programa e o texto do analista. Antes de sair do PC,
tira o que é de processo: código A000..., caminho das pastas (processos, SSEG, usuário) e nome
de arquivo de planta, PDF, imagem ou CIA. O repositório é público: issue também é.
"""

import os
import platform
import re
import urllib.parse

CODIGO = re.compile(r"A000\d{5}[A-Z]{2}\d{3}")
ARQUIVO = re.compile(r"[^\s\\/:\"'|]+\.(pdf|dwg|dxf|png|jpe?g|tiff?|docx?|xlsx?)\b", re.I)


def limpar(texto, caminhos=()):
    for c in sorted((c for c in caminhos if c), key=len, reverse=True):
        for v in {c, c.replace("\\", "/"), c.replace("/", "\\")}:
            texto = re.sub(re.escape(v), "<pasta>", texto, flags=re.I)
    texto = re.sub(re.escape(os.path.expanduser("~")), "<usuário>", texto, flags=re.I)
    texto = CODIGO.sub("<processo>", texto)
    texto = re.sub(r"CIA \d+[^\n|]*", "<CIA>", texto)
    return ARQUIVO.sub(lambda m: "<arquivo .%s>" % m.group(1).lower(), texto)


def montar(versao, descricao, quadro, caminhos=()):
    fim = "\n".join(quadro.strip().splitlines()[-40:])
    corpo = ("**O que aconteceu**\n%s\n\n**Programa:** SSEG.exe %s\n**Sistema:** %s %s (%s)\n\n"
             "**Fim do quadro do programa**\n```\n%s\n```\n"
             % (descricao.strip() or "(sem descrição)", versao, platform.system(), platform.release(),
                platform.version(), fim))
    return limpar(corpo, caminhos)


def url_issue(repo, titulo, corpo):
    q = urllib.parse.urlencode({"title": titulo, "body": corpo[:6000], "labels": "bug"})
    return "https://github.com/%s/issues/new?%s" % (repo, q)
