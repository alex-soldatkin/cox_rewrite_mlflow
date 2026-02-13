"""Core forest plot builder using lets_plot.

Uses manual numeric y positions (not categorical) for precise control over
alignment, dodge, spacing, and per-variable background shading.
"""

import pandas as pd
from lets_plot import (
    aes,
    coord_cartesian,
    element_blank,
    element_text,
    geom_point,
    geom_rect,
    geom_segment,
    geom_text,
    geom_vline,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    scale_fill_gradient2,
    scale_y_continuous,
    theme,
)

from .config import GROUP_ORDER, MODEL_COLOURS


def forest_plot(
    data: pd.DataFrame,
    scale: str = 'hr',
    dodge_by: str = 'model_name',
    title: str = '',
    xlim: tuple | None = None,
    width: int = 900,
    height: int | None = None,
    show_stars: bool = True,
    colour_by: str = 'model_name',
    dodge_width: float = 0.7,
    point_size: float = 3.0,
    note: str = '',
):
    """Build a forest plot with manual layout for precise alignment.

    Parameters
    ----------
    data : DataFrame with columns: covariate, estimate, se, ci_lower, ci_upper,
           p, stars, model_name, variable_group, variable_label
    scale : 'hr' (reference line at 1.0) or 'coef' (reference line at 0.0)
    dodge_by : column to dodge points vertically
    title : plot title
    xlim : (min, max) for x-axis; auto-calculated if None
    width : plot width in pixels
    height : plot height in pixels (auto if None)
    show_stars : whether to show significance stars right of each CI
    colour_by : column to map to point/segment colour
    dodge_width : total vertical spread for dodged models per variable
    point_size : size of point estimates
    note : additional note for caption
    """
    ref_line = 1.0 if scale == 'hr' else 0.0
    x_label = 'Hazard Ratio' if scale == 'hr' else 'Coefficient'
    data = data.copy()

    # ── 1. Variable layout: numeric y with gaps between groups ────────────
    var_info = (
        data.drop_duplicates('covariate')[['covariate', 'variable_label', 'variable_group']]
        .reset_index(drop=True)
    )
    groups_present = [g for g in GROUP_ORDER if g in var_info['variable_group'].values]

    y_counter = 0
    y_map = {}  # covariate -> numeric y

    for gi, group in enumerate(groups_present):
        gvars = var_info.loc[var_info['variable_group'] == group, 'covariate'].tolist()
        for var in gvars:
            y_map[var] = y_counter
            y_counter += 1
        y_counter += 1.5  # breathing room between groups

    # Flip so first variable is at top of plot
    max_y = max(y_map.values()) if y_map else 0
    y_map = {k: max_y - v for k, v in y_map.items()}

    data['y_num'] = data['covariate'].map(y_map)

    # ── 2. Dodge: offset y per model ──────────────────────────────────────
    models = data[dodge_by].unique().tolist()
    n_models = len(models)
    if n_models > 1:
        step = dodge_width / n_models
        offsets = {m: (i - (n_models - 1) / 2) * step
                   for i, m in enumerate(models)}
    else:
        offsets = {models[0]: 0.0}
    data['y_dodge'] = data['y_num'] + data[dodge_by].map(offsets)

    # ── 3. Auto x-limits ─────────────────────────────────────────────────
    if xlim is None:
        margin = 0.15
        lo, hi = data['ci_lower'].min(), data['ci_upper'].max()
        span = hi - lo
        xlim = (lo - margin * span, hi + margin * span)

    # ── 4. Background shading (green = protective, red = harmful) ────────
    mean_est = data.groupby('covariate')['estimate'].mean()
    bg_rows = []
    for var, ypos in y_map.items():
        # positive protectiveness => protective (green)
        protectiveness = -(mean_est.get(var, ref_line) - ref_line)
        bg_rows.append({
            'xmin': xlim[0], 'xmax': xlim[1],
            'ymin': ypos - 0.45, 'ymax': ypos + 0.45,
            'protectiveness': protectiveness,
        })
    bg_df = pd.DataFrame(bg_rows)

    # ── 5. Star placement: right of CI upper bound ───────────────────────
    star_nudge = (xlim[1] - xlim[0]) * 0.012
    data['star_x'] = data['ci_upper'] + star_nudge

    # ── 6. Auto height (generous to avoid crowding) ─────────────────────
    n_vars = len(y_map)
    if height is None:
        height = max(400, n_vars * 60 + len(groups_present) * 40 + 140)

    # ── 7. Colours ────────────────────────────────────────────────────────
    colours = MODEL_COLOURS[:len(models)]

    # ── 8. Caption ────────────────────────────────────────────────────────
    sig_note = ('*** p<0.001  ** p<0.01  * p<0.05  \u2020 p<0.10'
                if show_stars else '')
    direction = ('HR < 1 \u2190 protective \u00b7 harmful \u2192 HR > 1'
                 if scale == 'hr'
                 else 'Coef < 0 \u2190 protective \u00b7 harmful \u2192 Coef > 0')
    caption_parts = [direction, sig_note]
    if note:
        caption_parts.append(note)
    caption = '\n'.join(p for p in caption_parts if p)

    # ── 9. Y-axis breaks and labels ──────────────────────────────────────
    y_breaks = sorted(y_map.values())
    var_at_y = {v: k for k, v in y_map.items()}
    y_labels_list = [
        var_info.loc[var_info['covariate'] == var_at_y[y], 'variable_label'].values[0]
        for y in y_breaks
    ]

    # ── 10. Group labels + broken dividers (gap around text) ────────────
    x_mid = (xlim[0] + xlim[1]) / 2
    x_span = xlim[1] - xlim[0]
    group_label_rows = []
    divider_seg_rows = []  # split dividers that avoid the label text

    for gi, group in enumerate(groups_present):
        gvars = var_info.loc[var_info['variable_group'] == group, 'covariate'].tolist()
        top_y = max(y_map[v] for v in gvars)
        label_y = top_y + 0.75
        group_label_rows.append({'x': x_mid, 'y': label_y, 'label': group})

        # Build two segment pieces per divider, leaving a gap for the label
        gap_half = max(len(group) * x_span * 0.011, x_span * 0.04)
        divider_seg_rows.append({
            'x': xlim[0], 'xend': x_mid - gap_half,
            'y': label_y, 'yend': label_y,
        })
        divider_seg_rows.append({
            'x': x_mid + gap_half, 'xend': xlim[1],
            'y': label_y, 'yend': label_y,
        })

    group_label_df = pd.DataFrame(group_label_rows)
    divider_seg_df = pd.DataFrame(divider_seg_rows) if divider_seg_rows else None

    # ── 11. Axis limits ──────────────────────────────────────────────────
    y_lo = min(y_map.values()) - 0.7
    y_hi = max(y_map.values()) + 1.4

    # ── 12. Build plot ───────────────────────────────────────────────────
    p = (
        ggplot()
        # Background variable shading
        + geom_rect(
            data=bg_df,
            mapping=aes(xmin='xmin', xmax='xmax',
                        ymin='ymin', ymax='ymax',
                        fill='protectiveness'),
            alpha=0.3, size=0, show_legend=False,
        )
        + scale_fill_gradient2(
            low='#E53935', mid='#FAFAFA', high='#43A047',
            midpoint=0,
        )
        # Reference line
        + geom_vline(xintercept=ref_line, linetype='dashed',
                     color='#999999', size=0.6)
        # CI segments (identical y_dodge ensures perfect alignment with points)
        + geom_segment(
            data=data,
            mapping=aes(x='ci_lower', xend='ci_upper',
                        y='y_dodge', yend='y_dodge',
                        color=colour_by),
            size=1.0, alpha=0.5,
        )
        # Point estimates
        + geom_point(
            data=data,
            mapping=aes(x='estimate', y='y_dodge', color=colour_by),
            size=point_size, alpha=0.9,
        )
        # Group labels (watermark-style, in gap above each group)
        + geom_text(
            data=group_label_df,
            mapping=aes(x='x', y='y', label='label'),
            size=8, color='#D0D0D0', fontface='italic',
        )
        # Scales
        + scale_color_manual(values=colours, name='')
        + scale_y_continuous(breaks=y_breaks, labels=y_labels_list)
        # Labels and theme
        + labs(title=title, x=x_label, y='', caption=caption)
        + theme(
            axis_text_y=element_text(size=10),
            axis_title_x=element_text(size=11),
            plot_title=element_text(size=13, face='bold'),
            plot_caption=element_text(size=8, color='#888888'),
            panel_grid_major_y=element_blank(),
            panel_grid_minor_y=element_blank(),
            legend_position='bottom',
        )
        + coord_cartesian(xlim=xlim, ylim=(y_lo, y_hi))
        + ggsize(width, height)
    )

    # Significance stars (to the right of each CI)
    if show_stars:
        star_data = data[data['stars'].astype(str).str.strip() != ''].copy()
        if not star_data.empty:
            p = p + geom_text(
                data=star_data,
                mapping=aes(x='star_x', y='y_dodge', label='stars'),
                size=7, color='#333333', hjust=0,
            )

    # Group divider lines (broken around label text)
    if divider_seg_df is not None:
        p = p + geom_segment(
            data=divider_seg_df,
            mapping=aes(x='x', xend='xend', y='y', yend='yend'),
            color='#E0E0E0', size=0.4,
            show_legend=False,
        )

    return p
