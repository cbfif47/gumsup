"""Serializers for base models."""


from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from gumsup4.base.models import User, Item, Activity


class UserSerializer(ModelSerializer):
    """Serializer for custom users."""

    class Meta:
        model = User
        fields = ["username", "bio","is_private","id"]


class ItemFeedSerializer(ModelSerializer):
    user = UserSerializer()
    is_liked = serializers.BooleanField(default=False)
    is_saved = serializers.BooleanField(default=False)
    likes_count = serializers.IntegerField()
    comments_count = serializers.IntegerField()

    class Meta:
        model = Item
        fields = ["id","name","author","note","item_type","rating"
        ,"status","started_date","ended_date","last_date","hide_from_feed"
        ,"is_liked","is_saved","likes_count","comments_count","user"]

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
    user = UserSerializer()

    class Meta:
        model = Activity
        fields = ["id","seen", "item","user","message"]

