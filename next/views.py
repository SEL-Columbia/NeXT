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
from spatial_utils import pg_import

logger = logging.getLogger(__name__)

def get_object_or_404(cls, request):
    session = DBSession()
    id = request.matchdict.get('id', None)
    if id is None:
        raise NameError('You have no id in your request matchdict')
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


@view_config(route_name='scenarios', request_method='GET')
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
def show_create_scenario(request): 
    return {}
    
@view_config(route_name='scenarios', request_method='POST')
def create_scenario(request):
    """
    Bulk load the nodes from the demand and supply csv's
    """
            
    if(request.method=='POST'):
        session = DBSession()
        dbapi_conn = session.connection().connection
        sc = None
        try:
            logger.debug("Start node demand")
            demand_type = get_node_type('demand')
            supply_type = get_node_type('supply')
    
            name = request.POST['name']
            # make sure that we have a name
            # TODO we should
            assert len(name) != 0
    
            sc = Scenario(name)
            session.add(sc)
            session.flush()
            demand_file = request.POST['demand-csv']
            supply_file = request.POST['supply-csv']

            tmp_demand_file = os.path.join(
                request.registry.settings['next.temporary_folder'],
                demand_file.filename
                )

            tmp_supply_file = os.path.join(
                request.registry.settings['next.temporary_folder'],
                supply_file.filename
                )

            write_tmp_file(demand_file, tmp_demand_file)
            write_tmp_file(supply_file, tmp_supply_file)

            importer = pg_import.PGImport(dbapi_conn, 'nodes', ('weight', 'node_type_id', 'scenario_id', 'point'))
            demand_translator = pg_import.CSVToCSV_WKT_Point((0, 1), {0: 1, 1: demand_type.id, 2: sc.id})
            supply_translator = pg_import.CSVToCSV_WKT_Point((0, 1), {0: 1, 1: supply_type.id, 2: sc.id})
            demand_stream = StringIO.StringIO()
            supply_stream = StringIO.StringIO()
            in_demand_stream = open(tmp_demand_file, 'rU')
            in_supply_stream = open(tmp_supply_file, 'rU')
            #TODO:  may want to move srid to configuration at some point
            demand_translator.translate(in_demand_stream, demand_stream, 4326)
            supply_translator.translate(in_supply_stream, supply_stream, 4326)
            demand_stream.seek(0)
            supply_stream.seek(0)
            importer.do_import(demand_stream)
            importer.do_import(supply_stream)
            
            #do we need to close the out_demand_stream/supply_stream?
            #TODO:  Figure out how to participate in the 
            #SQL Alchemy transaction...otherwise, this is 
            #difficult to test
            # dbapi_conn.commit()
            logger.debug("End node demand")
        except Exception as error:
            # dbapi_conn.rollback()
            raise(error)    

            
        # send the user to the run scenario page right now
        # at this point, we should have the scenario, so create the edges
        # session.commit()
        sc.create_edges()
        return HTTPFound(
            location=request.route_url('show-scenario', id=sc.id))
        # return HTTPFound(location=request.route_url('run-scenario', id=sc.id))
        
    elif request.method == 'GET':
        return {}
    else:
        raise HTTPForbidden()



# @view_config(route_name='run-scenario')
def run_scenario(request):
    """ Create the nearest-neighbor edges """

    session = DBSession()
    scenario = get_object_or_404(Scenario, request)
    scenario.create_edges()
    # need to do an explicit commit here since no SQLAlchemy
    # objects were written (therefore SQLAlchemy doesn't think it needs to 
    # commit)
    # session.connection().connection.commit()
    return HTTPFound(
        location=request.route_url('show-scenario', id=scenario.id))


def to_geojson_feature_collection(features):
    "Returns list of entities as a GeoJSON feature collection"
    return json_response(
            {'type': 'FeatureCollection',
             'features': [feat.to_geojson() for feat in features]})


@view_config(route_name='nodes', request_method='GET')
def show_nodes(request):
    """ 
    Returns nodes as geojson
    type parameter used as a filter
    If type=='demand', then add nearest-neighbor distance to output
    """

    session = DBSession()
    scenario = get_object_or_404(Scenario, request)
    nodes = []
    if (request.GET.has_key("type")):
        request_node_type = request.GET["type"]
        if(request_node_type == "demand"):
            return show_demand_json(scenario)
        else: 
            nodes = scenario.get_nodes().\
                filter_by(node_type=get_node_type(request_node_type))
    else:
        nodes = scenario.get_nodes()

    return to_geojson_feature_collection(nodes)


def show_demand_json(scenario):
    session = DBSession()
    conn = session.connection()
    sql = text('''
    select nodes.id,
    nodetypes.name,
    nodes.weight,
    st_asgeojson(nodes.point),
    edges.distance 
    from nodes, edges, nodetypes
    where nodes.scenario_id = :sc_id and
    nodes.id = edges.from_node_id and
    nodes.node_type_id = nodetypes.id and
    nodetypes.name='demand'
    ''')
    rset = conn.execute(sql, sc_id=scenario.id).fetchall()
    feats = [
        {
        'type': 'Feature',
        'geometry': simplejson.loads(feat[3]),
        'properties': {
            'id':feat[0],
            'type':feat[1],
            'weight':feat[2],
            'distance': feat[4]
            }
        } for feat in rset
    ]
    return json_response({'type': 'FeatureCollection', 'features': feats })


@view_config(route_name='graph-scenario')
def graph_scenario(request):
    sc = get_object_or_404(Scenario, request)
    return json_response(map(list, sc.get_demand_vs_distance(num_partitions=20)))


@view_config(route_name='graph-scenario-cumul')
def graph_scenario_cumul(request):
    sc = get_object_or_404(Scenario, request)
    return json_response(map(list, 
        sc.get_partitioned_demand_vs_dist(num_partitions=100)))


@view_config(route_name='show-scenario', renderer='show-scenario.mako')
def show_scenario(request):
    """
    """
    return {'scenario': get_object_or_404(Scenario, request)}


@view_config(route_name='find-demand-within')
def find_demand_with(request):
    sc = get_object_or_404(Scenario, request)
    distance = request.json_body.get('d', 1000)
    return json_response(
        {'total': sc.get_percent_within(distance)}
        )


@view_config(route_name='create-supply-nodes')
def create_supply_nodes(request):
    """
    Create new supply based on distance and re-create the nearest neighbor edges.  Display the new output
    """
    session = DBSession()
    sc = get_object_or_404(Scenario, request)
    distance = float(request.json_body.get('d', 1000))
    num_supply_nodes = int(request.json_body.get('n', 1))

    centroids = sc.locate_supply_nodes(distance, num_supply_nodes)
    session.add_all(centroids)

    # need to flush so that create_edges knows about new nodes
    session.flush()
    sc.create_edges()
    return HTTPFound(
        location=request.route_url('show-scenario', id=sc.id))

    
@view_config(route_name='nodes', request_method='POST')
def add_nodes(request):
    session = DBSession()
    sc = get_object_or_404(Scenario, request)
    new_nodes = []
    for feature in request.json_body['features']:
        # assumes point geom
        coords = feature['geometry']['coordinates']
        geom = WKTSpatialElement(
            'POINT(%s %s)' % (coords[0], coords[1])
            )
        type_property = feature['properties']['type']
        weight = feature['properties']['weight']
        node_type = get_node_type(type_property)
        node = Node(geom, weight, node_type, sc)
        new_nodes.append(node)
    session.add_all(new_nodes)
    session.flush()
    sc.create_edges()
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
