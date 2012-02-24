CREATE OR REPLACE FUNCTION pop_over_dist(
  scenario_id integer,   
  num_partitions integer)
  RETURNS TABLE (pop double precision, distance integer)
  AS 
$$ 
  WITH dists AS 
  (SELECT distance FROM 
    (SELECT row_num FROM generate_series(
      (SELECT 1), 
      (SELECT count(*) FROM edges WHERE scenario_id=$1),
      (SELECT max(distance) FROM 
        (SELECT 1 distance UNION ALL SELECT count(*) / 
          (SELECT min(ct) FROM (
                SELECT $2 ct UNION ALL 
                SELECT (count(*) - 1) ct FROM edges WHERE scenario_id=$1) a) 
              num_parts FROM edges
        WHERE scenario_id=$1) a )) row_num) a,
     (SELECT row_number() over () row_num, distance FROM
       (SELECT distance FROM edges WHERE scenario_id=$1
        ORDER BY distance) d) b
     WHERE a.row_num=b.row_num)
  SELECT 
    (cast(sum(d.weight) as float) / 
    (SELECT cast(sum(weight) as float) FROM nodes
      WHERE scenario_id=$1 and node_type_id=1)) weight, 
    d.distance
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
