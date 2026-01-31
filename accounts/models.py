from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class LoginOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP for {self.user.username} - {'Used' if self.is_used else 'Unused'}"