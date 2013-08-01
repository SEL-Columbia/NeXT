import logging
from paste.script.command import Command
from pyramid.paster import bootstrap
from sqlalchemy import engine_from_config
from next import initialize_sql


logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)

geom_types = ('POINT', 'GEOMETRY',)
fix_folder = 'fixtures'


class ImportFixtures(Command):

    summary = ''
    parser = Command.standard_parser()
    parser.add_option('--input-file',
                      dest='input_file',
                      help='')

    def command(self):
        from yaml import load
        from shapely.wkt import loads

        config_uri = self.args[0]
        fixtures_data = load(open(self.args[1], 'r'))

        env = bootstrap(config_uri)
        engine = engine_from_config(env['registry'].settings, 'sqlalchemy.')

        try:
            engine.execute(
                'ALTER TABLE nodes DROP CONSTRAINT enforce_srid_point')
        except:
            pass

        initialize_sql(engine)

        from next.model.models import Base

        tables = Base.metadata.tables
        for record in fixtures_data:
            table = tables.get(record['table'], None)
            if table is not None:
                logger.info('Load fixtures for table -> %s ' % table)
                inst = {}
                for column_name, cell in record['fields'].iteritems():
                    column_spec = table.c.get(column_name, None)
                    if column_spec is not None:
                        if str(column_spec.type) in geom_types:
                            # Hardcoding SRID=4326 for now
                            # PostGIS 2.0 doesn't default it
                            inst[column_spec.name] \
                                = "SRID=4326;%s" % loads(cell).wkb.encode('hex')
                        else:
                            inst[column_spec.name] = cell
                table.insert().execute(inst)


class ExportFixtures(Command):

    summary = ''
    parser = Command.standard_parser()
    parser.add_option('--output',
                      dest='output',
                      help='')

    def command(self):
        from next.models import Base
        from shapely.wkb import loads
        from yaml import dump
        config_uri = self.args[0]
        env = bootstrap(config_uri)
        engine = engine_from_config(env['registry'].settings, 'sqlalchemy.')
        initialize_sql(engine)

        tables = Base.metadata.sorted_tables
        assert self.args[1] is not None, 'You should provide a output file'
        yaml_file = open(self.args[1], 'w')
        fixtures = []

        for table in tables:
            for row in table.select().execute():
                c = {'table': table.name, 'fields': {}}
                columns = table.c.keys()
                # sanity check before we export the data
                assert len(columns) == len(row)
                for i in range(len(columns)):
                    column = table.c[columns[i]]
                    cell = row[i]
                    if str(column.type) in geom_types:
                        # we have to call str on the binary column first
                        c['fields'][column.name] = loads(str(cell)).wkt
                    else:
                        c['fields'][column.name] = cell

                fixtures.append(c)

        dump(fixtures, yaml_file)


class ShapefileConvert(Command):

    summary = ''
    parser = Command.standard_parser()
    parser.add_option('--shapefile', dest='shape_path', help='')

    def command(self):
        """
        """
        from osgeo import ogr
        from osgeo.osr import SpatialReference
        sp = SpatialReference()
        sp.ImportFromEPSG(4326)
        shapefile = ogr.Open(self.options.shape_path)
        layer = shapefile.GetLayer()
        for i in xrange(0, layer.GetFeatureCount()):
            f = layer.GetFeature(i)
            geometry = f.GetGeometryRef()
            geometry.TransformTo(sp)
            #print geometry.ExportToWkt()
            print '%s, %s' % (geometry.GetX(), geometry.GetY())

