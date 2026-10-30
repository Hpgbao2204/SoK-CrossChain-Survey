"""Step 4: merge abstract-stage decisions and codes, add records from other methods,
and compute every number used in the paper.

Inputs : data/to_abstract.csv, data/screening/abs_code_*.txt, data/screening/other_methods.csv
Outputs: data/included_studies.csv   one row per included study with its codes
         data/screening/abstract_decisions.csv
         data/prisma_counts.json     numbers for the PRISMA diagram
         data/corpus_stats.json      counts used in the text, tables and figures

Code line format: rid dec type stage props classes tech eval
  dec   I include; EA application only; EN no security contribution; EO off-topic
        ED duplicate or superseded version; EQ non-refereed outlet without evaluation, or a
        preprint survey/position paper; EI insufficient information (no abstract, unclear title)
  type  S survey/SoK, M attack or measurement study, D defense
  stage S1 specify (design time), S2 assure (pre-deployment), S3 operate and respond (runtime)
  props digits 1-7 for P1-P7, '-' if none named; classes digits 1-7 for T1-T7, '-' if none named
  tech  comma-separated technique families; eval F formal, E experiment/prototype, R real
        incident or real-chain data, N none reported in the abstract
"""
import csv, glob, json, re
from collections import Counter, defaultdict
from pathlib import Path

D = Path(__file__).resolve().parents[1]
S = D / 'screening'

recs = {r['rid']: r for r in csv.DictReader(open(D / 'to_abstract.csv', encoding='utf-8'))}
codes = {}
for p in sorted(glob.glob(str(S / 'abs_code_*.txt'))):
    for line in open(p, encoding='utf-8'):
        if not line.strip() or line.startswith('#'):
            continue
        f = line.split()
        codes['R' + f[0]] = f  # later files (corrections) override earlier ones
missing = set(recs) - set(codes)
assert not missing, f'uncoded: {sorted(missing)[:10]}'

SCREEN_EXCL = {'EA', 'EN', 'EO'}      # decided on title and abstract
ELIG_EXCL = {'ED', 'EQ', 'EI'}        # decided on bibliographic record and evidence

rows, dec_rows = [], []
for rid, r in recs.items():
    f = codes[rid]
    dec = f[1]
    dec_rows.append({'rid': rid, 'decision': dec, 'title': r['title']})
    if dec != 'I':
        continue
    typ, stage, props, classes, tech, ev = f[2:8]
    rows.append({'id': rid, 'source': 'database', 'title': r['title'], 'year': r['year'], 'venue': r['venue'],
                 'doi': r['doi'], 'arxiv': r['arxiv'], 'cites': r['cites'], 'type': typ, 'stage': stage,
                 'props': props, 'classes': classes, 'tech': tech, 'eval': ev,
                 'peer_reviewed': 'no' if re.search(r'arxiv|eprint|research square|ssrn|zenodo|figshare', r['venue'], re.I)
                 or r['venue'] == '' else 'yes'})
for o in csv.DictReader(open(S / 'other_methods.csv', encoding='utf-8')):
    rows.append({'id': o['oid'], 'source': 'other', 'title': o['title'], 'year': o['year'], 'venue': o['venue'],
                 'doi': o['doi'], 'arxiv': o['arxiv'], 'cites': '', 'type': o['type'], 'stage': o['stage'],
                 'props': o['props'], 'classes': o['classes'], 'tech': o['tech'], 'eval': o['eval'],
                 'peer_reviewed': 'no' if o['venue'] == 'arXiv' else 'yes'})

with open(D / 'included_studies.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(sorted(rows, key=lambda x: (x['type'], x['stage'], x['year'], x['id'])))
with open(S / 'abstract_decisions.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=['rid', 'decision', 'title'])
    w.writeheader()
    w.writerows(dec_rows)

# ---------- PRISMA numbers ----------
s1 = json.loads((D / 'prisma_counts_stage1.json').read_text(encoding='utf-8'))
title_dec = Counter(r['title_decision'] for r in csv.DictReader(open(S / 'title_decisions.csv', encoding='utf-8')))
abs_dec = Counter(codes[k][1] for k in recs)
screened = s1['rules']['screen']
excl_screen = sum(v for k, v in title_dec.items() if k != 'keep') + sum(abs_dec[k] for k in SCREEN_EXCL)
assessed = screened - excl_screen
prisma = {
    'identified': s1['identified'], 'by_source': s1['by_source'],
    'duplicates': s1['duplicates_removed'], 'rule_R1': s1['rules'].get('R1', 0), 'rule_R2': s1['rules'].get('R2', 0),
    'screened': screened, 'excluded_screening': excl_screen,
    'excluded_screening_title': sum(v for k, v in title_dec.items() if k != 'keep'),
    'excluded_screening_abstract': {k: abs_dec[k] for k in sorted(SCREEN_EXCL)},
    'assessed': assessed, 'excluded_eligibility': {k: abs_dec[k] for k in sorted(ELIG_EXCL)},
    'included_db': abs_dec['I'], 'other_identified': sum(1 for r in rows if r['source'] == 'other'),
    'other_excluded': 0, 'included_total': len(rows),
}
assert prisma['assessed'] - sum(prisma['excluded_eligibility'].values()) == prisma['included_db']
(D / 'prisma_counts.json').write_text(json.dumps(prisma, indent=2), encoding='utf-8')

# ---------- corpus statistics ----------
def digits(s):
    return [c for c in s if c.isdigit()]

st = {}
st['n'] = len(rows)
st['by_type'] = Counter(r['type'] for r in rows)
st['by_stage'] = Counter(r['stage'] for r in rows if r['type'] == 'D')
st['by_year'] = Counter(r['year'] for r in rows)
st['by_year_stage'] = defaultdict(Counter)
for r in rows:
    key = r['stage'] if r['type'] == 'D' else ('Survey' if r['type'] == 'S' else 'Attack/measurement')
    st['by_year_stage'][r['year']][key] += 1
st['peer_reviewed'] = Counter(r['peer_reviewed'] for r in rows)
st['since_2024'] = sum(1 for r in rows if int(r['year']) >= 2024)
# property x stage, class x stage for defenses (and attack/measurement studies as a row)
groups = {'M': [r for r in rows if r['type'] == 'M']}
for sname in ('S1', 'S2', 'S3'):
    groups[sname] = [r for r in rows if r['type'] == 'D' and r['stage'] == sname]
st['prop_by_group'] = {g: Counter(p for r in rs for p in digits(r['props'])) for g, rs in groups.items()}
st['class_by_group'] = {g: Counter(c for r in rs for c in digits(r['classes'])) for g, rs in groups.items()}
st['no_class_by_group'] = {g: sum(1 for r in rs if not digits(r['classes'])) for g, rs in groups.items()}
st['no_prop_by_group'] = {g: sum(1 for r in rs if not digits(r['props'])) for g, rs in groups.items()}
st['size_by_group'] = {g: len(rs) for g, rs in groups.items()}
st['tech_by_stage'] = {sname: Counter(t for r in groups[sname] for t in r['tech'].split(',')) for sname in ('S1', 'S2', 'S3')}
st['eval_by_stage'] = {sname: Counter(r['eval'] for r in groups[sname]) for sname in ('S1', 'S2', 'S3')}
st['real_eval_by_stage'] = {sname: sum('R' in r['eval'] for r in groups[sname]) for sname in ('S1', 'S2', 'S3')}
st['s3_response'] = sum('RESP' in r['tech'] for r in groups['S3'])
st['s3_trace'] = sum('TRACE' in r['tech'] for r in groups['S3'])
st['s3_detect'] = sum(any(t in r['tech'] for t in ('RULE', 'ACC', 'GML', 'LLM')) for r in groups['S3'])
st['s3_trust'] = sum('TRUST' in r['tech'] for r in groups['S3'])
st['s1_auth'] = sum('AUTH' in r['tech'] for r in groups['S1'])
st['s1_auth_priv'] = sum('AUTH' in r['tech'] and '7' in r['props'] for r in groups['S1'])
st['s1_priv'] = sum('7' in digits(r['props']) for r in groups['S1'])
st['s1_verif'] = sum(any(t in r['tech'] for t in ('LC', 'ZK', 'OPT')) for r in groups['S1'])
st['s1_formal'] = sum('F' in r['eval'] for r in groups['S1'])
st['s1_t3'] = sum('3' in digits(r['classes']) for r in groups['S1'])
st['s2_ml'] = sum(any(t in r['tech'] for t in ('ML', 'LLM')) for r in groups['S2'])
st['t4_any_stage'] = {g: st['class_by_group'][g].get('4', 0) for g in groups}
(D / 'corpus_stats.json').write_text(json.dumps(st, indent=2, default=dict), encoding='utf-8')
print(json.dumps(prisma, indent=2))
print(json.dumps({k: st[k] for k in ('n', 'by_type', 'by_stage', 'peer_reviewed', 'since_2024', 'size_by_group',
                                     'no_class_by_group', 's3_response', 's3_trace', 's3_detect', 's3_trust',
                                     's1_auth', 's1_auth_priv', 's1_priv', 's1_verif', 's1_formal', 's1_t3', 's2_ml',
                                     'real_eval_by_stage', 't4_any_stage')}, indent=1, default=dict))
print('prop', json.dumps(st['prop_by_group'], default=dict))
print('class', json.dumps(st['class_by_group'], default=dict))
print('tech', json.dumps(st['tech_by_stage'], default=dict))
