"""Step 9: inter-coder agreement (Cohen's kappa) between coder 1 (released codes) and an independent coder 2.

Usage (from the SoK folder):
  python data/scripts/09_agreement.py sample     # writes the blank sheets for coder 2
  python data/scripts/09_agreement.py score      # reads the filled sheets and prints kappa

Two sheets are produced in data/agreement/ (UTF-8 CSV, opens in Excel):
  coding_sheet.csv     20% of the included studies, stratified by type/stage, for re-coding
                       type, stage, props and classes with the codebook in PROTOCOL.md
  screening_sheet.csv  10% of the screened records, half included and half excluded by coder 1,
                       for an include/exclude decision on title and abstract
Coder 2 must not look at included_studies.csv or the screening files while filling them in.
"""
import csv, json, random, sys
from collections import Counter, defaultdict
from pathlib import Path

D = Path(__file__).resolve().parents[1]
A = D / 'agreement'
A.mkdir(exist_ok=True)
SEED = 20261003


def kappa(a, b):
    """Cohen's kappa for two lists of nominal labels."""
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0, po, pe


def boot_ci(a, b, reps=2000):
    rng = random.Random(SEED)
    vals = []
    idx = list(range(len(a)))
    for _ in range(reps):
        s = [rng.choice(idx) for _ in idx]
        k, _, _ = kappa([a[i] for i in s], [b[i] for i in s])
        vals.append(k)
    vals.sort()
    return vals[int(0.025 * reps)], vals[int(0.975 * reps)]


def digits(s):
    return {c for c in (s or '') if c.isdigit()}


def sample():
    inc = list(csv.DictReader(open(D / 'included_studies.csv', encoding='utf-8')))
    recs = {r['rid']: r for r in csv.DictReader(open(D / 'records_dedup.csv', encoding='utf-8'))}
    rng = random.Random(SEED)
    strata = defaultdict(list)
    for r in inc:
        strata[(r['type'], r['stage'])].append(r)
    pick = []
    for key, rs in sorted(strata.items()):
        k = max(1, round(0.2 * len(rs)))
        pick += rng.sample(rs, k)
    rng.shuffle(pick)
    with open(A / 'coding_sheet.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['id', 'title', 'year', 'venue', 'abstract', 'type (S/M/D)', 'stage (S1/S2/S3/-)',
                    'props (digits 1-7, e.g. 137, or -)', 'classes (digits 1-7 or -)'])
        for r in pick:
            ab = recs.get(r['id'], {}).get('abstract', '') if r['id'].startswith('R') else ''
            w.writerow([r['id'], r['title'], r['year'], r['venue'], ab, '', '', '', ''])
    # screening sample: 10% of screened records, balanced between coder-1 includes and excludes
    title = {r['rid']: r['title_decision'] for r in csv.DictReader(open(D / 'screening' / 'title_decisions.csv', encoding='utf-8'))}
    absd = {r['rid']: r['decision'] for r in csv.DictReader(open(D / 'screening' / 'abstract_decisions.csv', encoding='utf-8'))}
    screened = list(csv.DictReader(open(D / 'to_screen.csv', encoding='utf-8')))
    dec1 = {r['rid']: ('include' if absd.get(r['rid']) == 'I' else 'exclude') for r in screened}
    pos = [r for r in screened if dec1[r['rid']] == 'include']
    neg = [r for r in screened if dec1[r['rid']] == 'exclude']
    n = round(0.1 * len(screened))
    spick = rng.sample(pos, n // 2) + rng.sample(neg, n - n // 2)
    rng.shuffle(spick)
    with open(A / 'screening_sheet.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['rid', 'title', 'year', 'venue', 'abstract', 'decision (include/exclude)'])
        for r in spick:
            w.writerow([r['rid'], r['title'], r['year'], r['venue'], r['abstract'], ''])
    json.dump({'coding': [r['id'] for r in pick], 'screening': [r['rid'] for r in spick]},
              open(A / 'sample_ids.json', 'w'), indent=1)
    print(f'coding sheet: {len(pick)} studies; screening sheet: {len(spick)} records -> {A}')


def score():
    inc = {r['id']: r for r in csv.DictReader(open(D / 'included_studies.csv', encoding='utf-8'))}
    out = {}
    rows = [r for r in csv.DictReader(open(A / 'coding_sheet.csv', encoding='utf-8-sig')) if r['type (S/M/D)'].strip()]
    if rows:
        ids = [r['id'] for r in rows]
        c1 = [inc[i] for i in ids]
        for field, col in (('type', 'type (S/M/D)'), ('stage', 'stage (S1/S2/S3/-)')):
            a = [r[field] for r in c1]
            b = [r[col].strip().upper() for r in rows]
            k, po, pe = kappa(a, b)
            lo, hi = boot_ci(a, b)
            out[field] = {'n': len(a), 'kappa': round(k, 3), 'ci95': [round(lo, 3), round(hi, 3)],
                          'observed_agreement': round(po, 3), 'chance_agreement': round(pe, 3)}
        for field, col in (('props', 'props (digits 1-7, e.g. 137, or -)'), ('classes', 'classes (digits 1-7 or -)')):
            per = {}
            for lab in '1234567':
                a = [lab in digits(r[field]) for r in c1]
                b = [lab in digits(r[col]) for r in rows]
                k, po, _ = kappa(a, b)
                per[('P' if field == 'props' else 'T') + lab] = round(k, 3)
            jac = [len(digits(x[field]) & digits(y[col])) / max(1, len(digits(x[field]) | digits(y[col])))
                   for x, y in zip(c1, rows)]
            vals = list(per.values())
            out[field] = {'per_label_kappa': per, 'mean_kappa': round(sum(vals) / len(vals), 3),
                          'min_kappa': min(vals), 'max_kappa': max(vals), 'mean_jaccard': round(sum(jac) / len(jac), 3)}
    srows = [r for r in csv.DictReader(open(A / 'screening_sheet.csv', encoding='utf-8-sig'))
             if r['decision (include/exclude)'].strip()]
    if srows:
        absd = {r['rid']: r['decision'] for r in csv.DictReader(open(D / 'screening' / 'abstract_decisions.csv', encoding='utf-8'))}
        a = ['include' if absd.get(r['rid']) == 'I' else 'exclude' for r in srows]
        b = [r['decision (include/exclude)'].strip().lower() for r in srows]
        k, po, pe = kappa(a, b)
        lo, hi = boot_ci(a, b)
        out['screening'] = {'n': len(a), 'kappa': round(k, 3), 'ci95': [round(lo, 3), round(hi, 3)],
                            'observed_agreement': round(po, 3), 'chance_agreement': round(pe, 3)}
        out['screening_disagreements'] = [r['rid'] for r, x, y in zip(srows, a, b) if x != y]
    (A / 'agreement_results.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    {'sample': sample, 'score': score}[sys.argv[1] if len(sys.argv) > 1 else 'sample']()
