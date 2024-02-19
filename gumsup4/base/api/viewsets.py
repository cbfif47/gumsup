"""Viewsets for base models."""


from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from gumsup4.base.models import User,Item
from .serializers import UserSerializer, ItemSerializer


class UserViewSet(ReadOnlyModelViewSet):
    """Viewset for the user model."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# class ItemViewSet(ModelViewSet):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#     serializer_class = ItemSerializer
                                                                          
#     queryset = Item.objects.all()[:20] #request.user.item_feed()[:20]