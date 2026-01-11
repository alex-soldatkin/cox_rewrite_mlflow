# Model 1: Baseline (No Community Control)

## Model Summary

**Convergence**: Successful

**Log-Likelihood**: -416.26
**AIC**: 850.53
**AUC**: 0.8737

## Coefficients

| Variable | Coefficient | Std Error | z | P>|z| | Odds Ratio |
|----------|-------------|-----------|---|-------|------------|
| const | 4.0519 | 2.6251 | 1.54 | 0.1227 | 57.5092 |
| camel_roa | -0.0559 | 0.0341 | -1.64 | 0.1006 | 0.9456 |
| family_rho_F | -0.0217* | 0.0108 | -2.00 | 0.0451 | 0.9785 |
| network_out_degree | -0.0371*** | 0.0110 | -3.39 | 0.0007 | 0.9635 |
| network_page_rank | 0.5421*** | 0.0625 | 8.68 | 0.0000 | 1.7196 |
| camel_npl_ratio | 0.0011 | 0.0041 | 0.27 | 0.7904 | 1.0011 |
| camel_tier1_capital_ratio | 0.0178* | 0.0089 | 2.00 | 0.0453 | 1.0180 |
| foreign_FEC_d | -0.0897** | 0.0333 | -2.69 | 0.0071 | 0.9142 |
| family_FOP | -0.0075 | 0.0059 | -1.28 | 0.2001 | 0.9925 |

_Significance: + p<0.10, * p<0.05, ** p<0.01, *** p<0.001_
