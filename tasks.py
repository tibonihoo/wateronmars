import os
import shutil
import configparser

from invoke import task
from fabric import Connection

DJANGO_APPS = ["wom_classification", "wom_pebbles", "wom_river", "wom_user", "wom_tributary"]

"""This tasks.py will work with an additional configuration file
where the info about deployment hosts setup is described.

The reason for that is to be able to add tasks.py itself to the
source (because the local commands are useful for devs).

The configuration file is called fabhosts.cfg and formated in INI format as follow:

  [targetName]
  connection = {userA}@{hostX}
  site_dir = ~/path/to/wateronmars_site
  virtual_env_dir = ../venv
  final_deploy_action = touch /path/to/passenger/tmp/restart.txt
  provider = ...

- connection gives user and host info of where the deployment will happen
- virtual_end_dir is relative to site_dir
- final_deploy_action can be ommited
- provider can be ommited OR replace all the others if its value is 'heroku'

There must be as many such sections as there are user+host for deployment.
"""

USER_CONF_FILE = "fabhosts.cfg"
USER_CONF = configparser.ConfigParser()
if not os.path.isfile(USER_CONF_FILE):
    raise RuntimeError("A file called {0} is needed (see tasks.py's doc for more info).".format(USER_CONF_FILE))
USER_CONF.read("./fabhosts.cfg")

DEPLOY_TARGETS = USER_CONF.sections()

@task
def serve(c):
    c.run("python3 manage.py migrate")
    c.run("python3 manage.py collectstatic --noinput")
    c.run("python3 manage.py runserver")

@task
def test(c):
    c.run("coverage run manage.py test {0}".format(" ".join(DJANGO_APPS)))

def deploy_heroku(c):
    c.run("git pull --rebase heroku master")
    c.run("git push heroku master")
    # NOTE: for existing apps running with Django1.4, the first upgrade to
    # Django1.11 should fail here and be replaced by a manual:
    # "heroku run \"python3 manage.py migrate --fake\""
    c.run("heroku run \"python3 manage.py migrate\"")

def deploy_on_remote(c, target_config):
    with Connection(target_config["connection"]) as conn:
        site_dir = target_config["site_dir"]
        run_in_dir = lambda cmd: conn.run("cd '{0}' && {1}".format(site_dir, cmd))
        venv_dir = target_config["virtual_env_dir"]
        run_in_dir("git pull --rebase origin master")
        requirements = target_config["requirements"]
        run_in_dir("source {0}/bin/activate && pip3 install -r {1}".format(venv_dir, requirements))
        # NOTE: for existing apps running with Django1.4, the first upgrade to
        # Django1.11 should fail here and be replaced by a manual:
        # "python3 manage.py migrate --fake" !
        run_in_dir("source {0}/bin/activate && python3 manage.py migrate".format(venv_dir))
        run_in_dir("source {0}/bin/activate && python3 manage.py collectstatic --noinput".format(venv_dir))
        try:
            run_in_dir(target_config["final_deploy_action"])
        except configparser.NoOptionError:
            pass

@task
def fix_contenttype_integrity_on_remote(c, to = None):
    """
    Post-migration integrity issue when adding a new model.
    """
    targets = to.split(",") if to else DEPLOY_TARGETS
    for target in targets:
        target_config = USER_CONF[target]
        if target_config.get("provider") == "heroku":
            print("Run commands directly with heroku run")
            continue
        with Connection(target_config["connection"]) as conn:
            site_dir = target_config["site_dir"]
            run_in_dir = lambda cmd: conn.run("cd '{0}' && {1}".format(site_dir, cmd))
            venv_dir = target_config["virtual_env_dir"]
            run_in_dir("source {0}/bin/activate && python3 manage.py migrate contenttypes 0001 --fake".format(venv_dir))
            run_in_dir("source {0}/bin/activate && python3 manage.py migrate contenttypes".format(venv_dir))
            run_in_dir("source {0}/bin/activate && python3 manage.py migrate --fake".format(venv_dir))
            try:
                run_in_dir(target_config["final_deploy_action"])
            except configparser.NoOptionError:
                pass

@task
def deploy(c, to = None):
    targets = to.split(",") if to else DEPLOY_TARGETS
    c.run("git pull --rebase origin master")
    c.run("git push origin master")
    for target in targets:
        print(f"STARTING DEPLOY ON: {target}")
        target_config = USER_CONF[target]
        if target_config.get("provider") == "heroku":
            deploy_heroku(c)
        else:
            deploy_on_remote(c, target_config)
        print(f"ENDING DEPLOY ON: {target}")

@task
def style_check(c):
    c.run("flake8 --ignore=E501,E111,E121 ./ --exclude=utils/,.git,__pycache__")


@task
def test_coverage(c):
    c.run('coverage report --omit "/tmp/*,_*,*/venv/*,*/migrations/*"')

@task
def schema_reset(c, app_name):
    migration_dir = os.path.join("./",app_name,"migrations")
    if os.path.isdir(migration_dir):
        print("Cleanup past migrations for {0}".format(app_name))
        shutil.rmtree(migration_dir)
    print("Initialize the migration data for {0}".format(app_name))
    c.run("python3 manage.py makemigrations {0} --initial".format(app_name))
    print("""Don't forget that to cancel previous migrations of the actual db (if any) with:
  python3 manage.py migrate {0} zero""".format(app_name))

@task
def schema_update(c, app_name=None):
    app_selection = [app_name] if app_name else DJANGO_APPS
    for app in app_selection:
        try:
            c.run("python3 manage.py makemigrations {0}".format(app))
        except:
            if app_name is None:
                pass
            else:
                raise
@task
def db_reset(c):
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
    c.run("python3 manage.py migrate")

@task
def db_update(c):
    c.run("python3 manage.py migrate")

@task
def transl_gen(c, lang):
    os.chdir("wom_user")
    try:
        c.run("python3 ../manage.py makemessages -l {0}".format(lang))
    finally:
        os.chdir("..")

@task
def transl_compile(c, lang):
    os.chdir("wom_user")
    try:
        c.run("python3 ../manage.py compilemessages -l {0}".format(lang))
    finally:
        os.chdir("..")

