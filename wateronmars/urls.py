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


from . import settings
from django.conf.urls import include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


from wom_user.views import (
    get_robots_txt,
    get_humans_txt,
    home,
    user_logout,
    user_profile,
    user_root,
    user_upload_opml,
    user_collection,
    user_upload_nsbmk,
    user_river_sources,
    user_river_source_add,
    user_tributary,
    user_tributary_twitter,
    user_tributary_twitter_add,
    user_river_source_item,
    user_river_view,
    user_river_sieve,
    user_collection_add,
    user_collection_item,
    request_for_update,
    request_for_cleanup,
    user_creation,
    user_auth_landing_twitter,
    )

from django.contrib.auth import views as auth_views
from django.views.static import serve as static_serve


urlpatterns = [
    url(r'^robots.txt$', get_robots_txt),
    url(r'^humans.txt$', get_humans_txt),
    url(r'^$', home, name='home'),
    url(r'^accounts/login/$', auth_views.LoginView.as_view(template_name='login.html'), name='user_login'),
    url(r'^accounts/logout/$', user_logout, name='user_logout'),
    url(r'^accounts/profile/$', user_profile, name='user_profile'),
    url(r'^u/(?P<owner_name>[^/]*)/$', user_root, name='user_root'),
    url(r'^u/(?P<owner_name>[^/]*)/sources/opml/$', user_upload_opml, name='user_upload_opml'),
    url(r'^u/(?P<owner_name>[^/]*)/collection/$', user_collection, name='user_collection'),
    url(r'^u/(?P<owner_name>[^/]*)/collection/nsbmk/$', user_upload_nsbmk, name='user_upload_nsbmk'),
    url(r'^u/(?P<owner_name>[^/]*)/sources/$', user_river_sources, name='user_river_sources'),
    url(r'^u/(?P<owner_name>[^/]*)/sources/add/$', user_river_source_add, name='user_river_source_add'),
    url(r'^u/(?P<owner_name>[^/]*)/sources/tributary/$', user_tributary, name='user_tributary'),
    url(r'^u/(?P<owner_name>[^/]*)/sources/tributary/twitter/$', user_tributary_twitter, name='user_tributary_twitter'),
    url(r'^u/(?P<owner_name>[^/]*)/sources/tributary/twitter/add/$', user_tributary_twitter_add, name='user_tributary_twitter_add'),
    url(r'^u/(?P<owner_name>[^/]*)/sources/item/(?P<source_url_code>.*)$', user_river_source_item, name='user_river_source_item'),
    url(r'^u/(?P<owner_name>[^/]*)/river/$', user_river_view, name='user_river_view'),
    url(r'^u/(?P<owner_name>[^/]*)/sieve/$', user_river_sieve, name='user_river_sieve'),
    url(r'^u/(?P<owner_name>[^/]*)/collection/add/$', user_collection_add, name='user_collection_add'),
    url(r'^u/(?P<owner_name>[^/]*)/collection/item/(?P<reference_url_code>.*)$',user_collection_item, name='user_collection_item'),
    # access to static files
    url(r'^static/(?P<path>.*)$', static_serve, {'document_root': settings.STATIC_ROOT}),
    ]

if not settings.USE_CELERY:
  urlpatterns += [
    # temporary hack to avoid depending too much on
    # background tasks
    url(r'^houston/we_ve_got_an_update_request/$', request_for_update),
    url(r'^houston/we_ve_got_a_cleanup_request/$', request_for_cleanup),
    ]

if not settings.READ_ONLY:
  urlpatterns += [
    url(r'^accounts/new/$', user_creation),
    url(r'^accounts/auth_landing/twitter/$', user_auth_landing_twitter, name='user_auth_landing_twitter'),
    url(r'^admin/', admin.site.urls),
    # Uncomment the admin/doc line below to
    # enable admin documentation
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    ]

