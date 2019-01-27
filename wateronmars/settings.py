# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright 2013-2019 Thibauld Nion
#
# This file is part of WaterOnMars (https://github.com/tibonihoo/wateronmars) 
#
# WaterOnMars is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# WaterOnMars is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with WaterOnMars.  If not, see <http://www.gnu.org/licenses/>.
#

# Django settings for wateronmars project.

import os
APP_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


ADMINS = (
    # ('Your name', 'your@email'),
)

MANAGERS = ADMINS

# A string formatted following the example of TEAM section given at:
# http://humanstxt.org/Standard.html
# WOM_USER_HUMANS_TEAM = """/* TEAM */
#   Admin: Me.
#   Site: http://example.com
#   From: Where ?
# """

# A string formatted following the example of THANKS section given at:
# http://humanstxt.org/Standard.html
# WOM_USER_HUMANS_THANKS = """/* THANKS */
#   My Hero: Her Name.
#   Site: http://example.com/
# """


# User-Agent (important for websites that protect against DDOS by
# blacklisting some user-agents)
USER_AGENT = "wateronmars"

# Login URL
# WARNING: please check that the url mapping correctly maps the login
# view to this login url.
LOGIN_URL = "/accounts/login/"

try:
  import djcelery  
  djcelery.setup_loader()
  USE_CELERY = True
except ImportError:
  print "djcelery not available, no background task possible"
  USE_CELERY = False

# Feel free to force de-activation of celery
USE_CELERY = False


# Test if we're on heroku environment
DEPLOYMENT_PLATFORM = None
if os.environ.get("PYTHONHOME","").startswith("/app/.heroku"):
  DEPLOYMENT_PLATFORM = "heroku"
else:
  DEPLOYMENT_PLATFORM = os.environ.get("DEPLOYMENT_PLATFORM","")


# Set to True to activate the DEMO mode
DEMO = False
DEMO_USER_NAME = "demo"
DEMO_USER_PASSWD = "redh2o"

# DEBUG or not DEBUG
DEBUG = True
TEMPLATE_DEBUG = DEBUG


# Database setup
if DEPLOYMENT_PLATFORM == "heroku":
  # use Heroku's prostgres
  import dj_database_url
  DATABASES = {'default': dj_database_url.config()}
else:
  # use a local sqlite
  DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': './db.sql3',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
  }
  
# Allow all host headers
ALLOWED_HOSTS = ['*']

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = None

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'


SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ""
  
# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
# Put strings here, like "/home/html/static" or "C:/www/django/static".
# Always use forward slashes, even on Windows.
# Don't forget to use absolute paths, not relative paths.
# "/home/thibauld/Development/wateronmars/wom-experiment/static"
STATICFILES_DIRS = []

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'q-@+zcucbl_@i7fjf@fm_gnqmifik8e&amp;l8j24x!r7z*z7cjls%'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
  'django.contrib.sessions.middleware.SessionMiddleware',
  'django.middleware.locale.LocaleMiddleware',
  'django.middleware.common.CommonMiddleware',
  'django.middleware.csrf.CsrfViewMiddleware',
  'django.contrib.auth.middleware.AuthenticationMiddleware',
  'django.contrib.messages.middleware.MessageMiddleware',
  # Uncomment the next line for simple clickjacking protection:
  # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'wateronmars.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'wateronmars.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    #"/home/thibauld/Development/wateronmars/wom-experiment/templates"
)



INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'south',
    'wom_pebbles',
    'wom_river',
    'wom_classification',
    'wom_user',
    'wom_tributary'
    )


if USE_CELERY:
  INSTALLED_APPS += (
    'kombu.transport.django',  
    'djcelery',  
  )


BROKER_BACKEND = "django"


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
      'console':{
        'level': 'DEBUG',
        'class': 'logging.StreamHandler',
      },
      'mail_admins': {
        'level': 'ERROR',
        'filters': ['require_debug_false'],
      'class': 'django.utils.log.AdminEmailHandler'
      }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'wom_pebbles.tasks': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'wom_user.tasks': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'wom_river.tasks': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# Translation support.
# Note: translation set-up thanks to the following tutorial:
# http://www.marinamele.com/taskbuster-django-tutorial/internationalization-localization-languages-time-zones
from django.utils.translation import ugettext_lazy as _

LANGUAGES = (
  ("en", _("English")),
  ("fr", _("French")),
)

LOCALE_PATHS = (
  os.path.join(APP_BASE_DIR, "..", "wom_user", "locale"),
)
