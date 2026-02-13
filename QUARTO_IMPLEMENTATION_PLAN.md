# Quarto Master Document Implementation Plan
**Date**: 2026-02-12
**Target**: Modular academic paper addressing reviewer feedback
**Format**: Typst (via Quarto)
**Language**: British English

---

## 1. File Structure

```
./quarto/
├── _quarto.yml                          # Project configuration (Typst, bibliography, formatting)
├── index.qmd                            # Master document (includes all sections)
├── _extensions/                         # Quarto extensions (if needed for Typst)
│
├── sections/                            # Main paper sections
│   ├── 01-introduction.qmd             # Introduction + motivation
│   ├── 02-literature-review.qmd        # Three-domain literature review
│   ├── 03-institutional-context.qmd    # NEW: Addresses "weak institutions" feedback
│   ├── 04-hypotheses.qmd               # Research questions & hypotheses
│   ├── 05-data.qmd                     # Data sources, Neo4j methodology, descriptives
│   ├── 06-methods.qmd                  # Cox models, measurement, econometric strategy
│   ├── 07-results.qmd                  # Results overview + section includes
│   ├── 08-discussion.qmd               # Interpretation, policy implications
│   └── 09-conclusion.qmd               # Summary and future research
│
├── results/                             # Modular results by experiment (included in 07-results.qmd)
│   ├── results-exp010-mechanisms.qmd   # Main: TCE mechanisms (2004-2020)
│   ├── results-exp011-subperiods.qmd   # Main: Temporal heterogeneity
│   ├── results-exp009-crises.qmd       # Main: Crisis interactions
│   └── results-exp012-governors.qmd    # Main: Regime effects
│
├── appendices/                          # Supplementary material
│   ├── appendix-A-literature-tables.qmd # Lit review summary tables
│   ├── appendix-B-metrics.qmd          # Variable definitions (from family_survival_revised.md)
│   ├── appendix-C-robustness.qmd       # exp_008 (community), exp_013 (endogeneity), exp_007 (lags)
│   ├── appendix-D-baseline-models.qmd  # exp_002, exp_003 baseline cross-sectional
│   └── appendix-E-regression-tables.qmd # Full regression output tables
│
├── figures/                             # Figures (referenced or generated)
│   └── README.md                        # Documentation of figure sources
│
├── tables/                              # Table generation scripts
│   ├── table_generator.py              # Python utilities for reading CSVs → formatted tables
│   └── README.md                        # Documentation of table sources
│
└── references.bib                       # Bibliography (preserves citation keys from original)
```

---

## 2. Section-by-Section Outline

### 2.1 Introduction (`01-introduction.qmd`)

**Key Content**:
- Russian banking contraction: 1,525 banks (1996) → 309 (2025)
- Sodbiznesbank 2004 crisis as watershed moment (murder of shadow owner, physical resistance to CBR)
- Research gap: existing literature ignores family kinship networks
- **Address feedback**: Why study family networks? Not just "interesting" but theoretically necessary given institutional environment

**Reviewer Feedback Addressed**:
- **drfilich comment on "coordination mechanisms"**: Clarify coordination is about **resource pooling, information sharing, and mutual support** within family networks, not coordination with state
- **Main motivation clarity**: Frame as filling empirical gap (no prior data on family networks in Russian banking) + theoretical puzzle (why do family networks persist despite agency costs?)

**Hypotheses Preview**:
- H1: Family network density → lower hazard (substitution function)
- H2: Context-dependent effects (protective in 2008, liability in 2014+ regulatory targeting)

**Length**: ~2,000 words

---

### 2.2 Literature Review (`02-literature-review.qmd`)

**Structure** (three interconnected domains):

1. **Russian Banking Failures** (based on existing Section 1.1 in family_survival_revised.md):
   - CAMEL determinants
   - Ownership structures (foreign protective, state mixed)
   - Political economy (electoral cycles, corruption)
   - Factional networks (Soldatkin 2020 media vs ownership factions)

2. **Family Ownership & Business Groups**:
   - Socioemotional Wealth (SEW) framework
   - Institutional voids literature (Khanna & Palepu)
   - Family networks as governance mechanisms
   - Generational dynamics

3. **Network Effects on Survival**:
   - Network centrality and crisis recovery
   - Community structure in ownership networks
   - Information advantages of kinship ties

**Reviewer Feedback Addressed**:
- **drfilich: "why has prior literature failed to incorporate family networks?"**: Add explicit paragraph on data constraints (family relationships not in regulatory data, requires manual coding from CBR ownership disclosures)

**Length**: ~4,000 words

---

### 2.3 Institutional Context (`03-institutional-context.qmd`) **[NEW SECTION]**

**Purpose**: Directly address drfilich's core concerns about "weak institutions" and "substitution vs interference"

**Content**:

#### 3.1 Defining Weak Formal Institutions in Russia
**Concrete examples** (not abstract claims):
- **Sodbiznesbank 2004**: Murder of shadow owner Alexander Slesarev, physical barricades preventing CBR access, "suspension of law" (Ledeneva 1998)
- **Selective enforcement**: 80% banks met CBR prudential ratios yet failed (Barajas et al. 2023) → compliance insufficient for survival
- **Electoral cycle manipulation**: 2-3× lower failure probability pre-elections (Fungáčová & Poghosyan 2022) → regulatory forbearance politicised
- **Otkritie-Trust 2017**: State "sanitisation" targeted systemically important family-controlled groups, not just failing institutions → regulatory intervention strategic, not rule-based

**Definition**: Weak institutions = inability of formal rules to credibly commit to impartial enforcement, leading to:
1. Actors investing in relationship-based protection
2. Regulatory outcomes determined by political connections, not compliance
3. Formal compliance necessary but not sufficient for survival

#### 3.2 Ledeneva's Substitution vs Interference Framework
**Theoretical foundation**:
- **Substitution**: Informal mechanisms **replace** absent or ineffective formal institutions (e.g., family ties provide liquidity when interbank markets freeze)
- **Interference**: Informal mechanisms **subvert** formal institutions' intended purpose (e.g., ownership fragmentation to evade transfer pricing rules)

**Empirical Mapping**:

| Period          | Regime         | Dominant Function  | Mechanism                                                                 | Evidence (from experiments)                       |
| --------------- | -------------- | ------------------ | ------------------------------------------------------------------------- | ------------------------------------------------- |
| **2004-2007**   | Ignatyev early | Substitution       | Family networks provide trust, liquidity backstops when formal weak       | exp_011: FCR protective, no crisis interaction    |
| **2008**        | GFC            | Substitution       | Internal capital markets buffer external shock (foreign markets frozen)   | exp_009: Family×2008 protective (+26.6% survival) |
| **2013-2020**   | Nabiullina     | Interference       | Ownership fragmentation evades regulatory consolidation/transfer pricing  | exp_010: Fragmentation HR=0.882 (strongest)       |
| **2014-2017**   | Sanctions      | Mixed/Target risk  | High centrality attracts regulatory targeting (Otkritie-Trust)            | exp_009: Foreign×2014 harmful; centrality liability|

**Reviewer Feedback Addressed**:
- **drfilich: "why are formal institutions seen as failing?"**: This section provides explicit definition + empirical examples, not assertion
- **drfilich: "why talk about substitution vs interference?"**: Shows this is not ad-hoc interpretation but application of Ledeneva's established framework to survival patterns
- **drfilich: "evidence that state regulators lean on informal mechanisms?"**: Reframe claim - not that state "leans on" families, but that families **substitute** when state cannot credibly protect property rights (2008) vs **interfere** when state tightens rules (2013+)

**Length**: ~2,500 words

---

### 2.4 Hypotheses (`04-hypotheses.qmd`)

**Formal Hypotheses** (refined from family_survival_revised.md):

**H1: Direct Effects (Unconditional Protection)**
- H1a: Higher family connection ratio → lower hazard
- H1b: Mechanism heterogeneity (Political, Tax, Capital) → all significant but Tax strongest

**H2: Context-Dependent Effects (Crisis Interactions)**
- H2a: Family networks **more** protective during economic crises (2008 GFC)
- H2b: Foreign ownership **protective** during economic crises but **harmful** during geopolitical crises (2014 sanctions)
- H2c: Network centrality **protective** baseline but **liability** during regulatory targeting (2014-2017 cleanup)

**H3: Temporal Stability (Structural Breaks)**
- H3a: Ownership effects **vary** across periods (Ignatyev vs Nabiullina regimes)
- H3b: Substitution dominant pre-2013, Interference post-2013

**Length**: ~1,500 words

---

### 2.5 Data (`05-data.qmd`)

**Key Content**:
- **Neo4j Graph Database**: Ownership layers, family relationships (FAMILY edges), network metrics
- **CBR Data**: CAMEL ratios (2004-2020), bank registry, license revocation dates
- **Network Construction**: 44 quarterly snapshots (2004-2020), 4-quarter lag for endogeneity
- **Sample**: ~140,000 bank-quarter observations, 2,418 unique banks, 1,117 failure events

**Descriptive Statistics**:
- Table 1: Summary statistics (from aggregated CSVs)
- Table 2: Correlation matrix (ownership variables vs CAMEL)
- Figure 1: Bank failures over time (existing figure from memory-bank/papers)
- Figure 2: Family ownership distribution (to be generated from Neo4j summary stats)

**Measurement**:
- `family_connection_ratio`: Total family edges / direct owners (structural, not network-derived)
- `stake_fragmentation_index`: 1 - Σ(shares²) (ownership dispersion)
- `group_total_capital`, `group_sector_count`: Internal capital market proxies

**Length**: ~3,000 words

---

### 2.6 Methods (`06-methods.qmd`)

**Econometric Strategy**:

1. **Cox Proportional Hazards** (time-varying covariates):
   - Baseline specification
   - Crisis interaction models
   - Stratified models (region, sector, community)

2. **Model Specifications**:
   - M1: Baseline (family + CAMEL + ownership)
   - M2-M4: Individual mechanisms (Political, Tax, Capital)
   - M5-M6: Crisis interactions
   - M7-M10: Enhanced mechanisms (H3+, stratification)

3. **Robustness Checks**:
   - Lagged network metrics (4Q lag, exp_007)
   - Community fixed effects (exp_008)
   - Reverse causality tests (exp_013)
   - Subperiod analysis (exp_011)

**Length**: ~2,500 words

---

### 2.7 Results (`07-results.qmd`) **[MODULAR INCLUDES]**

**Structure**:
```markdown
## 7. Results

### 7.1 Overview
[Brief summary of main findings]

### 7.2 Transaction Cost Mechanisms (2004-2020)
{{< include results/results-exp010-mechanisms.qmd >}}

### 7.3 Temporal Heterogeneity and Structural Breaks
{{< include results/results-exp011-subperiods.qmd >}}

### 7.4 Crisis Interactions
{{< include results/results-exp009-crises.qmd >}}

### 7.5 Regulatory Regime Effects
{{< include results/results-exp012-governors.qmd >}}

### 7.6 Summary of Findings
[Synthesis table comparing key coefficients across experiments]
```

---

#### Results Module 1: `results-exp010-mechanisms.qmd`

**Content**:
- **Table 3**: Main regression results (M1-M6) from exp_010
  - Source: `experiments/exp_010_mechanism_testing/summary_*.csv`
  - Format: Hazard ratios, standard errors, significance stars
  - Columns: M1 (Political), M2 (Tax), M3 (Capital), M4 (Full), M5 (EPU), M6 (Interactions)

- **Table 4**: Enhanced mechanisms (M7-M10)
  - M7: H3+ (capital + diversification)
  - M8: Sector stratification
  - M9: Community stratification (lowest AIC!)
  - M10: Deep proxies (tax, vehicles)

- **Figure 3**: Survival comparison (banks vs group companies)
  - Source: `experiments/exp_010_mechanism_testing/survival_comparison.png`

- **Key Findings**:
  - All 3 mechanisms significant (p<0.01)
  - Stake fragmentation strongest (HR=0.882, -11.8% hazard)
  - Community stratification best fit (AIC=6952.4 vs ~9700 for others)
  - Group capital, sector diversification, tax proxies all protective

**Length**: ~2,000 words + 2 tables + 1 figure

---

#### Results Module 2: `results-exp011-subperiods.qmd`

**Content**:
- **Table 5**: Coefficient evolution across periods
  - Source: `experiments/exp_011_subperiod_analysis/output/{period}/summary_*.csv`
  - Rows: Key variables (FCR, stake_frag, foreign, state)
  - Columns: 2004-2007 | 2007-2013 | 2013-2020
  - Shows structural breaks

- **Key Findings**:
  - FCR protective **stable** across periods (H3a partially rejected)
  - Foreign ownership **reversal**: protective 2007-2013 (GFC), harmful 2013-2020 (sanctions)
  - Fragmentation effect **stronger** in later period (regulatory evasion motive)

**Length**: ~1,500 words + 1 table

---

#### Results Module 3: `results-exp009-crises.qmd`

**Content**:
- **Table 6**: Crisis interaction models
  - Source: exp_009 outputs (via writeup crisis_interactions_writeup.md)
  - Specifications: M1 (Baseline), M2 (Crisis dummies), M3-M5 (Individual interactions), M6 (Full)

- **Key Findings**:
  - Family × 2008: **+26.6% survival boost** (substitution during GFC)
  - Foreign × 2008: Protective (access to parent bank capital)
  - Foreign × 2014: **-28.1% survival** (sanctions liability)
  - State ownership: Low variance (too few state banks)

**Length**: ~1,500 words + 1 table

---

#### Results Module 4: `results-exp012-governors.qmd`

**Content**:
- **Table 7**: Governor regime effects
  - Source: memory-bank/writeups/governor_regimes.md
  - Compare Ignatyev (2004-2013) vs Nabiullina (2013-2020) eras

- **Key Findings**:
  - Nabiullina era: Higher baseline hazard (cleanup campaign)
  - Ownership fragmentation **more protective** under Nabiullina (evasion)
  - Network centrality **liability** under Nabiullina (targeting)

**Length**: ~1,200 words + 1 table

---

### 2.8 Discussion (`08-discussion.qmd`)

**Structure**:

#### 8.1 The Family Connection Paradox Resolved
- Why do family networks protect despite agency costs?
- **Answer**: Substitution for weak institutions (internal capital markets, trust, information)
- Evidence: All 3 TCE mechanisms significant, strongest effects during institutional voids

#### 8.2 The Foreign Ownership Reversal
- Why protective 2008, harmful 2014?
- **Answer**: Nature of crisis matters
  - 2008: Economic crisis → foreign parent support valuable
  - 2014: Geopolitical crisis → foreign connections liability (sanctions, capital flight)

#### 8.3 Substitution vs Interference Across Time
- Empirical support for Ledeneva framework:
  - 2008: Substitution (family × crisis protective)
  - 2013+: Interference (fragmentation for regulatory evasion)
  - 2014-2017: Targeting risk (high centrality liability)

#### 8.4 Policy Implications
- Regulatory consolidation (Nabiullina) reduced sector size but may have incentivised evasion via fragmentation
- Network-based supervision needed (targeting systemically important family groups, not just individual banks)

**Reviewer Feedback Addressed**:
- **drfilich: "How does Alex know state regulators lean on informal mechanisms?"**: REFRAME - Not that state "leans on", but that **families substitute when state weak, interfere when state tightens**
- **drfilich: "Evidence for substitution vs interference?"**: This section provides empirical mapping (crisis interactions + subperiod analysis)

**Length**: ~3,500 words

---

### 2.9 Conclusion (`09-conclusion.qmd`)

**Key Content**:
- Summary of findings
- Contributions: (1) First empirical evidence on family networks in Russian banking, (2) Application of Ledeneva framework to survival analysis
- Limitations: (1) Disclosure mandate confound (exp_013), (2) Network endogeneity (addressed via lags), (3) Measurement (family_connection_ratio structural, not network-derived)
- Future research: (1) Micro-level family formation dynamics, (2) International comparison

**Length**: ~1,500 words

---

## 3. Appendices

### Appendix A: Literature Tables (`appendix-A-literature-tables.qmd`)
- Preserve existing Table A1-A3 from family_survival_revised.md
- Russian banking determinants
- Family ownership studies
- Effect magnitudes

### Appendix B: Metrics (`appendix-B-metrics.qmd`)
- Preserve existing metrics table from family_survival_revised.md
- Mathematical definitions of all variables
- Network centrality formulas

### Appendix C: Robustness Checks (`appendix-C-robustness.qmd`)

**C.1 Community Fixed Effects (exp_008)**
- Louvain community detection
- Stratified Cox model
- Shows network effects partially confounded with community structure

**C.2 Reverse Causality (exp_013)**
- OLS panel regressions (biennial 2012-2020)
- Tests whether survival → FCR (reverse causality)
- **Critical finding**: Disclosure mandate confound (FCR increase post-2013 may reflect regulatory reporting, not tie formation)

**C.3 Lagged Network Effects (exp_007)**
- 4-quarter lagged network metrics
- Controls for endogeneity (FCR may reflect ex-post restructuring)
- Family connection ratio temporal lag (still protective with lag)

### Appendix D: Baseline Models (`appendix-D-baseline-models.qmd`)
- exp_002, exp_003: Cross-sectional logistic and basic Cox models
- Foundation before time-varying specifications

### Appendix E: Full Regression Tables (`appendix-E-regression-tables.qmd`)
- Complete coefficient tables for all experiments
- Source: aggregated stargazer CSVs

---

## 4. Table & Figure Plan

### Main Tables (in results sections)

| Table | Title                                                         | Source CSVs                                                                      | Generator                 |
| ----- | ------------------------------------------------------------- | -------------------------------------------------------------------------------- | ------------------------- |
| 1     | Summary Statistics                                            | Aggregated from exp_010, exp_011 outputs                                         | `table_generator.py`      |
| 2     | Correlation Matrix                                            | Computed from merged data (or pre-computed CSV)                                  | Python code chunk         |
| 3     | Mechanism Testing (M1-M6)                                     | `exp_010_mechanism_testing/summary_M*.csv`                                       | Python stargazer reader   |
| 4     | Enhanced Mechanisms (M7-M10)                                  | `exp_010_mechanism_testing/summary_m*.csv`                                       | Python stargazer reader   |
| 5     | Subperiod Coefficient Evolution                               | `exp_011_subperiod_analysis/output/{2004-2007,2007-2013,2013-2020}/summary_*.csv` | Python CSV aggregator     |
| 6     | Crisis Interactions                                           | Extracted from writeup (or exp_009 output if CSVs available)                     | Manual/Python hybrid      |
| 7     | Governor Regime Effects                                       | From writeup governor_regimes.md                                                 | Manual table construction |
| A1-E* | Appendix tables                                               | Various (preserve from family_survival_revised.md + new robustness CSVs)         | Python + manual           |

### Main Figures

| Figure | Title                                      | Source                                                | Type                  |
| ------ | ------------------------------------------ | ----------------------------------------------------- | --------------------- |
| 1      | Bank Failures Cumulative (1989-2023)       | `memory-bank/papers/figures/bank_closures_cumulative` | Existing (reference)  |
| 2      | Family Ownership Distribution              | To be generated from Neo4j summary stats or CSV       | Python matplotlib/seaborn |
| 3      | Survival Comparison (Banks vs Companies)   | `exp_010_mechanism_testing/survival_comparison.png`   | Existing (reference)  |
| 4      | Coefficient Evolution Across Subperiods    | Generated from Table 5 data                           | Python matplotlib     |
| 5      | Crisis Interaction Effects (Forest Plot?)  | Generated from Table 6 data                           | Python matplotlib     |

---

## 5. _quarto.yml Configuration

```yaml
project:
  type: book
  output-dir: _output

book:
  title: "Banking on Family: Why Family Ownership Matters for the Survival of Russian Banks"
  author: "Alexander Soldatkin"
  date: today
  chapters:
    - index.qmd
    - sections/01-introduction.qmd
    - sections/02-literature-review.qmd
    - sections/03-institutional-context.qmd
    - sections/04-hypotheses.qmd
    - sections/05-data.qmd
    - sections/06-methods.qmd
    - sections/07-results.qmd
    - sections/08-discussion.qmd
    - sections/09-conclusion.qmd
    - appendices/appendix-A-literature-tables.qmd
    - appendices/appendix-B-metrics.qmd
    - appendices/appendix-C-robustness.qmd
    - appendices/appendix-D-baseline-models.qmd
    - appendices/appendix-E-regression-tables.qmd

bibliography: references.bib
csl: apa.csl  # Or cambridge style if preferred

format:
  typst:
    toc: true
    toc-depth: 3
    number-sections: true
    number-depth: 4
    columns: 1
    margin:
      x: 2.5cm
      y: 2.5cm
    papersize: a4
    mainfont: "Linux Libertine"  # Or another suitable font
    # Custom Typst template settings as needed

execute:
  echo: false
  warning: false
  message: false
  cache: false

jupyter: python3
```

---

## 6. Python Table Generation Utilities

**File**: `tables/table_generator.py`

**Functions**:
1. `read_stargazer_csv(path)` → DataFrame with coefficient, SE, significance
2. `format_regression_table(models, model_names)` → Formatted markdown/Typst table
3. `aggregate_subperiod_results(period_paths)` → Combined table across periods
4. `create_summary_stats(data)` → Descriptive statistics table
5. `hazard_ratio_to_percent(hr)` → Convert HR to % change in hazard

**Dependencies**:
- pandas, numpy
- pathlib (for relative path handling)
- No statsmodels or lifelines (just table formatting, not model fitting)

---

## 7. Addressing Reviewer Feedback: Mapping

| drfilich Comment                                                                             | Section Addressing It                | How Addressed                                                                                                                  |
| -------------------------------------------------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| "Why focus on institutional uncertainty as driver?"                                          | 03-institutional-context.qmd         | Define "weak institutions" with concrete examples (Sodbiznesbank, selective enforcement), not abstract assertion              |
| "Why are formal institutions seen as failing?"                                               | 03-institutional-context.qmd         | Evidence: 80% banks meet CBR ratios yet fail, electoral cycle manipulation, Otkritie-Trust targeting                          |
| "Coordination mechanisms - coordination with whom?"                                          | 01-introduction.qmd, 04-hypotheses   | Clarify: coordination **within family network** (resource pooling, information), not coordination with state                  |
| "Evidence for substitution vs interference distinction?"                                     | 03-institutional-context.qmd (Table) | Empirical mapping: 2008 crisis = substitution (protective), 2013+ = interference (fragmentation for evasion)                  |
| "How does Alex know state regulators lean on informal mechanisms during crises?"             | 08-discussion.qmd                    | REFRAME: Not that state "leans on" families, but families **substitute** when state weak (2008) vs **interfere** when tightens |
| "Coefficients on what???" (re: regional corruption)                                          | 02-literature-review.qmd             | Clarify dependent variable in literature review discussion                                                                     |
| "Not clear why ownership effects provide foundation for network mechanisms"                  | 02-literature-review.qmd             | Explicit bridge paragraph: ownership creates control rights → family ownership creates kinship-based governance networks      |
| "Unclear post-transition period definition"                                                  | Throughout                           | Use specific years (e.g., "post-2000 period") instead of vague "post-transition"                                              |
| "Statement taken for granted re: informal power structures"                                  | 03-institutional-context.qmd         | Provide theoretical foundation (Ledeneva 1998) + empirical examples before asserting importance                               |

---

## 8. Word Count Targets

| Section                    | Target Words |
| -------------------------- | ------------ |
| Introduction               | 2,000        |
| Literature Review          | 4,000        |
| Institutional Context      | 2,500        |
| Hypotheses                 | 1,500        |
| Data                       | 3,000        |
| Methods                    | 2,500        |
| Results (total)            | 7,200        |
| - exp_010                  | 2,000        |
| - exp_011                  | 1,500        |
| - exp_009                  | 1,500        |
| - exp_012                  | 1,200        |
| - Summary                  | 1,000        |
| Discussion                 | 3,500        |
| Conclusion                 | 1,500        |
| **Main Text Total**        | **~27,700**  |
| Appendices                 | 5,000        |
| **Grand Total**            | **~32,700**  |

---

## 9. Key Differences from family_survival_revised.md

| Original Document                                      | New Quarto Structure                                                   | Rationale                                                  |
| ------------------------------------------------------ | ---------------------------------------------------------------------- | ---------------------------------------------------------- |
| Single 257KB file                                      | Modular: 9 main sections + 4 results modules + 5 appendices            | Easier to iterate, clearer organisation                    |
| PDF via lualatex                                       | **Typst** via Quarto                                                   | User requirement                                           |
| Live Neo4j queries in Python chunks                    | No Neo4j, tables from pre-computed CSVs                                | Reproducibility without database dependency                |
| Abstract mention of "institutional uncertainty"        | Dedicated **Institutional Context** section (03) with concrete examples | Addresses drfilich feedback on defining "weak institutions" |
| Substitution/interference mentioned but not developed  | Empirical mapping table (crisis × period → function)                   | Addresses feedback on evidence for distinction             |
| Reviewer comments embedded in text                     | Feedback addressed **organically** (no explicit response section)      | Cleaner presentation                                       |
| Results organised by model type                        | Results organised by **experiment** (exp_010, exp_011, etc.)           | Clearer thematic structure                                 |
| Limited robustness discussion                          | Dedicated Appendix C with 3 robustness experiments                     | Addresses endogeneity/confounding concerns                 |

---

## 10. Implementation Steps (for next phase)

1. ✅ Create `./quarto/` directory structure
2. ✅ Write `_quarto.yml` configuration file
3. ✅ Create `index.qmd` master document
4. ✅ Draft Section 03 (Institutional Context) - **Priority** (addresses main feedback)
5. ✅ Build `table_generator.py` utilities
6. ✅ Create results modules (exp_010, exp_011, exp_009, exp_012)
7. ✅ Generate main tables (Tables 3-7) from CSVs
8. ⏳ Draft remaining main sections (01, 02, 04-09)
9. ⏳ Create appendices (A-E)
10. ⏳ Test Typst compilation (`quarto render`)
11. ⏳ Iterate based on output review

---

## 11. Open Questions for Finalisation

**For immediate resolution**:
1. ✅ **Bibliography**: User will handle later (preserve citation keys only)
2. ✅ **Typst template**: Use default Quarto Typst or custom template? → Default for now
3. **Figure generation**: Should Figure 2 (family ownership distribution) be generated from data, or skip if not already available? → Generate if summary stats CSV exists
4. **Appendix E scope**: Include **all** experiment regressions or just main 4? → Main 4 detailed, others summarised

**For later iterations**:
- CSL citation style (APA vs Cambridge)
- Figure aesthetics (colour scheme, fonts)
- Table formatting preferences (landscape vs portrait for wide tables)

---

## 12. Success Criteria

**Document is complete when**:
✅ All 9 main sections written (British English, academic tone)
✅ All 4 results modules complete with tables from CSVs
✅ Dedicated Institutional Context section addresses reviewer feedback
✅ Substitution vs Interference empirically mapped (Table in Section 03)
✅ Appendices C complete (robustness: exp_008, exp_013, exp_007)
✅ Bibliography preserves original citation keys
✅ Typst compilation successful (`quarto render` produces PDF)
✅ All tables regenerated from CSV sources (no manual entry)
✅ Figure references use relative paths
✅ Word count ~27,000-30,000 (main text)

---

**Plan Status**: Ready for implementation pending user approval
**Next Step**: Create directory structure and begin drafting Section 03 (Institutional Context) as highest priority
