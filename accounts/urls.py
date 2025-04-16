from django.urls import path
from accounts.views import (
    RegisterView, ActivateAccountView, CustomLoginView, CustomLogoutView,
    CustomPasswordResetView, CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView, CustomPasswordResetCompleteView,
    email_profile_info # enkel voor emailtests
)
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from accounts.views import EditProfileView


app_name = "accounts"

urlpatterns = [
    
    path("activate/<uidb64>/<token>/", ActivateAccountView.as_view(), name="activate"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("password_reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path("register/", RegisterView.as_view(), name="register"),
    path("password_reset/done/", CustomPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", CustomPasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path("profile/", TemplateView.as_view(template_name="accounts/profile.html"), name="profile"),
    path("profile/edit/", EditProfileView.as_view(), name="edit_profile"),
    path("email-profile-info/", email_profile_info, name="email_profile_info"), # enkel voor emailtests
]




