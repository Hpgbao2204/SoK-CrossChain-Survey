"""Step 6: data figures for the paper (vector PDF, sized for the LNCS text block of 122 mm).

fig5_incidents.pdf  bridge-incident losses per year, stacked by attack class (DefiLlama)
fig4_corpus.pdf     included studies per year, stacked by study type / lifecycle stage
fig6_coverage.pdf   coverage heatmaps: properties x stage and attack classes x stage, with incident share
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'data'
OUT = ROOT / 'figures'
MM = 1 / 25.4
plt.rcParams.update({
    'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 7.5, 'axes.labelsize': 7.5, 'axes.titlesize': 8, 'xtick.labelsize': 7, 'ytick.labelsize': 7,
    'legend.fontsize': 7, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': 0.6,
    'xtick.major.width': 0.6, 'ytick.major.width': 0.6, 'pdf.fonttype': 42,
})
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e4e3df'
CAT = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4']   # validated categorical order
OTHER = '#b5b3ad'


def stacked(ax, xs, series, colors, labels, hatches=None):
    bottom = np.zeros(len(xs))
    handles = []
    for i, (vals, col, lab) in enumerate(zip(series, colors, labels)):
        h = ax.bar(xs, vals, bottom=bottom, color=col, width=0.62, edgecolor='white', linewidth=0.8,
                   label=lab, hatch=(hatches[i] if hatches else None), zorder=3)
        handles.append(h)
        bottom += np.array(vals)
    return bottom, handles


# ---------- Fig. 4: incident losses ----------
inc = json.loads((D / 'incidents' / 'incident_stats.json').read_text(encoding='utf-8'))
years = sorted(inc['loss_by_year_class'])
classes = [('T2', 'T2 verification flaw'), ('T1', 'T1 key or verifier-set compromise'),
           ('T3', 'T3 contract logic or access control'), ('T4', 'T4 forged observation')]
series = [[inc['loss_by_year_class'][y].get(c, 0) for y in years] for c, _ in classes]
other = [sum(v for k, v in inc['loss_by_year_class'][y].items() if k not in dict(classes)) for y in years]
fig, ax = plt.subplots(figsize=(122 * MM, 52 * MM))
xs = np.arange(len(years))
top, _ = stacked(ax, xs, series + [other], CAT[:4] + [OTHER], [l for _, l in classes] + ['other'],
                 hatches=[None, '////', None, '\\\\\\\\', None])
for x, y, t in zip(xs, years, top):
    ax.text(x, t + 25, f"{inc['count_by_year'][y]} incidents", ha='center', va='bottom', fontsize=6.5, color=MUTED)
ax.set_xticks(xs, years)
ax.set_ylabel('Loss (million USD, nominal)')
ax.set_ylim(0, max(top) * 1.15)
ax.yaxis.grid(True, color=GRID, linewidth=0.6, zorder=0)
ax.legend(frameon=False, loc='upper right', ncol=1, handlelength=1.4, borderaxespad=0.2)
fig.tight_layout(pad=0.3)
fig.savefig(OUT / 'fig5_incidents.pdf')
plt.close(fig)

# ---------- Fig. 5: corpus per year ----------
st = json.loads((D / 'corpus_stats.json').read_text(encoding='utf-8'))
yrs = [str(y) for y in range(2019, 2027)]
groups = [('S1', 'S1 specify'), ('S2', 'S2 assure'), ('S3', 'S3 operate and respond'),
          ('Attack/measurement', 'attack or measurement'), ('Survey', 'survey or SoK')]
series = [[st['by_year_stage'].get(y, {}).get(g, 0) for y in yrs] for g, _ in groups]
fig, ax = plt.subplots(figsize=(122 * MM, 50 * MM))
xs = np.arange(len(yrs))
top, _ = stacked(ax, xs, series, CAT[:5], [l for _, l in groups], hatches=[None, '////', None, '\\\\\\\\', None])
for x, t in zip(xs, top):
    ax.text(x, t + 1.5, f'{int(t)}', ha='center', va='bottom', fontsize=6.5, color=MUTED)
ax.set_xticks(xs, yrs)
ax.set_ylabel('Included studies')
ax.set_ylim(0, max(top) * 1.15)
ax.yaxis.grid(True, color=GRID, linewidth=0.6, zorder=0)
ax.legend(frameon=False, loc='upper left', handlelength=1.4, borderaxespad=0.2)
fig.tight_layout(pad=0.3)
fig.savefig(OUT / 'fig4_corpus.pdf')
plt.close(fig)

# ---------- Fig. 6: coverage heatmaps ----------
cols = [('S1', 'S1'), ('S2', 'S2'), ('S3', 'S3'), ('M', 'A/M')]
props = ['P1 authenticity', 'P2 uniqueness', 'P3 conservation', 'P4 authorization', 'P5 atomicity',
         'P6 economic', 'P7 confidentiality']
cls = ['T1 key, verifier set', 'T2 verification', 'T3 logic, access', 'T4 observation',
       'T5 consistency', 'T6 economic, user', 'T7 privacy']
P = np.array([[st['prop_by_group'][g].get(str(i), 0) for g, _ in cols] for i in range(1, 8)], float)
C = np.array([[st['class_by_group'][g].get(str(i), 0) for g, _ in cols] for i in range(1, 8)], float)
n = np.array([st['size_by_group'][g] for g, _ in cols], float)
share = [inc['share_by_class'].get(f'T{i}', 0.0) for i in range(1, 8)]
BLUE = matplotlib.colors.LinearSegmentedColormap.from_list(
    'b', ['#fcfcfb', '#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b'])

fig, axes = plt.subplots(1, 2, figsize=(122 * MM, 58 * MM), gridspec_kw={'wspace': 0.95})
for ax, M, rows, title in ((axes[0], P, props, 'Security property'), (axes[1], C, cls, 'Attack class')):
    frac = M / n  # share of the studies in each column
    ax.imshow(frac, cmap=BLUE, vmin=0, vmax=0.6, aspect='auto')
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = int(M[i, j])
            ax.text(j, i, '0' if v == 0 else str(v), ha='center', va='center', fontsize=6.8,
                    color='white' if frac[i, j] > 0.33 else (MUTED if v == 0 else INK),
                    fontweight='bold' if v == 0 else 'normal')
            if v == 0:
                ax.add_patch(plt.Rectangle((j - 0.42, i - 0.42), 0.84, 0.84, fill=False, edgecolor='#c44e52',
                                           linewidth=0.8, linestyle=(0, (2, 1.2)), zorder=5))
    ax.set_xticks(range(len(cols)), [c for _, c in cols])
    ax.set_yticks(range(len(rows)), rows)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(-.5, len(cols)), minor=True)
    ax.set_yticks(np.arange(-.5, len(rows)), minor=True)
    ax.grid(which='minor', color='white', linewidth=1.5)
    ax.tick_params(which='minor', length=0)
    ax.set_title(title, loc='center', fontsize=7.5, color=INK, pad=6, fontweight='bold')
    ax.xaxis.tick_top()
# incident loss share next to the class panel
ax2 = axes[1]
for i, s in enumerate(share):
    # one decimal, the same convention as the text (T2 40.5% + T3 21.5% = 62.0%)
    ax2.text(len(cols) - 0.35, i, f'{s:.1f}%' if s >= 0.05 else '0%', ha='left', va='center', fontsize=6.8,
             color=INK if s >= 0.5 else MUTED)
ax2.text(len(cols) - 0.35, -0.62, 'loss', ha='left', va='bottom', fontsize=7, color=MUTED)
#
#
fig.subplots_adjust(left=0.175, right=0.935, top=0.86, bottom=0.03)
fig.savefig(OUT / 'fig6_coverage.pdf')
plt.close(fig)
print('figures written')
