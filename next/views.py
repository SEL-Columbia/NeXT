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

from sqlalchemy.sql import text

from next.model.models import Scenario
from next.model.models import Phase
from next.model.models import PhaseAncestor
from next.model.models import Node
from next.model.models import Edge
from next.model.models import NodeType
from next.model.models import BASE_SRID
from next.model.models import DBSession
from next.model.models import get_node_type
from next.model.models import get_cumulative_nodes, get_nodes
from next.import_helpers import import_nodes
import shapely
from geoalchemy2.shape import to_shape, from_shape
from spatial_utils import pg_import

logger = logging.getLogger(__name__)

# Utility functions
def get_object_or_404(cls, request, id_fields=('id',)):
    session = DBSession()
    id_vals = [request.matchdict.get(id_fld, None) for id_fld in id_fields]
    # import pdb; pdb.set_trace()
    if id_vals is None:
        raise NameError('You have no fields that match in your request matchdict')
    # import pdb; pdb.set_trace()
    obj = session.query(cls).get(id_vals)
    if obj is not None:
        return obj
    else:
        raise HTTPNotFound('Unable to locate class:%s with ids:%s' % (cls, id_vals))


def to_geojson_feature_collection(features):
    "Returns list of entities as a GeoJSON feature collection"
    return json_response(
            {'type': 'FeatureCollection',
             'features': [feat.to_geojson() for feat in features]})


def json_response(data):
    return Response(simplejson.dumps(data),
                    content_type='application/json')


def write_tmp_file(post_file, tmp_file):
    raw_file = post_file.file
    open_tmp = open(tmp_file, 'wb')
    copyfileobj(raw_file, open_tmp)
    open_tmp.close()


def to_tree_rows(root_phase):
    """
    Create row based representation of tree to easily print something like:
    \1
     \2
      \3
     \4
      \5
      \6
    \7
    """
    rows = []
    def populate_rows(ph, depth):
        row = {'id': ph['id'], 'cols': depth}
        rows.append(row)
        for child in ph['children']:
            populate_rows(child, depth + 1)

    populate_rows(root_phase, 0)
    return rows


#View functions
@view_config(route_name='index', renderer='index.mako')
def index(request):
    session = DBSession()
    sc_dict = {'scenarios': session.query(Scenario).all()}
    return sc_dict 


@view_config(route_name='scenarios', request_method='GET')
def show_all(request):
    session = DBSession()
    scs = session.query(Scenario).all()
    return json_response({'type': 'FeatureCollection',
                          'features': [sc.to_geojson() for sc in scs]})


@view_config(route_name='phases', request_method='GET')
def show_phases(request):
    session = DBSession()
    scenario = get_object_or_404(Scenario, request, ('id',))
    return json_response({'type': 'FeatureCollection',
                          'features': scenario.get_phases_geojson()})

    
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
        sc = phase = None
        try:
            demand_type = get_node_type('demand', session)
            supply_type = get_node_type('supply', session)
    
            name = request.POST['name']
            # make sure that we have a name
            assert len(name) != 0
    
            sc = Scenario(name)
            session.add(sc)
            session.flush()

            # add the root phase to the scenario
            phase = Phase(sc)
            session.add(phase)
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

            in_demand_stream = open(tmp_demand_file, 'rU')
            in_supply_stream = open(tmp_supply_file, 'rU')

            import_nodes(dbapi_conn, in_demand_stream, 
                    demand_type.id, sc.id, phase.id)
            import_nodes(dbapi_conn, in_supply_stream, 
                    supply_type.id, sc.id, phase.id)
            
        except Exception as error:
            raise(error)    

            
        # send the user to the run scenario page right now
        # at this point, we should have the scenario/phase, 
        # so create the edges
        # session.commit()
        phase.create_edges()
        return HTTPFound(
            location=request.route_url('show-phase', id=sc.id, phase_id=phase.id))
        
    elif request.method == 'GET':
        return {}
    else:
        raise HTTPForbidden()

@view_config(route_name='create-phase', request_method='POST')
def create_phase(request):
    """
    Create a new phase as the child of existing phase
    NOTE:  Many children can be added to same phase 
    TODO:  Is this needed?  Should we ONLY create phases upon adding nodes?
    """
            
    session = DBSession()
    parent = get_object_or_404(Phase, request, ('phase_id', 'id'))
    phase = Phase(parent.scenario, parent)

    return HTTPFound(
        location=request.route_url('show-phase', id=phase.scenario_id, phase_id=phase.id))


# @view_config(route_name='create-edges')
def create_edges(request):
    """ Create the nearest-neighbor edges """

    session = DBSession()
    phase = get_object_or_404(Phase, request, ('phase_id', 'id'))
    phase.create_edges()
    # need to do an explicit commit here since no SQLAlchemy
    # objects were written (therefore SQLAlchemy doesn't think it needs to 
    # commit)
    # session.connection().connection.commit()
    return HTTPFound(
        location=request.route_url('show-phase', id=phase.scenario_id, phase_id=phase.id))


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
                filter_by(node_type=get_node_type(request_node_type, session))
    else:
        nodes = scenario.get_nodes()

    return to_geojson_feature_collection(nodes)


@view_config(route_name='phase-nodes', request_method='GET')
def show_phase_nodes(request):
    """ 
    Returns nodes as geojson
    type parameter used as a filter
    If type=='demand', then add nearest-neighbor distance to output
    """

    phase = get_object_or_404(Phase, request, ('phase_id', 'id'))
    nodes = []
    if (request.GET.has_key("type")):
        request_node_type = request.GET["type"]
        if(request_node_type == "demand"):
            return show_phase_demand_json(phase)
        else: 
            nodes = get_nodes(phase.scenario_id, phase.id, node_type=request_node_type)
    else:
        nodes = get_nodes(phase.scenario_id, phase.id)

    return to_geojson_feature_collection(nodes)


@view_config(route_name='cumulative-phase-nodes', request_method='GET')
def show_cumulative_phase_nodes(request):
    """ 
    Returns nodes as geojson
    type parameter used as a filter
    If type=='demand', then add nearest-neighbor distance to output
    """

    session = DBSession()
    phase = get_object_or_404(Phase, request, ('phase_id', 'id'))
    nodes = []
    if (request.GET.has_key("type")):
        request_node_type = request.GET["type"]
        if(request_node_type == "demand"):
            return show_cumulative_phase_demand_json(phase)
        else: 
            nodes = get_cumulative_nodes(phase.scenario_id, phase.id, node_type=request_node_type)
    else:
        nodes = get_cumulative_nodes(phase.scenario_id, phase.id)

    return to_geojson_feature_collection(nodes)


#TODO Refactor these show_demand functions (push to models?  factor out sql?
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

def show_phase_demand_json(phase):
    session = DBSession()
    conn = session.connection()
    sql = text('''
    select nodes.id,
    nodetypes.name,
    nodes.weight,
    st_asgeojson(nodes.point),
    edges.distance 
    from nodes, edges, nodetypes, phase_ancestors
    where nodes.scenario_id = :sc_id and
    nodes.phase_id = :ph_id
    edges.scenario_id = :sc_id and
    edges.phase_id = :ph_id and
    nodes.id = edges.from_node_id and
    nodes.node_type_id = nodetypes.id and
    nodetypes.name='demand'
    ''')
    rset = conn.execute(sql, sc_id=phase.scenario_id, ph_id=phase.id).fetchall()
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



def show_cumulative_phase_demand_json(phase):
    session = DBSession()
    conn = session.connection()
    sql = text('''
    select nodes.id,
    nodetypes.name,
    nodes.weight,
    st_asgeojson(nodes.point),
    edges.distance 
    from nodes, edges, nodetypes, phase_ancestors
    where nodes.scenario_id = :sc_id and
    nodes.phase_id = phase_ancestors.ancestor_phase_id and
    phase_ancestors.phase_id = :ph_id and
    edges.scenario_id = phase_ancestors.scenario_id and
    edges.phase_id = phase_ancestors.phase_id and
    nodes.id = edges.from_node_id and
    nodes.node_type_id = nodetypes.id and
    nodetypes.name='demand'
    ''')
    rset = conn.execute(sql, sc_id=phase.scenario_id, ph_id=phase.id).fetchall()
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

@view_config(route_name='graph-phase')
def graph_phase(request):
    session = DBSession()
    phase = get_object_or_404(Phase, request, ('phase_id', 'id'))
    return json_response(map(list, phase.get_demand_vs_distance(num_partitions=20)))


@view_config(route_name='graph-phase-cumul')
def graph_phase_cumul(request):
    session = DBSession()
    phase = get_object_or_404(Phase, request, ('phase_id', 'id'))
    return json_response(map(list, 
        phase.get_partitioned_demand_vs_dist(num_partitions=100)))


@view_config(route_name='show-phase', renderer='show-phase.mako')
def show_phase(request):
    """
    """
    session = DBSession()
    scenario = get_object_or_404(Scenario, request)
    phase = get_object_or_404(Phase, request, ('phase_id', 'id'))
    phase_tree = scenario.get_phases_tree()
    tree_rows = to_tree_rows(phase_tree)
    return {'phase': phase,
            'scenario': scenario,
            'phase_tree_rows': tree_rows}


@view_config(route_name='find-demand-within')
def find_demand_with(request):
    session = DBSession()
    phase = get_object_or_404(Phase, request, ('phase_id', 'id'))
    distance = request.json_body.get('d', 1000)
    return json_response(
        {'total': phase.get_percent_within(distance)}
        )


@view_config(route_name='create-supply-nodes')
def create_supply_nodes(request):
    """
    Create new supply based on distance and re-create the nearest neighbor edges.  
    Create a new child phase of the phase passed in
    Display the new output
    """
    session = DBSession()
    phase = get_object_or_404(Phase, request, ('phase_id', 'id'))
    child_phase = Phase(phase.scenario, phase)
    session.add(child_phase)
    session.flush() #flush this so object has all id's
    distance = float(request.json_body.get('d', 1000))
    num_supply_nodes = int(request.json_body.get('n', 1))

    centroids = child_phase.locate_supply_nodes(distance, num_supply_nodes, session)
    session.add_all(centroids)

    # need to flush so that create_edges knows about new nodes
    session.flush()
    child_phase.create_edges()
    return json_response(
        {'scenario_id': child_phase.scenario_id,
         'phase_id': child_phase.id}
        )
    #return HTTPFound(
    #    location=request.route_url('show-phase', id=phase.scenario_id, phase_id=child_phase.id))

    
@view_config(route_name='phase-nodes', request_method='POST')
def add_nodes(request):
    """
    Add nodes to a new child phase
    """
    session = DBSession()
    phase = get_object_or_404(Phase, request, ('phase_id', 'id'))
    child_phase = Phase(phase.scenario, phase)
    new_nodes = []
    for feature in request.json_body['features']:
        # assumes point geom
        coords = feature['geometry']['coordinates']
        shp_pt = shapely.geometry.Point(coords[0], coords[1])
        wkb_geom = from_shape(shp_pt, srid=BASE_SRID)
        type_property = feature['properties']['type']
        weight = feature['properties']['weight']
        node_type = get_node_type(type_property, session)
        node = Node(wkb_geom, weight, node_type, child_phase)
        new_nodes.append(node)
    session.add_all(new_nodes)
    session.flush()
    child_phase.create_edges()
    return json_response(
        {'scenario_id': child_phase.scenario_id,
         'phase_id': child_phase.id}
        )


@view_config(route_name='remove-scenarios')
def remove_scenario(request):
    session = DBSession()
    sc_pairs = request.params
    sc_dict = sc_pairs.dict_of_lists()
    if (sc_dict.has_key('scenarios')):
        for sid in sc_pairs.dict_of_lists()['scenarios']:
            session.query(Edge).filter(Edge.scenario_id==int(sid)).delete()
            session.query(Node).filter(Node.scenario_id==int(sid)).delete()
            session.query(PhaseAncestor).filter(PhaseAncestor.scenario_id==int(sid)).delete()
            session.query(Phase).filter(Phase.scenario_id==int(sid)).delete()
            session.query(Scenario).filter(Scenario.id==int(sid)).delete()

    return HTTPFound(location=request.route_url('index'))

