# accounts/mixins.py

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_not_required

class LoginNotRequiredMixin:
    @method_decorator(login_not_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)