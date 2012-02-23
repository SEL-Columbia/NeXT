import logging

from shutil import copyfileobj
import os
import csv
import simplejson
import StringIO

from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden

from geoalchemy import WKTSpatialElement
from sqlalchemy.sql import text

from next.models import Scenario
from next.models import Node
from next.models import Edge
from next.models import NodeType
from next.models import DBSession
from next.models import get_node_type
from next.spatial_utils import pg_import

logger = logging.getLogger(__name__)

def get_object_or_404(cls, request):
    session = DBSession()
    id = request.matchdict.get('id', None)
    if id is None:
        raise NameError('You have id in your request matchdict')
    obj = session.query(cls).get(id)
    if obj is not None:
        return obj
    else:
        raise HTTPNotFound('Unable to locate class:%s id:%s' % (cls, id))


def json_response(data):
    return Response(simplejson.dumps(data),
                    content_type='application/json')


@view_config(route_name='index', renderer='index.mako')
def index(request):
    session = DBSession()
    return {'scenarios': session.query(Scenario).all()}


@view_config(route_name='show-all-scenarios')
def show_all(request):
    session = DBSession()
    scs = session.query(Scenario).all()
    return json_response({'type': 'FeatureCollection',
                          'features': [sc.to_geojson() for sc in scs]})


def csv_to_nodes(request, csv_file, scenario, node_type):
    """Function to read a csv file and add the contents of a csv file to
    the nodes table.

    Arguments:
        csv_reader:
        scenario:
        node_type:
    Returns a list of nodes to be added.

    """
    c = []  # collector list for all of the nodes.
    # get the raw file data and write it to tmp file
    raw_file = csv_file.file
    filename = csv_file.filename

    tmp_file = os.path.join(
        request.registry.settings['next.temporary_folder'],
        filename
        )

    copyfileobj(raw_file, open(tmp_file, 'wb'))

    # open the csv reader
    # using rU because of encoding issues with windows
    csv_reader = csv.reader(open(tmp_file, 'rU'))
    for row in csv_reader:
        geom = WKTSpatialElement('POINT(%s %s)' % (row[0], row[1]))

        if len(row) == 3:
            # do we have a csv file with a weight ?
            # if so, add it to the node
            node = Node(geom, row[2], node_type, scenario)
            c.append(node)
        elif len(row) == 2:
            # else don't add a weight to the node
            node = Node(geom, 1, node_type, scenario)
            c.append(node)

    return c

def write_tmp_file(post_file, tmp_file):
    raw_file = post_file.file
    open_tmp = open(tmp_file, 'wb')
    copyfileobj(raw_file, open_tmp)
    open_tmp.close()
    
    
@view_config(route_name='create-scenario', renderer='create-scenario.mako')
def create_scenario(request):
    """
    Bulk load the nodes from the population and facility csv's
    """
    if(request.method=='POST'):
        session = DBSession()
        dbapi_conn = session.connection().connection
        sc = None
        try:
            logger.debug("Start node population")
            pop_type = get_node_type('population')
            fac_type = get_node_type('facility')
    
            name = request.POST['name']
            # make sure that we have a name
            # TODO we should
            assert len(name) != 0
    
            sc = Scenario(name)
            session.add(sc)
            session.flush()
            pop_file = request.POST['pop-csv']
            fac_file = request.POST['fac-csv']
            
            tmp_pop_file = os.path.join(
                request.registry.settings['next.temporary_folder'],
                pop_file.filename
                )

            tmp_fac_file = os.path.join(
                request.registry.settings['next.temporary_folder'],
                fac_file.filename
                )

            write_tmp_file(pop_file, tmp_pop_file)
            write_tmp_file(fac_file, tmp_fac_file)

            importer = pg_import.PGImport(dbapi_conn, 'nodes', ('weight', 'node_type_id', 'scenario_id', 'point'))
            pop_translator = pg_import.CSVToCSV_WKT_Point((0, 1), {0: 1, 1: pop_type.id, 2: sc.id})
            fac_translator = pg_import.CSVToCSV_WKT_Point((0, 1), {0: 1, 1: fac_type.id, 2: sc.id})
            pop_stream = StringIO.StringIO()
            fac_stream = StringIO.StringIO()
            in_pop_stream = open(tmp_pop_file, 'rU')
            in_fac_stream = open(tmp_fac_file, 'rU')
            #TODO:  may want to move srid to configuration at some point
            pop_translator.translate(in_pop_stream, pop_stream, 4326)
            fac_translator.translate(in_fac_stream, fac_stream, 4326)
            pop_stream.seek(0)
            fac_stream.seek(0)
            importer.do_import(pop_stream)
            importer.do_import(fac_stream)
            
            #do we need to close the out_pop_stream/fac_stream?
            dbapi_conn.commit()
            logger.debug("End node population")
        except Exception as error:
            dbapi_conn.rollback()
            raise(error)    

            
        # send the user to the run scenario page right now
        # at this point, we should have the scenario, so create the edges

        sc.create_edges()
        return HTTPFound(
            location=request.route_url('show-scenario', id=sc.id))
        # return HTTPFound(location=request.route_url('run-scenario', id=sc.id))
        
    elif request.method == 'GET':
        return {}
    else:
        raise HTTPForbidden()



@view_config(route_name='run-scenario')
def run_scenario(request):
    
    session = DBSession()
    scenario = get_object_or_404(Scenario, request)
    scenario.create_edges()
    return HTTPFound(
        location=request.route_url('show-scenario', id=scenario.id))


@view_config(route_name='show-population-json')
def show_population_json(request):
    session = DBSession()
    conn = session.connection()
    sc = get_object_or_404(Scenario, request)
    sql = text('''
    select nodes.id,
    nodes.weight,
    st_asgeojson(nodes.point),
    edges.distance, nodetypes.name
    from nodes, edges, nodetypes
    where nodes.scenario_id = :sc_id and
    nodes.id = edges.from_node_id and
    nodes.node_type_id = nodetypes.id
    ''')
    rset = conn.execute(sql, sc_id=sc.id).fetchall()
    feats = [
        {
        'type': 'Feature',
        'geometry': simplejson.loads(feat[2]),
        'properties': {
            'distance': feat[3],
            'type':feat[4] }
        } for feat in rset
     ]
    return json_response({'type': 'FeatureCollection', 'features': feats })


@view_config(route_name='show-facility-json')
def show_facility_json(request):
    sc = get_object_or_404(Scenario, request)
    nodes = sc.get_nodes().filter_by(node_type=get_node_type('facility'))
    return json_response(
        {'type': 'FeatureCollection',
         'features': [feat.to_geojson() for feat in nodes]}
        )


@view_config(route_name='graph-scenario')
def graph_scenario(request):
    sc = get_object_or_404(Scenario, request)
    return json_response(map(list, sc.get_population_vs_distance()))

@view_config(route_name='graph-scenario-cumul')
def graph_scenario_cumul(request):
    sc = get_object_or_404(Scenario, request)
    return json_response(map(list, 
        sc.get_partitioned_pop_vs_dist(num_partitions=50)))

@view_config(route_name='show-scenario', renderer='show-scenario.mako')
def show_scenario(request):
    """
    """
    return {'scenario': get_object_or_404(Scenario, request)}


@view_config(route_name='find-pop-within')
def find_pop_with(request):
    sc = get_object_or_404(Scenario, request)
    distance = request.json_body.get('d', 1000)
    print(distance)
    return json_response(
        {'total': sc.get_percent_within(distance)}
        )


@view_config(route_name='create-facilities')
def create_facilities(request):
    """
    Create new facilities based on distance and re-create the nearest neighbor edges.  Display the new output
    """
    sc = get_object_or_404(Scenario, request)
    distance = float(request.json_body.get('d', 1000))
    num_facilities = int(request.json_body.get('n', 1))

    centroids = sc.locate_facilities(distance, num_facilities)
    sc.create_nodes(centroids, 'facility')
    sc.create_edges()
    return HTTPFound(
        location=request.route_url('show-scenario', id=sc.id))

    
@view_config(route_name='add-new-nodes')
def add_new_nodes(request):
    session = DBSession()
    sc = get_object_or_404(Scenario, request)
    new_nodes = []
    facility_type = get_node_type('facility')
    for new_node in request.json_body:
        geom = WKTSpatialElement(
            'POINT(%s %s)' % (new_node['x'], new_node['y'])
            )
        node = Node(geom, 1, facility_type, sc)
        new_nodes.append(node)
    session.add_all(new_nodes)
    return Response(str(new_nodes))


@view_config(route_name='remove-scenarios')
def remove_scenario(request):
    session = DBSession()
    sc_pairs = request.params
    sc_dict = sc_pairs.dict_of_lists()
    if (sc_dict.has_key('scenarios')):
        for sid in sc_pairs.dict_of_lists()['scenarios']:
            session.query(Edge).filter(Edge.scenario_id==int(sid)).delete()
            session.query(Node).filter(Node.scenario_id==int(sid)).delete()
            session.query(Scenario).filter(Scenario.id==int(sid)).delete()

    return HTTPFound(location=request.route_url('index'))
