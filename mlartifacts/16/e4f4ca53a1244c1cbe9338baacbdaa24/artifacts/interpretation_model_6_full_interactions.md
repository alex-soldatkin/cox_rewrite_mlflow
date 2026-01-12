# Interpretation Report: M6: Full Interactions (2014)

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **family_connection_ratio**: A one-unit increase decreases the hazard of failure by **1.1%**. (*** p<0.001)
- **family_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.3%**. (not significant)
- **state_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.5%**. (not significant)
- **foreign_ownership_total_pct**: A one-unit increase decreases the hazard of failure by **0.7%**. (not significant)
- **rw_page_rank_4q_lag**: A one-unit increase increases the hazard of failure by **0.2%**. (not significant)
- **rw_out_degree_4q_lag**: A one-unit increase decreases the hazard of failure by **2.3%**. (* p<0.05)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **8.9%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **0.4%**. (* p<0.05)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **1.6%**. (*** p<0.001)
- **crisis_2014**: A one-unit increase decreases the hazard of failure by **1.9%**. (not significant)
- **family_connection_ratio_x_crisis_2014**: A one-unit increase decreases the hazard of failure by **0.9%**. (not significant)
- **state_ownership_pct_x_crisis_2014**: A one-unit increase decreases the hazard of failure by **0.6%**. (not significant)
- **foreign_ownership_total_pct_x_crisis_2014**: A one-unit increase increases the hazard of failure by **2.1%**. (not significant)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **8.9%** (HR = 0.911)
2. **rw_out_degree_4q_lag***: Reduces hazard by **2.3%** (HR = 0.977)
3. **crisis_2014**: Reduces hazard by **1.9%** (HR = 0.981)
4. **family_connection_ratio***: Reduces hazard by **1.1%** (HR = 0.989)
5. **family_connection_ratio_x_crisis_2014**: Reduces hazard by **0.9%** (HR = 0.991)
6. **foreign_ownership_total_pct**: Reduces hazard by **0.7%** (HR = 0.993)
7. **state_ownership_pct_x_crisis_2014**: Reduces hazard by **0.6%** (HR = 0.994)
8. **state_ownership_pct**: Reduces hazard by **0.5%** (HR = 0.995)
9. **family_ownership_pct**: Reduces hazard by **0.3%** (HR = 0.997)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **foreign_ownership_total_pct_x_crisis_2014**: Increases hazard by **2.1%** (HR = 1.021)
2. **camel_tier1_capital_ratio***: Increases hazard by **1.6%** (HR = 1.016)
3. **camel_npl_ratio***: Increases hazard by **0.4%** (HR = 1.004)
4. **rw_page_rank_4q_lag**: Increases hazard by **0.2%** (HR = 1.002)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*