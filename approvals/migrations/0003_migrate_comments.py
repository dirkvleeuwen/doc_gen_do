from django.db import migrations

def migrate_comments(apps, schema_editor):
    ApprovalRequest = apps.get_model('approvals', 'ApprovalRequest')
    for request in ApprovalRequest.objects.all():
        if hasattr(request, 'comment'):  # Check if old field exists
            if request.status == 'PENDING':
                request.request_comment = request.comment
            else:
                request.review_comment = request.comment
            request.save()

def reverse_migrate(apps, schema_editor):
    ApprovalRequest = apps.get_model('approvals', 'ApprovalRequest')
    for request in ApprovalRequest.objects.all():
        if request.status == 'PENDING':
            request.comment = request.request_comment
        else:
            request.comment = request.review_comment
        request.save()

class Migration(migrations.Migration):
    dependencies = [
        ('approvals', '0002_split_approval_comments'),
    ]

    operations = [
        migrations.RunPython(migrate_comments, reverse_migrate),
    ]