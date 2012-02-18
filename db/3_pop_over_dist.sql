CREATE OR REPLACE FUNCTION pop_over_dist(
  scenario_id integer,   
  num_partitions integer)
  RETURNS TABLE (pop double precision, distance integer)
  AS 
$$ 
  WITH dists AS 
  (SELECT distance FROM generate_series(
    (SELECT min(distance) FROM edges WHERE scenario_id=$1), 
    (SELECT max(distance) FROM edges WHERE scenario_id=$1),
    (SELECT max(distance) FROM 
      (SELECT 1 distance UNION ALL SELECT (max(distance) - min(distance)) / $2 distance FROM edges
      WHERE scenario_id=$1) a )) distance)
  SELECT 
    (sum(cast(weight as float)) / 
    (select sum(weight) FROM nodes
      WHERE scenario_id=$1 and node_type_id=1)) weight, 
    dists.distance
  FROM 
    (SELECT weight, e.distance
      FROM edges e, nodes n
      WHERE n.node_type_id=1 AND
        e.from_node_id=n.id AND
        e.scenario_id = $1) pop_dist, 
    dists
  WHERE 
    pop_dist.distance <= dists.distance
  GROUP BY dists.distance
  ORDER BY dists.distance
$$
LANGUAGE SQL;
