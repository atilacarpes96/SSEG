#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sol_lancar.py — "Lançar no SOL" (SSEG.exe 2.6.5): grava a notificação no campo "Outros" do item, como o botão
Reprovar do SOL faz, sem clicar na tela e sem Claude (zero token). Pedido e autorização do Átila, 20/10/2026.

Como o SOL grava (lido do código da própria página do SOL em 20/10/2026, chunks da análise técnica):
  - opções do modal "Reprovar …": GET /parametro/<chave>  (chave da medida = tipo.chaveNC; dos outros itens, fixa)
  - gravar o item: POST /analise-tecnica/editar-item com
      {id, idAnaliseTecnica, idItemAnalisado, tipoItemAnaliseTecnica, statusResultadoAtec: "REPROVADO",
       justificativas: [{justificativa: <texto>, parametroNcs: <opção do modal>, id: null}, ...]}
    a lista vai INTEIRA (o modal reenvia as que já estavam marcadas): as que já existem no item ficam, e a do
    "Outros" leva o texto novo.
  - "Demais inconformidades": PUT /analise-tecnica/<id>/inconformidade com o texto (corpo texto puro).
  - Concluir a análise (PUT …/deferir|indeferir) NUNCA é chamado aqui: emitir a CIA é do analista, no SOL.
Item → id: medidas, riscos, elementos gráficos, ocupações, RT, RU e proprietário usam o id do próprio item;
tipo de edificação, característica geral e isolamento usam o id da característica. "Outras medidas" não entra
(a ação dela no SOL é outra).

Fluxo: plano() só LÊ (acha o item, diz o status atual e o que já está lançado nele) → o analista confirma →
lancar() grava e LÊ DE NOVO para conferir que o texto ficou igual. Quem fala com o SOL é a `aba` (avaliar(js)),
a aba do SOL logada do Chrome do analista (app/sol_aba.py).
"""

import json
import re
import unicodedata

import sol_caixa as sc

PARAMETRO = "/solcbm/api/v1/adm/parametro"
CHAVES = {  # chave das opções do modal, dos itens que não são medida (config do SOL, chunk 3)
    "RT": "analise.identificacao.RT", "RU": "analise.identificacao.RU", "PROPRIETARIO": "analise.identificacao.proprietario",
    "ISOLAMENTO_RISCO": "analise.caracteristicas.isolamento", "TIPO_EDIFICACAO": "analise.caracteristicas.edificacao",
    "OCUPACAO": "analise.caracteristicas.ocupacao", "GERAL": "analise.caracteristicas.geral",
    "ELEMENTO_GRAFICO": "analise.elementos.pranchas", "RISCO_ESPECIFICO": "analise.riscos.especificos",
}  # conferidas no chunk 3 do SOL em 20/10/2026 (getConfiguracaoItemReprovado)
STATUS = {"APROVADO": "Aprovado", "REPROVADO": "Reprovado"}
LIMITE = 2000

GRAVAR = r"""(async () => {
  const tok = sessionStorage.getItem("access_token") || localStorage.getItem("access_token");
  const a = %s;
  const r = await fetch(a.url, { method: a.metodo, credentials: "include",
    headers: { Authorization: "Bearer " + tok, "Content-Type": a.tipo }, body: a.corpo });
  return JSON.stringify({ status: r.status, corpo: await r.text() });
})()"""


def _chave(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def itens(analise):
    """Todos os itens que o analista pode reprovar, na ordem da tela: [{tipo, id, nome, resultado, chave}]."""
    L = analise.get("licenciamento") or {}
    env, car, esp = L.get("envolvidos") or {}, L.get("caracteristica") or {}, L.get("especSeguranca") or {}
    out = []
    for tipo, lst in (("RT", env.get("rts")), ("RU", env.get("rus")), ("PROPRIETARIO", env.get("proprietarios"))):
        for p in lst or []:
            out.append({"tipo": tipo, "id": p.get("id"), "nome": "%s: %s" % (tipo.capitalize() if tipo == "PROPRIETARIO" else tipo,
                                                                             (p.get("nome") or "").strip()),
                        "resultado": p.get("resultado"), "chave": CHAVES[tipo]})
    for nome, tipo, campo in (("Tipo de edificação", "TIPO_EDIFICACAO", "resultadoTipoEdificacao"),
                              ("Característica geral", "GERAL", "resultadoGeral"),
                              ("Isolamento de risco", "ISOLAMENTO_RISCO", "resultadoIsolamentoRisco")):
        out.append({"tipo": tipo, "id": car.get("id"), "nome": nome, "resultado": car.get(campo), "chave": CHAVES[tipo]})
    for o in car.get("ocupacoes") or []:
        c = o.get("cnae") or {}
        out.append({"tipo": "OCUPACAO", "id": o.get("id"), "nome": "Ocupação %s — %s" % (c.get("divisao") or "", c.get("descricao") or ""),
                    "resultado": o.get("resultado"), "chave": CHAVES["OCUPACAO"]})
    for m in esp.get("medidas") or []:
        t = m.get("tipo") or {}
        out.append({"tipo": "MEDIDA_SEGURANCA", "id": m.get("id"), "nome": t.get("nome") or "?", "resultado": m.get("resultado"),
                    "chave": t.get("chaveNC")})
    # "Outras medidas" (MEDIDA_SEGURANCA_OUTRA) fica de fora: no SOL a ação dela é "Corrigir/Salvar correções", não Reprovar
    for r in L.get("especsRiscos") or []:
        t = r.get("risco") or r.get("tipo") or {}
        nome = (t.get("descricao") or t.get("nome")) if isinstance(t, dict) else t
        out.append({"tipo": "RISCO_ESPECIFICO", "id": r.get("id"), "nome": nome or "Risco específico", "resultado": r.get("resultado"),
                    "chave": CHAVES["RISCO_ESPECIFICO"]})
    for e in L.get("elemGraficos") or []:
        if e.get("situacao") == "ATIVO":
            out.append({"tipo": "ELEMENTO_GRAFICO", "id": e.get("id"), "nome": " ".join(str(e.get("descricao") or "").split()),
                        "resultado": e.get("resultado"), "chave": CHAVES["ELEMENTO_GRAFICO"]})
    return out


def achar(analise, nome):
    """O item do SOL com esse nome (o da coluna CIA). Medida casa pelo nome do tipo; elemento gráfico pela descrição.
    "Demais inconformidades" é o campo de texto livre. Devolve o item, ou None."""
    k = _chave(nome)
    if k in ("demais inconformidades", "outras inconformidades", "inconformidades"):
        return {"tipo": "INCONFORMIDADE", "id": analise.get("id"), "nome": "Demais inconformidades", "resultado": None, "chave": None}
    lst = itens(analise)
    iguais = [i for i in lst if _chave(i["nome"]) == k]
    if not iguais:  # "Planta Baixa" × "planta baixa"; "Ocupação F-8" × "Ocupação F-8 — Restaurantes"
        iguais = [i for i in lst if _chave(i["nome"]).startswith(k) or k.startswith(_chave(i["nome"]))]
    return iguais[0] if len(iguais) == 1 else None


def _igual(t):
    """Para conferir a leitura de volta: o servidor pode trocar \r\n por \n ou cortar espaço no fim da linha."""
    return "\n".join(l.rstrip() for l in str(t or "").replace("\r\n", "\n").split("\n")).strip()


def _justs(resultado):
    return [j for j in ((resultado or {}).get("justificativas") or []) if j]


def plano(aba, id_analise, nome, texto):
    """Só lê. {ok, item, status, ja_outros, outras, tamanho, aviso} — o que a janela mostra antes de confirmar."""
    texto = texto or ""
    a = sc.buscar(aba, "%s/%s" % (sc.API, id_analise))
    if (a.get("status") or "") not in ("EM_ANALISE", ""):
        return {"ok": False, "aviso": "A análise no SOL está %s: não dá para lançar." % a.get("status")}
    it = achar(a, nome)
    if not it:
        return {"ok": False, "item": "", "aviso": "Não achei no SOL um item chamado \"%s\": escolha o item na lista." % nome,
                "opcoes": ["Demais inconformidades"] + [i["nome"] for i in itens(a)], "tamanho": len(texto)}
    p = {"ok": True, "item": it["nome"], "tipo": it["tipo"], "tamanho": len(texto), "aviso": "",
         "opcoes": ["Demais inconformidades"] + [i["nome"] for i in itens(a)]}
    if len(texto) > LIMITE:
        p.update(ok=False, aviso="%d caracteres: passa do limite de %d da caixa do SOL. Divida antes." % (len(texto), LIMITE))
    if it["tipo"] == "INCONFORMIDADE":
        p.update(status="", ja_outros=a.get("inconformidade") or "", outras=0)
        return p
    r = it["resultado"] or {}
    js = _justs(r)
    p["status"] = STATUS.get(r.get("statusResultadoAtec"), "Analisar")
    outros = [j for j in js if _chave((j.get("parametroNcs") or {}).get("valor")) == "outros"]
    p["ja_outros"] = outros[0].get("justificativa") if outros else ""
    p["outras"] = len(js) - len(outros)  # opções prontas já marcadas no item (ficam)
    return p


def _gravar(aba, metodo, url, corpo, tipo="application/json"):
    arg = json.dumps({"metodo": metodo, "url": url, "corpo": corpo, "tipo": tipo})
    r = aba.avaliar(GRAVAR % arg)  # uma vez só: gravação não se repete sozinha
    if r["status"] in (401, 403):
        raise PermissionError("o SOL recusou a gravação (%s): a sessão caiu ou a análise não é sua" % r["status"])
    if not 200 <= r["status"] < 300:
        raise RuntimeError("o SOL respondeu %s ao gravar: %s" % (r["status"], (r["corpo"] or "")[:300]))
    return r["corpo"]


def pedido(analise, it, outros_param, texto):
    """Corpo do editar-item: as justificativas que já estão no item ficam; a do "Outros" leva o texto novo."""
    r = it["resultado"] or {}
    js = [{"justificativa": j.get("justificativa"), "parametroNcs": j.get("parametroNcs"), "id": None}
          for j in _justs(r) if (j.get("parametroNcs") or {}).get("id") != outros_param.get("id")]
    js.append({"justificativa": texto, "parametroNcs": outros_param, "id": None})
    return {"id": r.get("id"), "idAnaliseTecnica": analise.get("id"), "idItemAnalisado": it["id"],
            "tipoItemAnaliseTecnica": it["tipo"], "statusResultadoAtec": "REPROVADO", "justificativas": js}


def lancar(aba, id_analise, nome, texto):
    """Grava e confere. {ok, item, conferido, aviso}. Lê o item de novo antes (o que vale é o estado de agora)."""
    if not (texto or "").strip():
        raise ValueError("texto vazio")
    if len(texto) > LIMITE:
        raise ValueError("%d caracteres: passa de %d" % (len(texto), LIMITE))
    a = sc.buscar(aba, "%s/%s" % (sc.API, id_analise))
    if (a.get("status") or "") not in ("EM_ANALISE", ""):
        raise RuntimeError("a análise no SOL está %s" % a.get("status"))
    it = achar(a, nome)
    if not it:
        raise LookupError("não achei no SOL o item \"%s\"" % nome)
    if it["tipo"] == "INCONFORMIDADE":
        _gravar(aba, "PUT", "%s/%s/inconformidade" % (sc.API, id_analise), texto, "text/plain")
        try:
            depois = sc.buscar(aba, "%s/%s" % (sc.API, id_analise)).get("inconformidade") or ""
        except (RuntimeError, OSError, ValueError) as e:
            return {"ok": False, "item": it["nome"], "conferido": False, "aviso": "gravou, mas não consegui ler de volta (%s)" % e}
        ok = _igual(depois) == _igual(texto)
        return {"ok": ok, "item": it["nome"], "conferido": ok,
                "aviso": "" if ok else "o SOL guardou um texto diferente: confira na tela"}
    if not it["chave"]:
        raise RuntimeError("o SOL não informou as opções do modal deste item")
    opcoes = sc.buscar(aba, "%s/%s" % (PARAMETRO, it["chave"]))
    outros = [o for o in opcoes or [] if _chave(o.get("valor")) == "outros" and o.get("ativo", True)]
    if len(outros) != 1:
        raise RuntimeError("não achei a opção \"Outros\" no modal deste item (%d)" % len(outros))
    _gravar(aba, "POST", "%s/editar-item" % sc.API, json.dumps(pedido(a, it, outros[0], texto), ensure_ascii=False))
    # confere: lê de novo e compara o texto do "Outros" deste item
    try:
        it2 = achar(sc.buscar(aba, "%s/%s" % (sc.API, id_analise)), nome) or {}
    except (RuntimeError, OSError, ValueError) as e:  # gravou: quem chama marca como lançado, sem conferir
        return {"ok": False, "item": it["nome"], "conferido": False, "aviso": "gravou, mas não consegui ler de volta (%s): confira na tela" % e}
    r2 = it2.get("resultado") or {}
    gravado = [j.get("justificativa") for j in _justs(r2) if (j.get("parametroNcs") or {}).get("id") == outros[0].get("id")]
    ok = r2.get("statusResultadoAtec") == "REPROVADO" and [_igual(g) for g in gravado] == [_igual(texto)]
    return {"ok": ok, "item": it["nome"], "conferido": ok,
            "aviso": "" if ok else "gravou, mas a leitura de volta não bateu (status %s, %d texto(s)): confira na tela do SOL"
            % (r2.get("statusResultadoAtec"), len(gravado))}
