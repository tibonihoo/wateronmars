from django.conf.urls import patterns
from django.conf.urls import url


urlpatterns = patterns('wom_river.views',
                       url(r'^river$', 'public_river_view'),
                       url(r'^sources$', 'public_river_sources'),      
                       )
