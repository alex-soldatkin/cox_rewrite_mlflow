"""
Execute quarterly network snapshot queries against Neo4j and export to Parquet.

This script runs the generated Cypher queries via the Neo4j GDS Python client,
computing network metrics for each quarterly window and exporting to Parquet files.

Usage:
    python execute_quarterly_pipeline.py --queries rolling_windows/output/quarterly_2010_2020/quarterly_queries.cypher
"""

import os
import sys
import time
import argparse
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Load environment
load_dotenv()

# Import Neo4j GDS client (same as rolling window pipeline)
from graphdatascience import GraphDataScience

def parse_query_file(query_file):
    """
    Parse the generated Cypher query file into individual window queries.
    
    Returns:
        List of (window_name, query_string) tuples
    """
    with open(query_file, 'r') as f:
        content = f.read()
    
    # Split by window separators
    queries = []
    blocks = content.split('='*70)
    
    for i in range(1, len(blocks), 2):  # Every other block contains a query
        if i + 1 < len(blocks):
            header = blocks[i].strip()
            query = blocks[i + 1].strip()
            
            # Extract window name from header comment
            if '//' in header:
                window_name = header.split('//')[1].strip()
                queries.append((window_name, query))
    
    return queries

def execute_window(gds, window_name, query, output_dir):
    """
    Execute a single quarterly window query and export to Parquet.
    
    Args:
        gds: GraphDataScience client
        window_name: Name of the quarterly window (e.g., "Q1_2010")
        query: Cypher query string (contains multiple CALL statements)
        output_dir: Directory to save Parquet file
    
    Returns:
        dict with execution metrics (runtime, node_count, etc.)
    """
    start_time = time.time()
    
    print(f"\n{'='*70}")
    print(f"Processing: {window_name}")
    print(f"{'='*70}")
    
    try:
        # Split query into individual statements
        # Each CALL statement should be executed separately
        statements = []
        current_stmt = []
        
        for line in query.split('\n'):
            stripped = line.strip()
            
            # Skip comments and empty lines
            if not stripped or stripped.startswith('//'):
                continue
            
            current_stmt.append(line)
            
            # Check if statement is complete (ends with semicolon)
            if stripped.endswith(';'):
                statements.append('\n'.join(current_stmt))
                current_stmt = []
        
        print(f"   Executing {len(statements)} statements...")
        
        # Execute statements sequentially
        result_df = None
        
        for i, stmt in enumerate(statements, 1):
            stmt_type = "unknown"
            if "gds.graph.project" in stmt:
                stmt_type = "PROJECT"
            elif "pageRank" in stmt:
                stmt_type = "PageRank"
            elif "degree" in stmt and "REVERSE" in stmt:
                stmt_type = "InDegree"
            elif "degree" in stmt:
                stmt_type = "OutDegree"
            elif "wcc" in stmt:
                stmt_type = "WCC"
            elif "louvain" in stmt:
                stmt_type = "Louvain"
            elif "nodeProperties.stream" in stmt:
                stmt_type = "EXPORT"
            elif "graph.drop" in stmt:
                stmt_type = "CLEANUP"
            
            print(f"     [{i}/{len(statements)}] {stmt_type}...", end='', flush=True)
            
            try:
                result = gds.run_cypher(stmt)
                
                # If this is the export statement, save the results
                if "nodeProperties.stream" in stmt:
                    result_df = pd.DataFrame(result)
                
                print(f" ✓")
                
            except Exception as e:
                print(f" ✗")
                raise Exception(f"Failed at statement {i} ({stmt_type}): {e}")
        
        if result_df is None or result_df.empty:
            print(f"⚠️  Warning: No results for {window_name}")
            return {
                'window': window_name,
                'status': 'empty',
                'runtime': time.time() - start_time
            }
        
        # Pivot network metrics into columns
        df_pivot = result_df.pivot_table(
            index=['Id', 'regn_cbr', 'window_name', 'window_start', 'window_end',
                   'window_start_year', 'window_end_year', 'quarter'],
            columns='nodeProperty',
            values='propertyValue',
            aggfunc='first'
        ).reset_index()
        
        # Rename columns for consistency
        df_pivot.columns.name = None
        df_pivot = df_pivot.rename(columns={
            'community_louvain': 'rw_community_louvain',
            'page_rank': 'rw_page_rank',
            'in_degree': 'rw_in_degree',
            'out_degree': 'rw_out_degree',
            'wcc': 'rw_wcc'
        })
        
        # Add degree sum
        df_pivot['rw_degree'] = df_pivot['rw_in_degree'] + df_pivot['rw_out_degree']
        
        # Save to Parquet
        output_file = os.path.join(output_dir, f"node_features_{window_name.replace(' ', '_')}.parquet")
        df_pivot.to_parquet(output_file, engine='pyarrow', compression='snappy')
        
        runtime = time.time() - start_time
        
        print(f"✅ Completed {window_name}")
        print(f"   Nodes: {len(df_pivot)}")
        print(f"   Runtime: {runtime:.1f}s")
        print(f"   Output: {output_file}")
        
        return {
            'window': window_name,
            'status': 'success',
            'runtime': runtime,
            'node_count': len(df_pivot),
            'output_file': output_file
        }
        
    except Exception as e:
        runtime = time.time() - start_time
        print(f"❌ Failed {window_name}: {e}")
        
        return {
            'window': window_name,
            'status': 'failed',
            'runtime': runtime,
            'error': str(e)
        }

def main():
    parser = argparse.ArgumentParser(description='Execute quarterly network snapshot pipeline')
    parser.add_argument('--queries', type=str,
                       default='rolling_windows/output/quarterly_2010_2020/quarterly_queries.cypher',
                       help='Path to generated queries file')
    parser.add_argument('--output', type=str,
                       default='rolling_windows/output/quarterly_2010_2020',
                       help='Output directory for Parquet files')
    parser.add_argument('--start-from', type=int, default=0,
                       help='Start from window index (for resuming)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of windows to process (for testing)')
    
    args = parser.parse_args()
    
    # Load Neo4j credentials
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    
    if not neo4j_password:
        print("❌ Error: NEO4J_PASSWORD not set in .env file")
        return
    
    print(f"Connecting to Neo4j at {neo4j_uri}...")
   
    # Initialize GDS client
    try:
        gds = GraphDataScience(neo4j_uri, auth=(neo4j_user, neo4j_password))
        print(f"✅ Connected to Neo4j")
        print(f"   GDS version: {gds.version()}")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Parse queries
    print(f"\nParsing queries from: {args.queries}")
    queries = parse_query_file(args.queries)
    
    if not queries:
        print("❌ No queries found in file")
        return
    
    print(f"✅ Found {len(queries)} quarterly windows")
    
    # Apply filters
    if args.start_from > 0:
        queries = queries[args.start_from:]
        print(f"   Starting from window #{args.start_from + 1}")
    
    if args.limit:
        queries = queries[:args.limit]
        print(f"   Limited to {args.limit} windows")
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Execute windows
    print(f"\n{'='*70}")
    print(f"EXECUTING {len(queries)} QUARTERLY WINDOWS")
    print(f"Estimated total runtime: {len(queries) * 4 / 60:.1f} hours")
    print(f"{'='*70}")
    
    results = []
    start_time_total = time.time()
    
    for i, (window_name, query) in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] {window_name}")
        
        result = execute_window(gds, window_name, query, args.output)
        results.append(result)
        
        # Progress update
        elapsed = time.time() - start_time_total
        avg_time = elapsed / i
        remaining = avg_time * (len(queries) - i)
        
        print(f"   Progress: {i}/{len(queries)} ({100*i/len(queries):.1f}%)")
        print(f"   Elapsed: {elapsed/60:.1f} min | ETA: {remaining/60:.1f} min")
    
    # Summary
    total_runtime = time.time() - start_time_total
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'failed')
    
    print(f"\n{'='*70}")
    print(f"PIPELINE COMPLETE")
    print(f"{'='*70}")
    print(f"Total runtime: {total_runtime/3600:.2f} hours")
    print(f"Successful: {successful}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    
    # Save results summary
    results_df = pd.DataFrame(results)
    summary_file = os.path.join(args.output, 'execution_summary.csv')
    results_df.to_csv(summary_file, index=False)
    print(f"\n✅ Execution summary saved to: {summary_file}")
    
    if failed > 0:
        print(f"\n⚠️  {failed} windows failed. Check errors above.")
        failed_windows = results_df[results_df['status'] == 'failed']['window'].tolist()
        print(f"   Failed windows: {', '.join(failed_windows)}")
    
    # Close connection
    gds.close()
    print(f"\n✅ Pipeline complete. Output directory: {args.output}")

if __name__ == '__main__':
    main()
