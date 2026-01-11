# Legacy Analysis Map

**Directory:** `OLD_WRITEUP_DIR`
**Path:** `/Users/alexandersoldatkin/projects/factions-networks-thesis/drafts/families`

This directory contains the statistical analysis, regression modeling, and visualization scripts for the thesis.

## Regression Modeling

### 1. `family_regression_analysis.py`

- **Purpose**: Main script for bank survival analysis using Logistic Regression.
- **Key Functions**:
  - `run_logistic_regression`: Fits logit models using `statsmodels`. Includes `lifespan_years` as a control.
  - `format_stargazer`: Compiles model results into a summary table.
- **Drivers**: Defines model specifications (e.g., "Age Only", "Family %", "Combined Family") and runs the pipeline.

### 2. `panel_regression.py`

- **Purpose**: Advanced panel data analysis using `linearmodels`.
- **Methods Implemented**:
  1.  **Between Estimator**: Cross-sectional analysis of time-invariant variables (e.g., `family_ownership_percentage`).
  2.  **First Differences**: Analyzes changes over time (`diff()`).
  3.  **Pooled OLS**: Clustered standard errors.
  4.  **Random Effects**: GLS estimation.
- **Output**: Comparison of different panel estimators.

### 3. `family_regression_timeseries.py`

- **Purpose**: Analyzes how survival determinants change over time (time-series analysis).
- **Logic**: Runs the survival model on snapshots of data (e.g., year-by-year) to track coefficient evolution.

## Visualization

### 1. `family_visualizations.py`

- **Purpose**: Diagnostic plots for logistic regression models using `lets_plot`.
- **Plot Types**:
  - **Forest Plots**: Visualizes coefficients/odds ratios.
  - **Effect Plots**: Predicted probabilities vs. predictor values (marginal effects).
  - **Binned Residuals**: Diagnostic for model fit.
  - **Decision Boundary**: 2D visualization of classification boundaries.

### 2. `cox_predictions_plot.py`

- **Purpose**: Visualization for Cox Proportional Hazards models.
- **Plot Types**:
  - **Hazard Ratios**: Estimates relative to a baseline (median).
  - **Faceted Plots**: Compares multiple models/predictors side-by-side.
  - **Forest Plots**: For Cox model coefficients.

### 3. `umap_plot.py`

- **Purpose**: Dimensionality reduction and clustering visualization.
- **Key Features**:
  - Preprocesses data (one-hot encoding, log transform, scaling).
  - Runs UMAP (`uniform_manifold_approximation_and_projection`).
  - Interactive plots with tooltips using `lets_plot`.

## Reporting & Utilities

### 1. `stargazer_cox.py` (and `cox_stargazer_new.py`)

- **Purpose**: Custom wrapper around `stargazer` library to format regression outputs (OLS, Logit, Cox).
- **Enhancements**: Adds extra metrics to the table footer: AIC, BIC, F1 Score, Precision, Recall, Accuracy, ROC AUC.
- **Output**: HTML/LaTeX tables for the thesis write-up.

### 2. `family_analysis_data.py`

- **Purpose**: specific data fetching logic for family analysis from Neo4j.
- **Key Logic**: Queries Bank nodes, computes 'survived' status (based on `date_banki_memory`), and 'foundation_year'.
