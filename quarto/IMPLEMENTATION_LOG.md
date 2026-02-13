# Implementation Log: Quarto Writeup

This log documents the construction of the Quarto master document from prior experimental outputs and the integration of defence feedback from `memory-bank/papers/family_survival_revised.md`.

## 1. Document Architecture

The document is a modular Quarto project rendering to Typst/PDF. `index.qmd` includes 19 component files via `{{< include >}}` directives.

```
quarto/
  index.qmd                           # master entry point
  _quarto.yml                         # Typst format config
  references.bib                      # citations (BibLaTeX)
  tables/table_generator.py           # shared table formatting utilities
  sections/01-introduction.qmd        # Ch 1
  sections/02-literature-review.qmd   # Ch 2
  sections/03-institutional-context.qmd # Ch 3
  sections/04-hypotheses.qmd          # Ch 4
  sections/05-data.qmd                # Ch 5
  sections/06-methods.qmd             # Ch 6
  sections/07-results.qmd             # Ch 7 (summary + includes)
  sections/08-discussion.qmd          # Ch 8
  sections/09-conclusion.qmd          # Ch 9
  results/results-exp009-crises.qmd   # Sec 7.3 crisis interactions
  results/results-exp010-mechanisms.qmd # Sec 7.1 mechanism testing
  results/results-exp011-subperiods.qmd # Sec 7.2 subperiod analysis
  results/results-exp012-governors.qmd  # Sec 7.4 governor regimes
  appendices/appendix-{A..E}.qmd      # appendices A--E
```

### Render command

```bash
QUARTO_PYTHON=.venv-quarto/bin/python quarto render index.qmd
```

Output: `_output/index.pdf` (Typst format, A4, numbered sections, ToC).

---

## 2. Defence Feedback Addressed

Source: `memory-bank/papers/family_survival_revised.md` (reviewer: drfilich)

### 2a. Causal language audit

**Feedback**: 'lax caution, makes claims that cannot be substantiated', 'associated not causes'

**Action**: Systematic replacement across all `.qmd` files:
- 'demonstrates' -> 'is associated with' / 'suggests'
- 'confirms' -> 'is consistent with'
- 'proves' -> 'provides evidence for'

**Files touched**: `08-discussion.qmd`, `09-conclusion.qmd`, `07-results.qmd`, `results-exp010-mechanisms.qmd`

### 2b. Network endogeneity elevated to substantive finding

**Feedback**: 'endogeneity is not clearly signposted as a significant result'; the revised paper (family_survival_revised.md, line 952) framed network centrality endogeneity as a key finding under 'Network centrality: The endogeneity of systemic importance'

**Action**: Renamed discussion section from 'Dynamic Reverse Causality as a Substantive Finding' to 'Network Endogeneity as a Substantive Finding'. Added two subsections:

1. **Endogeneity of Pure Network Centrality** -- the 'network firefighter' interpretation: out-degree (voluntary, protective, HR = 0.958--0.977) vs PageRank (potentially involuntary, harmful or neutral, HR = 1.010 in 2007--2013)
2. **Dynamic Reverse Causality of the Family Connection Ratio** -- the bidirectional FCR finding from exp_013

```markdown
## Network Endogeneity as a Substantive Finding

### Endogeneity of Pure Network Centrality
[...] out-degree (voluntary, protective) vs PageRank (involuntary, harmful) [...]

### Dynamic Reverse Causality of the Family Connection Ratio
[...] bidirectional and temporally heterogeneous [...]
```

**File**: `sections/08-discussion.qmd`

### 2c. Other tie types acknowledged

**Feedback**: 'need to be clear that there are other types of ties', 'family networks are not the only possibility'

**Action**: Added explicit acknowledgement in introduction, discussion (section 'Other Informal Tie Types'), and conclusion limitations that kinship is one of several informal governance mechanisms. Explained why family is the focus: (1) verifiable through CBR disclosures and naming conventions; (2) Ledeneva's framework foregrounds kinship; (3) prior factionalism work motivates the family dimension.

**Files touched**: `01-introduction.qmd`, `08-discussion.qmd`, `09-conclusion.qmd`

### 2d. 'Structural clusters' -> 'structural neighbourhoods'

**Feedback**: 'cluster is the wrong word, local neighbourhood is better'

**Action**: Global search-and-replace across all `.qmd` files.

### 2e. Exogenous vs endogenous shock distinction

**Feedback**: '2008 and 2014 are different. Rogov and Reinhart', '2008 Russia was not in the epicentre, shock exogenous'

**Action**: Added to `results-exp009-crises.qmd` and `03-institutional-context.qmd`: 2008 was an exogenous economic shock (Reinhart & Rogoff typology); 2014 was an endogenous geopolitical shock. Citation added to `references.bib`.

### 2f. DIA deposit insurance and 2004 crisis detail

**Feedback**: 'Leak from CBR: shortlist of banks to be included in DIA. Bank run.'

**Action**: Expanded Sodbiznesbank subsection in `03-institutional-context.qmd` to include the leaked DIA eligibility list and resulting bank run.

### 2g. Putin political context for 2008

**Feedback**: 'Putin PM: we will have Russian banks first, foreign banks are not a priority during 2008'

**Action**: Added to `03-institutional-context.qmd`: Putin's public signalling that Russian banks would receive priority state support during the GFC.

### 2h. CBR governor political dimension

**Feedback**: 'CBR governor very trusted by Putin: tacit conflict between banks run by security services vs CBR'

**Action**: Added to `03-institutional-context.qmd` and `results-exp012-governors.qmd`: Nabiullina's appointment as a political decision by Putin, with the cleanup campaign creating tacit conflict with siloviki-connected banks.

### 2i. Directed vs undirected centrality

**Feedback**: 'Centrality measures should be different for FAMILY (undirected) OWNERSHIP (directed)'

**Action**: Added paragraph in `05-data.qmd` clarifying: ownership metrics computed on directed graph; family connection ratio computed from undirected family subgraph (kinship is symmetric). Referenced Padgett & Ansell (1993).

### 2j. ERGMs acknowledged

**Feedback**: 'in networks, we have to use ERGMs'

**Action**: Added note in `06-methods.qmd` acknowledging ERGMs as an alternative but computationally prohibitive at our scale (~140K observations).

### 2k. 'Counter-cyclical' language corrected

**Feedback**: 'not a business cycle, refine the language'

**Action**: Replaced 'counter-cyclical hedge' with 'cross-sector diversification buffer' in `results-exp010-mechanisms.qmd`.

### 2l. H1 clarity and alternative framing

**Feedback**: 'H1 setup is not clear but clear in discussion', 'Flip H1: banks survive regardless of CAMEL'

**Action**: Rewrote H1a in `04-hypotheses.qmd` to lead with the expected finding. Added paragraph on the alternative interpretation that family connections may override formal regulatory criteria.

### 2m. H2c reformulated for modularity

**Feedback**: 'H2 community structure... formulate in terms of modularity'

**Action**: Rewrote H2c in `04-hypotheses.qmd` to use 'local neighbourhood' and reference community detection/modularity.

### 2n. Closure heterogeneity caveat

**Feedback**: 'family connections may be associated differently with different closure reasons'

**Action**: Added limitation paragraph in `08-discussion.qmd` and future research item in `09-conclusion.qmd`.

### 2o. Contagion literature

**Feedback**: 'Contagion mechanisms? Acemoglu paper'

**Action**: Added Acemoglu, Ozdaglar & Tahbaz-Salehi (2015) to `02-literature-review.qmd` and `references.bib`.

### 2p. Multicollinearity note

**Feedback**: 'multicollinearity'

**Action**: Added note in `05-data.qmd` identification considerations on VIF monitoring and L2 penaliser.

### 2q. Illustrative cases

**Feedback**: 'Pugachev, Hatimsky, Bank in Rostov'

**Action**: Added brief mention of Mezhprombank/Pugachev and Centre-Invest (Rostov) in `01-introduction.qmd`.

### New citations added to `references.bib`

- Reinhart & Rogoff (2009) *This Time Is Different*
- Acemoglu, Ozdaglar & Tahbaz-Salehi (2015) systemic risk in networks
- Padgett & Ansell (1993) Florentine marriage networks

---

## 3. Dynamic Tables from Experiment CSVs

### Problem

The original writeup used static markdown tables with hardcoded values. Several had errors (e.g., M7-M10 HR values did not match the actual CSV data), and some had missing fields (exp_009 AIC column was all `--`).

### Solution

Replaced static tables with Python code chunks using `#| output: asis` that read directly from experiment CSV outputs. The `table_generator.py` module provides shared formatting utilities.

### Key pattern

```python
#| output: asis

import pandas as pd
import sys
sys.path.insert(0, 'tables')
from table_generator import fmt_cell, TABLE_LABELS, to_quarto_table

df = pd.read_csv('../experiments/exp_010_mechanism_testing/stargazer_M1_Political.csv')
# ... build DataFrame ...
print(to_quarto_table(result, 'Caption text.', 'tbl-label'))
```

### Tables converted

| Table | File | Data source |
|:---|:---|:---|
| tbl-mechanism-main (M1--M4) | `results-exp010-mechanisms.qmd` | `stargazer_M{1..4}_*.csv` |
| tbl-mechanism-enhanced | `results-exp010-mechanisms.qmd` | `stargazer_column.csv` |
| tbl-mechanism-summary-exp010 (M7--M10) | `results-exp010-mechanisms.qmd` | `summary_m{7..10}*.csv` |
| tbl-subperiod-baseline | `results-exp011-subperiods.qmd` | `aggregated/stargazer_coef_model_1_baseline.csv` |
| tbl-crisis-model-fit | `results-exp009-crises.qmd` | `model_fit_comparison.csv` (extracted from MLflow) |
| tbl-full-m1-m4 | `appendix-E-regression-tables.qmd` | Same as main tables |
| tbl-full-m7-m10 | `appendix-E-regression-tables.qmd` | `stargazer_column.csv` |
| tbl-full-subperiod | `appendix-E-regression-tables.qmd` | `aggregated/stargazer_coef_model_1_baseline.csv` |

### Data corrections discovered

- **M7 FCR**: static table had HR = 0.944\*\*\*, CSV shows HR = 0.925\*\*\*
- **M8 fragmentation**: static table had HR = 0.826\*\*, CSV shows HR = 0.966 (n.s.)
- **exp_009 C-index**: static table had 0.637--0.639, MLflow shows 0.694--0.699
- **exp_009 AIC**: was `--` throughout, MLflow shows 9,698--9,715

### exp_009 model_fit_comparison.csv

The experiment script (`run_cox.py`) overwrites `stargazer_column.csv` on each model iteration, so only M6 (full interactions) survived on disk. Per-model AIC and C-index were extracted from MLflow:

```bash
source .venv/bin/activate && python -c "
import mlflow
mlflow.set_tracking_uri('sqlite:///mlflow.db')
experiment = mlflow.get_experiment_by_name('exp_009_crisis_interactions')
runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
latest = runs.groupby('tags.mlflow.runName').first().reset_index()
# ... save to model_fit_comparison.csv
"
```

Saved to `experiments/exp_009_crisis_interactions/model_fit_comparison.csv`.

---

## 4. Technical Issues and Solutions

### 4a. Pandas version conflict

**Problem**: `table_generator.py` needed pandas 3.0 for `Styler.to_typst()` (initially explored), but `graphdatascience` in the main `.venv` requires `pandas < 3.0`.

**Solution**: Created a separate virtual environment `.venv-quarto/` with pandas 3.0, Jupyter, and tabulate:

```bash
uv venv .venv-quarto
.venv-quarto/bin/pip install pandas jupyter tabulate
```

Registered as Jupyter kernel:

```bash
.venv-quarto/bin/python -m ipykernel install --user --name python3
```

### 4b. `Styler.to_typst()` does not integrate with Quarto

**Problem**: pandas 3.0's `Styler.to_typst()` generates raw Typst `#table(...)` markup, but Quarto's crossref system (Pandoc-based) cannot resolve `<tbl-label>` references in raw Typst blocks. Wrapping in `` ```{=typst} `` caused 'the character `#` is not valid in code' errors.

**Solution**: Abandoned `to_typst()` entirely. Used `df.to_markdown(index=False)` with Quarto's native caption syntax:

```python
def to_quarto_table(df, caption, label):
    md = df.to_markdown(index=False)
    return f'{md}\n\n: {caption} {{#{label}}}'
```

This integrates cleanly with Quarto's crossref system and Pandoc's Typst backend.

### 4c. Quarto finding wrong Python

**Problem**: Quarto resolved `jupyter: python3` to the system Python 3.14 (which lacked Jupyter), ignoring the `.venv-quarto` kernel.

**Solution**: Set the `QUARTO_PYTHON` environment variable:

```bash
QUARTO_PYTHON=/path/to/.venv-quarto/bin/python quarto render index.qmd
```

### 4d. Significance star escaping in markdown

**Problem**: `***` in table cells (e.g., `0.925***`) was parsed as bold+italic by Pandoc.

**Solution**: Regex escape in `fmt_cell()`:

```python
s = re.sub(r'\*+', lambda m: '\\*' * len(m.group(0)), s)
```

### 4e. Negative sign rendering

**Problem**: Minus signs in coefficient values rendered as hyphens in Typst.

**Solution**: Replace leading `-` with `$-$` (math-mode minus):

```python
if s.startswith('-'):
    s = '$-$' + s[1:]
```

### 4f. Citation-emdash parsing

**Problem**: `[@reinhart_ThisTimeDifferent_2009]---foreign-owned` caused Pandoc error: 'label reinhart_ThisTimeDifferent_2009---foreign-owned does not exist'.

**Solution**: Added spaces around the em-dash:

```markdown
[@reinhart_ThisTimeDifferent_2009] --- foreign-owned
```

### 4g. `_quarto.yml` validation error

**Problem**: Full Jupyter kernelspec YAML failed validation ('object is missing required property language').

**Solution**: Simplified to `jupyter: python3` and let Quarto resolve the kernel.

---

## 5. Formatting Conventions

- **Single quotation marks only** (no double quotes in prose)
- **British English** throughout (colour, behaviour, licence, organisation, etc.)
- **Extra newlines between list items** in `.qmd` files
- **Typst output format** (not LaTeX/PDF)
- **Em-dashes**: `---` with no surrounding spaces in prose, but spaces required adjacent to citation brackets

---

## 6. Files Created or Modified

### New files

| File | Purpose |
|:---|:---|
| `quarto/` (entire directory) | Quarto master document (19 .qmd files) |
| `quarto/tables/table_generator.py` | Shared formatting utilities for dynamic tables |
| `quarto/_quarto.yml` | Quarto project configuration (Typst format) |
| `quarto/references.bib` | BibLaTeX bibliography |
| `.venv-quarto/` | Separate venv with pandas 3.0 for Quarto rendering |
| `experiments/exp_009_crisis_interactions/model_fit_comparison.csv` | Per-model AIC/C-index extracted from MLflow |

### Key utility functions in `table_generator.py`

| Function | Purpose |
|:---|:---|
| `fmt_cell(val)` | Escape stars, math-mode minus signs for stargazer values |
| `fmt_hr(exp_coef, p_val)` | Format hazard ratio with escaped significance stars |
| `fmt_stat(var, val)` | Format model fit statistics (comma-separated integers, 3dp C-index, etc.) |
| `to_quarto_table(df, caption, label)` | `to_markdown()` + Quarto caption syntax with crossref label |
| `TABLE_LABELS` | Dict mapping variable names to short display labels |
