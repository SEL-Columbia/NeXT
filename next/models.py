"""
Models for Next project.

Ivan Willig, Chris Natali

"""

import logging
from geoalchemy import Column
from geoalchemy import GeometryColumn
from geoalchemy import Point
from geoalchemy import GeometryDDL
from geoalchemy import WKTSpatialElement

from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import ForeignKey

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
from sqlalchemy.sql import func
from zope.sqlalchemy import ZopeTransactionExtension
import shapely

logger = logging.getLogger(__name__)
DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


def get_node_type(type):
    session = DBSession()
    return session.query(NodeType).filter_by(name=unicode(type)).first()


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

    def get_total_demand(self):
        """
        select sum(nodes.weight) from nodes where ...
        """
        session = DBSession()
        total = session.query(func.sum(Node.weight))\
            .filter_by(scenario=self)\
            .filter_by(node_type=get_node_type('demand'))
        # Check whether we have results
        if(total.count() > 0):
            return float(total[0][0])
        else:
            return 0.0

    def get_total_demand_within(self, d):
        """
        """
        session = DBSession()
        total = session.query(func.sum(Node.weight)).join(
            Edge, Node.id == Edge.from_node_id)\
            .filter(Node.scenario_id == self.id)\
            .filter(Edge.distance <= d)\
            .filter(Node.node_type == get_node_type('demand'))
        #Check whether we have results
        if(total.count() > 0 and (total[0][0] != None)):
            #print total
            return float(total[0][0])
        else:
            return 0.0


    def get_percent_within(self, d):
        total = self.get_total_demand()
        subset = self.get_total_demand_within(d)
        return subset / total


    def to_geojson(self):
        bounds = self.get_bounds(srid=4326)
        coords = []
        if (bounds):
            if (isinstance(bounds, shapely.geometry.point.Point)):
                coords = bounds.bounds
            else:
                coords = list(bounds.exterior.coords)

        return {'type': 'Feature',
                'properties': {'id': self.id, 'name': self.name},
                'geometry':
                {'type': 'LineString',
                 'coordinates': coords
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
            '''select st_astext(
               st_transform(st_setsrid(st_extent(point), 4326), :srid))
               from nodes where scenario_id = :sc_id''')
        #TODO:  Handle case where no nodes in scenario
        rset = conn.execute(sql, srid=srid, sc_id=self.id)
        if (rset.rowcount > 0):
            rset1 = rset.fetchone()[0]
            if(rset1):
                return loads(rset1)

        return None

    def get_demand_vs_distance(self, num_partitions=5):
        session = DBSession()
        conn = session.connection()
        sql = text(
        '''
        select * from density_over_dist(:sc_id, :num_parts)
        ''')

        rset = conn.execute(
                sql, 
                sc_id=self.id,
                num_parts=num_partitions)
        return rset


    def get_partitioned_demand_vs_dist(self, num_partitions=5):
        # This function is only valid when there are edges
        # and the distance between the max/min is > 0
        session = DBSession()
        conn = session.connection()
        sql = text(
        '''
        select * from demand_over_dist(:sc_id, :num_parts)
        ''')

        rset = conn.execute(
            sql,
            sc_id=self.id,
            num_parts=num_partitions)
        return rset
        

    def get_demand_nodes_outside_distance(self, distance):
        """
        Get the demand nodes that are further than distance from their associated supply.
        """
        session = DBSession()
        demand_nodes = session.query(Node).join(
            Edge, Node.id == Edge.from_node_id)\
            .filter(Node.scenario_id == self.id)\
            .filter(Edge.distance > distance)\
            .filter(Node.node_type == get_node_type('demand'))

        return demand_nodes


    def locate_supply_nodes(self, distance, num_supply_nodes):
        """
        locate num_supply_nodes that cover the demand within
        distance from those supply_nodes.
        """
        demand_nodes = self.get_demand_nodes_outside_distance(distance).all()
        pts = get_coords(demand_nodes)
        km = distance / 1000.0
        from spatial_utils import cluster_r, util

        # Alter cluster_r to only send back indices of
        # points, not clusters themselves
        clusters = cluster_r.hclust(pts, km, "average")
        cluster_nodes = []
        for i in range(0, len(clusters)):
            cluster_nodes.append([])
            for j in range(0, len(clusters[i])):
                cluster_nodes[i].append(demand_nodes[clusters[i][j]])
            
        centroids = []
        for cluster in cluster_nodes:
            pts = get_coords(cluster)
            unzipped = zip(*pts)
            pt = util.points_to_centroid(unzipped)
            weights = map(lambda x: x.weight, cluster)
            weight = sum(weights)
            geom = WKTSpatialElement('POINT(%s %s)' % (pt[0], pt[1]))
            node = Node(geom, weight, get_node_type('supply'), self)
            centroids.append(node)

        centroids.sort(key=lambda x: x.weight, reverse=True)

        k_clusts = []
        if num_supply_nodes > len(centroids):
            k_clusts = centroids
        else:
            k_clusts = centroids[0:num_supply_nodes]

        return k_clusts
        

    def create_edges(self):
        """
        Clear out any existing edges and run nearest neighbor to
        associate demand nodes with their nearest supply.
        """
        session = DBSession()
        conn = session.connection()
        sql = text(
        '''
        select run_near_neigh(:sc_id);
        ''')

        rset = conn.execute(
            sql,
            sc_id=self.id)
        
    
    def create_nodes(self, points, type_string):
        """
        Create a list of nodes from the list of points
        """
        session = DBSession()
        node_type = get_node_type(type_string)
        new_nodes = []
        for pt in points:
            geom = WKTSpatialElement('POINT(%s %s)' % (pt[0], pt[1]))
            node = Node(geom, 1, node_type, self)
            new_nodes.append(node)

        session.add_all(new_nodes)
                                     
    
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
                 'properties': {'id': self.id, 
                                'type': self.node_type.name,
                                'weight': self.weight }
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


def get_coords(nodes):
    """ 
    Get array of coordinates from the list of nodes
    """
    
    #Not sure why lambda function from within map scope
    #cannot see session.  This inner function is a workaround.
    def get_coord_fun(sesh):
        return lambda pt_node: pt_node.point.coords(sesh)

    coord_fun = get_coord_fun(DBSession)
    return map(coord_fun, nodes)


# Needed this to add the nodes table to the PostGIS geometry_table.
GeometryDDL(Node.__table__)


def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
