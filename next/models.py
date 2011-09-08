"""
"""
import transaction
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Unicode

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Region(object):

    def __init__(self, name, bbox):
        self.name = name
        self.bbox = bbox


class Edge(object):

    def __init__(self, from_node, to_node, weight):
        self.from_node = from_node
        self.to_node = to_node
        self.weight = weight


class NodeType(object):
    """
    """

    def __init__(self, name):
        self.name = name


class Node(object):
    """
    A node is a point location

    possible types

       population

       health_clinic

       water points

    """

    def __init__(self, point, weight, node_type, region):
        self.point = point
        self.weight = weight
        self.node_type = node_type
        self.region = region


def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
