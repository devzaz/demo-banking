from django.urls import path
from . import views

app_name = "transfers"

urlpatterns = [
    # CLIENT
    path("beneficiaries/", views.beneficiary_list, name="client_beneficiaries"),
    path("beneficiaries/add/", views.beneficiary_create, name="client_add_beneficiary"),
    path("wires/", views.wire_requests_list, name="client_wire_requests"),
    path("wires/create/", views.wire_request_create, name="client_wire_create"),

    # ADMIN
    path("admin/wires/", views.admin_wire_requests, name="admin_wire_requests"),
    path("admin/wires/<int:wire_id>/approve/", views.admin_wire_approve, name="admin_wire_approve"),
    path("admin/wires/<int:wire_id>/reject/", views.admin_wire_reject, name="admin_wire_reject"),
]