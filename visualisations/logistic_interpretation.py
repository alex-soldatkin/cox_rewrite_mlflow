
import pandas as pd
import numpy as np

def generate_logistic_interpretation_report(model_result, model_name="Logistic Model"):
    """
    Generates a markdown report interpreting the coefficients of a fitted Logistic model (statsmodels).
    
    Args:
        model_result: Fitted statsmodels LogitResult
        model_name: Name of the model
        
    Returns:
        str: Markdown content
    """
    # Extract data
    params = model_result.params
    pvalues = model_result.pvalues
    
    # Build summary DF
    summary = pd.DataFrame({
        'coef': params,
        'p': pvalues
    })
    
    # Calculate Odds Ratios
    summary['OR'] = np.exp(summary['coef'])
    summary['pct_change'] = (summary['OR'] - 1) * 100
    
    # Sort
    protective = summary[summary['coef'] < 0].sort_values('coef') # Coef < 0 => OR < 1 => Protective
    risk = summary[summary['coef'] > 0].sort_values('coef', ascending=False) # Coef > 0 => OR > 1 => Risk
    
    lines = []
    lines.append(f"# Interpretation Report: {model_name}")
    lines.append("")
    
    lines.append("## 1. Variable Interpretations")
    lines.append("Interpretation logic: *Holding all other covariates constant...*")
    lines.append("")
    
    for var_name, row in summary.iterrows():
        if var_name == "const": continue
        
        coef = row['coef']
        pct = row['pct_change']
        p_val = row['p']
        
        significance = ""
        if p_val < 0.001: significance = "(*** p<0.001)"
        elif p_val < 0.01: significance = "(** p<0.01)"
        elif p_val < 0.05: significance = "(* p<0.05)"
        elif p_val < 0.1: significance = "(+ p<0.1)"
        else: significance = "(not significant)"
        
        direction = "decreases" if coef < 0 else "increases"
        abs_pct = abs(pct)
        
        sentence = f"- **{var_name}**: A one-unit increase {direction} the odds of failure by **{abs_pct:.1f}%**. {significance}"
        lines.append(sentence)
        
    lines.append("")
    lines.append("## 2. Most Protective Variables (Decreased Odds)")
    lines.append("Ranked by strength of protection (largest % decrease in odds).")
    lines.append("")
    
    if protective.empty:
        lines.append("_No protective variables found._")
    else:
        for i, (var_name, row) in enumerate(protective.iterrows(), 1):
            if var_name == "const": continue
            pct_drop = (1 - row['OR']) * 100
            p_val = row['p']
            stars = "*" if p_val < 0.05 else ""
            lines.append(f"{i}. **{var_name}**{stars}: Reduces odds by **{pct_drop:.1f}%** (OR = {row['OR']:.3f})")
            
    lines.append("")
    lines.append("## 3. Highest Risk Variables (Increased Odds)")
    lines.append("Ranked by strength of risk (largest % increase in odds).")
    lines.append("")
    
    if risk.empty:
        lines.append("_No risk variables found._")
    else:
        for i, (var_name, row) in enumerate(risk.iterrows(), 1):
            if var_name == "const": continue
            pct_inc = (row['OR'] - 1) * 100
            p_val = row['p']
            stars = "*" if p_val < 0.05 else ""
            lines.append(f"{i}. **{var_name}**{stars}: Increases odds by **{pct_inc:.1f}%** (OR = {row['OR']:.3f})")
            
    lines.append("")
    lines.append("---")
    lines.append("*Note: Interpretations assume ceteris paribus. Significance: * p < 0.05.*")
    
    return "\n".join(lines)
