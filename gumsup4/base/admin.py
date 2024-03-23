"""Admin for gumsup4 base models."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models


@admin.register(models.User)
class CustomUserAdmin(UserAdmin):
    """Admin for custom users."""
    fieldsets = UserAdmin.fieldsets+ (
        (                      
            'More info', # you can also use None 
            {
                'fields': (
                    'bio','is_private'
                ),
            },
        ),
    )
    

@admin.register(models.Follow)
class FollowAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.FollowRequest)
class FollowRequestsAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.Activity)
class ActivityAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.Item)
class ActivityAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.ItemLike)
class ActivityAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.ItemTag)
class ActivityAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.AppleSSO)
class AppleSSOAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.DemoFolder)
class DemoFolderAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.DemoSong)
class DemoSongAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.DemoDemo)
class DemoDemoAdmin(admin.ModelAdmin):
    """Admin for posts."""