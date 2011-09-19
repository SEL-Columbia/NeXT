
from shapely.wkb import loads
from next.models import Edge
from spatial_utils import util
from nn import computeSphericalDistance


def generate_nearest_neighbor(scenario, pop_nodes, facility_nodes):
    """
    Nearest Neighbor via QuadTree.  Faster for large number of
    facilities (i.e. > 1000)
    Note that this function does not commit any edges to the database.
    arguments:
          scenario: the scenario we are running in
          pop_nodes: an iterable of next.models.Node
          facility_nodes: iterable of next.models.Node

    return: A list of edges that have the property of being a
            relation between a pop_node and its closest facility_node
    """
    edges = []
    bounds = scenario.get_bounds(srid=4326).bounds
    qt = util.QuadTree(10, bounds[:2], bounds[2:],
                       lambda obj: loads(str(obj.point.geom_wkb)).bounds[:2])
    for fac_nd in facility_nodes: qt.add(fac_nd)
    for pop_node in pop_nodes:
        pop_geometry = loads(str(pop_node.point.geom_wkb))
        pop_pt = pop_geometry.bounds[:2]
        fac_node = qt.find_nearest(pop_pt)
        fac_geometry = loads(str(fac_node.point.geom_wkb))
        nearestDist = computeSphericalDistance(pop_geometry, fac_geometry)
        edge = Edge(scenario, pop_node, fac_node, nearestDist)
        edges.append(edge)
    return edges
