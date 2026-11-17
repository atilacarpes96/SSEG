#!/usr/bin/env python3
"""
documentos.py — documentos dos envolvidos (ART/RRT do RT, documentos do RU, procurações) e as assinaturas digitais
que estão dentro de cada PDF, lidas pelo pdfsig (Poppler), sem IA e sem o validador do ITI (pede login gov.br).

Por quê (prova 3 da IA local, 17/11/2026): em exigência de assinatura, os modelos locais liam o carimbo impresso
"Assinado utilizando o(s) seguinte(s) selo(s) do gov.br" de uma cópia sem certificado e diziam "cumpriu", mesmo com
o fato do script no prompt. Ter ou não ter certificado no PDF quem diz é o pdfsig; validar no ITI continua com o
analista.

  python3 documentos.py <pasta do processo>        mostra a seção (o que a pré-análise da reanálise acrescenta)

Os PDFs ficam em <pasta>/documentos/<id>-<nome>.pdf, fora do Git (sseg/processos/). Quem baixa é o sol_caixa.py
(servidor), pela aba logada, junto com as CIAs: baixar(pasta, api, buscar).
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys

SUB = "documentos"
SEM_JANELA = 0x08000000 if os.name == "nt" else 0
# manifesto de assinatura impresso (gov.br, Docusign…): sem certificado no PDF, é cópia do documento assinado
CARIMBO = re.compile(r"(?i)(assinado utilizando o\(s\) seguinte\(s\) selo|documento assinado digitalmente|"
                     r"assinado eletronicamente|assinado digitalmente por|verifique as assinaturas|"
                     r"validar\.iti\.gov\.br|docusign envelope|clicksign)")
ASSINATURA_CIA = re.compile(r"(?i)assinad|assinatura")


def _exe(nome):
    pasta = os.environ.get("SSEG_POPPLER") or os.path.dirname(shutil.which("pdftotext") or "")
    return os.path.join(pasta, nome + (".exe" if os.name == "nt" else "")) if pasta else nome


def lista(api):
    """[{id, nome, papel, de}] dos arquivos dos envolvidos no JSON do licenciamento, sem repetir id."""
    env = (api or {}).get("envolvidos") or {}
    out, vistos = [], set()

    def add(arq, papel, de):
        if isinstance(arq, dict) and arq.get("id") and arq["id"] not in vistos:
            vistos.add(arq["id"])
            out.append({"id": int(arq["id"]), "nome": arq.get("nomeArquivo") or "", "papel": papel, "de": de})

    for chave, papel in (("rts", "RT"), ("rus", "Responsável pelo uso"), ("proprietarios", "Proprietário")):
        for e in env.get(chave) or []:
            nome = e.get("nome") or ""
            for a in [e.get("arquivo")] + list(e.get("arquivos") or []):
                add(a, papel, nome)
            p = e.get("procurador") or {}
            for a in [p.get("arquivo")] + list(p.get("arquivos") or []):
                add(a, "Procuração (%s)" % papel.lower(), "%s → procurador %s" % (nome, p.get("nome") or ""))
    return out


def _arquivo(pasta, doc):
    limpo = re.sub(r"[^\w.\- ]+", "_", doc["nome"] or "documento.pdf").strip() or "documento.pdf"
    return os.path.join(pasta, SUB, "%d-%s" % (doc["id"], limpo if limpo.lower().endswith(".pdf") else limpo + ".pdf"))


def baixar(pasta, api, buscar):
    """Baixa os documentos que faltam. buscar(id) -> bytes. Devolve (baixados, falhas)."""
    feitos, falhas = 0, []
    for doc in lista(api):
        arq = _arquivo(pasta, doc)
        if os.path.exists(arq):
            continue
        try:
            dados = buscar(doc["id"])
        except PermissionError:
            raise
        except (RuntimeError, OSError, ValueError) as e:
            falhas.append("%s: %s" % (doc["nome"], e))
            continue
        os.makedirs(os.path.dirname(arq), exist_ok=True)
        with open(arq + ".parte", "wb") as fh:
            fh.write(dados)
        os.replace(arq + ".parte", arq)
        feitos += 1
    return feitos, falhas


def assinaturas(pdf):
    """{certificados: [{nome, quando, integra}], carimbo: bool, texto: bool, paginas}. integra: a assinatura confere
    com o conteúdo (pdfsig "Signature is Valid"); a cadeia do certificado não é conferida (-nocert, sem rede)."""
    r = {"certificados": [], "carimbo": False, "texto": False, "paginas": 0}
    if not open(pdf, "rb").read(5).startswith(b"%PDF"):
        r["erro"] = "não é PDF"
        return r
    try:
        o = subprocess.run([_exe("pdfsig"), "-nocert", pdf], capture_output=True, text=True, errors="replace",
                           timeout=60, creationflags=SEM_JANELA).stdout
        for bloco in re.split(r"\nSignature #\d+:", o)[1:]:
            g = lambda k: (re.search(r"- %s: (.*)" % k, bloco) or [None, ""])[1].strip()
            r["certificados"].append({"nome": g("Signer Certificate Common Name"), "quando": g("Signing Time"),
                                      "integra": "is Valid" in g("Signature Validation")})
    except (OSError, subprocess.SubprocessError):
        # 17/11/2026: o Poppler do Windows (winget) vem sem o pdfsig; no PC quem lê o certificado é o pyHanko
        try:
            r["certificados"] = _pyhanko(pdf)
        except ImportError:
            r["erro"] = "pdfsig e pyHanko ausentes: certificado não conferido"
        except Exception as e:  # noqa: BLE001 — PDF que o pyHanko não abre: não vira "sem assinatura"
            r["erro"] = "certificado não conferido (%s)" % str(e)[:120]
    try:
        t = subprocess.run([_exe("pdftotext"), "-l", "30", pdf, "-"], capture_output=True, text=True, errors="replace",
                           timeout=60, creationflags=SEM_JANELA).stdout
        r["texto"] = len(re.sub(r"\s", "", t)) > 200
        r["carimbo"] = bool(CARIMBO.search(t))
        r["paginas"] = t.count("\f")
    except (OSError, subprocess.SubprocessError):
        pass
    return r


def _pyhanko(pdf):
    """Mesmo resultado do pdfsig -nocert (conferido em 20 documentos da caixa, 17/11/2026): nome do certificado, data e se
    a assinatura confere com o conteúdo. Sem raízes confiáveis: a cadeia do ITI não é conferida. Campo de assinatura que
    o pyHanko não consegue ler (CMS quebrado; o pdfsig dá "Unknown Validation Failure") entra como não íntegro."""
    import logging
    from pyhanko.pdf_utils.reader import PdfFileReader
    from pyhanko.sign.validation import validate_pdf_signature
    logging.getLogger("pyhanko").setLevel(logging.ERROR)
    logging.getLogger("pyhanko_certvalidator").setLevel(logging.ERROR)
    out = []
    with open(pdf, "rb") as fh:
        for s in PdfFileReader(fh, strict=False).embedded_signatures:
            try:
                st = validate_pdf_signature(s)
                integra = bool(st.intact and st.valid)
            except Exception:  # noqa: BLE001
                integra = False
            cert = s.signer_cert
            quando = s.self_reported_timestamp
            out.append({"nome": cert.subject.native.get("common_name", "") if cert else "",
                        "quando": quando.strftime("%b %d %Y %H:%M:%S") if quando else "", "integra": integra})
    with open(pdf, "rb") as fh:
        campos = fh.read().count(b"/ByteRange")
    out += [{"nome": "", "quando": "", "integra": False} for _ in range(max(0, campos - len(out)))]
    return out


def exigencias_de_assinatura(cia_txt):
    """Exigências da CIA que falam de assinatura, pela leitura dos palpites (palpite_local.partir)."""
    try:
        import palpite_local
        return [(s, t) for s, _sub, t in palpite_local.partir(cia_txt) if ASSINATURA_CIA.search(t)]
    except Exception:  # noqa: BLE001 — parser de CIA não pode derrubar a pré-análise
        return []


def secao(pasta, api, cia_txt=""):
    """Texto para a pré-análise da reanálise. Vazio sem documentos baixados."""
    docs = [(d, _arquivo(pasta, d)) for d in lista(api)]
    docs = [(d, a) for d, a in docs if os.path.exists(a)]
    if not docs:
        return ""
    L = ["DOCUMENTOS DOS ENVOLVIDOS — assinatura digital dentro do PDF (documentos.py + pdfsig, sem IA, sem o ITI)"]
    exig = exigencias_de_assinatura(cia_txt)
    if exig:
        L.append("A última CIA cobrou assinatura em %d exigência(s):" % len(exig))
        L += ["  · %s %s" % (s, (t[:160] + "…") if len(t) > 160 else t) for s, t in exig]
    for d, a in docs:
        s = assinaturas(a)
        if s.get("erro"):
            situ = "?? " + s["erro"]
        elif s["certificados"]:
            situ = "assinado digitalmente por " + "; ".join(
                "%s (%s)%s" % (c["nome"] or "sem nome", c["quando"] or "sem data", "" if c["integra"] else
                               " — ASSINATURA NÃO CONFERE com o conteúdo") for c in s["certificados"])
        elif s["carimbo"]:
            situ = ("!! carimbo de assinatura eletrônica impresso, mas NENHUM certificado no PDF: é cópia, o ITI não "
                    "valida")
        elif not s["texto"]:
            situ = "sem certificado; PDF escaneado (sem texto): assinatura à mão só se vê na imagem"
        else:
            situ = "sem certificado e sem carimbo; assinatura à mão, se houver, só na imagem"
        L.append("- %s · %s · %s\n    %s" % (d["papel"], d["de"], os.path.relpath(a, pasta), situ))
    L.append("Certificado no PDF não é validade no ITI (validar.iti.gov.br, com login gov.br): isso é do analista.")
    return "\n".join(L) + "\n\n"


def main(argv=None):
    pasta = (argv or sys.argv[1:] or ["."])[0]
    apis = sorted(glob.glob(os.path.join(pasta, "api-*.json")) or glob.glob(os.path.join(pasta, "base-api-*.json")),
                  key=os.path.getmtime)
    if not apis:
        print("sem api-<ID>.json em %s" % pasta)
        return 1
    with open(apis[-1], encoding="utf-8") as fh:
        api = json.load(fh)
    try:
        with open(os.path.join(pasta, "cia-ultima.txt"), encoding="utf-8", errors="replace") as fh:
            cia = fh.read()
    except OSError:
        cia = ""
    print(secao(pasta, api, cia) or "Nenhum documento de envolvido baixado em %s/%s." % (pasta, SUB))
    return 0


if __name__ == "__main__":
    sys.exit(main())
