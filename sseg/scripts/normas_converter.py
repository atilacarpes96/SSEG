"""Conversor PDF -> Markdown das normas (SSEG).
Texto na ordem do PDF, tabelas celula a celula pela posicao dos caracteres,
expoentes de nota (X¹), texto riscado (~~), marcador de pagina e figuras em PNG."""
import pymupdf, re, sys, os, json
from collections import Counter, defaultdict

VOCAB = set()
SUP = str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹')
ITEM = re.compile(r'^(\d{1,2}(?:\.\d{1,3}){0,6})\.?\s+(?=\S)')
NOVO_PAR = re.compile(r'^([□☐■●◦]|[a-z]\.\s+[A-ZÀ-ÚÑº]|\([A-Z0-9]{1,3}\)\s|\d{1,2}(?:\.\d{1,3}){0,6}\.?\s*$|\d{1,2}(?:\.\d{1,3}){0,6}\.?\s+[A-ZÀ-Ú“"(]|[a-z]\)\s|[IVXL]+\s*[-–—]\s|Art\.\s|§|Nota|NOTA|Notas|NOTAS|Tabela|TABELA|Figura|FIGURA|Anexo|ANEXO|Par[áa]grafo|•|▪|-\s)')
TERMINAL = re.compile(r'[.:;!?]["”)]?(~~)?\s*$')
MARGEM = 0.075

def norm_line(s):
    s = s.strip().lower().replace('–', '-').replace('—', '-')
    return re.sub(r'\d+', '#', re.sub(r'\s+', '', s))

def strike_segs(page):
    segs = []
    for d in page.get_drawings():
        for it in d['items']:
            if it[0] == 'l':
                p1, p2 = it[1], it[2]
                if abs(p1.y - p2.y) < 0.8 and abs(p1.x - p2.x) > 2:
                    segs.append((min(p1.x, p2.x), max(p1.x, p2.x), (p1.y + p2.y) / 2))
            elif it[0] == 're':
                r = it[1]
                if r.height < 1.6 and r.width > 2:
                    segs.append((r.x0, r.x1, (r.y0 + r.y1) / 2))
    return segs

def struck(b, segs):
    x0, y0, x1, y1 = b; h = y1 - y0; w = max(x1 - x0, 0.1)
    return any(min(c, x1) - max(a, x0) >= 0.3 * w and y0 + 0.3 * h <= y <= y1 - 0.3 * h for a, c, y in segs)

def inside(b, r, tol=0.5):
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    return r[0] - tol <= cx <= r[2] + tol and r[1] - tol <= cy <= r[3] + tol

def chars_of(page, segs):
    """lista de linhas: cada linha = lista de (char, bbox, sup, riscado, bloco)"""
    lines = []; lid = 0
    d = page.get_text('rawdict', sort=False)
    for bi, bl in enumerate(d['blocks']):
        if bl['type'] != 0: continue
        for ln in bl['lines']:
            cs = []; lid += 1
            for sp in ln['spans']:
                sup = bool(sp['flags'] & 1)
                for ch in sp['chars']:
                    cc = ' ' if ord(ch['c']) < 32 else ch['c']
                    cs.append((cc, ch['bbox'], sup, struck(ch['bbox'], segs) if cc.strip() else None, bi, sp['size'], lid))
            if cs:
                ded = []
                for c in cs:
                    if c[0].strip() and any(d[0] == c[0] and abs(d[1][0] - c[1][0]) < 0.35 * (c[1][2] - c[1][0] + 0.1) and abs(d[1][1] - c[1][1]) < 1.0 for d in ded[-4:]):
                        continue
                    ded.append(c)
                lines.append({'chars': ded, 'bbox': ln['bbox'], 'block': bi})
    return lines

def render(cs, gap=0.45):
    """chars -> texto; expoente so se a fonte for menor que a da linha; ~~ por trechos, espacos fora do marcador"""
    if not cs: return ''
    sizes=[c[5] for c in cs if c[0].strip()] or [1]
    ref=max(sizes)
    st=[c[3] for c in cs]
    for k in range(len(st)):
        if st[k] is None:
            a=next((st[x] for x in range(k-1,-1,-1) if st[x] is not None),False)
            b=next((st[x] for x in range(k+1,len(st)) if st[x] is not None),False)
            st[k]=bool(a and b)
    out=[]; buf=''; cur=False
    def flush():
        nonlocal buf
        if not buf: return
        if cur:
            m=re.match(r'^(\s*)(.*?)(\s*)$',buf,re.S)
            out.append(m.group(1)+('~~'+m.group(2)+'~~' if m.group(2) else '')+m.group(3))
        else: out.append(buf)
        buf=''
    prev=None; pprev=None
    for c,k in zip(cs,st):
        ch=c[0]
        g_=c[1][0]-prev[1][2] if prev is not None else 0
        if prev is not None and ch.strip() and prev[0].strip() and g_ > gap*max(c[5],1) and not (c[5] < 0.85*prev[5] and g_ < 0.6*prev[5]) and not (prev[0] == '-' and pprev is not None and pprev[0].isalnum() and prev[1][0] - pprev[1][2] < 0.15*max(prev[5],1)):
            buf+=' '
        pprev=prev; prev=c
        if c[2] and ch.isdigit() and c[5]<=0.85*ref: ch=ch.translate(SUP)
        if k!=cur: flush(); cur=k
        buf+=ch
    flush()
    return ''.join(out)

def repeated_margin_lines(doc):
    cnt = Counter(); first = {}
    for pno, p in enumerate(doc):
        H = p.rect.height; seen = set()
        for b in p.get_text('dict')['blocks']:
            if b['type'] != 0: continue
            for ln in b['lines']:
                y0, y1 = ln['bbox'][1], ln['bbox'][3]
                if y1 < H * MARGEM * 1.6 or y0 > H * (1 - MARGEM * 1.6):
                    t = ''.join(s['text'] for s in ln['spans'])
                    k = norm_line(t)
                    if k and k not in seen:
                        seen.add(k); cnt[k] += 1; first.setdefault(k, pno)
    return {k: first[k] for k, n in cnt.items() if n >= 3 and len(re.findall(r'[^\W\d_]', k)) >= 15}

def is_margin(line, H, rep, pno=None, lines=()):
    y0, y1 = line['bbox'][1], line['bbox'][3]
    if not (y1 < H * MARGEM * 1.6 or y0 > H * (1 - MARGEM * 1.6)): return False
    t = ''.join(c[0] for c in line['chars']).strip()
    k = norm_line(t)
    if k in rep: return True
    if re.fullmatch(r'(p[áa]g(ina)?\.?\s*)?\d{1,3}(\s*(de|/)\s*\d{1,3})?', t.lower()) is None: return False
    # numero de pagina: so se, na mesma faixa, nao houver outro texto (fora cabecalho repetido)
    for o in lines:
        if o is line: continue
        if min(o['bbox'][3], y1) - max(o['bbox'][1], y0) > 0:
            ot = ''.join(c[0] for c in o['chars']).strip()
            if ot and norm_line(ot) not in rep: return False
    return True

def figure_regions(page, tabs, rep_xrefs, lines=()):
    R = page.rect; regs = []
    for info in page.get_image_info(xrefs=True):
        r = pymupdf.Rect(info['bbox']) & R
        if r.is_empty or r.width < 12 or r.height < 12: continue
        if info.get('xref') in rep_xrefs: continue
        regs.append(r)
    try:
        cl = page.cluster_drawings()
    except Exception:
        cl = []
    for r in cl:
        r = pymupdf.Rect(r) & R
        if r.width < 25 or r.height < 25: continue
        # moldura em volta de texto corrido (formularios) nao e figura
        longas = sum(1 for ln in lines if inside(ln['bbox'], r, 1) and len(''.join(c[0] for c in ln['chars']).strip()) > 40)
        if longas >= 2: continue
        if r.get_area() > 0.8 * R.get_area(): continue
        if any((r & t).get_area() > 0.5 * r.get_area() for t in tabs): continue
        regs.append(r)
    # junta regioes sobrepostas
    out = []
    for r in sorted(regs, key=lambda r: (r.y0, r.x0)):
        for o in out:
            if (o & r).get_area() > 0 or o.intersects(r):
                o |= r; break
        else:
            out.append(pymupdf.Rect(r))
    return [r for r in out if not any((r & t).get_area() > 0.6 * r.get_area() for t in tabs)]

def cell_text(cs):
    """agrupa pela linha do PDF; linha de expoente (fonte menor) entra na linha que sobrepoe; ordena por x"""
    cs=[c for c in cs if c[0].strip()]
    if not cs: return ''
    g=defaultdict(list)
    for c in cs: g[c[6]].append(c)
    L=[{'c':v,'y0':min(c[1][1] for c in v),'y1':max(c[1][3] for c in v),'sz':max(c[5] for c in v)} for v in g.values()]
    big=max(x['sz'] for x in L)
    main=[x for x in L if x['sz']>0.85*big or len(L)==1]
    small=[x for x in L if x not in main]
    # so e expoente a linha pequena e curta (ate 3 caracteres); o resto e linha normal
    for x in list(small):
        if len(x['c'])>3: small.remove(x); main.append(x)
    for x in small:
        best=None
        for m in main:
            ov=min(x['y1'],m['y1'])-max(x['y0'],m['y0'])
            if ov>0.3*(x['y1']-x['y0']) and (best is None or ov>best[0]): best=(ov,m)
        if best: best[1]['c']+=x['c']
        else: main.append(x)
    # linhas do PDF que estao na mesma altura (texto quebrado em pedacos) viram uma so
    main.sort(key=lambda x:(x['y0']+x['y1'])/2)
    merged=[]
    for m in main:
        if merged:
            p=merged[-1]; h=min(m['y1']-m['y0'],p['y1']-p['y0'])
            mx0=min(c[1][0] for c in m['c']); mx1=max(c[1][2] for c in m['c'])
            px0=min(c[1][0] for c in p['c']); px1=max(c[1][2] for c in p['c'])
            if min(m['y1'],p['y1'])-max(m['y0'],p['y0'])>0.7*h and (mx0>=px1-1 or px0>=mx1-1):
                p['c']+=m['c']; p['y0']=min(p['y0'],m['y0']); p['y1']=max(p['y1'],m['y1']); continue
        merged.append(m)
    parts=[render(sorted(x['c'],key=lambda c:c[1][0]),gap=0.10).strip() for x in merged]
    s=''
    for p in parts:
        if not s: s=p
        elif s.endswith('-~~') and p.startswith('~~') and p[2:3].isalnum(): s=dehyph(s[:-2],p[2:],VOCAB)
        elif s.endswith('-') and not s.endswith(' -') and p[:1].isalnum(): s=dehyph(s,p,VOCAB)
        else: s+='<br>'+p
    s=re.sub(r'(?<=\S) {2,}',' ',s)
    return s.replace('|','\\|')

def ink(page,rect,dpi=200):
    import numpy as np
    r=pymupdf.Rect(rect)+(1.6,1.6,-1.6,-1.6)
    if r.is_empty or r.width<2 or r.height<2: return None
    pix=page.get_pixmap(dpi=dpi,clip=r,colorspace=pymupdf.csGRAY)
    a=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.stride)[:,:pix.width]
    m=a<128
    if m.sum()<12: return None
    ys,xs=np.where(m); m=m[ys.min():ys.max()+1,xs.min():xs.max()+1]
    from PIL import Image
    im=Image.fromarray((m*255).astype('uint8')).resize((40,40))
    return (np.array(im)>127, m.shape[1]/m.shape[0])

def match_glyph(page,cb,cands):
    t=ink(page,cb)
    if t is None: return None
    best=(0,None)
    for txt,v in cands:
        inter=(t[0]&v[0]).sum(); uni=(t[0]|v[0]).sum()
        sc=inter/max(uni,1)*min(t[1],v[1])/max(t[1],v[1])
        if sc>best[0]: best=(sc,txt)
    return best

def table_md(tab, pchars, segs, page, pno, stats, glyphs=(), owned=()):
    rows=[]; ys=[]; usados=set()
    for row in tab.rows:
        cells=[]
        for cb in row.cells:
            if cb is None: cells.append(None); continue
            mine=[c for c in pchars if id(c) not in usados and inside(c[1],cb)]
            usados.update(id(c) for c in mine)
            cells.append((cb,mine))
        rows.append(cells); ys.append(row.bbox[1])
    # caracteres dentro da tabela que nao cairam em nenhuma celula (celula mesclada): vai para a celula a esquerda na mesma linha
    tb_=pymupdf.Rect(tab.bbox)
    ow=set(id(c) for c in owned)
    sobras=[c for c in list(pchars) if id(c) not in usados and c[0].strip() and (inside(c[1],tb_) or id(c) in ow)]
    for c in sobras:
        cy=(c[1][1]+c[1][3])/2; cx=(c[1][0]+c[1][2])/2
        ri=next((k for k,row in enumerate(tab.rows) if row.bbox[1]-0.5<=cy<=row.bbox[3]+0.5),None)
        if ri is None:
            ri=min(range(len(tab.rows)),key=lambda k:min(abs(cy-tab.rows[k].bbox[1]),abs(cy-tab.rows[k].bbox[3])))
        ncol=len(rows[ri])
        x0s=[min([r_[k][0][0] for r_ in rows if k<len(r_) and r_[k] is not None] or [1e9]) for k in range(ncol)]
        ks=[k for k in range(ncol) if x0s[k]<=cx+0.5]
        k=ks[-1] if ks else 0
        if rows[ri][k] is None:
            rows[ri][k]=((x0s[k] if x0s[k]<1e9 else c[1][0], tab.rows[ri].bbox[1], cx+1, tab.rows[ri].bbox[3]), [])
        x=rows[ri][k]
        x[1].append(c); usados.add(id(c)); stats['chars_celula_mesclada']+=1
    # junta linhas que a tabela partiu por causa de texto riscado
    merged=[]
    for k,r in enumerate(rows):
        y=ys[k]
        if merged and any(abs(sy-y)<1.2 for _,_,sy in segs) and (r[0] is None or not r[0][1]):
            prev=merged[-1]
            for ci,c in enumerate(r):
                if c is None or ci>=len(prev): continue
                if prev[ci] is None: prev[ci]=c
                else: prev[ci]=(pymupdf.Rect(prev[ci][0])|pymupdf.Rect(c[0]),prev[ci][1]+c[1])
            stats['linhas_riscadas_juntadas']+=1
        else: merged.append(list(r))
    txt=[[None if c is None else cell_text(c[1]) for c in r] for r in merged]
    # celula com tinta e sem texto: glifo desenhado como vetor
    cands=None
    for ri,r in enumerate(merged):
        for ci,c in enumerate(r):
            if c is None or txt[ri][ci]: continue
            if cands is None:
                cands=[]; seen=set()
                for rj,rr in enumerate(merged):
                    for cj,cc in enumerate(rr):
                        t=txt[rj][cj]
                        if cc is not None and t and len(t)<=6 and (t not in seen or len(cands)<60):
                            v=ink(page,cc[0])
                            if v is not None: cands.append((t,v)); seen.add(t)
            m=match_glyph(page,c[0],cands)
            if m is None: continue
            fn=f"{stats['_base']}-p{pno:03d}-cel{ri+1}x{ci+1}.png"
            page.get_pixmap(dpi=150,clip=pymupdf.Rect(c[0])).save(os.path.join(stats['_imgdir'],fn))
            txt[ri][ci]=f"![célula sem texto no PDF — ver imagem]({stats['_rel']}/{fn})"
            stats['celulas_so_imagem']+=1
    # glifo desenhado como vetor dentro de celula com texto (ex.: expoente de nota)
    for ri,r in enumerate(merged):
        for ci,c in enumerate(r):
            if c is None or not txt[ri][ci] or txt[ri][ci].startswith('!['): continue
            cb=pymupdf.Rect(c[0])
            if any(cb.contains(pymupdf.Point((g.x0+g.x1)/2,(g.y0+g.y1)/2)) for g in glyphs):
                fn=f"{stats['_base']}-p{pno:03d}-cel{ri+1}x{ci+1}.png"
                page.get_pixmap(dpi=150,clip=cb).save(os.path.join(stats['_imgdir'],fn))
                txt[ri][ci]+=f" ![parte desenhada — ver imagem]({stats['_rel']}/{fn})"
                stats['celulas_com_desenho']+=1
    rows=[[t or '' for t in r] for r in txt]
    if not rows: return ''
    n=max(len(r) for r in rows)
    rows=[r+['']*(n-len(r)) for r in rows]
    md=['|'+'|'.join(rows[0])+'|','|'+'|'.join(['---']*n)+'|']
    md+=['|'+'|'.join(r)+'|' for r in rows[1:]]
    return '\n'.join(md)

def dehyph(a, b, vocab):
    """a termina com '-' no fim da linha"""
    m1 = re.search(r'(\w+)-$', a); m2 = re.match(r'(\w+)', b)
    if not m1 or not m2: return a + b
    w1, w2 = m1.group(1), m2.group(1)
    if w2[0].isupper() or w2[0].isdigit(): return a + b          # SISBOM-MSCI, ICP-Brasil
    if (w1 + '-' + w2).lower() in vocab and (w1 + w2).lower() not in vocab: return a + b
    return a[:-1] + b

def convert(pdf, outmd, imgdir, relimg):
    doc = pymupdf.open(pdf)
    rep = repeated_margin_lines(doc)
    xc = Counter(i[0] for p in doc for i in p.get_images())
    rep_xrefs = {x for x, n in xc.items() if n >= 3}
    global VOCAB
    vocab = VOCAB = set(re.findall(r'\w+(?:-\w+)*', ' '.join(p.get_text() for p in doc).lower()))
    base = os.path.splitext(os.path.basename(outmd))[0]
    paras = []          # cada item: dict(tipo, texto)
    stats = Counter(); stats['_base']=base; stats['_imgdir']=imgdir; stats['_rel']=relimg
    for pi, page in enumerate(doc):
        H = page.rect.height
        segs = strike_segs(page)
        try: tabs_all = page.find_tables().tables
        except Exception: tabs_all = []
        tb_raw = [pymupdf.Rect(t.bbox) for t in tabs_all]
        tabs = [t for t in tabs_all if t.row_count >= 2 and t.col_count >= 2]
        # tabela que corta palavra ao meio nao e tabela (rotulos de figura): vira figura
        pw_ = page.get_text('words'); demov = []
        def cell_at(t, x, y):
            for ri, row in enumerate(t.rows):
                for ci, cb in enumerate(row.cells):
                    if cb and cb[0] - 0.3 <= x <= cb[2] + 0.3 and cb[1] - 0.3 <= y <= cb[3] + 0.3: return (ri, ci)
            return None
        for t in list(tabs):
            R_ = pymupdf.Rect(t.bbox); cortes = 0
            for w in pw_:
                if len(w[4]) < 3 or not R_.intersects(pymupdf.Rect(w[:4])): continue
                yc = (w[1] + w[3]) / 2
                a = cell_at(t, w[0] + 1.2, yc); b = cell_at(t, w[2] - 1.2, yc)
                if (a and b and a != b) or (bool(a) != bool(b)): cortes += 1
            if cortes:
                tabs.remove(t); demov.append(R_); stats['tabelas_viraram_figura'] += 1
                continue
            # "tabela" que e so moldura em volta de texto corrido: todo o texto numa coluna so
            porcol = Counter()
            for w in pw_:
                if not inside(w[:4], R_): continue
                ca = cell_at(t, (w[0] + w[2]) / 2, (w[1] + w[3]) / 2)
                porcol[ca[1] if ca else -1] += 1
            tot = sum(porcol.values())
            colw = 0
            dom = porcol.most_common(1)[0][0] if porcol else -1
            for row in t.rows:
                if dom >= 0 and dom < len(row.cells) and row.cells[dom]:
                    colw = max(colw, row.cells[dom][2] - row.cells[dom][0])
            if t.col_count >= 2 and tot > 30 and porcol.most_common(1)[0][1] > 0.95 * tot and colw > 0.7 * R_.width:
                tabs.remove(t); stats['molduras_desfeitas'] += 1
        tb = [pymupdf.Rect(t.bbox) for t in tabs]
        lines = chars_of(page, segs)
        figs = figure_regions(page, tb, rep_xrefs, lines) + demov
        pwords = page.get_text('words')
        glyphs = [pymupdf.Rect(d['rect']) for d in page.get_drawings() if d.get('fill') is not None and 1.5 < d['rect'].width < 14 and 2.5 < d['rect'].height < 14 and sum(1 for it in d['items'] if it[0] == 'c') >= 2]
        pchars = [c for ln in lines for c in ln['chars']]
        hit = [c for c in pchars if c[3]]
        rsegs = [sg for sg in segs if any(min(sg[1], c[1][2]) - max(sg[0], c[1][0]) >= 0.3 * max(c[1][2]-c[1][0], 0.1) and c[1][1]+0.3*(c[1][3]-c[1][1]) <= sg[2] <= c[1][3]-0.3*(c[1][3]-c[1][1]) for c in hit)]
        # elementos em ordem de fluxo
        elems = []; done_t = set(); done_f = set(); owned = defaultdict(list)
        paras.append({'tipo': 'pag', 'texto': f'<!-- pág {pi + 1} -->'})
        # pagina com texto girado (tabela em paisagem): a estrutura de colunas so a imagem preserva
        tot_ = rot_ = 0
        for b_ in page.get_text('dict')['blocks']:
            for l_ in b_.get('lines', []):
                n_ = sum(len(x['text']) for x in l_['spans']); tot_ += n_
                if abs(l_['dir'][0]) < 0.9: rot_ += n_
        if tot_ and rot_ > 0.3 * tot_:
            fnp = f'{base}-p{pi + 1:03d}-pagina.png'
            page.get_pixmap(dpi=110).save(os.path.join(imgdir, fnp))
            paras.append({'tipo': 'fig', 'texto': f'![Página {pi + 1} inteira — tabela girada, a estrutura das colunas está na imagem]({relimg}/{fnp})'})
            stats['paginas_giradas_com_imagem'] += 1
        for ln in lines:
            if is_margin(ln, H, rep, pi, lines) and not any(r.contains(pymupdf.Point((ln['bbox'][0] + ln['bbox'][2]) / 2, (ln['bbox'][1] + ln['bbox'][3]) / 2)) for r in tb_raw):
                stats['margem'] += 1; continue
            fc = ln['chars'][0][1]
            cands_t = [i for i, r in enumerate(tb) if inside(ln['bbox'], r, 1)]
            ti = min(cands_t, key=lambda i: tb[i].get_area()) if cands_t else None
            if ti is not None:
                owned[ti].extend(ln['chars'])
                if ti not in done_t:
                    done_t.add(ti); elems.append(('tab', ti))
                continue
            fi = next((i for i, r in enumerate(figs) if inside(ln['bbox'], r, 1)), None)
            ltx = ''.join(c[0] for c in ln['chars']).strip()
            if fi is not None and (ITEM.match(ltx) and re.match(r'\d{1,2}\.\d', ltx) or len(ltx) > 70):
                fi = None   # linha de corpo de texto encostada na figura nao e rotulo
            if fi is not None:
                if fi not in done_f:
                    done_f.add(fi); elems.append(('fig', fi))
                elems.append(('figtxt', fi, ln))
                continue
            elems.append(('lin', ln))
        for i in range(len(tb)):
            if i not in done_t: elems.append(('tab', i))
        for i in range(len(figs)):
            if i not in done_f: elems.append(('fig', i))
        soltos = [g for g in glyphs if not any(t.contains(g) for t in tb) and not any(f.intersects(g) for f in figs)]
        grupos = []
        for g in soltos:
            for G in grupos:
                if (G + (-20, -8, 20, 8)).intersects(g): G |= g; break
            else: grupos.append(pymupdf.Rect(g))
        for G in grupos:
            figs.append(G + (-6, -4, 6, 4)); elems.append(('fig', len(figs) - 1))
        figtxt = defaultdict(list); usadas_fig = set()
        for e in elems:
            if e[0] == 'figtxt':
                lb = e[2]['bbox']
                ws_ = []
                for wi, w in enumerate(pwords):
                    if wi not in usadas_fig and inside(w[:4], lb, 1):
                        usadas_fig.add(wi); ws_.append(w[4])
                jn = []
                for w in ws_:
                    if jn and jn[-1].endswith('-') and len(jn[-1]) > 1 and w[:1].isalpha(): jn[-1] += w
                    else: jn.append(w)
                figtxt[e[1]].append(' '.join(jn))
        for e in elems:
            if e[0] == 'tab':
                stats['tabelas'] += 1
                paras.append({'tipo': 'tab', 'texto': table_md(tabs[e[1]], [c for c in pchars if not any(j != e[1] and tb[e[1]].contains(tb[j]) and inside(c[1], tb[j]) for j in range(len(tb)))], rsegs, page, pi + 1, stats, glyphs, [c for c in owned[e[1]] if not any(j != e[1] and tb[e[1]].contains(tb[j]) and inside(c[1], tb[j]) for j in range(len(tb)))])})
            elif e[0] == 'fig':
                stats['figuras'] += 1
                r = figs[e[1]]
                fn = f'{base}-p{pi + 1:03d}-{e[1] + 1}.png'
                page.get_pixmap(dpi=110, clip=r).save(os.path.join(imgdir, fn))
                t = ' '.join(x for x in figtxt.get(e[1], []) if x)
                t = re.sub(r'(\w)- (?=[a-zà-ú])', r'\1-', t)
                s = f'![Figura da pág. {pi + 1}]({relimg}/{fn})'
                if t: s += f'\n<!-- texto na figura: {t} -->'
                paras.append({'tipo': 'fig', 'texto': s})
            elif e[0] == 'lin':
                ln = e[1]; txt = render(ln['chars']).rstrip()
                if not txt.strip(): continue
                last = next((p for p in reversed(paras) if p['tipo'] in ('par', 'pag')), None)
                prev = paras[-1]
                lt = txt.lstrip()
                ltc = lt[2:] if lt.startswith('~~') else lt
                cont_ok = prev['tipo'] == 'par' or (prev['tipo'] == 'pag' and len(paras) >= 2 and paras[-2]['tipo'] == 'par')
                tgt = prev if prev['tipo'] == 'par' else (paras[-2] if cont_ok else None)
                novo = True
                so_num = tgt is not None and re.fullmatch(r'\d{1,2}(?:\.\d{1,3}){0,6}\.?', tgt['texto'].strip())
                if so_num and ltc[:1].islower() and tgt.get('antes') is not None and not TERMINAL.search(tgt['antes']['texto']):
                    # era uma referencia ("no item / 4.6.7 desta"), nao um item novo
                    ant = tgt['antes']; num = tgt['texto'].strip()
                    paras.remove(tgt)
                    ant['texto'] += ' ' + num + ' ' + lt; ant['block'] = (pi, ln['block']); ant['ult'] = txt
                    continue
                if so_num and not NOVO_PAR.match(ltc):
                    novo = False
                elif tgt is not None and re.match(r'^\d{1,2}(?:\.\d{1,3}){0,6}\.?(\s|$)', ltc) and not TERMINAL.search(tgt['texto']) and re.search(r'(?i)\b(item|itens|subitem|subitens|no|nos|do|dos|ao|aos|e|ou|a|o|conforme|vide|ver)\s*$', tgt['texto']):
                    novo = False   # numero no inicio da linha e continuacao de referencia ("no item / 7.5.2. Contudo")
                elif tgt is not None and not NOVO_PAR.match(ltc):
                    same_block = tgt.get('block') == (pi, ln['block'])
                    ends = TERMINAL.search(tgt['texto'])
                    if same_block and not (ends and ltc[:1].isupper() and len(tgt['ult']) < 0.75 * tgt['larg']):
                        novo = False
                    elif not same_block and not ends and (ltc[:1].islower() or ltc[:1] in '(,;'):
                        novo = False
                if not novo and tgt['texto'].lstrip('~').startswith(('□', '☐')) and ltc[:1].isupper():
                    novo = True   # campo do formulario abaixo da caixa de marcar
                if not novo:
                    if prev['tipo'] == 'pag':
                        tgt['texto'] += ' ' + prev['texto']; paras.pop()
                    a = tgt['texto']
                    if a.endswith('-~~') and lt.startswith('~~') and lt[2:3].isalpha():
                        tgt['texto'] = dehyph(a[:-2], lt[2:], vocab)
                    else:
                        tgt['texto'] = dehyph(a, lt, vocab) if a.endswith('-') and not a.endswith(' -') else a + ' ' + lt
                    tgt['block'] = (pi, ln['block']); tgt['ult'] = txt
                    tgt['larg'] = max(tgt['larg'], ln['bbox'][2] - ln['bbox'][0])
                else:
                    paras.append({'tipo': 'par', 'texto': lt, 'block': (pi, ln['block']), 'ult': txt,
                                  'larg': ln['bbox'][2] - ln['bbox'][0], 'antes': tgt})
    out = []
    for p in paras:
        t = p['texto']
        if p['tipo'] == 'par':
            t = re.sub(r'[ \t]{2,}', ' ', t)
            t = t.replace('~~ ~~', ' ')
            pre = '~~' if t.startswith('~~') else ''
            tt = t[len(pre):]
            m = ITEM.match(tt)
            if m and len(m.group(1)) <= 18 and ('.' in m.group(1) or (int(m.group(1)) <= 15 and re.match(r'[A-ZÀ-Ú“"(]', tt[m.end():]))):
                if pre:
                    t = f'**{m.group(1)}** ~~' + tt[m.end():] if False else f'~~**{m.group(1)}** ' + tt[m.end():]
                else:
                    t = f'**{m.group(1)}** ' + tt[m.end():]
        out.append(t)
    md = f'<!-- convertido de {os.path.basename(pdf)} pelo converter.py (SSEG) -->\n\n' + '\n\n'.join(out) + '\n'
    open(outmd, 'w', encoding='utf-8', newline='\n').write(md)
    stats['kb_pdf'] = os.path.getsize(pdf) // 1024; stats['kb_md'] = len(md.encode()) // 1024
    return {k:v for k,v in stats.items() if not k.startswith('_')}

if __name__ == '__main__':
    outdir = sys.argv[1]; os.makedirs(os.path.join(outdir, 'img'), exist_ok=True)
    for f in sys.argv[2:]:
        name = re.sub(r'[^\w.-]+', '_', os.path.splitext(os.path.basename(f))[0]).strip('_')
        st = convert(f, os.path.join(outdir, name + '.md'), os.path.join(outdir, 'img'), 'img')
        print(json.dumps({'arq': name, **st}, ensure_ascii=False), flush=True)
