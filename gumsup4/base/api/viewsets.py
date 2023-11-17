"""Viewsets for base models."""


from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from gumsup4.base.models import User,Post
from .serializers import UserSerializer, PostSerializer


class UserViewset(ReadOnlyModelViewSet):
    """Viewset for the user model."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class PostViewset(ModelViewSet):
    serializer_class = PostSerializer
    queryset = Post.objects.all()