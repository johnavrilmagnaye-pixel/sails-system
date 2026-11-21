from django.contrib.auth import views as django_auth_views
from django.urls import re_path, reverse_lazy

from accounts.forms import CRMPasswordResetForm, SetNewPasswordForm
from accounts import views as accounts_views


def get_auth_urls(redirect_to):
    return [
        re_path(r'^$', accounts_views.login, {'redirect_to': redirect_to}, name='login'),
        re_path(r'^logout/$', django_auth_views.logout_then_login, name='logout'),

        re_path(r'^password_reset/$', accounts_views.CRMPasswordResetView.as_view(
                email_template_name='accounts/password_reset_email.html',
                form_class=CRMPasswordResetForm,
                subject_template_name='accounts/password_reset_subject.txt',
                success_url=reverse_lazy('password_reset_done'),
                template_name='accounts/password_reset_form.html'
            ), name='password_reset'
                ),
        re_path(r'^password_reset/done/$', accounts_views.login, {
                'redirect_to': redirect_to,
                'extra_context': {'reset_password_done': True}
            }, name='password_reset_done'
                ),
        re_path(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
            django_auth_views.PasswordResetConfirmView.as_view(
                form_class=SetNewPasswordForm,
                template_name='accounts/password_reset_confirm.html',
                success_url=reverse_lazy('password_reset_complete')
            ), name='password_reset_confirm'
        ),
        re_path(r'^password_reset/complete/$', accounts_views.login, {
                'redirect_to': redirect_to,
                'extra_context': {'reset_password_complete': True}
            }, name='password_reset_complete'
                ),

        re_path(r'^activation/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$', accounts_views.activation, name='activation')
    ]
