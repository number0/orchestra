from django.conf.urls import url
from django.views.generic import RedirectView

from orchestra.accounts.views import OrchestraRegistrationView
from orchestra.accounts.views import AccountSettingsView


urlpatterns = [
    # We have to override the register endpoint to emit the
    # `orchestra_user_registered` signal
    url(r'^accounts/register/$',
        OrchestraRegistrationView.as_view(),
        name='registration_register'),
    url(r'^accounts/settings/$',
        AccountSettingsView.as_view(), name='account_settings'),
    url(r'^password/change/done/$',
        RedirectView.as_view(
            pattern_name='account_settings'),
        name='auth_password_change_done'),
]