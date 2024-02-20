from google.oauth2 import id_token # for verifying tokens
from google.auth.transport import requests
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer, ItemSerializer, ItemFeedSerializer
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from ..models import User, Follow, Activity, FollowRequest, Item, ItemLike, ItemTag, Comment
from rest_framework import status



@csrf_exempt
def ConvertToken(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        token = data["idToken"]
        idinfo = id_token.verify_oauth2_token(token, requests.Request()
            , settings.IOS_GOOGLE_CLIENT_ID) #store this somewhere, mobile client id
        useremail = idinfo['email']
        user, created = User.objects.get_or_create(email=useremail)
        rex_token, created = Token.objects.get_or_create(user=user)
        print(rex_token)
        return JsonResponse({"token": rex_token.key
            ,"username": user.username
            , "user_id": user.id})
        #item = Item.create(user=user,name=request.post.get('name', 'name'),item_type="BOOK",status=1)
        #return JsonResponse(item.values_list('name',flat=True))
    else:
        return HttpResponse("Request method is not a get")


class FeedView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        items = request.user.item_feed()
        serializer = ItemFeedSerializer(items,many=True)
        content = {
            'has_new_activity': request.user.has_new_activity(),
            'username': request.user.username,
            'feed': serializer.data,  # None
        }
        return Response(content)

    def post(self, request, format=None):
        serializer = ItemSerializer(data=request.data)
        serializer.initial_data["user"] = request.user.id
        if serializer.is_valid():
        	serializer.save()
        	return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemView(APIView):
    """
    Retrieve, update or delete a snippet instance.
    """
    def get_object(self, item_id):
        try:
            return Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            raise Http404

    def get(self, request, item_id, format=None):
        item = self.get_object(item_id)
        serializer = ItemSerializer(item)
        return Response(serializer.data)

    def put(self, request, item_id, format=None):
        item = self.get_object(item_id)
        serializer = ItemSerializer(snippet, data=request.data)
        if serializer.is_valid():
            serializer.save(user=re)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, item_id, format=None):
        item = self.get_object(item_id)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

