from django.db import models
from django.conf import settings

class SentEmail(models.Model):
    to = models.EmailField()
    subject = models.CharField(max_length=255)
    html_message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Mail aan {self.to} op {self.sent_at.strftime('%Y-%m-%d %H:%M')}"