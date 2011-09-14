dropdb next

createdb next 
createlang plpgsql next

psql -d next -f /usr/share/postgresql/8.4/contrib/postgis-1.5/postgis.sql
psql -d next -f /usr/share/postgresql/8.4/contrib/postgis-1.5/spatial_ref_sys.sql
