from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import PasswordResetView
from django.db import transaction
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.i18n import set_language as django_set_language

from accounts.models import UserAccountLink
from accounts.helpers import AccountHelper
from accounts.forms import AccountCreationForm, CRMAuthenticationForm, ActivationUserProfileForm


def set_language(request):
    response = django_set_language(request)
    language = request.POST.get('language')
    user_link = getattr(request, 'user_link', None)
    if user_link and language in dict(settings.LANGUAGES):
        user_link.language = language
        user_link.save(update_fields=('language', 'updated_at'))
    return response


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request, redirect_to=None, extra_context=None):
    redirect_to = request.GET.get('next', redirect_to)
    user = None

    action = request.POST.get('action')
    login_form = CRMAuthenticationForm(data=request.POST or None if action == 'login' else None, prefix='login')
    signup_form = AccountCreationForm(data=request.POST or None if action == 'signup' else None, prefix='signup')

    if action == 'login' and login_form.is_valid():
        user = login_form.get_user()
    elif action == 'signup' and signup_form.is_valid():
        create_kwargs = {
            'name': signup_form.cleaned_data['account_name'],
        }
        if signup_form.user is not None:
            create_kwargs['user'] = signup_form.user
        else:
            create_kwargs.update({
                'email': signup_form.cleaned_data['email'],
                'password': signup_form.cleaned_data['password'],
            })
        account = AccountHelper.create(**create_kwargs)
        user = account.get_owner().user

    if user:
        auth_login(request, user)
        return redirect(redirect_to)

    request.session.set_test_cookie()

    context = {
        'form': login_form,
        'signup_form': signup_form,
        'show_signup': action == 'signup',
        'next': redirect_to
    }

    if extra_context is not None:
        context.update(extra_context)

    return render(request, 'accounts/login.html', context)


def activation(request, uidb64=None, token=None):
    try:
        link_id = urlsafe_base64_decode(uidb64)
        user_link = UserAccountLink.objects.select_related('user', 'account').get(pk=link_id)
    except (TypeError, ValueError, OverflowError, UserAccountLink.DoesNotExist):
        user_link = None

    if user_link is not None and user_link.is_invited and user_link.check_activation_token(token):
        is_link_valid = True
        user = user_link.user

        form = ActivationUserProfileForm(data=request.POST or None, instance=user)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                user_link.is_active = True
                user_link.is_invited = False
                user_link.save(update_fields=('is_active', 'is_invited', 'updated_at'))
                user_link.select_link()
                auth_login(request, user)

            for admin in UserAccountLink.objects.active().admins().filter(
                    account=user_link.account).exclude(user_id=user.id):
                admin.add_notification(
                    mark_safe(_('User ({name}) joined the account').format(name=user_link.name))
                )

            return redirect(reverse('companies', urlconf='crm.urls'))
    else:
        is_link_valid = False
        form = None

    return render(request, 'accounts/activation.html', {
        'is_link_valid': is_link_valid,
        'form': form
    })


class CRMPasswordResetView(PasswordResetView):
    def form_valid(self, form):
        self.extra_email_context = {
            'account_url': self.request.build_absolute_uri('/').rstrip('/')
        }

        return super().form_valid(form)



from functools import partial, wraps

from django.contrib.auth.decorators import login_required
from django.forms.formsets import formset_factory
from django.http import JsonResponse
from django.shortcuts import render

from core.decorators import admin_required

from accounts.forms import InviteUserForm, BaseInviteUserFormset


@login_required()
@admin_required()
def invite_user(request):
    account = request.account

    allowed_users_number = 10 # Default for now

    # http://stackoverflow.com/questions/622982/django-passing-custom-form-parameters-to-formset
    formset_cls = formset_factory(
        wraps(InviteUserForm)(partial(InviteUserForm, account=account)),
        formset=BaseInviteUserFormset,
        extra=allowed_users_number,
        max_num=allowed_users_number
    )

    formset = formset_cls(data=request.POST or None)
    if formset.is_valid():
        users = []
        for form in formset:
            if not form.cleaned_data:
                continue

            new_user = form.save()
            if not new_user:
                continue

            users.append(new_user)

        return JsonResponse({
            'success': True,
            'users': [user.serialize() for user in users]
        })

    return render(request, 'crm/includes/modal_forms/settings/invite_user.html', {
        'formset': formset,
        'allowed_users_number': allowed_users_number
    })
