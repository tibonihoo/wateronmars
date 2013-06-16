from django.conf.urls import patterns
from django.conf.urls import url


urlpatterns = patterns('',
                       url(r'^(?P<owner_name>[^/]*)/sources/opml/$', 'wom_user.views.user_upload_opml'),
                       url(r'^(?P<owner_name>[^/]*)/collection/$', 'wom_user.views.user_collection'),
                       url(r'^(?P<owner_name>[^/]*)/sources/$', 'wom_river.views.user_river_sources'),
                       url(r'^(?P<owner_name>[^/]*)/river/$', 'wom_river.views.user_river_view'),
                       url(r'^(?P<owner_name>[^/]*)/sieve/$', 'wom_river.views.user_river_sieve'),
                       url(r'^(?P<owner_name>[^/]*)/collection/add/$','wom_user.views.user_collection_add')
                       )
