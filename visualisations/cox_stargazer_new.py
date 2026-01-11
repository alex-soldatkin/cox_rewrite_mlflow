import pandas as pd
import numpy as np
from lets_plot import *

LetsPlot.setup_html()


def create_cox_comparison_long_df(models, model_names):
    """
    Create a comparison table for Cox models using stargazer-style output.

    Args:
        models (list): List of fitted Cox models
        model_names (list): List of model names

    Returns:
        DataFrame: Comparison table
    """
    # Create a summary DataFrame for each model
    model_summaries = []
    for model, model_name in zip(models, model_names):
        model_summary = model.summary.copy().reset_index()
        model_summary["model_name"] = model_name
        model_summary["aic"] = model.AIC_partial_
        model_summary["log_likelihood"] = model.log_likelihood_
        model_summary["model_formula"] = model.formula
        model_summaries.append(model_summary)

    model_summaries_df = pd.concat(model_summaries, ignore_index=True)

    def get_stars(p_value):
        if p_value < 0.001:
            return "***"
        elif p_value < 0.01:
            return "**"
        elif p_value < 0.05:
            return "*"
        elif p_value < 0.1:
            return "+"
        else:
            return ""

    model_summaries_df["stars"] = model_summaries_df["p"].apply(get_stars)

    return model_summaries_df


# test
# cox_comparison_long_df = create_cox_comparison_long_df(models, model_names)
# cox_comparison_long_df.head(5)


def create_cox_comparison_table(cox_comparison_long_df):
    """
    Create a comparison table for Cox models using stargazer-style output.

    Args:
        cox_comparison_long_df (DataFrame): DataFrame with model summaries and model names

    Returns:
        DataFrame: Comparison table
    """

    # coeff + stars (upper) + (se)
    def format_cell(row):
        coef = row["coef"]
        se = row["se(coef)"]
        stars = row["stars"]
        if type(coef) == str:
            return coef
        if pd.isna(coef):
            return ""
        if pd.isna(se):
            return ""
        return f"{coef:.3f}{stars} ({se:.3f})"

    cox_comparison_long_df["display_coef"] = cox_comparison_long_df.apply(
        format_cell, axis=1
    )
    cox_comparison_long_df = cox_comparison_long_df[
        ["covariate", "model_name", "display_coef", "log_likelihood"]
    ]
    # pivot to wide format, put log likelihood at the bottom
    cox_comparison_wide_df = cox_comparison_long_df.pivot(
        index="covariate", columns="model_name", values="display_coef"
    )
    cox_comparison_wide_df.fillna("", inplace=True)
    cox_comparison_wide_df.style.set_table_attributes('class="table table-striped"')
    cox_comparison_wide_df.style.set_caption("Cox Model Comparison Table")
    cox_comparison_wide_df.style.set_table_styles(
        [{"selector": "th", "props": [("text-align", "center")]}]
    )
    # remove model_name and covariate from index
    cox_comparison_wide_df.index.name = None
    cox_comparison_wide_df.columns.name = None
    return cox_comparison_wide_df


# Create the comparison table
# create_cox_comparison_table(cox_comparison_long_df)
def create_cox_comparison_table_latex(cox_comparison_long_df):
    """
    Create a comparison table for Cox models using stargazer-style output.
    Args:
        cox_comparison_long_df (DataFrame): DataFrame with model summaries and model names
    Returns:
        DataFrame: Comparison table
    """

    # coeff + stars (upper) + (se)
    def format_cell(row):
        coef = row["coef"]
        se = row["se(coef)"]
        stars = row["stars"]
        if type(coef) == str:
            return coef
        if pd.isna(coef) or pd.isna(se):
            return ""
        return f"{coef:.3f}{stars} ({se:.3f})"

    cox_comparison_long_df["display_coef"] = cox_comparison_long_df.apply(
        format_cell, axis=1
    )
    cox_comparison_long_df = cox_comparison_long_df[
        ["covariate", "model_name", "display_coef", "log_likelihood"]
    ]
    # pivot to wide format
    cox_comparison_wide_df = cox_comparison_long_df.pivot(
        index="covariate", columns="model_name", values="display_coef"
    )
    cox_comparison_wide_df.fillna("", inplace=True)
    # remove model_name and covariate from index
    cox_comparison_wide_df.index.name = None
    cox_comparison_wide_df.columns.name = None

    # Create the table without styling first
    latex_table = (
        cox_comparison_wide_df
        # .to_latex(
        # column_format="l|" + "c" * len(model_names),
        # caption="Cox Model Comparison Table",
        # label="tab:cox_model_comparison",
        # escape=True)
    )

    # Replace with double hlines at top and bottom, and single for the header
    # latex_table = latex_table.replace("\\toprule", "\\hline\\hline")
    # latex_table = latex_table.replace("\\midrule", "\\hline")
    # latex_table = latex_table.replace("\\bottomrule", "\\hline\\hline")

    # # Add resizebox to make it fit page width
    # latex_table = latex_table.replace(
    #     "\\begin{table}",
    #     "\\begin{table}[H]\n\\resizebox{\\textwidth}{!}"
    # )
    # latex_table = latex_table.replace(
    #     "\\end{tabular}",
    #     "\\end{tabular}}"
    # )

    return latex_table


# Create and print the comparison table
# print(create_cox_comparison_table(cox_comparison_long_df))


def create_cox_forest_plot_from_long_df(cox_comparison_long_df):

    plot = (
        ggplot(cox_comparison_long_df, aes(y="covariate", group="model_name"))
        + ggsize(1200, 600)
        + scale_x_continuous()
        + geom_bar(
            aes(y="covariate", fill="covariate"),
            width=1.1,
            alpha=0.05,
            show_legend=False,
        )
        + scale_fill_manual(
            values=[
                "#FF9999",
                "#66B3FF",
            ]
        )
        + geom_errorbar(
            aes(
                xmin="exp(coef) lower 95%", xmax="exp(coef) upper 95%", color="stars"
            ),  # Added color aesthetic
            position=position_dodgev(0.8),
            linetype=7,
            tooltips=layer_tooltips()
            .line("Model: | @model_name")
            .line("Covariate: | @covariate")
            .line("formula: | @model_formula"),
        )
        + geom_point(
            aes(x="exp(coef)", color="stars"),  # Added color aesthetic
            size=1.3,
            alpha=0.7,
            position=position_dodgev(0.8),
            tooltips=layer_tooltips()
            .line("Model: | @model_name")
            .line("Covariate: | @covariate")
            .line("formula: | @model_formula"),
        )
        + scale_color_manual(  # Added custom color scale
            name="Significance:",
            values={
                "": "gray",  # Non-significant
                "+": "#f6a600",  # 0.1 star
                "*": "#c90016",  # 1 star
                "**": "#9f1d35",  # 2 stars
                "***": "#800020",  # 3 stars
            },
            labels={
                "": "Not significant",
                "+": "p < 0.1",
                "*": "p < 0.05",
                "**": "p < 0.01",
                "***": "p < 0.001",
            },
        )
        + geom_text(
            aes(x="exp(coef)", label="stars"),
            size=3,
            position=position_dodgev(0.8),
            nudge_x=0.015,
            tooltips=layer_tooltips()
            .line("Model: | @model_name")
            .line("Covariate: | @covariate")
            .line("formula: | @model_formula"),
        )
        + geom_vline(xintercept=1, linetype="dashed", color="red", alpha=0.5)
        + labs(
            title="Comparison of Cox Time-Varying Models",
            x="Hazard Ratio (HR)",
            y="",
            caption="Note: HR > 1 indicates increased risk of bank closure, HR < 1 indicates decreased risk.",
        )
        + theme(
            axis_text_y=element_text(size=8),
            legend_position="bottom",
            panel_grid_major_y=element_blank(),
        )
        + coord_cartesian(xlim=(0.725, 1.15))
    )
    return plot

def create_single_column_stargazer(model, c_index=None, n_subjects=None):
    """
    Creates a single-column DataFrame for a single fitted Cox model,
    formatted in Stargazer style (Coef*** (SE)).
    
    Args:
        model: Fitted lifelines CoxTimeVaryingFitter (or CoxPHFitter)
        c_index (float, optional): Manually calculated C-index if model doesn't have it.
        n_subjects (int, optional): Number of unique subjects/entities.
        
    Returns:
        pd.DataFrame: Index = Covariates + Metrics, Column = 'Value'
    """
    summary = model.summary.copy()
    
    # Helper for stars
    def get_stars(p_value):
        if p_value < 0.001: return "***"
        elif p_value < 0.01: return "**"
        elif p_value < 0.05: return "*"
        elif p_value < 0.1: return "+"
        else: return ""

    # Helper for formatting
    def format_row(row):
        coef = row["coef"]
        se = row["se(coef)"]
        p = row.get("p", row.get("p-value"))
        stars = get_stars(p) if p is not None else ""
        return f"{coef:.3f}{stars} ({se:.3f})"

    # Create Series for Coefs
    coef_series = summary.apply(format_row, axis=1)
    
    # Determine C-index to use
    val_c_index = ""
    if c_index is not None:
        val_c_index = f"{c_index:.3f}"
    elif hasattr(model, 'concordance_index_'):
        val_c_index = f"{model.concordance_index_:.3f}"
    
    # Calculate -log2(p) of LL-ratio test
    ll_ratio_p = model.log_likelihood_ratio_test().p_value
    ll_ratio_metric = f"{-np.log2(ll_ratio_p):.2f}" if ll_ratio_p > 0 else "inf"

    # Create Series for Metrics
    metrics = {
        "Observations": f"{model.event_observed.shape[0]}",  # Approx N
        "Subjects": f"{n_subjects}" if n_subjects is not None else "",
        "Events": f"{model.event_observed.sum()}",
        "Log Likelihood": f"{model.log_likelihood_:.2f}",
        "AIC Partial": f"{model.AIC_partial_:.2f}",
        "-log2(p) LLR": ll_ratio_metric,
        "C-index": val_c_index
    }
    
    # Combine
    # Convert dict to series
    metrics_series = pd.Series(metrics)
    
    # Concat
    final_series = pd.concat([coef_series, metrics_series])
    
    # Return as DataFrame
    df = final_series.to_frame(name="Stargazer_Output")
    df.index.name = "variable"
    return df

def create_single_column_stargazer_hr(model, c_index=None, n_subjects=None):
    """
    Creates a single-column DataFrame for a single fitted Cox model,
    formatted in Stargazer style but reporting HAZARD RATIOS (HR*** (SE_HR)).
    SE_HR is approximated via Delta Method: SE(HR) = HR * SE(coef).
    
    Args:
        model: Fitted lifelines CoxTimeVaryingFitter
        c_index (float, optional): Manually calculated C-index.
        n_subjects (int, optional): Number of unique subjects/entities.
        
    Returns:
        pd.DataFrame: Index = Covariates + Metrics, Column = 'Value'
    """
    summary = model.summary.copy()
    
    # Helper for stars
    def get_stars(p_value):
        if p_value < 0.001: return "***"
        elif p_value < 0.01: return "**"
        elif p_value < 0.05: return "*"
        elif p_value < 0.1: return "+"
        else: return ""

    # Helper for formatting
    def format_row(row):
        hr = row.get("exp(coef)")
        se_coef = row.get("se(coef)")
        
        # Delta method for SE of exp(beta): SE = exp(beta) * SE(beta)
        if hr is not None and se_coef is not None:
             se_hr = hr * se_coef
        else:
             se_hr = 0.0
             
        p = row.get("p", row.get("p-value"))
        stars = get_stars(p) if p is not None else ""
        return f"{hr:.3f}{stars} ({se_hr:.3f})"

    # Create Series for Coefs
    coef_series = summary.apply(format_row, axis=1)
    
    # Determine C-index to use
    val_c_index = ""
    if c_index is not None:
        val_c_index = f"{c_index:.3f}"
    elif hasattr(model, 'concordance_index_'):
        val_c_index = f"{model.concordance_index_:.3f}"
    
    # Calculate -log2(p) of LL-ratio test
    ll_ratio_p = model.log_likelihood_ratio_test().p_value
    ll_ratio_metric = f"{-np.log2(ll_ratio_p):.2f}" if ll_ratio_p > 0 else "inf"

    # Create Series for Metrics
    metrics = {
        "Observations": f"{model.event_observed.shape[0]}",
        "Subjects": f"{n_subjects}" if n_subjects is not None else "",
        "Events": f"{model.event_observed.sum()}",
        "Log Likelihood": f"{model.log_likelihood_:.2f}",
        "AIC Partial": f"{model.AIC_partial_:.2f}",
        "-log2(p) LLR": ll_ratio_metric,
        "C-index": val_c_index
    }

    
    # Combine
    metrics_series = pd.Series(metrics)
    final_series = pd.concat([coef_series, metrics_series])
    
    # Return as DataFrame
    df = final_series.to_frame(name="Stargazer_Output_HR")
    df.index.name = "variable"
    return df
