"""Step 8: the systematization table of representative studies.

Rows are grouped by PCL stage and defense family; every code comes from data/included_studies.csv,
so the table cannot drift from the coded corpus. Output: tables/tab_studies.tex
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'data'
(ROOT / 'tables').mkdir(exist_ok=True)
rows = {r['id']: r for r in csv.DictReader(open(D / 'included_studies.csv', encoding='utf-8'))}
hand = {r['id']: r['kind'] for r in csv.DictReader(open(D / 'screening' / 'handoffs.csv', encoding='utf-8'))}
HAND_SYM = {'H1-partial': 'H1$^\\circ$', 'spec-to-monitor': 'H1$^\\circ$', 'H2': 'H2', 'H3-partial': 'H3$^\\circ$'}

# (stage, family label, family size in the corpus, [(id, short name, bib key, technique)])
GROUPS = [
    ('S1', 'light clients, ZK and optimistic verification', 50, [
        ('R0274', 'zkBridge', 'xie2022zkbridge', 'ZK proof of consensus'),
        ('R1294', 'Glimpse', 'scaffino2023glimpse', 'on-demand light client')]),
    ('S1', 'committees, threshold signatures and collateral', 57, [
        ('R0356', 'XCLAIM', 'zamyatin2019xclaim', 'collateralized vaults'),
        ('R0035', 'Bool Network', 'yin2022bool', 'MPC committee, TEE')]),
    ('S1', 'atomic swaps, channels and atomic calls', 94, [
        ('R0160', 'MAD-HTLC', 'tsabary2021madhtlc', 'HTLC incentives'),
        ('R0639', 'PipeSwap', 'pipeswap2025', 'adaptor signatures')]),
    ('S1', 'authentication, access control and privacy', 113, [
        ('R0186', 'P2C2T', 'p2c2t2025', 'anonymous locks'),
        ('R0917', 'zk-HTLC', 'zkhtlc2026', 'ZK proofs, HTLC')]),
    ('S1', 'formal protocol models', 12, [
        ('R0947', 'IBC in TLA+', 'tsai2023ibc', 'model checking')]),
    ('S2', 'static, symbolic and formal analysis', 8, [
        ('R0051', 'SmartAxe', 'liao2024smartaxe', 'static analysis'),
        ('R0569', 'BridgeGuard', 'zhou2025bridgeguard', 'symbolic dataflow'),
        ('R1420', 'Phantom Events', 'liu2025phantom', 'static analysis')]),
    ('S2', 'fuzzing, learned and LLM auditors', 10, [
        ('R1000', 'BridgeFuzz', 'winkler2026bridgefuzz', 'fuzzing'),
        ('R1488', 'IntentFuzz', 'augusto2026intentfuzz', 'protocol-aware fuzzing'),
        ('R0945', 'CrossGuard', 'tran2026crossguard', 'few-shot learning')]),
    ('S3', 'rule and accounting monitors', 11, [
        ('R0046', 'XScope', 'zhang2022xscope', 'security rules'),
        ('R0265', 'XChainWatcher', 'augusto2025xchainwatcher', 'Datalog rules'),
        ('R0745', 'Monte Crypto', 'liu2024monte', 'value accounting')]),
    ('S3', 'graph and learned detectors', 10, [
        ('R0130', 'Wu et al.', 'wu2025safeguarding', 'call-structure mining'),
        ('R1045', 'VeriBridge', 'tran2025veribridge', 'static-informed graph')]),
    ('S3', 'trust scoring, tracing and response', 21, [
        ('R0318', 'CCC-TM', 'yi2024ccctm', 'committee trust model'),
        ('R0307', 'ABCTracer', 'lin2025track', 'transaction tracing'),
        ('R1323', 'Auto-pausing', 'mateus2025pausing', 'conformance, pause')]),
]
STAGE_NAME = {'S1': 'S1 Specify', 'S2': 'S2 Assure', 'S3': 'S3 Operate and respond'}
NCOL = 7


def ids(prefix, s):
    d = [c for c in s if c.isdigit()]
    return ', '.join(prefix + c for c in d) if d else '--'


L = ['\\begin{table}[!htb]', '\\centering',
     '\\caption{Representative defenses by PCL stage and family ($n$ = studies of the family in the corpus). '
     'Evidence: F formal proof or model checking, E prototype or experiment, '
     'R real incidents or real-chain data. Hand-off as in Fig.~\\ref{fig:framework}; $^\\circ$ partial.}',
     '\\label{tab:approaches}', '\\scriptsize', '\\setlength{\\tabcolsep}{3pt}', '\\renewcommand{\\arraystretch}{1.18}',
     '\\arrayrulecolor{black!25}',
     '\\begin{tabular}{@{}M{2.5cm}M{0.65cm}M{2.45cm}M{1.7cm}M{1.45cm}M{1.25cm}M{0.9cm}@{}}',
     '\\arrayrulecolor{black}\\toprule',
     '\\textbf{Study} & \\textbf{Year} & \\textbf{Technique} & \\textbf{Properties} & \\textbf{Attack classes} & '
     '\\textbf{Evidence} & \\textbf{Hand-\\newline off} \\\\',
     '\\midrule\\arrayrulecolor{black!25}']
first = True
for stage, fam, n, items in GROUPS:
    if not first:
        L.append('\\hline')
    first = False
    L.append(f'\\rowcolor{{black!8}}\\multicolumn{{{NCOL}}}{{@{{}}l@{{}}}}{{\\textbf{{{STAGE_NAME[stage]}}}: {fam} ($n={n}$)}} \\\\')
    for i, (rid, name, key, tech) in enumerate(items):
        r = rows[rid]
        ev = ', '.join(c for c in 'FER' if c in r['eval']) or '--'
        h = HAND_SYM.get(hand.get(rid, ''), '--')
        L.append('\\hline')
        L.append(' & '.join([f'{name}~\\cite{{{key}}}', r['year'], tech, ids('P', r['props']), ids('T', r['classes']), ev, h]) + ' \\\\')
L += ['\\arrayrulecolor{black}\\bottomrule', '\\end{tabular}', '\\end{table}']
(ROOT / 'tables' / 'tab_studies.tex').write_text('\n'.join(L) + '\n', encoding='utf-8')
print('rows', sum(len(g[3]) for g in GROUPS))
