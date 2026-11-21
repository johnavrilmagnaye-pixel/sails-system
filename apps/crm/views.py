import mimetypes

from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.views.generic import TemplateView

from core.decorators import admin_required

from accounts.models import UserAccountLink
from crm.forms import ExportForm
from crm.mixins import CompletedIntroRequiredMixin
from crm.models import Upload


class AppTemplateView(CompletedIntroRequiredMixin, TemplateView):
    template_name = 'crm/app.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        timezone_field = UserAccountLink._meta.get_field('timezone')
        context['timezone_options'] = [
            {'id': str(value), 'text': str(label)}
            for value, label in timezone_field.choices
        ]
        return context


class IntroTemplateView(TemplateView):
    template_name = 'crm/app.html'

    def get(self, request, *args, **kwargs):
        if request.account.intro.is_completed:
            return redirect(reverse('companies'))

        return super().get(self, request, *args, **kwargs)


@login_required()
@admin_required()
def export_items(request, model_name):
    return render(request, 'crm/includes/modal_forms/export.html', {
        'form': ExportForm(),
        'model_name': model_name}
    )


@login_required()
def download_upload(request, upload_id):
    try:
        upload = Upload.objects.by_account(request.account).get(id=upload_id)
    except Upload.DoesNotExist:
        raise Http404

    try:
        content_type, encoding = mimetypes.guess_type(upload.name)
    except:
        response = HttpResponse(upload.file.file)
    else:
        response = HttpResponse(upload.file.file, content_type=content_type)

    response['Content-Disposition'] = 'attachment; filename="{}"'.format(upload.name).encode('utf-8')
    return response
