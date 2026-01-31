from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import KTT
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from audit.services import log_action


@staff_member_required
def admin_ktt_create(request):
    customers = User.objects.all()

    if request.method == "POST":
        KTT.objects.create(
            customer_id=request.POST.get("customer_id"),
            title=request.POST.get("title"),
            message=request.POST.get("message"),
            is_published=True
        )
        log_action(
            user=request.user,
            action="INSTRUMENT_CREATE",
            description=f"KTT created for customer {request.POST.get("customer_id")}"
        )


        messages.success(request, "KTT created and published")
        return redirect("instruments:admin_ktt_create")

    return render(request, "admin/instruments/ktt_create.html", {
        "customers": customers
    })




@login_required
def client_ktt_list(request):
    instruments = KTT.objects.filter(
        customer=request.user,
        is_published=True
    ).order_by("-created_at")

    return render(request, "client/instruments/ktt_list.html", {
        "instruments": instruments
    })


@login_required
def client_ktt_detail(request, ktt_id):
    ktt = KTT.objects.get(
        id=ktt_id,
        customer=request.user,
        is_published=True
    )

    return render(request, "client/instruments/ktt_detail.html", {
        "ktt": ktt
    })
