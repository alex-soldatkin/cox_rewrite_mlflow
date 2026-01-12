CALL apoc.periodic.iterate(
  'MATCH (father:Person), (child:Person)
   WHERE father <> child 
     AND father.FirstName IS NOT NULL 
     AND child.MiddleName IS NOT NULL
     AND char_length(father.FirstName) >= 2 
     AND char_length(child.FirstName) >= 2
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