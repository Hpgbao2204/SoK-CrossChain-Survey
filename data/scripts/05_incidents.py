"""Step 5: map DefiLlama bridge hacks to the attack classes T1-T7 and to the earliest stage.

Input : data/incidents/defillama_hacks.json  (https://api.llama.fi/hacks, downloaded 2026-10-03)
Output: data/incidents/bridge_incidents.csv  every record with bridgeHack = true, with class and stage
        data/incidents/incident_stats.json   totals per class, per year and per stage

The mapping uses DefiLlama's 'technique' field. Overrides record cases where the auditor
post-mortems cited in data/incidents/major_incidents.csv give a different root cause.
"""
import csv, json, datetime
from collections import Counter, defaultdict
from pathlib import Path

D = Path(__file__).resolve().parents[1] / 'incidents'
raw = json.load(open(D / 'defillama_hacks.json', encoding='utf-8'))

T1 = {'Validator Key Compromised', 'Private Key Compromised', 'Hot Wallet Key Compromised', 'Deployer Key Compromised',
      'Weak Key Generation', 'Key Leaked via Infrastructure', 'Key Stored Publicly', 'Phishing', 'Database Breach'}
T2 = {'Signature Verification Flaw', 'Forged Proof', 'Proof Verifier Bug', 'Cross-Chain Message Spoofing',
      'Unbacked Cross-Chain Mint'}
T3 = {'Bridge Logic Flaw', 'Withdrawal Logic Flaw', 'Swap Logic Flaw', 'Missing Input Validation',
      'Improper Access Control', 'Caller Impersonation', 'Arbitrary External Call', 'Token Approval Abuse',
      'Uninitialized Proxy', 'Infinite Mint'}
T4 = {'Spoofed Event Log'}          # observation layer: off-chain components accept forged events
T6 = {'DNS Hijack', 'Impersonation Scam'}  # user-level and front-end attacks
# name, date -> class, with the reason
OVERRIDE = {
    ('Orbit Bridge', '2023-12-31'): ('T1', '7 of 10 signer keys compromised (Rekt; Lee et al. style post-mortems)'),
    ('Kelp', '2026-04-18'): ('T4', 'single verifier fed forged observations via poisoned RPC nodes (LayerZero report; Chainalysis)'),
    ('Gravity Bridge', '2026-05-30'): ('T3', 'permissionless token registry poisoned via fabricated denom (QuillAudits)'),
    ('ALEX', '2024-05-16'): ('T1', 'deployer key obtained by phishing'),
}


def cls(x, day):
    o = OVERRIDE.get((x['name'], day))
    if o:
        return o[0]
    t = x.get('technique') or ''
    for name, s in (('T1', T1), ('T2', T2), ('T3', T3), ('T4', T4), ('T6', T6)):
        if t in s:
            return name
    return 'unclassified'


STAGE = {'T1': 'S1', 'T4': 'S1', 'T2': 'S2', 'T3': 'S2', 'T6': 'out of scope', 'unclassified': 'unclassified'}
rows = []
for x in raw:
    if not x.get('bridgeHack'):
        continue
    day = datetime.datetime.fromtimestamp(x['date'], datetime.timezone.utc).strftime('%Y-%m-%d')
    c = cls(x, day)
    rows.append({'date': day, 'name': x['name'], 'loss_musd': round((x.get('amount') or 0) / 1e6, 3),
                 'returned_musd': round((x.get('returnedFunds') or 0) / 1e6, 3),
                 'defillama_classification': x.get('classification') or '', 'technique': x.get('technique') or '',
                 'class': c, 'earliest_stage': STAGE[c], 'override': OVERRIDE.get((x['name'], day), ('', ''))[1],
                 'source': x.get('source') or ''})
rows.sort(key=lambda r: r['date'])
with open(D / 'bridge_incidents.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

tot = sum(r['loss_musd'] for r in rows)
by_cls = Counter()
n_cls = Counter()
by_year_cls = defaultdict(Counter)
n_year = Counter()
for r in rows:
    by_cls[r['class']] += r['loss_musd']
    n_cls[r['class']] += 1
    by_year_cls[r['date'][:4]][r['class']] += r['loss_musd']
    n_year[r['date'][:4]] += 1
stats = {
    'n': len(rows), 'total_musd': round(tot, 1), 'first': rows[0]['date'], 'last': rows[-1]['date'],
    'loss_by_class': {k: round(v, 1) for k, v in by_cls.most_common()},
    'share_by_class': {k: round(100 * v / tot, 1) for k, v in by_cls.most_common()},
    'count_by_class': dict(n_cls),
    'loss_by_year_class': {y: {k: round(v, 1) for k, v in c.items()} for y, c in sorted(by_year_cls.items())},
    'count_by_year': dict(sorted(n_year.items())),
    'share_stage': {s: round(100 * sum(v for k, v in by_cls.items() if STAGE[k] == s) / tot, 1)
                    for s in set(STAGE.values())},
    'loss_ge_50m': sum(1 for r in rows if r['loss_musd'] >= 50),
}
(D / 'incident_stats.json').write_text(json.dumps(stats, indent=2), encoding='utf-8')
print(json.dumps(stats, indent=2))
