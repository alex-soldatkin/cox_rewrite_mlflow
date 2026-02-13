"""Forest plot: exp_017 placebo / falsification tests."""

from .config import get_exp017_placebo_paths
from .data import load_experiment
from .plot import forest_plot


def get_data(scale: str = 'hr'):
    paths = get_exp017_placebo_paths()
    return load_experiment(paths, scale=scale)


def create_plot(scale: str = 'hr', **kwargs):
    """Create placebo test forest plot.

    Shows M1 Real FCR vs M7 Non-family HHI vs M8 Random ownership,
    demonstrating that the protective effect is specific to family
    connections and not generic ownership concentration.
    """
    data = get_data(scale=scale)
    defaults = dict(
        title='Placebo Tests (exp_017)',
        note='Cox time-varying models. Non-family HHI and random ownership replace FCR.',
    )
    defaults.update(kwargs)
    return forest_plot(data, scale=scale, **defaults)
