Releases
=========

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

  postgresql-9.0 (and postgresql-server-dev-9.0)
  PostGIS (see http://postgis.refractions.net/docs/ch02.html)
  Python 2.7
  python-psycopg2 (python lib for postgresql)
  python-setuptools 


**Install & Run**

1. Check out the project 

::

  git clone git:/github.com/modilabs/NeXT.git

2. Setup the virtualenv and activate it

3. Install the python project requirements 
   
:: 

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


