import os

os.environ["WOM_ROOT_URL"] = "wom.test.example.com"
os.environ["WOM_DJANGO_SECRET_KEY"] = "1321"


from .settings import *

DEMO = False
READ_ONLY = False
