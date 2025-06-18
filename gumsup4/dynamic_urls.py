# dynamic_urls.py
from django.conf import settings
from django.urls import get_resolver, URLResolver
from django.utils.deprecation import MiddlewareMixin
from importlib import import_module

class SiteBasedURLRoutingMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.rex_urls = import_module("gumsup4.rex_urls")
        self.mansions_urls = import_module("gumsup4.mansions_urls")

    def __call__(self, request):
        if request.get_host() is not None:
            host = request.get_host().lower()
        else:
            host = 'rex'

        if 'thisismansions' in host:
            request.urlconf = self.mansions_urls
            request.site_context = 'mansions'
        else:
            request.urlconf = self.rex_urls
            request.site_context = 'rex'

        return self.get_response(request)