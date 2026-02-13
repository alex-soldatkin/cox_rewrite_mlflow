# create long df from regression results
def create_long_logistic_results(fitted_models, model_names):
    """
    Create a long-format DataFrame from the fitted logistic regression models' results.
    Each row corresponds to a predictor variable and its associated statistics for each model.
    Parameters:
    fitted_models (list): List of fitted statsmodels logistic regression models.
    model_names (list): List of names corresponding to each model in fitted_models.
    Returns:
    pd.DataFrame: A long-format DataFrame containing the model results.
    """

    def get_stars(p_value):
        """
        Helper function to determine significance stars based on p-value.
        """
        if p_value < 0.001:
            return "***"
        elif p_value < 0.01:
            return "**"
        elif p_value < 0.05:
            return "*"
        else:
            return ""
    from io import StringIO
    long_logistic_results = pd.DataFrame()

    for model, model_name in zip(fitted_models, model_names):
        model_results_html = StringIO(model.summary().tables[1].as_html())
        model_results_df = pd.read_html(model_results_html, header=0, index_col=0)[0]
        model_results_df['odds_ratio'] = model_results_df['coef'].apply(lambda x: np.exp(x))
        
        model_results_df.rename(
            columns={
                "coef": "log_odds",
                "std err": "std_error",
                "P>|z|": "p_value",
                "[0.025": "conf_int_lower",
                "0.975]": "conf_int_upper",
            },
            inplace=True,
        )
        # exponentiate confidence intervals
        model_results_df['conf_int_lower'] = model_results_df['conf_int_lower'].apply(
            lambda x: np.exp(x)
        )
        model_results_df['conf_int_upper'] = model_results_df['conf_int_upper'].apply(
            lambda x: np.exp(x)
        )
        model_results_df['stars'] = model_results_df['p_value'].apply(get_stars)
        model_results_df['model_name'] = model_name
        # drop the intercept
        model_results_df = model_results_df[model_results_df.index != "Intercept"]
        long_logistic_results = pd.concat([long_logistic_results, model_results_df], axis=0)
    long_logistic_results.reset_index(inplace=True)
    long_logistic_results.rename(columns={"index": "covariate"}, inplace=True)
    # add variable group for CAMEL, topology, state, family, foreign, crisis

    return long_logistic_results
        
long_logistic_results = create_long_logistic_results(fitted_models, model_names)

state_or_plot = (
    ggplot(long_logistic_results.query(
        "variable_group == 'State'"
    ), aes(y="covariate", group="model_name"))
    # + ggsize(1200, 600)
    + scale_x_continuous()
    + geom_tile(
        aes(y="covariate", fill="odds_ratio"),
        x=4.25,
        width=7.5,
        height=0.99,  # Centers at x=4.25, spans 0.5 to 8
        alpha=0.05,
        show_legend=False,
    )
    + scale_fill_gradientn(
        colors=["#CD7586", "#FFFFFF",   "#FFFFFF", "#FFFFFF", "#14824B"],
        # limits=[0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 3.5],
        # breaks=[.6, 0.8, 0.9, 1, 1.05, 1.07, 1.1, 1.15, 1.2, 1.3, 1.4, 1.5, 2, 3, 4, 5, 6, 7, 8],
        name="Odds Ratio",
        # trans="symlog",
        guide=guide_colorbar(
            title="Odds Ratio (OR)",
 
            barwidth=10,
            barheight=0.5,
            nbin=100,
        ),
    )
    + geom_errorbar(
        aes(xmin="conf_int_lower", xmax="conf_int_upper"),
        # width=0.1,
        # height=0.1,
        color="lightgrey",
        position=position_dodgev(0.8),
        linetype=7,
        tooltips=layer_tooltips().line('Model: | @model_name')
    )
    + geom_vline(xintercept=1, linetype="dashed", color="red", alpha=0.5)
    + geom_point(
        aes(x="odds_ratio"),
        size=1,
        alpha=0.7,
        color="red",
        position=position_dodgev(0.8),
        tooltips=layer_tooltips().line('Model: | @model_name')
    )
    + geom_text(
        aes(x="odds_ratio", label="stars"),
        size=4,
        position=position_dodgev(0.8),
        nudge_x=0.015,
    )
    + labs(
        title="",
        x="Odds Ratio (OR)",
        y="",
        caption="Note: OR > 1 indicates increased odds of bank survival, OR < 1 indicates decreased odds. \n Protective factors (OR > 1) are shaded in green, risk factors (OR > 1) in red. \n *** p < 0.001, ** p < 0.01, * p < 0.05.",
    )
    + theme(
        axis_text_y=element_text(size=12),
        panel_grid_major_y=element_blank(),
        panel_grid_ontop_y=True
    )
    # + scale_x_log10(
    #     # breaks=[0.6, 0.8, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 2.5, 3, 3.5, 4, 5, 6, 7, 8],
    # )
    + scale_y_discrete(position="left")
    + facet_wrap("variable_group", scales="free", ncol=1)
    + coord_cartesian(xlim=(0.75, 1.45))
    + ggsize(1000, 400)
)

ggsave(
    state_or_plot,
    filename="state_or_plot.html",
    path="./writeup/figures",
)
state_or_plot