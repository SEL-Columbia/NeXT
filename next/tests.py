
import unittest
#from pyramid.config import Configurator
from pyramid import testing


def _initTestingDB():
    from sqlalchemy import create_engine
    from next.models import initialize_sql
    from next.models import DBSession
    initialize_sql(
        create_engine('postgresql://postgres:password@localhost/next')
        )
    return DBSession()


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


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.session = _initTestingDB()

    def tearDown(self):
        testing.tearDown()

    def _get_region(self):
        from next.models import Region
        return Region(u'New York City')

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
            self._get_region(),
            )

    def test_region(self):
        from next.models import Region
        r1 = self._get_region()
        self.session.add(r1)
        r2 = self.session.query(Region).first()
        self.assertEqual(r1.name, r2.name)

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
