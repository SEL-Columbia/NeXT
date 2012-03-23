CREATE OR REPLACE FUNCTION phases_from_root(
  scenario_id integer,
  phase_id integer)
  RETURNS TABLE (id integer, parent_id integer, name character)
  AS
$$
  WITH RECURSIVE children(id, parent_id, name) AS (
    SELECT id, parent_id, name FROM phases
    WHERE scenario_id=$1 AND id=$2
    UNION
        SELECT phases.id, phases.parent_id, phases.name
        FROM phases, children
        WHERE children.parent_id = phases.id)
  SELECT * FROM children;
$$
LANGUAGE SQL;
