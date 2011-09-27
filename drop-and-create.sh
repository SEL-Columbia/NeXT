dropdb next

createdb next 

pgis_sql=`find /usr/share/postgresql -name postgis.sql`
if [ -f "$pgis_sql" ]; then
    psql -d next -f "$pgis_sql"
else
    echo "postgis.sql not found, check your postgis installation."
    return -1
fi

sp_ref_sql=`find /usr/share/postgresql -name spatial_ref_sys.sql`
if [ -f "$sp_ref_sql" ]; then
    psql -d next -f "$sp_ref_sql"
else
    echo "spatial_ref_sys.sql not found, check your postgis installation."
    return -1
fi
