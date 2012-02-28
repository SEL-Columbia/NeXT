CREATE OR REPLACE FUNCTION pop_over_dist(
  scenario_id integer,   
  num_partitions integer)
  RETURNS TABLE (distance integer, pop double precision)
  AS 
$$ 
  WITH dists AS 
  (SELECT * FROM uniform_sample_dists($1, $2))
  SELECT 
    d.distance,
    (cast(sum(d.weight) as float) / 
    (SELECT cast(sum(weight) as float) FROM nodes
      WHERE scenario_id=$1 and node_type_id=1)) weight
  FROM 
    (SELECT DISTINCT node_id, weight, dists.distance FROM
      (SELECT n.id node_id, weight, e.distance
        FROM edges e, nodes n
        WHERE n.node_type_id=1 AND
          e.from_node_id=n.id AND
          e.scenario_id = $1) pop_dist, 
      dists
      WHERE 
        pop_dist.distance <= dists.distance
     ) d
  GROUP BY d.distance
  ORDER BY d.distance
$$
LANGUAGE SQL;
