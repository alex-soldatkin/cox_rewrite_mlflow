MATCH (p:Person)
WHERE p.Name = -1 AND p.MiddleName is NOT null
 SET p.Name = p.LastName + ' ' + p.FirstName + ' ' + p.MiddleName
RETURN p.Name
LIMIT 10;

MATCH (p:Person)
WHERE p.MiddleName = '-' AND p.FirstName = '-'
 SET p:DepositInsurance
REMOVE p:Person
RETURN p;

MATCH (p:Person)
WHERE p.MiddleName = '-' 
SET p.MiddleName = null 
RETURN p;

MATCH (p:Person)
WHERE p.FirstName = '-' 
SET p.FirstName = null 
RETURN p;

CALL apoc.periodic.iterate('MATCH ()-[r:SIMILAR]->() RETURN r',
'DETACH DELETE r',
{ parallel: true , batchSize:500000 });

MATCH (p:Person)
WHERE p.FirstName = "0" AND p.MiddleName = "0"
 SET p.FirstName = null
 SET p.MiddleName = null
RETURN p;

// clean up :Person nodes 
call apoc.periodic.iterate('
MATCH (a:Person), (b:Person)
    WHERE a <> b AND a.Id = b.Id AND a.Inn = b.Inn
    WITH *, a.Name AS full_name
    WITH *, head(collect([a, b])) AS nodes
    RETURN nodes',

'
WITH nodes
call apoc.refactor.mergeNodes(
nodes, { properties:"overwrite", mergeRels: false }
) yield node
RETURN node',
{ parallel: false , batchSize:1 });

// Step 1: Match surnames and patronymics using string similarity
CALL apoc.periodic.iterate(
  'MATCH (father:Person), (child:Person)
   WHERE father <> child 
     AND father.FirstName IS NOT NULL 
     AND child.MiddleName IS NOT NULL
     AND char_length(father.FirstName) >= 2 
     AND char_length(child.FirstName) >= 2
     // Quick filters before expensive operations
     AND char_length(father.FirstName) <= char_length(child.MiddleName) + 2
     AND NOT (father)-[:FAMILY]-(child)
   WITH father, child,
        apoc.text.levenshteinSimilarity(father.FirstName, child.MiddleName) AS patronymic_similarity,
        apoc.text.levenshteinSimilarity(father.LastName, child.LastName) AS surname_similarity
   WHERE patronymic_similarity > 0.55 AND surname_similarity > 0.88
   RETURN father, child', 
  'MERGE (father)-[r:FAMILY {type:"father-child"}]->(child)
   SET r += {
     value: 1.0, 
     Size: 1.0, 
     source: "imputed"
   }', 
  {parallel:true, batchSize:20}
);

// Step 2: Create sibling relationships based on shared fathers
CALL apoc.periodic.iterate(
  'MATCH (father:Person)-[:FAMILY {type:"father-child"}]->(child1:Person)
   MATCH (father)-[:FAMILY {type:"father-child"}]->(child2:Person)
   WHERE child1 <> child2 
     AND NOT (child1)-[:FAMILY {type:"sibling"}]-(child2)
   RETURN child1, child2',
  'MERGE (child1)-[r:FAMILY {type:"sibling"}]->(child2)
   SET r += {
     value: 1.0,
     Size: 1.0,
     source: "imputed"
   }',
  {parallel:true, batchSize:50}
);
