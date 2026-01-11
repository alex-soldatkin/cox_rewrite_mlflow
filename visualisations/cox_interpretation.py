
import pandas as pd
import numpy as np

def generate_interpretation_report(model, model_name="Cox Time-Varying Model"):
    """
    Generates a markdown report interpreting the coefficients of a fitted Cox model.
    
    Args:
        model: Fitted lifelines CoxTimeVaryingFitter
        model_name: Name of the model for the header
        
    Returns:
        str: Markdown content
    """
    summary = model.summary.copy()
    
    # Calculate metrics
    # exp(coef) is the Hazard Ratio (HR)
    # % change = (HR - 1) * 100
    summary['HR'] = np.exp(summary['coef'])
    summary['pct_change'] = (summary['HR'] - 1) * 100
    
    # Sort for rankings
    protective = summary[summary['coef'] < 0].sort_values('coef') # Most negative first (most protective)
    risk = summary[summary['coef'] > 0].sort_values('coef', ascending=False) # Most positive first (highest risk)
    
    lines = []
    lines.append(f"# Interpretation Report: {model_name}")
    lines.append("")
    
    lines.append("## 1. Variable Interpretations")
    lines.append("Interpretation logic: *Holding all other covariates constant...*")
    lines.append("")
    
    for var_name, row in summary.iterrows():
        coef = row['coef']
        pct = row['pct_change']
        p_val = row.get("p", row.get("p-value"))
        
        significance = ""
        if p_val < 0.001: significance = "(*** p<0.001)"
        elif p_val < 0.01: significance = "(** p<0.01)"
        elif p_val < 0.05: significance = "(* p<0.05)"
        elif p_val < 0.1: significance = "(+ p<0.1)"
        else: significance = "(not significant)"
        
        direction = "decreases" if coef < 0 else "increases"
        # Absolute percent for readability in the sentence
        abs_pct = abs(pct)
        
        sentence = f"- **{var_name}**: A one-unit increase {direction} the hazard of failure by **{abs_pct:.1f}%**. {significance}"
        lines.append(sentence)
        
    lines.append("")
    lines.append("## 2. Most Protective Variables (Decreased Risk)")
    lines.append("Ranked by strength of protection (largest % decrease in hazard).")
    lines.append("")
    
    if protective.empty:
        lines.append("_No protective variables found._")
    else:
        for i, (var_name, row) in enumerate(protective.iterrows(), 1):
            pct_drop = (1 - row['HR']) * 100
            p_val = row.get("p", row.get("p-value"))
            stars = "*" if p_val < 0.05 else ""
            lines.append(f"{i}. **{var_name}**{stars}: Reduces hazard by **{pct_drop:.1f}%** (HR = {row['HR']:.3f})")
            
    lines.append("")
    lines.append("## 3. Highest Risk Variables (Increased Risk)")
    lines.append("Ranked by strength of risk (largest % increase in hazard).")
    lines.append("")
    
    if risk.empty:
        lines.append("_No risk variables found._")
    else:
        for i, (var_name, row) in enumerate(risk.iterrows(), 1):
            pct_inc = (row['HR'] - 1) * 100
            p_val = row.get("p", row.get("p-value"))
            stars = "*" if p_val < 0.05 else ""
            lines.append(f"{i}. **{var_name}**{stars}: Increases hazard by **{pct_inc:.1f}%** (HR = {row['HR']:.3f})")
            
    lines.append("")
    lines.append("---")
    lines.append("*Note: Interpretations assume ceteris paribus (all other variables held constant). Significance: * p < 0.05.*")
    
    return "\n".join(lines)
