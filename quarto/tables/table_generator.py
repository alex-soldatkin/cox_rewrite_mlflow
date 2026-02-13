"""
Table generation utilities for the Quarto master document.

Reads experiment CSV outputs (summary, stargazer column, stargazer wide format)
and produces formatted markdown tables for Quarto/Typst rendering.
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path

# Base path for experiment outputs (relative to quarto/ directory)
BASE_PATH = Path(__file__).parent.parent.parent


def read_summary_csv(path: str) -> pd.DataFrame:
    """
    Read a lifelines summary CSV (long format).

    Columns: covariate, coef, exp(coef), se(coef), coef lower 95%,
             coef upper 95%, exp(coef) lower 95%, exp(coef) upper 95%,
             cmp to, z, p, -log2(p)
    """
    df = pd.read_csv(path)
    return df


def read_stargazer_column(path: str) -> pd.DataFrame:
    """
    Read a stargazer column CSV (2-column format: variable, Stargazer_Output).

    Values are formatted as 'coef*** (se)' for variables
    and plain numbers for summary statistics.
    """
    df = pd.read_csv(path)
    return df


def read_stargazer_wide(path: str) -> pd.DataFrame:
    """
    Read a wide-format stargazer CSV (aggregated across models).

    First column: variable names
    Remaining columns: model-specific 'coef*** (se)' or 'HR*** (se)' values
    """
    df = pd.read_csv(path, index_col=0)
    return df


def parse_stargazer_value(val: str) -> dict:
    """
    Parse a stargazer-formatted value like '-0.070** (0.024)' into components.

    Returns dict with keys: coef, se, stars, significant
    """
    if pd.isna(val) or val == '' or val == 'nan':
        return {'coef': np.nan, 'se': np.nan, 'stars': '', 'significant': False}

    val = str(val).strip()

    # Try to parse as plain number (summary stats rows)
    try:
        return {'coef': float(val), 'se': np.nan, 'stars': '', 'significant': False}
    except ValueError:
        pass

    # Parse formatted value: 'coef*** (se)'
    pattern = r'^(-?[\d.]+(?:e[+-]?\d+)?)\s*(\*{1,3}|\+)?\s*\(([^)]+)\)$'
    match = re.match(pattern, val)
    if match:
        coef = float(match.group(1))
        stars = match.group(2) or ''
        se = float(match.group(3))
        return {
            'coef': coef,
            'se': se,
            'stars': stars,
            'significant': len(stars) > 0
        }

    return {'coef': np.nan, 'se': np.nan, 'stars': '', 'significant': False}


def significance_stars(p_value: float) -> str:
    """Convert p-value to significance stars."""
    if pd.isna(p_value):
        return ''
    if p_value < 0.001:
        return '***'
    if p_value < 0.01:
        return '**'
    if p_value < 0.05:
        return '*'
    if p_value < 0.10:
        return '+'
    return ''


def format_coef_se(coef: float, se: float, p: float, decimals: int = 3) -> str:
    """Format coefficient with significance stars and standard error."""
    if pd.isna(coef):
        return ''
    stars = significance_stars(p)
    return f'{coef:.{decimals}f}{stars} ({se:.{decimals}f})'


def format_hr_se(hr: float, se: float, p: float, decimals: int = 3) -> str:
    """Format hazard ratio with significance stars and standard error."""
    if pd.isna(hr):
        return ''
    stars = significance_stars(p)
    return f'{hr:.{decimals}f}{stars} ({se:.{decimals}f})'


# === Variable name mappings ===

VARIABLE_LABELS = {
    'family_connection_ratio': 'Family connection ratio ($\\rho_F$)',
    'family_connection_ratio_temporal_lag': 'Family connection ratio (lagged)',
    'family_ownership_pct': 'Family ownership (%)',
    'family_FOP': 'Family ownership (%)',
    'state_ownership_pct': 'State ownership (%)',
    'foreign_ownership_total_pct': 'Foreign ownership (%)',
    'camel_roa': 'Return on assets',
    'camel_npl_ratio': 'Non-performing loan ratio',
    'camel_tier1_capital_ratio': 'Tier 1 capital ratio',
    'camel_liquid_assets_ratio': 'Liquid assets ratio',
    'rw_page_rank_4q_lag': 'PageRank (4Q lag)',
    'rw_out_degree_4q_lag': 'Out-degree (4Q lag)',
    'network_page_rank': 'PageRank',
    'network_out_degree': 'Out-degree',
    'network_in_degree': 'In-degree',
    'network_betweenness': 'Betweenness centrality',
    'network_C_b': 'Clustering coefficient',
    'stake_fragmentation_index': 'Stake fragmentation index',
    'family_company_count': 'Family company count',
    'group_total_capital': 'Group total capital',
    'group_sector_count': 'Group sector count',
    'group_total_paid_tax': 'Group total paid tax',
    'group_total_vehicles': 'Group total vehicles',
    'epu_index': 'EPU index',
    'governor_nabiullina': 'Nabiullina era',
    'crisis_2004': 'Crisis 2004',
    'crisis_2008': 'Crisis 2008',
    'crisis_2014': 'Crisis 2014',
}


TABLE_LABELS = {
    'family_connection_ratio': 'Family connection ratio',
    'family_connection_ratio_temporal_lag': 'Family connection ratio (lagged)',
    'family_ownership_pct': 'Family ownership (%)',
    'family_FOP': 'Family ownership (%)',
    'state_ownership_pct': 'State ownership (%)',
    'foreign_ownership_total_pct': 'Foreign ownership (%)',
    'camel_roa': 'ROA',
    'camel_npl_ratio': 'NPL ratio',
    'camel_tier1_capital_ratio': 'Tier 1 capital ratio',
    'camel_liquid_assets_ratio': 'Liquid assets ratio',
    'rw_page_rank_4q_lag': 'PageRank (4Q lag)',
    'rw_out_degree_4q_lag': 'Out-degree (4Q lag)',
    'network_page_rank': 'PageRank',
    'network_out_degree': 'Out-degree',
    'network_in_degree': 'In-degree',
    'network_betweenness': 'Betweenness centrality',
    'network_C_b': 'Clustering coefficient',
    'stake_fragmentation_index': 'Stake fragmentation index',
    'family_company_count': 'Family company count',
    'group_total_capital': 'Group total capital',
    'group_sector_count': 'Group sector count',
    'group_total_paid_tax': 'Group total paid tax',
    'group_total_vehicles': 'Group total vehicles',
    'group_total_receipts': 'Group total receipts',
    'epu_index': 'EPU index',
    'governor_nabiullina': 'Nabiullina era',
    'crisis_2004': 'Crisis 2004',
    'crisis_2008': 'Crisis 2008',
    'crisis_2014': 'Crisis 2014',
    'community_failure_lag': 'Community failure lag',
    'nonfamily_ownership_hhi': 'Non-family ownership HHI',
    'random_ownership': 'Random ownership (noise)',
    'pseudo_2008': 'Pseudo-crisis 2008',
    'pseudo_2014': 'Pseudo-crisis 2014',
    'family_connection_ratio_x_crisis_2008': 'FCR $\\times$ Crisis 2008',
    'family_connection_ratio_x_crisis_2014': 'FCR $\\times$ Crisis 2014',
    'family_connection_ratio_x_pseudo_2008': 'FCR $\\times$ Pseudo 2008',
    'family_connection_ratio_x_pseudo_2014': 'FCR $\\times$ Pseudo 2014',
}


def label_variable(var_name: str) -> str:
    """Get human-readable label for a variable name."""
    return VARIABLE_LABELS.get(var_name, var_name)


def fmt_cell(val):
    """Format a stargazer CSV cell for markdown output.

    Escapes asterisks and uses Unicode minus for negative values.
    """
    if pd.isna(val) or str(val).strip() in ('', 'nan'):
        return '--'
    s = str(val).strip()
    s = re.sub(r'\*+', lambda m: '\\*' * len(m.group(0)), s)
    if s.startswith('-'):
        s = '\u2212' + s[1:]
    return s


def fmt_hr(exp_coef, p_val, decimals=3):
    """Format a hazard ratio with escaped significance stars."""
    if pd.isna(exp_coef):
        return '--'
    stars = ''
    if p_val < 0.001:
        stars = '\\*\\*\\*'
    elif p_val < 0.01:
        stars = '\\*\\*'
    elif p_val < 0.05:
        stars = '\\*'
    elif p_val < 0.10:
        stars = '+'
    return f'{exp_coef:.{decimals}f}{stars}'


def fmt_stat(var, val):
    """Format a model fit statistic for table display."""
    if pd.isna(val) or str(val).strip() in ('', 'nan'):
        return ''
    v = float(val)
    if var in ('Observations', 'Subjects', 'Events'):
        return f'{int(v):,}'
    elif var == 'Log Likelihood':
        return f'\u2212{abs(v):,.2f}' if v < 0 else f'{v:,.2f}'
    elif var in ('AIC Partial', 'AIC'):
        return f'{v:,.2f}'
    elif var == 'C-index':
        return f'{v:.3f}'
    return str(val)


def to_quarto_table(df, caption, label):
    """Convert a DataFrame to a Quarto markdown table with caption and label.

    Uses to_markdown() for the table body and adds a Quarto-compatible
    caption line with cross-reference label.
    """
    md = df.to_markdown(index=False)
    return f'{md}\n\n: {caption} {{#{label}}}'


# === Table builders ===

def build_mechanism_table(
    model_paths: dict[str, str],
    use_hr: bool = True,
    decimals: int = 3
) -> pd.DataFrame:
    """
    Build a combined regression table from multiple model summary CSVs.

    Args:
        model_paths: dict mapping model names to CSV file paths
        use_hr: if True, show exp(coef) (hazard ratios); otherwise raw coefficients
        decimals: number of decimal places

    Returns:
        DataFrame with variables as rows, models as columns
    """
    all_vars = []
    model_data = {}

    for model_name, path in model_paths.items():
        df = read_summary_csv(path)
        coef_col = 'exp(coef)' if use_hr else 'coef'
        se_col = 'se(coef)'

        formatted = {}
        for _, row in df.iterrows():
            var = row['covariate']
            if var not in all_vars:
                all_vars.append(var)
            formatted[var] = format_coef_se(
                row[coef_col], row[se_col], row['p'], decimals
            ) if use_hr else format_coef_se(
                row['coef'], row[se_col], row['p'], decimals
            )

        model_data[model_name] = formatted

    # Build output DataFrame
    result = pd.DataFrame(index=all_vars)
    for model_name, data in model_data.items():
        result[model_name] = result.index.map(lambda v, d=data: d.get(v, ''))

    result.index = result.index.map(label_variable)
    return result


def build_subperiod_comparison(
    period_paths: dict[str, str],
    variable_subset: list[str] = None,
    use_hr: bool = True,
    decimals: int = 3
) -> pd.DataFrame:
    """
    Build a table comparing coefficients across subperiods.

    Args:
        period_paths: dict mapping period labels to summary CSV paths
        variable_subset: optional list of variables to include
        use_hr: if True, show hazard ratios
        decimals: number of decimal places
    """
    period_data = {}

    for period_label, path in period_paths.items():
        df = read_summary_csv(path)
        if variable_subset:
            df = df[df['covariate'].isin(variable_subset)]

        coef_col = 'exp(coef)' if use_hr else 'coef'
        formatted = {}
        for _, row in df.iterrows():
            formatted[row['covariate']] = format_coef_se(
                row[coef_col], row['se(coef)'], row['p'], decimals
            ) if use_hr else format_coef_se(
                row['coef'], row['se(coef)'], row['p'], decimals
            )

        period_data[period_label] = formatted

    all_vars = variable_subset or list(
        set().union(*[d.keys() for d in period_data.values()])
    )

    result = pd.DataFrame(index=all_vars)
    for period_label, data in period_data.items():
        result[period_label] = result.index.map(lambda v, d=data: d.get(v, ''))

    result.index = result.index.map(label_variable)
    return result


def df_to_markdown(df: pd.DataFrame, caption: str = '') -> str:
    """Convert a DataFrame to a markdown table string."""
    lines = []
    if caption:
        lines.append(f': {caption}' + ' {#tbl-auto}')
        lines.append('')

    # Header
    header = '| Variable | ' + ' | '.join(df.columns) + ' |'
    separator = '|:---|' + '|'.join([':---'] * len(df.columns)) + '|'
    lines.append(header)
    lines.append(separator)

    # Rows
    for idx, row in df.iterrows():
        cells = ' | '.join(str(v) for v in row.values)
        lines.append(f'| {idx} | {cells} |')

    return '\n'.join(lines)


# === Convenience functions for specific experiments ===

def get_exp010_paths() -> dict:
    """Get paths to exp_010 mechanism testing summary CSVs."""
    base = BASE_PATH / 'experiments' / 'exp_010_mechanism_testing'
    return {
        'M1: Political': base / 'summary_M1_Political.csv',
        'M2: Tax': base / 'summary_M2_Tax_Optimization.csv',
        'M3: Capital': base / 'summary_M3_Internal_Capital.csv',
        'M4: Full': base / 'summary_M4_Full_Mechanism.csv',
        'M7: H3+': base / 'summary_m7.csv',
        'M9: Community': base / 'summary_m9.csv',
        'M10: Deep': base / 'summary_m10_H3_Deep_Proxies.csv',
    }


def get_exp011_baseline_paths() -> dict:
    """Get paths to exp_011 subperiod baseline summary CSVs."""
    base = BASE_PATH / 'experiments' / 'exp_011_subperiod_analysis' / 'output'
    return {
        '2004--2007': base / '2004_2007' / 'summary_model_1_baseline.csv',
        '2007--2013': base / '2007_2013' / 'summary_model_1_baseline.csv',
        '2013--2020': base / '2013_2020' / 'summary_model_1_baseline.csv',
    }
