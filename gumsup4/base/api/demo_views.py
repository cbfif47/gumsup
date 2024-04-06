import json
from django.conf import settings
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import LiteUserSerializer
from gumsup4.base.api import demo_serializers as ds
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from ..models import User, DemoFolder, DemoSong, DemoDemo, DemoComment, DemoShare
from rest_framework import status
from django.shortcuts import get_object_or_404
import requests
from django.db.models.expressions import Window
from django.db.models.functions import RowNumber
from django.db.models import F, Q, Max
from urllib import parse
from django.views.decorators.csrf import csrf_exempt

def ParseFolders(folders):
	for folder in folders:
		print(folder.name)
		id_index = folder.url.find("folders/") + 8
		params_index = folder.url.find("?")
		if params_index > 0:
			folder_id = folder.url[id_index:params_index]
		else:
			folder_id = folder.url[id_index:1000]
		# need to do api key securley
		parsed_url = "https://www.googleapis.com/drive/v3/files?fields=nextPageToken,files(id,name, createdTime, mimeType)&q='" + folder_id + "'+in+parents&key=" + settings.GOOGLE_DRIVE_KEY
		try:
			resource_key = parse.parse_qs(parse.urlparse(folder.url).query)['resourcekey'][0]
			headers = {"X-Goog-Drive-Resource-Keys": folder_id + "/" + resource_key}
			print(headers)
			r = requests.get(parsed_url,headers = headers)
		except:
			r = requests.get(parsed_url)
		print(parsed_url)
		print(r.json())
		files = r.json()["files"]
		songs = []
		for f in files:
			file_name = f["name"]
			file_type = file_name[-3:]
			if f["mimeType"][0:5] == "audio" and (file_type == "mp3" or file_type == "m4a"):
				file_url = "https://drive.google.com/uc?export=download&id=" + f["id"]
				createdTime = f["createdTime"]
				separator = file_name.find("-")
				if separator > 0:
					song_title = file_name[0:separator].strip()
					version = file_name[(separator + 1):-4].strip()
				else:
					song_title = file_name[0:-4].strip()
					version = "v1"
				# lets make songs if they dont exist, will default to no star or archive
				song, song_created = DemoSong.objects.get_or_create(folder=folder,title=song_title)
				songs.append(song.id)
				# same url could be referenced by multiple users
				if DemoDemo.objects.filter(song__folder=folder,url=file_url).exists() == False:
					new_demo = DemoDemo.objects.create(song=song,url=file_url,version=version,source_created=createdTime,file_extension=file_type)
				else:
					existing = DemoDemo.objects.filter(song__folder=folder,url=file_url).get()
					if existing.song != song or existing.version != version:
						existing.song = song
						existing.version = version
						existing.save()
		
		#delete songs no longer in the folder
		DemoSong.objects.filter(folder=folder).exclude(Q(id__in=songs)).delete()

		# now set priority
		songs = DemoSong.objects.filter(folder=folder)
		for song in songs:
			new_max_created = DemoDemo.objects.filter(song=song).aggregate(Max("source_created", default=""))
			if new_max_created['source_created__max'] > song.priority_as_of:
				demos = DemoDemo.objects.filter(song__folder=folder,song=song).annotate(row_number=Window(expression=RowNumber()
					,order_by=[F("source_created").desc(),F("version").asc()]))
				for demo in demos:
					demo.is_primary = (demo.row_number == 1) #all row 1s are primary TODO deal with manuals
					demo.save()
				song.priority_as_of = new_max_created['source_created__max']
				song.save()
	return True

def get_feed(request,full_refresh):
	folders = DemoFolder.objects.filter(Q(user=request.user) | Q(shares__shared_to_user=request.user))

	if full_refresh == "true":
		ParseFolders(folders)

	fs = ds.FolderSerializer(folders,many=True,context={'user': request.user})
	return fs


class MainView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get(self, request, format=None): 
		full_refresh = request.GET.get("full_refresh","")

		fs = get_feed(request,full_refresh)
		return Response(fs.data)


class EditSongView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def post(self, request, song_id, format=None):
		action = request.query_params.get("action","")
		song = get_object_or_404(DemoSong,id=song_id)
		if action == "":
			return HttpResponse("No action provided")
		elif action == "star":
			# need some sort of permission check
			song.is_starred = True
		elif action == "unstar":
			song.is_starred = False
		elif action == "archive":
			song.is_archived = True
		elif action == "unarchive":
			song.is_archived = False
		song.save()
		ss = ds.SongSerializer(song)
		return Response(ss.data)

class EditDemoView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def post(self, request, demo_id, format=None):
		is_primary = request.query_params.get("is_primary","")
		demo = get_object_or_404(DemoDemo,id=demo_id)
		song = demo.song
		other_demos = DemoDemo.objects.filter(song=song).exclude(id=demo.id)
		if is_primary == "":
			return HttpResponse("No action provided")
		elif is_primary == "true":
			# need some sort of permission check
			demo.is_primary = True
			other_demos.update(is_primary=False)
			demo.save()
		ss = ds.SongSerializer(song)
		return Response(ss.data)


class CreateCommentView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def post(self, request, demo_id, format=None):
		demo = get_object_or_404(DemoDemo,id=demo_id)
		timestamp = request.data["timestamp"]
		if timestamp >0:
			comment = DemoComment.objects.create(user=request.user,body=request.data["body"],demo=demo,timestamp=timestamp)
		else:
			comment = DemoComment.objects.create(user=request.user,body=request.data["body"],demo=demo)
		serializer = ds.DemoSerializer(demo)
		return Response(serializer.data)

	def delete(self, request, demo_id, format=None):
		comment = get_object_or_404(DemoComment,id=request.data["comment_id"])
		if comment.user == request.user:
			comment .delete()
			success = True
		else:
			success = False
		return Response(success)


class FolderView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def post(self, request, format=None):
		try: 
			folder, created = DemoFolder.objects.update_or_create(user=request.user,id=request.data["id"], defaults={"url":request.data["url"],"name": request.data["name"],"name": request.data["name"],"folder_type": request.data["folder_type"]})
		except:
			folder, created = DemoFolder.objects.update_or_create(user=request.user,url=request.data["url"], defaults={"name": request.data["name"],"name": request.data["name"],"folder_type": request.data["folder_type"]})
		if created == True:
			serializer = get_feed(request,"true")
		else:
			serializer = get_feed(request,"false")
		return Response(serializer.data)

	def delete(self, request, format=None):
		folder = get_object_or_404(DemoFolder,id=request.data["id"])
		if folder.user == request.user:
			folder.delete()
			return Response(True)
		else:
			return Response(False)


# share view for deleting shares if person who shared or person shared to, also to handle following link
class ShareView(APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]
	
	def post(self, request, format=None):
		folder = get_object_or_404(DemoFolder,key=request.data["key"])

		if not DemoShare.objects.filter(shared_to_user=request.user,folder=folder).exists() and folder.user != request.user:
			new_share = DemoShare.objects.create(user=folder.user,folder=folder,shared_to_user=request.user,can_edit=False)
	        # now lets refresh their feed, itll include this one now. i can make that a function
		fs = get_feed(request,full_refresh="false")
		return Response(fs.data)
			
	def delete(self, request, format=None):
		share = get_object_or_404(DemoShare,id=request.data["id"])
		if share.folder.user == request.user or share.shared_to_user == request.user:
			share.delete()
			return Response(True)


@csrf_exempt
def AppleSiteAssociationView(request):
	the_json = """{
				  "applinks": {
       			  "apps": [],
				      "details": [
				           {
				             "appIDs": [ "SN4RBG3Z5J.rexwithfriends.demoitis" ],
				             "components": [
				               {
				                  "/": "demoitis/sharelink",
				                  "?": { "key": * }
				               }
				             ]
				           }
				       ]
				   }
				}"""
	return JsonResponse(json.loads(the_json))

