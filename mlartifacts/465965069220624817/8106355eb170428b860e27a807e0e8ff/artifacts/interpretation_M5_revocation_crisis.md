# Interpretation Report: M5: Revocation + crisis interactions

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **family_connection_ratio**: A one-unit increase decreases the hazard of failure by **0.9%**. (*** p<0.001)
- **family_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.2%**. (+ p<0.1)
- **state_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.3%**. (not significant)
- **foreign_ownership_total_pct**: A one-unit increase decreases the hazard of failure by **0.6%**. (not significant)
- **rw_page_rank_4q_lag**: A one-unit increase increases the hazard of failure by **0.7%**. (not significant)
- **rw_out_degree_4q_lag**: A one-unit increase decreases the hazard of failure by **1.6%**. (+ p<0.1)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **9.5%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **0.1%**. (not significant)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **0.7%**. (* p<0.05)
- **crisis_2004**: A one-unit increase increases the hazard of failure by **0.1%**. (not significant)
- **crisis_2008**: A one-unit increase increases the hazard of failure by **0.1%**. (not significant)
- **crisis_2014**: A one-unit increase increases the hazard of failure by **0.1%**. (not significant)
- **family_connection_ratio_x_crisis_2008**: A one-unit increase decreases the hazard of failure by **0.7%**. (not significant)
- **family_connection_ratio_x_crisis_2014**: A one-unit increase decreases the hazard of failure by **0.9%**. (not significant)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **9.5%** (HR = 0.905)
2. **rw_out_degree_4q_lag**: Reduces hazard by **1.6%** (HR = 0.984)
3. **family_connection_ratio***: Reduces hazard by **0.9%** (HR = 0.991)
4. **family_connection_ratio_x_crisis_2014**: Reduces hazard by **0.9%** (HR = 0.991)
5. **family_connection_ratio_x_crisis_2008**: Reduces hazard by **0.7%** (HR = 0.993)
6. **foreign_ownership_total_pct**: Reduces hazard by **0.6%** (HR = 0.994)
7. **state_ownership_pct**: Reduces hazard by **0.3%** (HR = 0.997)
8. **family_ownership_pct**: Reduces hazard by **0.2%** (HR = 0.998)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **0.7%** (HR = 1.007)
2. **rw_page_rank_4q_lag**: Increases hazard by **0.7%** (HR = 1.007)
3. **camel_npl_ratio**: Increases hazard by **0.1%** (HR = 1.001)
4. **crisis_2014**: Increases hazard by **0.1%** (HR = 1.001)
5. **crisis_2008**: Increases hazard by **0.1%** (HR = 1.001)
6. **crisis_2004**: Increases hazard by **0.1%** (HR = 1.001)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*