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
from django.urls import path, include
from django.views.generic import TemplateView
from gumsup4.base.api import viewsets
from rest_framework import routers
from gumsup4 import views
from django.contrib.auth.views import LogoutView

# from .router import router

router = routers.DefaultRouter()
router.register(r'posts', viewsets.PostViewset, 'post')

urlpatterns = [
    path("", views.PostsPageView.as_view(), name='home'),
    path("posts/<post_id>", views.PostView.as_view(), name='post'),
    path("posts/<post_id>/repost", views.RePostView.as_view(), name='repost'),
    path("login/", views.LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'),name='logout'),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("api/", include(router.urls)),
    path("signup/", views.RegisterView.as_view(), name="signup"),
    path("search-users/", views.SearchUsersList.as_view(), name='search_users'),
    path("search-posts/", views.SearchPostsView.as_view(), name='search_posts'),
    path("users/<username>", views.UserView.as_view(), name="user"),
    path("users/<username>/followers/", views.UserFollowersView.as_view(), name="followers"),
    path("users/<username>/following/", views.UserFollowingView.as_view(), name="following"),
    path("saves/<post_id>", views.SavedPostView.as_view(), name='save'),
    path("saves/", views.SavedPostsView.as_view(), name='saves'),
]
