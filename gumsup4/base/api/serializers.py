"""Serializers for base models."""


from rest_framework.serializers import ModelSerializer

from gumsup4.base.models import User, Post


class UserSerializer(ModelSerializer):
    """Serializer for custom users."""

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name"]


class PostSerializer(ModelSerializer):
    class Meta:
        model = Post
        fields = ('id', 'why', 'date_created')
