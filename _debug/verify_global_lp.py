"""
Verify Global Link Prediction Results
"""
import os
import sys
from graphdatascience import GraphDataScience
from dotenv import load_dotenv

load_dotenv()
neo4j_url = os.getenv("NEO4J_URI", "bolt://localhost:7687")
gds = GraphDataScience(neo4j_url, auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")))

print("Verifying FAMILY edges...")

# Count by source
res = gds.run_cypher("""
    MATCH ()-[r:FAMILY]->()
    RETURN coalesce(r.source, 'NULL') as source, count(r) as count
    ORDER BY count DESC
""")
print(res)

# Check a predicted edge
pred = gds.run_cypher("""
    MATCH (s)-[r:FAMILY]->(t)
    WHERE r.source = 'logistic_pred'
    RETURN s.Id, t.Id, r.confidence, r.temporal_start, r.temporal_end
    LIMIT 1
""")
if not pred.empty:
    print("\nSample Predicted Edge:")
    print(pred.iloc[0])
    
    # Verify temporal prop types (should be int/float)
    t_start = pred.iloc[0]['r.temporal_start']
    print(f"Temporal Start: {t_start} ({type(t_start)})")

else:
    print("\nNO PREDICTED EDGES FOUND!")

# Check 'official' valid edges (source not imputed)
valid = gds.run_cypher("""
    MATCH ()-[r:FAMILY]->()
    WHERE coalesce(r.source, '') <> 'imputed'
    RETURN count(r) as valid_count
""")
print(f"\nValid Edges (Ground Truth + Predict): {valid.iloc[0]['valid_count']}")
