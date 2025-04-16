from django.contrib.auth.backends import ModelBackend

class ApprovedUserBackend(ModelBackend):
    def user_can_authenticate(self, user):
        is_active = super().user_can_authenticate(user)
        return is_active and getattr(user, "is_approved", False)
