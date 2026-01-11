# Interpretation Report: Model 4: +Foreign

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the odds of failure by **490.5%**. (** p<0.01)
- **camel_npl_ratio**: A one-unit increase increases the odds of failure by **2.1%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the odds of failure by **45.1%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase decreases the odds of failure by **74.8%**. (+ p<0.1)
- **network_in_degree**: A one-unit increase decreases the odds of failure by **0.0%**. (not significant)
- **network_out_degree**: A one-unit increase decreases the odds of failure by **23.4%**. (*** p<0.001)
- **network_page_rank**: A one-unit increase decreases the odds of failure by **1.0%**. (not significant)
- **family_FOP**: A one-unit increase decreases the odds of failure by **0.5%**. (not significant)
- **family_rho_F**: A one-unit increase decreases the odds of failure by **50.6%**. (*** p<0.001)
- **foreign_FOP_t**: A one-unit increase decreases the odds of failure by **0.0%**. (not significant)
- **foreign_FEC_d**: A one-unit increase decreases the odds of failure by **0.4%**. (** p<0.01)

## 2. Most Protective Variables (Decreased Odds)
Ranked by strength of protection (largest % decrease in odds).

2. **camel_liquid_assets_ratio**: Reduces odds by **74.8%** (OR = 0.252)
3. **family_rho_F***: Reduces odds by **50.6%** (OR = 0.494)
4. **camel_roa***: Reduces odds by **45.1%** (OR = 0.549)
5. **network_out_degree***: Reduces odds by **23.4%** (OR = 0.766)
6. **network_page_rank**: Reduces odds by **1.0%** (OR = 0.990)
7. **family_FOP**: Reduces odds by **0.5%** (OR = 0.995)
8. **foreign_FEC_d***: Reduces odds by **0.4%** (OR = 0.996)
9. **foreign_FOP_t**: Reduces odds by **0.0%** (OR = 1.000)
10. **network_in_degree**: Reduces odds by **0.0%** (OR = 1.000)

## 3. Highest Risk Variables (Increased Odds)
Ranked by strength of risk (largest % increase in odds).

1. **camel_tier1_capital_ratio***: Increases odds by **490.5%** (OR = 5.905)
2. **camel_npl_ratio***: Increases odds by **2.1%** (OR = 1.021)

---
*Note: Interpretations assume ceteris paribus. Significance: * p < 0.05.*