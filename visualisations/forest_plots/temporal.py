"""Forest plot: exp_011 subperiod evolution (2004-07, 2007-13, 2013-20)."""

from .config import get_exp011_baseline_paths
from .data import load_experiment
from .plot import forest_plot


def get_data(scale: str = 'hr'):
    paths = get_exp011_baseline_paths()
    return load_experiment(paths, scale=scale)


def create_plot(scale: str = 'hr', **kwargs):
    """Create temporal evolution forest plot.

    Shows baseline model coefficients across three subperiods to
    highlight the foreign ownership reversal and family effect evolution.
    """
    data = get_data(scale=scale)
    defaults = dict(
        title='Temporal Evolution of Effects (Subperiod Analysis)',
        note='Baseline model (M1) from exp_011 across three subperiods.',
    )
    defaults.update(kwargs)
    return forest_plot(data, scale=scale, **defaults)
