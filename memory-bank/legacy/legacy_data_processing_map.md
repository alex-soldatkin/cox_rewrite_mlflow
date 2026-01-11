# Legacy Data Processing Map

**Directory:** `DATA_PROCESSING_DIR`
**Path:** `/Users/alexandersoldatkin/projects/factions-networks-thesis/data_processing`

This directory handles the raw data processing, transformation, and imputation logic.

## Core Scripts

### 1. `get_seo_accounting_years.py`

- **Purpose**: Extracts accounting year availability for entities from a large declarations JSON file.
- **Input**: Large JSON file (user prompted).
- **Output**: `accounting_inn_id.jsonl` containing `Id`, `Inn`, and available `Years` for entities with financial info (`InfoCounters['Finance'] > 0`).

### 2. `split_large_json.py`

- **Purpose**: Splits a massive JSON file into smaller, manageable chunks (JSONL format).
- **Input**: Large JSON file.
- **Output**: Multiple keys/files in a specified directory (e.g., `../data/split_json/filename_i.jsonl`).
- **Usage**: Useful for processing the 60GB+ declarations file.

### 3. `stream_large_file.py`

- **Purpose**: Streams and downloads a large file from a URL (defaulting to `declarator.org` dumps) to disk.
- **Input**: URL.
- **Output**: Saved file on disk.

## Subdirectory: `cbr_accounting/`

Detailed accounting data processing and imputation.

### 1. `cbr_aggregation.py`

- **Purpose**: Aggregates and standardizes Central Bank of Russia (CBR) Forms 101 and 102 data.
- **Key Logic**:
  - Defines complex SQL queries (using DuckDB or similar SQL dialect in Python strings) to map legacy account codes to modern standards.
  - Calculates derived metrics: `net_interest_income`, `ROA`, `ROE`, `NIM`, etc.
  - Performs accounting identity checks (`assets = liabilities + equity`).
  - Generates a final report and saves to Parquet.
- **Output**: `final_final_banking_indicators.parquet` (implied from context) or `OUTPUT_PARQUET`.

### 2. `cbr_imputation.py`

- **Purpose**: Imputes missing values in banking data using a panel data approach.
- **Class**: `PanelImputer`
- **Key Logic**:
  - **Flows (Income/Expense)**: Upsamples quarterly/yearly data to monthly using cubic spline interpolation (`scipy.interpolate.CubicSpline`) or simply filling gaps.
  - **Stocks (Assets/Liabilities)**: Uses State Space Models (SSM) via `statsmodels` (`UnobservedComponents`) to impute missing stock values, or falls back to cubic interpolation in fast mode.
  - **Reconciliation**: Re-enforces accounting identities after imputation.
  - **Parallel Processing**: Uses `ThreadPoolExecutor` to process multiple banks (REGN) in parallel.
- **Input**: Parquet file (e.g., `final_banking_indicators_imputed.parquet`).
- **Output**: Fully imputed dataset and audit logs (`OUT_AUDIT`).
