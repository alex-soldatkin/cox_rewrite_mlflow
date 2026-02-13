"""
exp_017: Placebo / Falsification Tests

Three tests showing the FCR effect is specific, not spurious:
  A. Random FCR permutation within community strata (100 iterations)
  B. Pseudo-crisis dates (shift 2008→2005-2006, 2014→2011-2012)
  C. Non-family ownership HHI as negative control

All tests re-run the baseline Cox model from exp_009.
"""

import mlflow
import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mlflow_utils.tracking import setup_experiment
from mlflow_utils.quarterly_window_loader import QuarterlyWindowDataLoader
from lifelines import CoxTimeVaryingFitter
from lifelines.utils import concordance_index
from visualisations.cox_stargazer_new import (
    create_single_column_stargazer,
    create_single_column_stargazer_hr,
)
from visualisations.cox_interpretation import generate_interpretation_report
from sklearn.preprocessing import StandardScaler

EXP_DIR = os.path.dirname(os.path.abspath(__file__))

OWNERSHIP_FEATURES = [
    'family_connection_ratio', 'family_ownership_pct',
    'state_ownership_pct', 'foreign_ownership_total_pct',
]
NETWORK_FEATURES = ['rw_page_rank_4q_lag', 'rw_out_degree_4q_lag']
CAMEL_FEATURES = ['camel_roa', 'camel_npl_ratio', 'camel_tier1_capital_ratio']
BASE_FEATURES = OWNERSHIP_FEATURES + NETWORK_FEATURES + CAMEL_FEATURES

REAL_CRISES = {
    'crisis_2008': ('2008-09-01', '2009-12-31'),
    'crisis_2014': ('2014-03-01', '2015-12-31'),
}

PSEUDO_CRISES = {
    'pseudo_2008': ('2005-09-01', '2006-12-31'),
    'pseudo_2014': ('2011-03-01', '2012-12-31'),
}

N_PERMUTATIONS = 100
RNG_SEED = 42


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


def prepare_cox_data(df, features):
    df_cox = df.copy()
    df_cox['date'] = pd.to_datetime(df_cox['DT'])
    df_cox = df_cox.sort_values(by=['regn', 'date'])
    df_cox['start'] = df_cox['date']
    df_cox['stop'] = df_cox.groupby('regn')['date'].shift(-1)
    mask_last = df_cox['stop'].isna()
    df_cox.loc[mask_last, 'stop'] = df_cox.loc[mask_last, 'start'] + pd.Timedelta(days=30)
    min_dates = df_cox.groupby('regn')['date'].transform('min')
    df_cox['start_t'] = (df_cox['start'] - min_dates).dt.days
    df_cox['stop_t'] = (df_cox['stop'] - min_dates).dt.days
    df_cox = df_cox[df_cox['stop_t'] > df_cox['start_t']]

    feat_cols = [c for c in features if c in df_cox.columns]
    df_cox[feat_cols] = df_cox[feat_cols].fillna(0)
    final = [c for c in feat_cols if df_cox[c].nunique() > 1]

    if final:
        scaler = StandardScaler()
        df_cox[final] = scaler.fit_transform(df_cox[final])
        for col in final:
            lo, hi = df_cox[col].min(), df_cox[col].max()
            if hi > lo:
                df_cox[col] = 100 * (df_cox[col] - lo) / (hi - lo)

    keep = ['regn', 'start_t', 'stop_t', 'event', 'community_collapsed'] + final
    keep = [c for c in keep if c in df_cox.columns]
    return df_cox[keep].copy(), final


def run_cox(model_name, df_cox, features, log_mlflow=True, **kwargs):
    """Run a single Cox model. Returns (ctv, stg) or (None, None)."""
    n_events = int(df_cox['event'].sum())
    if n_events < 10:
        print(f"  Skipping {model_name}: only {n_events} events")
        return None, None

    ctv = CoxTimeVaryingFitter(penalizer=0.01, l1_ratio=0.0)
    try:
        if 'community_collapsed' in df_cox.columns:
            ctv.fit(df_cox, id_col='regn', event_col='event',
                    start_col='start_t', stop_col='stop_t',
                    strata=['community_collapsed'], show_progress=False)
        else:
            ctv.fit(df_cox, id_col='regn', event_col='event',
                    start_col='start_t', stop_col='stop_t', show_progress=False)
    except Exception as e:
        print(f"  Model failed: {e}")
        return None, None

    try:
        ph = ctv.predict_partial_hazard(df_cox)
        c_idx = concordance_index(df_cox['stop_t'], -ph, df_cox['event'])
    except Exception:
        c_idx = None

    n_subj = df_cox['regn'].nunique()
    stg = create_single_column_stargazer(ctv, c_index=c_idx, n_subjects=n_subj)

    if log_mlflow:
        with mlflow.start_run(run_name=model_name):
            mlflow.log_param("model_type", "CoxTimeVarying")
            mlflow.log_param("n_observations", len(df_cox))
            mlflow.log_param("n_banks", n_subj)
            mlflow.log_param("n_events", n_events)
            for k, v in kwargs.items():
                mlflow.log_param(k, v)
            mlflow.log_metric("log_likelihood", ctv.log_likelihood_)
            mlflow.log_metric("aic_partial", ctv.AIC_partial_)
            if c_idx is not None:
                mlflow.log_metric("c_index", c_idx)

            stg_path = os.path.join(EXP_DIR, f'stargazer_{model_name.replace(" ", "_").replace(":", "")}.csv')
            stg.to_csv(stg_path)
            mlflow.log_artifact(stg_path)

            hr = create_single_column_stargazer_hr(ctv, c_index=c_idx, n_subjects=n_subj)
            hr_path = stg_path.replace('stargazer_', 'stargazer_hr_')
            hr.to_csv(hr_path)
            mlflow.log_artifact(hr_path)

            interp = generate_interpretation_report(ctv, model_name=model_name)
            interp_path = os.path.join(EXP_DIR, f'interpretation_{model_name.replace(" ", "_").replace(":", "")}.md')
            with open(interp_path, 'w') as f:
                f.write(interp)
            mlflow.log_artifact(interp_path)

    return ctv, stg


def get_fcr_coef(ctv):
    """Extract FCR coefficient and p-value from a fitted model."""
    if ctv is None:
        return np.nan, np.nan
    summary = ctv.summary
    if 'family_connection_ratio' in summary.index:
        row = summary.loc['family_connection_ratio']
        return row['coef'], row.get('p', row.get('p-value', np.nan))
    return np.nan, np.nan


# ── Placebo A: FCR Permutation ──────────────────────────────────────────

def run_permutation_test(df, n_perms=N_PERMUTATIONS, seed=RNG_SEED):
    """Permute FCR within community strata and re-run Cox N times."""
    print(f"\n{'=' * 70}")
    print(f"PLACEBO A: FCR PERMUTATION ({n_perms} iterations)")
    print(f"{'=' * 70}")

    rng = np.random.RandomState(seed)

    # First run with real FCR (M1 baseline)
    print("\nM1: Real FCR (baseline)")
    df_cox, feats = prepare_cox_data(df, BASE_FEATURES)
    ctv_real, stg_real = run_cox('M1_real_FCR', df_cox, feats, model_key='M1_real')
    real_coef, real_p = get_fcr_coef(ctv_real)
    print(f"  Real FCR coef: {real_coef:.6f}, p={real_p:.4f}")

    # Permutation loop
    perm_coefs = []
    perm_pvals = []
    print(f"\nRunning {n_perms} permutations (within community strata)...")

    for i in range(n_perms):
        df_perm = df.copy()
        # Permute FCR within each community
        for comm in df_perm['community_collapsed'].unique():
            mask = df_perm['community_collapsed'] == comm
            # Get unique bank FCR values and shuffle
            bank_fcrs = df_perm.loc[mask].groupby('regn')['family_connection_ratio'].first()
            shuffled = rng.permutation(bank_fcrs.values)
            fcr_map = dict(zip(bank_fcrs.index, shuffled))
            df_perm.loc[mask, 'family_connection_ratio'] = df_perm.loc[mask, 'regn'].map(fcr_map)

        df_cox_perm, feats_perm = prepare_cox_data(df_perm, BASE_FEATURES)
        ctv_perm, _ = run_cox(f'perm_{i}', df_cox_perm, feats_perm, log_mlflow=False)
        coef, p = get_fcr_coef(ctv_perm)
        perm_coefs.append(coef)
        perm_pvals.append(p)

        if (i + 1) % 10 == 0:
            print(f"  Completed {i + 1}/{n_perms}")

    perm_coefs = np.array(perm_coefs)
    valid = ~np.isnan(perm_coefs)
    n_valid = valid.sum()

    # Empirical p-value: fraction of permuted coefs more extreme than real
    if n_valid > 0 and not np.isnan(real_coef):
        emp_p = (np.abs(perm_coefs[valid]) >= np.abs(real_coef)).mean()
    else:
        emp_p = np.nan

    print(f"\n  Real FCR coefficient: {real_coef:.6f}")
    print(f"  Permuted mean: {np.nanmean(perm_coefs):.6f}")
    print(f"  Permuted std: {np.nanstd(perm_coefs):.6f}")
    print(f"  Empirical p-value: {emp_p:.4f}")
    print(f"  Valid permutations: {n_valid}/{n_perms}")

    # Save results
    perm_df = pd.DataFrame({
        'iteration': range(n_perms),
        'fcr_coef': perm_coefs,
        'fcr_pval': perm_pvals,
    })
    perm_df.to_csv(os.path.join(EXP_DIR, 'permutation_results.csv'), index=False)

    return {
        'real_coef': real_coef, 'real_p': real_p,
        'perm_mean': np.nanmean(perm_coefs),
        'perm_std': np.nanstd(perm_coefs),
        'empirical_p': emp_p,
        'n_valid': n_valid,
    }, stg_real


# ── Placebo B: Pseudo-Crisis Dates ─────────────────────────────────────

def create_crisis_indicators(df, crisis_dict):
    df['DT'] = pd.to_datetime(df['DT'])
    cols = []
    for name, (start, end) in crisis_dict.items():
        df[name] = ((df['DT'] >= pd.Timestamp(start)) & (df['DT'] <= pd.Timestamp(end))).astype(int)
        cols.append(name)
    return df, cols


def create_interactions(df, features, crisis_cols):
    interaction_cols = []
    for feat in features:
        for crisis in crisis_cols:
            col = f'{feat}_x_{crisis}'
            df[col] = df[feat] * df[crisis]
            interaction_cols.append(col)
    return df, interaction_cols


def run_pseudo_crisis_test(df):
    """Run Cox with real and pseudo crisis interaction terms."""
    print(f"\n{'=' * 70}")
    print("PLACEBO B: PSEUDO-CRISIS DATES")
    print(f"{'=' * 70}")

    results = {}

    # M4: Pseudo-crisis (2008→2005-2006)
    df_pseudo = df.copy()
    df_pseudo, pseudo_cols = create_crisis_indicators(df_pseudo, PSEUDO_CRISES)
    df_pseudo, pseudo_int = create_interactions(df_pseudo, ['family_connection_ratio'], pseudo_cols)
    features_pseudo = BASE_FEATURES + pseudo_cols + pseudo_int

    print("\nM4: Pseudo-crisis dates (2008→2005-06, 2014→2011-12)")
    df_cox, feats = prepare_cox_data(df_pseudo, features_pseudo)
    ctv, stg = run_cox('M4_pseudo_crisis', df_cox, feats,
                       model_key='M4_pseudo', crisis_type='pseudo')
    results['M4_pseudo'] = stg

    # M6: Real crisis (reference)
    df_real = df.copy()
    df_real, real_cols = create_crisis_indicators(df_real, REAL_CRISES)
    df_real, real_int = create_interactions(df_real, ['family_connection_ratio'], real_cols)
    features_real = BASE_FEATURES + real_cols + real_int

    print("\nM6: Real crisis dates (reference)")
    df_cox, feats = prepare_cox_data(df_real, features_real)
    ctv, stg = run_cox('M6_real_crisis', df_cox, feats,
                       model_key='M6_real', crisis_type='real')
    results['M6_real'] = stg

    return results


# ── Placebo C: Non-Family Ownership HHI ────────────────────────────────

def run_nonfamily_hhi_test(df):
    """Replace FCR with non-family ownership HHI as negative control."""
    print(f"\n{'=' * 70}")
    print("PLACEBO C: NON-FAMILY OWNERSHIP HHI")
    print(f"{'=' * 70}")

    results = {}

    # Compute non-family ownership concentration proxy:
    # Use (1 - family_ownership_pct/100) as a rough non-family ownership share
    # Then use state + foreign as non-family concentration proxy
    df_nf = df.copy()
    df_nf['nonfamily_ownership_hhi'] = (
        (df_nf['state_ownership_pct'] / 100) ** 2 +
        (df_nf['foreign_ownership_total_pct'] / 100) ** 2
    ).fillna(0)

    # Replace FCR with non-family HHI
    features_nf = [
        'nonfamily_ownership_hhi', 'family_ownership_pct',
        'state_ownership_pct', 'foreign_ownership_total_pct',
    ] + NETWORK_FEATURES + CAMEL_FEATURES

    print("\nM7: Non-family ownership HHI (replacing FCR)")
    df_cox, feats = prepare_cox_data(df_nf, features_nf)
    ctv, stg = run_cox('M7_nonfamily_hhi', df_cox, feats,
                       model_key='M7_nonfamily')
    results['M7_nonfamily'] = stg

    # M8: Random ownership concentration
    df_rand = df.copy()
    rng = np.random.RandomState(RNG_SEED)
    df_rand['random_ownership'] = rng.uniform(0, 1, len(df_rand))

    features_rand = [
        'random_ownership', 'family_ownership_pct',
        'state_ownership_pct', 'foreign_ownership_total_pct',
    ] + NETWORK_FEATURES + CAMEL_FEATURES

    print("\nM8: Random ownership concentration (pure noise)")
    df_cox, feats = prepare_cox_data(df_rand, features_rand)
    ctv, stg = run_cox('M8_random', df_cox, feats,
                       model_key='M8_random')
    results['M8_random'] = stg

    return results


def create_aggregated_stargazer(all_stg):
    if not all_stg:
        return
    dfs = []
    for key, stg in all_stg.items():
        if stg is not None:
            col = stg.rename(columns={'Stargazer_Output': key})
            dfs.append(col)
    if dfs:
        agg = pd.concat(dfs, axis=1)
        agg_path = os.path.join(EXP_DIR, 'stargazer_aggregated.csv')
        agg.to_csv(agg_path)
        print(f"\nSaved aggregated stargazer to {agg_path}")


def main():
    print("=" * 70)
    print("EXP_017: PLACEBO / FALSIFICATION TESTS")
    print("=" * 70)

    setup_experiment("exp_017_placebo_tests")

    # Load data
    print("\n1. Loading data...")
    loader = QuarterlyWindowDataLoader(
        quarterly_dir='rolling_windows/output/quarterly_2004_2020'
    )
    df = loader.load_with_lags(lag_quarters=4, start_year=2004, end_year=2020)
    print(f"Loaded {len(df):,} obs, {df['regn'].nunique()} banks")

    df = collapse_small_communities(df)
    df = aggregate_temporal_communities(df)

    all_stg = {}

    # A: Permutation test
    perm_results, stg_real = run_permutation_test(df)
    if stg_real is not None:
        all_stg['M1_real'] = stg_real

    # B: Pseudo-crisis test
    crisis_stg = run_pseudo_crisis_test(df)
    all_stg.update(crisis_stg)

    # C: Non-family HHI test
    hhi_stg = run_nonfamily_hhi_test(df)
    all_stg.update(hhi_stg)

    create_aggregated_stargazer(all_stg)

    # Summary
    print(f"\n{'=' * 70}")
    print("PLACEBO TEST SUMMARY")
    print(f"{'=' * 70}")
    print(f"\nA. Permutation test:")
    print(f"   Real FCR coef: {perm_results['real_coef']:.6f} (p={perm_results['real_p']:.4f})")
    print(f"   Permuted mean: {perm_results['perm_mean']:.6f} (std={perm_results['perm_std']:.6f})")
    print(f"   Empirical p-value: {perm_results['empirical_p']:.4f}")
    print(f"\nB. Pseudo-crisis: see stargazer_M4_pseudo_crisis.csv vs stargazer_M6_real_crisis.csv")
    print(f"   Pseudo-crisis interactions should be non-significant.")
    print(f"\nC. Non-family HHI: see stargazer_M7_nonfamily_hhi.csv")
    print(f"   If non-family HHI is also protective, effect is generic concentration.")
    print(f"\n{'=' * 70}")
    print("EXP_017 COMPLETE")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
