CREATE OR REPLACE FUNCTION near_neigh(scenario_id integer)
RETURNS TABLE (demand_node_id integer, supply_node_id integer, distance integer)
AS
$$
  WITH demand_supply_dist AS
  (SELECT 
    CAST(
    ST_Distance(
      -- compare based on the demand points utm zone
      ST_Transform(demand.point, utmzone(ST_Centroid(demand.point))),
      ST_Transform(supply.point, utmzone(ST_Centroid(demand.point))))
    AS integer) dist, 
    demand.id demand_id,
    supply.id supply_id
  FROM 
    nodes demand,
    nodes supply 
  WHERE
    demand.node_type_id=1 AND
    supply.node_type_id=2 AND
    demand.scenario_id=$1 AND
    supply.scenario_id=$1)
  SELECT DISTINCT
    agg.demand_id,
    demand_supply.supply_id, 
    agg.dist
  FROM
    (SELECT
      min(dist) dist, 
      demand_id 
    FROM demand_supply_dist 
    GROUP BY demand_id) agg,
    (SELECT * FROM demand_supply_dist) demand_supply
  WHERE agg.demand_id=demand_supply.demand_id AND
    agg.dist=demand_supply.dist
$$
LANGUAGE SQL;
