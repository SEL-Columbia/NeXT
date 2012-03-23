-- Drop relationship from nodes to phases
ALTER TABLE nodes DROP COLUMN phase_id;

-- Ditto for edges
ALTER TABLE edges DROP COLUMN phase_id;

-- Drop phases
DROP TABLE phases;

-- Drop trigger function
DROP FUNCTION tgr_phase_id();
