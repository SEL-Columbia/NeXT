#!/bin/bash

files="db/base.sql db/0_base.sql db/1_base.sql db/2_phases.sql db/9_nodes_from_phase.sql"
for file in $files;
  do psql -d $1 -f $file
done

