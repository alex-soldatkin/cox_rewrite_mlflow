Implementation Plan: exp_007 Lagged Network Effects
Experiment Goal: Address endogeneity of network metrics by using lagged network indicators to predict survival, establishing temporal precedence whilst controlling for autocorrelation.

Research Question: Do network positions at t-4 quarters causally predict bank failure at time t, or are network effects merely contemporaneous correlations?

1. Endogeneity Problem Statement
1.1 Sources of Endogeneity in Current Models (exp_004-006)
Simultaneity/Reverse Causality:

Failing banks may lose network connections before death (reverse causation)
Successful banks attract more ownership stakes (selection bias)
Fire sales force healthy banks to acquire distressed banks → artificially high out-degree
Omitted Variables:

Unobserved management quality affects both network position and survival
Regulatory treatment influences both networking strategy and failure risk
Sectoral shocks simultaneously impact network formation and survival
Measurement Error:

Community-level confounding (addressed in exp_006 but endogeneity remains)
Network metrics measured contemporaneously with survival status
1.2 Why Lagging Helps (and Limitations)
✅ Advantages:

Temporal precedence: Network position at t-4 predates survival outcome at t → rules out reverse causality within lag window
Anticipatory effects: If network metrics are truly protective, past positions should predict future survival (not just current)
Instrument-like properties: Lagged networks less correlated with current unobservables (though not a formal instrument)
⚠️ Limitations:

Autocorrelation: Network positions highly persistent → lagged values still correlated with current values → residual endogeneity
Long-run confounding: Omitted variables affecting both past network and current survival (e.g., stable management quality)
Optimal lag choice: Too short (t-1) = high autocorrelation; too long (t-8) = weak predictive power
2. Data Availability Assessment
2.1 Current Data Structure
Accounting Data (CBR):

Frequency: Monthly (median 31 days between observations)
Coverage: 2004-02-01 to 2025-05-01 (21 years, 240 unique dates)
Granularity: 82 unique quarters (Q1 2004 - Q1 2025)
Observations: ~2,000-2,900 banks per quarter (declining over time)
Network Data (Neo4j + Rolling Windows):

Current setup: 2-year non-overlapping windows (2014-2016, 2016-2018, 2018-2020)
Problem: Too coarse for quarterly lags (cannot lag by 1 quarter within 2-year window)
Available metrics: page_rank, in_degree, out_degree, community_louvain, wcc
Missing: betweenness, closeness, eigenvector (not pre-computed)
2.2 Data Requirements for exp_007
Minimum Requirement:

Quarterly network snapshots (or at least semi-annual) to enable t-4 quarter lag
Options:

Option A: Generate Quarterly Network Snapshots (RECOMMENDED)
Approach: Re-run rolling window pipeline with quarterly windows

// rolling_windows/pipeline_quarterly.py
window_configs = [
    {"start": "2014-01-01", "end": "2014-03-31"},  // Q1 2014
    {"start": "2014-04-01", "end": "2014-06-30"},  // Q2 2014
    ...
    {"start": "2020-10-01", "end": "2020-12-31"},  // Q4 2020
]
Pros:

✅ Precise temporal alignment with accounting data
✅ Enables flexible lag specifications (1, 2, 4, 8 quarters)
✅ Captures network dynamics at policy-relevant frequency
Cons:

❌ Computationally expensive (~28 quarterly windows for 2014-2020)
❌ Small network samples per quarter (may lose rare connections)
❌ Requires ~2-3 hours of Neo4j computation
Option B: Interpolate from 2-Year Windows
Approach: Assume network metrics constant within 2-year windows, use window midpoint as timestamp

Pros:

✅ No additional data generation required
✅ Fast implementation
Cons:

❌ Measurement error: Assumes zero within-window variation
❌ Cannot lag within same 2-year window (only across windows)
❌ Effective lag = 2 years minimum (too long for causal inference)
Verdict: Option A required for meaningful lagged analysis. Option B insufficient.

Option C: Use Static Network with Time-Decay Weighting
Approach: Compute static network metrics but weight edges by recency

MATCH (n:Bank)-[r:OWNERSHIP]->(m:Bank)
WHERE r.end_date >= date('2014-01-01')
WITH n, m, r,
     duration.between(r.start_date, date('2015-01-01')).days AS days_active
WHERE days_active > 0
RETURN ...
Pros:

✅ Intermediate complexity
✅ Captures temporal dynamics without full quarterly snapshots
Cons:

❌ Still requires custom pipeline development
❌ Less interpretable than true quarterly snapshots
❌ Ad-hoc temporal weighting choice
3. Proposed Experimental Design
3.1 Experiment Structure: exp_007_lagged_network
Core Hypothesis: Network metrics at t-4 quarters predict survival at t, controlling for:

Lagged CAMEL ratios (t-1, t-4)
Community fixed effects (from exp_006)
Autocorrelation in network metrics
3.2 Model Specifications
Model 1: Baseline Contemporaneous (Reproduction of exp_005)
survival_t ~ camel_t + network_t + family_t + foreign_t + controls_t
Purpose: Establish baseline for comparison.

Model 2: Simple Lagged Network (4-Quarter Lag)
survival_t ~ camel_t + network_{t-4} + family_t + foreign_t + controls_t
Test: Do lagged network metrics retain predictive power?

Expected: Weaker coefficients if endogeneity was driving M1 results.

Model 3: Lagged Network + Contemporaneous Controls
survival_t ~ camel_t + network_{t-4} + family_t + foreign_t + controls_t
Improvement: Control for current fundamentals whilst using lagged network.

Logic: If network_{t-4} remains significant after controlling for camel_t, suggests network has independent predictive power beyond current fundamentals.

Model 4: Lagged Network + Lagged Controls (Full Lag)
survival_t ~ camel_{t-4} + network_{t-4} + family_{t-4} + foreign_{t-4} + controls_{t-4}
Purpose: Pure prediction model using only information available 4 quarters ago.

Use Case: Regulatory early warning systems.

Model 5: Autocorrelation-Adjusted (Arellano-Bond Style)
survival_t ~ camel_t + (network_t - network_{t-4}) + network_{t-4} + family_t + ...
Innovation: Decompose network effect into:

Level effect: network_{t-4} (pre-determined)
Change effect: Δnetwork_{t-4 to t} (potentially endogenous but captures dynamics)
Justification: If network changes are driven by survival prospects, controlling for past level isolates causal delta effect.

Model 6: Community-Stratified Lagged (Combining exp_006 + exp_007)
CoxTimeVaryingFitter(strata=['community_collapsed']).fit(
    survival_t ~ camel_t + network_{t-4} + ...
)
Purpose: Control both community confounding and endogeneity.

Expected: Cleanest causal estimate (though potentially weak due to double-adjustment).

3.3 Lag Specifications to Test
Primary Lag: t-4 quarters (1 year)

Rationale: Policy-relevant horizon for regulatory intervention
Autocorrelation: Balances persistence vs. endogeneity
Robustness Checks:

Lag	Quarters	Rationale
t-1	1Q	Test immediate predictive power (high autocorrelation baseline)
t-2	2Q	Medium-term lag (6 months)
t-4	4Q	Primary specification (1 year)
t-8	8Q	Long-term lag (2 years, low autocorrelation but weak prediction)
Expectation: Inverted-U relationship:

Short lags (t-1): Strong prediction but high endogeneity
Optimal lag (t-4): Balance prediction and exogeneity
Long lags (t-8): Weak prediction (network position outdated)
4. Autocorrelation Mitigation Strategies
4.1 Problem Statement
Network Persistence: Bank network positions highly stable over time.

Evidence (anticipated from data):

# Autocorrelation of network_out_degree
corr(network_t, network_{t-1}) ≈ 0.85-0.95  # Very high
corr(network_t, network_{t-4}) ≈ 0.70-0.85  # Still substantial
Implication: Lagged network still correlated with current unobservables → residual endogeneity.

4.2 Diagnostic Tests
Test 1: First-Stage Autocorrelation Regression
network_t = α + β·network_{t-4} + controls + ε
Interpret: R² and β coefficient measure persistence.

R² > 0.80 → very high autocorrelation → lagging insufficient
R² < 0.50 → moderate autocorrelation → lagging helpful
Test 2: Hausman-Style Endogeneity Test
# Estimate two models:
M1: survival_t ~ network_t + controls
M2: survival_t ~ network_{t-4} + controls
# Compare coefficients:
hausman_stat = (β_M1 - β_M2)' Var(β_M1 - β_M2)^{-1} (β_M1 - β_M2)
Interpret:

Large difference + significant test → endogeneity present
Similar coefficients → lagged network is valid proxy (low endogeneity)
4.3 Mitigation Strategies
Strategy 1: First-Difference Specification
Approach: Model changes in network position instead of levels

Δsurvival_t = β·Δnetwork_{t-4 to t} + Δcontrols + ε
Advantage: Differences less autocorrelated than levels → reduces persistence problem.

Limitation: Survival is binary (dead/alive) → differencing less natural. Consider duration models.

Strategy 2: Arellano-Bond Dynamic Panel Estimator
Approach: Include lagged dependent variable + instrument with deeper lags

hazard_t = β·network_{t-4} + γ·hazard_{t-1} + controls
# Instrument network_{t-4} with network_{t-8}
Advantage: Gold standard for dynamic panel endogeneity.

Limitation: Requires panel structure (multiple observations per bank over time) and longer time series (need t-8 instruments).

Feasibility: ✅ Possible if we generate quarterly snapshots 2010-2020 (40 quarters).

Strategy 3: Include Lagged Dependent Variable
Approach: Control for past survival probability

survival_t ~ network_{t-4} + survival_probability_{t-4} + controls
Advantage: Absorbs autocorrelated unobservables.

Limitation: Biases coefficient estimates (Nickell bias) unless sample very large.

Recommendation: Use as robustness check, not primary specification.

Strategy 4: Placebo Test with Forward Lags
Approach: Test if future network predicts current survival (should not!)

# Placebo regression (should be nonsignificant):
survival_t ~ network_{t+4} + controls
Interpret:

Significant network_{t+4} → omitted variable bias (unobservables drive both)
Nonsignificant network_{t+4} → lagged specification valid
Use: Falsification test for endogeneity.

5. Implementation Roadmap
Phase 1: Data Generation (Est. 3-5 hours)
Step 1.1: Generate Quarterly Network Snapshots
Task: Modify rolling window pipeline for quarterly windows.

Script: rolling_windows/generate_quarterly_snapshots_2010_2020.py

import pandas as pd
from datetime import datetime, timedelta
# Generate quarterly windows
quarters = pd.date_range(start='2010-01-01', end='2020-12-31', freq='QS')
window_configs = []
for start in quarters:
    end = start + pd.DateOffset(months=3) - pd.Timedelta(days=1)
    window_configs.append({
        "name": f"Q{start.quarter}_{start.year}",
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "filter": f"date('{start.strftime('%Y-%m-%d')}') <= r.start_date <= date('{end.strftime('%Y-%m-%d')}')"
    })
# Run GDS pipeline for each quarter
for config in window_configs:
    create_projection(config)
    compute_metrics(config)  # page_rank, degree, louvain
    export_to_parquet(config)
Metrics to Compute (per quarter):

page_rank (already available)
in_degree, out_degree (already available)
community_louvain (already available)
wcc (already available)
NEW: betweenness_centrality (if computationally feasible)
NEW: closeness_centrality (if computationally feasible)
Output: rolling_windows/output/quarterly_2010_2020/node_features_Q{X}_{YYYY}.parquet

Estimated Runtime:

44 quarterly windows × 4 min/window ≈ 2.9 hours
Step 1.2: Create Quarterly Data Loader
Task: Extend 
RollingWindowDataLoader
 to support quarterly matching.

Script: mlflow_utils/quarterly_window_loader.py

class QuarterlyWindowDataLoader(RollingWindowDataLoader):
    def __init__(self, quarter_dir='rolling_windows/output/quarterly_2010_2020'):
        super().__init__()
        self.quarter_dir = quarter_dir
    
    def load_with_lags(self, lag_quarters=4):
        """
        Load accounting + network data with specified lag.
        
        Returns DataFrame with columns:
        - camel_t (current quarter)
        - network_{t-lag} (lagged network metrics)
        - community_t (current community for stratification)
        """
        # Load accounting data
        accounting = self.load_accounting_data()
        accounting['quarter'] = pd.to_datetime(accounting['DT']).dt.to_period('Q')
        
        # Load quarterly network snapshots
        network_quarters = self._load_all_quarterly_snapshots()
        
        # Create lagged network features
        network_lagged = network_quarters.copy()
        network_lagged['quarter'] = network_lagged['quarter'].shift(lag_quarters)
        network_lagged.columns = [f"{col}_{lag_quarters}q_lag" if col.startswith('network_') else col 
                                   for col in network_lagged.columns]
        
        # Merge accounting_t with network_{t-lag}
        merged = accounting.merge(network_lagged, on=['regn', 'quarter'], how='left')
        
        return merged
Phase 2: Model Implementation (Est. 2-3 hours)
Step 2.1: Create Experiment Directory
cd experiments
cp -r exp_006_community_fixed_effects exp_007_lagged_network
cd exp_007_lagged_network
Step 2.2: Configure Models
File: 
config_cox.yaml

experiment:
  name: "Cox_Lagged_Network_2014_2020"
  description: "Lagged network effects to address endogeneity"
  
data:
  start_year: 2014
  end_year: 2020
  lag_quarters: 4  # Primary specification
models:
  model_1_baseline_contemporaneous:
    name: "M1: Baseline (Contemporaneous Network)"
    features:
      - camel_roa
      - camel_npl_ratio
      - camel_tier1_capital_ratio
      - network_out_degree  # t
      - network_page_rank  # t
      - family_rho_F
      - foreign_FEC_d
    use_lagged_network: false
    stratify_by_community: false
    
  model_2_lagged_network_simple:
    name: "M2: Lagged Network (t-4 quarters)"
    features:
      - camel_roa
      - camel_npl_ratio
      - camel_tier1_capital_ratio
      - network_out_degree_4q_lag  # t-4
      - network_page_rank_4q_lag  # t-4
      - family_rho_F
      - foreign_FEC_d
    use_lagged_network: true
    lag_quarters: 4
    stratify_by_community: false
    
  model_3_lagged_network_contemp_controls:
    name: "M3: Lagged Network + Current Controls"
    features:
      - camel_roa  # t (current)
      - camel_npl_ratio
      - camel_tier1_capital_ratio
      - network_out_degree_4q_lag  # t-4 (lagged)
      - network_page_rank_4q_lag
      - family_rho_F  # t (current)
      - foreign_FEC_d
    use_lagged_network: true
    lag_quarters: 4
    stratify_by_community: false
    
  model_4_full_lag:
    name: "M4: Fully Lagged (All t-4)"
    features:
      - camel_roa_4q_lag
      - camel_npl_ratio_4q_lag
      - camel_tier1_capital_ratio_4q_lag
      - network_out_degree_4q_lag
      - network_page_rank_4q_lag
      - family_rho_F_4q_lag
      - foreign_FEC_d_4q_lag
    use_lagged_network: true
    lag_quarters: 4
    stratify_by_community: false
    
  model_5_arellano_bond:
    name: "M5: Autocorrelation-Adjusted (Delta + Level)"
    features:
      - camel_roa
      - network_out_degree_4q_lag  # Level effect
      - network_out_degree_delta_4q  # Change from t-4 to t
      - network_page_rank_4q_lag
      - network_page_rank_delta_4q
      - family_rho_F
      - foreign_FEC_d
    use_lagged_network: true
    use_delta_specification: true
    lag_quarters: 4
    stratify_by_community: false
    
  model_6_community_stratified_lagged:
    name: "M6: Community-Stratified + Lagged Network"
    features:
      - camel_roa
      - network_out_degree_4q_lag
      - network_page_rank_4q_lag
      - family_rho_F
      - foreign_FEC_d
    use_lagged_network: true
    lag_quarters: 4
    stratify_by_community: true  # Combine exp_006 + exp_007
robustness:
  test_lags: [1, 2, 4, 8]  # Quarters
  placebo_test: true  # Test network_{t+4} → survival_t (should be ns)
  hausman_test: true  # Compare contemporaneous vs. lagged
Step 2.3: Implement Run Script
File: 
run_cox.py

from quarterly_window_loader import QuarterlyWindowDataLoader
def run():
    config = load_config()
    
    # Load data with lags
    loader = QuarterlyWindowDataLoader()
    lag_quarters = config['data']['lag_quarters']
    
    df = loader.load_with_lags(lag_quarters=lag_quarters)
    
    # For Arellano-Bond models, compute deltas
    if model_cfg.get('use_delta_specification'):
        for var in ['network_out_degree', 'network_page_rank']:
            df[f'{var}_delta_4q'] = df[var] - df[f'{var}_4q_lag']
    
    # Run Cox models as in exp_006
    for model_key, model_cfg in config['models'].items():
        with mlflow.start_run(run_name=model_cfg['name']):
            # ... fit model, log metrics
            
            # Additional diagnostics for exp_007
            if model_cfg.get('use_lagged_network'):
                # Autocorrelation diagnostic
                autocorr = compute_autocorrelation(df, lag_quarters)
                mlflow.log_metric("network_autocorr_t_vs_tlag", autocorr)
                
                # First-stage R²
                r2_first_stage = compute_first_stage_r2(df, lag_quarters)
                mlflow.log_metric("first_stage_r2", r2_first_stage)
Phase 3: Diagnostic Tests (Est. 1-2 hours)
Test 3.1: Autocorrelation Analysis
Script: experiments/exp_007_lagged_network/diagnostics/autocorrelation.py

def compute_autocorrelation_structure(df, max_lag=8):
    """
    Compute autocorrelation of network metrics at different lags.
    """
    results = []
    for lag in range(1, max_lag + 1):
        for var in ['network_out_degree', 'network_page_rank']:
            df_lagged = df[[var, 'regn', 'quarter']].copy()
            df_lagged['quarter_lag'] = df_lagged['quarter'] - lag
            
            merged = df.merge(df_lagged, 
                            left_on=['regn', 'quarter'],
                            right_on=['regn', 'quarter_lag'],
                            suffixes=('_t', f'_t{lag}'))
            
            corr = merged[[f'{var}_t', f'{var}_t{lag}']].corr().iloc[0, 1]
            results.append({'variable': var, 'lag': lag, 'correlation': corr})
    
    return pd.DataFrame(results)
# Visualise autocorrelation decay
import matplotlib.pyplot as plt
autocorr_df = compute_autocorrelation_structure(df)
autocorr_df.pivot(index='lag', columns='variable', values='correlation').plot()
plt.title("Network Metric Autocorrelation by Lag")
plt.xlabel("Lag (quarters)")
plt.ylabel("Correlation")
plt.savefig("autocorrelation_decay.png")
mlflow.log_artifact("autocorrelation_decay.png")
Test 3.2: Placebo Test (Forward Lag)
Script: experiments/exp_007_lagged_network/diagnostics/placebo_test.py

def run_placebo_test(df):
    """
    Test if FUTURE network predicts CURRENT survival (should not!).
    If significant → omitted variable bias.
    """
    # Create forward-lagged network (t+4)
    df_forward = df.copy()
    df_forward['quarter_forward'] = df_forward['quarter'] + 4
    
    df = df.merge(df_forward[['regn', 'quarter_forward', 'network_out_degree']],
                  left_on=['regn', 'quarter'],
                  right_on=['regn', 'quarter_forward'],
                  suffixes=('', '_forward4q'))
    
    # Run Cox with forward-lagged network
    ctv = CoxTimeVaryingFitter()
    ctv.fit(df, 
            id_col='regn',
            event_col='event',
            start_col='start_t',
            stop_col='stop_t',
            formula='network_out_degree_forward4q + camel_roa + ...')
    
    # Log placebo test result
    placebo_coef = ctv.params_['network_out_degree_forward4q']
    placebo_pval = ctv.summary.loc['network_out_degree_forward4q', 'p']
    
    mlflow.log_metric("placebo_coef_forward4q", placebo_coef)
    mlflow.log_metric("placebo_pval_forward4q", placebo_pval)
    
    if placebo_pval < 0.05:
        print("⚠️ WARNING: Placebo test significant! Omitted variable bias likely.")
    else:
        print("✅ Placebo test passed. Lagged specification appears valid.")
Test 3.3: Hausman-Style Endogeneity Test
Script: experiments/exp_007_lagged_network/diagnostics/hausman_test.py

def hausman_endogeneity_test(df):
    """
    Compare contemporaneous vs. lagged network coefficients.
    Large difference suggests endogeneity in contemporaneous model.
    """
    # Model A: Contemporaneous
    ctv_contemp = CoxTimeVaryingFitter()
    ctv_contemp.fit(df, formula='network_out_degree + camel_roa + ...')
    
    # Model B: Lagged
    ctv_lagged = CoxTimeVaryingFitter()
    ctv_lagged.fit(df, formula='network_out_degree_4q_lag + camel_roa + ...')
    
    # Extract coefficients
    beta_contemp = ctv_contemp.params_['network_out_degree']
    beta_lagged = ctv_lagged.params_['network_out_degree_4q_lag']
    
    se_contemp = ctv_contemp.standard_errors_['network_out_degree']
    se_lagged = ctv_lagged.standard_errors_['network_out_degree_4q_lag']
    
    # Hausman test statistic
    diff = beta_contemp - beta_lagged
    se_diff = np.sqrt(se_contemp**2 + se_lagged**2)
    z_stat = diff / se_diff
    p_val = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    mlflow.log_metric("hausman_beta_diff", diff)
    mlflow.log_metric("hausman_z_stat", z_stat)
    mlflow.log_metric("hausman_pval", p_val)
    
    if p_val < 0.05:
        print(f"✅ Hausman test significant (p={p_val:.4f}). Endogeneity detected in contemporaneous model.")
    else:
        print(f"⚠️ Hausman test non-significant (p={p_val:.4f}). Contemporaneous and lagged estimates similar → low endogeneity?")
Phase 4: Robustness Checks (Est. 2 hours)
Robustness 4.1: Vary Lag Length
Test: Run models with lags = {1, 2, 4, 8} quarters

Script: Loop over lag_quarters in config

for lag in [1, 2, 4, 8]:
    df_lag = loader.load_with_lags(lag_quarters=lag)
    # Run model 2 (lagged network simple)
    # Log metrics with tag f"lag_{lag}q"
Visualise: Plot coefficient estimates vs. lag length

Expected:

Short lags (1-2Q): Strong prediction, high autocorrelation
Optimal lag (4Q): Balance
Long lags (8Q): Weak prediction
Robustness 4.2: Subperiod Analysis
Test: Run separately for:

2010-2014 (pre-sanctions)
2014-2017 (sanctions shock)
2017-2020 (post-shock adjustment)
Rationale: Structural breaks may alter network effect dynamics.

Robustness 4.3: Alternative Community Definitions
Test: Re-run Model 6 with:

Louvain communities (current)
Sectoral communities (oil/retail/international)
Geographic communities (Moscow/regional)
Rationale: Verify community stratification robust to definition.

6. Expected Results and Interpretation
6.1 Hypotheses
H1 (Endogeneity Exists): Lagged network coefficients weaker than contemporaneous

β_lag < β_contemp → reverse causality was inflating contemporaneous estimates
Hausman test significant
H2 (True Causal Effect): Lagged network remains significant after adjustment

β_lag significant (p < 0.05) → network genuinely predictive
Robust to autocorrelation controls
H3 (Autocorrelation Dominates): Lagged and contemporaneous coefficients similar

β_lag ≈ β_contemp + Hausman test non-significant
High autocorrelation → residual endogeneity
H4 (Placebo Null): Forward-lagged network non-significant

β_forward ≈ 0, p > 0.10
Validates lagged specification
6.2 Interpretation Guide
Result Pattern	Interpretation	Causal Claim Strength
β_lag < β_contemp (both sig)	Partial endogeneity corrected	⭐⭐⭐ Moderate
β_lag ≈ 0 (ns), β_contemp sig	Full endogeneity (no true effect)	❌ Weak
β_lag ≈ β_contemp (both sig)	Low endogeneity OR high autocorrelation	⭐⭐ Weak-Moderate
β_lag sig, β_forward ns, Hausman sig	Strong causal evidence	⭐⭐⭐⭐ Strong
β_lag sig, β_forward sig	Omitted variable bias	❌ Weak
6.3 Policy Implications by Result
If H1 + H2 (Partial endogeneity, true effect exists): → Network metrics valid early warning indicators with 1-year lead time → Supervisors should monitor lagged network positions for stress testing

If H3 (High autocorrelation): → Need stronger identification strategy (instruments, natural experiments) → Lagging alone insufficient; combine with community FE (Model 6)

If H4 fails (Placebo test significant): → Omitted variables dominate (e.g., management quality affects both past network and current survival) → Need additional controls or IV approach

7. Alternative Identification Strategies (If Lagging Insufficient)
7.1 Instrumental Variables
Potential Instruments for network_out_degree:

Geographic distance to Moscow:

Relevance: Banks far from Moscow have fewer ownership opportunities (connection costs)
Exclusion: Geographic location uncorrelated with survival (conditional on fundamentals, regional fixed effects)
Limitation: May violate exclusion if regional economies differ systematically
Historical network position (pre-sample):

Relevance: Network position in 2000-2005 predicts position in 2014-2020 (persistence)
Exclusion: Pre-sample network uncorrelated with 2014-2020 shocks (assumes no long-run confounding)
Limitation: Requires extending data back to 2000-2005
Regulatory events creating exogenous connections:

Example: Licence revocations force healthy banks to acquire customers (exogenous out-degree increase)
Relevance: Licence revocations predict network changes
Exclusion: Licence revocations of other banks uncorrelated with focal bank's survival (exclusion restriction)
Limitation: Rare events, small sample
Feasibility: Moderate. Geographic distance most tractable.

7.2 Difference-in-Differences (Sanctions Shock)
Natural Experiment: 2014 Western sanctions

Approach:

Treatment group: Banks with high foreign ownership (affected by sanctions)
Control group: Purely domestic banks (unaffected)
Outcome: Network position changes 2013-2015
Model:

network_change = β·(foreign_exposure × post_2014) + bank_FE + year_FE + ε
Causal Claim: Sanctions-induced network changes → survival outcomes

Limitation: SUTVA violations (spillovers between treated/control banks)

7.3 Regression Discontinuity (Regulatory Thresholds)
Discontinuity: Minimum capital requirements (e.g., 300M RUB threshold)

Approach:

Banks just above threshold: Eligible for certain activities → higher network opportunities
Banks just below: Ineligible → constrained network formation
Model:

network_t = α + τ·above_threshold + f(capital - threshold) + ε
survival_t ~ network_t (instrumented by above_threshold)
Advantage: Clean identification if threshold exogenously enforced.

Limitation: Banks may manipulate capital around threshold (sorting).

8. Implementation Timeline
Week 1: Data Generation
Day 1-2: Modify rolling window pipeline for quarterly snapshots
Day 3: Run pipeline for 2010-2020 (44 quarters, ~3 hours)
Day 4: Create QuarterlyWindowDataLoader and test
Day 5: Validate data quality (missing values, temporal alignment)
Week 2: Model Development
Day 1: Set up exp_007 directory and config files
Day 2: Implement Models 1-4 (baseline, simple lag, contemp controls, full lag)
Day 3: Implement Model 5 (Arellano-Bond delta specification)
Day 4: Implement Model 6 (community-stratified lagged)
Day 5: Test all models, debug convergence issues
Week 3: Diagnostics and Robustness
Day 1: Autocorrelation analysis (Test 3.1)
Day 2: Placebo test (Test 3.2) and Hausman test (Test 3.3)
Day 3: Vary lag length robustness (4.1)
Day 4: Subperiod analysis (4.2)
Day 5: Aggregate results, create stargazer tables
Week 4: Analysis and Documentation
Day 1-2: Interpret results, create visualisations
Day 3: Write detailed analysis writeup
Day 4: Compare with exp_004-006, synthesise findings
Day 5: Present recommendations, identify next steps (IV if needed)
Total Estimated Time: 4 weeks (part-time, 2-3 hours/day)

9. Success Criteria
Minimum Viable Result
✅ Quarterly network snapshots generated (2010-2020) ✅ Model 2 (lagged network) converges and shows interpretable coefficients ✅ Hausman test executed (contemporaneous vs. lagged comparison) ✅ C-index comparison shows predictive power of lagged metrics

Strong Result
✅ All above + ✅ β_lag < β_contemp AND β_lag remains significant (partial endogeneity corrected) ✅ Placebo test non-significant (β_forward ≈ 0) ✅ Model 6 (community-stratified lagged) converges (cleanest estimate) ✅ Autocorrelation diagnostic shows decay (correlation < 0.70 at 4Q lag)

Publishable Result
✅ All above + ✅ Robustness across lag lengths (1Q, 2Q, 4Q, 8Q show consistent pattern) ✅ Subperiod stability (pre-sanctions, sanctions, post-sanctions similar) ✅ IV or DiD analysis corroborates lagged estimates (if needed) ✅ Comprehensive writeup with policy recommendations

10. Risks and Mitigation
Risk 1: Quarterly Snapshots Too Computationally Expensive
Mitigation:

Use semi-annual snapshots (2/year) instead of quarterly (4/year)
Reduces windows from 44 to 22 → half the computation time
Lag specification: t-2 semesters (1 year) instead of t-4 quarters
Risk 2: High Autocorrelation Renders Lagging Ineffective
Mitigation:

Proceed to IV approach (geographic distance instrument)
Document autocorrelation as limitation, recommend future experiments
Focus on Model 6 (community-stratified lagged) as best available estimate
Risk 3: Model 5 (Arellano-Bond) Fails to Converge
Mitigation:

Simplify to delta specification only (no instruments)
Use first-difference Cox model (if lifelines supports)
Document convergence issues, focus on interpretable Models 2-4
Risk 4: Data Quality Issues (Missing Quarters)
Mitigation:

Forward-fill network metrics for missing quarters (assumption: network constant until updated)
Report missingness rates transparently
Sensitivity analysis excluding banks with >20% missing quarters
11. Next Steps After exp_007
If Lagging Demonstrates Causal Effect:
Policy brief: Lagged network metrics as early warning system (1-year lead time)
Regulatory stress testing: Incorporate lagged network into CBR models
Extension: Multi-lag distributed lag model (network_{t-1} + network_{t-2} + ... + network_{t-8})
If High Autocorrelation Persists:
exp_008: IV approach with geographic distance instrument
exp_009: DiD using 2014 sanctions shock
Collaboration: Request granular monthly network data from CBR
If Endogeneity Fully Explains Effects:
Revisit interpretation: Network metrics as selection indicators not causal factors
Focus on community effects: Exp_006 community stratification as primary result
Alternative mechanisms: Explore reverse causality stories (failing banks lose connections)
12. Conclusion
exp_007 addresses the most critical methodological limitation of exp_004-006: endogeneity of network metrics through temporal precedence.

Key Innovation: Combining quarterly network snapshots with 1-year lags establishes temporal ordering whilst autocorrelation diagnostics and placebo tests validate causal interpretation.

If successful, exp_007 will:

Strengthen causal claims for network effects on bank survival
Demonstrate predictive power of lagged network positions (policy-relevant)
Provide blueprint for similar analyses in other financial network contexts
If unsuccessful (high autocorrelation or placebo failures), exp_007 will:

Motivate IV approaches (exp_008-009)
Clarify limitations of observational network data
Refocus research on community-level mechanisms (exp_006 as primary result)
Recommendation: Proceed with exp_007 as outlined. The methodological rigour and policy relevance justify the 4-week investment, regardless of outcome sign.