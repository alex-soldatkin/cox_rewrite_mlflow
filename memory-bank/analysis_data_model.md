# Analysis Data Model & Variable Dictionary

This document details the data structures used for the "Factions & Networks" thesis re-analysis. It describes how raw data sources (Accounting, Graph, Rolling Windows) are transformed into a unified `AnalysisDatasetRow` for statistical modeling (Survival Analysis, Panel Regression).

## 1. Unified Analysis Schema (`AnalysisDatasetRow`)

The core unit of analysis is a **Bank-Observation** (e.g., Bank-Month, Bank-Quarter or Bank-Year). This is represented by the `AnalysisDatasetRow` model in `data_models/analysis.py`.

### Primary Identifier & Target

| Field           | Type    | Description                                                             | Usage                                             |
| --------------- | ------- | ----------------------------------------------------------------------- | ------------------------------------------------- |
| `regn`          | `int`   | CBR Registration Number. Unique ID for banks.                           | Primary Key (Entity).                             |
| `date`          | `date`  | Observation date (e.g., 2015-01-01).                                    | Primary Key (Time).                               |
| `failed`        | `bool`  | True if the bank license was revoked in the subsequent period.          | **Dependent Variable** (Binary Classification).   |
| `survival_time` | `float` | Time (days/years) until failure or censoring.                           | **Dependent Variable** (Survival Analysis / Cox). |
| `is_crisis`     | `bool`  | 1 if observation falls in crisis years (2008-09, 2014-15), 0 otherwise. | Control / Interaction Term.                       |

### Component 1: CAMEL Indicators (`CamelIndicators`)

_Source_: `data_models/accounting.py` (`AccountingRecord` from Form 101/102).

Standard financial health controls used in banking literature.

| Variable          | Field Path                  | Definition / Derivation       | Expected Impact                          |
| ----------------- | --------------------------- | ----------------------------- | ---------------------------------------- |
| **Capital**       | `camel.tier1_capital_ratio` | Total Equity / Total Assets   | (-) Higher capital reduces failure risk. |
|                   | `camel.leverage_ratio`      | Equity / Assets               | (-) Similar to Tier 1.                   |
| **Asset Quality** | `camel.npl_ratio`           | NPL / Total Loans             | (+) Bad loans increase failure risk.     |
|                   | `camel.llp_ratio`           | Loan Loss Provisions / Loans  | (+) Proxy for expected losses.           |
| **Management**    | `camel.cost_to_income`      | Operating Exp / Operating Inc | (+) Inefficiency increases risk.         |
| **Earnings**      | `camel.roa`                 | Net Income / Assets           | (-) Profitability aids survival.         |
|                   | `camel.roe`                 | Net Income / Equity           | (-) Alternative profit metric.           |
| **Liquidity**     | `camel.liquid_assets_ratio` | Liquid Assets / Total Assets  | (-) Liquidity buffer prevents runs.      |

### Component 2: Network Topology (`NetworkTopologyMetrics`)

_Source_: `data_models/rolling_windows.py` (`RollingWindowNodeFeatures`) or `data_models/graph.py` (`GraphEnrichedNode`).

Measures the bank's position within the ownership/social graph at time $t$.

| Variable       | Field Path                     | Definition                                           | Hypothesis / Usage                                |
| -------------- | ------------------------------ | ---------------------------------------------------- | ------------------------------------------------- |
| **Centrality** | `network.page_rank`            | PageRank score in the ownership graph.               | High PR -> Systemic Importance? or High exposure? |
|                | `network.degree`               | Total connections (In + Out).                        | General connectedness.                            |
|                | `network.eigenvector`          | Connection to influential nodes.                     | Implicit power/influence.                         |
| **Complexity** | `network.ownership_complexity` | ($C_b$) Score based on path lengths & unique owners. | (+) Complexity hides bad risks / expropriation.   |

### Component 3: Family Ownership (`FamilyOwnershipMetrics`)

_Source_: Path-finding algorithms in Neo4j (`GraphEnrichedNode` / custom queries).

Variables quantifying kinship ties within the bank's ownership structure.

| Variable         | Field Path                           | Definition                                | Hypothesis                                  |
| ---------------- | ------------------------------------ | ----------------------------------------- | ------------------------------------------- | ------------------------------------------------- | ----------------------------------------- |
| **Family Value** | `family.family_ownership_pct`        | ($FOP$) % of bank owned by family groups. | U-shaped? Family support vs. Expropriation. |
| **Connectivity** | `family.total_family_connections`    | ($                                        | F_b                                         | $) Count of kinship ties among owners.            | (+) Cohesion / Collusion.                 |
| **Control**      | `family.family_controlled_companies` | ($                                        | C_F                                         | $) Num. of companies controlled by bank families. | (+) Empire building / Resource tunneling. |

### Component 4: State & Foreign Ownership

_Source_: Owner node attributes and paths in Neo4j.

| Variable    | Field Path                      | Definition                              | Hypothesis                                      |
| ----------- | ------------------------------- | --------------------------------------- | ----------------------------------------------- |
| **State**   | `state.state_ownership_pct`     | ($SOP$) % owned by Govt/State entities. | (-) Implicit state guarantee (Too Big To Fail). |
| **Foreign** | `foreign.foreign_ownership_pct` | ($FOP_d$) % owned by non-RU entities.   | (+/-) Better governance or higher flight risk?  |

---

## 2. Data Flow & Linkage

The `AnalysisDatasetRow.create_row(...)` factory method orchestrates the assembly of these components:

1.  **Accounting Data Step**:
    - Input: `AccountingRecord` (raw SQL/Parquet data).
    - Transformation: `CamelIndicators.from_accounting_record()`.
    - Logic: Ratios are computed (e.g., `equity / assets`) handling zero-division.

2.  **Graph/Rolling Step**:
    - Input: `RollingWindowNodeFeatures` (Parquet from GraphSAGE/RW pipeline) **OR** `GraphEnrichedNode` (Direct Neo4j fetch).
    - Transformation: `NetworkTopologyMetrics.from_rolling_features()`.
    - Logic: Maps `page_rank`, `degree` from graph-calculated properties.

3.  **Ownership Step**:
    - Input: Pre-computed ownership metrics (likely from complex Cypher queries or specific extraction pipelines).
    - Transformation: Passed directly into `FamilyOwnershipMetrics` etc.

## 3. Usage in Analysis

The resulting dataset is a panel $D = \{ (Y_{it}, \mathbf{X}_{it}) \}$ where:

- $i$ = Bank (regn)
- $t$ = Time (Quarter/Year)

### Failure Prediction Models

- **Cox Proportional Hazards**: `Surv(survival_time, failed) ~ CAMEL + Network + Family + E`
- **Logistic Regression**: `logit(P(failed)) ~ CAMEL + Network + Family + Controls`

The modular schema allowing swapping "Network" features (e.g., trying `PageRank` vs `Eigenvector`) while keeping "CAMEL" controls constant ensures robust testing of hypotheses.
