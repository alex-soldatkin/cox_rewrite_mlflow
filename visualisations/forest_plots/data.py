"""Unified data loading for forest plots.

Handles two CSV formats:
- Summary CSVs (lifelines output): covariate, coef, exp(coef), se(coef), CIs, z, p
- Stargazer column CSVs: variable, Stargazer_Output ('coef*** (se)' format)
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

from .config import VARIABLE_ORDER, get_group, get_label

# Summary statistics rows to exclude from stargazer CSVs
_STATS_ROWS = {
    'Observations', 'Subjects', 'Events', 'Log Likelihood',
    'AIC Partial', 'AIC', '-log2(p) LLR', 'C-index',
}


def _significance_stars(p_value: float) -> str:
    if pd.isna(p_value):
        return ''
    if p_value < 0.001:
        return '***'
    if p_value < 0.01:
        return '**'
    if p_value < 0.05:
        return '*'
    if p_value < 0.10:
        return '\u2020'
    return ''


def _parse_stargazer_value(val: str) -> dict:
    """Parse 'coef*** (se)' into components."""
    if pd.isna(val) or str(val).strip() in ('', 'nan'):
        return {'coef': np.nan, 'se': np.nan, 'stars': ''}
    val = str(val).strip()
    pattern = r'^(-?[\d.]+(?:e[+-]?\d+)?)\s*(\*{1,3}|\+)?\s*\(([^)]+)\)$'
    match = re.match(pattern, val)
    if match:
        return {
            'coef': float(match.group(1)),
            'se': float(match.group(3)),
            'stars': match.group(2) or '',
        }
    return {'coef': np.nan, 'se': np.nan, 'stars': ''}


def load_summary_csv(path: str | Path, model_name: str, scale: str = 'hr') -> pd.DataFrame:
    """Load a lifelines summary CSV into the standard forest-plot schema.

    Parameters
    ----------
    path : path to summary CSV
    model_name : label for this model (used in dodge / legend)
    scale : 'hr' for hazard ratios, 'coef' for log-hazard coefficients

    Returns
    -------
    DataFrame with columns: covariate, estimate, se, ci_lower, ci_upper, p, stars, model_name
    """
    df = pd.read_csv(path)
    if scale == 'hr':
        out = pd.DataFrame({
            'covariate': df['covariate'],
            'estimate': df['exp(coef)'],
            'se': df['se(coef)'],
            'ci_lower': df['exp(coef) lower 95%'],
            'ci_upper': df['exp(coef) upper 95%'],
            'p': df['p'],
            'stars': df['p'].apply(_significance_stars),
            'model_name': model_name,
        })
    else:
        out = pd.DataFrame({
            'covariate': df['covariate'],
            'estimate': df['coef'],
            'se': df['se(coef)'],
            'ci_lower': df['coef lower 95%'],
            'ci_upper': df['coef upper 95%'],
            'p': df['p'],
            'stars': df['p'].apply(_significance_stars),
            'model_name': model_name,
        })
    return out


def load_stargazer_column(
    path: str | Path, model_name: str, scale: str = 'coef',
) -> pd.DataFrame:
    """Load a stargazer column CSV (variable, Stargazer_Output) into standard schema.

    CIs are computed as estimate +/- 1.96*se.  For HR-format files the
    estimate is already exponentiated; CIs are computed on the HR scale.
    """
    raw = pd.read_csv(path)
    col = 'Stargazer_Output' if 'Stargazer_Output' in raw.columns else raw.columns[1]
    # Filter out summary statistic rows
    raw = raw[~raw['variable'].isin(_STATS_ROWS)].copy()

    parsed = raw[col].apply(_parse_stargazer_value).apply(pd.Series)
    out = pd.DataFrame({
        'covariate': raw['variable'].values,
        'estimate': parsed['coef'].values,
        'se': parsed['se'].values,
        'ci_lower': (parsed['coef'] - 1.96 * parsed['se']).values,
        'ci_upper': (parsed['coef'] + 1.96 * parsed['se']).values,
        'p': np.nan,
        'stars': parsed['stars'].values,
        'model_name': model_name,
    })
    # Replace '+' with dagger for consistency
    out['stars'] = out['stars'].replace({'+': '\u2020'})

    if scale == 'hr' and 'HR' not in col:
        # Exponentiate if raw coefficients but HR scale requested
        out['ci_lower'] = np.exp(out['ci_lower'])
        out['ci_upper'] = np.exp(out['ci_upper'])
        out['estimate'] = np.exp(out['estimate'])

    return out.dropna(subset=['estimate']).reset_index(drop=True)


def load_experiment(
    model_paths: dict[str, str | Path],
    scale: str = 'hr',
) -> pd.DataFrame:
    """Load multiple models, auto-detecting CSV format.

    Adds variable_group, variable_label, and a categorical sort order.
    """
    frames = []
    for model_name, path in model_paths.items():
        path = Path(path)
        # Auto-detect format: summary CSVs have 'covariate' as first column
        sample = pd.read_csv(path, nrows=1)
        if 'covariate' in sample.columns:
            df = load_summary_csv(path, model_name, scale=scale)
        else:
            df = load_stargazer_column(path, model_name, scale=scale)
        frames.append(df)

    data = pd.concat(frames, ignore_index=True)
    data['variable_group'] = data['covariate'].map(get_group)
    data['variable_label'] = data['covariate'].map(get_label)

    # Sort: respect VARIABLE_ORDER for known variables, append unknowns at end
    order_map = {v: i for i, v in enumerate(VARIABLE_ORDER)}
    data['_sort'] = data['covariate'].map(lambda v: order_map.get(v, 999))
    data = data.sort_values(['_sort', 'model_name']).drop(columns='_sort')

    return data.reset_index(drop=True)
