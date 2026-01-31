from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from .models import AuditLog

@staff_member_required
def audit_log_list(request):
    logs = AuditLog.objects.select_related("user").order_by("-created_at")[:500]

    return render(request, "admin/audit/list.html", {
        "logs": logs
    })
