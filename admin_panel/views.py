from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from ledger.models import Account
from decimal import Decimal
from transfers.models import ExternalWireRequest
from ledger.services import (
    deposit_pending,
    deposit_settle,
    deposit_settle_by_reference
)
from ledger.models import (
    LedgerEntry
)

from .models import FundingInstruction
from audit.services import log_action



@staff_member_required
def customer_list(request):
    customers = User.objects.filter(is_staff=False)
    context = {
        'customers':customers
    }
    return render(request, "admin/customers/list.html", context)

@staff_member_required
def customer_create(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("admin_customer_create")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=False
        )

        messages.success(request, "Customer created successfully")
        return redirect("admin_customer_list")

    return render(request, "admin/customers/create.html")


@staff_member_required
def account_create(request, customer_id):
    customer = User.objects.get(id=customer_id)

    if request.method == "POST":
        currency = request.POST.get("currency")

        Account.objects.create(
            customer=customer,
            currency=currency
        )

        messages.success(request, "Account created successfully")
        return redirect("admin_customer_list")

    return render(request, "admin/accounts/create.html", {
        "customer": customer
    })


@staff_member_required
def account_list(request):
    accounts = Account.objects.select_related("customer").all()
    return render(request, "admin/accounts/list.html", {
        "accounts": accounts
    })



@staff_member_required
def deposit_create(request):
    accounts = Account.objects.select_related("customer").all()

    if request.method == "POST":
        account_id = request.POST.get("account_id")
        amount = Decimal(request.POST.get("amount"))
        reference = request.POST.get("reference")


        deposit_pending(
            account_id = account_id,
            amount = amount,
            reference = reference
        )
        

        log_action(
            user=request.user,
            action="DEPOSIT_CREATE",
            description=f"Deposit created for account {account_id}, amount {amount}"
        )

        messages.success(request, "Deposit created as HELD (Transit)")
        return redirect("admin_account_list")

    return render(request, "admin/deposits/create.html",{
        "accounts":accounts
    })

@staff_member_required
def deposit_release(request, account_id):
    account = get_object_or_404(Account, id = account_id)
    ledger = LedgerEntry.objects.filter(account=account).first()
    amount = Decimal(ledger.amount)



    if request.method == "POST":
        reference = request.POST.get("reference")

        deposit_settle_by_reference(
            account_id=account.id,
            reference=reference
        )
        log_action(
            user=request.user,
            action="DEPOSIT_RELEASE",
            description=f"Deposit released for account {account.id}, reference {reference}"
        )

        messages.success(request, "Deposit Released successfully")
        return redirect("admin_account_list")

    return render(request, "admin/deposits/release.html",{
        "account":account,
        "amount":amount
    })


@staff_member_required
def funding_instruction_edit(request):
    instruction, _ = FundingInstruction.objects.get_or_create(id=1)

    if request.method == "POST":
        instruction.content = request.POST.get("content")
        instruction.save()
        messages.success(request, "Funding instruction updated")

        return redirect("admin_funding_instruction")


    return render(request, "admin/funding/edit.html", {
        "instruction":instruction
    })