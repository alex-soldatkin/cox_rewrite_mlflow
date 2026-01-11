# Interpretation Report: Model 2: +Network (RW)

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the odds of failure by **612.5%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the odds of failure by **2.2%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the odds of failure by **45.4%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase decreases the odds of failure by **67.4%**. (not significant)
- **network_in_degree**: A one-unit increase decreases the odds of failure by **0.0%**. (not significant)
- **network_out_degree**: A one-unit increase decreases the odds of failure by **24.1%**. (*** p<0.001)
- **network_page_rank**: A one-unit increase decreases the odds of failure by **2.3%**. (** p<0.01)

## 2. Most Protective Variables (Decreased Odds)
Ranked by strength of protection (largest % decrease in odds).

2. **camel_liquid_assets_ratio**: Reduces odds by **67.4%** (OR = 0.326)
3. **camel_roa***: Reduces odds by **45.4%** (OR = 0.546)
4. **network_out_degree***: Reduces odds by **24.1%** (OR = 0.759)
5. **network_page_rank***: Reduces odds by **2.3%** (OR = 0.977)
6. **network_in_degree**: Reduces odds by **0.0%** (OR = 1.000)

## 3. Highest Risk Variables (Increased Odds)
Ranked by strength of risk (largest % increase in odds).

1. **camel_tier1_capital_ratio***: Increases odds by **612.5%** (OR = 7.125)
2. **camel_npl_ratio***: Increases odds by **2.2%** (OR = 1.022)

---
*Note: Interpretations assume ceteris paribus. Significance: * p < 0.05.*