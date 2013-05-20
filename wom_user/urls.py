from django.conf.urls import patterns
from django.conf.urls import url


urlpatterns = patterns('',
                       url(r'^.*/opml/$', 'wom_user.views.user_upload_opml'),
                       url(r'^.*/sources/$', 'wom_river.views.user_river_sources'),
                       url(r'^.*/river/$', 'wom_river.views.user_river_view'),
                       url(r'^.*/sieve/$', 'wom_river.views.user_river_sieve'),
                       url(r'^.*/collection/$', 'wom_user.views.user_collection'),
                       )
