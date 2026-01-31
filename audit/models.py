from django.db import models
from django.contrib.auth.models import User

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("LOGIN", "Login"),
        ("DEPOSIT_CREATE", "Deposit Created"),
        ("DEPOSIT_RELEASE", "Deposit Released"),
        ("WIRE_STATUS", "Wire Status Updated"),
        ("INSTRUMENT_CREATE", "Instrument Created"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} — {self.created_at}"
