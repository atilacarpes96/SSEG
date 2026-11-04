#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ditado.py — o 🎤 do SSEG.exe no PC (2.8.10, 04/11/2026): transcreve no servidor o áudio gravado na janela.

Por quê: o WebView2 do programa não transcreve (2.8.2) e a digitação por voz do Windows (Win+H) abre o painel mas não
escreve no campo da janela (relato do Átila, 04/11/2026). O programa grava o áudio (webm/opus) e manda pelo SSH;
aqui o faster-whisper do transcritor (~/transcritor/venv, modelo "small", já baixado) devolve o texto.

USO (no servidor):
  ~/transcritor/venv/bin/python sseg/scripts/ditado.py <arquivo de áudio>
  ~/transcritor/venv/bin/python sseg/scripts/ditado.py -      # áudio pela entrada padrão (é o que o SSEG.exe faz)
Saída: só o texto transcrito. Erro: mensagem em stderr e código 1.
Medido em 04/11/2026 (2 núcleos ARM): ~1,5 s para carregar o modelo + ~7 s para 12–15 s de fala.
"""

import os
import sys
import tempfile

# vocabulário que o Whisper erra sem contexto (vai como prompt inicial; não é transcrito)
CONTEXTO = ("Análise de PPCI no CBMRS. RT 01/2024, RTCBMRS, CIA, SOL, campo 4, memorial descritivo, planta baixa, "
            "Decreto Estadual 51.803, item 5.2.2, Tabela 6M.6, hidrantes, extintores, brigada de incêndio, "
            "saídas de emergência, ocupação F-6, J-4, M-2.")


def main():
    if len(sys.argv) < 2:
        print("uso: ditado.py <arquivo de áudio>", file=sys.stderr)
        return 1
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("faster-whisper não instalado: rode com ~/transcritor/venv/bin/python", file=sys.stderr)
        return 1
    arq, tmp = sys.argv[1], None
    if arq == "-":  # o áudio chega pelo SSH: arquivo temporário só durante a transcrição
        dados = sys.stdin.buffer.read()
        if not dados:
            print("áudio vazio", file=sys.stderr)
            return 1
        fd, tmp = tempfile.mkstemp(prefix="sseg-ditado-", suffix=".webm")
        with os.fdopen(fd, "wb") as fh:
            fh.write(dados)
        arq = tmp
    try:
        m = WhisperModel("small", device="cpu", compute_type="int8")
        segs, _info = m.transcribe(arq, language="pt", vad_filter=True, beam_size=1, initial_prompt=CONTEXTO)
        print(" ".join(s.text.strip() for s in segs).strip())
    finally:
        if tmp:
            os.unlink(tmp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
