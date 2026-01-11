# Interpretation Report: Model 1: Core

## 1. Variable Interpretations
Interpretation logic: *Holding all other covariates constant...*

- **camel_roa**: A one-unit increase decreases the hazard of failure by **10.8%**. (*** p<0.001)
- **family_rho_F**: A one-unit increase decreases the hazard of failure by **3.7%**. (*** p<0.001)
- **network_out_degree**: A one-unit increase decreases the hazard of failure by **44.2%**. (*** p<0.001)

## 2. Most Protective Variables (Decreased Risk)
Ranked by strength of protection (largest % decrease in hazard).

1. **network_out_degree***: Reduces hazard by **44.2%** (HR = 0.558)
2. **camel_roa***: Reduces hazard by **10.8%** (HR = 0.892)
3. **family_rho_F***: Reduces hazard by **3.7%** (HR = 0.963)

## 3. Highest Risk Variables (Increased Risk)
Ranked by strength of risk (largest % increase in hazard).

_No risk variables found._

---
*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*