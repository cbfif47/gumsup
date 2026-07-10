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
        self.river_urls = import_module("gumsup4.river_urls")
        self.chris_urls = import_module("gumsup4.chris_urls")

    def __call__(self, request):
        if request.get_host() is not None:
            host = request.get_host().lower()
        else:
            host = 'rex'

        if 'chris-browder' in host or 'chris.localhost' in host:
            request.urlconf = self.chris_urls
            request.site_context = 'chris'
        elif 'thisismansions' in host or 'mansions.localhost' in host:
            request.urlconf = self.mansions_urls
            request.site_context = 'mansions'
        elif 'river.localhost' in host:
            request.urlconf = self.river_urls
            request.site_context = 'river'
        elif 'rexwithfriends' in host or 'rex.localhost' in host:
            request.urlconf = self.rex_urls
            request.site_context = 'rex'
        elif 'localhost' in host:
            request.urlconf = self.river_urls
            request.site_context = 'river'
        else:
            request.urlconf = self.rex_urls
            request.site_context = 'rex'

        return self.get_response(request)