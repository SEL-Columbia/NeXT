-- Drop triggers
DROP TRIGGER tgr_phase_id ON phases;
DROP TRIGGER tgr_phase_ancestors_add ON phases;

-- Drop functions
DROP FUNCTION tgr_phase_id();
DROP FUNCTION tgr_phase_ancestors_add();
DROP FUNCTION phases_from_root(integer, integer);

-- Drop relationship from nodes to phases
ALTER TABLE nodes DROP COLUMN phase_id;

-- Ditto for edges
ALTER TABLE edges DROP COLUMN phase_id;

-- Drop phases
DROP TABLE phase_ancestors;
DROP TABLE phases;

