"""Generate all forest plots for the Quarto document.

Usage:
    uv run visualisations/forest_plots/generate.py [--scale hr|coef] [--format png|svg|both]
"""

import argparse
import sys
from pathlib import Path

from lets_plot import LetsPlot
from lets_plot.export import ggsave

from . import mechanism, temporal, crisis, strata, granger, competing_risks, placebo
from .config import OUTPUT_DIR

LetsPlot.setup_html()


PLOTS = {
    'forest_mechanism_comparison': mechanism.create_plot,
    'forest_temporal_evolution': temporal.create_plot,
    'forest_crisis_interactions': lambda **kw: crisis.create_plot(interactions_only=False, **kw),
    'forest_stratification_comparison': strata.create_plot,
    'forest_granger': granger.create_plot,
    'forest_competing_risks': competing_risks.create_plot,
    'forest_placebo': placebo.create_plot,
}


def main():
    parser = argparse.ArgumentParser(description='Generate forest plots for Quarto.')
    parser.add_argument(
        '--scale', choices=['hr', 'coef'], default='hr',
        help='Scale: hr (hazard ratios, ref=1) or coef (log-hazard, ref=0).',
    )
    parser.add_argument(
        '--format', choices=['png', 'svg', 'both'], default='png',
        help='Output format.',
    )
    parser.add_argument(
        '--only', nargs='*', choices=list(PLOTS.keys()),
        help='Generate only specific plots.',
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    targets = args.only if args.only else list(PLOTS.keys())
    formats = ['png', 'svg'] if args.format == 'both' else [args.format]

    for name in targets:
        print(f'Generating {name} (scale={args.scale})...')
        plot_fn = PLOTS[name]
        p = plot_fn(scale=args.scale)

        for fmt in formats:
            out_path = OUTPUT_DIR / f'{name}.{fmt}'
            ggsave(p, filename=out_path.name, path=str(out_path.parent))
            print(f'  Saved: {out_path}')

    print('Done.')


if __name__ == '__main__':
    main()
