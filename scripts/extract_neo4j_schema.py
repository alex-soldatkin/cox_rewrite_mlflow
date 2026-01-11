import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

if not all([uri, user, password]):
    print("Error: Missing NEO4J_URI, NEO4J_USER, or NEO4J_PASSWORD in .env")
    exit(1)

driver = GraphDatabase.driver(uri, auth=(user, password))

schema_data = {
    "nodes": {},
    "relationships": {}
}

with driver.session() as session:
    print("Fetching Node Types and Properties...")
    # Get node labels and property keys/types
    # We sample the graph to guess types if APOC is not available, but let's try db.schema.nodeTypeProperties first (Neo4j 5.x)
    try:
        result = session.run("CALL db.schema.nodeTypeProperties()")
        for record in result:
            node_type = record["nodeType"] # formatted like ":Label" or ":Label1:Label2"
            labels = record["nodeLabels"]
            prop_name = record["propertyName"]
            prop_types = record["propertyTypes"]
            # mandatory = record["mandatory"]
            
            # Combine labels into a single key or handle primary label
            # Simple approach: use the first label
            if not labels:
                continue
            
            label = labels[0] # Simplification
            
            if label not in schema_data["nodes"]:
                schema_data["nodes"][label] = {}
            
            if prop_name:
                schema_data["nodes"][label][prop_name] = prop_types
                
    except Exception as e:
        print(f"Error calling db.schema.nodeTypeProperties: {e}")
        print("Falling back to sampling...")
        # Fallback sampling if needed (omitted for brevity unless requested)

    print("Fetching Relationship Types and Properties...")
    try:
        result = session.run("CALL db.schema.relTypeProperties()")
        for record in result:
            rel_type = record["relType"] # ":TYPE"
            prop_name = record["propertyName"]
            prop_types = record["propertyTypes"]
            
            type_name = rel_type.strip(":")
            
            if type_name not in schema_data["relationships"]:
                schema_data["relationships"][type_name] = {}
            
            if prop_name:
                schema_data["relationships"][type_name][prop_name] = prop_types

    except Exception as e:
        print(f"Error calling db.schema.relTypeProperties: {e}")

driver.close()

print(json.dumps(schema_data, indent=2))
