"""
exp_016 Step 1: Extract and categorise bank closure types from Neo4j.

Queries the Bank node properties ReasonText and reason_banki_memory
to categorise closures into: forced revocation, voluntary liquidation,
reorganisation/sanitisation.

Run this FIRST before the Cox models to inspect closure type distribution.
"""

import os
import sys
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from dotenv import load_dotenv
from graphdatascience import GraphDataScience


def connect_neo4j():
    load_dotenv()
    gds = GraphDataScience(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
    )
    return gds


def extract_closure_data(gds):
    """Query Neo4j for all dead banks with closure reason fields."""
    cypher = """
    MATCH (b:Bank)
    WHERE b.regn_cbr IS NOT NULL
    RETURN
        toString(b.regn_cbr) AS regn_cbr,
        b.is_dead AS is_dead,
        b.DeathDate AS death_date,
        b.ReasonText AS reason_text,
        b.reason_banki_memory AS reason_banki,
        b.ReorganizationInfo AS reorg_info,
        b.StatusDate AS status_date,
        b.lifespan_days AS lifespan_days
    """
    df = gds.run_cypher(cypher)
    print(f"Total banks queried: {len(df):,}")
    print(f"Dead banks: {df['is_dead'].sum():,}")
    return df


def categorise_closure(row):
    """Categorise a bank's closure based on available reason fields.

    Categories:
        revocation  - forced licence revocation by CBR
        voluntary   - voluntary liquidation / surrender of licence
        reorganisation - merger, acquisition, sanitisation
        unknown     - no reason data or unclassifiable
    """
    reason = str(row.get('reason_text') or '').lower().strip()
    banki = str(row.get('reason_banki') or '').lower().strip()
    reorg = row.get('reorg_info')

    # Check reorganisation first (explicit flag)
    if reorg is not None and reorg > 0:
        return 'reorganisation'

    combined = reason + ' ' + banki

    # Reorganisation / sanitisation keywords (Russian and English)
    reorg_keywords = [
        'реорганиз', 'присоедин', 'слиян', 'преобразов',
        'санац', 'санир', 'оздоров',
        'reorgani', 'merger', 'sanit', 'acqui',
    ]
    for kw in reorg_keywords:
        if kw in combined:
            return 'reorganisation'

    # Voluntary liquidation keywords
    voluntary_keywords = [
        'добровольн', 'ликвидац', 'по решению учредител',
        'по решению акционер', 'по решению участник',
        'voluntary', 'liquidat',
    ]
    for kw in voluntary_keywords:
        if kw in combined:
            return 'voluntary'

    # Forced revocation keywords
    revocation_keywords = [
        'отзыв', 'аннулир', 'лишен',
        'revok', 'annul', 'withdraw', 'cancel',
    ]
    for kw in revocation_keywords:
        if kw in combined:
            return 'revocation'

    # Court-declared bankruptcy / tax authority closure → treat as forced
    bankruptcy_keywords = [
        'банкрот', 'несостоятельн', 'конкурсн',
        'закрыто налогов', 'bankrupt',
    ]
    for kw in bankruptcy_keywords:
        if kw in combined:
            return 'revocation'

    # If bank is dead but no reason matched
    if row.get('is_dead'):
        return 'unknown'

    return 'alive'


def main():
    print("=" * 70)
    print("EXP_016 STEP 1: EXTRACT CLOSURE TYPES FROM NEO4J")
    print("=" * 70)

    gds = connect_neo4j()
    df = extract_closure_data(gds)

    # Filter to dead banks for categorisation
    dead = df[df['is_dead'] == True].copy()
    alive = df[df['is_dead'] != True].copy()

    print(f"\nDead banks with reason_text: {dead['reason_text'].notna().sum()}")
    print(f"Dead banks with reason_banki: {dead['reason_banki'].notna().sum()}")
    print(f"Dead banks with reorg_info: {(dead['reorg_info'].notna() & (dead['reorg_info'] > 0)).sum()}")

    # Show sample reason texts
    print("\n--- Sample reason_text values (first 20 non-null) ---")
    sample_reasons = dead[dead['reason_text'].notna()]['reason_text'].head(20)
    for i, r in enumerate(sample_reasons):
        print(f"  {i+1}. {r}")

    print("\n--- Sample reason_banki values (first 20 non-null) ---")
    sample_banki = dead[dead['reason_banki'].notna()]['reason_banki'].head(20)
    for i, r in enumerate(sample_banki):
        print(f"  {i+1}. {r}")

    # Categorise
    print("\nCategorising closure types...")
    dead['closure_type'] = dead.apply(categorise_closure, axis=1)
    alive['closure_type'] = 'alive'

    # Distribution
    print("\n--- Closure Type Distribution (Dead Banks) ---")
    dist = dead['closure_type'].value_counts()
    for ct, count in dist.items():
        pct = 100 * count / len(dead)
        print(f"  {ct:20s}: {count:5d} ({pct:5.1f}%)")

    # Combine and save
    result = pd.concat([dead, alive], ignore_index=True)
    result['regn'] = pd.to_numeric(result['regn_cbr'], errors='coerce').astype('Int64')

    out_path = os.path.join(os.path.dirname(__file__), 'closure_types.csv')
    result[['regn', 'regn_cbr', 'is_dead', 'death_date', 'closure_type',
            'reason_text', 'reason_banki', 'reorg_info']].to_csv(out_path, index=False)
    print(f"\nSaved to {out_path}")

    # Show unknowns for manual review
    unknowns = dead[dead['closure_type'] == 'unknown']
    if len(unknowns) > 0:
        print(f"\n--- Unknown closure types ({len(unknowns)}) - review manually ---")
        for _, row in unknowns.head(20).iterrows():
            print(f"  regn={row['regn_cbr']}: reason_text='{row['reason_text']}', "
                  f"reason_banki='{row['reason_banki']}'")

    print(f"\n{'=' * 70}")
    print("DONE. Review closure_types.csv before running Cox models.")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
