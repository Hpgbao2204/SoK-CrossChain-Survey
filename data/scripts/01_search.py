"""Step 1 of the review: query OpenAlex, Semantic Scholar and arXiv with one Boolean string.

Raw responses go to data/raw/<source>.jsonl, one record per line, together with the
query and the date of the search in data/raw/search_log.json.
Run from the SoK folder:  python data/scripts/01_search.py [openalex|s2|arxiv ...]
"""
import json, sys, time, datetime, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / 'raw'
RAW.mkdir(parents=True, exist_ok=True)
YEARS = (2019, 2026)

XCHAIN = ['cross-chain', 'crosschain', 'cross-blockchain', 'inter-blockchain', 'blockchain bridge',
          'token bridge', 'bridge protocol', 'blockchain interoperability', 'interoperability protocol',
          'atomic swap', 'cross-ledger', 'sidechain']
SEC = ['attack', 'exploit', 'vulnerability', 'security', 'secure', 'anomaly', 'hack', 'privacy',
       'audit', 'fraud', 'formal verification', 'trust']
CTX = ['blockchain', 'distributed ledger', 'DeFi', 'smart contract']


def q(t):
    return f'"{t}"' if (' ' in t or '-' in t) else t


def boolean():
    grp = lambda xs: '(' + ' OR '.join(q(x) for x in xs) + ')'
    return f'{grp(CTX)} AND {grp(XCHAIN)} AND {grp(SEC)}'


def get(url, tries=8, accept='application/json'):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'sok-review-script/1.0', 'Accept': accept})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # rate limits and transient errors
            wait = 5 * (i + 1)
            print(f'  retry {i + 1} after {wait}s: {e}', flush=True)
            time.sleep(wait)
    raise RuntimeError('giving up on ' + url)


def openalex():
    flt = f'title_and_abstract.search:{boolean()},publication_year:{YEARS[0]}-{YEARS[1]}'
    cursor, n = '*', 0
    with open(RAW / 'openalex.jsonl', 'w', encoding='utf-8') as f:
        while cursor:
            url = ('https://api.openalex.org/works?per-page=200&cursor=' + urllib.parse.quote(cursor)
                   + '&filter=' + urllib.parse.quote(flt))
            d = json.loads(get(url))
            for w in d['results']:
                f.write(json.dumps(w, ensure_ascii=False) + '\n')
                n += 1
            cursor = d['meta'].get('next_cursor')
            print(f'openalex {n}/{d["meta"]["count"]}', flush=True)
            time.sleep(1.2)
    return n


def s2():
    # S2 bulk syntax: | = OR, + = AND, "..." = phrase
    grp = lambda xs: '(' + ' | '.join(f'"{x}"' if (' ' in x or '-' in x) else x for x in xs) + ')'
    query = f'{grp(CTX)} + {grp(XCHAIN)} + {grp(SEC)}'
    fields = 'title,abstract,year,venue,publicationVenue,externalIds,citationCount,publicationTypes,authors,url'
    token, n = None, 0
    with open(RAW / 's2.jsonl', 'w', encoding='utf-8') as f:
        while True:
            url = ('https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=' + urllib.parse.quote(query)
                   + f'&year={YEARS[0]}-{YEARS[1]}&fields={fields}' + (f'&token={token}' if token else ''))
            d = json.loads(get(url))
            for w in d.get('data', []):
                f.write(json.dumps(w, ensure_ascii=False) + '\n')
                n += 1
            print(f's2 {n}/{d.get("total")}', flush=True)
            token = d.get('token')
            if not token:
                break
            time.sleep(3)
    return n, query


def arxiv():
    grp = lambda xs: '(' + ' OR '.join(f'all:"{x}"' if (' ' in x or '-' in x) else f'all:{x}' for x in xs) + ')'
    query = f'{grp(XCHAIN)} AND {grp(SEC)}'
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    start, n = 0, 0
    with open(RAW / 'arxiv.jsonl', 'w', encoding='utf-8') as f:
        while True:
            url = ('http://export.arxiv.org/api/query?search_query=' + urllib.parse.quote(query)
                   + f'&start={start}&max_results=200&sortBy=submittedDate&sortOrder=descending')
            root = ET.fromstring(get(url, accept='application/atom+xml'))
            entries = root.findall('a:entry', ns)
            if not entries:
                break
            stop = False
            for e in entries:
                pub = e.findtext('a:published', '', ns)
                yr = int(pub[:4]) if pub else 0
                if yr < YEARS[0]:
                    stop = True
                    continue
                rec = {'id': e.findtext('a:id', '', ns), 'title': ' '.join(e.findtext('a:title', '', ns).split()),
                       'abstract': ' '.join(e.findtext('a:summary', '', ns).split()), 'published': pub, 'year': yr,
                       'authors': [a.findtext('a:name', '', ns) for a in e.findall('a:author', ns)],
                       'doi': e.findtext('{http://arxiv.org/schemas/atom}doi', '', ns),
                       'journal_ref': e.findtext('{http://arxiv.org/schemas/atom}journal_ref', '', ns)}
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')
                n += 1
            print(f'arxiv {n}', flush=True)
            if stop or len(entries) < 200:
                break
            start += 200
            time.sleep(3.5)
    return n, query


if __name__ == '__main__':
    which = sys.argv[1:] or ['openalex', 's2', 'arxiv']
    logp = RAW / 'search_log.json'
    log = json.loads(logp.read_text(encoding='utf-8')) if logp.exists() else {}
    log['boolean'] = boolean()
    for w in which:
        today = datetime.date.today().isoformat()
        if w == 'openalex':
            log['openalex'] = {'date': today, 'n': openalex(), 'field': 'title_and_abstract'}
        elif w == 's2':
            n, qq = s2()
            log['s2'] = {'date': today, 'n': n, 'query': qq, 'field': 'title_and_abstract (bulk)'}
        elif w == 'arxiv':
            n, qq = arxiv()
            log['arxiv'] = {'date': today, 'n': n, 'query': qq, 'field': 'all'}
        logp.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(log, indent=2, ensure_ascii=False))
