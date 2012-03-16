import unittest
#from pyramid.config import Configurator
from pyramid import testing
from next.models import Scenario, Node, Edge, NodeType, get_node_type
from geoalchemy import WKTSpatialElement
import simplejson

def _initTestingDB():
    from sqlalchemy import create_engine
    from next.models import initialize_sql
    from next.models import DBSession
    initialize_sql(
        create_engine('postgresql://postgres:password@localhost/next_testing')
        )
    return DBSession()


def _initTestData(session):
    # Initialize Scenario with 2 pop nodes and 2 facilities
    # Assumes Reference Data (i.e. NodeTypes) are loaded
    
    scenario = Scenario("Test")
    session.add(scenario)
    # session.flush()

    fac1 = Node(
               WKTSpatialElement('POINT (0 0)'),
               1,
               get_node_type('facility'), 
               scenario
           )

    fac2 = Node(
               WKTSpatialElement('POINT (-1 -1)'),
               1,
               get_node_type('facility'), 
               scenario
           )

    hh1  = Node(
               WKTSpatialElement('POINT (1 1)'),
               1,
               get_node_type('population'), 
               scenario
           )

    hh2  = Node(
               WKTSpatialElement('POINT (-2 -2)'),
               1,
               get_node_type('population'), 
               scenario
           )

    session.add(fac1)
    session.add(fac2)
    session.add(hh1)
    session.add(hh2)
    session.flush()

class TestMyView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.session = _initTestingDB()
        self.connection = self.session.connection()
        self.trans = self.connection.begin()
        # many of the views call show-scenario 
        # Not sure why __init__ is not called
        # to load all of these
        self.config.add_route('show-scenario', '/scenario/{id}')
        _initTestData(self.session)

    def tearDown(self):
        self.trans.rollback()
        # self.session.rollback()
        self.session.close()
        testing.tearDown()

    def helper_get_nodes(self, scenario_id, node_type=None):
        " Helper to get nodes of type from scenario "
        from next.views import show_nodes
        request = testing.DummyRequest()
        params = {'id': scenario_id}
        if (node_type):
            request.GET = {'type': node_type}
            
        request.matchdict = params
        response = show_nodes(request)
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
       

    def test_create_scenario(self):
        from next.views import create_scenario
        import StringIO
        import cgi
        dbapi_conn = self.session.connection().connection

        fac_csv = '''0.0,0.0'''
        pop_csv = '''
        1.0,1.0
        -1.0,-1.0'''

        fac_strm = StringIO.StringIO(fac_csv)
        pop_strm = StringIO.StringIO(pop_csv)
        fac_fs = cgi.FieldStorage()
        pop_fs = cgi.FieldStorage()
        fac_fs.filename = 'fac.csv'
        fac_fs.file = fac_strm
        pop_fs.filename = 'pop.csv'
        pop_fs.file = pop_strm


        post_vars = {'name': "Test2", 'pop-csv': pop_fs, 'fac-csv': fac_fs}
        request = testing.DummyRequest(post=post_vars)
        request.registry = self.config.registry
        # set the temp folder
        request.registry.settings['next.temporary_folder'] = '/tmp'
        response = create_scenario(request)

        # ensure that we have a scenario named Test2 
        sc2 = self.session.query(Scenario).filter(Scenario.name == "Test2").first()
        self.assertTrue(sc2.name == "Test2")
        
        # ensure that we've added 3 nodes
        self.assertEqual(3, sc2.get_nodes().count())



    def test_run_scenario(self):
        from next.views import run_scenario
        sc1 = self.session.query(Scenario).filter(Scenario.name == "Test").first()
        params = {'id': sc1.id}
        request = testing.DummyRequest()
        request.matchdict = params
        response = run_scenario(request)
        # ensure that hh's are assoc'd with correct fac's
        hh1 = self.session.query(Node).filter(Node.point.x == 1.0).first()
        hh2 = self.session.query(Node).filter(Node.point.x == -2.0).first()

        fac1 = self.session.query(Node).\
          filter(Edge.to_node_id == Node.id).\
          filter(Edge.from_node_id == hh1.id).first()
       
        fac2 = self.session.query(Node).\
          filter(Edge.to_node_id == Node.id).\
          filter(Edge.from_node_id == hh2.id).first()
        
        fac1_coords = fac1.point.coords(self.session)
        fac2_coords = fac2.point.coords(self.session)
        self.assertTrue(fac1_coords[0] == 0.0 and fac1_coords[1] == 0.0)
        self.assertTrue(fac2_coords[0] == -1.0 and fac2_coords[1] == -1.0)



    def test_show_nodes(self):
        from next.views import show_nodes, run_scenario
        sc1 = self.session.query(Scenario).filter(Scenario.name == "Test").first()
        params = {'id': sc1.id}
        #test getting all nodes
        request = testing.DummyRequest()
        request.matchdict = params
        response = show_nodes(request)
        feature_coll = simplejson.loads(response.body)
        features = feature_coll['features']
        self.assertEqual(4, len(features))
        #test getting the population nodes
        #need to run_scenario first to generate edges
        response = run_scenario(request)

        get_params = {'type': "population"}
        request = testing.DummyRequest(params=get_params)
        request.matchdict = params
        response = show_nodes(request)
        feature_coll = simplejson.loads(response.body)
        features = feature_coll['features']
        self.assertEqual(2, len(features))
        feature = features[0]
        coords = feature['geometry']['coordinates']
        self.assertTrue(([1, 1] == coords) or ([-2, -2] == coords))
        self.assertEqual("population", feature['properties']['type'])
        

    def test_graph_scenario(self):
        from next.views import graph_scenario, run_scenario
        sc1 = self.session.query(Scenario).filter(Scenario.name == "Test").first()
        request = testing.DummyRequest()
        params = {'id': sc1.id}
        request.matchdict = params
        #create the edges
        run_scenario(request)
        response = graph_scenario(request)
        pairs = simplejson.loads(response.body)
        #TODO Elaborate this test (add data and check calc)
        pair = pairs[0]
        sum_of_density = sum(map(lambda x: x[1], pairs))
        self.assertTrue(sum_of_density < 1)
        self.assertTrue(pair[1] < 1)
        self.assertEqual(1, len(pairs))


    def test_graph_scenario_cumul(self):
        from next.views import graph_scenario_cumul, run_scenario
        sc1 = self.session.query(Scenario).filter(Scenario.name == "Test").first()
        request = testing.DummyRequest()
        params = {'id': sc1.id}
        request.matchdict = params
        #create the edges
        run_scenario(request)
        response = graph_scenario_cumul(request)
        pairs = simplejson.loads(response.body)
        #TODO Elaborate this test (add data and check calc)
        # import pdb; pdb.set_trace()
        pair = pairs[0]
        self.assertTrue(pair[1] < 1)
        self.assertEqual(1, len(pairs))

    def test_find_pop_with(self):
        from next.views import find_pop_with, run_scenario
        sc1 = self.session.query(Scenario).filter(Scenario.name == "Test").first()
        request = testing.DummyRequest()
        params = {'id': sc1.id}
        request.matchdict = params
        #create the edges
        run_scenario(request)
        request.json_body = {'d': 1000} 
        response = find_pop_with(request)
        total = simplejson.loads(response.body)
        self.assertEqual(0, total['total'])

    def test_create_facilities(self):
        from next.views import create_facilities, run_scenario
        sc1 = self.session.query(Scenario).filter(Scenario.name == "Test").first()
        request = testing.DummyRequest()
        params = {'id': sc1.id}
        request.matchdict = params
        #create the edges
        run_scenario(request)

        request.json_body = {'d': 1000, 'n': 10} 
        response = create_facilities(request)
        #ensure that we have two new facility nodes
        pop_nodes = self.helper_get_nodes(sc1.id, "facility") 
        self.assertEqual(4, len(pop_nodes['features']))
        
    def test_add_nodes(self):
        from next.views import add_nodes
        sc1 = self.session.query(Scenario).filter(Scenario.name == "Test").first()
        request = testing.DummyRequest()
        params = {'id': sc1.id}
        request.matchdict = params

        nodes = {'features':
                  [
                      {
                      'geometry': {
                          'coordinates': [10.0, 10.0]
                          },
                      'properties': {
                          'type': 'population',
                          'weight': 3
                          }
                      },
                      {
                      'geometry': {
                          'coordinates': [20.0, 20.0]
                          },
                      'properties': {
                          'type': 'facility',
                          'weight': 3
                          }
                      }
                 ]
               }
                      
        request.json_body = nodes 
        response = add_nodes(request)
        #ensure that we have two new nodes (6 total)
        nodes = self.helper_get_nodes(sc1.id) 
        self.assertEqual(6, len(nodes['features']))


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.session = _initTestingDB()

    def tearDown(self):
        self.session.rollback()
        self.session.close()
        testing.tearDown()

    def _get_scenario(self):
        from next.models import Scenario
        return Scenario(u'scenario1')

    def _get_node_type(self):
        from next.models import NodeType
        return NodeType(u'population')

    def _get_node(self):
        from next.models import Node
        from geoalchemy import WKTSpatialElement
        return Node(
            WKTSpatialElement('POINT (1 1)'),
            100,
            self._get_node_type(),
            self._get_scenario(),
            )

    def test_scenario(self):
        from next.models import Scenario
        s1 = self._get_scenario()
        self.session.add(s1)
        s2 = self.session.query(Scenario).first()
        self.assertEqual(s1.name, s2.name)

    def test_node_type(self):
        from next.models import NodeType
        _type = NodeType(u'population')
        self.session.add(_type)

    def test_node(self):
        from next.models import Node
        n1 = self._get_node()
        self.session.add(n1)
        n2 = self.session.query(Node).first()
        self.assertEqual(n1, n2)
        

if __name__ == '__main__':
    unittest.main()
