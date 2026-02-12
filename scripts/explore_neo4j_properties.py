import os
import pandas as pd
from graphdatascience import GraphDataScience
from dotenv import load_dotenv

def explore():
    load_dotenv()
    gds = GraphDataScience(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
    )

    print("\n[SCHEMA] Node Labels count:")
    print(gds.run_cypher("CALL db.labels()"))

    print("\n[PROPERTIES] Company Node Keys (Sample):")
    res = gds.run_cypher("MATCH (c:Company) RETURN keys(c) as k LIMIT 5")
    all_keys = set()
    for row in res['k']:
        all_keys.update(row)
    print(sorted(list(all_keys)))

    print("\n[PROPERTIES] Bank Node Keys (Sample):")
    res = gds.run_cypher("MATCH (b:Bank) RETURN keys(b) as k LIMIT 5")
    all_keys = set()
    for row in res['k']:
        all_keys.update(row)
    print(sorted(list(all_keys)))

    print("\n[COMMUNITIES] Checking for community-related properties on Banks:")
    res = gds.run_cypher("MATCH (b:Bank) WHERE b.rw_community_louvain_4q_lag IS NOT NULL RETURN b.rw_community_louvain_4q_lag LIMIT 1")
    if not res.empty:
        print(f"Sample Louvain: {res.iloc[0,0]}")
    else:
        print("No rw_community_louvain_4q_lag found on Banks")

    print("\n[PROPERTIES] Full list of properties for Company (first 20):")
    res = gds.run_cypher("MATCH (c:Company) WITH keys(c) as k UNWIND k as prop RETURN DISTINCT prop LIMIT 50")
    print(res['prop'].tolist())

if __name__ == "__main__":
    explore()
