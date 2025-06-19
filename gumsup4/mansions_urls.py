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
#from django.conf.urls import url
from django.views.generic import TemplateView
from rest_framework import routers
from gumsup4 import views, mansions_views
from gumsup4.base.api import serializers, viewsets, api_views, demo_views
from django.contrib.auth.views import LogoutView
from django.conf.urls.static import static
from django.conf import settings

# from .router import router

router = routers.DefaultRouter()

urlpatterns = [
    path('', mansions_views.MansionsHomeView.as_view(),name='mansions'),
    path('music/<slug:slug>/', mansions_views.MansionsAlbumView.as_view(), name='music'),
    path('music/<slug:slug>/lyrics', mansions_views.MansionsAlbumLyricsView.as_view(), name='lyrics'),
    path('music/<slug:slug>/making-of', mansions_views.MansionsMakingOfView.as_view(), name='making-of'),
    path('shows/', mansions_views.MansionsShowsView.as_view(),name='shows'),
    path("admin/", admin.site.urls),
    #path('video/', mansions_views.MansionsVideoView.as_view(),name='video'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
