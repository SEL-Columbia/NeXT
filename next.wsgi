from pyramid.paster import get_app
application = get_app(
  '/home/modwsgi/<deploy_dir>/<environment>.ini', 'main')
