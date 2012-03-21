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
