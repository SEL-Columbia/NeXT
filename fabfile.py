import os

from fabric.api import env, run, cd
# from fabric.decorators import hosts

DEFAULTS = {
    'home': '/home/modwsgi',
    'repo': 'NeXT'
    }

DEPLOYMENTS = {
    'stage': {
        'host_string': 'modwsgi@128.59.149.71:12127',
        'project': 'next_stage', 
        'branch': 'master'
        }, 
    'prod': {
        'host_string': 'modwsgi@spatialplanner.modilabs.org:12127',
        'project': 'next_prod',
        'branch': 'master'
        }
    }

def run_in_virtualenv(command):
    d = {
        'activate': os.path.join(
            env.src_directory, 'bin', 'activate'),
        'command': command
        }
    run('source %(activate)s && %(command)s' % d)


def setup_env(deployment):
    env.update(DEFAULTS)
    env.update(DEPLOYMENTS[deployment])
    env.project_directory = os.path.join(env.home, env.project)
    env.src_directory = os.path.join(env.project_directory, env.repo)
    env.wsgi_file = os.path.join(env.project_directory, 'next.wsgi')
    env.pip_requirements_file = os.path.join(env.src_directory, 'requirements.txt')


def deploy(deployment):
    setup_env(deployment)
    with cd(env.src_directory):
        run("git pull origin %(branch)s" % env)
        run('find . -name "*.pyc" | xargs rm -rf')
        
    run_in_virtualenv("pip install -r %s" % env.pip_requirements_file)
    with cd(env.src_directory):
        run("sudo su postgres ./load-sql.sh")
        
    run('touch %s' % env.wsgi_file)
