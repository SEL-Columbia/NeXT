CREATE OR REPLACE FUNCTION nodes_from_phase(
  scenario_id integer,
  phase_id integer)
  RETURNS TABLE (id integer, 
                 weight integer, 
                 node_type_id integer,
                 scenario_id integer,
                 phase_id integer,
                 point geometry)
  AS
$$
  SELECT id, weight, node_type_id, scenario_id, phase_id, point FROM nodes
  WHERE scenario_id=$1 AND
        phase_id IN (SELECT id FROM phases_from_root($1, $2));
$$
LANGUAGE SQL;
