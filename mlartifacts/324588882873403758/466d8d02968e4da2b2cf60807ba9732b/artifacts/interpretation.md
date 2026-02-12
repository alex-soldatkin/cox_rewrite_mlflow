# Interpretation Report: M5: Full + Stratified

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **family_connection_ratio_temporal_lag**: A one-unit increase increases the hazard of failure by **0.9%**. (not significant)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **7.4%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **2.5%**. (*** p<0.001)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **4.2%**. (*** p<0.001)
- **rw_page_rank_4q_lag**: A one-unit increase increases the hazard of failure by **3.1%**. (*** p<0.001)
- **rw_out_degree_4q_lag**: A one-unit increase decreases the hazard of failure by **6.8%**. (*** p<0.001)
- **family_ownership_pct**: A one-unit increase decreases the hazard of failure by **0.3%**. (not significant)
- **foreign_ownership_total_pct**: A one-unit increase increases the hazard of failure by **0.8%**. (not significant)
- **state_ownership_pct**: A one-unit increase decreases the hazard of failure by **1.3%**. (not significant)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **7.4%** (HR = 0.926)
2. **rw_out_degree_4q_lag***: Reduces hazard by **6.8%** (HR = 0.932)
3. **state_ownership_pct**: Reduces hazard by **1.3%** (HR = 0.987)
4. **family_ownership_pct**: Reduces hazard by **0.3%** (HR = 0.997)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **4.2%** (HR = 1.042)
2. **rw_page_rank_4q_lag***: Increases hazard by **3.1%** (HR = 1.031)
3. **camel_npl_ratio***: Increases hazard by **2.5%** (HR = 1.025)
4. **family_connection_ratio_temporal_lag**: Increases hazard by **0.9%** (HR = 1.009)
5. **foreign_ownership_total_pct**: Increases hazard by **0.8%** (HR = 1.008)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*