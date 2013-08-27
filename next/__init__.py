from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from next.model import initialize_base, initialize_session

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_base(engine)
    initialize_session(engine)

    config = Configurator(settings=settings)

    config.add_static_view('static', 'next:static')
    config.add_route('index', '/')
    config.add_route('scenarios', '/scenarios')
    config.add_route('create-scenario', '/scenarios/create')
    config.add_route('remove-scenarios', '/scenarios/remove')

    config.add_route('show-scenario', '/scenarios/{id}')
    config.add_route('create-phase', '/scenarios/{id}/phases/{phase_id}/create')
    config.add_route('remove-phase', '/scenarios/{id}/phases/{phase_id}/remove')
    config.add_route('show-phase', '/scenarios/{id}/phases/{phase_id}')
    config.add_route('phases', '/scenarios/{id}/phases')
    config.add_route('nodes', '/scenarios/{id}/nodes')
    config.add_route('phase-nodes', '/scenarios/{id}/phases/{phase_id}/nodes')
    config.add_route('cumulative-phase-nodes', '/scenarios/{id}/phases/{phase_id}/cumulative-nodes')
    config.add_route('find-demand-within', '/scenarios/{id}/phases/{phase_id}/find-demand-within')

    config.add_route('graph-phase', '/scenarios/{id}/phases/{phase_id}/graph-data')
    config.add_route('graph-phase-cumul', '/scenarios/{id}/phases/{phase_id}/graph-data-cumul')

    config.add_route('create-supply-nodes', '/scenarios/{id}/phases/{phase_id}/create-supply-nodes')

    config.scan()
    return config.make_wsgi_app()
