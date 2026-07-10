"""gumsup4 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from rest_framework import routers
from gumsup4 import river_views, consumers
from django.conf.urls.static import static
from django.conf import settings


# from .router import router

router = routers.DefaultRouter()

urlpatterns = [
    path('group/<group_id>/', river_views.group_view, name='river_group'),
    path('/new_game', river_views.new_game_view, name='river_new_game'),
    path('game/<game_id>/', river_views.game_view, name='river_game'),
    path("admin/", admin.site.urls),
] #+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# WebSocket endpoints (used by htmx ws extension)
websocket_urlpatterns = [
    re_path(r"ws/game/(?P<group_id>[0-9a-f-]+)/$", consumers.GameConsumer.as_asgi()),
]