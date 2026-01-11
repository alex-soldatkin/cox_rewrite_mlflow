# Interpretation Report: Model 1: Baseline (No Community FE)

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_roa**: A one-unit increase decreases the hazard of failure by **9.6%**. (*** p<0.001)
- **family_rho_F**: A one-unit increase decreases the hazard of failure by **3.0%**. (*** p<0.001)
- **network_out_degree**: A one-unit increase decreases the hazard of failure by **37.9%**. (*** p<0.001)
- **network_page_rank**: A one-unit increase decreases the hazard of failure by **1.2%**. (+ p<0.1)
- **camel_npl_ratio**: A one-unit increase increases the hazard of failure by **0.9%**. (*** p<0.001)
- **camel_tier1_capital_ratio**: A one-unit increase increases the hazard of failure by **1.9%**. (*** p<0.001)
- **foreign_FEC_d**: A one-unit increase decreases the hazard of failure by **10.7%**. (*** p<0.001)
- **family_FOP**: A one-unit increase decreases the hazard of failure by **0.3%**. (not significant)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **network_out_degree***: Reduces hazard by **37.9%** (HR = 0.621)
2. **foreign_FEC_d***: Reduces hazard by **10.7%** (HR = 0.893)
3. **camel_roa***: Reduces hazard by **9.6%** (HR = 0.904)
4. **family_rho_F***: Reduces hazard by **3.0%** (HR = 0.970)
5. **network_page_rank**: Reduces hazard by **1.2%** (HR = 0.988)
6. **family_FOP**: Reduces hazard by **0.3%** (HR = 0.997)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

1. **camel_tier1_capital_ratio***: Increases hazard by **1.9%** (HR = 1.019)
2. **camel_npl_ratio***: Increases hazard by **0.9%** (HR = 1.009)

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*