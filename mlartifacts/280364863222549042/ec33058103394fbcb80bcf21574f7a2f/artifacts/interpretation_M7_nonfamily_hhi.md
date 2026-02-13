# Interpretation Report: M7_nonfamily_hhi

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **nonfamily_ownership_hhi**: A one-unit increase increases the hazard of failure by **0.2%**. (not significant)
- **family_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.4%**. (*** p<0.001)
- **state_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.4%**. (not significant)
- **foreign_ownership_total_pct**: A one-unit increase decreases the hazard of failure by **0.2%**. (not significant)
- **rw_page_rank_4q_lag**: A one-unit increase increases the hazard of failure by **0.4%**. (not significant)
- **rw_out_degree_4q_lag**: A one-unit increase decreases the hazard of failure by **2.1%**. (* p<0.05)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **8.4%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **1.0%**. (*** p<0.001)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **1.6%**. (*** p<0.001)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **8.4%** (HR = 0.916)
2. **rw_out_degree_4q_lag***: Reduces hazard by **2.1%** (HR = 0.979)
3. **family_ownership_pct***: Reduces hazard by **0.4%** (HR = 0.996)
4. **state_ownership_pct**: Reduces hazard by **0.4%** (HR = 0.996)
5. **foreign_ownership_total_pct**: Reduces hazard by **0.2%** (HR = 0.998)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **1.6%** (HR = 1.016)
2. **camel_npl_ratio***: Increases hazard by **1.0%** (HR = 1.010)
3. **rw_page_rank_4q_lag**: Increases hazard by **0.4%** (HR = 1.004)
4. **nonfamily_ownership_hhi**: Increases hazard by **0.2%** (HR = 1.002)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*