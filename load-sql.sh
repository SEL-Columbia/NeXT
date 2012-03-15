#!/bin/bash

files=`ls db/*.sql`
for file in $files;
  do psql -d $1 -f $file
done

