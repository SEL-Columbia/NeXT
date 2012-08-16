-- Drop all old functions
DROP FUNCTION density_over_dist(integer, integer);
DROP FUNCTION demand_over_dist(integer, integer);
DROP FUNCTION uniform_sample_dists(integer, integer);
DROP FUNCTION run_near_neigh(integer);
DROP FUNCTION near_neigh(integer);

-- Simplifies querying cumulative nodes from a phase
CREATE OR REPLACE VIEW nodes_ancestors AS
    SELECT
        nodes.id, 
        nodes.phase_id nodes_phase_id,
        nodes.scenario_id,
        nodes.node_type_id,
        nodes.weight,
        nodes.point,
        pa.phase_id pa_phase_id
    FROM
        nodes,
        phase_ancestors pa
    WHERE
        nodes.phase_id = pa.ancestor_phase_id AND
        nodes.scenario_id = pa.scenario_id;
 
-- Get all demand/supply distance pairs for a given scenario/phase_id
-- (all ancestor nodes of this phase are included)
CREATE OR REPLACE FUNCTION demand_supply_dists(scenario_id integer, phase_id integer)
RETURNS TABLE (demand_node_id integer, supply_node_id integer, distance integer)
AS 
$$
  SELECT 
    demand.id demand_id,
    supply.id supply_id,
    CAST(
    ST_Distance(
      -- compare based on the demand points utm zone
      ST_Transform(demand.point, utmzone(ST_Centroid(demand.point))),
      ST_Transform(supply.point, utmzone(ST_Centroid(demand.point))))
    AS integer) dist 
  FROM 
    nodes_ancestors demand,
    nodes_ancestors supply 
  WHERE
    demand.node_type_id=1 AND
    supply.node_type_id=2 AND
    demand.scenario_id=$1 AND
    supply.scenario_id=$1 AND
    demand.pa_phase_id=$2 AND
    supply.pa_phase_id=$2
$$
LANGUAGE SQL;


-- Calculates nearest neighbor supply node for each demand node
CREATE OR REPLACE FUNCTION near_neigh(scenario_id integer, phase_id integer)
RETURNS TABLE (demand_node_id integer, supply_node_id integer, distance integer)
AS
$$
  SELECT DISTINCT
    agg.demand_node_id,
    demand_supply.supply_node_id, 
    agg.distance
  FROM
    (SELECT
      min(distance) distance, 
      demand_node_id 
    FROM demand_supply_dists($1, $2)
    GROUP BY demand_node_id) agg,
    (SELECT * FROM demand_supply_dists($1, $2)) demand_supply
  WHERE agg.demand_node_id=demand_supply.demand_node_id AND
    agg.distance=demand_supply.distance
$$
LANGUAGE SQL;

-- Drops existing scenario edges, runs new nearest neighbor
-- and populates edges
CREATE OR REPLACE FUNCTION run_near_neigh(scenario_id integer, phase_id integer)
RETURNS void AS
$$
BEGIN
  -- TODO:  There should be no need to call this
  -- each time.  There must be a way to set the
  -- SRID for the table globally and NOT on each 
  -- insert
  -- PERFORM UpdateGeometrySRID('nodes', 'point', 4326);
  DELETE FROM edges WHERE edges.scenario_id=$1 AND edges.phase_id=$2;
  INSERT INTO edges 
    (from_node_id, to_node_id, scenario_id, phase_id, distance)
    SELECT demand_node_id, supply_node_id, $1 scenario_id, $2 phase_id, distance 
    FROM near_neigh($1, $2);
 RETURN;
 END;
 $$ LANGUAGE 'plpgsql';

-- Calculate n uniformly partitioned *distances*
CREATE OR REPLACE FUNCTION uniform_dists(
  scenario_id integer,
  phase_id integer,
  num_partitions integer)
  RETURNS TABLE (distance integer)
  AS
$$
  SELECT distance FROM generate_series(
    (SELECT 1), 
    (SELECT max(distance) FROM edges WHERE scenario_id=$1),
    -- step size is the larger of max(distance)/num_partitions 
    -- (an int result rounded down) and 1
    -- so that if the # partitions is greater than the
    -- largest distance, the step is 1
    (SELECT max(distance) FROM 
      (SELECT 1 distance UNION ALL 
       SELECT (max(distance) / $3) distance 
       FROM edges 
       WHERE scenario_id=$1 and phase_id=$2) parts_per)) distance
$$
LANGUAGE SQL;

-- Calculate n uniform sampled distances
-- (equal number of records within each interval)
CREATE OR REPLACE FUNCTION uniform_sample_dists(
  scenario_id integer,
  phase_id integer,
  num_partitions integer)
  RETURNS TABLE (distance integer, row_num bigint)
  AS
$$
  SELECT distance, samples.row_num FROM
    (SELECT row_num FROM generate_series(
      (SELECT 1), 
      (SELECT count(*) FROM edges WHERE scenario_id=$1 and phase_id=$2),
      -- step size is determined by num_records/num_partitions 
      -- so that there are an equal number of records
      (SELECT max(ct) FROM 
        (SELECT 1 ct UNION ALL SELECT count(*) / 
          (SELECT min(ct) FROM (
                SELECT $3 ct UNION ALL 
                SELECT (count(*) - 1) ct 
                FROM edges WHERE scenario_id=$1 AND phase_id=$2) num_parts_and_total) 
              num_parts FROM edges
        WHERE scenario_id=$1) parts_per )) row_num) samples,
     (SELECT row_number() over () row_num, distance FROM
       (SELECT distance FROM edges WHERE scenario_id=$1 and phase_id=$2
        ORDER BY distance) ordered_dists) ordered_dists_row_nums
     WHERE samples.row_num=ordered_dists_row_nums.row_num
$$
LANGUAGE SQL;

-- Calculate the cumulative, weighted demand over distances
-- Distances defined by uniform_sample_dists function
CREATE OR REPLACE FUNCTION demand_over_dist(
  scenario_id integer,
  phase_id integer,
  num_partitions integer)
  RETURNS TABLE (distance integer, demand double precision)
  AS 
$$ 
  WITH dists AS 
  (SELECT * FROM uniform_sample_dists($1, $2, $3))
  SELECT 
    d.distance,
    (cast(sum(d.weight) as float) / 
    (SELECT cast(sum(weight) as float) FROM 
        nodes, 
        phase_ancestors pa
      WHERE 
        pa.phase_id=$2 AND
        pa.scenario_id=$1 AND
        nodes.scenario_id=$1 AND
        nodes.phase_id=pa.ancestor_phase_id AND 
        nodes.node_type_id=1)) weight
  FROM 
    (SELECT DISTINCT node_id, weight, dists.distance FROM
      (SELECT n.id node_id, weight, e.distance
        FROM 
          edges e, 
          nodes n
          /* no need to join this --> phase_ancestors pa */
        WHERE 
          /* no need to join
          pa.phase_id=$2 AND
          pa.scenario_id=$1 AND */
          n.node_type_id=1 AND
          e.from_node_id=n.id AND
          e.scenario_id=$1 AND
          e.phase_id=$2) demand_dist, 
      dists
      WHERE 
        demand_dist.distance <= dists.distance
     ) d
  GROUP BY d.distance
  ORDER BY d.distance
$$
LANGUAGE SQL;


-- Calculate a density histogram 
CREATE OR REPLACE FUNCTION density_over_dist(
  scenario_id integer,   
  phase_id integer,
  num_partitions integer)
  RETURNS TABLE (distance integer, demand double precision)
  AS 
$$ 
  WITH dists AS 
  (SELECT actual.distance actual_dist, offset_dist.distance offset_dist FROM 
    (SELECT row_number() over () row_num, * FROM uniform_dists($1, $2, $3)) actual,
    (SELECT (row_number() over () - 1) row_num, * FROM uniform_dists($1, $2, $3) OFFSET 1) offset_dist
  WHERE actual.row_num=offset_dist.row_num)
  SELECT 
    d.distance,
    (cast(sum(d.weight) as float) / 
    (SELECT cast(sum(weight) as float) 
        FROM 
          nodes,
          phase_ancestors pa
        WHERE 
          pa.phase_id=$2 AND
          pa.scenario_id=$1 AND
          nodes.phase_id=pa.ancestor_phase_id AND
          nodes.scenario_id=$1 AND 
          nodes.node_type_id=1)) weight
  FROM 
    (SELECT DISTINCT node_id, weight, dists.offset_dist distance FROM
      (SELECT n.id node_id, weight, e.distance
        FROM edges e, nodes n
        WHERE 
          n.node_type_id=1 AND
          e.from_node_id=n.id AND
          e.phase_id = $2 AND
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
