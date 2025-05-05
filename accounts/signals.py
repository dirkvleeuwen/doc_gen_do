from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.template.loader import render_to_string
import logging
logger = logging.getLogger(__name__)
from mailer.utils import send_html_email
from accounts.models import CustomUser

# Cache voor activatiecontrole
_user_was_inactive = {}
_user_approval_changed = {}

@receiver(pre_save, sender=CustomUser)
def cache_user_active_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = CustomUser.objects.get(pk=instance.pk)
            _user_was_inactive[instance.pk] = not old.is_active and instance.is_active
        except CustomUser.DoesNotExist:
            _user_was_inactive[instance.pk] = False

@receiver(post_save, sender=CustomUser)
def notify_user_upon_activation(sender, instance, created, **kwargs):
    if not created and _user_was_inactive.get(instance.pk, False):
        send_html_email(
            subject="Je account is geactiveerd",
            to=instance.email,
            template_name="emails/account_activated.html",
            text_template_name="emails/account_activated.txt",
            context={"user": instance},
            user=instance,
        )
        if settings.ADMINS:
            send_html_email(
                subject=f"Account geactiveerd: {instance.initials}",
                to=settings.ADMINS[0][1],
                template_name="emails/notify_admin_activated.html",
                text_template_name="emails/notify_admin_activated.txt",
                context={"user": instance},
            )
        else:
            logger.warning(
                "Geen ADMINS ingesteld; admin-notificatie geactiveerd account %r overgeslagen",
                instance.pk,
            )
        _user_was_inactive.pop(instance.pk, None)


@receiver(pre_save, sender=CustomUser)
def cache_approval_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            _user_approval_changed[instance.pk] = (
                not old.is_approved and instance.is_approved
            )
        except sender.DoesNotExist:
            _user_approval_changed[instance.pk] = False


@receiver(post_save, sender=CustomUser)
def notify_user_upon_approval(sender, instance, **kwargs):
    if _user_approval_changed.pop(instance.pk, False):
        send_html_email(
            subject="Je account is goedgekeurd",
            to=instance.email,
            template_name="emails/account_approved.html",
            text_template_name="emails/account_approved.txt",
            context={"user": instance},
            user=instance,
        )
        if settings.ADMINS:
            send_html_email(
                subject=f"Account goedgekeurd: {instance.initials}",
                to=settings.ADMINS[0][1],
                template_name="emails/notify_admin_approved.html",
                text_template_name="emails/notify_admin_approved.txt",
                context={"user": instance},
            )
        else:
            logger.warning(
                "Geen ADMINS ingesteld; admin-notificatie goedgekeurd account %r overgeslagen",
                instance.pk,
            )