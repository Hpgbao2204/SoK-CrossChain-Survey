# Review protocol and data

This folder holds everything needed to reproduce the counts, tables and figures of the SoK.
Run the scripts from the SoK folder in order; each step only reads the outputs of earlier steps.

| Step | Script | Output |
|---|---|---|
| 1 Search | `scripts/01_search.py` | `raw/openalex.jsonl`, `raw/s2.jsonl`, `raw/arxiv.jsonl`, `raw/search_log.json` |
| 2 Merge, de-duplicate, rules R1-R2 | `scripts/02_merge.py` | `records_all.csv`, `records_dedup.csv`, `to_screen.csv`, `prisma_counts_stage1.json` |
| 3 Title screening | `scripts/03_title_screen.py` | `screening/title_decisions.csv`, `to_abstract.csv` |
| 4 Abstract screening, eligibility, coding | `scripts/04_finalize.py` | `included_studies.csv`, `prisma_counts.json`, `corpus_stats.json` |
| 5 Incidents | `scripts/05_incidents.py` | `incidents/bridge_incidents.csv`, `incidents/incident_stats.json` |
| 6 Figures | `scripts/06_figures.py` | `../figures/fig4_corpus.pdf`, `fig5_incidents.pdf`, `fig6_coverage.pdf` |

## Research questions
- RQ1 Which attack classes threaten cross-chain communication, which security property does each violate, and how do they map to real incidents?
- RQ2 Which defenses exist at each lifecycle stage (specify, assure before deployment, operate and respond), and which properties and attack classes do they cover?
- RQ3 Which gaps remain within the stages and in the hand-offs between them?

## Search
- Databases: OpenAlex (title and abstract), Semantic Scholar bulk search, arXiv API. Search date 2026-10-03, years 2019-2026.
- Boolean string (OpenAlex form; exact strings per source in `raw/search_log.json`):
  `(blockchain OR "distributed ledger" OR DeFi OR "smart contract") AND ("cross-chain" OR crosschain OR "cross-blockchain" OR "inter-blockchain" OR "blockchain bridge" OR "token bridge" OR "bridge protocol" OR "blockchain interoperability" OR "interoperability protocol" OR "atomic swap" OR "cross-ledger" OR sidechain) AND (attack OR exploit OR vulnerability OR security OR secure OR anomaly OR hack OR privacy OR audit OR fraud OR "formal verification" OR trust)`
- Other methods: reference lists of included SoKs and the authors' bibliographies (`screening/other_methods.csv`).

## Automated rules (before screening)
- R1 non-research item (editorial, paratext, erratum, book, thesis, report), missing title, or year outside 2019-2026.
- R2 no cross-chain term in the title and fewer than two in the abstract.
- A third rule (no security term) was tested and dropped because it removed relevant studies.

## Inclusion criteria
- IC1 The study proposes, analyses or evaluates an attack, vulnerability, threat model or security mechanism whose object is cross-chain communication itself: a bridge, messaging protocol, relay, sidechain transfer, atomic swap or cross-chain payment channel, including the authentication and privacy of the parties to such a transfer.
- IC2 The study reviews such work (survey or SoK).

## Exclusion criteria
Title and abstract screening
- A cross-chain is only infrastructure for an application system (health records, supply chain, energy trading, voting); the security object is the application's data.
- N cross-chain without a security contribution (performance, architecture, standards, general interoperability surveys).
- O off-topic (single-chain security, sharding, general blockchain or DeFi fraud).
- R non-English, thesis or non-research.

Eligibility (bibliographic record and reported evidence)
- ED duplicate or superseded version (the journal version is kept).
- EQ non-refereed outlet without any formal or empirical evaluation; preprint surveys and position papers; outlets with no editorial process (Zenodo, Figshare, SSRN, Research Square).
- EI insufficient information to decide (no abstract and an ambiguous title, no accessible record).

Eligibility was decided on the abstract and the bibliographic record, not on the full text.

## Codebook (one line per included study)
- type: S survey or SoK; M attack or measurement study; D defense.
- stage (defenses): S1 specify (design-time protocol, trust model, authentication, privacy); S2 assure before deployment (analysis of code or specifications of a concrete implementation); S3 operate and respond (monitoring, detection, trust scoring at runtime, tracing, datasets of live transfers, response).
- props: security properties the study states it protects or analyses (P1 authenticity, P2 uniqueness, P3 conservation, P4 authorization, P5 atomicity and liveness, P6 economic soundness, P7 confidentiality). A property is coded only when the abstract names it or a mechanism that directly enforces it.
- classes: attack classes the study names (T1 key or verifier-set compromise, T2 verification flaws, T3 contract-logic and access-control flaws, T4 observation and relay attacks, T5 consistency and atomicity attacks, T6 economic and user-level attacks, T7 privacy and linkability attacks). '-' when no class is named.
- tech: technique families. S1: COM committee/notary/TSS/MPC, LC light client or relay, ZK proof-based bridge, OPT optimistic, SWAP HTLC/adaptor-signature swap, ATOM atomic cross-chain transactions, PCN payment channels, TEE, AUTH authentication or access control, PRIV privacy, INTEG data integrity or auditability, ECON incentives or game theory, FM formal model, ARCH secure architecture, TRUST reputation. S2: SA static analysis, FUZZ, FV formal verification of code, ML learned auditor, LLM, TEST test generation. S3: RULE rule or invariant monitor, ACC accounting, GML graph or learned detector, TRUST runtime trust scoring, TRACE transaction tracing, DATA dataset, RESP response.
- eval: F formal proof or model checking; E prototype or experiment; R evaluation on real incidents or real-chain data; N none reported.

## Incidents
DefiLlama hacks dataset (`incidents/defillama_hacks.json`, records with `bridgeHack = true`), mapped from its technique field to T1-T7 by `scripts/05_incidents.py`. Overrides are documented in the script. The incidents of at least USD 50 million in the paper's table are cross-checked against a second, independent source listed in `incidents/major_incidents.csv`.

## Known limitations to report
- Screening and coding were drafted by an LLM assistant and checked by the authors. Before submission, a second author should independently code a random 20% sample of `included_studies.csv` (stage, props, classes) and report Cohen's kappa per field.
- Coding uses titles and abstracts; 229 records had no indexed abstract.
- Loss figures are nominal USD at the time of the incident and do not subtract returned funds.

## Later steps
| Step | Script | Output |
|---|---|---|
| 7 Bibliography | `scripts/07_bib.py` | `../refs.bib` (from `../refs_extra.bib`, `../old/refs_v1.bib` and corpus records) |
| 8 Study table | `scripts/08_table.py` | `../tables/tab_studies.tex` (Table 4) |
| 9 Agreement | `scripts/09_agreement.py sample` / `score` | `agreement/coding_sheet.csv`, `agreement/screening_sheet.csv`, `agreement/agreement_results.json` (guide: `agreement/HUONG_DAN_KAPPA.md`) |

Figures 1-3 are generated by `../figures/make_drawio.py` (icons in `../figures/icons.py`); `../figures/drawio_html.py` renders an HTML preview of a .drawio file.
