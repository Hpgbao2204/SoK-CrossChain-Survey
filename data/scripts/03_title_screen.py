"""Step 3a: apply title-stage screening decisions.

Decision files in data/screening/:
  title_excl_<k>.txt  lines 'CODE rid rid ...' listing exclusions for batch k (A, N, O, R codes)
  title_keep_3.txt    line 'K rid ...' listing records kept in batch 3; the rest of batch 3 is code X
Codes: A application system using cross-chain only as infrastructure; N cross-chain without a security
contribution; O off-topic; X batch-3 exclusion (A/N/O not separated); R non-English, thesis or non-research.
Output: data/screening/title_decisions.csv and data/to_abstract.csv
"""
import csv
from pathlib import Path

D = Path(__file__).resolve().parents[1]
S = D / 'screening'
BATCH = 376

rows = list(csv.DictReader(open(D / 'to_screen.csv', encoding='utf-8')))
batch_of = {r['rid']: i // BATCH for i, r in enumerate(rows)}


def parse(p):
    out = {}
    for line in open(p, encoding='utf-8'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        code, *ids = line.split()
        for i in ids:
            out['R' + i] = code
    return out


dec = {}
for k in range(3):
    dec.update(parse(S / f'title_excl_{k}.txt'))
keep3 = parse(S / 'title_keep_3.txt')
for r in rows:
    rid = r['rid']
    if batch_of[rid] == 3:
        dec[rid] = 'keep' if keep3.get(rid) == 'K' else keep3.get(rid, 'X')
    else:
        dec.setdefault(rid, 'keep')

unknown = set(dec) - set(batch_of)
assert not unknown, unknown
with open(S / 'title_decisions.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['rid', 'title_decision'])
    for r in rows:
        w.writerow([r['rid'], dec[r['rid']]])
keep = [r for r in rows if dec[r['rid']] == 'keep']
with open(D / 'to_abstract.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(keep)
from collections import Counter
print(Counter(dec.values()), 'kept', len(keep))
