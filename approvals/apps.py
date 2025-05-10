from django.apps import AppConfig
from django.conf import settings


class ApprovalsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'approvals'

    def ready(self):
        # Controleer of de approvals functionaliteit is ingeschakeld
        if not getattr(settings, 'ENABLE_APPROVALS', True):
            return
            
        # Import signals
        import approvals.signals

        # Add default permissions
        from django.db.models.signals import post_migrate
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        def create_permissions(sender, **kwargs):
            from django.contrib.auth.models import Group
            
            # Create the reviewer group if it doesn't exist
            reviewer_group, created = Group.objects.get_or_create(name='Reviewers')
            
            # Get content type for our model
            content_type = ContentType.objects.get_for_model(sender.get_model('ApprovalRequest'))
            
            # Create custom permissions
            permissions = [
                ('can_review_submissions', 'Can review submission approval requests'),
            ]
            
            for codename, name in permissions:
                permission, created = Permission.objects.get_or_create(
                    codename=codename,
                    name=name,
                    content_type=content_type,
                )
                
                # Add permission to reviewer group
                reviewer_group.permissions.add(permission)

        post_migrate.connect(create_permissions, sender=self)