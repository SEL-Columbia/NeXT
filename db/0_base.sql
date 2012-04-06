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

CREATE OR REPLACE FUNCTION uniform_sample_dists(
  scenario_id integer,
  num_partitions integer)
  RETURNS TABLE (distance integer)
  AS
$$
  SELECT distance FROM
    (SELECT row_num FROM generate_series(
      (SELECT 1), 
      (SELECT count(*) FROM edges WHERE scenario_id=$1),
      (SELECT max(ct) FROM 
        (SELECT 1 ct UNION ALL SELECT count(*) / 
          (SELECT min(ct) FROM (
                SELECT $2 ct UNION ALL 
                SELECT (count(*) - 1) ct FROM edges WHERE scenario_id=$1) num_parts_and_total) 
              num_parts FROM edges
        WHERE scenario_id=$1) parts_per )) row_num) samples,
     (SELECT row_number() over () row_num, distance FROM
       (SELECT distance FROM edges WHERE scenario_id=$1
        ORDER BY distance) ordered_dists) ordered_dists_row_nums
     WHERE samples.row_num=ordered_dists_row_nums.row_num
$$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION demand_over_dist(
  scenario_id integer,   
  num_partitions integer)
  RETURNS TABLE (distance integer, demand double precision)
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
          e.scenario_id = $1) demand_dist, 
      dists
      WHERE 
        demand_dist.distance <= dists.distance
     ) d
  GROUP BY d.distance
  ORDER BY d.distance
$$
LANGUAGE SQL;

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

-- Drops existing scenario edges, runs new nearest neighbor
-- and populates edges
CREATE OR REPLACE FUNCTION run_near_neigh(scenario_id integer)
RETURNS void AS
$$
BEGIN
  -- TODO:  There should be no need to call this
  -- each time.  There must be a way to set the
  -- SRID for the table globally and NOT on each 
  -- insert
  PERFORM UpdateGeometrySRID('nodes', 'point', 4326);
  DELETE FROM edges WHERE edges.scenario_id=$1;
  INSERT INTO edges 
    (from_node_id, to_node_id, scenario_id, distance)
    SELECT demand_node_id, supply_node_id, $1 scenario_id, distance 
    FROM near_neigh($1);
 RETURN;
 END;
 $$ LANGUAGE 'plpgsql';
