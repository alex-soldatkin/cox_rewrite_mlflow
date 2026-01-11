# Lets-Plot Usage Notes (project-specific)

Practical guidance distilled from the visualisations implemented in this repo. Focused on the Python API, HTML outputs, and the quirks we hit.

## Environment & Runtime
- Use `python3` with `PYTHONPATH=.` so modules under `visualisations/` import correctly.
- To avoid matplotlib/font cache errors on macOS sandboxes, set `MPLCONFIGDIR=.mplconfig` and `XDG_CACHE_HOME=.cache` when running scripts.
- Save HTML via `ggsave(plot, filename=...)` (Lets-Plot does not expose `plot.save()` in Python).
- Install `lets-plot` with `pip --user --break-system-packages` if PEP 668 blocks system installs.

## Shared preprocessing
- Common derivations live in `visualisations/preprocessing/__init__.py`: date parsing, event selection, age calculations, geo extraction, and a lightweight Kaplan–Meier helper.
- Always call `enrich(load_asv())` to get consistent columns: `register_date`, `event_date`, `event_type`, `status_group`, `lat/lon`, `ssv_participant`, `sanitising_flag`, etc.

## Visual patterns that worked

### Survival (stacked_survival_curves.py)
- `geom_step` for Kaplan–Meier survival curves; ribbons for 95% CI via `geom_ribbon`.
- Group aesthetics: `color` for SSV membership, `linetype` for licence status; combine labels into a group to keep lines distinct.
- Keep `surv` bounded `[0,1]` with `scale_y_continuous(limits=[0,1])`.

### Age at event (event_age_scatter.py)
- Scatter with slight `position_jitter` to reduce overlap; shapes for SSV; colors for `event_type`.
- LOESS via `geom_smooth` caused unequal series errors; replaced with precomputed medians per year/event and `geom_line`.

### Density by cohort (event_density_ridges.py)
- Lets-Plot lacks `geom_density_ridges`; use faceted `geom_density` instead.
- Add cohort medians via `geom_vline` on the faceted plot.

### Cumulative flow (cumulative_flow.py)
- `geom_area` stacked by `status_group` for cumulative events; overlay `geom_line` for active stock.
- Compute exits first (revoked/annulled) to derive remaining active banks.

### Licence/status mosaic (licence_status_mosaic.py)
- Use `geom_tile` with `geom_text` labels for percentages. `scale_fill_gradient` highlights risk differences.
- Prepare categorical labels in advance (e.g., “Deposit licence” / “No deposit licence”).

### Sanitation timeline (sanitation_timeline.py)
- Avoid `reorder()` inside aesthetics (not supported); instead pre-build an ordered categorical.
- `geom_segment` for duration, start/end points with shapes and colors for outcome.

### Calendar heatmap + trend (calendar_heatmap_trend.py)
- Monthly counts via `geom_tile`; overlay `geom_point` with size mapped to rolling mean (`scale_size`).
- Use `Period` to month-bucket dates, then roll 3-month average per status.

### Spatial map with clustering (spatial_revocation_intensity.py)
- Base map: `geom_livemap(maptiles=maptiles_lets_plot(), location=[minLon, minLat, maxLon, maxLat])`.
- Heat layer: aggregate lat/lon into bins, build square polygons, render with `geom_map` (requires `map` DataFrame with vertices + `map_id`).
- Points: `geom_point` on top, small size (≈1.4) and semi-transparent to reduce overlap.
- Color scheme via `scale_color_manual` (active=green, revoked=red, annulled=grey, sanitising/sanitised=teal).
- Tooltips: `layer_tooltips().title("@asv_name").line("REGN: @asv_orgInfo_regn").line("Registered: @{register_date|%Y-%m-%d}") ...` to format dates; add sanitation/SSV flags.

## Things that did **not** work
- `geom_density_ridges` is unavailable in Lets-Plot Python; attempting it raises `NameError`.
- `plot.save(...)` doesn’t exist; must use `ggsave`.
- `reorder(var, other)` inside aesthetics is not supported; ordering must be precomputed.
- Using `geom_smooth(method='loess')` on grouped scatter triggered “All data series ... must have equal size”; pre-aggregate instead.
- `maptiles_openstreetmap` import isn’t exposed; use `maptiles_lets_plot`, `maptiles_solid`, or `maptiles_zxy`.
- Geo shapes via `lets_plot.geo_data` require `geopandas`; not available offline—hence manual bin polygons were used.
- `layer_labels().color(...)` isn’t supported; set text color via `theme(label_text=element_text(color=...))`.
- When a layer uses `fill` for one semantic (e.g., status) and tiles use `fill` for another (e.g., federal district), you must give `scale_fill_manual` a merged palette covering both sets of categories, otherwise the district colors will default to status colors. Use a separate `scale_color_manual` (or a stub layer) to expose the district legend while keeping pie fills for status.

## Styling & scales
- Prefer manual color scales when category semantics matter (e.g., statuses) to ensure consistent palette across plots.
- For gradients, `scale_fill_gradient(low, high)` gives clearer density cues than brewer palettes on numeric fills.
- Legends: set `name` in scales to control labels; place legends on the right to preserve map space.
- To separate legends, map districts to `color` and statuses to `fill`; if the layer doesn’t use `color`, add a zero-alpha stub layer to expose the district legend.
- For `geom_pie`, use `size_unit='x'` so pies respect grid spacing; slice labels via `labels=layer_labels().line('@n').format('@n','d').size(k)` and control text color with `theme(label_text=...)`.
- When mixing tile and pie fills, pass a merged palette to `scale_fill_manual` that covers both fill domains; otherwise tile colors will be remapped to the pie palette.
- For annexed/disputed tiles (SEV, ZAP, DNR, LNR, CR), overlay 45-degree parallel dashed strokes on the tile at ~0.6 alpha so the district fill still shows through; keep pies and labels above the hatch layer.
- To remove excess whitespace on tilemaps, derive limits from tile coordinates and set them with `scale_x_continuous(..., expand=[0,0])` and `scale_y_reverse(..., expand=[0,0])`, adding a small pad; adjust `ggsize` to fit the tighter extent.

## Tooltips
- Build with `layer_tooltips()`; `title()` uses current row; `line("Label: @field")` adds rows.
- Date formatting works with `@{date_col|%Y-%m-%d}`; ensure the column is datetime.
- Combine multiple flags on one line to save space: `.line("Sanitising: @sanitising_flag  Sanitised: @sanitised_flag")`.

## Output conventions
- Each script saves to `visualisations/output/<name>.html`.
- Scripts are standalone; no notebooks needed. Keep sizes modest for web (default lets-plot sizing is fine).

## Troubleshooting checklist
- `ModuleNotFoundError: visualisations`: set `PYTHONPATH=.`
- Fontconfig/matplotlib cache warnings: set writable `MPLCONFIGDIR` and `XDG_CACHE_HOME`.
- No data plotted: check for `df_geo` emptiness or missing `lat/lon`; `enrich()` must be called.
- Overplotting on maps: reduce `size`, increase `alpha`, or add jitter; heat layer helps contextualize density.
- GeoJSON tips: read with `geopandas`; dissolve sub-polygons and prefer `union_all()` (not `unary_union`) to avoid deprecation warnings; join points to regions with `sjoin(..., predicate="within")`. If you expand tile spacing, shrink `width/height` of `geom_tile` accordingly to prevent overlap.
