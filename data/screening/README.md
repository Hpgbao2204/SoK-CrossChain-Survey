# Screening and coding files

| File | Content |
|---|---|
| `title_excl_0..2.txt`, `title_keep_3.txt` | Title-stage decisions for the four batches of `to_screen.csv` (codes A, N, O, X, R; see `scripts/03_title_screen.py`) |
| `title_decisions.csv` | One row per screened record with its title-stage decision |
| `abs_code_00..09.txt` | Abstract-stage decision and coding, one line per record (format in `scripts/04_finalize.py`) |
| `abs_code_10_corrections.txt` | Corrections found during the citation check (they override earlier lines) |
| `abstract_decisions.csv` | Abstract-stage decision per record |
| `other_methods.csv` | Studies added by citation searching, with their codes |
| `handoffs.csv` | Studies whose output is consumed by, or produced for, another lifecycle stage |

Screening and coding were drafted by an LLM assistant from titles and abstracts and must be
checked by the authors; a second coder should re-code a random 20% sample (see `../PROTOCOL.md`).
