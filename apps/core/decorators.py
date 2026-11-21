from django.shortcuts import render


def user_passes_test_with_403(test_func):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request):
                return view_func(request, *args, **kwargs)

            resp = render(request, '403.html')
            resp.status_code = 403

            return resp
        return _wrapped_view
    return decorator


def admin_required():
    return user_passes_test_with_403(lambda request: bool(
        getattr(request, 'user_link', None) and request.user_link.is_admin
    ))


def owner_required():
    return user_passes_test_with_403(lambda request: bool(
        getattr(request, 'user_link', None) and request.user_link.is_owner
    ))


def receiver_multiple(signal, sender, dispatch_uid_prefix, **kwargs):
    def decorator(func):
        for model in sender:
            signal.connect(func, sender=model, dispatch_uid=dispatch_uid_prefix+'_'+model.__name__, **kwargs)
        return func
    return decorator
