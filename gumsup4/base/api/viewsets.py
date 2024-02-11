"""Viewsets for base models."""


from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from gumsup4.base.models import User,Item
from .serializers import UserSerializer, ItemSerializer


class UserViewSet(ReadOnlyModelViewSet):
    """Viewset for the user model."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class ItemViewSet(ModelViewSet):
    serializer_class = ItemSerializer
    queryset = Item.objects.all()