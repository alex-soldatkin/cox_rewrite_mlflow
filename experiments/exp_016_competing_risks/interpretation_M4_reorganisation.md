# Interpretation Report: M4: Reorganisation only

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **family_connection_ratio**: A one-unit increase decreases the hazard of failure by **0.3%**. (not significant)
- **family_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.2%**. (not significant)
- **state_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.2%**. (not significant)
- **foreign_ownership_total_pct**: A one-unit increase increases the hazard of failure by **0.6%**. (not significant)
- **rw_page_rank_4q_lag**: A one-unit increase decreases the hazard of failure by **0.3%**. (not significant)
- **rw_out_degree_4q_lag**: A one-unit increase decreases the hazard of failure by **0.4%**. (not significant)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **2.8%**. (not significant)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **1.0%**. (*** p<0.001)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **0.1%**. (not significant)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa**: Reduces hazard by **2.8%** (HR = 0.972)
2. **rw_out_degree_4q_lag**: Reduces hazard by **0.4%** (HR = 0.996)
3. **family_connection_ratio**: Reduces hazard by **0.3%** (HR = 0.997)
4. **rw_page_rank_4q_lag**: Reduces hazard by **0.3%** (HR = 0.997)
5. **family_ownership_pct**: Reduces hazard by **0.2%** (HR = 0.998)
6. **state_ownership_pct**: Reduces hazard by **0.2%** (HR = 0.998)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_npl_ratio***: Increases hazard by **1.0%** (HR = 1.010)
2. **foreign_ownership_total_pct**: Increases hazard by **0.6%** (HR = 1.006)
3. **camel_tier1_capital_ratio**: Increases hazard by **0.1%** (HR = 1.001)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*