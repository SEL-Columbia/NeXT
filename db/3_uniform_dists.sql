CREATE OR REPLACE FUNCTION uniform_dists(
  scenario_id integer,
  num_partitions integer)
  RETURNS TABLE (distance integer)
  AS
$$
  SELECT distance FROM generate_series(
    (SELECT 1), 
    (SELECT max(distance) FROM edges WHERE scenario_id=$1),
    (SELECT max(distance) FROM 
      (SELECT 1 distance UNION ALL 
       SELECT (max(distance) / $2) distance 
       FROM edges WHERE scenario_id=$1) parts_per)) distance
$$
LANGUAGE SQL;
