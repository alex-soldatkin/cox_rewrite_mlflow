# Logistic Regression Interpretation: Model 1: Baseline (No Community FE)

## Model Specification

**Type**: Logistic Regression
**Random Effects**: None
**Estimation**: Maximum Likelihood

## Coefficient Estimates (Log-Odds Scale)

| Variable | Coefficient (Mean) | Interpretation |
|----------|-------------------|----------------|
| `const` | 4.0519 | Baseline log-odds when all predictors = 0 (OR=57.509) |
| `camel_roa` | -0.0559 | Reduces odds by 5.4% (OR=0.946) |
| `family_rho_F` | -0.0217 | Reduces odds by 2.1% (OR=0.979) |
| `network_out_degree` | -0.0371 | Reduces odds by 3.6% (OR=0.964) |
| `network_page_rank` | 0.5421 | Increases odds by 72.0% (OR=1.720) |
| `camel_npl_ratio` | 0.0011 | Increases odds by 0.1% (OR=1.001) |
| `camel_tier1_capital_ratio` | 0.0178 | Increases odds by 1.8% (OR=1.018) |
| `foreign_FEC_d` | -0.0897 | Reduces odds by 8.6% (OR=0.914) |
| `family_FOP` | -0.0075 | Reduces odds by 0.7% (OR=0.993) |


## Model Notes

Standard logistic regression without community controls.

**Interpretation Note**: Coefficients represent changes in log-odds. Exponentiate to get odds ratios (OR).

---

_Generated: 2026-01-11 01:44:40.452103_
