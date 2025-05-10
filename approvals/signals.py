from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import ApprovalRequest
from mailer.utils import send_html_email
from . import is_enabled

@receiver(post_save, sender=ApprovalRequest)
def notify_approval_request(sender, instance, created, **kwargs):
    """Send notifications when approval requests are created or updated"""
    # Skip if approvals functionality is disabled
    if not is_enabled():
        return
        
    if created:
        # New approval request - notify reviewers
        subject = f"Nieuw goedkeuringsverzoek voor {instance.submission.instrument}"
        template = "emails/new_approval_request.html"
        for user in get_reviewers():
            context = {
                'reviewer': user,
                'request': instance,
                'submission': instance.submission,
            }
            send_html_email(
                subject=subject,
                to=user.email,
                template_name=template,
                context=context,
                user=user
            )
    elif instance.status in ['APPROVED', 'REJECTED']:
        # Status changed - notify requester
        subject = f"Goedkeuringsverzoek {instance.get_status_display().lower()}"
        template = "emails/approval_request_status.html"
        context = {
            'request': instance,
            'submission': instance.submission,
            'user': instance.requester
        }
        send_html_email(
            subject=subject,
            to=instance.requester.email,
            template_name=template,
            context=context,
            user=instance.requester
        )

def get_reviewers():
    """Get all users who can review submissions"""
    User = get_user_model()
    return User.objects.filter(
        groups__permissions__codename='can_review_submissions'
    ).distinct()