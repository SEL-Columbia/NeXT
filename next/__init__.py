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
    config.add_route('show-all-scenarios', '/scenarios')

    config.add_route('create-scenario', '/scenario/new')
    config.add_route('show-scenario', '/scenario/{id}')
    config.add_route('run-scenario', '/scenario/{id}/run')
    config.add_route('add-new-nodes', '/scenario/{id}/new-nodes'),
    config.add_route('find-pop-within', '/scenario/{id}/find-pop-within')
    config.add_route('remove-scenario', 'scenario/{id}/remove')

    config.add_route('graph-scenario', '/scenario/{id}/graph-data')
    config.add_route('graph-scenario-cumul', '/scenario/{id}/graph-data-cumul')

    config.add_route('show-population-json', '/scenario/{id}/population')
    config.add_route('show-facility-json', 'scenario/{id}/facilities')
    config.add_route('create-facilities', 'scenario/{id}/create-facilities')

    config.scan()
    return config.make_wsgi_app()
