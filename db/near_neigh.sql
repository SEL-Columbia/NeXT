CREATE OR REPLACE FUNCTION near_neigh(scenario_id integer)
RETURNS TABLE (pop_id integer, fac_id integer, distance integer)
AS
$$
  WITH pop_fac_dist AS
  (SELECT 
    CAST(
    ST_Distance(
      ST_Transform(pop.point, utmzone(ST_Centroid(pop.point))),
      ST_Transform(fac.point, utmzone(ST_Centroid(pop.point))))
    AS integer) dist, 
    pop.id pop_id,
    fac.id fac_id
  FROM 
    nodes pop,
    nodes fac
  WHERE
    pop.node_type_id=1 AND
    fac.node_type_id=2 AND
    pop.scenario_id=$1 AND
    fac.scenario_id=$1)
  SELECT DISTINCT
    agg.pop_id,
    pop_fac.fac_id, 
    agg.dist
  FROM
    (SELECT
      min(dist) dist, 
      pop_id 
    FROM pop_fac_dist 
    GROUP BY pop_id) agg,
    (SELECT * FROM pop_fac_dist) pop_fac
  WHERE agg.pop_id=pop_fac.pop_id AND
    agg.dist=pop_fac.dist
$$
LANGUAGE SQL;
