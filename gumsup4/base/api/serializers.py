"""Serializers for base models."""


from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework import serializers

from gumsup4.base.models import User, Item, Activity, Comment, ItemLike, ItemTag, AppleSSO, FollowRequest
from gumsup4.base.utilities import get_button_text, cbtimesince
from django.db.models import Q


class UserSerializer(ModelSerializer):
    """Serializer for custom users."""

    def to_representation(self,instance):
        ret = super().to_representation(instance)
        ret['follow_button_text'] = get_button_text(self.context.get("user"),instance)
        return ret

    class Meta:
        model = User
        fields = ["username", "bio","is_private","id"]

class LiteUserSerializer(ModelSerializer):
    """Serializer for custom users."""

    class Meta:
        model = User
        fields = ["username", "is_private","id","bio"]


class MeSerializer(ModelSerializer):
    """Serializer for custom users."""

    class Meta:
        model = User
        fields = ["username", "is_private","id","bio","hide_objectionable_content"]


class ItemFeedSerializer(ModelSerializer):
    user = LiteUserSerializer()
    saved_from = SerializerMethodField()

    def to_representation(self, instance):
        """Convert `username` to lowercase."""
        ret = super().to_representation(instance)
        ret['likes_count'] = ItemLike.objects.filter(item=instance).count()
        ret['comments_count'] = Comment.objects.filter(item=instance).count()
        ret['is_liked'] = ItemLike.objects.filter(item=instance,user=self.context.get("user")).exists()
        ret['is_saved'] = Item.objects.filter(user=self.context.get("user"),original_item=instance).exists()
        ret['timesince'] = cbtimesince(instance.last_date)
        ret['tags'] = ItemTag.objects.filter(item=instance).values('tag')
        mentioned_user_list = Activity.objects.filter(item=instance,action='item_mention').values_list('user')
        mentioned_users = User.objects.filter(Q(id__in=mentioned_user_list) & ~Q(blocks_received__user=self.context.get("user")))
        ret['mentions'] = LiteUserSerializer(mentioned_users,many=True).data
        return ret

    class Meta:
        model = Item
        fields = ["id","name","author","note","item_type","rating"
        ,"status","last_date","hide_from_feed"
        ,"user","saved_from"]

    id = serializers.CharField(read_only=True)
    name = serializers.CharField(required=True,max_length=75)
    author = serializers.CharField(required=False, allow_blank=True,max_length=50)
    note = serializers.CharField(required=False, allow_blank=True,max_length=250)
    item_type = serializers.ChoiceField(choices=Item.TYPE_CHOICES,allow_blank=True)
    rating = serializers.ChoiceField(choices=Item.RATING_CHOICES,allow_blank=True)
    status = serializers.ChoiceField(choices=Item.STATUS_CHOICES,default=1)
    last_date = serializers.DateTimeField(read_only=True)
    hide_from_feed = serializers.BooleanField(default=False)

    def get_saved_from(self,obj):
        if obj.original_item is not None:
            return ItemFeedSerializer(obj.original_item).data
        else:
            return None


class ItemSerializer(ModelSerializer):

    class Meta:
        model = Item
        fields = ["id","name","author","note","item_type","rating"
        ,"status","last_date","hide_from_feed"
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
        mentioned_user_list = Activity.objects.filter(item=instance.item,action='item_comment_mention').values_list('user')
        mentioned_users = User.objects.filter(Q(id__in=mentioned_user_list) & ~Q(blocks_received__user=self.context.get("user")))
        ret['mentions'] = LiteUserSerializer(mentioned_users,many=True).data
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


class ExploreSerializerV2(serializers.Serializer):
    name = serializers.CharField()
    total = serializers.IntegerField()
    avg_rating = serializers.DecimalField(decimal_places=1,max_digits=2)
    segment = serializers.CharField()


class AppleSSOSerializer(ModelSerializer):

    class Meta:
        model = AppleSSO
        fields = ["email","apple_id"]

class AutocompleteSerializer(ModelSerializer):
    author = serializers.CharField(source='clean_author')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['object_type'] = "item"
        return(ret)

    class Meta:
        model = Item
        fields = ["name","author"]


class FollowRequestSerializer(ModelSerializer):
    user = LiteUserSerializer()

    class Meta:
        model = FollowRequest
        fields = ["id","user","is_approved"]
        read_only_fields = ['user']




class StatSerializer(serializers.Serializer):
    item_type = serializers.CharField()
    year = serializers.IntegerField()
    avg_rating = serializers.DecimalField(decimal_places=1,max_digits=2)
    count = serializers.IntegerField()