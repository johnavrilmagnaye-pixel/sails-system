from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import JavaScriptCatalog
from django.urls import re_path, include, reverse_lazy

from accounts import views as accounts_views
from accounts.urls import get_auth_urls
from crm import views as crm_views
from crm import rest_views


urlpatterns = [
    re_path(r'^i18n/setlang/$', accounts_views.set_language, name='set_language'),
    re_path(r'^i18n/', include('django.conf.urls.i18n')),
    re_path(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    re_path(r'^', include(get_auth_urls(reverse_lazy('companies')))),
    re_path(r'^', include('notifications.urls')),

    re_path(r'^intro/$', crm_views.AppTemplateView.as_view(), name='intro'),
    re_path(r'^dashboard/$', crm_views.AppTemplateView.as_view(), name='dashboard'),
    re_path(r'^notifications/$', crm_views.AppTemplateView.as_view(), name='notifications'),

    re_path(r'^companies/$', crm_views.AppTemplateView.as_view(), name='companies'),
    re_path(r'^persons/$', crm_views.AppTemplateView.as_view(), name='persons'),
    re_path(r'^deals/$', crm_views.AppTemplateView.as_view(), name='deals'),
    re_path(r'^tasks/$', crm_views.AppTemplateView.as_view(), name='tasks'),

    re_path(r'^companies/(?P<company_id>\d+)/$', crm_views.AppTemplateView.as_view(), name='company'),
    re_path(r'^persons/(?P<person_id>\d+)/$', crm_views.AppTemplateView.as_view(), name='person'),
    re_path(r'^deals/(?P<deal_id>\d+)/$', crm_views.AppTemplateView.as_view(), name='deal'),
    re_path(r'^tasks/(?P<task_id>\d+)/$', crm_views.AppTemplateView.as_view(), name='task'),

    re_path(r'^settings/$', crm_views.AppTemplateView.as_view(), name='settings'),
    re_path(r'^settings/profile/$', crm_views.AppTemplateView.as_view(), name='profile'),
    re_path(r'^settings/users/$', crm_views.AppTemplateView.as_view(), name='users'),
    re_path(r'^settings/company_fields/$', crm_views.AppTemplateView.as_view(), name='company_fields'),
    re_path(r'^settings/person_fields/$', crm_views.AppTemplateView.as_view(), name='person_fields'),
    re_path(r'^settings/deal_fields/$', crm_views.AppTemplateView.as_view(), name='deal_fields'),
    re_path(r'^settings/task_fields/$', crm_views.AppTemplateView.as_view(), name='task_fields'),
    re_path(r'^settings/tags/$', crm_views.AppTemplateView.as_view(), name='tags'),
    re_path(r'^settings/contacts_imports/$', crm_views.AppTemplateView.as_view(), name='contacts_import'),

    re_path(r'^upload/(?P<upload_id>\d+)/download/$', crm_views.download_upload, name='download_upload'),

    re_path(r'^(?P<model_name>(company|person|deal|task))/export/$', crm_views.export_items, name='export_items'),

    # base views
    re_path(r'^user/invite/$', accounts_views.invite_user, name='invite_user'),

    re_path(r'^user/(?P<user_id>\d+)/change_status/$', rest_views.change_user_status, name='change_user_status'),
    re_path(r'^user/(?P<user_id>\d+)/change_role/$', rest_views.change_user_role, name='change_user_role'),
    re_path(r'^user/(?P<user_id>\d+)/make_owner/$', rest_views.make_owner, name='make_owner'),

    re_path(r'^update_deal_stages_positions/$', rest_views.update_deal_stages_positions, name='update_deal_stages_positions'),

    re_path(r'^rest/', include('crm.rest_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
