import logging

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import ForeignKey


from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.orm import relation
from sqlalchemy.sql import select, text
from sqlalchemy.sql import func

from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape, from_shape

import shapely

from . import Base, DBSession

BASE_SRID = 4326

logger = logging.getLogger(__name__)

def get_node_type(node_type, session):
    return session.query(NodeType).filter_by(name=unicode(node_type)).first()

class NodeType(Base):

    __tablename__ = 'nodetypes'
    # __table_args__ = {'autoload': True}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)

    def __init__(self, name):
        self.name = name


class Scenario(Base):

    __tablename__ = 'scenarios'
    __table_args__ = {'autoload': True}

    phases = relationship("Phase")

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '#<Scenario %s,%s>' % (self.name, self.id)

    def get_bounds(self, srid=900913):
        """
        Method to find the bound box for a scenario (based on all of
        its underlying nodes)
        """
        session = DBSession()
        extent_query = session.query(func.ST_Transform(
                         func.ST_SetSrid(
                           func.ST_Extent(Node.point), 
                         BASE_SRID), 
                       srid)).\
               filter(Node.scenario_id == self.id)
        tup = extent_query.one() # would throw an exception if more than one result
        shp = None
        wkb = tup[0]
        if(wkb is not None):
            shp = to_shape(wkb)
        return shp


    def get_root_phase(self):
        session = DBSession()
        phase = session.query(Phase).\
                filter((Phase.scenario_id == self.id) & (Phase.id == 1)).first()
        return phase


    def to_geojson(self):
        bounds = self.get_bounds(srid=4326)
        coords = []
        if (bounds):
            if (isinstance(bounds, shapely.geometry.Point)):
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
    """ 
    Represents a branch from a scenario or another phase.
    See `PhaseAncector` for more on the Phase tree hierarchy.
    """

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

    def is_root(self):
        """
        True if this phase is the root phase of a scenario
        """
        return (self.id == 1)

    def get_bounds(self, srid=900913):
        """
        Method to find the bounding box for a phase (based on all of
        its underlying nodes and those of its ancestors)
        """
        session = DBSession()
        extent_query = session.query(func.ST_Transform(
                         func.ST_SetSrid(
                           func.ST_Extent(Node.point), 
                         BASE_SRID), 
                       srid)).\
               filter((PhaseAncestor.scenario_id == self.scenario_id) &
                     (PhaseAncestor.phase_id == self.id) & 
                     (Node.phase_id == PhaseAncestor.ancestor_phase_id) & 
                     (Node.scenario_id == PhaseAncestor.scenario_id))
        tup = extent_query.one() # would throw an exception if more than one result
        shp = None
        wkb = tup[0]
        if(wkb is not None):
            shp = to_shape(wkb)
        return shp


    def to_geojson(self):
        bounds = self.get_bounds(srid=4326)
        coords = []
        if (bounds):
            if (isinstance(bounds, shapely.geometry.Point)):
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
        node_type = get_node_type(type_string, session)
        new_nodes = []
        for pt in points:
            shp = shapely.geometry.Point(pt[0], pt[1])
            wkb_geom = from_shape(shp, srid=BASE_SRID)
            node = Node(wkb_geom, 1, node_type, self)
            new_nodes.append(node)

        session.add_all(new_nodes)

    def get_descendents_query(self):
        """
        Returns a query object representing all phases
        descending from this phase...
        NOTE:  *including* this phase
        """
        session = DBSession()
        q = session.query(Phase).filter(
            (Phase.scenario_id == self.scenario_id) &
            (Phase.id == PhaseAncestor.phase_id) &
            (PhaseAncestor.ancestor_phase_id == self.id) &
            (PhaseAncestor.scenario_id == self.scenario_id))
        return q

    def get_nodes_query(self):
        """
        Returns query for nodes associated only with this phase
        """
        return get_nodes(self.scenario_id, self.id)
 
    def get_cumulative_nodes_query(self):
        """
        Returns query for nodes associated with this phase
        AND all of it's ancestor phases
        """
        return get_cumulative_nodes(self.scenario_id, self.id)

    def locate_supply_nodes(self, distance, num_supply_nodes, session):
        """
        locate num_supply_nodes that cover the demand within
        distance from those supply_nodes.
        """
        nodes = self.get_demand_nodes_outside_distance(distance).all()
        pts = [to_shape(node.point).coords[0] for node in nodes]
        # pts = get_coords(nodes)
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
            cluster_pts = [to_shape(node.point).coords[0] for node in cluster]
            # pts = get_coords(cluster)
            unzipped = zip(*cluster_pts)
            pt = util.points_to_centroid(unzipped)
            weights = map(lambda x: x.weight, cluster)
            weight = sum(weights)
            shp = shapely.geometry.Point(pt[0], pt[1])
            wkb_geom = from_shape(shp, srid=BASE_SRID)
            node = Node(wkb_geom, weight, get_node_type('supply', session), self)
            centroids.append(node)

        centroids.sort(key=lambda x: x.weight, reverse=True)

        k_clusts = []
        if num_supply_nodes > len(centroids):
            k_clusts = centroids
        else:
            k_clusts = centroids[0:num_supply_nodes]

        return k_clusts


class PhaseAncestor(Base):

    """ 
    Maintains the hierarchical relationship between phases.  
    For any `Phase`, the PhaseAncestor table maintains a record 
    associating it with *each* phase in its ancestry.  

    For example, given the following phase ancestry:

    1        The table representation would be:
    \        phase_id|phase_ancestor_id
     2              1|1
      \             2|1
       3            2|2
    \               3|1
     4              3|2
                    3|3
                    4|1

     Note that phase 3 references both phase 2 AND phase 1.  
     This allows for simplified, non-recursive joins.  

     To accomodate this, there's a trigger defined on the phase table
     to populate phase_ancestors upon add/delete of a phase.

     """

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
    # __table_args__ = {'autoload': True}

    id = Column(Integer, primary_key=True)
    point = Column(Geometry(geometry_type='POINT', srid=BASE_SRID))
    weight = Column(Integer)
    node_type_id = Column(Integer, ForeignKey('nodetypes.id'))
    phase_id = Column(Integer, ForeignKey('phases.id'))
    scenario_id = Column(Integer, ForeignKey('scenarios.id'))
    node_type = relationship(NodeType)
    phase = relationship(Phase)

    def __init__(self, point, weight, node_type, phase):
        self.point = point
        self.weight = weight
        self.node_type = node_type
        self.phase = phase 
        self.scenario_id = phase.scenario.id

    def to_geojson(self):
        # from shapely.wkb import loads
        # point = loads(str(self.point.geom_wkb))
        point = to_shape(self.point)
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
            join(Phase, 
                    (Phase.scenario_id == Node.scenario_id) &
                    (Phase.id == Node.phase_id)).\
            join(PhaseAncestor,
                 (Phase.id == PhaseAncestor.ancestor_phase_id) &\
                 (Phase.scenario_id == PhaseAncestor.scenario_id)).\
            filter((PhaseAncestor.scenario_id == scenario_id) &\
                   (PhaseAncestor.phase_id == phase_id))

    if(node_type):
        q = q.join(NodeType).filter(NodeType.name == node_type)

    return q

def get_nodes(scenario_id, phase_id, cls_or_fun=Node, node_type=None):
    session = DBSession()
    q = session.query(cls_or_fun).\
            filter((Node.scenario_id == scenario_id) &\
                   (Node.phase_id == phase_id))

    if(node_type):
        q = q.join(NodeType).filter(NodeType.name == node_type)

    return q

