from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def login_view(request):
    return render(request, 'shared/base_auth.html')

@login_required
def client_dashboard(request):
    return render(request, 'client/base_client.html')


@login_required
def admin_dashboard(request):
    return render(request, 'admin/base_admin.html')
