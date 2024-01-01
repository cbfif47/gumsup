from django.apps import AppConfig


class BaseConfig(AppConfig):
    name = "gumsup4.base"
    
    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        from . import signals
