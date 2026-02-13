"""Forest plot: exp_010 mechanism comparison (M1-M4)."""

from .config import get_exp010_mechanism_paths
from .data import load_experiment
from .plot import forest_plot


def get_data(scale: str = 'hr'):
    paths = get_exp010_mechanism_paths()
    return load_experiment(paths, scale=scale)


def create_plot(scale: str = 'hr', **kwargs):
    """Create mechanism comparison forest plot.

    Shows M1 Political, M2 Tax, M3 Capital, M4 Full side-by-side
    to illustrate independent contributions of each TCE mechanism.
    """
    data = get_data(scale=scale)
    defaults = dict(
        title='Mechanism Comparison (M1\u2013M4)',
        note='Models M1\u2013M4 from exp_010 (2004\u20132020, community stratification).',
    )
    defaults.update(kwargs)
    return forest_plot(data, scale=scale, **defaults)
