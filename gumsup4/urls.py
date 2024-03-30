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
from django.conf.urls import url
from django.views.generic import TemplateView
from rest_framework import routers
from gumsup4 import views
from gumsup4.base.api import serializers, viewsets, api_views, demo_views
from django.contrib.auth.views import LogoutView

# from .router import router

router = routers.DefaultRouter()
#router.register(r'items', viewsets.ItemViewSet)

urlpatterns = [
    path("items/", views.ItemsView.as_view(), name="items"),
    path("item-add/", views.ItemAddView.as_view(), name="item-add"),
    path("stats/", views.StatsView.as_view(), name="stats"),
    path("", views.ItemsFeedView.as_view(), name="home"),
    path("autocomplete-names/", views.AutocompleteNames, name="autocomplete-names"),
    path("autocomplete-authors/", views.AutocompleteAuthors, name="autocomplete-authors"),
    path("items/<item_id>", views.ItemDetailView.as_view(), name="view-item"),
    path("items/<item_id>/edit", views.ItemEditView.as_view(), name="edit-item"),
    path("items/<item_id>/delete", views.ItemDeleteView.as_view(), name="delete-item"),
    path("items/<item_id>/start", views.StartItem, name="start-item"),
    path("api/test-create/", views.CreateItem, name="create-item"),
    path("items/<item_id>/finish", views.FinishItemView.as_view(), name="finish-item"),
    path("items/<item_id>/save", views.SaveItemView.as_view(), name="save-item"),
    path("items/<item_id>/like", views.LikeItem, name='like-item'),
    path("login/", views.LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'),name='logout'),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path('accounts/', include('allauth.socialaccount.urls')),
    path("signup/", views.RegisterView.as_view(), name="signup"),
    path("search-users/", views.SearchUsersList.as_view(), name='search-users'),
    path("search/", views.SearchItemsView.as_view(), name='search-items'),
    path("suggested/", views.SuggestedView.as_view(), name='suggested'),
    path("suggested-welcome/", views.SuggestedWelcomeView.as_view(), name='suggested-welcome'),
    path("users/<username>", views.UserView.as_view(), name="user"),
    path("users/<username>/follow", views.FollowUser, name="user-follow"),
    path("edit-profile", views.UserEditView.as_view(), name="edit-user"),
    path("users/<username>/followers/", views.UserFollowersView.as_view(), name="followers"),
    path("users/<username>/following/", views.UserFollowingView.as_view(), name="following"),
    path("activity/", views.ActivityView.as_view(), name="activity"),
    path("follow-requests/", views.UserFollowRequestsView.as_view(), name="follow-requests"),
    path("welcome/", views.WelcomeView.as_view(), name='welcome'),
    path("comments/<comment_id>/delete", views.CommentDeleteView.as_view(), name="delete-comment"),
    path('api/', include(router.urls)),
    path('api/feed/', api_views.FeedView.as_view()),
    path('api/more-items/', api_views.MoreItemsView.as_view()),
    path('api/item/<item_id>', api_views.ItemView.as_view()),
    path('api/like-item/', api_views.LikeItemView.as_view()),
    path('api/user/<user_id>/', api_views.UserView.as_view()),
    path('api/user/<user_id>/items/', api_views.UserItemsView.as_view()),
    path('api/user/<user_id>/socials/', api_views.UserSocialsView.as_view()),
    path('api/activity/', api_views.ActivityView.as_view()),
    path('api/activity/count', api_views.ActivityCountView.as_view()),
    path('api/search/', api_views.SearchView.as_view()),
    path('api/suggestions/search/', api_views.SearchSuggestionsView.as_view()),
    path('api/suggestions/item/', api_views.AutocompleteView.as_view()),
    path('api/edit-user/', api_views.EditUserView.as_view()),
    path('api/explore/', api_views.ExploreView.as_view()),
    path('api/suggested-users/', api_views.SuggestedUsersView.as_view()),
    path("api/convert-token/", api_views.ConvertToken, name='convert-token'),
    path("api/apple-login/", api_views.AppleLogin),
    path('demoitis/main/', demo_views.MainView.as_view()),
    path('demoitis/song/<song_id>/', demo_views.EditSongView.as_view()),
    path('demoitis/demo/<demo_id>/', demo_views.EditDemoView.as_view()),
    path('api/follow-requests/', api_views.FollowRequestsView.as_view()),
]
