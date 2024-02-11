"""Serializers for base models."""


from rest_framework.serializers import ModelSerializer

from gumsup4.base.models import User, Item


class UserSerializer(ModelSerializer):
    """Serializer for custom users."""

    class Meta:
        model = User
        fields = ["username", "bio","is_private"]


class ItemSerializer(ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Item
        depth = 1
        fields = ('id', 'name', 'author', 'note', 'rating','user')
