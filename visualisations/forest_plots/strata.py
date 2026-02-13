"""Forest plot: exp_010 stratification comparison (M7-M10)."""

from .config import get_exp010_strata_paths
from .data import load_experiment
from .plot import forest_plot


def get_data(scale: str = 'hr'):
    paths = get_exp010_strata_paths()
    return load_experiment(paths, scale=scale)


def create_plot(scale: str = 'hr', **kwargs):
    """Create stratification comparison forest plot.

    Shows M7 Regional, M8 Sector, M9 Community, M10 Deep Proxies
    to demonstrate why community stratification yields the best fit.
    """
    data = get_data(scale=scale)
    defaults = dict(
        title='Stratification Comparison (M7\u2013M10)',
        note='Models M7\u2013M10 from exp_010 (2004\u20132020). M9 community strata has lowest AIC.',
    )
    defaults.update(kwargs)
    return forest_plot(data, scale=scale, **defaults)
