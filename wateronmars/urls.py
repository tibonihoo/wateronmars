import settings
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', 'wom_user.views.home', name='home'),
                       url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
                       url(r'^accounts/profile/$', 'wom_user.views.user_profile'),
                       url(r'^u/', include('wom_user.urls')),
                       
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

