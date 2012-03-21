CREATE OR REPLACE FUNCTION density_over_dist(
  scenario_id integer,   
  num_partitions integer)
  RETURNS TABLE (distance integer, demand double precision)
  AS 
$$ 
  WITH dists AS 
  (SELECT actual.distance actual_dist, offset_dist.distance offset_dist FROM 
    (SELECT row_number() over () row_num, * FROM uniform_dists($1, $2)) actual,
    (SELECT (row_number() over () - 1) row_num, * FROM uniform_dists($1, $2) OFFSET 1) offset_dist
  WHERE actual.row_num=offset_dist.row_num)
  SELECT 
    d.distance,
    (cast(sum(d.weight) as float) / 
    (SELECT cast(sum(weight) as float) FROM nodes
      WHERE scenario_id=$1 and node_type_id=1)) weight
  FROM 
    (SELECT DISTINCT node_id, weight, dists.offset_dist distance FROM
      (SELECT n.id node_id, weight, e.distance
        FROM edges e, nodes n
        WHERE n.node_type_id=1 AND
          e.from_node_id=n.id AND
          e.scenario_id = $1) demand_dist, 
      dists
      WHERE 
        demand_dist.distance < dists.offset_dist AND
        demand_dist.distance >= dists.actual_dist
     ) d
  GROUP BY d.distance
  ORDER BY d.distance
$$
LANGUAGE SQL;
