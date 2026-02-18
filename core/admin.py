from django.contrib import admin

from .models import AssignmentReason, Category, Location, LocationUsage, Status

admin.site.register(Location)
admin.site.register(Category)
admin.site.register(Status)
admin.site.register(AssignmentReason)
admin.site.register(LocationUsage)
