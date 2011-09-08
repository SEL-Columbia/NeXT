"""
"""
import transaction

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


class Region(Base):
    """
    """

    __tablename__ = 'regions'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '#<Region %s>' % self.name


class NodeType(Base):
    """
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
    point = GeometryColumn(Point(2))
    weight = Column(Integer)

    node_type_id = Column(Integer, ForeignKey('nodetypes.id'))
    node_type = relationship(
        NodeType,
        primaryjoin=node_type_id == NodeType.id
        )

    region_id = Column(Integer, ForeignKey('regions.id'))
    region = relationship(
        Region,
        primaryjoin=region_id == Region.id
        )

    def __init__(self, point, weight, node_type, region):
        self.point = point
        self.weight = weight
        self.node_type = node_type
        self.region = region

    def __repr__(self):
        return '#<Node %s>' % self.id


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
        return '#<Edge %s>' % self.id

GeometryDDL(Node.__table__)


def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
