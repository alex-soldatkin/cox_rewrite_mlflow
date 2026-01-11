# Experiment Framework & MLflow Implementation

This document details the architecture, patterns, and workflows for the MLflow-based experiment framework used in this project.

## 1. Architecture Overview

The framework is designed to separate **experiment logic** from **infrastructure utilities**.

```
project_root/
├── experiments/                 # Individual experiment definitions
│   ├── exp_000_template/        # Reusable template
│   ├── exp_001_time_varying/    # Actual experiments
│   └── ...
├── mlflow_utils/                # Shared utilities
│   ├── loader.py                # Data loading & Pydantic validation
│   └── tracking.py              # MLflow server & metrics helpers
└── data_models/                 # Pydantic schemas
    ├── accounting.py
    └── analysis.py
```

## 2. Core Components

### 2.1 Experiment Data Loader (`mlflow_utils/loader.py`)

The `ExperimentDataLoader` is the central gateway for training data. It performs three critical steps:

1.  **Fetch**: Queries Neo4j (population, graph metrics) and Parquet (accounting data).
2.  **Merge**: Joins disparate sources on reliable keys (`regn`, `date`).
3.  **Validate**: Projects every row into the `AnalysisDatasetRow` Pydantic model.

**Pattern:**

```python
loader = ExperimentDataLoader()
df = loader.load_training_data(start_date="2010-01-01", end_date="2020-12-31")
```

**Systematization:**
Data is not just merged; it is _typed_. The `AnalysisDatasetRow.create_row()` factory ensures that:

- `camel_` prefixes are used for CAMEL indicators.
- `family_` prefixes for family metrics.
- `network_` aliases for graph topology.
- `NaN`s are sanitized via `_safe_get`.

### 2.2 Pydantic Models (`data_models/`)

We enforce schema strictness at the application level.

- `AccountingRecord`: Mirrors the CBR 101/102 form data.
- `FamilyOwnershipMetrics`: `rho_F`, `FOP`, etc.
- `AnalysisDatasetRow`: The flattened, final row used for analysis.

### 2.3 MLflow Utilities (`mlflow_utils/tracking.py`)

Helper functions to standardize logging:

- `setup_experiment`: Sets the tracking URI (defaults to `http://127.0.0.1:5000` to avoid macOS AirPlay port conflicts).
- `log_metrics_survival`: Logs C-index and summary stats.
- `log_pydantic_params`: Dumps config objects as params.

## 3. Experiment Structure Pattern

Every experiment directory (e.g., `experiments/exp_001...`) is self-contained with two key files:

### 3.1 `config.yaml`

Declarative configuration of the run.

```yaml
experiment:
  name: "exp_001_time_varying"
  human_readable_name: "Model 1: Baseline"
  description: "Cox Time-Varying model with base controls only."
  tags:
    model_type: "cox_time_varying"

data:
  features: ["camel_roa", "family_rho_F", "network_page_rank"]
  target: "failed"

model:
  params:
    penalizer: 0.01
```

### 3.2 `run.py`

The execution script. It conforms to a standard template:

1.  **Load Config**: `yaml.safe_load("config.yaml")`.
2.  **Setup Check**: `setup_experiment()`.
3.  **Log Metadata**: Set `human_readable_name` and `description` as MLflow tags.
4.  **Load Data**: `loader.load_training_data()`.
5.  **Transform**: Apply model-specific transformations (e.g., episodic splitting for CoxTimeVarying).
6.  **Train & Log**: Fit model, log metrics/params to MLflow.

## 4. Usage & Workflows

### Running an Experiment

Execute the run script directly. It will auto-connect to the server.

```bash
uv run python experiments/exp_001_time_varying/run.py
```

### MLflow Server

The server must be running to view results.

```bash
uv run mlflow server --port 5000
```

**Important**: Access the dashboard via `http://127.0.0.1:5000`. Using `localhost:5000` can sometimes cause 403 errors on macOS due to AirPlay Receiver listing on port 5000.

### Creating a New Experiment

1.  Copy `experiments/exp_000_template` to `experiments/exp_NNN_name`.
2.  Update `config.yaml` with new features/params.
3.  Modify `run.py` if custom pre-processing is needed.

## 6. Visualization & Reporting Artifacts

To enable aggregated reporting across multiple experiments without re-running models, the pipeline generates validatable artifacts.

### 6.1 Stargazer Regression Tables

- **Artifact**: `stargazer_column.csv`
- **Purpose**: Stores pre-formatted regression results for a single run to be aggregated later.
- **Format**: CSV with header `variable,Stargazer_Output`.
  - Index columns: Covariate names (e.g., `camel_roa`), plus metrics (`Observations`, `Log Likelihood`, `C-index`).
  - Value column: String formatted as `Coef*** (SE)` (e.g., `-0.465*** (0.061)`).
- **Aggregation Logic**: `glob` all CSVs and `pd.concat(..., axis=1)`.

### 6.1b Hazard Ratio Tables

- **Artifact**: `stargazer_hr_column.csv`
- **Purpose**: Stores Hazard Ratios ($e^{\beta}$) instead of coefficients.
- **Format**: Identical structure. Values are `HR*** (SE_HR)` where $SE_{HR} \approx HR \cdot SE_{\beta}$ (Delta Method).

### 6.2 Isolated Survival Predictions

- **Artifact**: `predictions_isolated.parquet`
- **Purpose**: Enables "Counterfactual" or "Partial Dependence" style plotting of survival curves.
- **Methodology**:
  1.  Take the **latest state** of every bank in the training set.
  2.  For each variable $X_j$: It creates a synthetic dataset where $X_j$ keeps its true value, but all other variables $X_{-j}$ are set to the sample mean.
  3.  Computes survival curve $S(t | x_{i,j}, \bar{x}_{-j})$ using $S(t) = \exp(-H_0(t) \cdot \exp(\beta X))$.
- **Schema**:
  - `value` (float): The actual value of the variable for that bank.
  - `survival_prob` (float): Predicted survival probability.

### 6.3 Interpretation Reports

- **Artifact**: `interpretation.md`
- **Purpose**: Auto-generated markdown report interpreting the model's coefficients in plain English.
- **Content**:
  - Ranked list of risk factors and protective factors.
  - Percentage change in hazard for each variable.
  - Statistical significance indicators.

## 7. Experiment Metadata & Aggregation Pattern

To facilitate comparing many models (as in `exp_002_paper_models`), we use a specific metadata strategy.

### 7.1 Human Readable Tags

In `config.yaml`, always define:

- `human_readable_name`: A short, descriptive name (e.g., "Model 1: Controls").
  - **Usage**: Becomes the column header in aggregated Stargazer tables.
- `description`: A sentence describing the model's purpose.

In `run.py`, these **must** be logged as tags at the start of the run:

```python
mlflow.set_tag("human_readable_name", exp_config["human_readable_name"])
mlflow.set_tag("description", exp_config["description"])
```

### 7.2 Automated Aggregation Script

The script `scripts/aggregate_stargazer.py` is the engine for generating comparison tables.

- **Workflow**:
  1.  Scans `mlartifacts/` for all `stargazer_column.csv` and `stargazer_hr_column.csv` files.
  2.  Reads the `human_readable_name` tag for each corresponding run.
  3.  Joins all single-column CSVs into a master table.
  4.  Saves `stargazer/stargazer_aggregated_coef_*.csv` and `_hr_*.csv`.
- **Benefit**: You can run 10 separate experiments, then run this script once to get a single publication-ready comparison table.
