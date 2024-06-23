# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright (C) 2013-2019 Thibauld Nion
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

WOM_ROOT_URL = os.environ.get("WOM_ROOT_URL", "")  # Replace this ! 
if not WOM_ROOT_URL:
  raise Exception("'WOM_ROOT_URL' must be set to the URL where the site can be reached.")

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
  print("djcelery not available, no background task possible")
  USE_CELERY = False

# Feel free to force de-activation of celery
USE_CELERY = False


# Test if we're on heroku environment
DEPLOYMENT_PLATFORM = None
if "/app/.heroku" in os.environ["PATH"]:
  # Consider moving to django_heroku that requires python3
  DEPLOYMENT_PLATFORM = "heroku"
else:
  DEPLOYMENT_PLATFORM = os.environ.get("DEPLOYMENT_PLATFORM","")
print("Setting DEPLOYMENT_PLATFORM to {}".format(DEPLOYMENT_PLATFORM))


# Set to True to activate the DEMO mode
DEMO = True
DEMO_USER_NAME = "demo"
DEMO_USER_PASSWD = "redh2o"
# DEMO mode is safest if READ ONLY (typically the DEMO user credentials may be
# displayed publicly for convenience, and you don't want a random visiter
# filling up you db with radom feeds).
#
# You may still allow a DEMO run with READ_ONLY=False if you want to demo/test
# edition features of course, on a local or protected network (but releasing
# DEMO=True and READ_ONLY=True to the open web is almost surely a bad idea)
READ_ONLY = True

# DEBUG or not DEBUG
DEBUG = False


# Database setup
if DEPLOYMENT_PLATFORM == "heroku":
  import dj_database_url
  DATABASES = {'default': dj_database_url.config()}
else:
  # use a local sqlite
  DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
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
TIME_ZONE = "Europe/Paris"

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
STATIC_ROOT = os.path.join(APP_BASE_DIR, "static")
  
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
# see also https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-SECRET_KEY
SECRET_KEY = os.environ.get("WOM_DJANGO_SECRET_KEY", "")  # Replace this ! 
if not SECRET_KEY:
    raise Exception("Set 'SECRET_KEY' to a specific unique key !")


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

    
MIDDLEWARE = [
  'django.contrib.sessions.middleware.SessionMiddleware',
  'django.middleware.locale.LocaleMiddleware',
  'django.middleware.common.CommonMiddleware',
  'django.middleware.csrf.CsrfViewMiddleware',
  'django.contrib.auth.middleware.AuthenticationMiddleware',
  'django.contrib.messages.middleware.MessageMiddleware',
  'django.middleware.clickjacking.XFrameOptionsMiddleware',
  ]

ROOT_URLCONF = 'wateronmars.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'wateronmars.wsgi.application'


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
from django.utils.translation import gettext_lazy as _

LANGUAGES = (
  ("en", _("English")),
  ("fr", _("French")),
)

LOCALE_PATHS = (
  os.path.join(APP_BASE_DIR, "..", "wom_user", "locale"),
)


# Set the auto field used to build a primary key
# see also: https://stackoverflow.com/questions/67783120/warning-auto-created-primary-key-used-when-not-defining-a-primary-key-type-by
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
