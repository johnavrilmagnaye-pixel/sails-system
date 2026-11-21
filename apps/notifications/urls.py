from django.urls import re_path

from notifications.views import hide_all_notification, hide_notification


urlpatterns = [
    re_path(r'^notifications/(?P<notification_id>\d+)/hide/$', hide_notification, name='hide_notification'),
    re_path(r'^notifications/hide_all/$', hide_all_notification, name='hide_all_notification'),
]
