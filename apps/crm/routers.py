from rest_framework.routers import SimpleRouter

from crm import viewsets


router = SimpleRouter()


router.register(r'companies', viewsets.CompaniesViewSet, 'companies')
router.register(r'persons', viewsets.PersonsViewSet, 'persons')
router.register(r'deals', viewsets.DealsViewSet, 'deals')
router.register(r'tasks', viewsets.TasksViewSet, 'tasks')
router.register(r'periodic_tasks', viewsets.PeriodicTasksViewSet, 'periodic_tasks')
router.register(r'dashboard', viewsets.DashboardViewSet, 'dashboard')
router.register(r'contacts_imports', viewsets.ContactsImportsViewSet, 'contacts_imports')
router.register(r'items_export', viewsets.ItemsExportViewSet, 'items_export')
router.register(r'notes', viewsets.NotesViewSet, 'notes')
router.register(r'uploads', viewsets.UploadsViewSet, 'uploads')
router.register(r'deal_stages', viewsets.DealStagesViewSet, 'deal_stages')
router.register(r'deal_currencies', viewsets.DealCurrenciesViewSet, 'deal_currencies')
router.register(r'tags', viewsets.TagsViewSet, 'tags')
router.register(r'extra_fields', viewsets.ExtraFieldsViewSet, 'extra_fields')
