from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from notifications.models import Notification


@login_required()
def hide_notification(request, notification_id):
    try:
        notification = Notification.objects.by_account(request.account).get(user=request.user, id=notification_id)
    except Notification.DoesNotExist:
        return JsonResponse({'success': False})

    notification.is_read = True
    notification.save(update_fields=('is_read',))

    return JsonResponse({'success': True})


@login_required()
def hide_all_notification(request):
    Notification.objects.by_account(request.account).filter(
        user_id=request.user.id,
        is_read=False
    ).update(
        is_read=True
    )
    return JsonResponse({'success': True})
