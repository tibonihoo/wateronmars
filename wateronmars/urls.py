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
from django.urls import include, re_path

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
    user_tributary_mastodon,
    user_tributary_mastodon_add,
    user_tributary_mastodon_auth_gateway,
    user_river_source_item,
    user_river_view,
    user_river_sieve,
    user_collection_add,
    user_collection_item,
    request_for_update,
    request_for_cleanup,
    user_creation,
    user_auth_landing_twitter,
    user_auth_landing_mastodon,
    )

from django.contrib.auth import views as auth_views
from django.views.static import serve as static_serve


urlpatterns = [
    re_path(r'^robots.txt$', get_robots_txt),
    re_path(r'^humans.txt$', get_humans_txt),
    re_path(r'^$', home, name='home'),
    re_path(r'^accounts/login/$', auth_views.LoginView.as_view(template_name='login.html'), name='user_login'),
    re_path(r'^accounts/logout/$', user_logout, name='user_logout'),
    re_path(r'^accounts/profile/$', user_profile, name='user_profile'),
    re_path(r'^u/(?P<owner_name>[^/]*)/$', user_root, name='user_root'),
    re_path(r'^u/(?P<owner_name>[^/]*)/sources/opml/$', user_upload_opml, name='user_upload_opml'),
    re_path(r'^u/(?P<owner_name>[^/]*)/collection/$', user_collection, name='user_collection'),
    re_path(r'^u/(?P<owner_name>[^/]*)/collection/nsbmk/$', user_upload_nsbmk, name='user_upload_nsbmk'),
    re_path(r'^u/(?P<owner_name>[^/]*)/sources/$', user_river_sources, name='user_river_sources'),
    re_path(r'^u/(?P<owner_name>[^/]*)/sources/add/$', user_river_source_add, name='user_river_source_add'),
    re_path(r'^u/(?P<owner_name>[^/]*)/sources/tributary/$', user_tributary, name='user_tributary'),
    re_path(r'^u/(?P<owner_name>[^/]*)/sources/tributary/twitter/$', user_tributary_twitter, name='user_tributary_twitter'),
    re_path(r'^u/(?P<owner_name>[^/]*)/sources/tributary/twitter/add/$', user_tributary_twitter_add, name='user_tributary_twitter_add'),
    re_path(r'^u/(?P<owner_name>[^/]*)/sources/tributary/mastodon/$', user_tributary_mastodon, name='user_tributary_mastodon'),
    re_path(r'^u/(?P<owner_name>[^/]*)/sources/tributary/mastodon/add/$', user_tributary_mastodon_add, name='user_tributary_mastodon_add'),
    re_path(r'^u/(?P<owner_name>[^/]*)/sources/tributary/mastodon/auth_gateway/(?P<timeline_name>.+)$', user_tributary_mastodon_auth_gateway, name='user_tributary_mastodon_auth_gateway'),
    re_path(r'^u/(?P<owner_name>[^/]*)/sources/item/(?P<source_url_code>.*)$', user_river_source_item, name='user_river_source_item'),
    re_path(r'^u/(?P<owner_name>[^/]*)/river/$', user_river_view, name='user_river_view'),
    re_path(r'^u/(?P<owner_name>[^/]*)/sieve/$', user_river_sieve, name='user_river_sieve'),
    re_path(r'^u/(?P<owner_name>[^/]*)/collection/add/$', user_collection_add, name='user_collection_add'),
    re_path(r'^u/(?P<owner_name>[^/]*)/collection/item/(?P<reference_url_code>.*)$',user_collection_item, name='user_collection_item'),
    re_path(r'^accounts/auth_landing/twitter/$', user_auth_landing_twitter, name='user_auth_landing_twitter'),
    re_path(r'^accounts/auth_landing/mastodon/$', user_auth_landing_mastodon, name='user_auth_landing_mastodon'),
    # access to static files
    re_path(r'^static/(?P<path>.*)$', static_serve, {'document_root': settings.STATIC_ROOT}),
    ]

if not settings.USE_CELERY:
  urlpatterns += [
    # temporary hack to avoid depending too much on
    # background tasks
    re_path(r'^houston/we_ve_got_an_update_request/$', request_for_update),
    re_path(r'^houston/we_ve_got_a_cleanup_request/$', request_for_cleanup),
    ]

if not settings.READ_ONLY:
  urlpatterns += [
    re_path(r'^accounts/new/$', user_creation),
    re_path(r'^admin/', admin.site.urls),
    # Uncomment the admin/doc line below to
    # enable admin documentation
    re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    ]

