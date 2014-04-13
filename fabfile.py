import os
import shutil
import ConfigParser

from fabric.api import local
from fabric.api import run, cd
from fabric.api import env

DJANGO_APPS = ["wom_classification", "wom_pebbles", "wom_river", "wom_user"]

"""This fabfile.py will work with an additional configuration file
where the info about deployment hosts setup is described.

The reason for that is to be able to add fabfile.py itself to the
source (because the local commands are useful for devs).

The configuration file is called fabhosts.cfg and formated in INI format as follow:

[{userA}@{hostX}]
site_dir = ~/path/to/wateronmars_site
virtual_env_dir = ../venv
final_deploy_action = touch /path/to/passenger/tmp/restart.txt

There must be as many such sections as there are user+host for deployment.
Also please note:
- virtual_end_dir is relative to site_dir
- final_deploy_action can be ommited
"""

USER_CONF_FILE = "fabhosts.cfg"
USER_CONF = ConfigParser.ConfigParser()
if not os.path.isfile(USER_CONF_FILE):
    raise RuntimeError("A file called %s is needed (see fabfile.py's doc for more info)." % USER_CONF_FILE)
USER_CONF.read("./fabhosts.cfg")

env.hosts = USER_CONF.sections()


def validate():
    local("coverage run manage.py test %s" % " ".join(DJANGO_APPS))

def deploy_demo():
    local("git push heroku master")

def deploy():
    user_host_conf = lambda x: USER_CONF.get("{0}@{1}".format(env.user,env.host),x)
    local("git push origin master")
    with cd(user_host_conf("site_dir")):
        venv_dir = user_host_conf("virtual_env_dir")
        run("git pull origin master")
        run("source {0}/bin/activate && pip install -r requirements.txt".format(venv_dir))
        run("source {0}/bin/activate && python manage.py collectstatic".format(venv_dir))
        try:
            run(user_host_conf("final_deploy_action"))
        except ConfigParser.NoOptionError:
            pass

def fab8():
    local("flake8 --ignore=E501,E111,E121 ./ --exclude=utils/,.git,__pycache__")


def cov_report():
    local('coverage report --omit "/tmp/*,_*,*/venv/*,*/migrations/*"')

def db_reset():
    print("Cleanup past migrations")
    for app_name in DJANGO_APPS:
        migration_dir = os.path.join("./",app_name,"migrations")
        if os.path.isidir(migration_dir):
            shutil.rmtree(migration_dir)
    print("Initialize the migration data")
    for app_name in DJANGO_APPS:
        local("python manage.py schemamigration %s --initial" % app_name)
    # Just in case we're using a local sql3 db, remove it for
    # proper reset (in other cases, cleaning out the db must be
    # done before calling this script)
    if not os.path.isfile("./db.sql3"):
        print("""Couldn't find any local sql3 db.
WARNING: Make sure to clean any db used by Django before the reset !""")
    else:
        print("Remove db.sql3")
        os.remove("./db.sql3")
    print("Setup the base db")
    local("python manage.py syncdb")
    local("python manage.py migrate")
    
def db_update():
    local("python manage.py syncdb")
    local("python manage.py migrate")
