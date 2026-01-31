
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("accounts.urls")),
    path('demo/', include('demo.urls')),
    path("backoffice/", include("admin_panel.urls")),
    path("client/", include("client_portal.urls")),
    path("client/", include("transfers.urls")),
    path("", include("instruments.urls")),
    path("", include("audit.urls")),




]
