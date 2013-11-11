from django.contrib import admin

from wom_classification.models import Tag
from wom_classification.models import ClassificationData

admin.site.register(Tag)
admin.site.register(ClassificationData)
