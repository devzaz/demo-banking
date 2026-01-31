from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('otp/', views.otp_verify, name='otp_verify'),
    path("logout/", views.logout_view, name="logout"),
]
