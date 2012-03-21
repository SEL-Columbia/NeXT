from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from next.models import initialize_sql


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)

    config = Configurator(settings=settings)

    config.add_static_view('static', 'next:static')
    config.add_route('index', '/')
    config.add_route('scenarios', '/scenarios')
    config.add_route('create-scenario', '/scenarios/create')
    config.add_route('remove-scenarios', '/scenarios/remove')

    config.add_route('show-scenario', '/scenarios/{id}')
    config.add_route('nodes', '/scenarios/{id}/nodes')
    config.add_route('find-demand-within', '/scenarios/{id}/find-demand-within')

    config.add_route('graph-scenario', '/scenarios/{id}/graph-data')
    config.add_route('graph-scenario-cumul', '/scenarios/{id}/graph-data-cumul')

    config.add_route('create-supply-nodes', 'scenarios/{id}/create-supply-nodes')

    config.scan()
    return config.make_wsgi_app()
