# Interpretation Report: Model 6: Full

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the odds of failure by **284.1%**. (* p<0.05)
- **camel_npl_ratio**: A one-unit increase increases the odds of failure by **2.2%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the odds of failure by **46.8%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase decreases the odds of failure by **60.4%**. (not significant)
- **family_FOP**: A one-unit increase decreases the odds of failure by **0.4%**. (not significant)
- **family_rho_F**: A one-unit increase decreases the odds of failure by **33.2%**. (* p<0.05)
- **foreign_FOP_t**: A one-unit increase increases the odds of failure by **0.0%**. (* p<0.05)
- **foreign_FEC_d**: A one-unit increase decreases the odds of failure by **0.3%**. (* p<0.05)
- **state_SOP**: A one-unit increase decreases the odds of failure by **2.3%**. (not significant)
- **state_SCP**: A one-unit increase increases the odds of failure by **0.0%**. (* p<0.05)
- **network_page_rank**: A one-unit increase increases the odds of failure by **0.2%**. (not significant)
- **network_betweenness**: A one-unit increase decreases the odds of failure by **0.0%**. (** p<0.01)
- **network_C_b**: A one-unit increase decreases the odds of failure by **8.8%**. (*** p<0.001)

## 2. Most Protective Variables (Decreased Odds)
Ranked by strength of protection (largest % decrease in odds).

2. **camel_liquid_assets_ratio**: Reduces odds by **60.4%** (OR = 0.396)
3. **camel_roa***: Reduces odds by **46.8%** (OR = 0.532)
4. **family_rho_F***: Reduces odds by **33.2%** (OR = 0.668)
5. **network_C_b***: Reduces odds by **8.8%** (OR = 0.912)
6. **state_SOP**: Reduces odds by **2.3%** (OR = 0.977)
7. **family_FOP**: Reduces odds by **0.4%** (OR = 0.996)
8. **foreign_FEC_d***: Reduces odds by **0.3%** (OR = 0.997)
9. **network_betweenness***: Reduces odds by **0.0%** (OR = 1.000)

## 3. Highest Risk Variables (Increased Odds)
Ranked by strength of risk (largest % increase in odds).

1. **camel_tier1_capital_ratio***: Increases odds by **284.1%** (OR = 3.841)
2. **camel_npl_ratio***: Increases odds by **2.2%** (OR = 1.022)
3. **network_page_rank**: Increases odds by **0.2%** (OR = 1.002)
4. **foreign_FOP_t***: Increases odds by **0.0%** (OR = 1.000)
5. **state_SCP***: Increases odds by **0.0%** (OR = 1.000)

---
*Note: Interpretations assume ceteris paribus. Significance: * p < 0.05.*