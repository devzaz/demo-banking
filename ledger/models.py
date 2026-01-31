from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.core.exceptions import ValidationError

class Account(models.Model):
    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP'),
    ]

    customer = models.ForeignKey(
        User,
        on_delete = models.CASCADE,
        related_name = 'accounts'
    )

    currency = models.CharField(
        max_length = 3,
        choices=CURRENCY_CHOICES
        )

    available_balance = models.DecimalField(
        max_digits = 18,
        decimal_places =2,
        default=Decimal("0.00")
    )

    transit_balance = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default = Decimal("0.00")
    )

    held_balance = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default = Decimal("0.00")
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def total_balance(self):
        return (
            self.available_balance
            + self.transit_balance
            + self.held_balance
        )
    
    def __str__(self):
        return f"{self.customer}"

    def assert_integrity(self):
        """
        Docstring for assert_integrity
        
        demo level integrity check:
        Raises error if balances are inconsistence                    
        """
        total = self.total_balance()

        if total <= Decimal('0.00'):
            raise ValidationError(
                "Total balance cannot be negative"
            )
    

    def can_withdraw(self, amount):
        return self.available_balance >= amount

class LedgerEntry(models.Model):
    ENTRY_TYPES = [
        ("deposit_pending", "Deposit (Pending)"),
        ("deposit_settled", "Deposit (Settled)"),
        ("transfer", "Transfer"),
        ("fee", "Fee"),
        ("adjustment", "Adjustment"),
    ]

    account = models.ForeignKey(
        Account,
        on_delete = models.CASCADE,
        related_name = 'ledger_entries'
    )

    amount = models.DecimalField(
        max_digits=18,
        decimal_places=2
    )

    entry_type = models.CharField(
        max_length=20,
        choices=ENTRY_TYPES
    )

    reference = models.CharField(
        max_length = 255,
        blank= True,
        null = True
    )

    created_at = models.DateTimeField(auto_now_add = True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.entry_type} - {self.amount} on {self.created_at}"
