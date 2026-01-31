from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import (
    Beneficiary,
    ExternalWireRequest
)
from decimal import Decimal
from ledger.services import (
    hold_funds_for_wire,
    release_wire_hold
)
import uuid
from accounts.models import LoginOTP
from django.contrib.admin.views.decorators import staff_member_required
from audit.services import log_action

DEMO_OTP = "123456"


@login_required
def beneficiary_list(request):
    beneficiaries = Beneficiary.objects.filter(customer=request.user)
    return render(request, "client/beneficiaries/list.html", {
        "beneficiaries":beneficiaries
    })



@login_required
def beneficiary_create(request):
    if request.method == "POST":
        otp = request.POST.get("otp")
        if otp != DEMO_OTP:
            return render(request, "client/beneficiaries/create.html", {
                "error": "Invalid OTP"
            })

        Beneficiary.objects.create(
            customer=request.user,
            name=request.POST.get("name"),
            bank_name=request.POST.get("bank"),
            account_number=request.POST.get("account"),
            country=request.POST.get("country"),
        )

        return redirect("transfers:client_beneficiaries")

    return render(request, "client/beneficiaries/create.html")


@staff_member_required
def admin_wire_requests(request):
    requests = ExternalWireRequest.objects.all().order_by("-created_at")
    return render(request, "admin/wires/list.html", {
        "requests": requests
    })


@staff_member_required
def admin_wire_approve(request, wire_id):
    wire = ExternalWireRequest.objects.get(id=wire_id)

    wire.status = "APPROVED"
    log_action(
        user=request.user,
        action="WIRE_STATUS",
        description=f"Wire {wire.id} marked as {wire.status}"
    )
    wire.save()
    


    return redirect("transfers:admin_wire_requests")

@staff_member_required
def admin_wire_reject(request, wire_id):
    wire = ExternalWireRequest.objects.get(id=wire_id)

    release_wire_hold(
        account_id=wire.account_id,
        amount=wire.amount,
        reference=wire.reference
    )

    wire.status = "REJECTED"
    log_action(
        user=request.user,
        action="WIRE_STATUS",
        description=f"Wire {wire.id} marked as {wire.status}"
    )
    wire.save()

    return redirect("transfers:admin_wire_requests")


@login_required
def wire_request_create(request):
    beneficiaries = Beneficiary.objects.filter(customer = request.user)


    if request.method == "POST":
        account_id = request.POST.get("account_id")
        amount = Decimal(request.POST.get("amount"))
        reference = f"WIRE-{uuid.uuid4().hex[:8]}"

        hold_funds_for_wire(
            account_id=account_id,
            amount=amount,
            reference=reference
        )

        ExternalWireRequest.objects.create(
            customer=request.user,
            account_id=account_id,
            beneficiary_id=request.POST.get("beneficiary_id"),
            amount=amount,
            reference=reference,
            status="PENDING"
        )

        return redirect("transfers:client_wire_requests")
    
    return render(request, "client/wires/create.html", {
        "beneficiaries": beneficiaries,
        "accounts": request.user.accounts.all()
    })


@login_required
def wire_requests_list(request):
    requests = ExternalWireRequest.objects.filter(customer=request.user)
    return render(request, "client/wires/list.html", {
        "requests": requests
    })