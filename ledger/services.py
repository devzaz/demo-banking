from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Account, LedgerEntry


def _already_processed(account, entry_type, reference):
    if not reference:
        return False
    return LedgerEntry.objects.filter(
        account = account,
        entry_type = entry_type,
        reference = reference,
    ).exists()


    


def deposit_pending(account_id, amount: Decimal, reference=""):

    """
    Deposit (Pending → Transit)
    """
    if amount <= 0:
        raise ValidationError("Amount must be positive")

    with transaction.atomic():
        account = Account.objects.select_for_update().get(pk=account_id)

        if _already_processed(account, "deposit_pending", reference):
            return  # idempotent no-op

        LedgerEntry.objects.create(
            account=account,
            amount=amount,
            entry_type="deposit_pending",
            reference=reference
        )

        account.transit_balance += amount
        account.assert_integrity()
        account.save()


def deposit_settle(account_id, amount: Decimal, reference=""):
    """Deposit (Settle → Transit ↓, Available ↑)"""
    if amount <= 0:
        raise ValidationError("Amount must be positive")

    with transaction.atomic():
        account = Account.objects.select_for_update().get(pk=account_id)

        if account.transit_balance < amount:
            raise ValidationError("Insufficient transit balance")

        if _already_processed(account, "deposit_settled", reference):
            return  # idempotent no-op

        LedgerEntry.objects.create(
            account=account,
            amount=amount,
            entry_type="deposit_settled",
            reference=reference
        )

        account.transit_balance -= amount
        account.available_balance += amount
        account.assert_integrity()
        account.save()


def deposit_settle_by_reference(account_id, reference):
    """
    Release FULL deposit by reference only
    """
    if not reference:
        raise ValidationError("Reference is required")

    with transaction.atomic():
        account = Account.objects.select_for_update().get(pk=account_id)

        # Find the original pending deposit
        entry = LedgerEntry.objects.select_for_update().filter(
            account=account,
            entry_type="deposit_pending",
            reference=reference
        ).first()

        if not entry:
            raise ValidationError("No pending deposit found for this reference")

        amount = entry.amount  # 🔒 amount is locked

        # Prevent double release
        if _already_processed(account, "deposit_settled", reference):
            raise ValidationError("Deposit already released")

        if account.transit_balance < amount:
            raise ValidationError("Transit balance corrupted")

        LedgerEntry.objects.create(
            account=account,
            amount=amount,
            entry_type="deposit_settled",
            reference=reference
        )

        account.transit_balance -= amount
        account.available_balance += amount
        account.assert_integrity()
        account.save()


def external_wire(account_id, amount: Decimal, reference=""):
    '''External Wire / Outgoing Transfer (Available ↓)'''
    if amount <= 0:
        raise ValidationError("Amount must be positive")

    with transaction.atomic():
        account = Account.objects.select_for_update().get(pk=account_id)

        if not account.can_withdraw(amount):
            raise ValidationError("Insufficient available balance")

        if _already_processed(account, "transfer", reference):
            return  # idempotent no-op

        LedgerEntry.objects.create(
            account=account,
            amount=-amount,
            entry_type="transfer",
            reference=reference
        )

        account.available_balance -= amount
        account.assert_integrity()
        account.save()


def apply_fee(account_id, fee: Decimal, reference=""):
    """Fee (Optional, Available ↓)"""
    if fee <= 0:
        raise ValidationError("Fee must be positive")

    with transaction.atomic():
        account = Account.objects.select_for_update().get(pk=account_id)

        if not account.can_withdraw(fee):
            raise ValidationError("Insufficient available balance for fee")

        if _already_processed(account, "fee", reference):
            return  # idempotent no-op

        LedgerEntry.objects.create(
            account=account,
            amount=-fee,
            entry_type="fee",
            reference=reference
        )

        account.available_balance -= fee
        account.assert_integrity()
        account.save()




from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Account, LedgerEntry


def hold_funds_for_wire(account_id, amount: Decimal, reference=""):
    """
    Move funds from AVAILABLE → HELD for wire request
    """
    if amount <= 0:
        raise ValidationError("Amount must be positive")

    with transaction.atomic():
        account = Account.objects.select_for_update().get(pk=account_id)

        if not account.can_withdraw(amount):
            raise ValidationError("Insufficient available balance")

        LedgerEntry.objects.create(
            account=account,
            amount=-amount,
            entry_type="transfer",
            reference=reference
        )

        account.available_balance -= amount
        account.held_balance += amount
        account.assert_integrity()
        account.save()




def release_wire_hold(account_id, amount: Decimal, reference=""):
    """
    Release HELD → AVAILABLE on wire rejection
    """
    if amount <= 0:
        raise ValidationError("Amount must be positive")

    with transaction.atomic():
        account = Account.objects.select_for_update().get(pk=account_id)

        if account.held_balance < amount:
            raise ValidationError("Insufficient held balance")

        LedgerEntry.objects.create(
            account=account,
            amount=amount,
            entry_type="adjustment",
            reference=reference
        )

        account.held_balance -= amount
        account.available_balance += amount
        account.assert_integrity()
        account.save()










# def increase_transit(account:Account, amount:Decimal, reference=""):
#     """
#     deposite created as HOLD -> TRANSIT increase

#     """

#     if amount <= 0:
#         raise ValidationError("Amount must be positive")
    
#     with transaction.atomic():

#         account = Account.objects.select_for_update().get(pk=account.pk)

#         LedgerEntry.objects.create(
#             account=account,
#             amount=amount,
#             entry_type = "deposit_hold",
#             reference=reference
#         )


#         account.transit_balance = Decimal(account.transit_balance) + amount
#         account.assert_integrity()
#         account.save()


# def release_transit_to_available(account: Account, amount:Decimal, reference=""):
#     """
#     release TRANSIT to AVAILABLE

#     """

#     if amount <= 0:
#         raise ValidationError("Amount must be positive")
    
    
    
#     with transaction.atomic():
#         account = Account.objects.select_for_update().get(pk=account.pk)

#         if account.transit_balance < amount:
#             raise ValidationError("Insufficient transit balance")

#         LedgerEntry.objects.create(
#             account=account,
#             amount=amount,
#             entry_type= "deposit_release",
#             reference=reference
#         )

#         account.transit_balance -= amount
#         account.available_balance += amount
#         account.assert_integrity()
#         account.save()



# def decrease_available(account:Account, amount:Decimal, reference="", entry_type="transfer"):
#     """
#     used for external wire or fees (depends)
#     """

#     if amount <= 0:
#         raise ValidationError("Amount must be positve")
    
    
#     with transaction.atomic():

#         account = Account.objects.select_for_update().get(pk=account.pk)

#         if not account.can_withdraw(amount):
#             raise ValidationError("Insufficient available balance")
        
#         LedgerEntry.objects.create(
#             account=account,
#             amount=-amount,
#             entry_type = entry_type,
#             reference=reference

#         )

#         account.available_balance -= amount
#         account.assert_integrity()
#         account.save()
