import unittest
#from pyramid.config import Configurator
from pyramid import testing
from geoalchemy import WKTSpatialElement
import simplejson

from sqlalchemy import create_engine
from next import initialize_sql, DBSession
initialize_sql(
    create_engine('postgresql://postgres:password@localhost/next_testing')
)

from next.models import Scenario, Phase, Node, Edge, NodeType, get_node_type

def _initTestData(session):
    # Initialize Scenario with 2 demand nodes and 2 supply_nodes
    # Assumes Reference Data (i.e. NodeTypes) are loaded
    
    scenario = Scenario("Test")
    session.add(scenario)
    session.flush()
    phase1 = Phase(scenario)
    session.flush()
    # add a 2nd phase to test against
    phase2 = Phase(scenario, phase1)
    session.flush()

    supply1 = Node(
               WKTSpatialElement('POINT (0 0)'),
               1,
               get_node_type('supply'), 
               phase1
           )

    supply2 = Node(
               WKTSpatialElement('POINT (-1 -1)'),
               1,
               get_node_type('supply'), 
               phase1
           )

    hh1  = Node(
               WKTSpatialElement('POINT (1 1)'),
               1,
               get_node_type('demand'), 
               phase1
           )

    # hh2 is added to phase2
    hh2  = Node(
               WKTSpatialElement('POINT (-2 -2)'),
               1,
               get_node_type('demand'), 
               phase2
           )

    session.add(supply1)
    session.add(supply2)
    session.add(hh1)
    session.add(hh2)
    session.flush()
    

class TestMyView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.session = DBSession()
        self.connection = self.session.connection()
        self.trans = self.connection.begin()
        # many of the views call show-phase
        # Not sure why __init__ is not called
        # to load all of the routes
        self.config.add_route('show-phase', '/scenario/{id}/phases/{phase_id}')
        _initTestData(self.session)

    def tearDown(self):
        self.trans.rollback()
        # self.session.rollback()
        self.session.close()
        testing.tearDown()

    def helper_get_phase_nodes(self, scenario_id, phase_id, node_type=None):
        " Helper to get nodes of type from scenario "
        from next.views import show_phase_nodes
        request = testing.DummyRequest()
        params = {'id': scenario_id, 'phase_id': phase_id}
        if (node_type):
            request.GET = {'type': node_type}
            
        request.matchdict = params
        response = show_phase_nodes(request)
        return simplejson.loads(response.body)

    def test_index(self):
        from next.views import index
        request = testing.DummyRequest()
        response = index(request)
        self.assertTrue(isinstance(response, dict))

    def test_show_all(self):
        from next.views import show_all
        request = testing.DummyRequest()
        response = show_all(request)
        feature_coll = simplejson.loads(response.body)
        features = feature_coll['features']
        self.assertEqual(1, len(features))
        feature = features[0]
        coords = feature['geometry']['coordinates']
        test_coords = [[-2.0, -2.0], [-2.0, 1.0], [1.0, 1.0], [1.0, -2.0], [-2.0, -2.0]]
        self.assertEqual(test_coords, coords)
        name = feature['properties']['name']
        self.assertEqual("Test", name)

    def test_show_phases(self):
        from next.views import show_phases
        request = testing.DummyRequest()
        sc1 = self.session.query(Scenario).filter(Scenario.name == "Test").first()
        params = {'id': sc1.id}
        request.matchdict = params
        response = show_phases(request)
        feature_coll = simplejson.loads(response.body)
        features = feature_coll['features']
        # ensure that we have 1 parent with appropriate coords and 1 child phase
        props = features['properties']
        self.assertEqual(1, props['id'])
        coords = features['geometry']['coordinates']
        test_coords = [[-1.0, -1.0], [-1.0, 1.0], [1.0, 1.0], [1.0, -1.0], [-1.0, -1.0]]
        self.assertEqual(test_coords, coords)
        children = props['children'] 
        self.assertEqual(1, len(children))
        child = children[0]
        test_coords2 = [[-2.0, -2.0], [-2.0, 1.0], [1.0, 1.0], [1.0, -2.0], [-2.0, -2.0]]
        coords2 = child['geometry']['coordinates']
        self.assertEqual(test_coords2, coords2)
       

    def test_create_scenario(self):
        from next.views import create_scenario
        import StringIO
        import cgi
        dbapi_conn = self.session.connection().connection

        supply_csv = "0.0,0.0"
        demand_csv = "1.0,1.0\n-1.0,-1.0"

        supply_strm = StringIO.StringIO(supply_csv)
        demand_strm = StringIO.StringIO(demand_csv)
        supply_fs = cgi.FieldStorage()
        demand_fs = cgi.FieldStorage()
        supply_fs.filename = 'supply.csv'
        supply_fs.file = supply_strm
        demand_fs.filename = 'demand.csv'
        demand_fs.file = demand_strm

        post_vars = {'name': "Test2", 'demand-csv': demand_fs, 'supply-csv': supply_fs}
        request = testing.DummyRequest(post=post_vars)
        request.registry = self.config.registry
        # set the temp folder
        request.registry.settings['next.temporary_folder'] = '/tmp'
        response = create_scenario(request)

        # ensure that we have a scenario named Test2 
        sc2 = self.session.query(Scenario).filter(Scenario.name == "Test2").first()
        self.assertTrue(sc2.name == "Test2")
        
        # ensure that we've added 3 nodes
        node_query = self.session.query(Node).filter(Node.scenario_id == sc2.id)
        self.assertEqual(3, node_query.count())
        
        # ensure that it has 1 root phase
        phases = sc2.get_phases_geojson()
        props = phases['properties']
        self.assertEqual(1, props['id'])
        self.assertEqual([], props['children'])


    def test_create_edges(self):
        from next.views import create_edges
        sc1 = self.session.query(Scenario).filter(Scenario.name == "Test").first()
        params = {'id': sc1.id, 'phase_id': 2}
        request = testing.DummyRequest()
        request.matchdict = params
        response = create_edges(request)
        # ensure that hh's are assoc'd with correct supply's
        hh1 = self.session.query(Node).filter(Node.point.x == 1.0).first()
        hh2 = self.session.query(Node).filter(Node.point.x == -2.0).first()

        supply1 = self.session.query(Node).\
          filter(Edge.to_node_id == Node.id).\
          filter(Edge.from_node_id == hh1.id).first()
       
        supply2 = self.session.query(Node).\
          filter(Edge.to_node_id == Node.id).\
          filter(Edge.from_node_id == hh2.id).first()
        
        supply1_coords = supply1.point.coords(self.session)
        supply2_coords = supply2.point.coords(self.session)
        self.assertTrue(supply1_coords[0] == 0.0 and supply1_coords[1] == 0.0)
        self.assertTrue(supply2_coords[0] == -1.0 and supply2_coords[1] == -1.0)



    def test_show_phase_nodes(self):
        from next.views import show_phase_nodes, create_edges
        sc1 = self.session.query(Scenario).filter(Scenario.name == "Test").first()
        params = {'id': sc1.id, 'phase_id': 2}
        #test getting all nodes
        request = testing.DummyRequest()
        request.matchdict = params
        response = show_phase_nodes(request)
        feature_coll = simplejson.loads(response.body)
        features = feature_coll['features']
        self.assertEqual(4, len(features))
        #test getting the demand nodes
        #need to create_edges first to generate edges
        response = create_edges(request)

        get_params = {'type': "demand"}
        request = testing.DummyRequest(params=get_params)
        request.matchdict = params
        response = show_phase_nodes(request)
        feature_coll = simplejson.loads(response.body)
        features = feature_coll['features']
        self.assertEqual(2, len(features))
        feature = features[0]
        coords = feature['geometry']['coordinates']
        self.assertTrue(([1, 1] == coords) or ([-2, -2] == coords))
        self.assertEqual("demand", feature['properties']['type'])
        

    def test_graph_phase(self):
        from next.views import graph_phase, create_edges
        sc1 = self.session.query(Scenario).filter(Scenario.name == "Test").first()
        request = testing.DummyRequest()
        params = {'id': sc1.id, 'phase_id': 2}
        request.matchdict = params
        #create the edges
        create_edges(request)
        response = graph_phase(request)
        pairs = simplejson.loads(response.body)
        #TODO Elaborate this test (add data and check calc)
        pair = pairs[0]
        sum_of_density = sum(map(lambda x: x[1], pairs))
        self.assertTrue(sum_of_density < 1)
        self.assertTrue(pair[1] < 1)
        self.assertEqual(1, len(pairs))


    def test_graph_phase_cumul(self):
        from next.views import graph_phase_cumul, create_edges
        sc1 = self.session.query(Scenario).filter(Scenario.name == "Test").first()
        request = testing.DummyRequest()
        params = {'id': sc1.id, 'phase_id': 2}
        request.matchdict = params
        #create the edges
        create_edges(request)
        response = graph_phase_cumul(request)
        pairs = simplejson.loads(response.body)
        #TODO Elaborate this test (add data and check calc)
        # import pdb; pdb.set_trace()
        pair = pairs[0]
        self.assertTrue(pair[1] < 1)
        self.assertEqual(1, len(pairs))


    def test_find_demand_with(self):
        from next.views import find_demand_with, create_edges
        sc1 = self.session.query(Scenario).filter(Scenario.name == "Test").first()
        request = testing.DummyRequest()
        params = {'id': sc1.id, 'phase_id': 2}
        request.matchdict = params
        #create the edges
        create_edges(request)
        request.json_body = {'d': 1000} 
        response = find_demand_with(request)
        total = simplejson.loads(response.body)
        self.assertEqual(0, total['total'])

    def test_create_supply_nodes(self):
        from next.views import create_supply_nodes, create_edges
        sc1 = self.session.query(Scenario).filter(Scenario.name == "Test").first()
        request = testing.DummyRequest()
        params = {'id': sc1.id, 'phase_id': 2}
        request.matchdict = params
        #create the edges
        create_edges(request)

        request.json_body = {'d': 1000, 'n': 10} 
        response = create_supply_nodes(request)
        #ensure that we have two new supply nodes
        demand_nodes = self.helper_get_phase_nodes(sc1.id, 3, "supply") 
        self.assertEqual(4, len(demand_nodes['features']))
        
    def test_add_nodes(self):
        from next.views import add_nodes
        sc1 = self.session.query(Scenario).filter(Scenario.name == "Test").first()
        request = testing.DummyRequest()
        params = {'id': sc1.id, 'phase_id': 2}
        request.matchdict = params

        nodes = {'features':
                  [
                      {
                      'geometry': {
                          'coordinates': [10.0, 10.0]
                          },
                      'properties': {
                          'type': 'demand',
                          'weight': 3
                          }
                      },
                      {
                      'geometry': {
                          'coordinates': [20.0, 20.0]
                          },
                      'properties': {
                          'type': 'supply',
                          'weight': 3
                          }
                      }
                 ]
               }
                      
        request.json_body = nodes 
        response = add_nodes(request)
        #ensure that we have two new nodes (6 total)
        nodes = self.helper_get_phase_nodes(sc1.id, 3) 
        self.assertEqual(6, len(nodes['features']))


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.session = DBSession()

    def tearDown(self):
        self.session.rollback()
        self.session.close()
        testing.tearDown()

    def _get_scenario(self):
        from next.models import Scenario
        return Scenario(u'scenario1')

    def _get_phase(self):
        from next.models import Phase
        return Phase(self._get_scenario())

    def _get_node_type(self):
        from next.models import NodeType
        return NodeType(u'demand')

    def _get_node(self):
        from next.models import Node
        from geoalchemy import WKTSpatialElement
        return Node(
            WKTSpatialElement('POINT (1 1)'),
            100,
            self._get_node_type(),
            self._get_phase(),
            )

    def test_scenario(self):
        from next.models import Scenario
        s1 = self._get_scenario()
        self.session.add(s1)
        s2 = self.session.query(Scenario).first()
        self.assertEqual(s1.name, s2.name)

    def test_node_type(self):
        from next.models import NodeType
        _type = NodeType(u'demand')
        self.session.add(_type)

    def test_node(self):
        from next.models import Node
        n1 = self._get_node()
        self.session.add(n1)
        n2 = self.session.query(Node).first()
        self.assertEqual(n1, n2)
        
class TestImport(unittest.TestCase):

    def test_get_import_spec(self):
        from import_helpers import get_import_spec
        import StringIO
        csv_with_hdr = "val,weight,lat,lon\n1,9,0.1,1.1\n2,7,1.1,0.1"
        csv_stream = StringIO.StringIO(csv_with_hdr)
        (xy_spec, weight_spec) = get_import_spec(csv_stream)
        self.assertEqual((3, 2), xy_spec)
        self.assertEqual({'column': 1}, weight_spec)


if __name__ == '__main__':
    unittest.main()
