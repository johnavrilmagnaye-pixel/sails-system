from django.urls import include, re_path

from accounts import rest_views as base_views, api as users_views
from accounts.routers import router as base_router
from crm import rest_views
from crm.routers import router as crm_router
from notifications import api as notifications_views


urlpatterns = [
    re_path(r'^deals/board/$', rest_views.DealsBoardView.as_view()),
    re_path(r'^deals/funnel/$', rest_views.DealsFunnelView.as_view()),

    re_path(r'^tasks/calendar/$', rest_views.TasksCalendarView.as_view()),

    re_path(r'^accounts/$', base_views.AccountListView.as_view(), name='account-list'),
    re_path(r'^accounts/current/$', base_views.CurrentAccountView.as_view(), name='account-current'),
    re_path(r'^accounts/switch/$', base_views.SwitchAccountView.as_view(), name='account-switch'),
    re_path(r'^accounts/create/$', base_views.CreateAccountView.as_view(), name='account-create'),
    re_path(r'^current_account/$', base_views.CurrentAccountView.as_view()),

    re_path(r'^edit_profile/$', users_views.EditProfileAPI.as_view()),
    re_path(r'^change_password/$', users_views.ChangePasswordAPI.as_view()),
    re_path(r'^resend_invite/$', users_views.ResendInviteAPI.as_view()),

    re_path(r'^notification_settings/$', notifications_views.NotificationSettingsView.as_view()),
    re_path(r'^edit_notification_settings/$', notifications_views.EditNotificationSettingsAPI.as_view()),

    re_path(r'^notifications/$', notifications_views.NotificationsView.as_view()),


    re_path(r'^options/company/$', rest_views.CompanyOptionsView.as_view()),
    re_path(r'^options/person/$', rest_views.PersonOptionsView.as_view()),
    re_path(r'^options/deal/$', rest_views.DealOptionsView.as_view()),

    re_path(r'^options/user/$', users_views.UserOptionsView.as_view()),

    re_path(r'^', include(base_router.urls)),
    re_path(r'^', include(crm_router.urls)),
]
