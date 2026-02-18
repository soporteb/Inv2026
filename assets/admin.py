from django.contrib import admin

from .models import (
    Asset,
    AssetAssignment,
    AssetEvent,
    AssetLicense,
    AssetSensitiveData,
    CameraDetails,
    ComputerSpecs,
    NetworkDeviceDetails,
    PeripheralDetails,
    PrinterDetails,
    TeleconferenceDetails,
)

admin.site.register(Asset)
admin.site.register(AssetSensitiveData)
admin.site.register(AssetAssignment)
admin.site.register(AssetEvent)
admin.site.register(AssetLicense)
admin.site.register(ComputerSpecs)
admin.site.register(PeripheralDetails)
admin.site.register(PrinterDetails)
admin.site.register(NetworkDeviceDetails)
admin.site.register(TeleconferenceDetails)
admin.site.register(CameraDetails)
