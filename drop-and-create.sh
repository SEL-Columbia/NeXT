dropdb $1

createdb $1

sql_load_list="postgis.sql spatial_ref_sys.sql"

for file in $sql_load_list; 
do 
  file_path=`find /usr/share/postgresql/9.1/contrib/postgis-2.0 -name $file`
  if [ -f "$file_path" ]; then
    psql -U postgres -d $1 -f "$file_path"
  else
    echo "$file not found, check your postgis installation."
    return -1
  fi
done 
