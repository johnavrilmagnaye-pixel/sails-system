import os

from django.apps import apps
from django.conf import settings
from django.test.runner import DiscoverRunner


class ProjectDiscoverRunner(DiscoverRunner):
    """ Discovers project apps by their canonical Django names. Fixes imports of 'crm'` and 'apps.crm'. """

    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        if not test_labels:
            apps_path = os.path.join(settings.PROJECT_PATH, 'apps')
            test_labels = tuple(
                app_config.name
                for app_config in apps.get_app_configs()
                if os.path.commonpath((apps_path, app_config.path)) == apps_path
            )

        return super().build_suite(test_labels, extra_tests, **kwargs)
