# Interpretation Report: Model 5: +Topology

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the odds of failure by **298.4%**. (** p<0.01)
- **camel_npl_ratio**: A one-unit increase increases the odds of failure by **2.3%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the odds of failure by **46.7%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase decreases the odds of failure by **57.5%**. (not significant)
- **network_page_rank**: A one-unit increase decreases the odds of failure by **0.1%**. (not significant)
- **network_betweenness**: A one-unit increase decreases the odds of failure by **0.0%**. (* p<0.05)
- **network_C_b**: A one-unit increase decreases the odds of failure by **10.3%**. (*** p<0.001)

## 2. Most Protective Variables (Decreased Odds)
Ranked by strength of protection (largest % decrease in odds).

2. **camel_liquid_assets_ratio**: Reduces odds by **57.5%** (OR = 0.425)
3. **camel_roa***: Reduces odds by **46.7%** (OR = 0.533)
4. **network_C_b***: Reduces odds by **10.3%** (OR = 0.897)
5. **network_page_rank**: Reduces odds by **0.1%** (OR = 0.999)
6. **network_betweenness***: Reduces odds by **0.0%** (OR = 1.000)

## 3. Highest Risk Variables (Increased Odds)
Ranked by strength of risk (largest % increase in odds).

1. **camel_tier1_capital_ratio***: Increases odds by **298.4%** (OR = 3.984)
2. **camel_npl_ratio***: Increases odds by **2.3%** (OR = 1.023)

---
*Note: Interpretations assume ceteris paribus. Significance: * p < 0.05.*