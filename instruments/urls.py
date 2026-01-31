from django.urls import path
from . import views

app_name = "instruments"

urlpatterns = [
    path("backoffice/ktt/create/", views.admin_ktt_create, name="admin_ktt_create"),


    path("client/ktt/", views.client_ktt_list, name="client_ktt_list"),
    path("client/ktt/<int:ktt_id>/", views.client_ktt_detail, name="client_ktt_detail"),
]
