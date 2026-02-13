"""Forest plot: exp_009 crisis interaction effects."""

import pandas as pd

from .config import get_exp009_paths
from .data import load_stargazer_column
from .config import get_group, get_label, VARIABLE_ORDER
from .plot import forest_plot


def get_data(scale: str = 'hr'):
    """Load exp_009 crisis interactions from stargazer column CSVs.

    Returns two DataFrames: base effects and interaction terms,
    combined for plotting with separate facets.
    """
    paths = get_exp009_paths()
    path = paths['hr'] if scale == 'hr' else paths['coef']
    data = load_stargazer_column(path, model_name='M6: Full Interactions', scale=scale)

    # Add variable_group and variable_label
    data['variable_group'] = data['covariate'].map(get_group)
    data['variable_label'] = data['covariate'].map(get_label)

    # Sort
    order_map = {v: i for i, v in enumerate(VARIABLE_ORDER)}
    # Interaction terms go after base effects
    data['_sort'] = data['covariate'].map(lambda v: order_map.get(v, 500))
    data = data.sort_values('_sort').drop(columns='_sort').reset_index(drop=True)

    return data


def create_plot(scale: str = 'hr', interactions_only: bool = False, **kwargs):
    """Create crisis interactions forest plot.

    Parameters
    ----------
    scale : 'hr' or 'coef'
    interactions_only : if True, show only the interaction terms (ownership x crisis)
    """
    data = get_data(scale=scale)
    if interactions_only:
        data = data[data['variable_group'] == 'Interaction'].reset_index(drop=True)

    defaults = dict(
        title='Crisis Interaction Effects',
        note='Full interactions model (M6) from exp_009 (2004\u20132021).',
        dodge_width=0.0,  # Single model, no dodging needed
    )
    defaults.update(kwargs)
    return forest_plot(data, scale=scale, **defaults)
