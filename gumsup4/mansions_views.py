from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.views.generic import TemplateView, CreateView, ListView, DetailView, DeleteView, UpdateView
from django.views import View
from django.db.models import Count, Avg, Max, DateField
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .base.models import User, Follow, Activity, FollowRequest, Item, ItemLike, ItemTag, Comment, MansionsAlbum, MansionsShow
from .base.forms import RegisterForm, UserEditForm, ItemFormMain, ItemFormFinished, ItemEditForm, CommentForm
from django.contrib.auth import get_user_model
from django.db.models import Q, F
from django.db.models.functions import Trunc, ExtractYear
from .base.utilities import get_button_text
from datetime import datetime
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.utils import timezone
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client


class MansionsHomeView(ListView):
    model = MansionsAlbum
    template_name = "mansions/home.html"
    context_object_name = "albums"

    def get_queryset(self):
        queryset = super().get_queryset()
        album_type = self.request.GET.get("type")

        if album_type:
            queryset = queryset.filter(album_type=album_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["album_type_choices"] = MansionsAlbum.objects.values("album_type").distinct()
        context["selected_album_type"] = self.request.GET.get("type", "")
        return context

class MansionsAlbumView(DetailView):
    model = MansionsAlbum
    template_name = 'mansions/album.html'
    context_object_name = 'album'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'


class MansionsAlbumLyricsView(DetailView):
    model = MansionsAlbum
    template_name = 'mansions/lyrics.html'
    context_object_name = 'album'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

class MansionsShowsView(ListView):
    model = MansionsShow
    template_name = 'mansions/shows.html'  # You can rename this
    context_object_name = 'shows'  # default is 'object_list'
    ordering = ['-show_date']  # optional: newest first

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Example aggregates
        context["total_shows"] = MansionsShow.objects.count()
        context["distinct_cities"] = MansionsShow.objects.values("city","state").distinct().count()
        context["shows_by_state"] = (
            MansionsShow.objects.values("state")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )
        context["shows_by_venue"] = (
            MansionsShow.objects.values("city", "venue","state")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )
        context["shows_by_city"] = (
            MansionsShow.objects.values("city", "state")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )
        context["shows_by_year"] = (
            MansionsShow.objects.annotate(year=ExtractYear("show_date"))
            .values("year")
            .annotate(count=Count("id"))
            .order_by("year")
        )

        return context


class MansionsVideoView(TemplateView):

    def get(self, request, **kwargs):
        context = {
        }

        return render(request, 'mansions/video.html', context)


class MansionsMakingOfView(DetailView):
    model = MansionsAlbum
    template_name = 'mansions/making-of.html'
    context_object_name = 'album'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'