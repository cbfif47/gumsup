"""Serializers for base models."""


from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from gumsup4.base.models import User, DemoFolder, DemoSong, DemoDemo


class LiteUserSerializer(ModelSerializer):
    """Serializer for custom users."""

    class Meta:
        model = User
        fields = ["username", "is_private","id","bio"]


class DemoSerializer(ModelSerializer):
    """Serializer for custom users."""

    class Meta:
        model = DemoDemo
        fields = ["id","version", "is_primary","url","created","file_extension"]


class SongSerializer(ModelSerializer):
    """Serializer for custom users."""
    demos = DemoSerializer(many=True)

    class Meta:
        model = DemoSong
        fields = ["id", "title","is_starred","is_archived","demos"]


class FolderSerializer(ModelSerializer):
    songs = SongSerializer(many=True)
    user = LiteUserSerializer()
    shared_by = LiteUserSerializer()

    class Meta:
        model = DemoFolder
        fields = ["id", "name","url","folder_type","shared_by","user","songs"]