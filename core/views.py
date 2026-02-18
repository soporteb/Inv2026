from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from accounts.mixins import AdminRequiredMixin

from .forms import LocationForm
from .models import Location


class LocationListView(AdminRequiredMixin, ListView):
    model = Location
    template_name = "core/location_list.html"
    context_object_name = "locations"


class LocationCreateView(AdminRequiredMixin, CreateView):
    model = Location
    form_class = LocationForm
    template_name = "core/location_form.html"
    success_url = reverse_lazy("core:location_list")


class LocationUpdateView(AdminRequiredMixin, UpdateView):
    model = Location
    form_class = LocationForm
    template_name = "core/location_form.html"
    success_url = reverse_lazy("core:location_list")


class LocationDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        location = Location.objects.get(pk=pk)
        was_deleted = location.safe_delete()
        if was_deleted:
            messages.success(request, "Location deleted successfully.")
        else:
            messages.warning(
                request,
                "Location is referenced and was deactivated instead of deleted.",
            )
        return redirect("core:location_list")
