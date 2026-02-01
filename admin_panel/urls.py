from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("customers/", views.customer_list, name="admin_customer_list"),
    path("customers/create/", views.customer_create, name="admin_customer_create"),
    path(
        "customers/<int:customer_id>/accounts/create/",
        views.account_create,
        name="admin_account_create"
    ),
    path("accounts/", views.account_list, name="admin_account_list"),
    path("deposits/create/", views.deposit_create, name="admin_deposit_create"),
    path(
        "accounts/<int:account_id>/deposit/release/",
        views.deposit_release,
        name="admin_deposit_release"
    ),

    path(
        "funding-instructions/",
        views.funding_instruction_edit,
        name="admin_funding_instruction"
    ),

    path("import-sample-data/", views.import_sample_data, name="admin_import_sample_data"),



]
