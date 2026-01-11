# Interpretation Report: M2: Community Stratified

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **rw_page_rank_4q_lag**: A one-unit increase increases the hazard of failure by **0.2%**. (not significant)
- **rw_out_degree_4q_lag**: A one-unit increase decreases the hazard of failure by **2.3%**. (* p<0.05)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **9.0%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **0.4%**. (* p<0.05)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **1.7%**. (*** p<0.001)
- **family_connection_ratio**: A one-unit increase decreases the hazard of failure by **1.2%**. (*** p<0.001)
- **family_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.3%**. (+ p<0.1)
- **foreign_ownership_total_pct**: A one-unit increase increases the hazard of failure by **0.0%**. (not significant)
- **state_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.6%**. (not significant)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **9.0%** (HR = 0.910)
2. **rw_out_degree_4q_lag***: Reduces hazard by **2.3%** (HR = 0.977)
3. **family_connection_ratio***: Reduces hazard by **1.2%** (HR = 0.988)
4. **state_ownership_pct**: Reduces hazard by **0.6%** (HR = 0.994)
5. **family_ownership_pct**: Reduces hazard by **0.3%** (HR = 0.997)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **1.7%** (HR = 1.017)
2. **camel_npl_ratio***: Increases hazard by **0.4%** (HR = 1.004)
3. **rw_page_rank_4q_lag**: Increases hazard by **0.2%** (HR = 1.002)
4. **foreign_ownership_total_pct**: Increases hazard by **0.0%** (HR = 1.000)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*