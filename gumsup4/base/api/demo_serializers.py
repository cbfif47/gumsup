"""Serializers for base models."""


from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from gumsup4.base.models import User, DemoFolder, DemoSong, DemoDemo, DemoComment, DemoShare


class LiteUserSerializer(ModelSerializer):
    """Serializer for custom users."""

    class Meta:
        model = User
        fields = ["username", "is_private","id","bio"]

class DemoCommentSerializer(ModelSerializer):
    """Serializer for custom users."""
    user = LiteUserSerializer()

    class Meta:
        model = DemoComment
        fields = ["id", "user","body","timestamp","created"]


class DemoSerializer(ModelSerializer):
    comments = DemoCommentSerializer(many=True)

    class Meta:
        model = DemoDemo
        fields = ["id","version", "is_primary","url","created","file_extension","comments"]


class SongSerializer(ModelSerializer):
    """Serializer for custom users."""
    demos = DemoSerializer(many=True)

    class Meta:
        model = DemoSong
        fields = ["id", "title","is_starred","is_archived","demos"]


class FolderSerializer(ModelSerializer):
    songs = SongSerializer(many=True)
    user = LiteUserSerializer()

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.user == self.context.get("user"):
            ret['can_edit'] = True
            ret['is_owner'] = True
        else:
            share = DemoShare.objects.filter(folder=instance,shared_to_user=self.context.get("user")).first()
            ret['can_edit'] = share.can_edit
            ret['is_owner'] = False
            ret['url'] = ""
            ret['folder_type'] = ""
        return(ret)

    class Meta:
        model = DemoFolder
        fields = ["id", "name","url","folder_type","songs","user"]