# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright 2013 Thibauld Nion
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


import settings
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^robots.txt$', 'wom_user.views.get_robots_txt'),
                       url(r'^humans.txt$', 'wom_user.views.get_humans_txt'),
                       url(r'^$', 'wom_user.views.home', name='home'),
                       url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
                       url(r'^accounts/logout/$', 'wom_user.views.user_logout'),
                       url(r'^accounts/profile/$', 'wom_user.views.user_profile'),
                       url(r'^u/(?P<owner_name>[^/]*)/$', 'wom_user.views.user_root'),
                       url(r'^u/(?P<owner_name>[^/]*)/sources/opml/$', 'wom_user.views.user_upload_opml'),
                       url(r'^u/(?P<owner_name>[^/]*)/collection/$', 'wom_user.views.user_collection'),
                       url(r'^u/(?P<owner_name>[^/]*)/collection/nsbmk/$', 'wom_user.views.user_upload_nsbmk'),
                       url(r'^u/(?P<owner_name>[^/]*)/sources/$', 'wom_user.views.user_river_sources'),
                       url(r'^u/(?P<owner_name>[^/]*)/sources/add/$', 'wom_user.views.user_river_source_add'),
                       url(r'^u/(?P<owner_name>[^/]*)/sources/tributary/$', 'wom_user.views.user_tributary'),
                       url(r'^u/(?P<owner_name>[^/]*)/sources/tributary/twitter/$', 'wom_user.views.user_tributary_twitter'),
                       url(r'^u/(?P<owner_name>[^/]*)/sources/tributary/twitter/add/$', 'wom_user.views.user_tributary_twitter_add'),
                       url(r'^u/(?P<owner_name>[^/]*)/sources/item/(?P<source_url>.*)$', 'wom_user.views.user_river_source_item'),
                       url(r'^u/(?P<owner_name>[^/]*)/river/$', 'wom_user.views.user_river_view'),
                       url(r'^u/(?P<owner_name>[^/]*)/sieve/$', 'wom_user.views.user_river_sieve'),
                       url(r'^u/(?P<owner_name>[^/]*)/collection/add/$','wom_user.views.user_collection_add'),
                       url(r'^u/(?P<owner_name>[^/]*)/collection/item/(?P<reference_url>.*)$','wom_user.views.user_collection_item'),
                       # access to static files
                       url(r'^static/(?P<path>.*)$',
                           'django.views.static.serve',
                           {'document_root': settings.STATIC_ROOT}),
                       )

if not settings.USE_CELERY:
  urlpatterns += patterns('',
                       # temporary hack to avoid depending too much on
                       # background tasks
                       url(r'^houston/we_ve_got_an_update_request/$',
                           'wom_user.views.request_for_update'),
                       url(r'^houston/we_ve_got_a_cleanup_request/$',
                           'wom_user.views.request_for_cleanup'),
                        )

if not settings.READ_ONLY:
  urlpatterns += patterns('',
                          url(r'^accounts/new/$',
                              'wom_user.views.user_creation'),
                          url(r'^accounts/auth_landing/twitter/$',
                              'wom_user.views.user_auth_landing_twitter'),
                          url(r'^admin/',
                              include(admin.site.urls)),
                          # Uncomment the admin/doc line below to
                          # enable admin documentation
                          url(r'^admin/doc/',
                              include('django.contrib.admindocs.urls')),
                        )

