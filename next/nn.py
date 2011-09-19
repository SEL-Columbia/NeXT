import math
from shapely.wkb import loads
from next.models import Edge


def computeSphericalDistance(node1, node2):
    """
    http://en.wikipedia.org/wiki/Great-circle_distance
    """
    # Define
    convertDegreesToRadians = lambda x: x * math.pi / 180
    # Load
    longitude1, latitude1 = map(convertDegreesToRadians, node1.coords[0])
    longitude2, latitude2 = map(convertDegreesToRadians, node2.coords[0])
    # Initialize
    longitudeDelta = longitude2 - longitude1
    earthRadiusInMeters = 6371010
    # Prepare
    y = math.sqrt(math.pow(math.cos(latitude2) * math.sin(longitudeDelta), 2) + math.pow(math.cos(latitude1) * math.sin(latitude2) - math.sin(latitude1) * math.cos(latitude2) * math.cos(longitudeDelta), 2))
    x = math.sin(latitude1) * math.sin(latitude2) + math.cos(latitude1) * math.cos(latitude2) * math.cos(longitudeDelta)
    # Return
    return earthRadiusInMeters * math.atan2(y, x)


def generate_nearest_neighbor(scenario, pop_nodes, facility_nodes):
    """
    TODO, look to make this an interface
    Note that this function does not commit any edges to the database.
    arguments:
          scenario: the scenario we are running in
          pop_nodes: an iterable of next.models.Node
          facility_nodes: iterable of next.models.Node

    return: A list of edges that have the property of being a
            relation between a pop_node and its closest facility_node
    """
    edges = []
    for pop_node in pop_nodes:
        nearestDist = ()
        pop_geometry = loads(str(pop_node.point.geom_wkb))
        for fac_node in facility_nodes:
            fac_geometry = loads(str(fac_node.point.geom_wkb))
            between = pop_geometry.distance(fac_geometry)
            if between <= nearestDist:
                nearest = fac_node
                nearestDist = between

        edge = Edge(
            scenario,
            pop_node,
            nearest,
            computeSphericalDistance(pop_geometry, fac_geometry))

        edges.append(edge)

    assert len(edges) == pop_nodes.count()
    return edges




# Possible ideas for a more abstract process system
# class GeoProcess(object):
#     """
#     """

#     def __init__(self, node_set1, node_set2 ):
#         self.node_set1 = node_set1
#         self.node_set2 = node_set2

#     def __call__(self):
#         raise NameError('You must override this')


# class NN(GeoProcess):

#     def __init__(self, node_set1, node_set2):
#         GeoProcess.__init__(self, node_set1, node_set2)

#     def __call__(self):
#         pass


# nn = NN(pop_node, fac_node)
# nn()
