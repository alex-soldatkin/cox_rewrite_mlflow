import os
import json
from collections import defaultdict
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(user, password))

schema = {
    "nodes": defaultdict(set),
    "relationships": defaultdict(set)
}

SAMPLE_SIZE = 100

def get_type_name(val):
    if val is None:
        return "Optional[Any]"
    t = type(val).__name__
    if t == 'int': return 'float' # treating all numbers as floats for safety in Pydantic unless strictly int
    return t

with driver.session() as session:
    print("Fetching Node Labels...")
    labels = session.run("CALL db.labels()").value()
    
    for label in labels:
        print(f"Sampling node: {label} (Limit {SAMPLE_SIZE})")
        # Sample multiple nodes to catch sparse properties
        query = f"MATCH (n:`{label}`) RETURN n LIMIT {SAMPLE_SIZE}"
        result = session.run(query)
        
        props_map = defaultdict(set)
        
        for record in result:
            node = record["n"]
            for k, v in node.items():
                props_map[k].add(get_type_name(v))
        
        # Convert sets to sorted lists for JSON serialization
        final_props = {}
        for k, types in props_map.items():
            final_props[k] = list(types)
            
        schema["nodes"][label] = final_props

    print("Fetching Relationship Types...")
    rels = session.run("CALL db.relationshipTypes()").value()
    
    for rel_type in rels:
        print(f"Sampling rel: {rel_type} (Limit {SAMPLE_SIZE})")
        query = f"MATCH ()-[r:`{rel_type}`]->() RETURN r LIMIT {SAMPLE_SIZE}"
        result = session.run(query)
        
        props_map = defaultdict(set)
        
        for record in result:
            r = record["r"]
            for k, v in r.items():
                props_map[k].add(get_type_name(v))

        final_props = {}
        for k, types in props_map.items():
            final_props[k] = list(types)
            
        schema["relationships"][rel_type] = final_props

driver.close()
print(json.dumps(schema, indent=2))
