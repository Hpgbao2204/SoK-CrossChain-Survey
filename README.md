# Artifact: SoK on security properties through the cross-chain lifecycle

Everything needed to reproduce the counts, tables and figures of the paper.

- `data/PROTOCOL.md`: research questions, search string, inclusion and exclusion criteria, codebook.
- `data/records_dedup.csv`: all de-duplicated records with the automated-rule decision (abstracts omitted;
  `data/scripts/01_search.py` re-fetches them from OpenAlex, Semantic Scholar and arXiv).
- `data/screening/`: title- and abstract-stage decisions with reason codes, hand-off coding.
- `data/included_studies.csv`: the 429 included studies with their codes.
- `data/incidents/`: DefiLlama snapshot (3 October 2026, attribution: DefiLlama) and the class mapping.
- `data/scripts/`: from this folder run `python data/scripts/03_title_screen.py`, then 04, 05, 06 and 08,
  to regenerate every count, the figures (`figures/`) and the study table (`tables/`); 01 and 02 repeat the search.
