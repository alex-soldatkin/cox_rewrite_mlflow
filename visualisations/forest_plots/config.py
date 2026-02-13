"""Configuration for forest plots: variable groups, labels, colours, experiment paths."""

from pathlib import Path

# Root of the project
BASE_PATH = Path(__file__).parent.parent.parent

# ---------------------------------------------------------------------------
# Variable groups — controls faceting in forest plots
# ---------------------------------------------------------------------------

VARIABLE_GROUPS = {
    # Family / key independent variable
    'family_connection_ratio': 'Family',
    'family_ownership_pct': 'Family',
    # TCE mechanism proxies
    'stake_fragmentation_index': 'Mechanism',
    'family_company_count': 'Mechanism',
    'group_total_capital': 'Mechanism',
    'group_sector_count': 'Mechanism',
    'group_total_paid_tax': 'Mechanism',
    'group_total_vehicles': 'Mechanism',
    'group_total_receipts': 'Mechanism',
    # Other ownership controls
    'state_ownership_pct': 'Ownership',
    'foreign_ownership_total_pct': 'Ownership',
    'nonfamily_ownership_hhi': 'Ownership',
    'random_ownership': 'Ownership',
    # Contagion
    'community_failure_lag': 'Contagion',
    # CAMEL indicators
    'camel_roa': 'CAMEL',
    'camel_npl_ratio': 'CAMEL',
    'camel_tier1_capital_ratio': 'CAMEL',
    'camel_liquid_assets_ratio': 'CAMEL',
    # Network topology
    'rw_page_rank_4q_lag': 'Network',
    'rw_out_degree_4q_lag': 'Network',
    # Crisis dummies
    'crisis_2004': 'Crisis',
    'crisis_2008': 'Crisis',
    'crisis_2014': 'Crisis',
    # Regime
    'governor_nabiullina': 'Regime',
    'epu_index': 'Regime',
}

# Display order within the y-axis (top to bottom)
VARIABLE_ORDER = [
    # Family
    'family_connection_ratio',
    'family_ownership_pct',
    # Mechanism
    'stake_fragmentation_index',
    'family_company_count',
    'group_total_capital',
    'group_sector_count',
    'group_total_paid_tax',
    'group_total_vehicles',
    'group_total_receipts',
    # Ownership
    'state_ownership_pct',
    'foreign_ownership_total_pct',
    # CAMEL
    'camel_roa',
    'camel_npl_ratio',
    'camel_tier1_capital_ratio',
    'camel_liquid_assets_ratio',
    # Network
    'rw_page_rank_4q_lag',
    'rw_out_degree_4q_lag',
    # Crisis
    'crisis_2004',
    'crisis_2008',
    'crisis_2014',
    # Regime
    'governor_nabiullina',
    'epu_index',
]

GROUP_ORDER = ['Family', 'Mechanism', 'Ownership', 'CAMEL', 'Network', 'Contagion', 'Crisis', 'Regime', 'Interaction']

# ---------------------------------------------------------------------------
# Human-readable labels (reused from table_generator.py definitions)
# ---------------------------------------------------------------------------

VARIABLE_LABELS = {
    # Family
    'family_connection_ratio': '\u03C1F (Family connection ratio)',
    'family_ownership_pct': 'FOP (Family ownership %)',
    # TCE mechanism proxies
    'stake_fragmentation_index': 'SFI (Stake fragmentation)',
    'family_company_count': '|CF| (Family company count)',
    'group_total_capital': 'GTC (Group total capital)',
    'group_sector_count': 'GSC (Group sector count)',
    'group_total_paid_tax': 'GTPT (Group total paid tax)',
    'group_total_vehicles': 'GTV (Group total vehicles)',
    'group_total_receipts': 'GTR (Group total receipts)',
    # Ownership controls
    'state_ownership_pct': 'SOP (State ownership %)',
    'foreign_ownership_total_pct': 'FEC (Foreign ownership %)',
    'nonfamily_ownership_hhi': 'HHI (Non-family ownership)',
    'random_ownership': 'Random ownership (noise)',
    # Contagion
    'community_failure_lag': 'Community failure lag',
    # CAMEL indicators
    'camel_roa': 'ROA(b)',
    'camel_npl_ratio': 'NPL / Loans',
    'camel_tier1_capital_ratio': 'Tier 1 / Assets',
    'camel_liquid_assets_ratio': 'LA / TA',
    # Network topology
    'rw_page_rank_4q_lag': 'PR(v) (PageRank, 4Q lag)',
    'rw_out_degree_4q_lag': 'Cout(v) (Out-degree, 4Q lag)',
    # Crisis dummies
    'crisis_2004': 'Crisis 2004',
    'crisis_2008': 'Crisis 2008',
    'crisis_2014': 'Crisis 2014',
    # Regime
    'governor_nabiullina': 'Nabiullina era',
    'epu_index': 'EPU index',
}

# Interaction term labels (dynamic — matched by prefix)
INTERACTION_LABELS = {
    'family_connection_ratio_x_crisis_2004': '\u03C1F \u00D7 Crisis 2004',
    'family_connection_ratio_x_crisis_2008': '\u03C1F \u00D7 Crisis 2008',
    'family_connection_ratio_x_crisis_2014': '\u03C1F \u00D7 Crisis 2014',
    'state_ownership_pct_x_crisis_2004': 'SOP \u00D7 Crisis 2004',
    'state_ownership_pct_x_crisis_2008': 'SOP \u00D7 Crisis 2008',
    'state_ownership_pct_x_crisis_2014': 'SOP \u00D7 Crisis 2014',
    'foreign_ownership_total_pct_x_crisis_2004': 'FEC \u00D7 Crisis 2004',
    'foreign_ownership_total_pct_x_crisis_2008': 'FEC \u00D7 Crisis 2008',
    'foreign_ownership_total_pct_x_crisis_2014': 'FEC \u00D7 Crisis 2014',
    'family_connection_ratio_x_governor': '\u03C1F \u00D7 Nabiullina',
    'family_ownership_pct_x_governor': 'FOP \u00D7 Nabiullina',
    'state_ownership_pct_x_governor': 'SOP \u00D7 Nabiullina',
    'foreign_ownership_total_pct_x_governor': 'FEC \u00D7 Nabiullina',
    # Pseudo-crisis interactions (exp_017)
    'family_connection_ratio_x_pseudo_2008': '\u03C1F \u00D7 Pseudo 2008',
    'family_connection_ratio_x_pseudo_2014': '\u03C1F \u00D7 Pseudo 2014',
}

# ---------------------------------------------------------------------------
# Colour palette for models
# ---------------------------------------------------------------------------

MODEL_COLOURS = [
    '#1b9e77',  # teal
    '#d95f02',  # orange
    '#7570b3',  # purple
    '#e7298a',  # pink
    '#66a61e',  # green
    '#e6ab02',  # gold
]

# ---------------------------------------------------------------------------
# Experiment paths
# ---------------------------------------------------------------------------

EXP_010_DIR = BASE_PATH / 'experiments' / 'exp_010_mechanism_testing'
EXP_011_DIR = BASE_PATH / 'experiments' / 'exp_011_subperiod_analysis'
EXP_009_DIR = BASE_PATH / 'experiments' / 'exp_009_crisis_interactions'
EXP_012_DIR = BASE_PATH / 'experiments' / 'exp_012_governor_regimes'
EXP_015_DIR = BASE_PATH / 'experiments' / 'exp_015_granger_causality'
EXP_016_DIR = BASE_PATH / 'experiments' / 'exp_016_competing_risks'
EXP_017_DIR = BASE_PATH / 'experiments' / 'exp_017_placebo_tests'

OUTPUT_DIR = BASE_PATH / 'quarto' / 'figures'


def get_exp010_mechanism_paths() -> dict[str, Path]:
    """M1-M4 mechanism comparison paths."""
    return {
        'M1: Political': EXP_010_DIR / 'summary_M1_Political.csv',
        'M2: Tax': EXP_010_DIR / 'summary_M2_TaxOptimization.csv',
        'M3: Capital': EXP_010_DIR / 'summary_M3_InternalCapital.csv',
        'M4: Full': EXP_010_DIR / 'summary_M4_FullMechanism.csv',
    }


def get_exp010_strata_paths() -> dict[str, Path]:
    """M7-M10 stratification comparison paths."""
    return {
        'M7: Regional': EXP_010_DIR / 'summary_m7.csv',
        'M8: Sector': EXP_010_DIR / 'summary_m8.csv',
        'M9: Community': EXP_010_DIR / 'summary_m9_Community_Strata.csv',
        'M10: Deep': EXP_010_DIR / 'summary_m10_H3_Deep_Proxies.csv',
    }


def get_exp011_baseline_paths() -> dict[str, Path]:
    """Subperiod baseline model paths."""
    base = EXP_011_DIR / 'output'
    return {
        '2004\u20132007': base / '2004_2007' / 'summary_model_1_baseline.csv',
        '2007\u20132013': base / '2007_2013' / 'summary_model_1_baseline.csv',
        '2013\u20132020': base / '2013_2020' / 'summary_model_1_baseline.csv',
    }


def get_exp009_paths() -> dict[str, Path]:
    """Crisis interactions — stargazer column format only."""
    return {
        'coef': EXP_009_DIR / 'stargazer_column.csv',
        'hr': EXP_009_DIR / 'stargazer_hr_column.csv',
    }


def get_exp015_paths() -> dict[str, Path]:
    """Granger causality test — HR stargazer column format."""
    return {
        'M1: Baseline': EXP_015_DIR / 'stargazer_hr_M1_baseline.csv',
        'M2: +Contagion': EXP_015_DIR / 'stargazer_hr_M2_contagion.csv',
        'M4: Pre-2013': EXP_015_DIR / 'stargazer_hr_M4_pre2013.csv',
        'M5: Post-2013': EXP_015_DIR / 'stargazer_hr_M5_post2013.csv',
    }


def get_exp016_paths() -> dict[str, Path]:
    """Competing risks — HR stargazer column format."""
    return {
        'M1: All closures': EXP_016_DIR / 'stargazer_hr_M1_all_closures.csv',
        'M2: Revocation': EXP_016_DIR / 'stargazer_hr_M2_revocation.csv',
        'M3: Voluntary': EXP_016_DIR / 'stargazer_hr_M3_voluntary.csv',
        'M4: Reorganisation': EXP_016_DIR / 'stargazer_hr_M4_reorganisation.csv',
    }


def get_exp017_placebo_paths() -> dict[str, Path]:
    """Placebo tests — HR stargazer column format."""
    return {
        'M1: Real FCR': EXP_017_DIR / 'stargazer_hr_M1_real_FCR.csv',
        'M7: Non-family HHI': EXP_017_DIR / 'stargazer_hr_M7_nonfamily_hhi.csv',
        'M8: Random': EXP_017_DIR / 'stargazer_hr_M8_random.csv',
    }


def get_label(var_name: str) -> str:
    """Get human-readable label for a variable (including interaction terms)."""
    if var_name in VARIABLE_LABELS:
        return VARIABLE_LABELS[var_name]
    if var_name in INTERACTION_LABELS:
        return INTERACTION_LABELS[var_name]
    return var_name


def get_group(var_name: str) -> str:
    """Get variable group (including interaction terms assigned to 'Interaction')."""
    if var_name in VARIABLE_GROUPS:
        return VARIABLE_GROUPS[var_name]
    if '_x_' in var_name:
        return 'Interaction'
    return 'Other'
