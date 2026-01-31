from django.db import models

class FundingInstruction(models.Model):
    title = models.CharField(
        max_length=100,
        default = "How to wire Funds"
    )
    content = models.TextField()

    updated_at = models.DateTimeField(auto_now = True)


    def __str__(self):
        return self.title
