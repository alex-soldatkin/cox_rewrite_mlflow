"""
exp_015: Granger Causality Test

Discrete-time panel hazard model (complementary log-log) with lagged
community failure indicators, testing whether FCR Granger-causes survival
after controlling for contagion effects.

Models:
  M1: Baseline cloglog (FCR + CAMEL + ownership + network + community FE)
  M2: + community_failure_lag (contagion control)
  M3: Full period with contagion control
  M4: Pre-2013 only (no reverse causality per exp_013)
  M5: Post-2013 only
  M6: Wald test summary
"""

import mlflow
import sys
import os
import pandas as pd
import numpy as np
from collections import OrderedDict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mlflow_utils.tracking import setup_experiment
from mlflow_utils.quarterly_window_loader import QuarterlyWindowDataLoader
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from statsmodels.genmod.families import Binomial
from statsmodels.genmod.families.links import CLogLog

EXP_DIR = os.path.dirname(os.path.abspath(__file__))

OWNERSHIP_FEATURES = [
    'family_connection_ratio', 'family_ownership_pct',
    'state_ownership_pct', 'foreign_ownership_total_pct',
]
NETWORK_FEATURES = ['rw_page_rank_4q_lag', 'rw_out_degree_4q_lag']
CAMEL_FEATURES = ['camel_roa', 'camel_npl_ratio', 'camel_tier1_capital_ratio']
BASE_FEATURES = OWNERSHIP_FEATURES + NETWORK_FEATURES + CAMEL_FEATURES


def collapse_small_communities(df, community_col='rw_community_louvain_4q_lag', min_size=5):
    def extract_coarsest(val):
        if isinstance(val, (list, np.ndarray)):
            return float(val[0]) if len(val) > 0 else -1.0
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return -1.0
        return float(val)

    df['community_scalar'] = df[community_col].apply(extract_coarsest)
    counts = df.groupby('community_scalar')['regn'].nunique()
    small = counts[counts < min_size].index
    df['community_collapsed'] = df['community_scalar'].copy()
    df.loc[df['community_scalar'].isin(small), 'community_collapsed'] = -1
    return df


def aggregate_temporal_communities(df, community_col='community_collapsed'):
    bank_stable = (
        df[df[community_col].notna()]
        .groupby('regn')[community_col]
        .agg(lambda x: x.value_counts().index[0] if len(x) > 0 else -1)
    )
    df[community_col] = df['regn'].map(bank_stable)
    return df


def create_lagged_community_failure(df):
    """For each bank-quarter, compute whether any OTHER bank in the same
    community had event=1 in the previous 4 quarters."""
    print("Creating community failure lag indicators...")
    df = df.sort_values(['regn', 'DT'])
    df['DT'] = pd.to_datetime(df['DT'])

    # Build community-quarter failure counts (excluding the bank itself)
    failures = df[df['event'] == 1][['regn', 'DT', 'community_collapsed']].copy()
    failures = failures.rename(columns={'DT': 'failure_dt', 'regn': 'failed_regn'})

    # For each bank-quarter, check if any bank in same community failed
    # in the past 4 quarters (approx 365 days)
    community_failure_lag = []
    grouped = df.groupby('community_collapsed')

    for comm, comm_df in grouped:
        comm_failures = failures[failures['community_collapsed'] == comm]
        for _, row in comm_df.iterrows():
            dt = row['DT']
            lookback_start = dt - pd.Timedelta(days=365)
            # Failures in same community in past year, excluding self
            n_failures = ((comm_failures['failure_dt'] >= lookback_start) &
                          (comm_failures['failure_dt'] < dt) &
                          (comm_failures['failed_regn'] != row['regn'])).sum()
            community_failure_lag.append(min(n_failures, 1))  # Binary: any failure

    df['community_failure_lag'] = community_failure_lag
    n_exposed = (df['community_failure_lag'] > 0).sum()
    print(f"  Observations with community failure in past year: {n_exposed:,} "
          f"({100 * n_exposed / len(df):.1f}%)")
    return df


def create_lagged_community_failure_fast(df):
    """Vectorised version: for each bank-quarter, any other bank in same
    community had event=1 in the prior 4 quarters."""
    print("Creating community failure lag indicators (vectorised)...")
    df = df.sort_values(['regn', 'DT']).copy()
    df['DT'] = pd.to_datetime(df['DT'])

    # Get all failure events
    failures = df.loc[df['event'] == 1, ['regn', 'DT', 'community_collapsed']].copy()

    # For each observation, merge with failures in same community
    # within past ~365 days, excluding self
    df['community_failure_lag'] = 0

    for comm in df['community_collapsed'].unique():
        comm_mask = df['community_collapsed'] == comm
        comm_failures = failures[failures['community_collapsed'] == comm]

        if comm_failures.empty:
            continue

        failure_dates = comm_failures[['regn', 'DT']].values
        comm_idx = df.index[comm_mask]

        for idx in comm_idx:
            row_dt = df.at[idx, 'DT']
            row_regn = df.at[idx, 'regn']
            lookback = row_dt - pd.Timedelta(days=365)
            hits = sum(1 for f_regn, f_dt in failure_dates
                       if lookback <= f_dt < row_dt and f_regn != row_regn)
            if hits > 0:
                df.at[idx, 'community_failure_lag'] = 1

    n_exposed = (df['community_failure_lag'] > 0).sum()
    print(f"  Observations with community failure in past year: {n_exposed:,} "
          f"({100 * n_exposed / len(df):.1f}%)")
    return df


def prepare_panel(df, features, period_filter=None):
    """Prepare panel data for discrete-time hazard model."""
    df_panel = df.copy()

    if period_filter == 'pre_2013':
        df_panel = df_panel[df_panel['DT'] < pd.Timestamp('2013-07-01')]
    elif period_filter == 'post_2013':
        df_panel = df_panel[df_panel['DT'] >= pd.Timestamp('2013-07-01')]

    feat_cols = [c for c in features if c in df_panel.columns]
    df_panel[feat_cols] = df_panel[feat_cols].fillna(0)
    final = [c for c in feat_cols if df_panel[c].nunique() > 1]

    if final:
        scaler = StandardScaler()
        df_panel[final] = scaler.fit_transform(df_panel[final])

    keep = ['regn', 'event', 'community_collapsed'] + final
    keep = [c for c in keep if c in df_panel.columns]
    df_clean = df_panel[keep].dropna()

    print(f"  Panel: {len(df_clean):,} obs, {df_clean['regn'].nunique()} banks, "
          f"{int(df_clean['event'].sum())} events")
    return df_clean, final


def get_stars(p):
    if p < 0.001: return "***"
    elif p < 0.01: return "**"
    elif p < 0.05: return "*"
    elif p < 0.1: return "+"
    else: return ""


def create_glm_stargazer(result, model_name, n_subjects=None):
    """Create stargazer-style output from a statsmodels GLM result."""
    rows = {}
    for var in result.params.index:
        if var == 'const':
            continue
        coef = result.params[var]
        se = result.bse[var]
        p = result.pvalues[var]
        stars = get_stars(p)
        rows[var] = f"{coef:.4f}{stars} ({se:.4f})"

    metrics = {
        'Observations': str(int(result.nobs)),
        'Subjects': str(n_subjects) if n_subjects else '',
        'Events': str(int(result.model.endog.sum())),
        'Log Likelihood': f"{result.llf:.2f}",
        'AIC': f"{result.aic:.2f}",
        'BIC': f"{result.bic:.2f}",
    }
    rows.update(metrics)

    df = pd.DataFrame({'Stargazer_Output': rows})
    df.index.name = 'variable'
    return df


def create_glm_stargazer_hr(result, n_subjects=None):
    """Create HR-style stargazer (exponentiated coefficients)."""
    rows = {}
    for var in result.params.index:
        if var == 'const':
            continue
        coef = result.params[var]
        hr = np.exp(coef)
        se_hr = hr * result.bse[var]
        p = result.pvalues[var]
        stars = get_stars(p)
        rows[var] = f"{hr:.4f}{stars} ({se_hr:.4f})"

    metrics = {
        'Observations': str(int(result.nobs)),
        'Subjects': str(n_subjects) if n_subjects else '',
        'Events': str(int(result.model.endog.sum())),
        'Log Likelihood': f"{result.llf:.2f}",
        'AIC': f"{result.aic:.2f}",
    }
    rows.update(metrics)

    df = pd.DataFrame({'Stargazer_Output_HR': rows})
    df.index.name = 'variable'
    return df


def generate_glm_interpretation(result, model_name):
    """Generate markdown interpretation for GLM discrete-time hazard."""
    lines = [f"# Interpretation: {model_name}", "",
             "## Coefficient Interpretations",
             "Complementary log-log model. Exponentiated coefficients approximate hazard ratios.", ""]
    for var in result.params.index:
        if var == 'const':
            continue
        coef = result.params[var]
        hr = np.exp(coef)
        p = result.pvalues[var]
        pct = (hr - 1) * 100
        direction = "decreases" if coef < 0 else "increases"
        sig = get_stars(p)
        lines.append(f"- **{var}**: HR={hr:.4f}, {direction} hazard by {abs(pct):.1f}% {sig} (p={p:.4f})")
    lines.append("")

    # Granger test: report Wald test for FCR
    if 'family_connection_ratio' in result.params.index:
        coef = result.params['family_connection_ratio']
        p = result.pvalues['family_connection_ratio']
        lines.append("## Granger Causality Assessment")
        lines.append(f"- FCR coefficient: {coef:.4f} (p={p:.4f})")
        if p < 0.05:
            lines.append("- **FCR Granger-causes survival** at 5% level")
        elif p < 0.10:
            lines.append("- FCR Granger-causes survival at 10% level (marginal)")
        else:
            lines.append("- FCR does NOT Granger-cause survival at conventional levels")

    return "\n".join(lines)


def run_model(model_key, model_name, df_panel, features, period=None):
    """Run a single GLM cloglog model."""
    print(f"\n{'=' * 70}")
    print(f"Running: {model_name}")
    print(f"{'=' * 70}")

    df_clean, final_feats = prepare_panel(df_panel, features, period_filter=period)

    if df_clean['event'].sum() < 10:
        print(f"Skipping: only {int(df_clean['event'].sum())} events")
        return None, None

    with mlflow.start_run(run_name=model_name):
        mlflow.log_param("model_type", "GLM_cloglog")
        mlflow.log_param("model_key", model_key)
        mlflow.log_param("period_filter", period or "full")
        mlflow.log_param("n_observations", len(df_clean))
        mlflow.log_param("n_banks", df_clean['regn'].nunique())
        mlflow.log_param("n_events", int(df_clean['event'].sum()))
        mlflow.log_param("features", ", ".join(final_feats))

        y = df_clean['event']
        X = sm.add_constant(df_clean[final_feats])

        try:
            model = sm.GLM(y, X, family=Binomial(link=CLogLog()))
            result = model.fit()
            print(f"Converged. AIC={result.aic:.2f}")

            mlflow.log_metric("aic", result.aic)
            mlflow.log_metric("bic", result.bic)
            mlflow.log_metric("log_likelihood", result.llf)

            if 'family_connection_ratio' in result.params.index:
                mlflow.log_metric("fcr_coef", result.params['family_connection_ratio'])
                mlflow.log_metric("fcr_pval", result.pvalues['family_connection_ratio'])

            n_subj = df_clean['regn'].nunique()

            stg = create_glm_stargazer(result, model_name, n_subjects=n_subj)
            stg_path = os.path.join(EXP_DIR, f'stargazer_{model_key}.csv')
            stg.to_csv(stg_path)
            mlflow.log_artifact(stg_path)

            hr = create_glm_stargazer_hr(result, n_subjects=n_subj)
            hr_path = os.path.join(EXP_DIR, f'stargazer_hr_{model_key}.csv')
            hr.to_csv(hr_path)
            mlflow.log_artifact(hr_path)

            interp = generate_glm_interpretation(result, model_name)
            interp_path = os.path.join(EXP_DIR, f'interpretation_{model_key}.md')
            with open(interp_path, 'w') as f:
                f.write(interp)
            mlflow.log_artifact(interp_path)

            print(result.summary())
            return result, stg

        except Exception as e:
            print(f"Model failed: {e}")
            import traceback
            traceback.print_exc()
            mlflow.log_param("status", "failed")
            return None, None


def create_aggregated_stargazer(all_stg):
    if not all_stg:
        return
    dfs = []
    for key, stg in all_stg.items():
        col = stg.rename(columns={'Stargazer_Output': key})
        dfs.append(col)
    agg = pd.concat(dfs, axis=1)
    agg_path = os.path.join(EXP_DIR, 'stargazer_aggregated.csv')
    agg.to_csv(agg_path)
    print(f"\nSaved aggregated stargazer to {agg_path}")


def main():
    print("=" * 70)
    print("EXP_015: GRANGER CAUSALITY TEST")
    print("=" * 70)

    setup_experiment("exp_015_granger_causality")

    # Load data
    print("\n1. Loading data...")
    loader = QuarterlyWindowDataLoader(
        quarterly_dir='rolling_windows/output/quarterly_2004_2020'
    )
    df = loader.load_with_lags(lag_quarters=4, start_year=2004, end_year=2020)
    print(f"Loaded {len(df):,} obs, {df['regn'].nunique()} banks")

    # Communities
    df = collapse_small_communities(df)
    df = aggregate_temporal_communities(df)

    # Create contagion lag
    print("\n2. Creating contagion indicators...")
    df = create_lagged_community_failure_fast(df)

    # Models
    all_stg = {}

    # M1: Baseline (no contagion control)
    r, s = run_model('M1_baseline', 'M1: Baseline (no contagion)',
                     df, BASE_FEATURES)
    if s is not None: all_stg['M1'] = s

    # M2: + community contagion
    r, s = run_model('M2_contagion', 'M2: + Community contagion control',
                     df, BASE_FEATURES + ['community_failure_lag'])
    if s is not None: all_stg['M2'] = s

    # M3: Full period with contagion (same as M2, reference)
    # M4: Pre-2013 only
    r, s = run_model('M4_pre2013', 'M4: Pre-2013 (no reverse causality)',
                     df, BASE_FEATURES + ['community_failure_lag'],
                     period='pre_2013')
    if s is not None: all_stg['M4'] = s

    # M5: Post-2013 only
    r, s = run_model('M5_post2013', 'M5: Post-2013',
                     df, BASE_FEATURES + ['community_failure_lag'],
                     period='post_2013')
    if s is not None: all_stg['M5'] = s

    create_aggregated_stargazer(all_stg)

    # Summary
    print(f"\n{'=' * 70}")
    print("GRANGER CAUSALITY SUMMARY")
    print(f"{'=' * 70}")
    print("If FCR is significant in M2 (controlling for contagion) and M4")
    print("(pre-2013 where exp_013 shows no reverse causality), then FCR")
    print("Granger-causes survival.")
    print(f"\n{'=' * 70}")
    print("EXP_015 COMPLETE")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
