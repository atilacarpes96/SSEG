"""Confere o banco de notificações contra o texto das normas, com modelo LOCAL.

Roda só no PC de casa (precisa do Ollama com o qwen3.5:9b). Nada sai do PC.

Divisão do trabalho, de propósito:
  - o script faz a parte mecânica: separa cada notificação, acha a norma e os
    itens citados, e recorta o texto exato desses itens de normas/md/;
  - o modelo só julga um par pequeno por vez (notificação × texto do item).
Assim o modelo nunca lê o banco inteiro nem a norma inteira: em 04/10/2026 o
agente do DSHARNESS tentou ler os dois de uma vez, estourou o contexto e
esqueceu a tarefa.

O resultado é TRIAGEM, não fundamento: normas/md/ é extração automática do PDF
(serve para localizar trecho). Antes de mudar o banco, conferir no PDF oficial.

Uso:
  python conferir_banco_local.py                       # banco inteiro
  python conferir_banco_local.py --secao Extintores    # uma seção
  python conferir_banco_local.py --saida relatorio.md --modelo qwen3.5:9b
  python conferir_banco_local.py --rapido               # sem raciocínio (só para teste)
"""
import argparse, json, re, sys, time, unicodedata, urllib.request
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
NORMAS = AQUI.parent / 'normas'
BANCO = NORMAS / 'banco-notificacoes-padrao.md'
MD = NORMAS / 'md'
OLLAMA = 'http://127.0.0.1:11434/api/chat'

# Número da RT (e parte) -> (arquivo em normas/md, ano da versão que está lá).
# O ano serve para avisar quando a notificação cita outra versão.
ARQUIVOS = {
    '1': ('RT CBMRS 01 – Diretrizes Básicas de Segurança Contra Incêndio.md', '2024'),
    '2': ('RT CBMRS 02 – Termos e Definições.md', '2014'),
    '4': ('RT CBMRS 04 – Isolamento de Riscos.md', '2022'),
    '5p7': ('RT 05 Parte 07.md', '2025'),
    '5p1': ('RTCBMRS 5 parte 1 - 1 2016 - ppci na forma completa.md', '2016'),
    '10': ('RT10.md', '2024'),
    '11': ('RT11.md', '2016'),
    '12': ('RT12.md', '2021'),
    '14': ('RT14.md', '2016'),
    '17': ('RT17.md', '2025'),
    '18': ('RT18.md', '2025'),
    '31': ('RT31.md', '2025'),
    'isol': ('RTISOL.md', '2022'),
    'dec': ('DECRETO51803.md', '2014'),
}

RE_ITEM_LINHA = re.compile(r'^\*\*(\d+(?:\.\d+)+)\*\*')
RE_NUM = re.compile(r'\b\d{1,2}(?:\.\d{1,2}){1,6}\b')
RE_APOS_ITEM = re.compile(r'\b(?:itens?|subitens?)\s+((?:\d{1,2}(?:\.\d{1,2})+(?:\s*(?:,|e|a)\s*)?)+)', re.I)
RE_LONGO = re.compile(r'\b\d{1,2}(?:\.\d{1,2}){2,6}\b')
MAX_TRECHO = 3000


def norm_txt(s):
    return unicodedata.normalize('NFKC', s)


def ler_banco(secao_filtro=None):
    """[(secao, texto da notificação)], pulando o cabeçalho e o histórico."""
    itens, secao = [], None
    for linha in BANCO.read_text(encoding='utf-8').splitlines():
        if linha.startswith('## '):
            secao = linha[3:].strip()
            continue
        if linha.startswith('### '):
            continue
        if not secao or secao.startswith('⚠️ Regra') or secao.startswith('Histórico'):
            continue
        if secao_filtro and secao_filtro.lower() not in secao.lower():
            continue
        if linha.startswith('- '):
            itens.append([secao, linha[2:].strip()])
        elif itens and itens[-1][0] == secao and linha.startswith('  >'):
            # Ressalva já anotada embaixo da notificação: vai junto, para o
            # relatório mostrar que aquilo já foi visto.
            itens[-1].append(linha.strip(' >'))
    return [(i[0], i[1], ' '.join(i[2:])) for i in itens]


def normas_citadas(txt):
    """Chaves de ARQUIVOS citadas no texto, com o ano escrito na citação."""
    achadas = []
    t = norm_txt(txt)
    for m in re.finditer(r'RT\s*(?:CBMRS)?\s*(?:n\.?\s*[º°o]\.?\s*)?0?(\d{1,2})'
                         r'(?:\s*,?\s*parte\s*0?(\d+)(?:\.(\d))?)?'
                         r'(?:\s*(?:de|/)\s*(?:\d{1,2}/\d{1,2}/)?((?:19|20)\d{2}))?', t, re.I):
        num, parte, sub, ano = m.groups()
        chave = num
        if num == '5':
            chave = '5p7' if parte == '7' else '5p1'
        achadas.append((chave, ano))
    if re.search(r'Implanta[çc][ãa]o do SOL', t, re.I):
        achadas.append(('isol', None))
    if re.search(r'Decreto\s*(?:n[º°]\s*)?51\.?803', t, re.I):
        achadas.append(('dec', None))
    vistas, saida = set(), []
    for c, a in achadas:
        if c in ARQUIVOS and c not in vistas:
            vistas.add(c)
            saida.append((c, a))
    return saida


def itens_citados(txt):
    nums = []
    for m in RE_APOS_ITEM.finditer(txt):
        nums += RE_NUM.findall(m.group(1))
    nums += RE_LONGO.findall(txt)
    vistos, saida = set(), []
    for n in nums:
        if n not in vistos:
            vistos.add(n)
            saida.append(n)
    return saida


_cache = {}


def indice(chave):
    """{item: trecho} de um arquivo de normas/md."""
    if chave in _cache:
        return _cache[chave]
    linhas = (MD / ARQUIVOS[chave][0]).read_text(encoding='utf-8').splitlines()
    pos = [(i, RE_ITEM_LINHA.match(l).group(1)) for i, l in enumerate(linhas) if RE_ITEM_LINHA.match(l)]
    idx = {}
    for k, (i, num) in enumerate(pos):
        fim = len(linhas)
        for j, outro in pos[k + 1:]:
            # O trecho do item inclui os subitens dele (5.4.1 leva 5.4.1.x) e
            # para no primeiro item que não é filho.
            if not outro.startswith(num + '.'):
                fim = j
                break
        trecho = '\n'.join(l for l in linhas[i:fim] if l.strip())
        trecho = re.sub(r'<!--.*?-->|<br>', ' ', trecho)
        idx.setdefault(num, trecho[:MAX_TRECHO])
    _cache[chave] = idx
    return idx


def montar_par(txt):
    """Texto dos itens citados, com a origem; e avisos mecânicos."""
    normas = normas_citadas(txt)
    itens = itens_citados(txt)
    avisos, trechos = [], []
    if not normas:
        avisos.append('norma citada sem texto local (outro estado, ABNT ou não reconhecida)')
    for chave, ano in normas:
        arq, ano_local = ARQUIVOS[chave]
        if ano and ano != ano_local:
            avisos.append(f'cita versão {ano}; o texto local é de {ano_local}')
        idx = indice(chave)
        for n in itens:
            if n in idx:
                trechos.append(f'[{arq} — item {n}]\n{idx[n]}')
    achados = {t.split(' — item ')[1].split(']')[0] for t in trechos}
    faltando = [n for n in itens if n not in achados]
    if normas and faltando:
        avisos.append('item não achado no texto local: ' + ', '.join(faltando))
    if normas and not itens:
        avisos.append('não cita item numerado (tabela, anexo ou norma inteira)')
    return trechos, avisos


PROMPT = """Você confere notificações de análise de PPCI (Corpo de Bombeiros do RS) contra o texto oficial da norma.
Use SOMENTE o texto da norma abaixo. Não use conhecimento próprio.

NOTIFICAÇÃO:
{notif}

TEXTO DA NORMA (itens citados pela notificação):
{trechos}

Julgue se a notificação descreve corretamente o que esses itens dizem:
- "certo": o item diz o que a notificação afirma.
- "parcial": o item trata do assunto, mas a notificação omite uma condição ou exceção, generaliza, troca uma palavra que muda o sentido (por exemplo "inferior a" no lugar de "não mais de"), ou só parte confere.
- "errado": o item citado não trata do que a notificação afirma.
Responda em JSON: {{"veredito": "certo|parcial|errado", "motivo": "uma ou duas frases citando a diferença exata, ou dizendo que confere"}}"""

ESQUEMA = {
    'type': 'object',
    'properties': {
        'veredito': {'type': 'string', 'enum': ['certo', 'parcial', 'errado']},
        'motivo': {'type': 'string'},
    },
    'required': ['veredito', 'motivo'],
}


def julgar(modelo, notif, trechos, pensar):
    corpo = {
        'model': modelo,
        'messages': [{'role': 'user', 'content': PROMPT.format(notif=notif, trechos='\n\n'.join(trechos))}],
        'stream': False,
        'think': pensar,
        'format': ESQUEMA,
        'keep_alive': '10m',
        'options': {'temperature': 0, 'num_ctx': 16384},
    }
    req = urllib.request.Request(OLLAMA, json.dumps(corpo).encode(), {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.load(r)
    try:
        return json.loads(d['message']['content'])
    except (KeyError, json.JSONDecodeError):
        return {'veredito': 'erro', 'motivo': 'resposta do modelo não era JSON: ' + str(d.get('message', ''))[:200]}


def cel(s):
    return s.replace('|', '/').replace('\n', ' ').strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--secao', help='só as seções cujo título contém este texto')
    ap.add_argument('--modelo', default='qwen3.5:9b')
    # Sem raciocínio o 9B deu "certo" para tudo na seção Extintores (8 s);
    # com raciocínio pegou as duas citações parciais do gabarito (~45 s cada).
    ap.add_argument('--rapido', action='store_true', help='desliga o raciocínio: rápido, mas aprova demais')
    ap.add_argument('--saida', default=f'conferencia-banco-{datetime.now():%Y-%m-%d}.md')
    a = ap.parse_args()

    itens = ler_banco(a.secao)
    if not itens:
        sys.exit('Nenhuma notificação encontrada (confira --secao).')
    print(f'{len(itens)} notificações; modelo {a.modelo}')

    linhas_rel, contagem, t0 = [], {}, time.time()
    secao_atual = None
    for n, (secao, notif, ressalva) in enumerate(itens, 1):
        trechos, avisos = montar_par(notif)
        if trechos:
            r = julgar(a.modelo, notif, trechos, not a.rapido)
        else:
            r = {'veredito': 'sem texto', 'motivo': 'nada para comparar no texto local'}
        v = r.get('veredito', 'erro')
        contagem[v] = contagem.get(v, 0) + 1
        if ressalva:
            avisos.append('já tem ressalva anotada no banco')
        if secao != secao_atual:
            secao_atual = secao
            linhas_rel += ['', f'## {secao}', '', '| # | Notificação | Veredito | Motivo | Avisos |', '|---|---|---|---|---|']
        resumo = notif if len(notif) <= 160 else notif[:157] + '…'
        linhas_rel.append(f'| {n} | {cel(resumo)} | **{v}** | {cel(r.get("motivo", ""))} | {cel("; ".join(avisos))} |')
        print(f'  [{n}/{len(itens)}] {v:9} {secao[:30]} ({time.time() - t0:.0f}s)')

    cab = [
        f'# Conferência do banco de notificações — {datetime.now():%d/%m/%Y %H:%M}',
        '',
        f'Modelo local `{a.modelo}`, uma notificação por vez contra o texto dos itens citados em `normas/md/`.',
        '**Triagem, não fundamento:** `normas/md/` é extração automática do PDF. Antes de mudar o banco, conferir no PDF oficial.',
        '',
        'Resumo: ' + ', '.join(f'{k} {v}' for k, v in sorted(contagem.items())) + f' — {time.time() - t0:.0f} s no total.',
    ]
    Path(a.saida).write_text('\n'.join(cab + linhas_rel) + '\n', encoding='utf-8')
    print(f'Relatório: {Path(a.saida).resolve()}')


if __name__ == '__main__':
    main()
