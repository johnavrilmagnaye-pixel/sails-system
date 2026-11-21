import datetime as dt

from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.models import Notification


class NotificationsView(APIView):
    def get(self, request):
        notifications = Notification.objects.by_account(request.account).filter(
            is_read=False,
            user_id=request.user.id
        )

        return Response([notification.serialize() for notification in notifications])


class NotificationSettingsView(APIView):
    def get(self, request):
        return Response(request.user_link.notification_settings.serialize())


class EditNotificationSettingsAPI(APIView):
    def post(self, request):
        data = request.data
        notification_settings = request.user_link.notification_settings

        remind_task_before_hours = int(data.get('remind_task_before_hours', 0))
        remind_task_before_minutes = int(data.get('remind_task_before_minutes', 0))
        notification_settings.remind_task_before = dt.timedelta(
            hours=remind_task_before_hours,
            minutes=remind_task_before_minutes
        )

        notification_settings.notify_item_responsibles = data.get('notify_item_responsibles', {
            'company': False,
            'person': False,
            'deal': False,
            'task': False,
        })

        for field_name in (
            'remind_task', 'notify_task_completed',
            'notify_company_note', 'notify_person_note', 'notify_deal_note', 'notify_task_note'
        ):
            setattr(notification_settings, field_name, data.get(field_name, False))

        notification_settings.save()

        return Response(notification_settings.serialize())
