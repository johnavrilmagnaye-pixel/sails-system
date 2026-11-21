from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.db import models, transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone as tz
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from timezone_field import TimeZoneField

from core.models import BaseModel
from core.tasks import send_mail
from core.tokens import url_token_generator

from accounts.const import UserRole
from accounts.managers import UserAccountLinkManager


def get_user_account_name(account, user):
    return UserAccountLink(account=account, user=user).name


class Account(BaseModel):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name

    def get_owner(self):
        try:
            return UserAccountLink.objects.by_account(self).get(role=UserRole.OWNER)
        except UserAccountLink.DoesNotExist:
            return None

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
        }

    # legacy code
    @property
    def is_gta(self):
        return self.name == 'gta'

class UserAccountLink(BaseModel):
    """
    Link between a user and an account. It allows user work in different accounts and vice versa.
    It uses Django User model basic fields: email, password, first_name, last_name.
    Other fields (is_active, role, etc.) and foreign keys like permissions are added to this model
    to be able to specify it differently for different accounts.
    """

    ROLE_CHOICES = (
        (UserRole.OWNER, 'owner'),
        (UserRole.ADMIN, 'admin'),
        (UserRole.MANAGER, 'manager'),
    )

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.PositiveSmallIntegerField(verbose_name=_('Role'), choices=ROLE_CHOICES, default=UserRole.MANAGER)
    is_selected = models.BooleanField(verbose_name=_('Selected'), default=False)
    is_active = models.BooleanField(verbose_name=_('Active'), default=True)
    is_invited = models.BooleanField(verbose_name=_('Invited'), default=False)
    permissions = models.ManyToManyField(Permission, blank=True)
    timezone = TimeZoneField(
        verbose_name=_('Time zone'),
        choices_display='WITH_GMT_OFFSET',
        default=settings.TIME_ZONE,
    )
    language = models.CharField(
        verbose_name=_('Interface language'),
        max_length=10,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
    )

    objects = UserAccountLinkManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'account'),
                name='unique_user_account_link',
            ),
            models.UniqueConstraint(
                fields=('user',),
                condition=models.Q(is_selected=True),
                name='unique_selected_account_link_per_user',
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def name(self):
        if self.user.first_name or self.user.last_name:
            if not self.user.first_name:
                return self.user.last_name
            elif not self.user.last_name:
                return self.user.first_name
            return '{} {}'.format(self.user.first_name, self.user.last_name)
        return self.user.email

    @property
    def is_owner(self):
        return self.role == UserRole.OWNER

    @property
    def is_admin(self):
        return self.role in (UserRole.OWNER, UserRole.ADMIN)

    def select_link(self):
        """ Marks this link as selected for the user, unmark other links including archived accounts """
        with transaction.atomic():
            user_links = UserAccountLink.all_objects.select_for_update().filter(
                user_id=self.user_id,
            ).order_by('id')
            list(user_links.values_list('id', flat=True))

            user_links.filter(is_selected=True).update(is_selected=False)
            user_links.filter(id=self.id).update(is_selected=True)

        self.is_selected = True

    def has_perm(self, permission):
        """ Checks if the user has provided permission; admin users have all permissions """
        if self.is_admin:
            return True

        codename = getattr(permission, 'value', permission)
        return self.permissions.filter(codename=codename).exists()

    def email_user(self, email_name, context, from_email, headers=None):
        if headers is None:
            headers = {'Reply-To': settings.DEFAULT_FROM_EMAIL}

        send_mail.delay(
            render_to_string('notifications/{}/subject.txt'.format(email_name), context).strip(),
            render_to_string('notifications/{}/email.txt'.format(email_name), context),
            render_to_string('notifications/{}/email.html'.format(email_name), context),
            self.user.email,
            from_email,
            headers
        )

    # TODO: move out
    def add_notification(self, text):
        Notification = apps.get_model('notifications', 'Notification')
        Notification(account=self.account, user=self.user, text=text).save()

    def get_activation_url(self):
        return reverse('activation', kwargs={
            'uidb64': urlsafe_base64_encode(force_bytes(self.id)),
            'token': self.generate_activation_token(),
        })

    def get_activation_token_data(self):
        login_timestamp = ''
        if self.user.last_login is not None:
            login_timestamp = self.user.last_login.replace(microsecond=0, tzinfo=None)

        return '|'.join(map(str, (
            self.pk,
            self.user.password,
            login_timestamp,
            self.user.email,
            self.is_active,
            self.is_invited,
        )))

    def generate_activation_token(self):
        token_data = self.get_activation_token_data()
        return url_token_generator.make_token(token_data)

    def check_activation_token(self, token):
        token_data = self.get_activation_token_data()
        return url_token_generator.check_token(token_data, token)

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'name': self.name,
            'timezone': str(self.timezone),
            'language': self.language,
            'is_selected': self.is_selected,
            'is_active': self.is_active,
            'is_invited': self.is_invited,
            'is_owner': self.is_owner,
            'is_admin': self.is_admin,
            'role': UserRole(self.role).name.lower(),
            'permissions': [
                {'codename': codename}
                for codename in self.permissions.values_list('codename', flat=True)
            ],
        }

    def serialize_account(self):
        return {
            'id': self.account_id,
            'name': self.account.name,
            'is_selected': self.is_selected,
            'is_active': self.is_active,
            'role': self.role,
        }

    def option_serialize(self):
        return {
            'id': self.user_id,
            'text': self.name,
        }


class Intro(BaseModel):
    STEP_PROFILE = 1
    STEP_USERS = 2
    STEP_IMPORT = 3

    STEP_CHOICES = (
        (STEP_PROFILE, 'step_profile'),
        (STEP_USERS, 'step_users'),
        (STEP_IMPORT, 'step_import'),
    )

    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='intro')
    current_step = models.PositiveSmallIntegerField(choices=STEP_CHOICES, default=STEP_PROFILE)
    is_completed = models.BooleanField(default=False, db_index=True)

    def serialize(self):
        return {
            'id': self.id,
            'is_completed': self.is_completed,
            'current_step': self.current_step,
        }

    def complete(self):
        self.is_completed = True
        self.updated_at = tz.now()
        self.save(update_fields=('is_completed', 'updated_at'))

    def set_step(self, step):
        self.current_step = step
        self.updated_at = tz.now()
        self.save(update_fields=('current_step', 'updated_at'))
