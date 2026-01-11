# Interpretation Report: Model 6: Full

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **460.6%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **1.8%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **40.0%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase increases the hazard of failure by **5.8%**. (not significant)
- **network_in_degree**: A one-unit increase decreases the hazard of failure by **0.0%**. (not significant)
- **network_out_degree**: A one-unit increase decreases the hazard of failure by **25.3%**. (*** p<0.001)
- **network_page_rank**: A one-unit increase decreases the hazard of failure by **1.4%**. (* p<0.05)
- **family_FOP**: A one-unit increase decreases the hazard of failure by **0.4%**. (not significant)
- **family_rho_F**: A one-unit increase decreases the hazard of failure by **57.6%**. (*** p<0.001)
- **foreign_FOP_t**: A one-unit increase increases the hazard of failure by **0.0%**. (not significant)
- **foreign_FEC_d**: A one-unit increase decreases the hazard of failure by **0.5%**. (*** p<0.001)
- **state_SOP**: A one-unit increase decreases the hazard of failure by **1.9%**. (not significant)
- **state_SCP**: A one-unit increase increases the hazard of failure by **0.0%**. (not significant)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **family_rho_F***: Reduces hazard by **57.6%** (HR = 0.424)
2. **camel_roa***: Reduces hazard by **40.0%** (HR = 0.600)
3. **network_out_degree***: Reduces hazard by **25.3%** (HR = 0.747)
4. **state_SOP**: Reduces hazard by **1.9%** (HR = 0.981)
5. **network_page_rank***: Reduces hazard by **1.4%** (HR = 0.986)
6. **foreign_FEC_d***: Reduces hazard by **0.5%** (HR = 0.995)
7. **family_FOP**: Reduces hazard by **0.4%** (HR = 0.996)
8. **network_in_degree**: Reduces hazard by **0.0%** (HR = 1.000)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **460.6%** (HR = 5.606)
2. **camel_liquid_assets_ratio**: Increases hazard by **5.8%** (HR = 1.058)
3. **camel_npl_ratio***: Increases hazard by **1.8%** (HR = 1.018)
4. **foreign_FOP_t**: Increases hazard by **0.0%** (HR = 1.000)
5. **state_SCP**: Increases hazard by **0.0%** (HR = 1.000)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*