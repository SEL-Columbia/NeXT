Releases
=========

**0.2a-407c53e [2011-09-29]**

Fixed BUG in cumulative population SQL that was causing browser crash.

**0.2-ac8a75b [2011-09-29]**

Release that includes all originally spec'd functionality.
Added:

- The ability to add a facility and recalculate NN's
- Display of the cumulative population within X meters
- Calculator to determine percent within X meters
- Minor display fixes

**0.1-e0a2860 [2011-09-26]**

Initial release, demo'd to Vijay Modi and Matt Berg on 2011-09-21.  

- Import of Facilities/Population csv files
- Calculation of nearest facility per population point
- Rendering of facilities, population points on google maps
- Display of population distance to facility graph


Installation
============

The following is a brief guide to installing the NeXT application
(YMMV depending on your system and experience)

**Prerequisites**

The following applications/libraries are required by NeXT::

  python-setuptools
  python-virtualenv
  postgresql-9.0 (and postgresql-server-dev-9.0)
  PostGIS (see http://postgis.refractions.net/docs/ch02.html)
  (note that PostGIS has several dependencies itself)
  Python 2.7
  python-psycopg2 (python lib for postgresql)
  python-setuptools 


**Install & Run**

1. Check out the project 

::

  git clone git:/github.com/modilabs/NeXT.git

2. Setup the virtualenv and activate it

3. Install the python project requirements and deploy the development egg locally
   
:: 

  python setup.py install
  python setup.py develop

4. Install openlayers javascript libraries into the project's "static" subdir (i.e. <project>/static/openlayers should contain the openlayers js and css files)

5. Run the development server 
   
::

  paster serve developmen.ini --reload


Use Cases
=========

The following are the initial envisioned use cases for the NeXT spatial analysis tool.

**Create Scenario**

1. From the index view, navigate to create-scenario view.

2. Upload 2 (csv?) files:

  - Facilities (x, y)
  - Population (x, y, count)

3. Assign a name to the scenario and save it.

4. This runs the scenario and brings the user to the show-scenario view.

**View Scenario**

1. From the index view, select the scenario to view (brings the user to the show-scenario view).

2. The show-scenario view displays the map of the Facilities and Population along with the "Households within Distance to Facility" graph.

**Add Facility [Future]**

1. From the show-scenario view, user adds a facility to the map via mouse-click. 

2. The scenario is re-run and the view is refreshed with an updated map and graph.



Next steps for NeXT
===================

Ideal state
----------- 

#. We want the ability to chain high level spatial operations together.

#. We want these operations to be fast.

#. Render the results in graph and map from. Targeting the browser.

#. 


Open questions
--------------

#. SQL vs ORM? 

#. Client vs server rendering of information? 

#. Frameworks?

#. Cleaning and clustering.

#. User input, post processing. 



Parts
------
Side not, a collection of tools that help us get our job done.

#. Translation layer from shapefiles, csv, geojson, xml to PostGIS.

   #. Web based translation layer
   #. Command line translation layer, 

Current tools
org2ogr -f "Postgresql" PG:dbname=db shapefile.shp -nln newLayerName
shp2pgsql -s srid shapfile.shp newLayerName | psql -d db 


#. Web based UI.


#. Sql -> graph. A simple way to render the results of a sql into a graph, or map?

   server -> client
   python, sql -> javascript svg. 



   $('#graph').nextGraph('#');
   $('#map').nextMap('select * from nodes where sc 1');
