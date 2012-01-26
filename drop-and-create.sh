dropdb next

createdb next 

sql_load_list="postgis.sql spatial_ref_sys.sql rtpostgis.sql topology.sql"

for file in $sql_load_list; 
do 
  file_path=`find /usr/share/postgresql -name $file`
  if [ -f "$file_path" ]; then
    psql -U postgres -d next -f "$file_path"
  else
    echo "$file_path not found, check your postgis installation."
    return -1
  fi
done 
