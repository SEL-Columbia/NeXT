# import os
# import csv
# from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.url import route_url

# from geoalchemy import WKTSpatialElement

from next.models import Scenario
# from next.models import Node
# from next.models import NodeType
from next.models import DBSession


def get_object_or_404(cls, id):
    session = DBSession()
    obj = session.query(cls).get(id)
    if obj is not None:
        return obj
    else:
        # raise
        return HTTPNotFound('Unable to locate class:%s id:%s' % (cls, id))


@view_config(route_name='index', renderer='index.mako')
def index(request):
    session = DBSession()
    return {'scenarios': session.query(Scenario).all()}


@view_config(route_name='create-scenario', renderer='create-scenario.mako')
def create_scenario(request):
    """
    1. look up data from html form
    2. create new scenario (allow use to give name)
    3. upload two csv files
      -> import the csv files as nodes
      -> assgin types
    4. run scenario
    """

    scenario = request.POST

    return HTTPFound(route_url('run-scenario', request, id=scenario.id))


def run_scenario(request):
    """
    """
    scenario = get_object_or_404(Scenario, request.matchdict['id'])
    try:
        scenario.run()
    except:
        raise NameError('blah')
    return HTTPFound(route_url('show-scenario', request, id=scenario.id))


@view_config(route_name='show-scenario', renderer='show-scenario.mako')
def show_scenario(request):
    scenario = get_object_or_404(Scenario, request.matchdict['id'])

    if scenario.has_run():
        return {'scenario': scenario }

    else:
        return HTTPFound(route_url('run-scenario', request, id=scenario.id))
