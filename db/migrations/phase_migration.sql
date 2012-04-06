-- ** DDL Section **
-- Add the phases table
CREATE TABLE phases (
    id integer NOT NULL,
    scenario_id integer REFERENCES scenarios(id) NOT NULL, 
    parent_id integer,
    name character varying,
    PRIMARY KEY(id, scenario_id)
);

ALTER TABLE public.phases OWNER TO postgres;

-- Add the phase_ancestors table
-- (a denormalization that helps map to object model) 
CREATE TABLE phase_ancestors (
    id SERIAL PRIMARY KEY,
    phase_id integer, 
    ancestor_phase_id integer, 
    scenario_id integer REFERENCES scenarios(id) NOT NULL
);

ALTER TABLE public.phase_ancestors OWNER TO postgres;

-- add phase id to nodes
ALTER TABLE nodes ADD COLUMN phase_id integer;

-- add phase id to edges
ALTER TABLE edges ADD COLUMN phase_id integer;

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

-- Populate phases
-- (done after triggers created so that phase_id's and
-- ancestors are created via triggers)
INSERT INTO phases (scenario_id) (SELECT id FROM scenarios);

-- populate nodes phase id
UPDATE nodes SET phase_id = (SELECT max(id) FROM phases WHERE scenario_id=scenario_id);

-- populate edges phase id
UPDATE edges SET phase_id = (SELECT max(id) FROM phases WHERE scenario_id=scenario_id);

-- NOW we can add foreign key constraints without violating them
-- (if added prior to populating phases in nodes/edges,
--  we'd have nodes/edges with null phases)
-- Modify foreign key of nodes to include phase
ALTER TABLE nodes ADD CONSTRAINT nodes_phase_fkey FOREIGN KEY (phase_id, scenario_id) REFERENCES phases(id, scenario_id);
-- Modify phases to include parent fkey
ALTER TABLE phases ADD CONSTRAINT phases_parent_fkey FOREIGN KEY (parent_id, scenario_id) REFERENCES phases(id, scenario_id);
-- Modify foreign key of nodes to include phase
ALTER TABLE edges ADD CONSTRAINT edges_phase_fkey FOREIGN KEY (phase_id, scenario_id) REFERENCES phases(id, scenario_id);

-- Modify foreign key of phase_ancestors to include phase
ALTER TABLE phase_ancestors ADD CONSTRAINT phase_ancestors_phase_fkey FOREIGN KEY (phase_id, scenario_id) REFERENCES phases(id, scenario_id);
ALTER TABLE phase_ancestors ADD CONSTRAINT phase_ancestors_ancestor_phase_fkey FOREIGN KEY (ancestor_phase_id, scenario_id) REFERENCES phases(id, scenario_id);
