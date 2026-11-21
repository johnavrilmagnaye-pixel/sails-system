from django.apps import AppConfig


class CoreConfig(AppConfig):
    """ Project-agnostic functions and helpers suitable for extraction into external libraries """
    name = 'core'
    verbose_name = 'Core'
