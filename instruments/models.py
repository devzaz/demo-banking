from django.db import models
from django.contrib.auth.models import User

class KTT(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)

    title = models.CharField(max_length=200)
    message = models.TextField(help_text="Full KTT message body")

    is_published = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"KTT — {self.customer.username}"
