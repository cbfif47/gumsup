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
    path("oldfeed", views.PostsPageView.as_view(), name='oldfeed'),
    path("items/", views.ItemsView.as_view(), name="items"),
    path("", views.ItemsFeedView.as_view(), name="home"),
    path("autocomplete-names/", views.AutocompleteNames, name="autocomplete-names"),
    path("items/<item_id>", views.ItemDetailView.as_view(), name="view-item"),
    path("items/<item_id>/edit", views.ItemEditView.as_view(), name="edit-item"),
    path("items/<item_id>/start", views.StartItem, name="start-item"),
    path("items/<item_id>/delete", views.ItemDeleteView.as_view(), name="delete-item"),
    path("items/<item_id>/finish", views.FinishItemView.as_view(), name="finish-item"),
    path("items/<item_id>/save", views.SaveItemView.as_view(), name="save-item"),
    path("items/<item_id>/like", views.LikeItem, name='like-item'),
    path("item-lists/", views.ItemListListView.as_view(), name="item-lists"),
    path("item-lists/new", views.ItemListCreateView.as_view(), name="create-item-list"),
    path("item-lists/<pk>/delete", views.ItemListDeleteView.as_view(), name="delete-item-list"),
    path("item-lists/<item_list_id>/", views.ItemListView.as_view(), name="view-item-list"),
    path("item-lists/<pk>/edit", views.ItemListEditView.as_view(), name="edit-item-list"),
    path("posts/<post_id>", views.PostView.as_view(), name='post'),
    path("posts/<post_id>/repost", views.RePostView.as_view(), name='repost'),
    path("login/", views.LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'),name='logout'),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path('accounts/', include('allauth.socialaccount.urls')),
    path("api/", include(router.urls)),
    path("signup/", views.RegisterView.as_view(), name="signup"),
    path("search-users/", views.SearchUsersList.as_view(), name='search-users'),
    path("search/", views.SearchItemsView.as_view(), name='search-items'),
    path("suggested/", views.SuggestedView.as_view(), name='suggested'),
    path("users/<username>", views.UserView.as_view(), name="user"),
    path("users/<username>/follow", views.UserFollowView.as_view(), name="user-follow"),
    path("edit-profile", views.UserEditView.as_view(), name="edit-user"),
    path("users/<username>/followers/", views.UserFollowersView.as_view(), name="followers"),
    path("users/<username>/following/", views.UserFollowingView.as_view(), name="following"),
    path("users/<username>/activity/", views.ActivityView.as_view(), name="activity"),
    path("users/<username>/privacy/", views.UserPrivacyView.as_view(), name="privacy"),
    path("users/<username>/follow-requests/", views.UserFollowRequestsView.as_view(), name="follow-requests"),
    path("saves/<post_id>", views.SavedPostView.as_view(), name='save'),
    path("saves/", views.SavedPostsView.as_view(), name='saves'),
    path("welcome/", views.WelcomeView.as_view(), name='welcome'),
]
