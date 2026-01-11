# Interpretation Report: M2: Simple Lagged Network (t-4Q)

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **rw_page_rank_4q_lag**: A one-unit increase increases the hazard of failure by **0.3%**. (not significant)
- **rw_out_degree_4q_lag**: A one-unit increase decreases the hazard of failure by **2.2%**. (* p<0.05)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **8.9%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **0.4%**. (* p<0.05)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **1.5%**. (*** p<0.001)
- **family_rho_F**: A one-unit increase decreases the hazard of failure by **1.2%**. (*** p<0.001)
- **foreign_FEC_d**: A one-unit increase decreases the hazard of failure by **0.5%**. (*** p<0.001)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **8.9%** (HR = 0.911)
2. **rw_out_degree_4q_lag***: Reduces hazard by **2.2%** (HR = 0.978)
3. **family_rho_F***: Reduces hazard by **1.2%** (HR = 0.988)
4. **foreign_FEC_d***: Reduces hazard by **0.5%** (HR = 0.995)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **1.5%** (HR = 1.015)
2. **camel_npl_ratio***: Increases hazard by **0.4%** (HR = 1.004)
3. **rw_page_rank_4q_lag**: Increases hazard by **0.3%** (HR = 1.003)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*