import settings
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', 'wateronmars.views.home', name='home'),
                       # url(r'^wateronmars/', include('wateronmars.foo.urls')),
                       url(r'^public/', include('wom_river.urls')),
                       url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
                       url(r'^accounts/profile/$', 'wom_user.views.user_profile'),
                       url(r'^u/', include('wom_user.urls')),
                       
                       # Uncomment the admin/doc line below to enable admin documentation
                       # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       
                       # Uncomment the next line to enable the admin
                       url(r'^admin/', include(admin.site.urls)),
                       
                       # temporary hack to avoid depending too much on
                       # celery for background tasks
                       url(r'^houston/we_ve_got_an_update_request/$',
                           'wateronmars.views.request_for_update'),
                       url(r'^houston/we_ve_got_a_cleanup_request/$',
                           'wateronmars.views.request_for_cleanup'),
                       )


urlpatterns += patterns('',
                        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT})
)
