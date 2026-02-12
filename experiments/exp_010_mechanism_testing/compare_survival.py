import os
import pandas as pd
import numpy as np
from lifelines import KaplanMeierFitter
from graphdatascience import GraphDataScience
from dotenv import load_dotenv
import matplotlib.pyplot as plt

def run_comparison():
    load_dotenv()
    gds = GraphDataScience(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD')))

    print("Fetching survival data for Banks and Companies...")
    
    # Banks in family groups
    query_banks = """
    MATCH (b:Bank)
    OPTIONAL MATCH (b)<-[:OWNERSHIP]-(p:Person)
    WHERE EXISTS { (p)-[:FAMILY]-(:Person) }
    RETURN b.regn_cbr as id, b.temporal_start as t_start, b.temporal_end as t_end, b.is_dead as is_dead, 'Bank' as type
    """
    
    # Companies in family groups
    query_cos = """
    MATCH (c:Company)<-[:OWNERSHIP]-(p:Person)
    WHERE EXISTS { (p)-[:FAMILY]-(:Person) }
    RETURN c.inn as id, c.temporal_start as t_start, c.temporal_end as t_end, c.is_dead as is_dead, 'Company' as type
    """
    
    df_banks = gds.run_cypher(query_banks)
    df_cos = gds.run_cypher(query_cos)
    
    df = pd.concat([df_banks, df_cos]).dropna(subset=['t_start', 't_end', 'is_dead'])
    
    # Calculate duration in months
    # timestamps are epoch ms
    # 30.4375 is average days in a month (365.25 / 12)
    df['duration'] = (df['t_end'] - df['t_start']) / (1000 * 60 * 60 * 24 * 30.4375)
    df['event'] = df['is_dead'].map({True: 1, False: 0, 1: 1, 0: 0})
    
    # Subset to ensure meaningful comparison (remove outliers or broken dates)
    # 1 year = 12 months, 40 years = 480 months. 
    df = df[(df['duration'] > 0) & (df['duration'] < 600)]
    
    plt.figure(figsize=(10, 6))
    kmf = KaplanMeierFitter()
    
    for label, group in df.groupby('type'):
        kmf.fit(group['duration'], event_observed=group['event'], label=label)
        kmf.plot_survival_function()
        
    plt.title("Survival Comparison: Connected Banks vs. Group Companies")
    plt.xlabel("Months in Network")
    plt.ylabel("Survival Probability")
    plt.grid(True, alpha=0.3)
    
    # Add vertical line at 1 year (12 months) for reference
    plt.axvline(x=12, color='red', linestyle='--', alpha=0.5, label='1 Year')
    plt.legend()
    
    output_path = "experiments/exp_010_mechanism_testing/survival_comparison.png"
    plt.savefig(output_path)
    print(f"Survival plot saved to {output_path}")
    
    # Simple summary stats
    print(df.groupby('type')['duration'].describe())
    
if __name__ == "__main__":
    run_comparison()
