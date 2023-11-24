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
    username = models.CharField(max_length=20,unique=True)

    # every new user follows gummy and self by default
    def save(self, *args, **kwargs):
        if self._state.adding is True:
            self.username = self.username.lower() # force lowercase
            super().save(*args, **kwargs)
            if User.objects.filter(username='gummy').exists():
                Follow.objects.create(user=self,following=User.objects.get(username='gummy'))
                Follow.objects.create(user=self,following=self)
        else:
            super().save(*args, **kwargs)

    def is_following(self,following):
        return Follow.objects.filter(user=self,following=following).exists()

    def has_requested(self,following):
        return FollowRequest.objects.filter(user=self,following=following).exists()

    def has_pending_request(self,following):
        return FollowRequest.objects.filter(user=self,following=following,is_approved=None).exists()

    def has_declined_request(self,following):
        return FollowRequest.objects.filter(user=self,following=following,is_approved=False).exists()

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
        fc = Follow.objects.filter(following=self).exclude(user=self).count()
        return fc

    def following_count(self):
        fc = Follow.objects.filter(user=self).exclude(following=self).count()
        return fc

    def saved_posts(self):
        return Post.objects.filter(saved_post__user=self)

    def count_follow_requests(self):
        return FollowRequest.objects.filter(following=self,is_approved=None,auto_denied=False).count()

    def has_new_activity(self):
        if FollowRequest.objects.filter(following=self,is_approved=None,auto_denied=False).exists():
            return True
        elif Activity.objects.filter(user=self,seen=False).exists():
            return True
        else:
            return False

    def suggested_users(self):
        user_list = User.objects.raw("""with f as (select following_id from base_follow where user_id = %s
                                                   UNION ALL select following_id from base_followrequest where user_id = %s)
                                        SELECT u.id, u.username, u.bio
                                        FROM users u
                                        WHERE u.id not in (SELECT following_id from f)
                                        ORDER BY u.created DESC
                                        LIMIT 25
                                        """,[self.id,self.id])

        return user_list

    class Meta:
        """Metadata."""

        db_table = "users"


class Post(BaseModel):
    CATEGORY_CHOICES = [
        ('culture','culture'),
        ('LIFE','life'),
        ('PLACES','places'),
        ('STUFF','stuff')]

    user = models.ForeignKey(
        User, verbose_name="Posted By", on_delete=models.CASCADE,related_name="posted_by")

    what = models.CharField(max_length=50)
    why = models.TextField(max_length=250)
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
        return f"{self.user}'s post about {self.what}"

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
        User, verbose_name="User", on_delete=models.CASCADE,related_name="follows")
    following = models.ForeignKey(
        User, verbose_name="Following", on_delete=models.CASCADE,related_name="followers")

    def toggleFollow(user,following):
        if user.is_following(following): # if already follow, unfollow
            existing_follow = Follow.objects.filter(user=user,following=following)
            existing_follow.delete()
            FollowRequest.objects.filter(user=user,following=following).delete() #also any old requests
            return None
        elif following.is_private == False: #if not private, follow
            new_follow = Follow(user=user,following=following)
            new_follow.save()
            return new_follow
        elif user.has_pending_request(following): #cancel requests that are pending
            existing_follow_request = FollowRequest.objects.filter(user = user, following=following, is_approved=None)
            existing_follow_request.delete()
            return None
        else: #otherwise request the follow. If theyve had a denied one previously, this will auto deny
            new_follow_request = FollowRequest(user = user, following=following)
            new_follow_request.save()
            return None #this is what triggers activity logging

    def __str__(self):
        return f"{self.user} following {self.following}"

    class Meta:
        """Metadata."""

        ordering = ["-created"]


class FollowRequest(BaseModel):
    user = models.ForeignKey(
        User, verbose_name="User", on_delete=models.CASCADE,related_name="follow_requests")
    following = models.ForeignKey(
        User, verbose_name="Following", on_delete=models.CASCADE,related_name="requested_followers")
    is_approved = models.BooleanField(null=True,blank=True,default=None)
    auto_denied = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_approved == True:
                # if approving, create the follow
            new_follow = Follow.objects.create(user=self.user,following=self.following)
            Activity.objects.create(user=self.following,follow=new_follow,seen=True) #log the activity for the one who approved it as seen
            Activity.objects.create(user=self.user,follow_request=self) #log the activity for the requester
            super().save(*args, **kwargs)
        elif FollowRequest.objects.filter(user=self.user,following=self.following,is_approved=False).exists():
            self.auto_denied = True
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} requested to follow {self.following}"

    class Meta:
        """Metadata."""

        ordering = ["-created"]


class Activity(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,related_name="activity_for")
    follow = models.ForeignKey(
        Follow, on_delete=models.CASCADE, null=True,blank=True,default=None)
    repost = models.ForeignKey(
        Post, on_delete=models.CASCADE, null=True,blank=True,default=None,related_name="repost_activity")
    saved_post = models.ForeignKey(
        SavedPost, on_delete=models.CASCADE, null=True,blank=True,default=None,related_name="saved_post_activity")
    seen = models.BooleanField(default=False)
    follow_request = models.ForeignKey(
        FollowRequest, on_delete=models.CASCADE, null=True,blank=True,default=None,related_name="follow_request_activity")

    def __str__(self):
        if self.follow:
            description = 'hi'#self.follow.user.username + ' followed ' + self.user.username
        elif self.repost:
            description = 'hi'#self.repost.user.username + ' reposted ' + self.user.username
        else:
            description = 'hi'#self.saved_post.user.username + ' saved a post by ' + self.user.username
        return description

    class Meta:
        """Metadata."""

        ordering = ["-created"]


