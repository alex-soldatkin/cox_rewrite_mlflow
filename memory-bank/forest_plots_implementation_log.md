# Forest Plots Implementation Log

**Date**: 2026-02-13
**Tool**: lets_plot v4.8.2 (Python)
**Environment**: uv (PEP 723 managed)

## Files Touched

### Visualisation Module (`visualisations/forest_plots/`)

| File | Role |
|:---|:---|
| `__init__.py` | Package init |
| `config.py` | Variable labels (Unicode), group ordering, model colours, experiment paths |
| `data.py` | CSV loaders: `load_summary_csv()`, `load_stargazer_column()`, `load_experiment()` |
| `plot.py` | **Core builder**: manual numeric y positions, dodge, background shading, broken dividers |
| `mechanism.py` | exp_010 M1--M4 mechanism comparison |
| `temporal.py` | exp_011 subperiod evolution (3 periods) |
| `crisis.py` | exp_009 crisis interactions (M6 full model) |
| `strata.py` | exp_010 M7--M10 stratification comparison |
| `generate.py` | CLI entry point: `uv run python -m visualisations.forest_plots.generate` |

### Generated Figures (`quarto/figures/`)

| File | Source Experiment | Models |
|:---|:---|:---|
| `forest_mechanism_comparison.{png,svg}` | exp_010 | M1--M4 |
| `forest_stratification_comparison.{png,svg}` | exp_010 | M7--M10 |
| `forest_temporal_evolution.{png,svg}` | exp_011 | M1 × 3 subperiods |
| `forest_crisis_interactions.{png,svg}` | exp_009 | M6 full interactions |

### Quarto Results Modules

| File | Figure Label | Inline Reference |
|:---|:---|:---|
| `results-exp010-mechanisms.qmd` | `@fig-forest-mechanisms` | After @tbl-mechanism-main |
| `results-exp010-mechanisms.qmd` | `@fig-forest-stratification` | After @tbl-mechanism-summary-exp010 |
| `results-exp011-subperiods.qmd` | `@fig-forest-temporal` | After @tbl-subperiod-baseline |
| `results-exp009-crises.qmd` | `@fig-forest-crisis` | After @tbl-crisis-episodes |

## lets_plot Best Practices (Forest Plots)

### 1. Never put `group` in base `aes()`
The `group` aesthetic in a base `ggplot(aes(group=...))` is inherited by **all** layers, including `geom_vline`. Since `geom_vline` uses its own constant data (just `xintercept`), it cannot resolve the group variable, producing a silent 198-byte error SVG with `Variable not found: 'model_name'. Variables in data frame: []`. **Fix**: pass `group` only to geoms that need it.

### 2. Use manual numeric y positions, not categorical axes
`position_dodge` coordinates poorly across `geom_errorbar`, `geom_point`, and `geom_text` in lets_plot---dots end up misaligned with CI bars. **Fix**: compute numeric y positions manually and use `geom_segment` (for CIs) + `geom_point` (for estimates) sharing the exact same `y_dodge` column. This guarantees pixel-perfect alignment.

### 3. `geom_segment` > `geom_errorbar` for CIs
`geom_segment(aes(x='ci_lower', xend='ci_upper', y='y', yend='y'))` gives cleaner horizontal CI lines than `geom_errorbar`, which adds whiskers and complicates dodge alignment.

### 4. `scale_y_discrete(limits=...)` breaks `free_y` faceting
Setting `limits` on a discrete y-axis forces all labels into every facet panel, defeating `facet_grid(scales='free_y')`. **Fix**: use `pd.Categorical` on the data itself for ordering.

### 5. lets_plot does not render LaTeX in labels
`\rho_F`, `C_{out}`, `\times` all render as literal text. **Fix**: use Unicode: ρ (U+03C1), × (U+00D7), subscripts via plain text (Cout, etc.).

### 6. Broken divider lines around group labels
`geom_hline` cannot have gaps. **Fix**: use two `geom_segment` pieces per divider, computing a gap proportional to label text length:
```python
gap_half = max(len(group) * x_span * 0.011, x_span * 0.04)
```

### 7. Background shading by protectiveness
Use `geom_rect` with `scale_fill_gradient2(low='#E53935', mid='#FAFAFA', high='#43A047', midpoint=0)`. Compute protectiveness as `-(mean_estimate - ref_line)` so that HR < 1 (protective) maps to green and HR > 1 (harmful) maps to red.

### 8. Star placement
Position significance stars at `ci_upper + nudge` with `hjust=0` to place them just right of each CI, avoiding overlap with the CI line or estimate point.

## Errors Encountered and Fixes

| Error | Root Cause | Fix |
|:---|:---|:---|
| 198-byte error SVG: `Variable not found: 'model_name'` | `group` in base `aes()` inherited by `geom_vline` | Move `group` to individual geoms |
| All facet panels show all y-labels | `scale_y_discrete(limits=...)` overrides `free_y` | Use `pd.Categorical` ordering |
| LaTeX labels render as literal text | lets_plot has no LaTeX renderer | Replace with Unicode characters |
| Dots misaligned with CI bars | `position_dodge` inconsistent across geom types | Manual numeric y + shared `y_dodge` column |
| Divider lines cross through group labels | `geom_hline` has no gap mechanism | Two `geom_segment` pieces with computed gap |
| First group missing divider | `if gi > 0` guard skipped first group | Remove the guard |

## CLI Usage

```bash
# Generate all plots in both PNG and SVG
uv run python -m visualisations.forest_plots.generate --scale hr --format both

# Generate a single plot
uv run python -m visualisations.forest_plots.generate --plots mechanism --scale hr --format png
```

Output directory: `quarto/figures/`
