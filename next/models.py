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

    def has_run(self):
        # stub for right now
        return True


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

    def to_nice_geom(self):
        from shapely.wkb import loads
        return loads(str(self.point))


class Edge(Base):
    """
    """

    __tablename__ = 'edges'

    id = Column(Integer, primary_key=True)

    from_node_id = Column(Integer, ForeignKey('nodes.id'))
    from_node = relationship(
        Node,
        primaryjoin=from_node_id == Node.id
        )

    to_node_id = Column(Integer, ForeignKey('nodes.id'))
    to_node = relationship(
        Node,
        primaryjoin=to_node_id == Node.id
        )

    weight = Column(Integer)

    def __init__(self, from_node, to_node, weight):
        self.from_node = from_node
        self.to_node = to_node
        self.weight = weight

    def __repr__(self):
        return '#<Edge from:%s to: %s>' % (self.from_node.id, self.to_node.id)

# Needed this to add the nodes table to the PostGIS geometry_table.
GeometryDDL(Node.__table__)


def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
