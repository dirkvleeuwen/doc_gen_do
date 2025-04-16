from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from mailer.models import SentEmail
from pathlib import Path

def send_html_email(subject, to, template_name, context=None, user=None, attachments=None, text_template_name=None):
    context = context or {}
    html_body = render_to_string(template_name, context)
    
    if text_template_name:
        plain_body = render_to_string(text_template_name, context)
    else:
        plain_body = "Deze e-mail ondersteunt geen HTML."

    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    msg.attach_alternative(html_body, "text/html")

    if attachments:
        for attachment in attachments:
            filename, content, mimetype = attachment
            msg.attach(filename, content, mimetype)

    msg.send()

    SentEmail.objects.create(
        subject=subject,
        to=to,
        html_message=html_body,
        user=user,
    )

def send_plain_email(subject, to, plain_body, user=None):
    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )

    msg.send()

    SentEmail.objects.create(
        subject=subject,
        to=to,
        html_message=plain_body,
        user=user,
    )

def send_instrument_export_email(user, submission, export_type, attachment_filename, attachment_content, attachment_mimetype, body=None):
    context = {
        "submission": submission,
        "user": user,
        "instrument": submission.instrument,
        "subject": submission.subject,
        "body": body,
    }

    attachments = None
    if attachment_filename and attachment_content and attachment_mimetype:
        attachments = [(attachment_filename, attachment_content, attachment_mimetype)]

    subject = f"Informatie over {submission.instrument} '{submission.subject}'"

    if export_type == "txt":
        send_plain_email(
            subject=subject,
            to=user.email,
            plain_body=body,
            user=user
        )
    else:
        send_html_email(
            subject=subject,
            to=user.email,
            template_name="emails/export_email_body.html",
            context=context,
            user=user,
            attachments=attachments
        )