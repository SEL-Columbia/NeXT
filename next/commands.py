
import logging
from paste.script.command import Command
from pyramid.paster import bootstrap
from sqlalchemy import engine_from_config
from next.models import initialize_sql


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
        from next.models import Base
        from shapely.wkt import loads

        config_uri = self.args[0]
        env = bootstrap(config_uri)
        engine = engine_from_config(env['registry'].settings, 'sqlalchemy.')
        try:
            engine.execute(
                'ALTER TABLE nodes DROP CONSTRAINT enforce_srid_point')
        except:
            pass

        initialize_sql(engine)

        tables = Base.metadata.sorted_tables
        for table in tables:
            yaml_data = load(open('%s/%s.yaml' % (fix_folder, table.name)))
            logger.info('Loading data for %s' % table.name)
            for obj in yaml_data:
                # sanity check before we import the data
                assert len(obj.keys()) == len(table.c.keys())
                inst = {}
                for key, value in obj.iteritems():
                    column_spec = table.c[key]
                    if str(column_spec.type) in geom_types:
                        inst[column_spec.name] = loads(value).wkb.encode('hex')
                    else:
                        inst[column_spec.name] = value
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

        tables = Base.metadata.tables
        for table_name in tables.keys():
            yaml_file = open('%s/%s.yaml' % (fix_folder, table_name), 'w')
            table_data = []
            table = tables[table_name]

            logger.info('Exporing table -> %s' % table)
            logger.info('Table columns  -> %s ' % table.c.keys())

            stmt = table.select()
            for row in stmt.execute():
                c = {}
                columns = table.c.keys()
                # sanity check before we export the data
                assert len(columns) == len(row)
                for i in range(len(columns)):
                    column = table.c[columns[i]]
                    cell = row[i]
                    if str(column.type) in geom_types:
                        # we have to call str on the binary column first
                        c[column.name] = loads(str(cell)).wkt
                    else:
                        c[column.name] = cell
                table_data.append(c)
            dump(table_data, yaml_file)
            yaml_file.close()
