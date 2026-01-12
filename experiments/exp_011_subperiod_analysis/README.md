# exp_011: Subperiod Analysis (Structural Break Testing)

**Objective**: Test whether ownership effects vary systematically across three distinct crisis regimes by running exp_009 crisis interaction models on separate time windows.

**Research Question**: Do family/state/foreign ownership protective mechanisms exhibit structural breaks across crisis types (domestic banking vs. global financial vs. geopolitical)?

---

## Subperiods

| Period             | Years     | Crisis Included              | Regime Characteristics                            | Expected Findings                                      |
| ------------------ | --------- | ---------------------------- | ------------------------------------------------- | ------------------------------------------------------ |
| **Early Crisis**   | 2004-2007 | 2004 banking crisis          | Sodbiznesbank shock, early regulatory uncertainty | Family embeddedness strong, foreign effects weak       |
| **GFC & Recovery** | 2007-2013 | 2008 Global Financial Crisis | Lehman collapse, oil crash, Ignatyev era          | All ownership types protective (external shock)        |
| **Sanctions Era**  | 2013-2020 | 2014 Crimea sanctions        | Nabiullina cleanup, geopolitical stress           | Foreign reverses to liability, family/state strengthen |

**Hypothesis**: Ownership effects are **crisis-specific**, not universal—family protection strongest in domestic crises (2004, 2014), foreign ownership harmful only during geopolitical shocks (2014).

---

## Methodology

### Model Specifications (per subperiod)

Each subperiod runs 6 models identical to exp_009:

- **M1**: Baseline (no crisis effects)
- **M2**: Crisis dummy added
- **M3**: Family × Crisis interactions
- **M4**: State × Crisis interactions
- **M5**: Foreign × Crisis interactions
- **M6**: Full interactions (all ownership × crisis)

### Data

- **Source**: `QuarterlyWindowDataLoader` with 4Q lagged network metrics
- **Features**:
  - Ownership: `family_connection_ratio`, `family_ownership_pct`, `state_ownership_pct`, `foreign_ownership_total_pct`
  - Network: `rw_page_rank_4q_lag`, `rw_out_degree_4q_lag`
  - CAMEL: `camel_roa`, `camel_npl_ratio`, `camel_tier1_capital_ratio`
- **Temporal filtering**: Each subperiod restricts `df['year']` to its window

### Comparison Strategy

**Cross-subperiod coefficient comparison**:

1. Extract `family_connection_ratio` coefficient from M1 (baseline) for each period
2. Test: `β_2004-2007` vs `β_2007-2013` vs `β_2013-2020`
3. **Structural break test**: Chow test or coefficient difference z-test

**Interaction heterogeneity**:

- Compare `family × crisis_2004` (in 2004-2007 period)
- vs. `family × crisis_2008` (in 2007-2013 period)
- vs. `family × crisis_2014` (in 2013-2020 period)
- **Expected**: Interaction magnitudes differ (crisis-origin effects)

---

## Running the Experiment

### Sequential execution (all subperiods):

```bash
cd experiments/exp_011_subperiod_analysis
uv run python run_subperiods.py
```

This will:

1. Run 2004-2007 models (6 models → MLflow experiment `exp_011_subperiod_2004_2007`)
2. Run 2007-2013 models (6 models → MLflow experiment `exp_011_subperiod_2007_2013`)
3. Run 2013-2020 models (6 models → MLflow experiment `exp_011_subperiod_2013_2020`)
4. Total: 18 model runs

**Runtime estimate**: ~30-45 minutes (depending on sample sizes)

### Individual subperiod:

```bash
# Just 2004-2007
uv run python -c "
from run_subperiods import run_subperiod
run_subperiod('config_2004_2007.yaml')
"
```

---

## Expected Dataset Sizes

Based on exp_009 full dataset (143K obs, 1092 banks, 770 events):

| Period    | Est. Observations | Est. Banks | Est. Events | Crisis Obs     | Crisis % |
| --------- | ----------------- | ---------- | ----------- | -------------- | -------- |
| 2004-2007 | ~25-30K           | ~900-1000  | ~100-150    | ~2,500 (2004)  | ~10%     |
| 2007-2013 | ~50-60K           | ~800-900   | ~250-300    | ~12,000 (2008) | ~20%     |
| 2013-2020 | ~55-65K           | ~500-600   | ~350-400    | ~15,000 (2014) | ~23%     |

**Note**: Overlap years (2007, 2013) included in both adjacent periods to ensure crisis coverage completeness.

---

## Outputs

### Per subperiod:

- MLflow experiment with 6 runs (M1-M6)
- `interpretation_{model_key}.md` (effect rankings)
- `summary_{model_key}.csv` (coefficient tables)

### Aggregated (manual post-processing):

- `stargazer_subperiod_comparison.csv`: Side-by-side coefficients across periods
- `subperiod_analysis_writeup.md`: Interpretation of structural breaks

---

## Interpretation Framework

### Scenario A: Stable Coefficients

- `family_connection_ratio` has similar HR (~0.989) across all three periods
- **Conclusion**: Family effects are **universal**, not crisis-specific
- **Implication**: Family networks provide baseline protection regardless of shock origin

### Scenario B: Period-Specific Effects

- 2004-2007: `family_connection_ratio` HR = 0.975 (strong protection)
- 2007-2013: `family_connection_ratio` HR = 0.995 (weak protection)
- 2013-2020: `family_connection_ratio` HR = 0.980 (moderate protection)
- **Conclusion**: Domestic crises (2004, 2014) amplify family effects more than global shocks (2008)
- **Mechanism**: Family networks provide **local information** valuable during domestic uncertainty

### Scenario C: Foreign Ownership Reversal

- 2004-2007: `foreign_ownership_total_pct` HR = 0.95 (protective)
- 2007-2013: `foreign_ownership_total_pct` HR = 0.96 (protective)
- 2013-2020: `foreign_ownership_total_pct` HR = 1.05 (harmful)
- **Conclusion**: **Structural break in 2014**—sanctions reverse foreign ownership from asset to liability
- **Policy implication**: Crisis **origin** (geopolitical vs. financial) determines ownership effects

---

## Comparison to exp_009

| Aspect                  | exp_009 (Full Period)         | exp_011 (Subperiods)                 |
| ----------------------- | ----------------------------- | ------------------------------------ |
| **Timespan**            | 2004-2021 (pooled)            | Three separate windows               |
| **Crisis interactions** | All three crises in one model | One crisis per model (within-period) |
| **Advantage**           | Maximum statistical power     | Structural break detection           |
| **Limitation**          | Assumes constant coefficients | Smaller samples per period           |
| **Use case**            | Overall effects               | Period-specific mechanisms           |

**Complementarity**: exp_009 shows **average** effects; exp_011 reveals **heterogeneity** over time.

---

## Success Criteria

### Minimum Viable

✅ All 18 models converge (6 models × 3 periods)  
✅ At least one coefficient shows **significant difference** across periods (z-test p<0.05)  
✅ Crisis coverage adequate in each period (>5% observations in crisis dummy)

### Strong Result

✅ **Family effect stable** across periods (supports universal mechanism)  
✅ **Foreign effect reverses** post-2013 (supports geopolitical liability hypothesis)  
✅ **State effect strongest** in 2013-2020 (supports domestic consolidation hypothesis)

### Publishable

✅ Formal Chow test confirms structural break at 2013 boundary  
✅ Coefficient confidence intervals **non-overlapping** across key periods  
✅ Crisis interaction magnitudes align with theoretical predictions (domestic > global for family)

---

## Next Steps After exp_011

### If Structural Breaks Confirmed

1. **Update exp_009 writeup**: Add subperiod analysis section showing coefficient evolution
2. **Theoretical contribution**: Ownership effects are **regime-dependent**, not static
3. **Policy brief**: Different crisis origins require **different** regulatory responses

### If No Structural Breaks

1. **Validate exp_009 pooled results**: Constant coefficients justify pooling strategy
2. **Focus on crisis interactions**: Period-specific effects captured by interaction terms, not separate models
3. **Alternative: Governor fixed effects**: Test whether Ignatyev vs. Nabiullina leadership matters more than time periods

---

## File Structure

```
exp_011_subperiod_analysis/
├── README.md                    # This file
├── config_2004_2007.yaml       # Early crisis period config
├── config_2007_2013.yaml       # GFC & recovery period config
├── config_2013_2020.yaml       # Sanctions era config
├── run_subperiods.py           # Master execution script
├── config_cox.yaml             # (Legacy, unused - kept from exp_009 copy)
└── run_cox.py                  # (Legacy, unused - kept from exp_009 copy)
```

**Note**: `config_cox.yaml` and `run_cox.py` are remnants from copying exp_009; they are replaced by the subperiod-specific configs and `run_subperiods.py`.

---

## Reuse from Previous Experiments

- ✅ **exp_007**: `QuarterlyWindowDataLoader` for 4Q lagged network
- ✅ **exp_009**: Model specifications (M1-M6 structure), crisis interaction logic
- ✅ **exp_008**: Community aggregation (if stratified Cox needed)

**Leverage**: Zero new data generation required—reuses existing quarterly snapshots from exp_007/009.
