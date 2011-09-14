from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from next.models import initialize_sql
from rtree import Rtree


def rtree_factory(handler, registry):
    rtree_index = Rtree()

    def wrap(request):
        # addd the rtree to the index
        request.rtree = rtree_index
        response = handler(request)
        return response
    return wrap


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)

    config = Configurator(settings=settings)
    config.add_tween('next.rtree_factory')

    config.add_static_view('static', 'next:static')
    config.add_route('index', '/')
    config.add_route('show-region', '/region/{id}')
    config.add_route('upload-nodes', 'upload-nodes')
    config.add_route('add-region', '/add-region')
    config.add_route('rtree', '/rtree')

    config.scan()

    return config.make_wsgi_app()
