-- phase id trigger
-- Needs to be created prior to adding root phases to
-- existing scenarios and relating Nodes/Edges to them
DROP TRIGGER tgr_phase_id ON phases;

CREATE TRIGGER tgr_phase_id BEFORE INSERT ON phases FOR EACH ROW EXECUTE PROCEDURE tgr_phase_id();

DROP TRIGGER tgr_phase_ancestors ON phases;

CREATE TRIGGER tgr_phase_ancestors_add AFTER INSERT ON phases
    FOR EACH ROW EXECUTE PROCEDURE tgr_phase_ancestors_add();
