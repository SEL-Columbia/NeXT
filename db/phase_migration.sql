-- Add the phases table
CREATE TABLE phases (
    id integer NOT NULL,
    scenario_id integer REFERENCES scenarios(id) NOT NULL, 
    parent_id integer,
    name character varying,
    PRIMARY KEY(id, scenario_id)
);

ALTER TABLE public.phases OWNER TO postgres;

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

-- Populate phases
INSERT INTO phases (scenario_id) (SELECT id FROM scenarios);

-- add phase id to nodes
ALTER TABLE nodes ADD COLUMN phase_id integer;

-- populate nodes phase id
UPDATE nodes SET phase_id = (SELECT max(id) FROM phases WHERE scenario_id=scenario_id);

-- Modify foreign key of nodes to include phase
ALTER TABLE nodes ADD CONSTRAINT nodes_phase_fkey FOREIGN KEY (phase_id, scenario_id) REFERENCES phases(id, scenario_id);

-- add phase id to edges
ALTER TABLE edges ADD COLUMN phase_id integer;

-- populate nodes phase id
UPDATE edges SET phase_id = (SELECT max(id) FROM phases WHERE scenario_id=scenario_id);

-- Modify foreign key of nodes to include phase
ALTER TABLE edges ADD CONSTRAINT edges_phase_fkey FOREIGN KEY (phase_id, scenario_id) REFERENCES phases(id, scenario_id);
