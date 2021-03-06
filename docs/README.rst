Releases
=========

**0.3          [2012-04-09]**

Introduced "Phases":
- Each scenario can have a tree of phases
- A phase consitutes the cumulative demand/supply lineage
- Each addition of supply creates a new child phase

Flexible csv import:
- considers header fields of:
  - longitude (or lon or x)
  - latitude (or lat or y)
  - weight
If no header, assumes columns are longitude, latitude and weight

**0.2a-407c53e [2011-09-29]**

Fixed BUG in cumulative demand SQL that was causing browser crash.

**0.2-ac8a75b [2011-09-29]**

Release that includes all originally spec'd functionality.
Added:

- The ability to add a supply and recalculate NN's
- Display of the cumulative demand within X meters
- Calculator to determine percent within X meters
- Minor display fixes

**0.1-e0a2860 [2011-09-26]**

Initial release, demo'd to Vijay Modi and Matt Berg on 2011-09-21.  

- Import of Supply/Demand csv files
- Calculation of nearest supply per demand node 
- Rendering of supply, demand nodes on google maps
- Display of demand distance to supply graph


Installation
============

The following is a brief guide to installing the NeXT application
(YMMV depending on your system and experience)

**Prerequisites**

The following applications/libraries are required by NeXT

::


  Python 2.7
  R (r-base)
  R's sp package (via install.packages('sp') from within R)
  python-dev
  python-setuptools
  python-virtualenv
  python-pastescript (python lib for paster)
  postgresql-9.1 (and postgresql-server-dev-9.1)
  PostGIS 2.0 (see http://trac.osgeo.org/postgis/wiki/UsersWikiInstall)
  (note that PostGIS 2.0 has several dependencies itself, like libgdal and libgeos)

**Install & Run**

1. Check out the project 

::

  git clone git:github.com/modilabs/NeXT.git

2. Setup the virtualenv and activate it


3. Install the python project requirements and deploy the development egg locally
   
:: 

  pip install -r requirements.txt
  python setup.py develop

4. Install openlayers javascript libraries into the project's "static" subdir (i.e. <project>/static/openlayers should contain the openlayers js and css files)

5. Create the 'next' postgresql database and enable postgis extensions

::
  
  ./drop-and-create.sh

This should create a postgis enabled db owned by user 'next'

6. Create the next model via the next.sql script

::

  psql -d next -f db/next.sql

You can ignore the "already exists" errors when running (TODO:  clean this step up)

7. Populate 'next' node_types with demand and supply types

::

  paster import-fixtures <production | development>.ini fixtures.yaml  

8. Load Custom DB Functions

::

  ./load-sql.sh next
  
9. Run the development server 
   
::

  paster serve development.ini --reload


10. (optional) Run the production server.  

  First install

::

  apache2
  modwsgi (see http://code.google.com/p/modwsgi/wiki/QuickInstallationGuide)
  
Production runs on mod_wsgi via apache.  You can find a tutorial here:  http://docs.pylonsproject.org/projects/pyramid/en/1.0-branch/tutorials/modwsgi/index.html.  
Our deployment is configure with a "next" config file in /etc/apache2/sites-available that references the NeXT/next.wsgi script in this repo.  This config is then soft linked to from the /etc/apache2/sites-enabled dir.  


Use Cases
=========

The following are the initial envisioned use cases for the NeXT spatial analysis tool.

**Create Scenario**

1. From the index view, navigate to create-scenario view.

2. Upload 2 (csv?) files:

  - Supply (Facilities x, y, weight)
  - Demand (Population x, y, weight)

3. Assign a name to the scenario and save it.

4. This runs the scenario and brings the user to the show-scenario view.

**View Scenario**

1. From the index view, select the scenario to view (brings the user to the show-scenario view).

2. The show-scenario view displays the map of the Supply and Demand along with the "Demand within Distance to Facility" graph.

**Add Facility [Future]**

1. From the show-scenario view, user adds a supply node to the map via mouse-click. 

2. The scenario is re-run and the view is refreshed with an updated map and graph.



Next steps for NeXT
===================

Ideal state
----------- 

#. We want the ability to chain high level spatial operations together.

#. We want these operations to be fast.

#. Render the results in graph and map from. Targeting the browser.

Open questions
--------------

#. SQL vs ORM? 

#. Client vs server rendering of information?

#. Frameworks?

#. Cleaning and clustering.

#. User input, post processing. 


Current database tables as of Wed 26 Oct 2011 12:37:11 PM EDT
-------------------------------------------------------------

TODO, we should create a DDL sql file so we can create our tables
without our python application.

Scenario
   id       -> pk
   name     -> str

NodeType
   id       -> pk
   name     -> str

Node
  id        -> pk
  point     -> geometry
  weight    -> int
  node_type -> fk -> NodeType
  scenario  -> fk -> Scenario

Edge
  id        -> pk
  from_node -> fk Node
  to_node   -> fk Node
  distance  -> int



User stories
------------

*Chris this is my attempt to define how a user could use our system*

As a user, I want to be able to import a CSV (Or Shapefile) file into
a postgis database via a web interface.

As a user, I want to be able to select the spatial operation or
collection of spatial operation to be preformed on my data. In effect
the system presents me with a list of options to select from and a
button named *Run*. 

As a user, I want to be able to view the results of these operations
in the web browser. In both map and graph form.

As a user, I should be able to export the results of these operations
as a shapefile or csv file. 

Open Questions
--------------

- How do we map/translate user supplied information to
  our database schema. What geometry types do we want to support? As I
  see it, the more complex inputs we support, the more complicated our
  system must become, maybe.

  Right now we only support three columns for nodes::

   x | Y | weight
   --------------
  

  If we want to support more complex schema, how do we handle this in
  the a relational database?


- Do we want to store the resulting information in a database based a
  user's information? How do we want to even handle users in our
  system, or should that be handled by a different layer.

- Service vs application. How do we envision our application? Is this
  a service or a specific application? 


Parts
------
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


