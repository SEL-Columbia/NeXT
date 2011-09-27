"""
Models for Next project.

Ivan Willig, Chris Natali

"""

from geoalchemy import Column
from geoalchemy import GeometryColumn
from geoalchemy import Point
from geoalchemy import GeometryDDL

from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import ForeignKey

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Scenario(Base):
    """
    """

    __tablename__ = 'scenarios'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '#<Scenario %s>' % self.name

    def get_edges(self):
        session = DBSession()
        return session.query(Edge).filter_by(scenario=self)

    def get_nodes(self):
        session = DBSession()
        return session.query(Node).filter_by(scenario=self)

    def to_geojson(self):
        bounds = self.get_bounds(srid=4326)
        return {'type': 'Feature',
                'properties': {'id': self.id},
                'geometry':
                {'type': 'LineString',
                 'coordinates': list(bounds.exterior.coords)
                 }}

    def get_bounds(self, srid=900913):
        """
        Method to find the bound box for a scenario.
        TODO, remove the hard coded sql text
        """
        from shapely.wkt import loads
        session = DBSession()
        conn = session.connection()
        sql = text(
            '''select astext(
               st_transform(st_setsrid(st_extent(point), 4326), :srid))
               from nodes where scenario_id = :sc_id''')
        rset = conn.execute(sql, srid=srid, sc_id=self.id)
        return loads(rset.fetchone()[0])

    def get_population_vs_distance(self):
        session = DBSession()
        conn = session.connection()
        sql = text(
        '''select nodes.weight, edges.distance from nodes, edges
           where edges.from_node_id = nodes.id and nodes.scenario_id = :sc_id
           order by edges.distance ''')
        rset = conn.execute(sql, sc_id=self.id).fetchall()
        return rset

    def get_partitioned_pop_vs_dist(self, num_partitions=5):
        session = DBSession()
        conn = session.connection()
        sql = text(
        '''
        select sum(weight) weight, p.distance
          from
          (select weight, e.distance
            from edges e, nodes n
            where n.node_type_id=1 and
            e.from_node_id=n.id and
            e.scenario_id = :sc_id) pop_dist,
          (select distance from generate_series(
                    (select min(distance) from edges),
                    (select max(distance) from edges),
                    (select (max(distance) - min(distance)) / :num_parts from edges))
                    as distance) p
          where pop_dist.distance <= p.distance
          group by p.distance
          order by p.distance
        ''')
        rset = conn.execute(
            sql,
            sc_id=self.id,
            num_parts=num_partitions).fetchall()
        return rset


class NodeType(Base):
    """
    A NodeType
    """

    __tablename__ = 'nodetypes'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '#<NodeType %s>' % self.name


class Node(Base):
    """
    """
    __tablename__ = 'nodes'

    id = Column(Integer, primary_key=True)

    point = GeometryColumn(
        Point(dimension=2, spatial_index=True)
        )

    weight = Column(Integer)

    node_type_id = Column(Integer, ForeignKey('nodetypes.id'))
    node_type = relationship(
        NodeType,
        primaryjoin=node_type_id == NodeType.id
        )

    scenario_id = Column(Integer, ForeignKey('scenarios.id'))
    scenario = relationship(
        Scenario,
        primaryjoin=scenario_id == Scenario.id
        )

    def __init__(self, point, weight, node_type, scenario):
        self.point = point
        self.weight = weight
        self.node_type = node_type
        self.scenario = scenario

    def __repr__(self):
        return '#<Node id: %s type: %s>' % (self.id, self.node_type.name)

    def to_geojson(self):
        from shapely.wkb import loads
        point = loads(str(self.point.geom_wkb))
        return {'type': 'Feature',
                'geometry':
                {'type': point.type,
                 'coordinates': point.coords[0]
                 },
                 'properties': {'type': self.node_type.name,
                                'id': self.id }
                }


class Edge(Base):
    """
    """

    __tablename__ = 'edges'

    id = Column(Integer, primary_key=True)

    from_node_id = Column(Integer, ForeignKey('nodes.id'))
    from_node = relationship(
        Node,
        backref='edge',
        primaryjoin=from_node_id == Node.id
        )

    to_node_id = Column(Integer, ForeignKey('nodes.id'))
    to_node = relationship(
        Node,
        primaryjoin=to_node_id == Node.id
        )

    scenario_id = Column(Integer, ForeignKey('scenarios.id'))
    scenario = relationship(
        Scenario,
        primaryjoin=scenario_id == Scenario.id
        )

    distance = Column(Integer)

    def __init__(self, scenario, from_node, to_node, distance):
        self.scenario = scenario
        self.from_node = from_node
        self.to_node = to_node
        self.distance = distance

    def __repr__(self):
        return '#<Edge from:%s to: %s>' % (self.from_node.id, self.to_node.id)

# Needed this to add the nodes table to the PostGIS geometry_table.
GeometryDDL(Node.__table__)


def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
