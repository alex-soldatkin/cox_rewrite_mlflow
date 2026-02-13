"""Forest plot: exp_015 Granger causality test (M1, M2, M4, M5)."""

from .config import get_exp015_paths
from .data import load_experiment
from .plot import forest_plot


def get_data(scale: str = 'hr'):
    paths = get_exp015_paths()
    return load_experiment(paths, scale=scale)


def create_plot(scale: str = 'hr', **kwargs):
    """Create Granger causality forest plot.

    Shows M1 Baseline, M2 +Contagion, M4 Pre-2013, M5 Post-2013
    to demonstrate that FCR Granger-causes survival after controlling
    for community failure contagion.
    """
    data = get_data(scale=scale)
    defaults = dict(
        title='Granger Causality Test (exp_015)',
        note='Complementary log-log discrete-time hazard. Exponentiated coefficients \u2248 HRs.',
    )
    defaults.update(kwargs)
    return forest_plot(data, scale=scale, **defaults)
