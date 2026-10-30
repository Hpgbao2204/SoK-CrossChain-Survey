"""Step 2: normalize the three raw exports, remove duplicates and apply automated rules.

Outputs (data/):
  records_all.csv       every normalized record with its source
  records_dedup.csv     one row per unique work, with the rule decision (R1-R4 or 'screen')
  to_screen.csv         records that pass the rules and go to title/abstract screening
"""
import csv, json, re
from pathlib import Path

D = Path(__file__).resolve().parents[1]
RAW = D / 'raw'
YEARS = (2019, 2026)

XTERMS = ['cross-chain', 'crosschain', 'cross chain', 'cross-blockchain', 'inter-blockchain', 'interblockchain',
          'blockchain bridge', 'token bridge', 'bridge', 'interoperab', 'atomic swap', 'atomic cross',
          'cross-ledger', 'sidechain', 'side-chain', 'side chain', 'relay chain', 'relaychain', 'htlc',
          'hash time lock', 'hashed time', 'inter-chain', 'interchain', 'multi-chain', 'multichain', ' ibc ',
          'layerzero', 'wormhole', 'polkadot', 'cosmos']
SECTERMS = ['attack', 'exploit', 'vulnerab', 'secur', 'anomal', 'hack', 'privacy', 'private', 'audit', 'fraud',
            'verif', 'trust', 'threat', 'adversar', 'malicious', 'byzantine', 'theft', 'stolen', 'detect',
            'monitor', 'safety', 'safe', 'attest', 'proof', 'confidential', 'anonym', 'launder', 'mev', 'defect',
            'authenticat', 'integrity', 'robust', 'resilien', 'fault', 'risk', 'bug', 'incident', 'forensic',
            'censor', 'double spend', 'double-spend', 'griefing', 'replay', 'collusion', 'reputation']
NONRESEARCH_OA = {'paratext', 'editorial', 'erratum', 'letter', 'retraction', 'peer-review', 'book', 'other',
                  'supplementary-materials', 'libguides', 'grant', 'standard', 'report', 'dissertation'}
NONRESEARCH_S2 = {'Editorial', 'News', 'LettersAndComments'}


def unify(s):
    # unicode hyphens and dashes to ASCII so that 'cross‐chain' matches 'cross-chain'
    return re.sub('[‐‑‒–—−]', '-', (s or '').lower())


def norm_title(t):
    return re.sub(r'[^a-z0-9]', '', (t or '').lower())


def oa_abstract(inv):
    if not inv:
        return ''
    pos = [(p, w) for w, ps in inv.items() for p in ps]
    return ' '.join(w for _, w in sorted(pos))


def load():
    recs = []
    for line in open(RAW / 'openalex.jsonl', encoding='utf-8'):
        w = json.loads(line)
        loc = w.get('primary_location') or {}
        src = (loc.get('source') or {})
        ids = w.get('ids') or {}
        doi = (w.get('doi') or '').replace('https://doi.org/', '').lower()
        arx = ''
        for l in w.get('locations') or []:
            u = (l.get('landing_page_url') or '')
            m = re.search(r'arxiv\.org/abs/(\d{4}\.\d{4,5})', u)
            if m:
                arx = m.group(1)
        if doi.startswith('10.48550/arxiv.'):
            arx = doi.split('arxiv.')[1]
        recs.append(dict(src='openalex', sid=w['id'].split('/')[-1], title=w.get('title') or '',
                         abstract=oa_abstract(w.get('abstract_inverted_index')), year=w.get('publication_year'),
                         venue=src.get('display_name') or '', venue_type=src.get('type') or '', doi=doi, arxiv=arx,
                         type=w.get('type') or '', cites=w.get('cited_by_count') or 0,
                         authors='; '.join((a.get('author') or {}).get('display_name') or '' for a in w.get('authorships') or [])))
    for line in open(RAW / 's2.jsonl', encoding='utf-8'):
        w = json.loads(line)
        ex = w.get('externalIds') or {}
        pv = w.get('publicationVenue') or {}
        recs.append(dict(src='s2', sid=w.get('paperId'), title=w.get('title') or '', abstract=w.get('abstract') or '',
                         year=w.get('year'), venue=w.get('venue') or pv.get('name') or '', venue_type=pv.get('type') or '',
                         doi=(ex.get('DOI') or '').lower(), arxiv=ex.get('ArXiv') or '',
                         type=','.join(w.get('publicationTypes') or []), cites=w.get('citationCount') or 0,
                         authors='; '.join(a.get('name') or '' for a in w.get('authors') or [])))
    for line in open(RAW / 'arxiv.jsonl', encoding='utf-8'):
        w = json.loads(line)
        aid = re.sub(r'v\d+$', '', w['id'].split('/abs/')[-1])
        recs.append(dict(src='arxiv', sid=aid, title=w['title'], abstract=w['abstract'], year=w['year'],
                         venue='arXiv' + (f' ({w["journal_ref"]})' if w.get('journal_ref') else ''), venue_type='repository',
                         doi=(w.get('doi') or '').lower(), arxiv=aid, type='preprint', cites=0,
                         authors='; '.join(w['authors'])))
    return recs


def dedup(recs):
    groups, key2g = [], {}
    for r in recs:
        keys = [k for k in (('doi', r['doi']) if r['doi'] else None, ('arx', r['arxiv']) if r['arxiv'] else None,
                            ('t', norm_title(r['title'])) if len(norm_title(r['title'])) > 15 else None) if k]
        g = next((key2g[k] for k in keys if k in key2g), None)
        if g is None:
            g = len(groups)
            groups.append([])
        groups[g].append(r)
        for k in keys:
            key2g.setdefault(k, g)
    out = []
    for i, g in enumerate(groups):
        # prefer a peer-reviewed record (journal/conference) over a repository copy
        def rank(r):
            return (r['venue_type'] in ('journal', 'conference') or ('JournalArticle' in r['type'] or 'Conference' in r['type']),
                    bool(r['abstract']), r['src'] == 'openalex')
        best = dict(max(g, key=rank))
        best['abstract'] = max((r['abstract'] for r in g), key=len)
        best['doi'] = next((r['doi'] for r in g if r['doi'] and not r['doi'].startswith('10.48550')), best['doi'])
        best['arxiv'] = next((r['arxiv'] for r in g if r['arxiv']), '')
        best['cites'] = max(int(r['cites'] or 0) for r in g)
        best['sources'] = '+'.join(sorted({r['src'] for r in g}))
        best['n_copies'] = len(g)
        best['rid'] = f'R{i + 1:04d}'
        out.append(best)
    return out


def rule(r):
    types = set(r['type'].split(','))
    if r['src'] == 'openalex' and r['type'] in NONRESEARCH_OA or types & NONRESEARCH_S2:
        return 'R1'
    if not r['title'] or not r['year'] or not (YEARS[0] <= int(r['year']) <= YEARS[1]):
        return 'R1'
    t = ' ' + unify(r['title']) + ' '
    a = ' ' + unify(r['abstract']) + ' '
    xt = sum(t.count(k) for k in XTERMS)
    xa = sum(a.count(k) for k in XTERMS)
    if xt == 0 and xa < 2:
        return 'R2'
    # R3 (no security term) was tested and dropped: it removed relevant tracing and atomicity papers,
    # so these records go to manual screening instead.
    return 'screen'


if __name__ == '__main__':
    recs = load()
    cols = ['rid', 'sources', 'n_copies', 'title', 'year', 'venue', 'venue_type', 'type', 'doi', 'arxiv', 'cites',
            'authors', 'abstract', 'rule']
    with open(D / 'records_all.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['src', 'sid', 'title', 'year', 'venue', 'doi', 'arxiv', 'type'], extrasaction='ignore')
        w.writeheader()
        w.writerows(recs)
    out = dedup(recs)
    for r in out:
        r['rule'] = rule(r)
    with open(D / 'records_dedup.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(out)
    keep = [r for r in out if r['rule'] == 'screen']
    with open(D / 'to_screen.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(keep)
    from collections import Counter
    c = Counter(r['rule'] for r in out)
    summary = {'identified': len(recs), 'by_source': dict(Counter(r['src'] for r in recs)),
               'duplicates_removed': len(recs) - len(out), 'unique': len(out), 'rules': dict(c)}
    (D / 'prisma_counts_stage1.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
