"""
Models for Next project.

Ivan Willig, Chris Natali

"""

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

    def get_total_population(self):
        """
        select sum(nodes.weight) from nodes where ...
        """
        session = DBSession()
        total = session.query(func.sum(Node.weight))\
            .filter_by(scenario=self)\
            .filter_by(node_type=get_node_type('population'))
        # Check whether we have results
        if(total.count() > 0):
            return float(total[0][0])
        else:
            return 0.0

    def get_total_population_within(self, d):
        """
        """
        session = DBSession()
        total = session.query(func.sum(Node.weight)).join(
            Edge, Node.id == Edge.from_node_id)\
            .filter(Node.scenario_id == self.id)\
            .filter(Edge.distance <= d)\
            .filter(Node.node_type == get_node_type('population'))
        #print '------------------------------'
        #Check whether we have results
        if(total.count() > 0):
            #print total
            return float(total[0][0])
        else:
            return 0.0


    def get_percent_within(self, d):
        total = self.get_total_population()
        subset = self.get_total_population_within(d)
        return subset / total

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
            '''select st_astext(
               st_transform(st_setsrid(st_extent(point), 4326), :srid))
               from nodes where scenario_id = :sc_id''')
        #TODO:  Handle case where no nodes in scenario
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
        # This function is only valid when there are edges
        # and the distance between the max/min is > 0
        session = DBSession()
        ct = session.query(func.count(Edge.id)).filter_by(scenario=self).first()
        if(ct[0] == 0):
            return []
        
        conn = session.connection()
        sql = text(
        '''
        select max(distance) - min(distance) from edges where scenario_id = :sc_id
        ''')
        dist_diff = conn.execute(sql, sc_id=self.id).first()

        if(dist_diff[0] <= 0):
            return []

        sql = text(
        '''
        select 
          (sum(cast(weight as float)) / 
          (select sum(weight) from nodes 
            where scenario_id = :sc_id and node_type_id=1)) weight,
          p.distance
          from 
          (select weight, e.distance 
            from edges e, nodes n 
            where n.node_type_id=1 and 
            e.from_node_id=n.id and
            e.scenario_id = :sc_id) pop_dist,
          (select distance from generate_series(
                    (select min(distance) from edges 
                     where scenario_id = :sc_id),
                    (select max(distance) from edges 
                     where scenario_id = :sc_id),
                    (select (max(distance) - min(distance)) / 
                     :num_parts from edges 
                     where scenario_id = :sc_id)) 
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

        
    def get_pop_nodes_outside_distance(self, distance):
        """
        Get the population nodes that are further than distance from their associated facility.
        """
        session = DBSession()
        pop_nodes = session.query(Node).join(
            Edge, Node.id == Edge.from_node_id)\
            .filter(Node.scenario_id == self.id)\
            .filter(Edge.distance > distance)\
            .filter(Node.node_type == get_node_type('population'))

        return pop_nodes


    def locate_facilities(self, distance, num_facilities):
        """
        locate num_facilities that cover the population within
        distance from those facilities.
        """
        pop_nodes = self.get_pop_nodes_outside_distance(distance).all()
        pts = get_coords(pop_nodes)
        km = distance / 1000.0
        from spatial_utils import cluster_r, util
        clusters = cluster_r.hclust(pts, km, "average")
        clusters.sort(key=len, reverse=True)
        k_clusts = []
        if num_facilities > len(clusters):
            k_clusts = clusters
        else:
            k_clusts = clusters[0:num_facilities]
            
        centroids = []
        for cluster in k_clusts:
            unzipped = zip(*cluster)
            centroids.append(util.points_to_centroid(unzipped))

        return centroids
        

    def create_edges(self):
        """
        Clear out any existing edges and run nearest neighbor to
        associate population nodes with their nearest facility.
        """
        session = DBSession()
        pop_type = get_node_type('population')
        fac_type = get_node_type('facility')
        nodes = session.query(Node).filter_by(scenario=self)
        pop_nodes = nodes.filter_by(node_type=pop_type)
        fac_nodes = nodes.filter_by(node_type=fac_type)

        old_edges = session.query(Edge).filter_by(scenario=self)
        [session.delete(edge) for edge in old_edges]

        import nn_qt
        edges = nn_qt.generate_nearest_neighbor(self, pop_nodes, fac_nodes)
        session.add_all(edges)

    
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
