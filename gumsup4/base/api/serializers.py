"""Serializers for base models."""


from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from gumsup4.base.models import User, Item, Activity, Comment, ItemLike, ItemTag, AppleSSO
from gumsup4.base.utilities import get_button_text, cbtimesince


class UserSerializer(ModelSerializer):
    """Serializer for custom users."""

    def to_representation(self,instance):
        ret = super().to_representation(instance)
        ret['follow_button_text'] = get_button_text(self.context.get("user"),instance)
        ret['follower_count'] = instance.follower_count()
        ret['following_count'] = instance.following_count()
        return ret

    class Meta:
        model = User
        fields = ["username", "bio","is_private","id"]

class LiteUserSerializer(ModelSerializer):
    """Serializer for custom users."""

    class Meta:
        model = User
        fields = ["username", "is_private","id"]



class ItemFeedSerializer(ModelSerializer):
    user = LiteUserSerializer()

    def to_representation(self, instance):
        """Convert `username` to lowercase."""
        ret = super().to_representation(instance)
        ret['likes_count'] = ItemLike.objects.filter(item=instance).count()
        ret['comments_count'] = Comment.objects.filter(item=instance).count()
        ret['is_liked'] = ItemLike.objects.filter(item=instance,user=self.context.get("user")).exists()
        ret['is_saved'] = Item.objects.filter(user=self.context.get("user"),original_item=instance).exists()
        ret['timesince'] = cbtimesince(instance.last_date)
        ret['tags'] = ItemTag.objects.filter(item=instance).values('tag')
        return ret

    class Meta:
        model = Item
        fields = ["id","name","author","note","item_type","rating"
        ,"status","started_date","ended_date","last_date","hide_from_feed"
        ,"user"]

    id = serializers.CharField(read_only=True)
    name = serializers.CharField(required=True,max_length=75)
    author = serializers.CharField(required=False, allow_blank=True,max_length=50)
    note = serializers.CharField(required=False, allow_blank=True,max_length=250)
    item_type = serializers.ChoiceField(choices=Item.TYPE_CHOICES,allow_blank=True)
    rating = serializers.ChoiceField(choices=Item.RATING_CHOICES,allow_blank=True)
    status = serializers.ChoiceField(choices=Item.STATUS_CHOICES,default=1)
    started_date = serializers.DateField(required=False)
    ended_date = serializers.DateField(required=False)
    last_date = serializers.DateTimeField(read_only=True)
    hide_from_feed = serializers.BooleanField(default=False)


class ItemSerializer(ModelSerializer):

    class Meta:
        model = Item
        fields = ["id","name","author","note","item_type","rating"
        ,"status","started_date","ended_date","last_date","hide_from_feed"
        ,"original_item",
        "user"]


class ActivitySerializer(ModelSerializer):
    message = serializers.CharField(default="")
    item = ItemFeedSerializer()
    user = LiteUserSerializer()

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['timesince'] = cbtimesince(instance.created)
        return(ret)

    class Meta:
        model = Activity
        fields = ["id","seen", "item","user","message","created"]


class CommentSerializer(ModelSerializer):
    user = LiteUserSerializer()

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['timesince'] = cbtimesince(instance.created)
        return(ret)

    class Meta:
        model = Comment
        fields = ["user","body","id"]

class NewCommentSerializer(ModelSerializer):

    class Meta:
        model = Comment
        fields = ["body","item","user","id"]


class ItemLikeSerializer(ModelSerializer):
    user = UserSerializer()

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['timesince'] = cbtimesince(instance.created)
        return(ret)

    class Meta:
        model = ItemLike
        fields = ["id","user"]


class TagSerializer(ModelSerializer):

    class Meta:
        model = ItemTag
        fields = ["tag"]


class ExploreSerializer(serializers.Serializer):
    name = serializers.CharField()
    total = serializers.IntegerField()
    avg_rating = serializers.IntegerField()
    segment = serializers.CharField()


class AppleSSOSerializer(ModelSerializer):

    class Meta:
        model = AppleSSO
        fields = ["email","apple_id"]