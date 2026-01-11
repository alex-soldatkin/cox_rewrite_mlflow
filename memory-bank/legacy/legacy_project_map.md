# Legacy Project Map

This document maps the structure and contents of the legacy project directories as defined in the `.env` file. These directories contain the original data processing pipelines, acquisition scripts, accounting data, and the previous thesis write-up and analysis.

## 1. Data Processing (`DATA_PROCESSING_DIR`)

**Path:** `/Users/alexandersoldatkin/projects/factions-networks-thesis/data_processing`

Contains scripts (Python and Cypher) for processing raw data into the Neo4j graph and other formats.

### Key Subdirectories & Files

- **`cypher/`**: Extensive collection of Cypher queries for graph construction and analysis.
  - `01_process_declarations.cypher` - `25_size_props.cypher`: Nuumbered pipeline steps.
  - Includes steps for:
    - Declaration processing
    - Aggregation (relatives, work)
    - Geocoding (Google, DaData)
    - CBR & Banki.ru data integration
    - Family connection logic
    - Network metrics (Louvain, FastRP, Node2Vec)
- **`cbr_accounting/`**:
  - `cbr_aggregation.py`
  - `cbr_imputation.py`
- **`utils/`**: Utility scripts (assumed).
- **Root Scripts**:
  - `get_seo_accounting_years.py`
  - `split_large_json.py`
  - `stream_large_file.py`

## 2. Data Acquisition (`DATA_ACQ_DIR`)

**Path:** `/Users/alexandersoldatkin/projects/factions-networks-thesis/data_acquisition`

Contains scripts for scraping and acquiring data, along with some raw data files.

### Key Subdirectories & Files

- **`banks_cbr/`**: Scrapy project or similar structure for crawling bank data.
  - `spiders/` (implied by `scrapy.cfg`)
  - `banki_ru_active.jsonl`, `banks_db.jsonl`, `cbr.json`: Scraped data files.
- **Root Scripts**:
  - `async_reputation_seo.py`, `reputation_seo_neo.py`
  - `dadata_geocoding.py`, `google_geocoding_api.py`: Geocoding interfaces.
  - `reputation_accounting.py`, `reputation_client_search.py`
- **Data Files**:
  - `banks_data.jsonl`, `companies_data.jsonl`
  - `org_data.jsonl`, `seo_sample.json`

## 3. Accounting (`ACCOUNTING_DIR`)

**Path:** `/Users/alexandersoldatkin/projects/factions-networks-thesis/drafts/accounting_cbr_imputed`

Contains processed/imputed accounting data in Parquet format.

### Key Files

- `final_banking_indicators_imputed.parquet`
- `final_final_banking_indicators.parquet`
- `imputation_audit.parquet`

## 4. Old Writeup & Analysis (`OLD_WRITEUP_DIR`)

**Path:** `/Users/alexandersoldatkin/projects/factions-networks-thesis/drafts/families`

Contains the previous thesis analysis, including notebooks, regression models, and the write-up text.

### Key Subdirectories & Files

- **Analysis Notebooks**:
  - `survival_analysis.ipynb`, `cox_extended.ipynb`, `cox_extended_financials.ipynb`
  - `town_analysis_itsa.ipynb` (implied `family_analysis_itsa.ipynb`)
  - `family_analysis_notebook.ipynb`, `family_analysis_updated_notebook.ipynb`
  - `db_revoked_stats.ipynb`, `db_vis_revocation.ipynb`
- **Python Scripts**:
  - `family_regression_analysis.py`, `family_regression_timeseries.py`, `panel_regression.py`
  - `stargazer_cox.py`
  - `family_visualizations.py`, `cox_predictions_plot.py`
- **Writeup Markdown**:
  - `writeup` (directory)
  - `family_ownership.md`, `family_ownership_background.md`, `family_ownership_theory_maths.md`
- **Figures & Plots**:
  - `figures/`, `plots/`, `lets-plot-images/`
  - `family_survival_counts.png`, `family_survival_probability.png`

---

_Note: This map is generated based on a file system listing and file naming conventions._
