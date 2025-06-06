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
                    'bio','is_private',"hide_objectionable_content",'last_feed_call'
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

@admin.register(models.DemoComment)
class DemoCommentAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.DemoShare)
class DemoShareAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.Flag)
class FlagAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.Block)
class BlockAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.AdminMessage)
class AdminMessageAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.UserMessage)
class UserMessageAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.MansionsAlbum)
class MansionsAlbumAdmin(admin.ModelAdmin):
    """Admin for posts."""

@admin.register(models.MansionsShow)
class MansionsShowAdmin(admin.ModelAdmin):
    """Admin for posts."""

