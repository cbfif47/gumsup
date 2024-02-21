import uuid
import re

from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token




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
    username = models.CharField(
        "username",
        max_length = 20,
        unique = True,blank=True,null=True,
        validators=[validators.RegexValidator(r'^([A-Za-z0-9])+(?:-\w*)*$'
            ,('username can only have letters, digits, underscores and hyphens'))
            ,validators.MinLengthValidator(3, 'username needs to be at least 3 characters'),
             ],
        error_messages = {
            'unique': ("username taken :("),
        },
    )

    # every new user follows gummy and self by default
    def save(self, *args, **kwargs):
        if Token.objects.filter(user=self).exists() == False:
            Token.objects.create(user=self)
        if self.username:
            self.username = self.username.lower() # force lowercase
        if self.bio:
            self.bio = self.bio.lower() # force lowercase
        self.email = self.email.lower() # force lowercase
        #if self._state.adding is True:
        #    super().save(*args, **kwargs)
        #    ItemList.objects.create(user=self,name='default list',is_default=True)
        #    if User.objects.filter(username='gummy').exists():
        #        Follow.objects.create(user=self,following=User.objects.get(username='gummy'))
        #        # Follow.objects.create(user=self,following=self) -- no more as of 2024
        super().save(*args, **kwargs)

    def is_following(self,following):
        return Follow.objects.filter(user=self,following=following).exists()

    def has_requested(self,following):
        return FollowRequest.objects.filter(user=self,following=following).exists()

    def has_pending_request(self,following):
        return FollowRequest.objects.filter(user=self,following=following,is_approved=None).exists()

    def has_declined_request(self,following):
        return FollowRequest.objects.filter(user=self,following=following,is_approved=False).exists()

    def item_feed(self):
        feed = Item.objects.filter(
            (Q(user__followers__user=self) & ~Q(hide_from_feed=True))
            | Q(user=self)
            ).annotate(likes_count=Count("liked"),comments_count=Count("comments")).distinct().order_by("-last_date")
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
        user_list = User.objects.raw("""with f as (
                                            select following_id from base_follow where user_id = %s -- i follow
                                            UNION ALL select following_id from base_followrequest where user_id = %s -- i requested
                                        )
                                        SELECT u.id
                                             , u.username
                                             , u.bio
                                        FROM users u -- all users
                                        LEFT JOIN base_follow bf
                                            on u.id = bf.following_id -- to get count of followers
                                        LEFT JOIN f
                                            on f.following_id = bf.user_id -- followed by someone im following
                                        WHERE u.id not in (SELECT following_id from f) -- not following now
                                        and u.id <> %s -- not me
                                        and u.username is not null
                                        GROUP by u.id, u.username, u.bio
                                        ORDER BY count(f.following_id) DESC -- people my follows follow
                                               ,count(bf.user_id) DESC -- popular people
                                               , u.created DESC -- new people
                                        LIMIT 20
                                        """,[self.id,self.id,self.id])

        return user_list

    def __str__(self):
        if self.username:
            return f"{self.username}"
        else:
            return f"new user"

    class Meta:
        """Metadata."""

        db_table = "users"


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
            Activity.objects.create(user=self.following,follow=new_follow,seen=True,action='follow') #log the activity for the one who approved it as seen
            super().save(*args, **kwargs)
            Activity.objects.create(user=self.user,follow_request=self,action='follow_request_approved') #log the activity for requester
        elif FollowRequest.objects.filter(user=self.user,following=self.following,is_approved=False).exists():
            self.auto_denied = True
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
            Activity.objects.create(user=self.following,follow_request=self,action='follow_request')

    def __str__(self):
        return f"{self.user} requested to follow {self.following}"

    class Meta:
        """Metadata."""

        ordering = ["-created"]


class Item(BaseModel):

    RATING_CHOICES = [
        (1,'1'),
        (2,'2'),
        (3,'3'),
        (4,'4'),
        (5,'5')
        ]

    TYPE_CHOICES = [
        ('MOVIE','movie'),
        ('BOOK','book'),
        ('TV','tv'),
        ('FOOD','food'),
        ('LIFE','life')
        ]

    STATUS_CHOICES = [
        (1,'later'),
        (2,'now'),
        (3,'finished'),
        (4,'quit')
        ]

    user = models.ForeignKey(
        User, verbose_name="Created By", on_delete=models.CASCADE,related_name="created_by")

    name = models.CharField(max_length=75, blank=False)
    author = models.CharField(max_length=40,blank=True,null=True,default='')
    item_type = models.CharField(max_length=50
        , choices = TYPE_CHOICES
        , default='MOVIE'
        , verbose_name="Type", blank=False)
    note = models.TextField(max_length=250,blank=True,null=True,default='')
    rating = models.IntegerField(choices=RATING_CHOICES,blank=True,null=True)
    original_item = models.ForeignKey(
        'Item', on_delete=models.SET_DEFAULT,blank=True,null=True,default='')
    started_date = models.DateField(blank=True,null=True)
    ended_date = models.DateField(blank=True,null=True)
    status = models.IntegerField(choices=STATUS_CHOICES,default=1)
    last_status = models.IntegerField(choices=STATUS_CHOICES,default=1)
    last_date = models.DateTimeField(default=timezone.now)
    hide_from_feed = models.BooleanField(default=False)

    def filter_items(ItemsQuerySet,status='',item_type='', tags=''):
        items = ItemsQuerySet

        if status != '':
            status = int(status)
            items = items.filter(status=status)
        if item_type != '':
            items = items.filter(item_type=item_type.upper())
        if tags != '':
            items = items.filter(tagged__tag=tags)

        return items

    def save(self, *args, **kwargs):
        if self.status != self.last_status:
            self.last_date = timezone.now()
            self.last_status = self.status
        elif not self.last_status:
            self.last_status = self.status
        # force lowercase
        self.name = self.name.lower()
        if self.note:
            self.note = self.note.lower()
        if self.author:
            self.author = self.author.lower()
        if self.status == 1:
            self.started_date = None
        if self.status == 2:
            self.ended_date = None
            self.rating = None
        if self.status == 2 and self.started_date == None:
            self.started_date = datetime.now()
        if (self.status == 4 or self.status == 3) and self.ended_date is None:
            self.ended_date = datetime.now()
        if self.ended_date is not None and self.started_date is None:
            self.started_date = self.ended_date
        super().save(*args, **kwargs)

        # log mentions, save item activity is in the view
        mentions = re.findall("@[-\w]*",self.note)
        if mentions:
            for mention in mentions:
                username = mention.replace("@","")
                user = User.objects.filter(username=username.lower()).first()
                if user:
                    existing_save = Activity.objects.filter(user=user,item=self,action="item_save")
                    existing_mention = Activity.objects.filter(user=user,item=self,action="item_mention")
                    if not existing_save and not existing_mention:
                        Activity.objects.create(user=user,item=self,action='item_mention')

        # now do tags
        tags = re.findall("#[-\w]*",self.note)
        if tags:
            for tag in tags:
                text = tag.replace("#","")
                existing_tag = ItemTag.objects.filter(item=self,tag=text)
                if not existing_tag:
                    ItemTag.objects.create(item=self,tag=text)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        """Metadata."""

        ordering = ["-last_date","-updated"]


class ItemLike(BaseModel):
    user = models.ForeignKey(
        User, verbose_name="Like By", on_delete=models.CASCADE,related_name="liked_by")
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE,related_name="liked")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Activity.objects.create(user=self.item.user,item=self.item,item_like=self,action='item_like')

    def __str__(self):
        return f"By {self.user}"

    class Meta:
        """Metadata."""

        ordering = ["-created"]


class Comment(BaseModel):
    user = models.ForeignKey(
        User, verbose_name="commenter", on_delete=models.CASCADE,related_name="comments")
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE,related_name="comments")
    body = models.TextField(max_length=250, blank=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # log activity
        if self.item.user != self.user:
            Activity.objects.create(user=self.item.user,item=self.item,comment=self,action="item_comment")

        # log mentions, save item activity is in the view
        mentions = re.findall("@[-\w]*",self.body)
        if mentions:
            for mention in mentions:
                username = mention.replace("@","")
                user = User.objects.filter(username=username.lower()).first()
                if user and user != self.user:
                    existing_activity = Activity.objects.filter(user=user,comment=self)
                    if not existing_activity:
                        Activity.objects.create(user=user,item=self.item,comment=self,action="item_comment_mention")

    def __str__(self):
        return f"{self.user} comment on {self.item}"

    class Meta:
        """Metadata."""

        ordering = ["-created"]


class Activity(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,related_name="activity_for")
    follow = models.ForeignKey(
        Follow, on_delete=models.CASCADE, null=True,blank=True,default=None)
    seen = models.BooleanField(default=False)
    follow_request = models.ForeignKey(
        FollowRequest, on_delete=models.CASCADE, null=True,blank=True,default=None,related_name="follow_request_activity")
    item_like = models.ForeignKey(
        ItemLike, on_delete=models.CASCADE, null=True,blank=True,default=None,related_name="item_likst_activity")
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, null=True,blank=True,default=None,related_name="comment_item_activity")
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, null=True,blank=True,default=None,related_name="item_activity")
    action = models.CharField(max_length=40,blank=True,null=True,default='')

    def __str__(self):
        return f"{self.action} For {self.user} on {self.created}"

    class Meta:
        """Metadata."""

        ordering = ["-created"]


class ItemTag(BaseModel):
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE,related_name="tagged")
    tag = models.CharField(max_length=40,blank=False)

    def __str__(self):
        return f"{self.item} tagged {self.tag}"

    class Meta:
        """Metadata."""

        ordering = ["-created"]

