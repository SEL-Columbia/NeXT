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
from sqlalchemy.orm import relation
from sqlalchemy.sql import select, text
from sqlalchemy.sql import func
from geoalchemy2.shape import to_shape
from zope.sqlalchemy import ZopeTransactionExtension
import shapely
from next.model import Base
from next.model import DBSession 

BASE_SRID = 4326

logger = logging.getLogger(__name__)

def get_node_type(node_type):
    session = DBSession()
    return session.query(NodeType).filter_by(name=unicode(node_type)).first()

class NodeType(Base):

    __tablename__ = 'nodetypes'
    __table_args__ = {'autoload': True}

    def __init__(self, name):
        self.name = name


class Scenario(Base):

    __tablename__ = 'scenarios'
    __table_args__ = {'autoload': True}

    phases = relationship("Phase")

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '#<Scenario %s>' % self.name

    def get_bounds(self, srid=900913):
        """
        Method to find the bound box for a scenario.
        TODO, remove the hard coded sql text
        """
        from shapely.wkt import loads
        session = DBSession()
        conn = session.connection()
        expr = select([func.ST_Transform(
                         func.ST_SetSrid(
                           func.ST_Extent(Node.point), 
                         BASE_SRID), 
                       srid)]).\
               where(Node.scenario_id == self.id)
        result = conn.execute(expr)
        shp = None
        if (result.rowcount > 0):
            wkb = result.first()[0]
            if(wkb is not None):
                shp = to_shape(wkb)
        # leave it open, as it's from the pool...conn.close()
        result.close()
        return shp


#        sql = text(
#            '''select st_astext(
#               st_transform(st_setsrid(st_extent(point), 4326), :srid))
#               from nodes where scenario_id = :sc_id''')
#        #TODO:  Handle case where no nodes in scenario
#        rset = conn.execute(sql, srid=srid, sc_id=self.id)
#        if (rset.rowcount > 0):
#            rset1 = rset.fetchone()[0]
#            if(rset1):
#                return loads(rset1)
#
#        return None
    

    def get_root_phase(self):
        session = DBSession()
        phase = session.query(Phase).\
                filter((Phase.scenario_id == self.id) & (Phase.id == 1)).first()
        return phase


    def to_geojson(self):
        bounds = self.get_bounds(srid=4326)
        coords = []
        if (bounds):
            if (isinstance(bounds, shapely.geometry.point.Point)):
                coords = bounds.bounds
            else:
                coords = list(bounds.exterior.coords)

        return  {'type': 'Feature',
                'properties': {'id': self.id, 'name': self.name},
                'geometry':
                {'type': 'LineString',
                 'coordinates': coords
                 }}

    def get_phases_geojson(self):
        phase_dict = {}
        root = None
        for phase in self.phases:
            phase_dict[phase.id] = phase.to_geojson()

        for phase in self.phases:
            parent = None
            if(phase_dict.has_key(phase.parent_id)):
                parent = phase_dict[phase.parent_id]
            if(parent):
                child = phase_dict[phase.id]
                parent['properties']['children'].append(child)
            else:
                #we found the root
                root = phase_dict[phase.id]

        return root

    def get_phases_tree(self):
        phase_dict = {}
        root = None
        for phase in self.phases:
            phase_dict[phase.id] = {'id': phase.id, 'children': []}

        for phase in self.phases:
            parent = None
            if(phase_dict.has_key(phase.parent_id)):
                parent = phase_dict[phase.parent_id]
            if(parent):
                child = phase_dict[phase.id]
                parent['children'].append(child)
            else:
                #we found the root
                root = phase_dict[phase.id]

        return root

class Phase(Base):

    __tablename__ = 'phases'
    __table_args__ = {'autoload': True}

    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), primary_key=True) 
    scenario = relationship("Scenario")
    parent = relationship("Phase", remote_side=[id, scenario_id])

    """
    ancestors = relationship("Phase", 
        secondary = "phase_ancestors",
        primaryjoin = "(Phase.scenario_id == PhaseAncestor.scenario_id) &\
                       (Phase.id == PhaseAncestor.phase_id)",
        secondaryjoin = "(Phase.scenario_id == PhaseAncestor.scenario_id) &\
                         (Phase.id == PhaseAncestor.phase_id)")
    """


    def __init__(self, scenario, parent=None, name=None):
        self.scenario = scenario
        self.parent = parent
        self.name = name


        

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
               from nodes, phase_ancestors where 
               phase_ancestors.scenario_id = :sc_id and
               phase_ancestors.phase_id = :phase_id and
               nodes.phase_id = phase_ancestors.ancestor_phase_id and
               nodes.scenario_id = phase_ancestors.scenario_id''')
        #TODO:  Handle case where no nodes in scenario
        rset = conn.execute(sql, srid=srid, sc_id=self.scenario_id, phase_id=self.id)
        if (rset.rowcount > 0):
            rset1 = rset.fetchone()[0]
            if(rset1):
                return loads(rset1)

        return None
    

    def to_geojson(self):
        bounds = self.get_bounds(srid=4326)
        coords = []
        if (bounds):
            if (isinstance(bounds, shapely.geometry.point.Point)):
                coords = bounds.bounds
            else:
                coords = list(bounds.exterior.coords)

        return {'type': 'Feature',
                'properties': {'id': self.id, 'name': self.name, 'children': []},
                'geometry':
                {'type': 'LineString',
                 'coordinates': coords
                 }}


    def create_edges(self):
        """
        Clear out any existing edges and run nearest neighbor to
        associate demand nodes with their nearest supply.
        """
        session = DBSession()
        conn = session.connection()
        sql = text(
        '''
        select run_near_neigh(:sc_id, :phase_id);
        ''')

        rset = conn.execute(
            sql,
            sc_id=self.scenario_id,
            phase_id=self.id)


    def get_demand_vs_distance(self, num_partitions=5):
        session = DBSession()
        conn = session.connection()
        sql = text(
        '''
        select * from density_over_dist(:sc_id, :phase_id, :num_parts)
        ''')

        rset = conn.execute(
                sql, 
                sc_id=self.scenario_id,
                phase_id=self.id,
                num_parts=num_partitions)
        return rset


    def get_partitioned_demand_vs_dist(self, num_partitions=5):
        # This function is only valid when there are edges
        # and the distance between the max/min is > 0
        session = DBSession()
        conn = session.connection()
        sql = text(
        '''
        select * from demand_over_dist(:sc_id, :phase_id, :num_parts)
        ''')

        rset = conn.execute(
            sql,
            sc_id=self.scenario_id,
            phase_id=self.id,
            num_parts=num_partitions)
        return rset
        

    def get_demand_nodes_outside_distance(self, distance):
        """
        Get the demand nodes that are further than distance from their associated supply.
        """

        qu = get_cumulative_nodes(self.scenario_id, self.id, node_type='demand')
        qu = qu.join(Edge, Node.id == Edge.from_node_id)\
            .filter(Edge.distance > distance)

        return qu


    def get_total_demand(self):
        """
        select sum(nodes.weight) from nodes where ...
        """

        total = get_cumulative_nodes(self.scenario_id, self.id, cls_or_fun=func.sum(Node.weight), node_type='demand')
        # Check whether we have results
        if(total.count() > 0):
            return float(total[0][0])
        else:
            return 0.0


    def get_total_demand_within(self, distance):
        """
        """
        q = get_cumulative_nodes(self.scenario_id, self.id, cls_or_fun=func.sum(Node.weight), node_type='demand')
        total = q.join(Edge, Node.id == Edge.from_node_id)\
                .filter((Edge.scenario_id == self.scenario_id) & 
                        (Edge.phase_id == self.id) & 
                        (Edge.distance <= distance))

        #Check whether we have results
        if(total.count() > 0 and (total[0][0] != None)):
            #print total
            return float(total[0][0])
        else:
            return 0.0


    def get_percent_within(self, distance):
        total = self.get_total_demand()
        subset = self.get_total_demand_within(distance)
        return subset / total
    

    def create_nodes(self, points, type_string):
        """
        Create a list of nodes from the list of points
        """
        #TODO:  Take weight from points?
        session = DBSession()
        node_type = get_node_type(type_string)
        new_nodes = []
        for pt in points:
            geom = WKTSpatialElement('POINT(%s %s)' % (pt[0], pt[1]))
            node = Node(geom, 1, node_type, self)
            new_nodes.append(node)

        session.add_all(new_nodes)
        

    def locate_supply_nodes(self, distance, num_supply_nodes):
        """
        locate num_supply_nodes that cover the demand within
        distance from those supply_nodes.
        """
        nodes = self.get_demand_nodes_outside_distance(distance).all()
        pts = get_coords(nodes)
        km = distance / 1000.0
        from spatial_utils import cluster_r, util

        # Alter cluster_r to only send back indices of
        # points, not clusters themselves
        clusters = cluster_r.hclust(pts, km, "average")
        cluster_nodes = []
        for i in range(0, len(clusters)):
            cluster_nodes.append([])
            for j in range(0, len(clusters[i])):
                cluster_nodes[i].append(nodes[clusters[i][j]])
            
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


class PhaseAncestor(Base):

    __tablename__ = 'phase_ancestors'
    __table_args__ = ({'autoload': True})
    phase = relationship("Phase", 
             primaryjoin = "(PhaseAncestor.scenario_id == Phase.scenario_id) &\
                            (PhaseAncestor.phase_id == Phase.id)")
    ancestor = relationship("Phase", 
             primaryjoin = "(PhaseAncestor.scenario_id == Phase.scenario_id) &\
                            (PhaseAncestor.ancestor_phase_id == Phase.id)")


class Node(Base):

    __tablename__ = 'nodes'
    __table_args__ = {'autoload': True}

    point = GeometryColumn(
            Point(dimension=2, spatial_index=True)
            )

    node_type = relationship("NodeType")
    
    scenario = relationship(Scenario)
    phase = relationship(Phase)

    def __init__(self, point, weight, node_type, phase):
        self.point = point
        self.weight = weight
        self.node_type = node_type
        self.phase = phase 

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
    """
    ancestors = relationship("PhaseAncestor", 
        primaryjoin = "(Node.scenario_id == PhaseAncestor.scenario_id) &\
                       (Node.phase_id == PhaseAncestor.ancestor_phase_id)")
    """


class Edge(Base):

    __tablename__ = 'edges'
    __table_args__ = {'autoload': True}


def get_cumulative_nodes(scenario_id, phase_id, cls_or_fun=Node, node_type=None):
    session = DBSession()
    q = session.query(cls_or_fun).\
            join(Phase).\
            join(PhaseAncestor,
                 (Phase.id == PhaseAncestor.ancestor_phase_id) &\
                 (Phase.scenario_id == PhaseAncestor.scenario_id)).\
            filter((PhaseAncestor.scenario_id == scenario_id) &\
                   (PhaseAncestor.phase_id == phase_id))

    if(node_type):
        q = q.join(NodeType).filter(NodeType.name == node_type)

    return q


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

GeometryDDL(Node.__table__)
