from django.contrib import admin

from .models import Asset, AssetAssignment, AssetEvent

admin.site.register(Asset)
admin.site.register(AssetAssignment)
admin.site.register(AssetEvent)
