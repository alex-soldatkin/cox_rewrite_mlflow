# Interpretation Report: M2: Crisis 2014 Indicator

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **family_connection_ratio**: A one-unit increase decreases the hazard of failure by **1.1%**. (*** p<0.001)
- **family_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.3%**. (not significant)
- **state_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.5%**. (not significant)
- **foreign_ownership_total_pct**: A one-unit increase decreases the hazard of failure by **0.0%**. (not significant)
- **rw_page_rank_4q_lag**: A one-unit increase increases the hazard of failure by **0.2%**. (not significant)
- **rw_out_degree_4q_lag**: A one-unit increase decreases the hazard of failure by **2.3%**. (* p<0.05)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **8.9%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **0.4%**. (* p<0.05)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **1.6%**. (*** p<0.001)
- **crisis_2014**: A one-unit increase decreases the hazard of failure by **2.0%**. (not significant)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **8.9%** (HR = 0.911)
2. **rw_out_degree_4q_lag***: Reduces hazard by **2.3%** (HR = 0.977)
3. **crisis_2014**: Reduces hazard by **2.0%** (HR = 0.980)
4. **family_connection_ratio***: Reduces hazard by **1.1%** (HR = 0.989)
5. **state_ownership_pct**: Reduces hazard by **0.5%** (HR = 0.995)
6. **family_ownership_pct**: Reduces hazard by **0.3%** (HR = 0.997)
7. **foreign_ownership_total_pct**: Reduces hazard by **0.0%** (HR = 1.000)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **1.6%** (HR = 1.016)
2. **camel_npl_ratio***: Increases hazard by **0.4%** (HR = 1.004)
3. **rw_page_rank_4q_lag**: Increases hazard by **0.2%** (HR = 1.002)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*