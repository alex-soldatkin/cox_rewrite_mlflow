"""
Generate quarterly network snapshots for lagged analysis (2010-2020).

This script extends the rolling window pipeline to compute quarterly network metrics,
enabling temporal lag analysis for addressing endogeneity in network effects.

Usage:
    python generate_quarterly_snapshots.py --start 2010 --end 2020 --output rolling_windows/output/quarterly_2010_2020
"""

import pandas as pd
from datetime import datetime
import argparse
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

def generate_quarterly_windows(start_year: int, end_year: int):
    """
    Generate quarterly window configurations for network snapshot computation.
    
    Args:
        start_year: Starting year (inclusive)
        end_year: Ending year (inclusive)
    
    Returns:
        List of window configurations with start_date, end_date, and window_name
    """
    quarters = pd.date_range(
        start=f'{start_year}-01-01',
        end=f'{end_year}-12-31',
        freq='QS'  # Quarter Start frequency
    )
    
    window_configs = []
    for start in quarters:
        # Quarter end date (last day of quarter)
        end = start + pd.DateOffset(months=3) - pd.Timedelta(days=1)
        
        config = {
            "window_name": f"Q{start.quarter}_{start.year}",
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "start_year": start.year,
            "end_year": end.year,
            "quarter": start.quarter
        }
        window_configs.append(config)
    
    return window_configs

def create_cypher_query(window_config):
    """
    Generate Cypher query for quarterly network snapshot.
    
    Args:
        window_config: Dictionary with window parameters
    
    Returns:
        Cypher query string for network projection and computation
    """
    window_name = window_config['window_name']
    start_date = window_config['start_date']
    end_date = window_config['end_date']
    
    query = f"""
// Quarterly Network Snapshot: {window_name}
// Period: {start_date} to {end_date}

// 1. Create graph projection for this quarter
CALL gds.graph.project.cypher(
    '{window_name}',
    'MATCH (n:Bank) RETURN id(n) AS id, n.regn_cbr AS regn_cbr, n.Id AS Id',
    '
    MATCH (n:Bank)-[r:OWNERSHIP]->(m:Bank)
    WHERE r.start_date <= date(\\'{end_date}\\') AND 
          (r.end_date IS NULL OR r.end_date >= date(\\'{start_date}\\'))
    RETURN id(n) AS source, id(m) AS target, 
           coalesce(r.Share, 1.0) AS weight
    '
)
YIELD graphName, nodeCount, relationshipCount;

// 2. Compute PageRank
CALL gds.pageRank.mutate('{window_name}', {{
    mutateProperty: 'page_rank',
    relationshipWeightProperty: 'weight',
    maxIterations: 20,
    dampingFactor: 0.85
}})
YIELD nodePropertiesWritten, ranIterations, didConverge;

// 3. Compute In-Degree
CALL gds.degree.mutate('{window_name}', {{
    mutateProperty: 'in_degree',
    orientation: 'REVERSE'
}})
YIELD nodePropertiesWritten;

// 4. Compute Out-Degree
CALL gds.degree.mutate('{window_name}', {{
    mutateProperty: 'out_degree',
    orientation: 'NATURAL'
}})
YIELD nodePropertiesWritten;

// 5. Compute Weakly Connected Components
CALL gds.wcc.mutate('{window_name}', {{
    mutateProperty: 'wcc'
}})
YIELD componentCount;

// 6. Compute Louvain Communities
CALL gds.louvain.mutate('{window_name}', {{
    mutateProperty: 'community_louvain',
    relationshipWeightProperty: 'weight',
    maxIterations: 20,
    includeIntermediateCommunities: true
}})
YIELD communityCount, modularity;

// 7. Export node properties to stream
CALL gds.graph.nodeProperties.stream('{window_name}', 
    ['page_rank', 'in_degree', 'out_degree', 'wcc', 'community_louvain']
)
YIELD nodeId, nodeProperty, propertyValue
RETURN 
    gds.util.asNode(nodeId).Id AS Id,
    gds.util.asNode(nodeId).regn_cbr AS regn_cbr,
    nodeProperty,
    propertyValue,
    '{window_name}' AS window_name,
    '{start_date}' AS window_start,
    '{end_date}' AS window_end,
    {window_config['start_year']} AS window_start_year,
    {window_config['end_year']} AS window_end_year,
    {window_config['quarter']} AS quarter;

// 8. Clean up graph projection
CALL gds.graph.drop('{window_name}');
"""
    
    return query

def main():
    parser = argparse.ArgumentParser(description='Generate quarterly network snapshots')
    parser.add_argument('--start', type=int, default=2010, help='Start year')
    parser.add_argument('--end', type=int, default=2020, help='End year')
    parser.add_argument('--output', type=str, 
                       default='rolling_windows/output/quarterly_2010_2020',
                       help='Output directory for parquet files')
    parser.add_argument('--dry-run', action='store_true',
                       help='Generate queries without executing')
    
    args = parser.parse_args()
    
    # Generate window configurations
    windows = generate_quarterly_windows(args.start, args.end)
    
    print(f"Generated {len(windows)} quarterly windows from {args.start} to {args.end}")
    print(f"\nWindow list:")
    for i, w in enumerate(windows, 1):
        print(f"  {i:2d}. {w['window_name']}: {w['start_date']} to {w['end_date']}")
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    if args.dry_run:
        print(f"\n{'='*70}")
        print("DRY RUN MODE - Sample query for first window:")
        print(f"{'='*70}")
        sample_query = create_cypher_query(windows[0])
        print(sample_query)
        print(f"\n{'='*70}")
        print(f"To execute, run without --dry-run flag")
        print(f"Estimated runtime: {len(windows)} windows × 4 min/window ≈ {len(windows)*4/60:.1f} hours")
    else:
        print(f"\n⚠️  WARNING: This will execute {len(windows)} Cypher queries")
        print(f"   Estimated runtime: ~{len(windows)*4/60:.1f} hours")
        response = input("Proceed? (yes/no): ")
        
        if response.lower() != 'yes':
            print("Aborted.")
            return
        
        # TODO: Implement actual execution via GDS client
        print("\n🚧 Execution not yet implemented.")
        print("   Next step: Integrate with Neo4j GDS client to run queries")
        print("   For now, use the generated queries manually in Neo4j Browser")
        
        # Save queries to file
        queries_file = os.path.join(args.output, 'quarterly_queries.cypher')
        with open(queries_file, 'w') as f:
            for window in windows:
                f.write(f"\n{'='*70}\n")
                f.write(f"// {window['window_name']}\n")
                f.write(f"{'='*70}\n\n")
                f.write(create_cypher_query(window))
                f.write("\n\n")
        
        print(f"\n✅ Saved {len(windows)} queries to: {queries_file}")
        print(f"   Execute these queries in Neo4j Browser or via Python GDS client")

if __name__ == '__main__':
    main()
