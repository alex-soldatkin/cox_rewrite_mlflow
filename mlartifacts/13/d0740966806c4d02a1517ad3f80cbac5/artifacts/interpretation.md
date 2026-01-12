# Interpretation Report: M1: Baseline (2010-2021)

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **family_connection_ratio**: A one-unit increase decreases the hazard of failure by **1.1%**. (*** p<0.001)
- **family_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.4%**. (* p<0.05)
- **state_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.5%**. (not significant)
- **foreign_ownership_total_pct**: A one-unit increase increases the hazard of failure by **0.0%**. (not significant)
- **rw_page_rank_4q_lag**: A one-unit increase increases the hazard of failure by **0.2%**. (not significant)
- **rw_out_degree_4q_lag**: A one-unit increase decreases the hazard of failure by **1.9%**. (* p<0.05)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **8.7%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **0.6%**. (*** p<0.001)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **1.5%**. (*** p<0.001)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **8.7%** (HR = 0.913)
2. **rw_out_degree_4q_lag***: Reduces hazard by **1.9%** (HR = 0.981)
3. **family_connection_ratio***: Reduces hazard by **1.1%** (HR = 0.989)
4. **state_ownership_pct**: Reduces hazard by **0.5%** (HR = 0.995)
5. **family_ownership_pct***: Reduces hazard by **0.4%** (HR = 0.996)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **1.5%** (HR = 1.015)
2. **camel_npl_ratio***: Increases hazard by **0.6%** (HR = 1.006)
3. **rw_page_rank_4q_lag**: Increases hazard by **0.2%** (HR = 1.002)
4. **foreign_ownership_total_pct**: Increases hazard by **0.0%** (HR = 1.000)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*