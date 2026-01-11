# Interpretation Report: Model 5: Full

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_roa**: A one-unit increase decreases the hazard of failure by **9.8%**. (*** p<0.001)
- **family_rho_F**: A one-unit increase decreases the hazard of failure by **3.0%**. (*** p<0.001)
- **network_out_degree**: A one-unit increase decreases the hazard of failure by **37.6%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **0.9%**. (*** p<0.001)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **1.6%**. (** p<0.01)
- **network_page_rank**: A one-unit increase decreases the hazard of failure by **1.3%**. (+ p<0.1)
- **foreign_FEC_d**: A one-unit increase decreases the hazard of failure by **10.7%**. (*** p<0.001)
- **family_FOP**: A one-unit increase decreases the hazard of failure by **0.3%**. (not significant)
- **camel_liquid_assets_ratio**: A one-unit increase increases the hazard of failure by **1.0%**. (not significant)
- **state_SOP**: A one-unit increase decreases the hazard of failure by **1.4%**. (not significant)
- **state_SCP**: A one-unit increase increases the hazard of failure by **0.8%**. (not significant)
- **foreign_FOP_t**: A one-unit increase increases the hazard of failure by **1.5%**. (not significant)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **network_out_degree***: Reduces hazard by **37.6%** (HR = 0.624)
2. **foreign_FEC_d***: Reduces hazard by **10.7%** (HR = 0.893)
3. **camel_roa***: Reduces hazard by **9.8%** (HR = 0.902)
4. **family_rho_F***: Reduces hazard by **3.0%** (HR = 0.970)
5. **state_SOP**: Reduces hazard by **1.4%** (HR = 0.986)
6. **network_page_rank**: Reduces hazard by **1.3%** (HR = 0.987)
7. **family_FOP**: Reduces hazard by **0.3%** (HR = 0.997)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **1.6%** (HR = 1.016)
2. **foreign_FOP_t**: Increases hazard by **1.5%** (HR = 1.015)
3. **camel_liquid_assets_ratio**: Increases hazard by **1.0%** (HR = 1.010)
4. **camel_npl_ratio***: Increases hazard by **0.9%** (HR = 1.009)
5. **state_SCP**: Increases hazard by **0.8%** (HR = 1.008)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*