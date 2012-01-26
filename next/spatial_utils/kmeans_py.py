from quad_tree import QuadTree


def get_point(node_dict):
    return node_dict['xy']


class KMeansHelper(object):
    """Helper class to manage seeding, finding and updating clustered
    node assignment for KMeans"""

    def __init__(self):
        qt = None
        pass

    
    def seed(self, k, nodes):
        """ splits nodes based on x and y means of each of k partitions of
        nodes sorted by x and y """
        x_list = [nd[0] for nd in nodes]
        y_list = [nd[1] for nd in nodes]
        x_list.sort()
        y_list.sort()
    
        parts = range(0, len(nodes), (len(nodes)-1)/k)
        
        x_means = [sum(x_list[i:j])/len(x_list[i:j]) for i, j in zip(parts, parts[1:len(parts)])]
        y_means = [sum(y_list[i:j])/len(y_list[i:j]) for i, j in zip(parts, parts[1:len(parts)])]
        
        k_nodes = zip(x_means, y_means)
            
        return k_nodes

    def init_clusters(self, nodes):
        node_dicts = []
        
        x_list = [nd[0] for nd in nodes]
        y_list = [nd[1] for nd in nodes]
        x_list.sort()
        y_list.sort()

        sw = (x_list[0], y_list[0])
        ne = (x_list[-1], y_list[-1])

        self.qt = QuadTree(8, sw, ne, get_point, False)

        for i in range(0, len(nodes)):
            node_dict = {}
            node_dict['id'] = i
            node_dict['xy'] = nodes[i]
            self.qt.add(node_dict)

        
    def find_nearest(self, node):
        k_node = self.qt.find_nearest(node)
        return k_node['id']

    def update_clusters(self, cluster_assignments):
        """ Returns a new set of cluster nodes based on average of assigned points """
        cluster_list = []
        for k_id in range(0, len(cluster_assignments)):
            points = cluster_assignments[k_id]
            if len(points) > 0:
                x_list = [pt[0] for pt in points]
                y_list = [pt[1] for pt in points]
                x_list.sort()
                y_list.sort()
                x_mean = sum(x_list)/len(x_list)
                y_mean = sum(y_list)/len(y_list)
                cluster_list.append([x_mean, y_mean])
                
        return cluster_list
    
    
            
class KMeans(object):
    """Class implementing k-means clustering, based on the wikipedia
    entry more or less.  
    k:  number of clusters
    seed_function:  function that picks first k cluster nodes (args:  k, nodes)
    nearest_function:  function that determines nearest node (args:  point, k_nodes)
    """

    def __init__(self, k, helper):
        self.k = k
        self.helper = helper


    def assign_clusters(self, nodes):
        """ Assigns each node to one of K clusters """

        k_nodes = self.helper.seed(self.k, nodes)
        assignments = [None] * len(nodes)

        node_changed = True
        while node_changed:
            cluster_to_node = [None] * len(k_nodes)
            node_changed = False
            self.helper.init_clusters(k_nodes)
            for nd_id in range(0, len(nodes)):
                k_id = self.helper.find_nearest(nodes[nd_id])
                if cluster_to_node[k_id] == None:
                    cluster_to_node[k_id] = []

                cluster_to_node[k_id].append(nodes[nd_id])

                if assignments[nd_id] != k_id:
                    node_changed = True
                    assignments[nd_id] = k_id

            #assign new set of k_nodes
            k_nodes = self.helper.update_clusters(cluster_to_node)

        return (k_nodes, assignments)
                
