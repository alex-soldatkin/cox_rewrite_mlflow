// Exclude isolated banks with no network connections
MATCH (n:Bank)
WHERE n.regn_cbr IS NOT NULL
  AND (n.is_isolate IS NULL OR n.is_isolate = false)
RETURN 
    toString(n.regn_cbr) as regn_cbr,
    n.Id as bank_id,
    n.is_dead as is_dead,
    n.lifespan_days as lifespan_days,
    n.DeathDate as death_date,
    n.RegistrationDate as registration_date,
    n.is_isolate as is_isolate,

    // Family
    n.family_connection_ratio as family_connection_ratio,
    n.family_ownership_percentage as family_ownership_pct,
    n.direct_family_owned_value as family_owned_value_direct,
    n.direct_owners as direct_owners_count,
    n.total_family_connections as family_connections_count,
    n.family_controlled_companies as family_controlled_companies,

    // Foreign
    n.foreign_direct_ownership_percentage as foreign_ownership_direct_pct,
    n.total_foreign_ownership_percentage as foreign_ownership_total_pct,
    n.foreign_entity_count as foreign_entity_count,
    n.foreign_controlled_companies as foreign_controlled_companies,
    n.unique_country_count as foreign_country_diversity,

    // State
    n.state_ownership_percentage as state_ownership_pct,
    n.state_controlled_companies as state_controlled_companies,
    n.state_control_paths as state_control_paths,

    // Network / Centrality
    n.in_degree as in_degree,
    n.out_degree as out_degree,
    n.page_rank as page_rank,
    n.betweenness as betweenness,
    n.closeness as closeness,
    n.eigenvector as eigenvector,
    n.ownership_complexity_score as ownership_complexity_score
