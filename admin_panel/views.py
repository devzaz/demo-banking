from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from ledger.models import Account
from decimal import Decimal
from transfers.models import ExternalWireRequest,Beneficiary
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



from ledger.models import Account, LedgerEntry
from audit.models import AuditLog
from django.db.models import Sum

from instruments.models import KTT

from django.db import transaction
from transfers.models import Beneficiary

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






@staff_member_required
def admin_dashboard(request):
    context = {
        "total_customers": Account.objects.values("customer").distinct().count(),
        "total_accounts": Account.objects.count(),
        "total_available": Account.objects.aggregate(
            total=Sum("available_balance")
        )["total"] or 0,
        "total_held": Account.objects.aggregate(
            total=Sum("held_balance")
        )["total"] or 0,
        "pending_wires": ExternalWireRequest.objects.filter(
            status="PENDING"
        ).count(),
        "recent_ledger": LedgerEntry.objects.order_by("-created_at")[:10],
        "recent_audits": AuditLog.objects.order_by("-created_at")[:10],
    }

    return render(request, "admin/dashboard.html", context)










# import data


@staff_member_required
def import_sample_data(request):
    if request.method == "POST":
        with transaction.atomic():

            # --------------------------------------------------
            # 1️⃣ WIPE PREVIOUS DEMO DATA (SAFE FOR DEMO)
            # --------------------------------------------------
            User.objects.filter(username__startswith="demo_client_").delete()

            # --------------------------------------------------
            # 2️⃣ CREATE DEMO USERS (20)
            # --------------------------------------------------
            users = []
            for i in range(1, 21):
                user = User(
                    username=f"demo_client_{i}",
                    email=f"demo{i}@client.com"
                )
                user.set_password("demo1234")
                users.append(user)

            User.objects.bulk_create(users)
            users = list(User.objects.filter(username__startswith="demo_client_"))

            # --------------------------------------------------
            # 3️⃣ CREATE ACCOUNTS (1 PER USER)
            # --------------------------------------------------
            accounts = []
            for user in users:
                accounts.append(Account(
                    customer=user,
                    currency="USD"
                ))

            Account.objects.bulk_create(accounts)
            accounts = list(Account.objects.all())

            # --------------------------------------------------
            # 4️⃣ CREATE BENEFICIARIES (REQUIRED FOR WIRES)
            # --------------------------------------------------
            beneficiaries = []
            for acc in accounts:
                beneficiaries.append(Beneficiary(
                    customer=acc.customer,
                    name="Demo Beneficiary",
                    bank_name="Demo External Bank",
                    account_number=f"EXT-{acc.id}",
                    country="US",
                ))

            Beneficiary.objects.bulk_create(beneficiaries)
            beneficiaries = list(Beneficiary.objects.all())

            # --------------------------------------------------
            # 5️⃣ CREATE 100 DEPOSITS (LEDGER-SAFE)
            # --------------------------------------------------
            for i in range(100):
                acc = accounts[i % len(accounts)]
                ref = f"DEMO-DEP-{i+1}"

                deposit_pending(
                    account_id=acc.id,
                    amount=Decimal("1000"),
                    reference=ref
                )
                deposit_settle(
                    account_id=acc.id,
                    amount=Decimal("1000"),
                    reference=ref
                )

            # --------------------------------------------------
            # 6️⃣ CREATE WIRE REQUESTS (30)
            # --------------------------------------------------
            wires = []
            for i, acc in enumerate(accounts[:30]):
                beneficiary = beneficiaries[i % len(beneficiaries)]

                wires.append(ExternalWireRequest(
                    customer=acc.customer,
                    account=acc,
                    beneficiary=beneficiary,
                    amount=Decimal("500"),
                    status="PENDING" if i % 2 == 0 else "APPROVED",
                    reference=f"DEMO-WIRE-{i+1}"
                ))

            ExternalWireRequest.objects.bulk_create(wires)

            # --------------------------------------------------
            # 7️⃣ CREATE KTT INSTRUMENTS (10)
            # --------------------------------------------------
            instruments = []
            for acc in accounts[:10]:
                instruments.append(KTT(
                    customer=acc.customer,
                    title="Demo KTT Instrument",
                    message=(
                        "This is a demo-generated banking instrument.\n\n"
                        "Issued by Prominence Bank for demonstration purposes."
                    )
                ))

            KTT.objects.bulk_create(instruments)

            # --------------------------------------------------
            # 8️⃣ CREATE AUDIT LOGS (200)
            # --------------------------------------------------
            logs = []
            for i in range(200):
                logs.append(AuditLog(
                    user=None,
                    action="SYSTEM",
                    description=f"Demo audit event {i+1}"
                ))

            AuditLog.objects.bulk_create(logs)

        messages.success(request, "Large-scale demo data imported successfully")
        return redirect("admin_dashboard")

    return render(request, "admin/import_confirm.html")
