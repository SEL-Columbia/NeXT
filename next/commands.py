import csv
import logging
from paste.script.command import Command
from pyramid.paster import bootstrap
from sqlalchemy import engine_from_config
from next.models import initialize_sql
from geoalchemy import functions

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)


fix_folder = 'fixtures'


class ImportFixtures(Command):

    summary = ''
    parser = Command.standard_parser()
    parser.add_option('--input-file',
                      dest='input_file',
                      help='')

    def command(self):
        config_uri = self.args[0]
        env = bootstrap(config_uri)
        engine = engine_from_config(env['registry'].settings, 'sqlalchemy.')
        initialize_sql(engine)


class ExportFixtures(Command):

    summary = ''
    parser = Command.standard_parser()
    parser.add_option('--output',
                      dest='output',
                      help='')

    def command(self):
        from next.models import Base
        from shapely.wkb import loads
        config_uri = self.args[0]
        env = bootstrap(config_uri)
        engine = engine_from_config(env['registry'].settings, 'sqlalchemy.')
        initialize_sql(engine)

        tables = Base.metadata.tables
        for table_name in tables.keys():
            table = tables[table_name]

            #logger.info('Exporing table --> %s' % table)

            stmt = table.select()
            for row in stmt.execute():
                c = {}
                columns = table.c.keys()
                assert len(columns) == len(row)
                for i in range(len(columns)):
                    column = table.c[columns[i]]
                    cell = row[i]
                    if str(column.type) == 'POINT':
                        c[column.name] = loads(str(cell)).wkt
                    else:
                        c[column.name] = cell
                print c
