import numpy
import rpy2
from rpy2.robjects import r
import rpy2.robjects.numpy2ri


def hclust(pts, distance, clust_method="single", use_great_circle=True):
    """ Hierarchical clustering method.  Exposes R hclust function in Python.
    Algorithm:
    - Calculate distances for each pair of input pts
    (use_great_circle:  TRUE then use great_circle else use Euclidean)
    - Cluster the points via hclust with distances and clust_method
    - Cut the resultant clusters via cutree at the desired distance
    - distance should be in kilometers IF use_great_circle=TRUE, otherwise,
    they should be in the same metric as the input pts. 
    (see R doc for sp.spDist)
    - Return the set of sets of points (i.e. the clusters)
    """

    rpy2.robjects.numpy2ri.activate() 

    pt_array = numpy.array(pts)
    r.library('sp')
    sp_dists = r.spDists(pt_array, longlat=use_great_circle)
    dists = r('as.dist')(sp_dists)
    tree = r.hclust(dists, method=clust_method)
    clusters = r.cutree(tree, h=distance)
    
    # this is a little tricky
    # clusters maintains a list of indexes for each point in the original list.  
    # The indexes represent the cluster number
    # For example: 
    #   clusters = [1, 3, 3, 1, 2, 1]
    #
    # where the 0th, 3rd, and last point in the original set
    # belong to cluster number 1
    #
    # We want to return a list of clusters, each containing
    # the index to the original point, so we map them here.  
    #
    # Things are a little more confusing since R counts arrays
    # from 1, python from 0 (hence the "- 1" from the cluster index)
    list_of_pts = [[] for i in range(max(clusters))]
    for j in range(0, len(clusters)):
        list_of_pts[clusters[j] - 1].append(j)

    
    return list_of_pts


