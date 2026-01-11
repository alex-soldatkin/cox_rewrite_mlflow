# Interpretation Report: Model 2: +Network (RW)

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **588.8%**. (*** p<0.001)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **1.9%**. (*** p<0.001)
- **camel_roa**: A one-unit increase decreases the hazard of failure by **40.3%**. (*** p<0.001)
- **camel_liquid_assets_ratio**: A one-unit increase increases the hazard of failure by **13.8%**. (not significant)
- **network_in_degree**: A one-unit increase decreases the hazard of failure by **0.0%**. (not significant)
- **network_out_degree**: A one-unit increase decreases the hazard of failure by **25.4%**. (*** p<0.001)
- **network_page_rank**: A one-unit increase decreases the hazard of failure by **2.7%**. (*** p<0.001)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **camel_roa***: Reduces hazard by **40.3%** (HR = 0.597)
2. **network_out_degree***: Reduces hazard by **25.4%** (HR = 0.746)
3. **network_page_rank***: Reduces hazard by **2.7%** (HR = 0.973)
4. **network_in_degree**: Reduces hazard by **0.0%** (HR = 1.000)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **588.8%** (HR = 6.888)
2. **camel_liquid_assets_ratio**: Increases hazard by **13.8%** (HR = 1.138)
3. **camel_npl_ratio***: Increases hazard by **1.9%** (HR = 1.019)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*