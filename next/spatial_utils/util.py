from collections import deque
import math
import types

class Bounds:
    """Rectangular bounds, takes 2 tuples representing
       the lower left and upper right of the bounds"""
    def __init__(self, sw, ne):
        self.min_x = sw[0]
        self.min_y = sw[1]
        self.max_x = ne[0]
        self.max_y = ne[1]


    def intersects(self, other):
        return overlaps((self.min_x, self.max_x), \
                        (other.min_x, other.max_x)) and \
               overlaps((self.min_y, self.max_y), \
                        (other.min_y, other.max_y))


    def get_corners(self):
        corners = [[self.min_x, self.min_y], 
                   [self.min_x, self.max_y],
                   [self.max_x, self.min_y],
                   [self.max_x, self.max_y]]
        return corners


    def __str__(self):
        return "sw: {0},{1} ne: {2},{3}".format( \
                self.min_x, self.min_y, self.max_x, self.max_y)

class QuadTree:
    """class representing a point QuadTree with a maximum
       number of points per leaf, sw & ne coords, and an 
       optional function to convert the object into a point array."""
    def __init__(self, per_leaf, sw, ne, pt_fun=None, spherical=False):
        self.per_leaf = per_leaf
        self.root = self.QuadNode(sw, ne)
        self.pt_fun = pt_fun
        self.spherical = spherical


    class PointObj:
        """ class wrapping the values stored in quadtree leaves.  Lets 
            us treat everything as a point array ([0] == x, [1] == y). """
        def __init__(self, obj, pt_fun=None):
            self.obj = obj
            if (pt_fun):
                setattr(self, '__getitem__', 
                        types.MethodType(
                            lambda self, i: pt_fun(self.obj)[i], self))
            else:
                setattr(self, '__getitem__', 
                        types.MethodType(lambda self, i: self.obj[i], self))
        

    class QuadNode:
        """node within the QuadTree.  Leaves contain points.
           non-leaves do not."""
        def __init__(self, sw, ne):
            self.bounds = Bounds(sw, ne)
            self.points = []
            self.quads = []
       
        def __str__(self):
            return self.bounds.__str__() + "|" + self.points.__str__()
             
    def __str__(self):
        return self.to_str(self.root)

    def to_str(self, quad_node):
        str = ""
        quad_queue = deque()
        quad_queue.append(quad_node)
        while quad_queue:
            curr_qn = quad_queue.popleft() 
            str += "{0}\n".format(curr_qn.__str__())
            for qn in curr_qn.quads:
                quad_queue.append(qn)
        return str
            
    def _divide_quad(self, quad_node):
        """ Split the node into 4 equal sized quadrants
            and return them. """
        bnds = quad_node.bounds
        x_diff = bnds.max_x - bnds.min_x
        y_diff = bnds.max_y - bnds.min_y
        x_dist = x_diff / 2
        y_dist = y_diff / 2
        quad_nodes = []
        ne = self.QuadNode((bnds.min_x + x_dist, bnds.min_y + y_dist), \
                      (bnds.max_x, bnds.max_y))
        se = self.QuadNode((bnds.min_x + x_dist, bnds.min_y), \
                      (bnds.max_x, bnds.min_y + y_dist)) 
        sw = self.QuadNode((bnds.min_x, bnds.min_y), \
                      (bnds.min_x + x_dist, bnds.min_y + y_dist)) 
        nw = self.QuadNode((bnds.min_x, bnds.min_y + y_dist), \
                      (bnds.min_x + x_dist, bnds.max_y)) 
        quad_nodes.append(ne)
        quad_nodes.append(se)
        quad_nodes.append(sw)
        quad_nodes.append(nw)
        return quad_nodes
        
    def add(self, pt):
        """ Add the pt to the appropriate node
            in the QuadTree """
        pt_obj = self.PointObj(pt, self.pt_fun)
        self._add(pt_obj, self.root)

    def _add(self, pt, quad_node):
        """ Recursively look for the appropriate
            node to insert the tuple into.  Create
            new quadrants when existing leaf nodes
            get full. """
        if not quad_node.quads: # this is a leaf
            if len(quad_node.points) < self.per_leaf:
                quad_node.points.append(pt)
                return
            else:
                quad_node.quads = self._divide_quad(quad_node)
                pts = quad_node.points
                pts.append(pt)
                quad_node.points = []
                for p in pts:
                    self._add(p, quad_node)
        else:
            quad_ind = get_containing_quad(pt, quad_node.quads) 
            self._add(pt, quad_node.quads[quad_ind]) 

    def find_nearest(self, pt):
        """ Find the nearest point to pt """
        pt_obj = self._find_nearest(pt, self.root)
        if (pt_obj): 
            return pt_obj.obj

    def _find_nearest(self, pt, quad_node):
        """ Find the nearest point by finding the quad_node
        it would be added to (handling all corner cases)."""
        if not quad_node.quads:
            return get_nearest_point(pt, quad_node.points, self.spherical)
        else:
            cur_pt = None
            cur_dist = float("inf")
            quad_ind = get_containing_quad(pt, quad_node.quads)
            if(quad_ind != -1):
                cand_pt = self._find_nearest(pt, quad_node.quads[quad_ind])
                if not (cand_pt is None):
                    cand_dist = point_dist(pt, cand_pt, self.spherical)
                    if(cand_dist < cur_dist):
                        cur_dist = cand_dist
                        cur_pt = cand_pt
    
            # rank 'other' quad nodes by dist to point
            # if that dist is < cur_dist, we need to search it
            cand_inds = [0, 1, 2, 3]
            if (quad_ind != -1): 
                cand_inds.remove(quad_ind)
    
            cand_quads = [quad_node.quads[i] for i in cand_inds]
            cand_quads.sort(lambda a, b:  
                    cmp(get_dist_to_bounds(pt, a.bounds, self.spherical), 
                        get_dist_to_bounds(pt, b.bounds, self.spherical)))
            for cand_q in cand_quads:
                pt_bnd_dist = get_dist_to_bounds(pt, 
                        cand_q.bounds, self.spherical)
                if (pt_bnd_dist < cur_dist):
                    cand_pt = self._find_nearest(pt, cand_q)
                    if not (cand_pt is None):
                        cand_dist = point_dist(pt, cand_pt, self.spherical)
                        if (cand_dist < cur_dist):
                            cur_dist = cand_dist
                            cur_pt = cand_pt
    
            return cur_pt


def get_containing_quad(pt, quads):
    """ return the index of the quadrant containing the point """
    for i in range(len(quads)):
        if contains(pt, quads[i].bounds):
            return i

    return -1

def point_dist(pt1, pt2, spherical=False):
    diff_x = pt1[0] - pt2[0]
    diff_y = pt1[1] - pt2[1]
    if(spherical):
        diff_x = diff_x * \
        abs(math.cos(((pt1[1] + pt2[1]) / 2) * (math.pi / 180)))

    return math.sqrt((diff_x * diff_x) + (diff_y * diff_y))

def get_nearest_point(pt, pt_list, spherical=False):
    cur_dist = float("inf")
    cur_pt = None
    for cand_pt in pt_list:
        cand_dist = point_dist(pt, cand_pt, spherical)
        if cand_dist < cur_dist:
            cur_dist = cand_dist
            cur_pt = cand_pt

    return cur_pt


def get_dist_to_bounds(pt, bounds, spherical=False):
    """ return the distance from the point to the closest intersecting 
        point along the perimeter of bounds. """

    if(spherical):
        lat_lon_ratio = abs(math.cos(pt[1] * (math.pi / 180)))
        x_min_diff = abs(pt[0] - bounds.min_x) * lat_lon_ratio
        x_max_diff = abs(pt[0] - bounds.max_x) * lat_lon_ratio
    else:
        x_min_diff = abs(pt[0] - bounds.min_x)
        x_max_diff = abs(pt[0] - bounds.max_x)

    
    if (contains(pt, bounds)):
        return min([abs(pt[1] - bounds.min_y), 
               x_max_diff,
               x_min_diff,
               abs(pt[0] - bounds.max_x)])
    elif (bounds.min_x <= pt[0] <= bounds.max_x):
        return min([abs(pt[1] - bounds.min_y), abs(pt[1] - bounds.max_y)])
    elif (bounds.min_y <= pt[1] <= bounds.max_y):
        return min([x_min_diff, x_max_diff])
    else:
        return point_dist(pt, 
                get_nearest_point(pt, bounds.get_corners(), spherical), 
                spherical)
    

def contains(pt, bounds):
    """Determine whether the point is within the bounds"""
    return ((bounds.min_x <= pt[0] <= bounds.max_x) and \
            (bounds.min_y <= pt[1] <= bounds.max_y))

def overlaps(r1, r2):
    """Determine whether range r1 overlaps range r2
       range is defined a 2 element tuple where element
       0 is the min and 1 is the max of the range"""
    return (r2[0] <= r1[0] <= r2[1]) or \
           (r1[0] <= r2[0] <= r1[1]) or \
           (r1[0] == r2[1] or r2[0] == r1[1])


 
