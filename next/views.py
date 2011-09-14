import os
import csv
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from colander import MappingSchema
from colander import SchemaNode
from colander import String

from geoalchemy import WKTSpatialElement

from next.models import Region
from next.models import Node
from next.models import NodeType
from next.models import DBSession


@view_config(route_name='index', renderer='index.mako')
def index(request):
    session = DBSession()
    return {'regions': session.query(Region).all(),
            'types': session.query(NodeType).all()
            }


@view_config(route_name='rtree')
def rtree(request):
    return Response(str(request.rtree))


@view_config(route_name='show-region', renderer='show_region.mako')
def show_region(request):
    session = DBSession()
    region = session.query(Region).get(int(request.matchdict['id']))
    nodes = session.query(Node).filter_by(region=region)
    return {'region': region, 'nodes': nodes}


class AddRegionSchema(MappingSchema):
    name = SchemaNode(String())


@view_config(route_name='add-region')
def add_region(request):
    return Response()


@view_config(route_name='upload-nodes', renderer='upload_nodes.mako')
def upload_nodes(request):
    """
    XXXX To Do, make this less awful
    """
    session = DBSession()
    if request.method == 'GET':
        return {'node_types': session.query(NodeType).all(),
                'regions': session.query(Region).all()}

    elif request.method == 'POST':

        node_type = session.query(
            NodeType).get(request.params['node-type'])

        region = session.query(
            Region).get(request.params['region'])

        if node_type and region:

            filename = request.params['node-file'].filename
            node_file = request.params['node-file'].file
            file_path = os.path.join('/tmp', filename)
            tmp_file = open(file_path, 'wb')
            tmp_file.write(node_file.read())
            tmp_file.close()
            csv_file = csv.reader(open(file_path, 'rU'))

            for row in csv_file:
                node = Node(
                    WKTSpatialElement('POINT(%s %s)' % (row[0], row[1])),
                    0,
                    node_type,
                    region
                    )
                session.add(node)
        return HTTPFound(location='/')
    else:
        return HTTPFound(location='/')
