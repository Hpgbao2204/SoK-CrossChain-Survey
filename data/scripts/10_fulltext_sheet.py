"""Step 10 (optional): sheet for full-text validation of the studies behind the absence claims.

Covers every S2 and S3 study and every study with a candidate cross-stage hand-off. A reader opens
the full text (link column) and answers the yes/no questions; `score` then reports which abstract
codes changed, so the absence statements in Sections 6-7 can be confirmed or corrected.

Usage (from the SoK folder):
  python data/scripts/10_fulltext_sheet.py make    -> data/validation/fulltext_sheet.csv
  python data/scripts/10_fulltext_sheet.py score   -> data/validation/fulltext_results.json
"""
import csv, json, sys
from pathlib import Path

D = Path(__file__).resolve().parents[1]
V = D / 'validation'
V.mkdir(exist_ok=True)
QUESTIONS = [
    ('t4', 'addresses forged or censored observations (T4)? y/n'),
    ('t2', 'addresses verification flaws (T2)? y/n'),
    ('response', 'decides or executes a response (pause, limit, escalate)? y/n'),
    ('h1', 'checks code or runtime against a design-time specification or trust assumptions? y/n'),
    ('h2', 'passes audit findings or invariants to runtime monitoring? y/n'),
    ('h3', 'turns incidents into regression tests or revised properties? y/n'),
    ('props', 'properties addressed in the full text (digits 1-7)'),
    ('classes', 'attack classes addressed in the full text (digits 1-7)'),
]


def make():
    inc = list(csv.DictReader(open(D / 'included_studies.csv', encoding='utf-8')))
    hand = {r['id'] for r in csv.DictReader(open(D / 'screening' / 'handoffs.csv', encoding='utf-8'))}
    pick = [r for r in inc if (r['type'] == 'D' and r['stage'] in ('S2', 'S3')) or r['id'] in hand]
    with open(V / 'fulltext_sheet.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['id', 'stage', 'title', 'year', 'venue', 'link', 'abstract props', 'abstract classes']
                   + [q for _, q in QUESTIONS] + ['notes'])
        for r in sorted(pick, key=lambda x: (x['stage'], x['id'])):
            link = f"https://doi.org/{r['doi']}" if r['doi'] else (f"https://arxiv.org/abs/{r['arxiv']}" if r['arxiv'] else '')
            w.writerow([r['id'], r['stage'], r['title'], r['year'], r['venue'], link, r['props'], r['classes']]
                       + [''] * len(QUESTIONS) + [''])
    print(f'{len(pick)} studies -> {V / "fulltext_sheet.csv"}')


def score():
    inc = {r['id']: r for r in csv.DictReader(open(D / 'included_studies.csv', encoding='utf-8'))}
    rows = [r for r in csv.DictReader(open(V / 'fulltext_sheet.csv', encoding='utf-8-sig'))
            if any(r[q].strip() for _, q in QUESTIONS)]
    yes = lambda r, k: r[dict(QUESTIONS)[k]].strip().lower().startswith('y')
    out = {'checked': len(rows)}
    for k in ('t4', 't2', 'response', 'h1', 'h2', 'h3'):
        out[k] = [r['id'] for r in rows if yes(r, k)]
    changed = []
    for r in rows:
        for fld in ('props', 'classes'):
            ft = r[dict(QUESTIONS)[fld]].strip()
            if ft and set(c for c in ft if c.isdigit()) != set(c for c in inc[r['id']][fld] if c.isdigit()):
                changed.append({'id': r['id'], 'field': fld, 'abstract': inc[r['id']][fld], 'full_text': ft})
    out['code_changes'] = changed
    (V / 'fulltext_results.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    {'make': make, 'score': score}[sys.argv[1] if len(sys.argv) > 1 else 'make']()
