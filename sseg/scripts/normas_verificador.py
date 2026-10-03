"""Verificador independente: compara o .md convertido com o PDF original.
Nao importa o conversor. Referencias: palavras do PyMuPDF, texto do pdftotext (outro motor),
riscado do pymupdf4llm (outro detector) e desenho vetorial da pagina."""
import pymupdf, re, sys, json, subprocess, unicodedata, difflib
from collections import Counter, defaultdict

def nfk(s): return unicodedata.normalize('NFKC', s)
def ntok(s): return re.sub(r'[^\w]', '', nfk(s).lower())
def nstr(s): return re.sub(r'[^\w]', '', nfk(s).lower())
LIMPA = re.compile(r'<!--\s*(pág \d+|convertido de[^>]*|lido da imagem[^>]*)\s*-->|!\[[^\]]*\]\([^)]*\)|<br>|~~|\*\*|<!--\s*texto na figura:|-->')

def split_pages(md):
    parts = re.split(r'<!-- pág (\d+) -->', md)
    pages = defaultdict(str)
    for k in range(1, len(parts), 2): pages[int(parts[k])] += parts[k + 1]
    return pages

def margin_keys_words(doc):
    """linhas de cabecalho/rodape repetidas (mesma regra para todos os motores).
    Numero solto na margem so conta como numero de pagina se, na mesma faixa, so houver cabecalho repetido."""
    cnt = Counter(); per = []; first = {}
    for p in doc:
        H = p.rect.height; ls = defaultdict(list)
        for w in p.get_text('words'): ls[(w[5], w[6])].append(w)
        pl = []
        try: tbl = [pymupdf.Rect(t_.bbox) for t_ in p.find_tables().tables]
        except Exception: tbl = []
        for k, ws in ls.items():
            y0 = min(w[1] for w in ws); y1 = max(w[3] for w in ws)
            t = ' '.join(w[4] for w in ws)
            m = y1 < H * 0.12 or y0 > H * 0.88
            if m and any(r.contains(pymupdf.Point((ws[0][0] + ws[-1][2]) / 2, (y0 + y1) / 2)) for r in tbl): m = False
            pl.append([k, ws, t, m, y0, y1])
        per.append(pl)
        for k in {mkey(x[2]) for x in pl if x[3]}:
            cnt[k] += 1; first.setdefault(k, len(per) - 1)
    rep = {k: first[k] for k, n in cnt.items() if n >= 3 and len(re.findall(r'[^\W\d_]', k)) >= 15}
    out = []
    for pi_, pl in enumerate(per):
        for x in pl:
            if x[3] and re.fullmatch(r'[\d\s/de.ágin]*', x[2].lower()):
                viz = [o for o in pl if o is not x and min(o[5], x[5]) - max(o[4], x[4]) > 0]
                if any(not (o[3] and mkey(o[2]) in rep) for o in viz): x[3] = False
        out.append([tuple(x[:4]) for x in pl])
    return out, rep

def mkey(t):
    return re.sub(r'\d+', '#', re.sub(r'\s+', '', nfk(t).lower().replace('–', '-').replace('—', '-').strip()))

def is_marg(t, m, rep, pno=None):
    if not m: return False
    k = mkey(t)
    if k in rep: return True
    return re.fullmatch(r'(p[áa]g(ina)?\.?\s*)?\d{1,3}(\s*(de|/)\s*\d{1,3})?', t.strip().lower()) is not None

def pdf_words(doc):
    per, rep = margin_keys_words(doc)
    pages = []
    for pl in per:
        out = []; prev_end = False
        for k, lw, t, m in sorted(pl, key=lambda x: x[0]):
            if is_marg(t, m, rep): continue
            lws = [w[4] for w in sorted(lw, key=lambda w: w[7])]
            for idx, w in enumerate(lws):
                if idx == 0 and out and prev_end and w[:1].isalnum():
                    out[-1] = out[-1] + w
                else: out.append(w)
            prev_end = bool(lws) and lws[-1].endswith('-') and len(lws[-1]) > 1
        pages.append(out)
    return pages, rep

def pdftotext_str(pdf, rep):
    t = subprocess.run(['pdftotext', '-enc', 'UTF-8', pdf, '-'], capture_output=True, text=True).stdout
    pages = t.split('\f'); out = []
    for pno, pg in enumerate(pages):
        ls = pg.split('\n'); n = len(ls); keep = []
        for i, l in enumerate(ls):
            m = i < 6 or i > n - 6
            if is_marg(l, m, rep, pno): continue
            keep.append(l)
        out.append('\n'.join(keep))
    return out


def geo_blocks(doc, rep):
    """ordem geometrica (independe da ordem interna do PDF e do pdftotext):
    detecta a calha entre colunas, le faixa a faixa, coluna esquerda e depois direita.
    Devolve, por pagina, lista de blocos de texto (quebra em mudanca de coluna/faixa ou espaco vertical grande)."""
    out = []
    for pno, p in enumerate(doc):
        W, H = p.rect.width, p.rect.height
        ws = [w for w in p.get_text('words')]
        # linhas geometricas
        ws.sort(key=lambda w: ((w[1] + w[3]) / 2, w[0]))
        rows = []
        for w in ws:
            yc = (w[1] + w[3]) / 2; h = w[3] - w[1]
            for r in rows[-6:]:
                ov = min(w[3], r['y1']) - max(w[1], r['y0'])
                if ov > 0.5 * min(h, r['y1'] - r['y0']):
                    r['w'].append(w); break
            else:
                rows.append({'yc': yc, 'y0': w[1], 'y1': w[3], 'w': [w]})
        # calha: x que separa palavras dos dois lados no maior numero de linhas, cruzado por poucas
        gut = None; best = 0
        for x in range(int(W * 0.36), int(W * 0.64)):
            st = cr = 0
            for r in rows:
                if any(w[0] < x < w[2] for w in r['w']): cr += 1
                elif any(w[2] <= x for w in r['w']) and any(w[0] >= x for w in r['w']): st += 1
            sc = st - 2 * cr
            if st >= 5 and cr <= 0.5 * st and sc > best: best = sc; gut = x
        segs = []
        for r in rows:
            r['w'].sort(key=lambda w: w[0])
            if gut is None:
                segs.append(('F', r['yc'], r['w']))
            else:
                L = [w for w in r['w'] if w[2] <= gut]; Rr = [w for w in r['w'] if w[0] >= gut]; X = [w for w in r['w'] if w[0] < gut < w[2]]
                if X: segs.append(('F', r['yc'], r['w']))
                else:
                    if L: segs.append(('L', r['yc'], L))
                    if Rr: segs.append(('R', r['yc'], Rr))
        # faixas separadas por linhas de largura total
        order = []; band = []
        def flush():
            for col in ('L', 'R'):
                order.extend([s for s in band if s[0] == col])
            band.clear()
        for s in segs:
            if s[0] == 'F': flush(); order.append(s)
            else: band.append(s)
        flush()
        blocks = []; cur = []; last = None
        for s in order:
            t = ' '.join(w[4] for w in s[2])
            m = s[1] < H * 0.12 or s[1] > H * 0.88
            if is_marg(t, m, rep, pno): continue
            if last is not None and (s[0] != last[0] or s[1] - last[1] > 16 or s[1] < last[1]):
                blocks.append(cur); cur = []
            cur.append(t); last = s
        if cur: blocks.append(cur)
        out.append(['\n'.join(b) for b in blocks])
    return out

def xcount(tokens):
    c = Counter()
    for t in tokens:
        t = nfk(t).strip()
        if re.fullmatch(r'X\d{0,2}', t): c['X'] += 1
        elif t in ('-', '–', '—'): c['-'] += 1
    return c

ITEM_TXT = re.compile(r'(?m)^\s*(\d{1,2}(?:\.\d{1,3}){1,6})\.?\s+(?=[A-ZÀ-Ú“"(])')
ITEM_MD = re.compile(r'(?m)^(?:~~)?\*\*(\d{1,2}(?:\.\d{1,3}){1,6})\*\*\s')

def stoks(txt):
    raw = [x for x in re.split(r'\s+|<br>', re.sub(r'<[^>]+>|[*_]', ' ', txt)) if x]
    out = []
    for x in raw:
        if out and out[-1].endswith('-') and len(out[-1]) > 1 and x[:1].isalpha(): out[-1] += x
        else: out.append(x)
    return [ntok(x) for x in out]

def strike_words_ref(pdf, npages):
    import pymupdf4llm
    pymupdf4llm.use_layout(False)
    ch = pymupdf4llm.to_markdown(pdf, page_chunks=True, show_progress=False)
    res = {}
    for i, c in enumerate(ch):
        tx = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', c['text'])
        ws = stoks(' '.join(m.group(1) for m in re.finditer(r'~~(.+?)~~', tx, re.S)))
        res[i + 1] = Counter(w for w in ws if w)
    return res

def glyph_paths(page):
    n = 0
    for d in page.get_drawings():
        r = d['rect']
        if d.get('fill') is None: continue
        if 1.5 < r.width < 14 and 2.5 < r.height < 14 and sum(1 for it in d['items'] if it[0] == 'c') >= 2:
            n += 1
    return n

def verify(pdf, mdfile):
    doc = pymupdf.open(pdf); md = open(mdfile, encoding='utf-8').read()
    mdp = split_pages(md)
    R = {'pdf': pdf.split('/')[-1], 'md': mdfile.split('/')[-1]}
    pw, rep = pdf_words(doc)
    # V1 palavras
    P = Counter(ntok(w) for pg in pw for w in pg); P.pop('', None)
    mtext = LIMPA.sub(' ', md)
    M = Counter(ntok(w) for w in re.split(r'[\s|]+', mtext)); M.pop('', None)
    falt = {k: P[k] - M[k] for k in P if P[k] > M[k]}
    sobra = {k: M[k] - P[k] for k in M if M[k] > P[k]}
    for _rodada in range(4):
        # palavra faltante explicada por junção (ex.: SISBOM- MSCI) -> some em ambos os lados
        for k in list(sobra):
            for a in list(falt):
                if k.startswith(a) and k[len(a):] in falt and falt.get(a, 0) > 0:
                    b = k[len(a):]
                    n = min(sobra[k], falt[a], falt[b])
                    if n > 0:
                        sobra[k] -= n; falt[a] -= n; falt[b] -= n
        # e o inverso: palavra do PDF que o md separou (ex.: "fi=(∑M" -> "fi" "(∑M")
        for k in list(falt):
            for i_ in range(1, len(k)):
                a, b = k[:i_], k[i_:]
                if sobra.get(a, 0) > 0 and sobra.get(b, 0) > 0 and falt.get(k, 0) > 0:
                    n = min(falt[k], sobra[a], sobra[b]); falt[k] -= n; sobra[a] -= n; sobra[b] -= n

    falt = {k: v for k, v in falt.items() if v > 0}; sobra = {k: v for k, v in sobra.items() if v > 0}
    # resto que e so a mesma sequencia de letras quebrada em palavras diferentes (hifenizacao): mesmas letras dos dois lados
    if falt and Counter(''.join(k * n for k, n in falt.items())) == Counter(''.join(k * n for k, n in sobra.items())):
        R['V1_aviso_hifenizacao'] = sorted(falt); falt = {}; sobra = {}
    R['V1_palavras_faltando'] = sum(falt.values()); R['V1_ex_falt'] = sorted(falt, key=lambda k: -falt[k])[:12]
    R['V1_palavras_sobrando'] = sum(sobra.values()); R['V1_ex_sobra'] = sorted(sobra, key=lambda k: -sobra[k])[:12]
    # V2 X e traços por pagina
    v2 = []
    for i, pg in enumerate(pw):
        a = xcount(pg)
        cells = re.split(r'[\s|]+', LIMPA.sub(' ', mdp.get(i + 1, '')).replace('\\|', ' '))
        b = xcount(cells)
        if a != b: v2.append((i + 1, dict(a), dict(b)))
    R['V2_paginas_X_divergente'] = v2
    # V3 ordem: numeracao logica (sucessor valido) + todo item do PDF presente no md
    gb = geo_blocks(doc, rep)
    pt = ['\n'.join(b) for b in gb]
    seqp = []
    REFW = re.compile(r'(?i)\b(item|itens|subitem|subitens|no|nos|do|dos|ao|aos|e|ou|a|o|conforme|vide|ver)\s*$')
    for pg in pt:
        prev = ''
        for line in pg.split('\n'):
            if not line.strip(): continue
            m = ITEM_TXT.match(line)
            if m and not (prev and not re.search(r'[.:;!?]["”)]?\s*$', prev) and REFW.search(prev)):
                seqp.append(m.group(1))
            prev = line
    seqm = [m.group(1) for m in ITEM_MD.finditer(md)]
    seql = [m.group(1) for m in re.finditer(r'(?m)^(?:~~)?\*\*(\d{1,2}(?:\.\d{1,3}){0,6})\*\*\s', md)]
    T = lambda x: tuple(int(v) for v in x.split('.'))
    retro = []; salto = []; reinicio = []
    for a, b in zip(seql, seql[1:]):
        ta, tb = T(a), T(b)
        ok = tb == (1,) or tb == ta + (1,) or any(tb == ta[:k] + (ta[k] + 1,) for k in range(len(ta)))
        if not ok:
            if len(tb) == 1 and tb <= ta: reinicio.append(f'{a} -> {b}')
            else: (retro if tb <= ta else salto).append(f'{a} -> {b}')
    em_tab = re.findall(r'(?:\||<br>)\s*(?:~~)?(\d{1,2}(?:\.\d{1,3}){1,6})\.?\s', md)
    pares_pdf = set(zip(seqp, seqp[1:]))
    orig = [x for x in retro if tuple(x.split(' -> ')) in pares_pdf]
    retro = [x for x in retro if x not in orig]
    R['V3_aviso_numeracao_do_proprio_pdf'] = orig
    faltam = list((Counter(seqp) - Counter(seqm) - Counter(em_tab)).elements())
    R['V3_itens_pdf'] = len(seqp); R['V3_itens_md'] = len(seqm)
    R['V3_retrocessos'] = retro; R['V3_aviso_reinicio_numeracao'] = reinicio; R['V3_saltos'] = salto; R['V3_itens_ausentes_no_md'] = faltam
    # V4 integridade: paragrafo = trecho continuo do pdftotext, ou 2-3 pedacos que terminam/comecam em quebra de bloco
    def mk(blocklists):
        S = ''
        for b in blocklists:
            nb = nstr(b)
            if not nb: continue
            S += '^' + nb + ('§' if re.search(r'[.:;!?]["”)]?\s*$', b) and len(nb) > 6 else '¦')
        return S, re.sub('[\\^¦§]', '', S)
    ptt = pdftotext_str(pdf, rep)
    REFS = [mk([b for pg in gb for b in pg]), mk([b for pg in ptt for b in re.split(r'\n\s*\n', pg)])]
    def maxpref(t, S):
        lo, hi = 0, len(t)
        while lo < hi:
            m = (lo + hi + 1) // 2
            if t[:m] in S: lo = m
            else: hi = m - 1
        return lo
    def found_ref(t, bigS, big):
        if t in big: return True
        p = maxpref(t, big)
        for k in range(p, max(0, p - 400), -1):
            if (t[:k] + '¦') in bigS:
                b = t[k:]
                if ('^' + b) in bigS: return True
                q = maxpref('^' + b, bigS) - 1
                for k2 in range(q, max(0, q - 400), -1):
                    if ('^' + b[:k2] + '¦') in bigS and ('^' + b[k2:]) in bigS: return True
        return False
    def found(t): return any(found_ref(t, S, B) for S, B in REFS)
    # paginas com texto girado (tabelas em paisagem): as referencias embaralham; V4 nao se aplica
    girada = set()
    for i_, p_ in enumerate(doc):
        tot_ = rot_ = 0
        for b_ in p_.get_text('dict')['blocks']:
            for l_ in b_.get('lines', []):
                n_ = sum(len(s['text']) for s in l_['spans']); tot_ += n_
                if abs(l_['dir'][0]) < 0.9: rot_ += n_
        if tot_ and rot_ > 0.3 * tot_: girada.add(i_ + 1)
    R['V4_aviso_paginas_texto_girado'] = sorted(girada)
    pars = []
    for pg_, txt_ in mdp.items():
        if pg_ in girada: continue
        pars += re.split(r'\n\s*\n', txt_)
    bad = []
    for par in pars:
        s_ = par.strip()
        if not s_ or s_.startswith('|') or s_.startswith('![') or s_.startswith('<!--'): continue
        t = nstr(LIMPA.sub(' ', s_))
        if len(t) < 25: continue
        if not found(t): bad.append(s_[:110])
    R['V4_paragrafos_nao_continuos'] = len(bad); R['V4_ex'] = bad[:40]
    # V5 riscado: md x pymupdf4llm
    ref = strike_words_ref(pdf, len(doc)); v5 = []; v5w = []
    for i in range(1, len(doc) + 1):
        ws = stoks(' '.join(m.group(1) for m in re.finditer(r'~~(.+?)~~', mdp.get(i, ''), re.S)))
        mine = Counter(w for w in ws if w); r = ref.get(i, Counter())
        # a referencia marca como riscada a letra que encosta numa borda de tabela (ex.: "seguranç~~a~~"); token de 1-2 letras nao conta
        r = Counter({k: n for k, n in r.items() if len(k) > 2})
        # comparacao por conjunto de palavras (a referencia repete o texto das tabelas)
        mine_str = nstr(' '.join(m.group(1) for m in re.finditer(r'~~(.+?)~~', mdp.get(i, ''), re.S)))
        falta = [k for k in set(r) - set(mine) if k not in mine_str]
        d1 = len(falta); d2 = len(set(mine) - set(r))
        if d1: v5.append((i, 'faltam riscar', d1))
        if d2: v5w.append((i, 'riscadas a mais que a referência (conferir na imagem)', d2))
    R['V5_riscado_faltando'] = v5; R['V5_aviso_riscado_a_mais'] = v5w
    # V6 tinta sem texto: glifo vetorial ou imagem sem figura no md
    xc = Counter(i[0] for p in doc for i in p.get_images())
    v6 = []
    for i, p in enumerate(doc):
        g = glyph_paths(p)
        imgs = [x for x in p.get_image_info(xrefs=True) if xc.get(x.get('xref'), 0) < 3 and pymupdf.Rect(x['bbox']).width > 12 and pymupdf.Rect(x['bbox']).height > 12]
        has_fig = '![' in mdp.get(i + 1, '')
        if (g or imgs) and not has_fig: v6.append((i + 1, 'glifos_vetor', g, 'imagens', len(imgs)))
    R['V6_tinta_sem_texto'] = v6
    R['APROVADO'] = (R['V1_palavras_faltando'] == 0 and R['V1_palavras_sobrando'] == 0 and not v2 and not retro and not faltam and not bad and not v5 and not v6)
    return R

if __name__ == '__main__':
    print('RESULT:' + json.dumps(verify(sys.argv[1], sys.argv[2]), ensure_ascii=False))
