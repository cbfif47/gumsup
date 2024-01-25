import uuid
import re

from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.db import models
from django.db.models import Q
from django.utils import timezone


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

    def feed(self, superlike = '', category = ''):
        #following = Follow.objects.filter(user=self).values_list('following', flat=True)
        #feed = Post.objects.filter(user__in=following)
        feed = Post.objects.filter(user__followers__user=self)
        return feed

    def item_feed(self):
        feed = Item.objects.filter(user__followers__user=self).exclude(status=1).exclude(hide_from_feed=True)
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
                                        LEFT JOIN base_follow bf
                                            on u.id = bf.following_id
                                        WHERE u.id not in (SELECT following_id from f)
                                        and u.id <> %s
                                        and u.username is not null
                                        GROUP by u.id, u.username, u.bio, u.created
                                        ORDER BY count(bf.user_id) DESC, u.created DESC
                                        LIMIT 20
                                        """,[self.id,self.id,self.id])

        return user_list

    def has_lists(self):
        x = ItemList.objects.filter(user=self,is_default=False).count() > 0
        return x

    def __str__(self):
        if self.username:
            return f"{self.username}"
        else:
            return f"new user"

    class Meta:
        """Metadata."""

        db_table = "users"


class Post(BaseModel):
    CATEGORY_CHOICES = [
        ('CULTURE','culture'),
        ('LIFE','life'),
        ('PLACES','places'),
        ('STUFF','stuff')]

    user = models.ForeignKey(
        User, verbose_name="Posted By", on_delete=models.CASCADE,related_name="posted_by")

    what = models.CharField(max_length=50)
    why = models.TextField(max_length=250)
    original_post = models.ForeignKey(
        'Post', on_delete=models.SET_DEFAULT,blank=True,null=True,default='')
    superlike = models.BooleanField(default=False)
    category = models.CharField(max_length=50
        , choices = CATEGORY_CHOICES
        , default='LIFE'
        , verbose_name="Category", blank=False)
    url = models.URLField(blank=True,default='')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        gummy = User.objects.get(username='gummy')
        # now lets log activity

        # first repost. dont do it if its gummy
        if self.original_post_id:
                original_poster = self.original_post.user
                if original_poster != gummy:
                    Activity.objects.create(user=original_poster,repost=self)
        else:
            original_poster = gummy

        #now mentions, dont notify same person as above, and no gummy, and no self-mention
        mentions = re.findall("@[-\w]*",self.why)
        for mention in mentions:
            username = mention.replace("@","")
            user = User.objects.filter(username=username.lower()).first()
            if user:
                if user != original_poster and user != self.user: 
                    Activity.objects.create(user=user,mention=self)

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


class ItemList(BaseModel):
    user = models.ForeignKey(
        User, verbose_name="List created By", on_delete=models.CASCADE,related_name="list_by")
    name = models.CharField(max_length=50, blank=False)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        """Metadata."""

        ordering = ["-is_default","-created"]


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
    last_date = models.DateField(default=timezone.now)
    item_list = models.ForeignKey(ItemList, models.SET_DEFAULT,blank=True,null=True,default='')
    hide_from_feed = models.BooleanField(default=False)

    def filter_items(ItemsQuerySet,status='',item_type='', tags=''):

        if status != '':
            status = int(status)
            if item_type != '':
                if tags != '':
                    items = ItemsQuerySet.filter(status=status,item_type=item_type.upper(),tagged__tag=tags)
                else:
                    items = ItemsQuerySet.filter(status=status,item_type=item_type.upper())
            elif tags != '':
                items = ItemsQuerySet.filter(status=status,tagged__tag=tags)
            else:
                items = ItemsQuerySet.filter(status=status)
        elif item_type != '':
            if tags != '':
                items = ItemsQuerySet.filter(item_type=item_type.upper(),tagged__tag=tags)
            else:
                items = ItemsQuerySet.filter(item_type=item_type.upper())
        elif tags != '':
                items = ItemsQuerySet.filter(tagged__tag=tags)
        else:
            items = ItemsQuerySet

        return items

    def save(self, *args, **kwargs):
        if self.status == 2 and self.started_date:
            self.last_date = self.started_date
        elif self.status == 3 and self.ended_date:
            self.last_date = self.ended_date
        elif self.status == 4 and self.ended_date:
            self.last_date = self.ended_date
        else:
            self.last_date = timezone.localtime(self.created)
        # for lowercase
        self.name = self.name.lower()
        if self.note:
            self.note = self.note.lower()
        super().save(*args, **kwargs)

        # log mentions, save item activity is in the view
        mentions = re.findall("@[-\w]*",self.note)
        if mentions:
            for mention in mentions:
                username = mention.replace("@","")
                user = User.objects.filter(username=username.lower()).first()
                existing_save = Activity.objects.filter(user=user,save_item=self)
                existing_mention = Activity.objects.filter(user=user,mention_item=self)
                if not existing_save and not existing_mention:
                    Activity.objects.create(user=user,mention_item=self)

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
        Activity.objects.create(user=self.item.user,like_item=self)

    def __str__(self):
        return f"By {self.user}"

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
    mention = models.ForeignKey(
        Post, on_delete=models.CASCADE, null=True,blank=True,default=None,related_name="mention_activity")
    mention_item = models.ForeignKey(
        Item, on_delete=models.CASCADE, null=True,blank=True,default=None,related_name="mention_item_activity")
    save_item = models.ForeignKey(
        Item, on_delete=models.CASCADE, null=True,blank=True,default=None,related_name="save_item_activity")
    like_item = models.ForeignKey(
        ItemLike, on_delete=models.CASCADE, null=True,blank=True,default=None,related_name="like_item_activity")

    def __str__(self):
        return f"For {self.user} on {self.created}"

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
