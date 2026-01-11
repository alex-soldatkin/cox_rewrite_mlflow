# Interpretation Report: Model 3: +Family

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the odds of failure by **533.1%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the odds of failure by **2.1%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the odds of failure by **44.8%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase decreases the odds of failure by **70.3%**. (not significant)
- **network_in_degree**: A one-unit increase decreases the odds of failure by **0.0%**. (* p<0.05)
- **network_out_degree**: A one-unit increase decreases the odds of failure by **24.3%**. (*** p<0.001)
- **network_page_rank**: A one-unit increase decreases the odds of failure by **1.7%**. (* p<0.05)
- **family_FOP**: A one-unit increase decreases the odds of failure by **0.5%**. (not significant)
- **family_rho_F**: A one-unit increase decreases the odds of failure by **52.2%**. (*** p<0.001)

## 2. Most Protective Variables (Decreased Odds)
Ranked by strength of protection (largest % decrease in odds).

2. **camel_liquid_assets_ratio**: Reduces odds by **70.3%** (OR = 0.297)
3. **family_rho_F***: Reduces odds by **52.2%** (OR = 0.478)
4. **camel_roa***: Reduces odds by **44.8%** (OR = 0.552)
5. **network_out_degree***: Reduces odds by **24.3%** (OR = 0.757)
6. **network_page_rank***: Reduces odds by **1.7%** (OR = 0.983)
7. **family_FOP**: Reduces odds by **0.5%** (OR = 0.995)
8. **network_in_degree***: Reduces odds by **0.0%** (OR = 1.000)

## 3. Highest Risk Variables (Increased Odds)
Ranked by strength of risk (largest % increase in odds).

1. **camel_tier1_capital_ratio***: Increases odds by **533.1%** (OR = 6.331)
2. **camel_npl_ratio***: Increases odds by **2.1%** (OR = 1.021)

---
*Note: Interpretations assume ceteris paribus. Significance: * p < 0.05.*