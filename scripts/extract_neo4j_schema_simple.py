import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(user, password))

schema = {"nodes": {}, "relationships": {}}

with driver.session() as session:
    print("Fetching Node Labels...")
    labels = session.run("CALL db.labels()").value()
    
    for label in labels:
        print(f"Sampling node: {label}")
        # Sample one node to get properties
        query = f"MATCH (n:`{label}`) RETURN n LIMIT 1"
        result = session.run(query).single()
        if result:
            node = result["n"]
            # Get property keys and python types
            props = {}
            for k, v in node.items():
                props[k] = type(v).__name__
            schema["nodes"][label] = props
            
    print("Fetching Relationship Types...")
    rels = session.run("CALL db.relationshipTypes()").value()
    
    for rel_type in rels:
        # Sample one relationship
        print(f"Sampling rel: {rel_type}")
        query = f"MATCH ()-[r:`{rel_type}`]->() RETURN r LIMIT 1"
        result = session.run(query).single()
        if result:
            r = result["r"]
            props = {}
            for k, v in r.items():
                props[k] = type(v).__name__
            schema["relationships"][rel_type] = props

driver.close()
print(json.dumps(schema, indent=2))
