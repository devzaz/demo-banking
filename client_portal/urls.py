from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="client_dashboard"),
    path(
        "funding-instructions/",
        views.funding_instructions,
        name="client_funding_instructions"
    ),
    path("statements/", views.statement_view, name="client_statements"),
    path("statements/csv/", views.statement_csv, name="statement_csv"),
    path("statements/pdf/", views.statement_pdf, name="statement_pdf"),

]