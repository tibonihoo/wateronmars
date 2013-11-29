import settings
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', 'wom_user.views.home', name='home'),
                       url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
                       url(r'^accounts/profile/$', 'wom_user.views.user_profile'),
                       url(r'^u/(?P<owner_name>[^/]*)/sources/opml/$', 'wom_user.views.user_upload_opml'),
                       url(r'^u/(?P<owner_name>[^/]*)/collection/$', 'wom_user.views.user_collection'),
                       url(r'^u/(?P<owner_name>[^/]*)/collection/nsbmk/$', 'wom_user.views.user_upload_nsbmk'),
                       url(r'^u/(?P<owner_name>[^/]*)/sources/$', 'wom_user.views.user_river_sources'),
                       url(r'^u/(?P<owner_name>[^/]*)/sources/add/$', 'wom_user.views.user_river_source_add'),
                       url(r'^u/(?P<owner_name>[^/]*)/sources/remove/$', 'wom_user.views.user_river_source_remove'),
                       url(r'^u/(?P<owner_name>[^/]*)/river/$', 'wom_user.views.user_river_view'),
                       url(r'^u/(?P<owner_name>[^/]*)/sieve/$', 'wom_user.views.user_river_sieve'),
                       url(r'^u/(?P<owner_name>[^/]*)/collection/add/$','wom_user.views.user_collection_add'),
                       # access to static files
                       url(r'^static/(?P<path>.*)$',
                           'django.views.static.serve',
                           {'document_root': settings.STATIC_ROOT})
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
  
if not settings.DEMO:
  urlpatterns += patterns('',
                          url(r'^accounts/new/$',
                              'wom_user.views.user_creation'),
                          url(r'^admin/',
                              include(admin.site.urls)),
                          # Uncomment the admin/doc line below to
                          # enable admin documentation
                          url(r'^admin/doc/',
                              include('django.contrib.admindocs.urls')),
                        )

