"""Base models for gumsup4"""


import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class BaseModel(models.Model):
    """Base model all models inherit from."""

    id = models.UUIDField(primary_key=True
        , editable=False
        , default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        """Metadata."""

        abstract = True


class User(BaseModel, AbstractUser):
    """Base user class."""
    is_private = models.BooleanField(default=False)
    bio = models.TextField(max_length=140,default='',blank=True)
 

    # every new user follows gummy and self by default
    def save(self, *args, **kwargs):
        if self._state.adding is True:
            super().save(*args, **kwargs)
            Follow.objects.create(user=self,following=User.objects.get(username='gummy'))
            Follow.objects.create(user=self,following=self)
        else:
            super().save(*args, **kwargs)

    def is_following(self,following):
        return Follow.objects.filter(user=self,following=following).exists()

    def feed(self, superlike = '', category = ''):
        #following = Follow.objects.filter(user=self).values_list('following', flat=True)
        #feed = Post.objects.filter(user__in=following)
        feed = Post.objects.filter(user__followers__user=self)
        return feed

    def follower_list(self):
        followed_by = User.objects.filter(follows__following=self).filter(~Q(id=self.id))
        return followed_by

    def following_list(self):
        follows = User.objects.filter(followers__user=self).filter(~Q(id=self.id))
        return follows

    def follower_count(self):
        fc = Follow.objects.filter(following=self).count()
        return fc

    def following_count(self):
        fc = Follow.objects.filter(user=self).exclude(following=self).count()
        return fc

    def saved_posts(self):
        return Post.objects.filter(saved_post__user=self)

    class Meta:
        """Metadata."""

        db_table = "users"


class Post(BaseModel):
    CATEGORY_CHOICES = [
        ('ART','Art'),
        ('LIFE','Life'),
        ('PLACES','Places'),
        ('STUFF','Stuff')]

    user = models.ForeignKey(
        User, verbose_name="Gummed By", on_delete=models.CASCADE,related_name="posted_by")

    what = models.CharField(max_length=50)
    why = models.TextField(max_length=140)
    original_post = models.ForeignKey(
        'self', on_delete=models.SET_DEFAULT,blank=True,null=True,default='')
    superlike = models.BooleanField(default=False)
    category = models.CharField(max_length=50
        , choices = CATEGORY_CHOICES
        , default='LIFE'
        , verbose_name="Category", blank=False)
    url = models.URLField(blank=True,default='')

    def is_saved(self,user):
        return SavedPost.objects.filter(user=user,post=self).exists()

    def filter_posts(postsQuerySet,superlike='',category=''):

        if superlike == 'y':
            if category != '':
                    feed = postsQuerySet.filter(superlike=True,category=category.upper())
            else:
                    feed = postsQuerySet.filter(superlike=True)
        elif category != '':
            feed = postsQuerySet.filter(category=category.upper())
        else:
            feed = postsQuerySet

        return feed

    def __str__(self):
        return f"{self.user}'s post on {self.created}"

    class Meta:
        """Metadata."""

        ordering = ["-created"]



class SavedPost(BaseModel):
    user = models.ForeignKey(
        User, verbose_name="Saved By", on_delete=models.CASCADE,related_name="saved_by")
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,related_name="saved_post")
    tried = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.post.user}'s post saved by {self.user} on {self.created}"

    class Meta:
        """Metadata."""

        ordering = ["-created"]


class Follow(BaseModel):
    user = models.ForeignKey(
        User, verbose_name="Followed By", on_delete=models.CASCADE,related_name="follows")
    following = models.ForeignKey(
        User, verbose_name="Following", on_delete=models.CASCADE,related_name="followers")

    def toggleFollow(user,following):
        if user.is_following(following):
            existing_follow = Follow.objects.filter(user=user,following=following)
            existing_follow.delete()
        else:
            # todo add logic for requests
            new_follow = Follow(user=user,following=following)
            new_follow.save()

    def __str__(self):
        return f"{self.user} following {self.following}"

    class Meta:
        """Metadata."""

        ordering = ["-created"]


class FollowRequest(BaseModel):
    user = models.ForeignKey(
        User, verbose_name="Followed By", on_delete=models.CASCADE,related_name="follow_requests")
    following = models.ForeignKey(
        User, verbose_name="Following", on_delete=models.CASCADE,related_name="requested_followers")
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} requested to follow {self.following}"

    class Meta:
        """Metadata."""

        ordering = ["-created"]
