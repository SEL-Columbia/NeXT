import os
import sys

from setuptools import setup, find_packages
here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'simplejson',
    'gunicorn',
    'geojson',
    'psycopg2',
    'pyyaml',
    'numpy',
    'rpy2',
    'Shapely',
    'geoalchemy2',
    'colander',
    'SQLAlchemy',
    'transaction',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'zope.interface>=3.8.0',
    'zope.sqlalchemy',
    ]

if sys.version_info[:3] < (2, 5, 0):
    requires.append('pysqlite')

setup(name='NeXT',
      version='0.0',
      description='NeXT',
      long_description = README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='next',
      install_requires = requires,
      entry_points = """\
      [paste.paster_command]

      export-fixtures = next.commands:ExportFixtures
      import-fixtures = next.commands:ImportFixtures
      shape-converter = next.commands:ShapefileConvert

      [paste.app_factory]
      main = next:main
      """,
      paster_plugins=['pyramid'],
      )
