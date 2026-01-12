"""Query FAMILY relationship distribution from Neo4j for link prediction planning."""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(user, password))

print("=" * 60)
print("FAMILY RELATIONSHIP DISTRIBUTION ANALYSIS")
print("=" * 60)

with driver.session() as session:
    # 1. Distribution by source and type
    print("\n1. FAMILY relationships by source and type:")
    print("-" * 50)
    query = """
    MATCH ()-[r:FAMILY]->()
    RETURN r.source AS source, r.type AS type, count(*) AS count
    ORDER BY count DESC
    """
    result = session.run(query)
    df = pd.DataFrame([dict(r) for r in result])
    print(df.to_string())
    
    # 2. Total counts by source
    print("\n\n2. Total FAMILY relationships by source:")
    print("-" * 50)
    query = """
    MATCH ()-[r:FAMILY]->()
    RETURN r.source AS source, count(*) AS count
    ORDER BY count DESC
    """
    result = session.run(query)
    for r in result:
        print(f"  {r['source']}: {r['count']}")
    
    # 3. Sample of non-imputed FAMILY relationships with names
    print("\n\n3. Sample of official (non-imputed) FAMILY relationships:")
    print("-" * 50)
    query = """
    MATCH (p1:Person)-[r:FAMILY]->(p2:Person)
    WHERE r.source <> 'imputed' OR r.source IS NULL
    RETURN 
        p1.FirstName AS p1_first, p1.MiddleName AS p1_middle, p1.LastName AS p1_last,
        r.type AS rel_type, r.source AS source,
        p2.FirstName AS p2_first, p2.MiddleName AS p2_middle, p2.LastName AS p2_last
    LIMIT 20
    """
    result = session.run(query)
    df = pd.DataFrame([dict(r) for r in result])
    print(df.to_string())
    
    # 4. Check for common Russian surnames in FAMILY relationships
    print("\n\n4. Most common surnames in FAMILY relationships:")
    print("-" * 50)
    query = """
    MATCH (p:Person)-[:FAMILY]-()
    WHERE p.LastName IS NOT NULL
    RETURN p.LastName AS surname, count(*) AS count
    ORDER BY count DESC
    LIMIT 20
    """
    result = session.run(query)
    for r in result:
        print(f"  {r['surname']}: {r['count']}")

    # 5. Sample of imputed relationships to understand name patterns
    print("\n\n5. Sample of IMPUTED FAMILY relationships (for comparison):")
    print("-" * 50)
    query = """
    MATCH (p1:Person)-[r:FAMILY]->(p2:Person)
    WHERE r.source = 'imputed'
    RETURN 
        p1.FirstName AS p1_first, p1.MiddleName AS p1_middle, p1.LastName AS p1_last,
        r.type AS rel_type,
        p2.FirstName AS p2_first, p2.MiddleName AS p2_middle, p2.LastName AS p2_last
    LIMIT 15
    """
    result = session.run(query)
    df = pd.DataFrame([dict(r) for r in result])
    print(df.to_string())
    
    # 6. Check available node properties for Person
    print("\n\n6. Sample Person node properties:")
    print("-" * 50)
    query = """
    MATCH (p:Person)
    WHERE p.FirstName IS NOT NULL AND p.LastName IS NOT NULL
    RETURN keys(p) as properties
    LIMIT 1
    """
    result = session.run(query).single()
    if result:
        print(f"  Properties: {result['properties']}")
        
    # 7. Check if there are temporal properties on FAMILY rels
    print("\n\n7. FAMILY relationship temporal properties sample:")
    print("-" * 50)
    query = """
    MATCH ()-[r:FAMILY]->()
    RETURN keys(r) as properties
    LIMIT 1
    """
    result = session.run(query).single()
    if result:
        print(f"  Properties: {result['properties']}")

driver.close()
print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
