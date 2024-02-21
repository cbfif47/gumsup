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
from .serializers import UserSerializer, ItemSerializer, ItemFeedSerializer, ActivitySerializer
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from ..models import User, Follow, Activity, FollowRequest, Item, ItemLike, ItemTag, Comment
from rest_framework import status
from django.shortcuts import get_object_or_404


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
		for i in items:
			i.is_liked = ItemLike.objects.filter(user=request.user,item=i).exists()
			i.is_saved = Item.objects.filter(user=request.user,original_item=i).exists()

		feed = ItemFeedSerializer(items,many=True)
		user = UserSerializer(request.user)
		activity_count = Activity.objects.filter(user=request.user,seen=False).count()
		content = {
            'activity_count': activity_count,
            'user': user.data,
            'feed': feed.data,  # None
        }
		return Response(content)

	def post(self, request, format=None):
		try:
			item = Item.objects.get(id=request.data["id"])
			if item.user == request.user:
				serializer = ItemSerializer(item,data=request.data)
			else:
				return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
		except:
			serializer = ItemSerializer(data=request.data)
		serializer.initial_data["user"] = request.user.id
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, format=None):
		try:
			item = Item.objects.get(id=request.data["id"])
			if item.user == request.user:
				item.delete()
				return Response(request.data, status=status.HTTP_201_DELETED)
			else:
				return Response(request.data, status=status.HTTP_400_BAD_REQUEST)
		except:
			return Response(request.data, status=status.HTTP_400_BAD_REQUEST)

class LikeItemView(APIView):

	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def post(self, request, format=None):
		item = get_object_or_404(Item, id = request.data["item_id"])
		action = request.data["action"]
		existing_like = ItemLike.objects.filter(user=request.user,item=item)

        # check the action. due to async aspect we could get out of sync
		if existing_like and action == "unlike":
			existing_like.delete()
			return HttpResponse("unliked") # Sending an success response
		elif not existing_like and action == "like":
			m = ItemLike(user=request.user,item=item) # Creating Like Object
			m.save()  # saving it to store in database
			return HttpResponse("liked") # Sending an success response
		else:
			return HttpResponse("no action") # Sending an success response


class ActivityView(APIView):

	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request, format=None):
		activities = Activity.objects.filter(user=request.user)
		for activity in activities:
			if activity.action == "follow":
				activity.message = activity.follow.user.username + " followed you."
				activity.user = activity.follow.user
			elif activity.action == 'follow_request':
				activity.message = activity.follow_request.user.username + " requested to follow you."
				activity.user = activity.follow_request.user
			elif activity.action == 'follow_request_approved':
				activity.message = activity.follow_request.following.username + " approved your follow request."
				activity.user = activity.follow_request.following
			elif activity.action == 'item_mention':
				activity.message = activity.item.user.username + " mentioned you in a post about " + activity.item.name + "."
			elif activity.action == 'item_like':
				activity.message = activity.item_like.user.username + " liked your post about " + activity.item.name + "."
			elif activity.action == 'item_save':
				activity.message = activity.item.user.username + " saved your post about " + activity.item.name + "."
			elif activity.action == 'item_comment':
				activity.message = activity.comment.user.username + " commented on your post about " + activity.item.name + "."
			elif activity.action == 'item_comment_mention':
				activity.message = activity.comment.user.username + " mentioned you in a comment about " + activity.item.name + "."
		for a in activities:
			if a.item:
				a.item.is_liked = ItemLike.objects.filter(user=request.user,item=a.item).exists()
				a.item.is_saved = Item.objects.filter(user=request.user,original_item=a.item).exists()
				a.item.likes_count = ItemLike.objects.filter(item=a.item).count()
				a.item.comments_count = Comment.objects.filter(item=a.item).count()
		serializer = ActivitySerializer(activities,many=True)
		return Response(serializer.data)