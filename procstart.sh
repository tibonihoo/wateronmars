# Local Processes configuration for test deployment
screen -L -d -m python manage.py celeryd -E -B --loglevel=INFO
python manage.py runserver
