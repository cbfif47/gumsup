"""Admin for gumsup4 base models."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models


@admin.register(models.User)
class CustomUserAdmin(UserAdmin):
    """Admin for custom users."""

@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    """Admin for posts."""
    

@admin.register(models.Follow)
class FollowAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.FollowRequest)
class FollowRequestsAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.Activity)
class ActivityAdmin(admin.ModelAdmin):
    """Admin for posts."""