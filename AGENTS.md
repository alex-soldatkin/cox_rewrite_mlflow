# AGENTS.md

This document serves as the **primary entry point** for AI agents and developers working on the `cos_rewrite_mlflow` project. It consolidates rules, workflows, and navigation paths to ensure consistent, high-quality contributions.

## 🚨 Critical Rules (from `GEMINI.md`)

- **Language**: strictly **British English** (e.g., `colour`, `standardise`).
- **Data Access**: 
    - **Neo4j**: **READ-ONLY**. Use credentials from `.env`.
    - **Old Files**: Read-only access to paths in `.env`.
- **Code Style**:
    - **Modular**: Keep code in subdirectories.
    - **Pydantic**: Use `data_models/` for ALL structured data (Analysis, Graph, Accounting).
- **Environment**: Use **`uv`** for management.
- **Visualisation**: Follow `memory-bank/LETS_PLOT_BEST_PRACTICES.md` strictly.

---

## 🧭 Navigation

| Path | Description |
| :--- | :--- |
| **@[memory-bank](memory-bank/)** | **Core Context**. `experiment_framework.md` (Architecture) & `analysis_data_model.md` (Schema). |
| **@[experiments](experiments/)** | **Sandbox**. `exp_000_template/` is the golden standard. |
| **@[mlflow_utils](mlflow_utils/)** | **Infrastructure**. `ExperimentDataLoader` and tracking logic. |
| **[data_models/](data_models/)** | **Schemas**. Pydantic definitions for `AnalysisDatasetRow`, `AccountingRecord`, etc. |
| **[queries/cypher](queries/cypher/)** | **Graph Queries**. Standard Cypher queries. Always reuse or add new `NNN_name.cypher` files here. |
| **[stargazer/](stargazer/)** | **Results**. Aggregated regression tables (CSV/LaTeX) ready for paper inclusion. |
| **[mlartifacts/](mlartifacts/)** | **MLflow Storage**. Local file store for run artifacts. **Do not modify manually.** |
| **[lifelines_docs/](lifelines_docs/)** | **Docs**. Offline documentation for the `lifelines` library. |
| **[_debug/](_debug/)** | **Tools**. Scripts for verifying data, migrations, and debugging. |
| **[.env](.env)** | **Config**. Credentials and paths. |

---

## �️ Tools & Workflows

### 1. Dependency Management (`uv`)
- **Run Script**: `uv run python path/to/script.py`
- **Add Package**: `uv add <package>`
- **Remove Package**: `uv remove <package>`
- **MLflow Server**: `uv run mlflow server --port 5000` (Access: `http://127.0.0.1:5000`)

### 2. Experiment Workflow
1.  **Clone**: Copy `experiments/exp_000_template` -> `experiments/exp_NNN_name`.
2.  **Config**: Update `config.yaml` (define `features`, `target`, `human_readable_name`).
3.  **Code**: Modify `run.py`. **MUST** use `ExperimentDataLoader`.
4.  **Run**: `uv run python experiments/exp_NNN_name/run.py`.

### 3. Data Loading Standard
**Do not write ad-hoc SQL/Cypher in scripts.**
```python
from mlflow_utils.loader import ExperimentDataLoader

loader = ExperimentDataLoader()
# Fetches + Merges + Validates against Pydantic Schema
df = loader.load_training_data(start_date="2015-01-01", end_date="2020-01-01")
```

### 4. Visualisation Standard
- **Library**: `lets-plot`.
- **Ref**: `memory-bank/LETS_PLOT_BEST_PRACTICES.md`.
- **Output**: HTML artifacts.

### 5. Memory Bank Usage
**CRITICAL**: The `memory-bank/` is a shared context store.
- **APPEND, DO NOT OVERWRITE**: When adding new findings, append to existing files or create compatible new ones.
- **Do not delete** history unless it is explicitly obsolete.

---

## 📊 Data & Loaders

### Available Data (`data_processing/rolling_windows/output/`)
- **`production_run_1990_2022_v6`**: **Primary Source**. Biannual (2-year) rolling windows.
    - Use `mlflow_utils.temporal_fcr_loader.TemporalFCRLoader` to load this.
    - Contains `fcr_temporal`, `page_rank`, `out_degree`.
- **`quarterly_temporal_fcr_2002_2021_v1`**: Quarterly snapshots for lag analysis.
    - Use `mlflow_utils.quarterly_window_loader.QuarterlyWindowDataLoader`.

### Best Practices for Data Loading
1.  **Use Loaders**: Do not parse parquet files manually.
    - Loaders handle `gds_id` mapping (crucial for Neo4j merging).
    - Loaders handle date alignment (window midpoints vs. accounting dates).
2.  **Lags**: Use built-in lag functions (e.g., `load_with_lags(lag_periods=2)`).
3.  **Neo4j Merging**:
    - **Solution**: Use `gds_id` (internal node ID) for stable merging between Graph and DataFrame.
    - **Avoid**: Merging on `regn` text alone if `gds_id` is available, as it's more robust.

---

## 🐛 Debugging & verification

The `_debug/` directory contains useful one-off scripts. **Check these before writing new verification tools.**

- **Data Checks**:
    - `check_dates.py`: Verify date ranges in parquet files.
    - `check_parquet.py`, `inspect_parquet.py`: Quick look at parquet schemas/content.
- **MLflow**:
    - `debug_mlflow.py`: Connectivity test for local MLflow server.
    - `verify_artifact.py`: Test artifact downloading.
- **Graph/Migations**:
    - `migration_gds_id.py`: Sets `gds_id` on nodes.
    - `global_gds_link_prediction.py`: Example of complex GDS pipeline (Hybrid Link Prediction).

---

## 🧠 Memory Bank Shortcuts

- **[Experiment Framework](memory-bank/experiment_framework.md)**: How experiments are structured.
- **[Data Model](memory-bank/analysis_data_model.md)**: The `AnalysisDatasetRow` schema.
- **[Plotting Guide](memory-bank/LETS_PLOT_BEST_PRACTICES.md)**: Lets-Plot dos and don'ts.
