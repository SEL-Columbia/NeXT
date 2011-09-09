dropdb next

createdb next 

psql -d next -f /usr/share/postgresql/contrib/postgis-1.5/postgis.sql
psql -d next -f /usr/share/postgresql/contrib/postgis-1.5/spatial_ref_sys.sql
