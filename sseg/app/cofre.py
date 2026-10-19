# -*- coding: utf-8 -*-
"""
cofre.py — a cópia da matrícula e da senha do SOL neste PC (2.5.0).

Fica no Gerenciador de Credenciais do Windows (alvo "SSEG-SOL"), não em arquivo de texto: só o seu usuário
do Windows lê. Autorizado pelo Átila em 17/10/2026 ("senha salva uma vez só, no PC e no servidor").
A senha só passa por aqui e pelo SSH até o servidor; nunca vai para log, chat nem Git.
Fora do Windows (desenvolvimento) as funções devolvem "indisponível" e não gravam nada.
"""

import os

ALVO = "SSEG-SOL"


def disponivel():
    return os.name == "nt"


if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    class _FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

    class _CRED(ctypes.Structure):
        _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR),
                    ("Comment", wintypes.LPWSTR), ("LastWritten", _FILETIME), ("CredentialBlobSize", wintypes.DWORD),
                    ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)), ("Persist", wintypes.DWORD),
                    ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
                    ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR)]

    _adv = ctypes.WinDLL("advapi32", use_last_error=True)
    _adv.CredWriteW.argtypes = [ctypes.POINTER(_CRED), wintypes.DWORD]
    _adv.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(_CRED))]
    _adv.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    _adv.CredFree.argtypes = [ctypes.c_void_p]
    _GENERIC, _PERSIST_LOCAL = 1, 2


def gravar(matricula, senha):
    """True se gravou. Levanta RuntimeError se o Windows recusar."""
    if not disponivel():
        return False
    blob = senha.encode("utf-16-le")
    buf = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
    c = _CRED()
    c.Type, c.TargetName, c.UserName, c.Persist = _GENERIC, ALVO, matricula, _PERSIST_LOCAL
    c.CredentialBlobSize, c.CredentialBlob = len(blob), ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte))
    if not _adv.CredWriteW(ctypes.byref(c), 0):
        raise RuntimeError("O Windows recusou guardar a credencial (erro %s)." % ctypes.get_last_error())
    return True


def matricula():
    """A matrícula guardada, ou "" (a senha não sai daqui: o único leitor dela seria o próprio programa)."""
    if not disponivel():
        return ""
    p = ctypes.POINTER(_CRED)()
    if not _adv.CredReadW(ALVO, _GENERIC, 0, ctypes.byref(p)):
        return ""
    try:
        return p.contents.UserName or ""
    finally:
        _adv.CredFree(p)


def apagar():
    if not disponivel():
        return False
    return bool(_adv.CredDeleteW(ALVO, _GENERIC, 0))
