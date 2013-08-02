-- phase id trigger
-- Needs to be created prior to adding root phases to
-- existing scenarios and relating Nodes/Edges to them
-- Ensure that phase id is set appropriately by default
CREATE FUNCTION tgr_phase_id() RETURNS TRIGGER AS $$
    BEGIN
        IF TG_OP = 'INSERT' THEN
            -- Set ID to (count of all phases for THIS scenario) + 1
            NEW.id := count(*)+1 from phases where scenario_id=NEW.scenario_id;
        END IF;
        RETURN NEW;
    END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tgr_phase_id BEFORE INSERT ON phases
    FOR EACH ROW EXECUTE PROCEDURE tgr_phase_id();

-- Get entire branch of phases from "this" phase to root
-- Created PRIOR to phase_ancestor trigger which depends on this
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

-- Ensure that phase_ancestors are updated each time we add a phase
-- (phases are only inserted/deleted, never updated)
CREATE FUNCTION tgr_phase_ancestors_add() RETURNS TRIGGER AS $$
    BEGIN
        IF TG_OP = 'INSERT' THEN
            -- Populate phase_ancestors with branch of phases
            INSERT INTO phase_ancestors 
              (phase_id, ancestor_phase_id, scenario_id)
              SELECT NEW.id, id, NEW.scenario_id 
              FROM phases_from_root(NEW.scenario_id, NEW.id);
        END IF;
        RETURN NEW;
    END;
$$ 
LANGUAGE plpgsql;

CREATE TRIGGER tgr_phase_ancestors_add AFTER INSERT ON phases
    FOR EACH ROW EXECUTE PROCEDURE tgr_phase_ancestors_add();
