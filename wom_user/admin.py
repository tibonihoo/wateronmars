from django.contrib import admin

from wom_user.models import UserProfile
from wom_user.models import UserBookmark
from wom_user.models import ReferenceUserStatus

admin.site.register(UserProfile)
admin.site.register(UserBookmark)
admin.site.register(ReferenceUserStatus)

