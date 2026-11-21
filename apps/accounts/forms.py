from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.forms.formsets import BaseFormSet
from django.utils.encoding import smart_str
from django.utils.translation import gettext_lazy as _

from timezone_field.forms import TimeZoneFormField

from core.utils import email_admins

from accounts.models import Account, UserAccountLink
from notifications.helpers import NotificationsHelper


class CRMAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': _('Invalid email address or password.'),
        'no_cookies': _('Your browser does not support cookies.'),
        'inactive': _('This account is inactive.'),
    }

    username = forms.EmailField(label=_('Email address'), max_length=255)
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput())


class AccountCreationForm(forms.Form):
    error_messages = {
        'invalid_credentials': _('Invalid email address or password.'),
    }

    account_name = forms.CharField(label=_('Account name'), max_length=30)
    email = forms.EmailField(label=_('Email address'), max_length=255)
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput())

    user = None

    def clean_account_name(self):
        account_name = self.cleaned_data['account_name'].strip()
        if Account.all_objects.filter(name__iexact=account_name).exists():
            raise forms.ValidationError(_('An account with this name already exists.'))
        return account_name

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data['email'])
        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        if not email or not password:
            return cleaned_data

        self.user = User.objects.filter(email__iexact=email).first()
        if self.user is not None and (
                not self.user.is_active or not self.user.check_password(password)):
            raise forms.ValidationError(self.error_messages['invalid_credentials'])

        return cleaned_data


class CRMPasswordResetForm(PasswordResetForm):
    error_messages = {
        'unknown': _('No user with this email address exists.'),
    }

    email = forms.EmailField(label=_('Email address'), max_length=255)

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data['email'])
        if not User.objects.filter(is_active=True, email__iexact=email).exists():
            raise forms.ValidationError(self.error_messages['unknown'])

        return email


class SetNewPasswordForm(forms.Form):
    new_password = forms.CharField(label=_('New password'), widget=forms.PasswordInput())

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password'])

        if commit:
            self.user.save()

        return self.user


class ActivationUserProfileForm(forms.ModelForm):
    email = forms.EmailField(label=_('Email address'))
    first_name = forms.CharField(label=_('First name'), max_length=30, required=False)
    last_name = forms.CharField(label=_('Last name'), max_length=30, required=False)
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.has_usable_password():
            self.fields['password'].required = False
            self.fields['password'].help_text = _('Leave blank to keep the password for your existing account.')

    def save(self, commit=True):
        user = super().save(commit=False)

        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()

        return user


class BaseInviteUserFormset(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return

        if not any(self.cleaned_data):
            raise forms.ValidationError(_('Enter at least one email address'))

        values = set()
        for form in [form for form in self.forms if form.cleaned_data]:
            value = form.cleaned_data['email']
            if value in values:
                raise forms.ValidationError(_('The form must not contain duplicate values'))

            values.add(value)


class InviteUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, account, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.account = account

    def save(self, commit=True):
        email = User.objects.normalize_email(self.cleaned_data['email'])

        try:
            with transaction.atomic():
                user, user_created = User.objects.get_or_create(
                    email__iexact=email,
                    defaults={
                        'username': email,
                        'email': email,
                    },
                )
                if user_created:
                    user.set_unusable_password()
                    user.save(update_fields=('password',))

                user_link, created = UserAccountLink.objects.get_or_create(
                    user=user,
                    account=self.account,
                    defaults={'is_active': False, 'is_invited': True},
                )
                if not created:
                    if user_link.is_active and not user_link.is_invited:
                        return None
                    user_link.is_active = False
                    user_link.is_invited = True
                    user_link.save(update_fields=('is_active', 'is_invited', 'updated_at'))
        except IntegrityError as e:
            email_admins(
                'Integrity error in InviteUserForm',
                'Account - {}\nError message: {}'.format(
                    self.account.name,
                    smart_str(e)
                )
            )
            return

        NotificationsHelper.user_invite(self.account, user_link)

        return user_link


class UserProfileForm(forms.ModelForm):
    timezone = TimeZoneFormField()
    language = forms.ChoiceField(choices=settings.LANGUAGES)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name',)
