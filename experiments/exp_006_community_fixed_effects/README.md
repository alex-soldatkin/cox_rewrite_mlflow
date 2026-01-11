# Experiment 006: Community Fixed Effects (2014-2020)

## Overview

This experiment tests within-community versus across-community network effects using Louvain community-level fixed effects. It extends the time-varying rolling window analysis from exp_004 and exp_005 by incorporating community structure.

## Rationale

The continuation guide (line 623) notes:

> "Louvain communities already computed in rolling windows. Multi-level models with community fixed effects to test within-community contagion effects."

This experiment addresses whether:

1. Banks in the same community exhibit correlated failure patterns
2. Network effects are driven by within-community or across-community connections
3. Community structure confounds existing network variable estimates

## Models

### Model 1: Baseline (No Community FE)

Replicates best performing model from exp_005 without community controls.

### Model 2: Community Fixed Effects

Adds community indicator variables (dummy coding) to control for community-level unobserved heterogeneity.

### Model 3: Community + Interactions

Tests whether network effects vary by community through `network_out_degree × community` and `network_page_rank × community` interactions.

### Model 4: Within-Community Network Effects

Uses within-community demeaned network variables to isolate pure within-community effects, controlling for across-community variation.

## Data

- **Period**: 2014-2020 (non-overlapping 2-year windows)
- **Windows**: 3 windows (2014-2016, 2016-2018, 2018-2020)
- **Community Detection**: Louvain algorithm with weighted edges
- **Scaling**: StandardScaler with 0-100 normalization

## Key Features

- Community indicators with small community collapsing (min_size=5)
- Within-community demeaning of network variables
- Time-varying community membership
- Community-clustered standard errors (Logistic models)

## Running the Experiment

```bash
cd experiments/exp_006_community_fixed_effects

# Run Cox models
uv run python run_cox.py

# Run Logistic models
uv run python run_logistic.py
```

## Expected Outcomes

- **C-index improvement** if community FE captures unobserved heterogeneity
- **Network coefficient attenuation** if community structure confounds relationships
- **Persistent network effects** suggest genuine within-community mechanisms
- **Sign reversals** may indicate ecological fallacy or Simpson's paradox

## MLflow

- **Cox Experiment**: `Cox_Community_FE_2014_2020`
- **Logistic Experiment**: `Logistic_Community_FE_2014_2020`
- **UI**: http://127.0.0.1:5000
