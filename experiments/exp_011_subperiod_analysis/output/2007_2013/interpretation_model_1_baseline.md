# Interpretation Report: M1: Baseline (2007-2013)

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **family_connection_ratio**: A one-unit increase decreases the hazard of failure by **1.6%**. (*** p<0.001)
- **family_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.5%**. (** p<0.01)
- **state_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.6%**. (not significant)
- **foreign_ownership_total_pct**: A one-unit increase decreases the hazard of failure by **0.1%**. (not significant)
- **rw_page_rank_4q_lag**: A one-unit increase increases the hazard of failure by **1.0%**. (** p<0.01)
- **rw_out_degree_4q_lag**: A one-unit increase decreases the hazard of failure by **4.2%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **1.5%**. (*** p<0.001)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **0.9%**. (* p<0.05)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **rw_out_degree_4q_lag***: Reduces hazard by **4.2%** (HR = 0.958)
2. **family_connection_ratio***: Reduces hazard by **1.6%** (HR = 0.984)
3. **state_ownership_pct**: Reduces hazard by **0.6%** (HR = 0.994)
4. **family_ownership_pct***: Reduces hazard by **0.5%** (HR = 0.995)
5. **foreign_ownership_total_pct**: Reduces hazard by **0.1%** (HR = 0.999)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_npl_ratio***: Increases hazard by **1.5%** (HR = 1.015)
2. **rw_page_rank_4q_lag***: Increases hazard by **1.0%** (HR = 1.010)
3. **camel_tier1_capital_ratio***: Increases hazard by **0.9%** (HR = 1.009)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*