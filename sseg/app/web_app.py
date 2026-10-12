# -*- coding: utf-8 -*-
"""
web_app.py — abre a interface 2.0 (web/index.html) numa janela do WebView2 (Edge) via pywebview.

Sem pywebview ou sem WebView2, quem chama cai na janela clássica (Tk, 1.x). No build,
SSEG_TESTE_FOTO fotografa cada tela (SSEG.tour no JavaScript) e grava os erros da página em
<foto>-erros.txt — o mesmo contrato da janela clássica.
"""

import os
import time
import traceback

PASSOS = ["inicio", "menu", "busca", "config", "conversa", "github", "servidor", "bug", "detalhes", "processo"]


def _tour(jan, api, foto):
    from PIL import ImageGrab
    base_f, ext = os.path.splitext(foto)
    erros = []
    try:
        time.sleep(8)  # página carregada e barra de estado conferida
        for i, passo in enumerate(PASSOS):
            jan.evaluate_js("SSEG.tour(%r)" % passo)
            time.sleep(3 if passo == "busca" else 2)
            ImageGrab.grab().save(foto if i == 0 else "%s-%s%s" % (base_f, passo, ext))
    except Exception:
        erros.append(traceback.format_exc())
    erros += api._erros_js
    with open(base_f + "-erros.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(erros))
    jan.destroy()


def principal(recurso):
    import webview
    from api import Api
    api = Api()
    try:
        altura = min(860, webview.screens[0].height - 80)
    except Exception:
        altura = 760
    jan = webview.create_window("SSEG", recurso(os.path.join("web", "index.html")), js_api=api,
                                width=1120, height=altura, min_size=(720, 520), background_color="#F4F1EF",
                                text_select=True)
    api._ligar(jan)
    foto = os.environ.get("SSEG_TESTE_FOTO")
    if foto:
        webview.start(_tour, (jan, api, foto), gui="edgechromium")
    else:
        webview.start(gui="edgechromium")
