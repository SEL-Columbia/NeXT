import unittest
#from pyramid.config import Configurator
from pyramid import testing
from geoalchemy import WKTSpatialElement


def _initTestingDB():
    from sqlalchemy import create_engine
    from next.models import initialize_sql
    from next.models import DBSession
    initialize_sql(
        create_engine('postgresql://postgres:password@localhost/next')
        )
    return DBSession()


def _get_scenario():
    from next.models import Scenario
    return Scenario(u'scenario1')


def _get_node_type(type=u'population'):
    from next.models import NodeType
    return NodeType(type)


class TestMyView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        _initTestingDB()

    def tearDown(self):
        testing.tearDown()

    def test_index(self):
        from next.views import index
        request = testing.DummyRequest()
        response = index(request)
        self.assertTrue(isinstance(response, dict))
        self.assertIn('scenarios', response)
        self.assertTrue(isinstance(response['scenarios'], list))


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.session = _initTestingDB()

    def tearDown(self):
        testing.tearDown()

    def _get_node(self):
        from next.models import Node
        return Node(
            WKTSpatialElement('POINT (1 1)'),
            100,
            _get_node_type(),
            _get_scenario(),
            )

    def test_scenario(self):
        s1 = _get_scenario()
        self.session.add(s1)

    def test_node_type(self):
        from next.models import NodeType
        _type = NodeType(u'population')
        self.session.add(_type)

    def test_node(self):
        n1 = self._get_node()
        self.session.add(n1)


class TestNearestNeighbor(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.session = _initTestingDB()

    def tearDown(self):
        testing.tearDown()

    def _get_data(self, scenario):
        from next.models import Node

        pop1 = Node(
            WKTSpatialElement('POINT (1 1)'),
            1,
            _get_node_type(),
            scenario)

        fac_1 = Node(
            WKTSpatialElement('POINT (1 3)'),
            1,
            _get_node_type('facility'),
            scenario)

        fac_2 = Node(
            WKTSpatialElement('POINT (1 10)'),
            1,
            _get_node_type('facility'),
            scenario)

        return pop1, fac_1, fac_2

    def test_simple_case(self):
        from next.nn import generate_nearest_neighbor
        from next.models import Edge, Scenario
        sc = Scenario(u'simple case')
        pop1, fac_1, fac_2 = self._get_data(sc)
        self.session.add_all([sc, pop1, fac_1, fac_2])
        self.session.flush()

        edges = generate_nearest_neighbor(
            sc,
            [pop1],
            [fac_1, fac_2])

        self.assertTrue(isinstance(edges, list))
        self.assertTrue(isinstance(edges[0], Edge))
        self.assertEqual(edges[0].from_node, pop1)
        self.assertEqual(edges[0].to_node, fac_1)

    def test_quad_tree(self):
        from next.nn_qt import generate_nearest_neighbor
        from next.models import Edge, Scenario
        sc = Scenario(u'quad test')
        pop1, fac_1, fac_2 = self._get_data(sc)

        self.session.add_all([sc, pop1, fac_1, fac_2])
        self.session.flush()

        edges = generate_nearest_neighbor(
            sc,
            [pop1],
            [fac_1, fac_2])

        self.assertTrue(isinstance(edges, list))
        self.assertTrue(isinstance(edges[0], Edge))
        self.assertEqual(edges[0].from_node, pop1)
        self.assertEqual(edges[0].to_node, fac_1)
