from django.urls import path
from . import views

urlpatterns = [
    # path('login', views.login_view, name='login'),
    path('client/dashboard/', views.client_dashboard, name='client_dashboard'),
    path('backoffice/dashboard/', views.admin_dashboard, name='admin_dashboard'),
]