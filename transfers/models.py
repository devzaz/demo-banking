from django.db import models
from django.contrib.auth.models import User



class Beneficiary(models.Model):
    customer = models.ForeignKey(
        User,
        on_delete = models.CASCADE,
        related_name = "benificiaries"

    )
    name = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    country = models.CharField(max_length=50)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.name} - {self.bank_name} - {self.account_number}"
    


class ExternalWireRequest(models.Model):
    STATUS_CHOICES =  [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    customer = models.ForeignKey(
        User,
        on_delete = models.CASCADE
    )
    account = models.ForeignKey(
        "ledger.Account",
        on_delete=models.CASCADE
    )
    beneficiary = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(max_digits=18, decimal_places=2)

    reference = models.CharField(
        max_length=50,
        unique=True,
        help_text="Internal transaction reference"
    )
    status  = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"wire {self.id} - {self.status}"