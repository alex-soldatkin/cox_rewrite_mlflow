"""Forest plot: exp_016 competing risks — cause-specific Cox models."""

from .config import get_exp016_paths
from .data import load_experiment
from .plot import forest_plot


def get_data(scale: str = 'hr'):
    paths = get_exp016_paths()
    return load_experiment(paths, scale=scale)


def create_plot(scale: str = 'hr', **kwargs):
    """Create competing risks forest plot.

    Shows M1 All closures, M2 Revocation, M3 Voluntary, M4 Reorganisation
    side-by-side, demonstrating that FCR is protective against forced
    revocation only.
    """
    data = get_data(scale=scale)
    defaults = dict(
        title='Competing Risks: Cause-Specific Cox (exp_016)',
        note='Cox time-varying models. Other closure types censored in cause-specific models.',
    )
    defaults.update(kwargs)
    return forest_plot(data, scale=scale, **defaults)
