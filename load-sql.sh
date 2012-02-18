#!/bin/bash

files=`ls db/*.sql`
for file in $files;
  do psql -d next -f $file
done

