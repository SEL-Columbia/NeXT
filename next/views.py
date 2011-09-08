from pyramid.response import Response
from pyramid.view import view_config

from colander import MappingSchema
from colander import SchemaNode
from colander import String


@view_config(route_name='index', renderer='index.mako')
def index(request):
    return {}


class AddRegionSchema(MappingSchema):
    name = SchemaNode(String())


@view_config(route_name='add-region')
def add_region(request):
    return Response('okay')
