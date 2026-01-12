# Interpretation Report: M5: Foreign × Crisis

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **family_connection_ratio**: A one-unit increase decreases the hazard of failure by **1.1%**. (*** p<0.001)
- **family_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.3%**. (** p<0.01)
- **state_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.4%**. (not significant)
- **foreign_ownership_total_pct**: A one-unit increase decreases the hazard of failure by **0.4%**. (not significant)
- **rw_page_rank_4q_lag**: A one-unit increase increases the hazard of failure by **0.3%**. (not significant)
- **rw_out_degree_4q_lag**: A one-unit increase decreases the hazard of failure by **1.8%**. (* p<0.05)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **8.2%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **1.0%**. (*** p<0.001)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **1.6%**. (*** p<0.001)
- **crisis_2008**: A one-unit increase increases the hazard of failure by **0.1%**. (not significant)
- **crisis_2014**: A one-unit increase increases the hazard of failure by **0.1%**. (not significant)
- **foreign_ownership_total_pct_x_crisis_2008**: A one-unit increase decreases the hazard of failure by **0.5%**. (not significant)
- **foreign_ownership_total_pct_x_crisis_2014**: A one-unit increase increases the hazard of failure by **2.1%**. (not significant)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **8.2%** (HR = 0.918)
2. **rw_out_degree_4q_lag***: Reduces hazard by **1.8%** (HR = 0.982)
3. **family_connection_ratio***: Reduces hazard by **1.1%** (HR = 0.989)
4. **foreign_ownership_total_pct_x_crisis_2008**: Reduces hazard by **0.5%** (HR = 0.995)
5. **state_ownership_pct**: Reduces hazard by **0.4%** (HR = 0.996)
6. **foreign_ownership_total_pct**: Reduces hazard by **0.4%** (HR = 0.996)
7. **family_ownership_pct***: Reduces hazard by **0.3%** (HR = 0.997)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **foreign_ownership_total_pct_x_crisis_2014**: Increases hazard by **2.1%** (HR = 1.021)
2. **camel_tier1_capital_ratio***: Increases hazard by **1.6%** (HR = 1.016)
3. **camel_npl_ratio***: Increases hazard by **1.0%** (HR = 1.010)
4. **rw_page_rank_4q_lag**: Increases hazard by **0.3%** (HR = 1.003)
5. **crisis_2014**: Increases hazard by **0.1%** (HR = 1.001)
6. **crisis_2008**: Increases hazard by **0.1%** (HR = 1.001)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*