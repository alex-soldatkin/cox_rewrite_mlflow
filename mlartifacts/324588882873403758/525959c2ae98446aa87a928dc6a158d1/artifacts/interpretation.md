# Interpretation Report: M3: + Network Controls

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **family_connection_ratio_temporal_lag**: A one-unit increase increases the hazard of failure by **0.9%**. (not significant)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **7.0%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **2.4%**. (*** p<0.001)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **4.2%**. (*** p<0.001)
- **rw_page_rank_4q_lag**: A one-unit increase increases the hazard of failure by **3.1%**. (*** p<0.001)
- **rw_out_degree_4q_lag**: A one-unit increase decreases the hazard of failure by **6.4%**. (*** p<0.001)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **7.0%** (HR = 0.930)
2. **rw_out_degree_4q_lag***: Reduces hazard by **6.4%** (HR = 0.936)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **4.2%** (HR = 1.042)
2. **rw_page_rank_4q_lag***: Increases hazard by **3.1%** (HR = 1.031)
3. **camel_npl_ratio***: Increases hazard by **2.4%** (HR = 1.024)
4. **family_connection_ratio_temporal_lag**: Increases hazard by **0.9%** (HR = 1.009)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*