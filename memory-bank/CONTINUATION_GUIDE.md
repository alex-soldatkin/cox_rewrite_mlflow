# Continuation Guide: Russian Bank Survival Analysis

This document serves as the "source of truth" for anyone picking up this project. It synthesises the architecture, theoretical context, and operational workflows developed for re-analysing the "Banking on Family" thesis.

## 1. Project Context & Current State

### Core Objective

To identify the determinants of Russian bank survival (2004–2025) using a combination of **Survival Analysis (Cox Time-Varying)** and **Classification (Logistic Regression)**.

### Key Theoretical Achievement

- **Family Connection Ratio (`family_rho_F`)**: Identified as the most robust protective factor. Relational density (who is connected to whom) is more predictive than raw ownership percentage.
- **Network Endogeneity**: Discovered that high centrality (PageRank, Betweenness) often correlates with _higher_ failure risk or "forced survival" as a "Network Firefighter." Centrality in this network is often a marker of being selected by the Central Bank to absorb failing nodes, rather than simple market strength.

### Current Status

- Final clean runs for **Cox TV (`exp_002`)** and **Logistic TV (`exp_003`)** are complete.
- Aggregated publication-ready tables exist in `./stargazer/`.
- Automated interpretation reports exist in each MLflow run's artifacts.

---

## 2. Infrastructure & Environment

### Tech Stack

- **Runtime**: Python 3.12+ managed by `uv`.
- **Database**: Neo4j (Graph data for ownership/management) + Parquet (Accounting financials).
- **Experiment Tracking**: MLflow (running on `http://localhost:5000`).
- **Statistical Libraries**: `statsmodels` (Logistic), `lifelines` (Cox TV), `scikit-learn` (Metrics).

### Commands & Setup

- **Start MLflow**: `uv run mlflow server --port 5000`
- **Install Dependencies**: `uv sync`
- **Neo4j Schema**: To view current graph schema:
  `cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD -c "CALL db.schema.visualization()"`

---

## 3. The Experiment Loop

Experiments are modular and self-contained in `experiments/exp_...`.

### A. Configuration (`config.yaml`)

Models are defined declaratively. **CRITICAL**: Use the Pydantic aliased names for features (e.g., `family_FOP` instead of raw column names).

```yaml
experiment:
  name: "exp_003_logistic_tv"
  human_readable_name: "Model 6: Full" # Used as heading in aggregated tables
  description: "Comprehensive Logistic specification..."
data:
  features: ["camel_roa", "family_rho_F", "network_C_b"] # Aliased names
  target: "failed"
```

### B. Execution (`run.py`)

Standard lifecycle:

1.  **Setup Tracking**: Standardizes MLflow URI and experiment IDs.
2.  **Load Data**: `loader.load_training_data()` fetches and merges Neo4j/Parquet data.
3.  **Train**: Fits the model (Cox or Logit).
4.  **Artifact Generation**:
    - `create_single_column_stargazer`: Formats coefficients for later aggregation.
    - `generate_interpretation_report`: Writes a plain-English `interpretation.md`.
    - `generate_isolated_predictions`: Calculates counterfactual survival curves. Only triggered if `save_predictions` is set to `true` in `config.yaml`.

### C. Running an Experiment

```bash
uv run python experiments/exp_003_logistic_tv/run.py
```

---

## 4. The Data Engine (`mlflow_utils/loader.py`)

This project uses a strict Pydantic layer to prevent "schema drift."

- **Model**: `data_models/analysis.py` defines `AnalysisDatasetRow`.
- **Aliasing**: The loader maps raw data to clean prefixes:
  - `camel_`: Financial indicators.
  - `family_`: Kinship metrics.
  - `state_` / `foreign_`: Ownership types.
  - `network_`: Topology metrics (e.g., `network_C_b` for complexity).

**If you add a new metric to Neo4j, you MUST update `AnalysisDatasetRow` and the `create_row` logic in `loader.py`.**

---

## 5. Aggregation & Reporting

Generating a single comparison table from 10 different MLflow runs:

1.  **Script**: `scripts/aggregate_stargazer.py`
2.  **Logic**:
    - It scans the `mlartifacts/` directory.
    - Finds all `stargazer_column.csv` or `stargazer_hr_column.csv` files.
    - Matches them with the `human_readable_name` tag from the MLflow run.
    - Horizontal-joins them into a final CSV.
3.  **Command**:
    `uv run python scripts/aggregate_stargazer.py`
4.  **Output**: Found in `./stargazer/stargazer_aggregated_...csv`.

---

## 6. Critical Files to Watch

- **`GEMINI.md`**: Project-specific rules (British English, `uv` commands, Neo4j access).
- **`memory-bank/experiment_framework.md`**: Deep dive into the architecture.
- **`visualisations/`**: Contains the logic for stargazer formatting and automated interpretation.
- **`regression_writeup.md`**: The latest intellectual synthesis of the results.

## 8. Data Models (Pydantic)

The project relies on strict Pydantic models (found in `./data_models/`) to ensure data integrity across the pipeline:

- **`accounting.py`**: Models for CBR forms 101/102 (e.g., `AccountingRecord`, `BalanceSheet`).
- **`graph.py`**: Data structures for ownership (`OWNERSHIP` relationship), management, and family ties.
- **`analysis.py`**: The "master" model (`AnalysisDatasetRow`) used by `ExperimentDataLoader`. It performs the final aliasing and sanitization.
- **`rolling_windows.py`**: Schema for time-sliced population data.

## 9. Historical context & Thesis Papers

The `./memory-bank/papers/` directory contains the intellectual heritage and working drafts of the analysis:

- **`family_survival_improved.qmd`**: The primary Quarto document for the revised thesis. It contains the literature review, hypothesis development, and the original "CAMEL + Family" narrative.
- **`temp_*.md`**: Thematic extracts (Theory, Database, Ownership) used for re-building the argument during the transition to the MLflow framework.

## 10. Legacy Pipeline & Provenance

The current clean datasets in `./stargazer/` and the Parquet files in the accounting directory are the result of a multi-stage legacy pipeline documented in `memory-bank/legacy/`:

- **Data Aggregation**: `cbr_aggregation.py` maps historical CBR account codes to modern banking indicators (ROA, NIM, etc.) and enforces accounting identities.
- **Advanced Imputation**: The "Gold" Parquet datasets (e.g., `final_banking_indicators_imputed.parquet`) were processed via `cbr_imputation.py` using **State Space Models (SSM)** for stocks and **Cubic Splines** for flows. This ensures that the time-varying analysis is not biased by sparse reporting.
- **Legacy Maps**: Detailed breakdown of the original folder structure can be found in:
  - `memory-bank/legacy/legacy_project_map.md` (Overview)
  - `memory-bank/legacy/legacy_data_processing_map.md` (Aggregation/Imputation)
  - `memory-bank/legacy/legacy_analysis_map.md` (Original Regression Logic)

## 7. Troubleshooting & Gotchas

- **Port 5000**: On macOS, AirPlay Receiver often hogs port 5000. Disable it in System Settings or use `http://127.0.0.1:5000` explicitly.
- **Neo4j Credentials**: Stored in a local `.env` file (not in git). The `run.py` scripts load these automatically.
- **Pydantic Validation**: If `run.py` fails during data loading, it's usually a `ValidationError` in `AnalysisDatasetRow`. Check for unexpected `NaN` values in new columns.
