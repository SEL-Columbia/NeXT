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
    env.project_tmp_directory = os.path.join(env.project_directory, 'tmp')
    env.src_directory = os.path.join(env.project_directory, env.repo)
    env.wsgi_file = os.path.join(env.src_directory, 'next.wsgi')
    env.pip_requirements_file = os.path.join(env.src_directory, 'requirements.txt')


def deploy(deployment):
    pull(deployment)        
    run_in_virtualenv("pip install -r %s" % env.pip_requirements_file)
    with cd(env.src_directory):
        run("sudo su postgres ./load-sql.sh")
        
    run('touch %s' % env.wsgi_file)


def pull(deployment):
    setup_env(deployment)
    with cd(env.src_directory):
        run("git pull origin %(branch)s" % env)
        run('find . -name "*.pyc" | xargs rm -rf')
        

def setup(deployment):
    pull(deployment)
    run('mkdir -p %s' % env.project_tmp_directory)
    with cd(env.project_tmp_directory):

        # because we use an OLD version of bootstrap, we're kinda screwed
        # NEED TO UPGRADE OR REMOVE DEPENDENCY ON BOOTSTRAP
        #run("wget http://twitter.github.com/bootstrap/assets/bootstrap.zip")
        #run("unzip -u bootstrap.zip")

         #with cd("bootstrap"):
            #run("wget http://twitter.github.com/bootstrap/assets/js/bootstrap-tab.js")
   

        #run("wget http://openlayers.org/download/OpenLayers-2.11.zip")
        #run("unzip -u OpenLayers-2.11.zip")
        with cd(os.path.join("OpenLayers-2.11", "build")):
            run("./build.py")

        with cd("OpenLayers-2.11"):
            open_layers_path = os.path.join("..", "openlayers")
            open_layers_js_path = os.path.join("build", "OpenLayers.js")
            run("mkdir -p %s" % open_layers_path)
            run("cp -R img %s" % open_layers_path)
            run("cp -R theme %s" % open_layers_path)
            run("cp %s %s" % (open_layers_js_path, open_layers_path))

        static_dir = os.path.join(env.src_directory, "next", "static")
        run("cp -R %s %s" % ("bootstrap", static_dir))
        run("cp -R %s %s" % ("openlayers", static_dir))
        
