"""
Efficient quarterly network snapshot generation using master projection + filtering.

This approach follows the existing rolling_windows pipeline pattern:
1. Create ONE master graph projection with ALL temporal relationships
2. Filter by quarter using tStart/tEnd properties  
3. Run algorithms on filtered view
4. Export and cleanup

Usage:
    python execute_quarterly_efficient.py --start 2010 --end 2020
"""

import os
import sys
import time
import argparse
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
load_dotenv()

from graphdatascience import GraphDataScience

def create_quarter_windows(start_year: int, end_year: int):
    """Generate quarterly window configurations."""
    quarters = pd.date_range(start=f'{start_year}-01-01', end=f'{end_year}-12-31', freq='QS')
    
    windows = []
    for start in quarters:
        end = start + pd.DateOffset(months=3) - pd.Timedelta(days=1)
        
        # Convert to milliseconds since epoch (matching base graph tStart/tEnd format)
        start_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)
        
        windows.append({
            "name": f"Q{start.quarter}_{start.year}",
            "start_ms": start_ms,
            "end_ms": end_ms,
            "start_year": start.year,
            "end_year": end.year,
            "quarter": start.quarter
        })
    
    return windows

def ensure_base_graph(gds, base_graph_name="base_temporal"):
    """
    Ensure master projection exists with temporal properties.
    Reuses existing 'base_temporal' from rolling windows pipeline if available.
    """
    print(f"Checking for base graph '{base_graph_name}'...")
    
    try:
        G = gds.graph.get(base_graph_name)
        print(f"✅ Base graph '{base_graph_name}' found (reusing from rolling windows)")
        print(f"   Nodes: {G.node_count()}")
        print(f"   Relationships: {G.relationship_count()}")
        return G
    except ValueError:
        print(f"❌ Base graph '{base_graph_name}' not found!")
        print(f"\nPlease create the base projection first using the rolling windows pipeline:")
        print(f"  cd rolling_windows")
        print(f"  python run_pipeline.py  # This creates 'base_temporal'")
        print(f"\nOr run the existing 2-year windows which will create it as a side-effect.")
        raise RuntimeError(f"Base graph '{base_graph_name}' does not exist")

def process_quarterly_window(gds, base_G, window, output_dir):
    """
    Process a single quarterly window using graph filtering.
    
    Args:
        gds: GraphDataScience client
        base_G: Base graph projection  
        window: Window configuration dict
        output_dir: Output directory for Parquet files
    
    Returns:
        dict with execution metrics
    """
    window_name = window['name']
    start_time = time.time()
    
    print(f"\n{'='*70}")
    print(f"Processing: {window_name}")
    print(f"{'='*70}")
    
    try:
        # Filter base graph to this quarterly window
        # tStart < end AND tEnd > start → relationship active during window
        node_filter = "n.tStart < $end AND n.tEnd > $start"
        rel_filter = "r.tStart < $end AND r.tEnd > $start"
        
        filter_params = {
            "start": float(window['start_ms']),
            "end": float(window['end_ms'])
        }
        
        print(f"   Creating filtered graph...")
        
        # Use context manager to automatically cleanup
        with gds.graph.filter(
            f"temp_{window_name}",
            base_G,
            node_filter,
            rel_filter,
            parameters=filter_params,
            concurrency=4
        ) as G:
            
            print(f"   Filtered to {G.node_count()} nodes, {G.relationship_count()} relationships")
            
            # Run algorithms (same as original quarterly pipeline)
            algorithms = [
                ("PageRank", lambda: gds.pageRank.mutate(
                    G,
                    mutateProperty='page_rank',
                    relationshipWeightProperty='weight',
                    maxIterations=20,
                    dampingFactor=0.85
                )),
                ("InDegree", lambda: gds.degree.mutate(
                    G,
                    mutateProperty='in_degree',
                    orientation='REVERSE'
                )),
                ("OutDegree", lambda: gds.degree.mutate(
                    G,
                    mutateProperty='out_degree',
                    orientation='NATURAL'
                )),
                ("WCC", lambda: gds.wcc.mutate(
                    G,
                    mutateProperty='wcc'
                )),
                ("Louvain", lambda: gds.louvain.mutate(
                    G,
                    mutateProperty='community_louvain',
                    relationshipWeightProperty='weight',
                    maxIterations=20,
                    includeIntermediateCommunities=True
                ))
            ]
            
            print(f"   Running algorithms:")
            for name, func in algorithms:
                print(f"     - {name}...", end='', flush=True)
                func()
                print(" ✓")
            
            # Export node properties
            print(f"   Exporting results...")
            df = gds.graph.nodeProperties.stream(
                G,
                ['page_rank', 'in_degree', 'out_degree', 'wcc', 'community_louvain'],
                separate_property_columns=True,
                db_node_properties=['Id', 'regn_cbr']
            )
            
            # Fix data types for Parquet compatibility
            df['regn_cbr'] = df['regn_cbr'].astype(str)  # Convert to string
            df['Id'] = df['Id'].astype(str)  # UUID as string
            
            # Add metadata
            df['window_name'] = window_name
            df['window_start_year'] = window['start_year']
            df['window_end_year'] = window['end_year']
            df['quarter'] = window['quarter']
            
            # Rename for consistency
            df = df.rename(columns={
                'community_louvain': 'rw_community_louvain',
                'page_rank': 'rw_page_rank',
                'in_degree': 'rw_in_degree',
                'out_degree': 'rw_out_degree',
                'wcc': 'rw_wcc'
            })
            
            # Add degree sum
            df['rw_degree'] = df['rw_in_degree'] + df['rw_out_degree']
            
            # Save to Parquet
            output_file = os.path.join(output_dir, f"node_features_{window_name}.parquet")
            df.to_parquet(output_file, engine='pyarrow', compression='snappy')
            
        # Graph automatically cleaned up by context manager
        
        runtime = time.time() - start_time
        
        print(f"✅ Completed {window_name}")
        print(f"   Nodes: {len(df)}")
        print(f"   Runtime: {runtime:.1f}s")
        print(f"   Output: {output_file}")
        
        return {
            'window': window_name,
            'status': 'success',
            'runtime': runtime,
            'node_count': len(df),
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
    parser = argparse.ArgumentParser(description='Execute quarterly network snapshots (efficient method)')
    parser.add_argument('--start', type=int, default=2010, help='Start year')
    parser.add_argument('--end', type=int, default=2020, help='End year')
    parser.add_argument('--output', type=str,
                       default='rolling_windows/output/quarterly_2010_2020',
                       help='Output directory')
    parser.add_argument('--base-graph', type=str, default='base_temporal',
                       help='Name for base graph projection (default: base_temporal from rolling windows)')
    parser.add_argument('--rebuild-base', action='store_true',
                       help='Rebuild base graph (otherwise reuse if exists)')
    parser.add_argument('--start-from', type=int, default=0,
                       help='Start from window index (for resuming)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of windows (for testing)')
    
    args = parser.parse_args()
    
    # Load Neo4j credentials
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    
    if not neo4j_password:
        print("❌ Error: NEO4J_PASSWORD not set")
        return
    
    print(f"Connecting to Neo4j at {neo4j_uri}...")
    gds = GraphDataScience(neo4j_uri, auth=(neo4j_user, neo4j_password))
    print(f"✅ Connected (GDS {gds.version()})")
    
    # Generate windows
    windows = create_quarter_windows(args.start, args.end)
    print(f"\n✅ Generated {len(windows)} quarterly windows")
    
    # Apply filters
    if args.start_from > 0:
        windows = windows[args.start_from:]
    if args.limit:
        windows = windows[:args.limit]
    
    print(f"   Processing {len(windows)} windows")
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Ensure base graph exists (ONE-TIME operation)
    print(f"\n{'='*70}")
    print("STEP 1: ENSURE BASE GRAPH")
    print(f"{'='*70}")
    
    if args.rebuild_base:
        print("Dropping existing base graph (--rebuild-base)")
        gds.graph.drop(args.base_graph, failIfMissing=False)
    
    base_G = ensure_base_graph(gds, args.base_graph)
    
    # Process windows
    print(f"\n{'='*70}")
    print(f"STEP 2: PROCESS {len(windows)} QUARTERLY WINDOWS")
    print(f"Estimated total runtime: {len(windows) * 1.5 / 60:.1f} minutes")
    print(f"{'='*70}")
    
    results = []
    start_time_total = time.time()
    
    for i, window in enumerate(windows, 1):
        print(f"\n[{i}/{len(windows)}] {window['name']}")
        
        result = process_quarterly_window(gds, base_G, window, args.output)
        results.append(result)
        
        # Progress
        elapsed = time.time() - start_time_total
        avg_time = elapsed / i
        remaining = avg_time * (len(windows) - i)
        
        print(f"   Progress: {i}/{len(windows)} ({100*i/len(windows):.1f}%)")
        print(f"   Elapsed: {elapsed/60:.1f} min | ETA: {remaining/60:.1f} min")
    
    # Summary
    total_runtime = time.time() - start_time_total
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'failed')
    
    print(f"\n{'='*70}")
    print("PIPELINE COMPLETE")
    print(f"{'='*70}")
    print(f"Total runtime: {total_runtime/60:.1f} minutes ({total_runtime/3600:.2f} hours)")
    print(f"Successful: {successful}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    
    # Save summary
    results_df = pd.DataFrame(results)
    summary_file = os.path.join(args.output, 'execution_summary.csv')
    results_df.to_csv(summary_file, index=False)
    print(f"\n✅ Summary saved to: {summary_file}")
    
    if failed > 0:
        failed_windows = results_df[results_df['status'] == 'failed']['window'].tolist()
        print(f"\n⚠️  {failed} windows failed: {', '.join(failed_windows)}")
    
    gds.close()
    print(f"\n✅ Complete. Output: {args.output}")

if __name__ == '__main__':
    main()
