# Interpretation Report: Model 6: Full

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **174.4%**. (** p<0.01)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **1.2%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **36.7%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase increases the hazard of failure by **27.4%**. (not significant)
- **family_FOP**: A one-unit increase decreases the hazard of failure by **0.3%**. (* p<0.05)
- **family_rho_F**: A one-unit increase decreases the hazard of failure by **15.3%**. (*** p<0.001)
- **foreign_FOP_t**: A one-unit increase increases the hazard of failure by **0.0%**. (not significant)
- **foreign_FEC_d**: A one-unit increase decreases the hazard of failure by **0.0%**. (* p<0.05)
- **state_SOP**: A one-unit increase decreases the hazard of failure by **0.4%**. (not significant)
- **state_SCP**: A one-unit increase decreases the hazard of failure by **0.0%**. (not significant)
- **network_page_rank**: A one-unit increase decreases the hazard of failure by **0.6%**. (** p<0.01)
- **network_betweenness**: A one-unit increase decreases the hazard of failure by **0.0%**. (+ p<0.1)
- **network_C_b**: A one-unit increase decreases the hazard of failure by **3.2%**. (*** p<0.001)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **36.7%** (HR = 0.633)
2. **family_rho_F***: Reduces hazard by **15.3%** (HR = 0.847)
3. **network_C_b***: Reduces hazard by **3.2%** (HR = 0.968)
4. **network_page_rank***: Reduces hazard by **0.6%** (HR = 0.994)
5. **state_SOP**: Reduces hazard by **0.4%** (HR = 0.996)
6. **family_FOP***: Reduces hazard by **0.3%** (HR = 0.997)
7. **foreign_FEC_d***: Reduces hazard by **0.0%** (HR = 1.000)
8. **network_betweenness**: Reduces hazard by **0.0%** (HR = 1.000)
9. **state_SCP**: Reduces hazard by **0.0%** (HR = 1.000)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **174.4%** (HR = 2.744)
2. **camel_liquid_assets_ratio**: Increases hazard by **27.4%** (HR = 1.274)
3. **camel_npl_ratio***: Increases hazard by **1.2%** (HR = 1.012)
4. **foreign_FOP_t**: Increases hazard by **0.0%** (HR = 1.000)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*