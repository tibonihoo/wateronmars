from django.contrib import admin

from wom_river.models import FeedSource
from wom_river.models import ReferenceUserStatus

admin.site.register(FeedSource)
admin.site.register(ReferenceUserStatus)
