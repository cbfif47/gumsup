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
from django.db.models.functions import Trunc
from .base.utilities import get_button_text
from datetime import datetime
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.utils import timezone
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client


class MansionsHomeView(TemplateView):

    def get(self, request, **kwargs):
        context = {
            "albums": MansionsAlbum.objects.all()
        }

        return render(request, 'mansions/home.html', context)

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


class MansionsVideoView(TemplateView):

    def get(self, request, **kwargs):
        context = {
        }

        return render(request, 'mansions/video.html', context)