from django.conf.urls import patterns
from django.conf.urls import url


urlpatterns = patterns('',
                       url(r'^(?P<ownername>[^/]*)/sources/opml/$', 'wom_user.views.user_upload_opml'),
                       url(r'^(?P<ownername>[^/]*)/sources/$', 'wom_river.views.user_river_sources'),
                       url(r'^(?P<ownername>[^/]*)/river/$', 'wom_river.views.user_river_view'),
                       url(r'^(?P<ownername>[^/]*)/sieve/$', 'wom_river.views.user_river_sieve'),
                       url(r'^(?P<ownername>[^/]*)/collection/$', 'wom_user.views.user_collection'),
                       )
