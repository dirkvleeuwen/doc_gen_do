from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, View
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib import messages
from django.conf import settings
from .forms import CustomUserCreationForm
from mailer.utils import send_html_email
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from .forms import EditProfileForm
from django.contrib.auth.decorators import login_not_required
from accounts.mixins import LoginNotRequiredMixin


User = get_user_model()

class RegisterView(LoginNotRequiredMixin, CreateView):
    form_class = CustomUserCreationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activation_url = self.request.build_absolute_uri(
            reverse_lazy("accounts:activate", kwargs={"uidb64": uid, "token": token})
        )
        send_html_email(
            subject="Activeer je account",
            to=user.email,
            template_name="emails/account_activation.html",
            text_template_name="emails/account_activation.txt",
            context={"user": user, "activation_url": activation_url},
        )
        send_html_email(
            subject="Nieuwe registratie wacht op goedkeuring",
            to=settings.ADMINS[0][1],
            template_name="emails/notify_admin_new_user.html",
            text_template_name="emails/notify_admin_new_user.txt",
            context={"user": user},
        )
        return response


class ActivateAccountView(LoginNotRequiredMixin, View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, "Je account is geactiveerd. Je kunt nu inloggen.")
            return redirect("accounts:login")
        else:
            messages.error(request, "De activatielink is ongeldig of verlopen.")
            return redirect("accounts:login")


class CustomLoginView(LoginNotRequiredMixin, LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("instrument_submission_list")


class CustomPasswordResetView(LoginNotRequiredMixin, PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "emails/password_reset.txt"
    html_email_template_name = "emails/password_reset.html"
    success_url = reverse_lazy("accounts:password_reset_done")


class CustomPasswordResetDoneView(LoginNotRequiredMixin, PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class CustomPasswordResetConfirmView(LoginNotRequiredMixin, PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class CustomPasswordResetCompleteView(LoginNotRequiredMixin, PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"

class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = EditProfileForm
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Je profiel is bijgewerkt.')
        return super().form_valid(form)

# enkel voor emailtests
def email_profile_info(request):
    user = request.user
    context = {"user": user}
    send_html_email(
        subject="Jouw profielinformatie",
        to=user.email,
        template_name="emails/profile_info.html",
        text_template_name="emails/profile_info.txt",
        context=context,
    )
    messages.success(request, "Je profielinformatie is naar je e-mailadres verstuurd.")
    return redirect("accounts:profile")