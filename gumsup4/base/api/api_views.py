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
from . import serializers as sz
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from ..models import User, Follow, Activity, FollowRequest, Item, ItemLike, ItemTag, Comment, AppleSSO, FollowRequest, Flag, Block, UserMessage
from rest_framework import status
from django.shortcuts import get_object_or_404
from gumsup4.base.utilities import get_button_text
from django.db.models import Q, F, Count, Avg, Max, Value, Variance
from django.db.models.functions import Coalesce, Extract
from django.utils import timezone


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
		if user.username:
			return JsonResponse({"token": rex_token.key
	            ,"username": user.username
	            , "user_id": user.id})
		else:
			return JsonResponse({"token": rex_token.key
	            ,"username": ""
	            , "user_id": user.id})
	else:
		return HttpResponse("Request method is not a get")


class FeedView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request, format=None):
		max_last_date = request.GET.get("max_last_date","")
		if max_last_date != "":
			items = request.user.item_feed().filter(last_date__lt=max_last_date)[:30]
		else:
			items = request.user.item_feed()[:30]
			request.user.last_feed_call = timezone.now()
			request.user.save()
		
		my_tags = ItemTag.objects.filter(item__user=request.user).order_by().values('tag').distinct()
		feed = sz.ItemFeedSerializer(items,many=True,context={'user': request.user})
		user = sz.MeSerializer(request.user)
		tags = sz.TagSerializer(my_tags,many=True)
		activity_count = Activity.objects.filter(user=request.user,seen=False).count()
		friends = User.objects.filter(followers__user=request.user).values_list('username',flat=True)
		user_message = UserMessage.objects.filter(user=request.user).first()
		if user_message:
			message = user_message.message.message
			user_message.delete()
		else:
			message = ""
		content = {
            'activity_count': activity_count,
            'user': user.data,
            'feed': feed.data,  # None
            'tags': tags.data,
            'friends': friends,
            'message': message
        }
		return Response(content)

	def post(self, request, format=None):
		try:
			item = Item.objects.get(id=request.data["id"])
			if item.user == request.user:
				serializer = sz.ItemSerializer(item,data=request.data)
			else:
				return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
		except:
			serializer = sz.ItemSerializer(data=request.data)
		serializer.initial_data["user"] = request.user.id
		if serializer.is_valid():
			i = serializer.save()
			if "v2" in request.data:
				return Response(sz.ItemFeedSerializer(i).data, status=status.HTTP_201_CREATED)
			else:
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


class MoreItemsView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request, format=None):
		max_last_date = request.GET.get("max_last_date","")
		item_type = request.GET.get("item_type","")
		status = request.GET.get("status","0")
		if max_last_date != "":
			items = request.user.item_feed().filter(last_date__lt=max_last_date)
		else:
			items = request.user.item_feed() #this shouldnt happen
		if item_type != "":
			items = items.filter(item_type=item_type)
		if status != "0":
			items = items.filter(status=status)

		feed = sz.ItemFeedSerializer(items[:30],many=True,context={'user': request.user})

		return Response(feed.data)


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
		max_last_date = request.GET.get("max_last_date","")
		activity_base = Activity.objects.filter(
			Q(user=request.user)
			# nothing from blocked users
			& ~Q(follow__user__blocks_received__user=request.user) & ~Q(item__user__blocks_received__user=request.user)
			 & ~Q(item_like__user__blocks_received__user=request.user) & ~Q(comment__user__blocks_received__user=request.user)
			  & ~Q(follow_request__user__blocks_received__user=request.user)
			# nothing from users who blocked me
			& ~Q(follow__user__blocks__blocked_user=request.user) & ~Q(item__user__blocks__blocked_user=request.user)
			 & ~Q(item_like__user__blocks__blocked_user=request.user) & ~Q(comment__user__blocks__blocked_user=request.user)
			  & ~Q(follow_request__user__blocks__blocked_user=request.user)
			)
		if max_last_date != "":
			activities = activity_base.filter(Q(created__lt=max_last_date))[:50]
		else:
			activities = activity_base[:50]
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
		serializer = sz.ActivitySerializer(activities,many=True,context={'user': request.user})
		data = serializer.data
		# now mark them all as seen
		Activity.objects.filter(user=request.user,seen=False).update(seen=True)
		# for a in activities:
		# 	if a.seen == False:
		# 		a.seen = True
		# 		a.save()
		return Response(serializer.data)


class ItemView(APIView):

	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request, item_id,format=None):
		item = get_object_or_404(Item, id = item_id)
		if request.user.is_blocked_or_blocking(item.user):
			return Response(False, status=status.HTTP_400_BAD_REQUEST)
		# get comments and likes detail
		comments = Comment.objects.filter(Q(item=item_id) & ~Q(user__blocks_received__user=request.user))
		if request.user.hide_objectionable_content:
			comments = comments.filter(Q(flags__isnull=True))
		serializer = sz.CommentSerializer(comments,many=True,context={'user': request.user})
		likes = ItemLike.objects.filter(Q(item=item_id) & ~Q(user__blocks_received__user=request.user))
		likes_serializer = sz.ItemLikeSerializer(likes,many=True,context={'user': request.user})

		content = {
            'comments': serializer.data,
            'likes': likes_serializer.data
        }
		return Response(content)

	def post(self, request, item_id,format=None):
		# make a comment
		item = get_object_or_404(Item, id = item_id)
		if request.user.is_blocked_or_blocking(item.user):
			return Response(False, status=status.HTTP_400_BAD_REQUEST)
		serializer = sz.NewCommentSerializer(data=request.data)
		serializer.initial_data["user"] = request.user.id
		serializer.initial_data["item"] = item_id
		if serializer.is_valid():
			c = serializer.save()
			if "v2" in request.data:
				return Response(sz.CommentSerializer(c,context={'user': request.user}).data, status=status.HTTP_201_CREATED)
			else:
				return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, item_id, format=None):
		# delete comments
		try:
			item = get_object_or_404(Item, id = item_id)
			comment = Comment.objects.get(id=request.data["comment_id"])
			if comment.user == request.user or comment.user == item.user:
				comment.delete()
				return Response(request.data, status=status.HTTP_201_DELETED)
			else:
				return Response(request.data, status=status.HTTP_400_BAD_REQUEST)
		except:
			return Response(request.data, status=status.HTTP_400_BAD_REQUEST)


class UserView(APIView):

	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request,user_id,format=None):
		user = get_object_or_404(User, id = user_id)
		if request.user.is_blocked_or_blocking(user):
			return Response(False, status=status.HTTP_400_BAD_REQUEST)
		serializer = sz.UserSerializer(user,many=False,context={'user': request.user})
		return Response(serializer.data)

	def post(self, request,user_id,format=None):
		user = get_object_or_404(User, id = user_id)
		if user != request.user:
			new_follow = Follow.toggleFollow(user=request.user, following=user)
			if new_follow:
				Activity.objects.create(user=user,follow=new_follow,action='follow')
			text = get_button_text(request.user,user)
			return HttpResponse(text) # Sending an success response
		else:
			return HttpResponse("whoops")


class UserItemsView(APIView):

	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request,user_id,format=None):
		user = get_object_or_404(User, id = user_id)
		if request.user.is_blocked_or_blocking(user):
			return Response(False, status=status.HTTP_400_BAD_REQUEST)
		max_last_date = request.GET.get("max_last_date","")
		item_type = request.GET.get("item_type","")
		status = request.GET.get("status","0")
		tag = request.GET.get("tag","")
		if max_last_date != "":
			items = user.viewable_items(request.user).filter(last_date__lt= max_last_date)
		else:
			items = user.viewable_items(request.user)
		if item_type != "":
			items = items.filter(item_type=item_type)
		if status != "0":
			items = items.filter(status=status)
		if tag != "":
			items = items.filter(tagged__tag=tag)

		serializer = sz.ItemFeedSerializer(items[:25],many=True,context={'user': request.user})
		return Response(serializer.data)


class ActivityCountView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request, format=None):
		activity_count = Activity.objects.filter(user=request.user,seen=False).count()
		return HttpResponse(activity_count)


class SearchView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request, **kwargs):
		query = request.GET.get("q",'')
		mode = request.GET.get("mode",'')
		query_object = request.GET.get("object",'')
		if len(query) > 2:
			base_items = Item.objects.filter(
				(Q(user=request.user) #owned by user
		                | Q(user__is_private=False) #public user
		                | Q(user__followers__user=request.user) #following user
		                )
				& ~Q(user__blocks_received__user=request.user) #not someone ive blocked
				& ~Q(user__blocks__blocked_user=request.user) #not someone who blocked me
				)
			if request.user.hide_objectionable_content:
				base_items = base_items.filter(Q(flags__isnull=True))
			if query_object == "item":
				if mode == 'strict':
					items = base_items.filter(Q(name=query)).distinct() #strict match
				elif mode == 'author':
					items = base_items.filter(Q(author=query)).distinct() #strict match
				else:
					items = base_items.filter(
		                Q(name__icontains=query) #term matches
		                    | Q(author__icontains=query)
		                    | Q(note__icontains=query)
		                ).distinct() 
				serializer = sz.ItemFeedSerializer(items,many=True,context={'user': request.user})
			elif query_object == "user":
				users = User.objects.filter((Q(username__icontains=query) 
					| Q(bio__icontains=query)
					| Q(email__icontains=query))
					& Q(username__isnull=False)
					& ~Q(blocks_received__user=request.user)
					& ~Q(blocks__blocked_user=request.user)
					)
				serializer = sz.LiteUserSerializer(users,many=True,context={'user': request.user})
			else:
				return HttpResponse("whoops")
			#stats = raw_feed.aggregate(count=Count("id"),ratings=Count("rating"),avg_rating=Avg("rating"))
			return Response(serializer.data)
		else:
			return HttpResponse("whoops")


class SearchSuggestionsView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request, **kwargs):
		query = request.GET.get("q",'')
		query_object = request.GET.get("object",'item')
		if query_object == 'item':
			suggestions = Item.objects.filter(Q(name__icontains=query)
		                    | Q(author__icontains=query)).order_by("name").distinct().values_list("name",flat=True)[:5]
		elif query_object == 'user':
			suggestions = User.objects.filter((Q(username__icontains=query) | Q(bio__icontains=query)
					| Q(email__icontains=query))
					& ~Q(blocks_received__user=request.user)
					& ~Q(blocks__blocked_user=request.user)
			).order_by("username").distinct().values_list("username",flat=True)[:5]
		suggestions = list(suggestions)
		if query not in suggestions:
			suggestions.insert(0,query)
		return Response(suggestions)


class AutocompleteView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request, **kwargs):
		query = request.GET.get("q",'')
		items = Item.objects.filter(Q(name__icontains=query)).annotate(clean_author=Coalesce('author',Value(""))).order_by('name','clean_author').values('name','clean_author').distinct()[:5]
		serializer = sz.AutocompleteSerializer(items,many=True)
		return Response(serializer.data)


class ExploreView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request, **kwargs):
		version = request.GET.get("v",'')
		popular = Item.objects.all().values('name').annotate(total=Count('name')
			,avg_rating=Avg('rating')
            ,max_date=Max('last_date'),segment=Value("popular")).order_by('-total','-max_date').exclude(total=1)[:3]


		highest_rated = Item.objects.filter(rating__gte=1).values('name').annotate(total=Count('rating')
			,avg_rating=Avg('rating')
            ,max_date=Max('last_date'),segment=Value("highest_rated")).filter(total__gte=2).order_by('-avg_rating','-max_date','-total')[:3]
		if version == 'v2':
			serializer = sz.ExploreSerializerV2(popular.union(highest_rated),many=True)
		else:
			serializer = sz.ExploreSerializer(popular.union(highest_rated),many=True)
		return Response(serializer.data)


class EditUserView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def post(self, request, **kwargs):
		user = get_object_or_404(User, id = request.data["id"])

		if user == request.user:
			serializer = sz.MeSerializer(user,data=request.data)
			if serializer.is_valid():
				serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.data)

	def delete(self, request, **kwargs):
		user = get_object_or_404(User, id = request.data["id"])

		if user == request.user:
			user.delete()
			return Response(True, status=status.HTTP_201_DELETED)
		return Response(False, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def AppleLogin(request):

	if request.method == 'POST':
		data = json.loads(request.body)
		try:
			email = data["email"]
			apple_id = data["apple_id"]
			apple_sso_key = data["apple_sso_key"]
		except:
			return HttpResponse("Missing data")
		if apple_sso_key != settings.APPLE_SSO_KEY:
			return HttpResponse("Bad sso key")
		if email != "":
			apple_sso, created = AppleSSO.objects.get_or_create(email=email,apple_id=apple_id)
		else:
			# apple only gives the email the first time, so if we dont get it in the request, find the record
			apple_sso = AppleSSO.objects.filter(apple_id=apple_id).first() #if they switch things around, there could be two. get the latest
			email = apple_sso.email

		user, created = User.objects.get_or_create(email=email)
		rex_token, created = Token.objects.get_or_create(user=user)
		return JsonResponse({"token": rex_token.key
            ,"username": user.username
            , "user_id": user.id})
	else:
		return HttpResponse("Request method is not a post")


class UserSocialsView(APIView):

	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request,user_id,format=None):
		user = get_object_or_404(User, id = user_id)
		max_last_date = request.GET.get("max_last_date","")
		social_type = request.GET.get("social_type","followers")
		if user.is_private & request.user.is_following(user) == False: # i should just make this a permission class thing
			Response(status=status.HTTP_400_BAD_REQUEST)
		if request.user.is_blocked_or_blocking(user):
			return Response(False, status=status.HTTP_400_BAD_REQUEST)
		if social_type == "followers":
			users = User.objects.filter(follows__following=user)
		else:
			users = User.objects.filter(followers__user=user)
		if max_last_date != "":
			users = users.filter(created__lt= max_last_date)

		serializer = sz.LiteUserSerializer(users[:100],many=True)
		return Response(serializer.data)


class SuggestedUsersView(APIView):

	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request,format=None):
		users = request.user.suggested_users()

		serializer = sz.UserSerializer(users,many=True,context={'user': request.user})
		return Response(serializer.data)


class FollowRequestsView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request, **kwargs):
		requests = FollowRequest.objects.filter(following=request.user)
		serializer = sz.FollowRequestSerializer(requests,many=True)
		return Response(serializer.data)

	def post(self, request, **kwargs):
		follow_request = get_object_or_404(FollowRequest, id = request.data["id"])

		if follow_request.following == request.user:
			follow_request.is_approved = request.data["is_approved"]
			follow_request.save()
			serializer = sz.FollowRequestSerializer(follow_request)
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response("didnt work")

class ObjectionView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request, **kwargs):
		users = User.objects.filter(blocks_received__user=request.user)	
		serializer = sz.LiteUserSerializer(users,many=True)
		return Response(serializer.data)

	def post(self, request, **kwargs):
		if request.data["object_type"] == "item":
			item = get_object_or_404(Item, id = request.data["id"])
			if item.user == request.user:
				return Response(False, status=status.HTTP_400_BAD_REQUEST)
			flag = Flag.objects.create(user=request.user,item=item)
		elif request.data["object_type"] == "comment":
			comment = get_object_or_404(Comment, id = request.data["id"])
			if comment.user == request.user:
				return Response(False, status=status.HTTP_400_BAD_REQUEST)
			flag = Flag.objects.create(user=request.user,comment=comment)
		elif request.data["object_type"] == "user":
			user = get_object_or_404(User, id = request.data["id"])
			if user == request.user:
				return Response(False, status=status.HTTP_400_BAD_REQUEST)
			block = Block.objects.create(user=request.user,blocked_user=user)
		return Response(True, status=status.HTTP_201_CREATED)
	

class UsernameCheckView(APIView):

	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request,format=None):
		username = request.GET.get("username","")
		available = not User.objects.filter(username=username).exclude(id=request.user.id).exists()
		return Response(available)


class StatsView(APIView):

	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request,format=None):

		stats_by_year = Item.objects.filter(user=request.user,status=3).annotate(year=Extract("last_date","year")).values("year","item_type").annotate(item_count=Count("id"),avg_rating=Avg("rating"),var=Variance("rating")).order_by('item_type')
		stats_overall = Item.objects.filter(user=request.user,status=3).annotate(year=Value(1900)).values("year","item_type").annotate(item_count=Count("id"),avg_rating=Avg("rating"),var=Variance("rating")).order_by('item_type')
		stats = stats_by_year.union(stats_overall)
		for stat in stats:
			if stat["avg_rating"] == None:
				ass = "n/a"
			elif stat["var"] > 1.5:
				ass = "hot taker"
			elif stat["avg_rating"] < 3:
				ass = "hater"
			elif stat["avg_rating"] < 4:
				ass = "shrugger"
			else:
				ass = "lover"
			stat["assessment"] = ass
		serializer = sz.StatSerializer(stats,many=True)
		return Response(serializer.data)