from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.views.generic import TemplateView, CreateView, ListView, DetailView, DeleteView, UpdateView
from django.views import View
from django.db.models import Count, Avg, Max
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .base.models import User, Follow, Activity, FollowRequest, Item, ItemLike, ItemTag, Comment
from .base.forms import RegisterForm, UserEditForm, ItemFormMain, ItemFormFinished, ItemEditForm, CommentForm
from django.contrib.auth import get_user_model
from django.db.models import Q, F
from django.db.models.functions import Trunc
from .base.utilities import get_button_text
from datetime import datetime
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.utils import timezone
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client


class HomePageView(TemplateView):
    template_name = "base.html"

class UserCheckMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        elif not request.user.username:
            return redirect('welcome')
        return super(UserCheckMixin, self).dispatch(request, *args, **kwargs)



class FilterableItemsMixin:

    def make_filtered_context(self,raw_items,request):
        status = request.GET.get('status', '')
        item_type = request.GET.get('item_type', '')
        tags = request.GET.get('tags', '')
        query = request.GET.get('q', '')
        items = Item.filter_items(raw_items,status, item_type, tags)
        has_new_activity = request.user.has_new_activity() 
        if tags != '':
            selected_tags = tags #get_object_or_404(ItemList,id=item_list)
        else:
            selected_tags = None
        if status != '':
            selected_status = Item.status.field.choices[int(status) - 1][1]
        else:
            selected_status = None
        if item_type != '':
            selected_item_type = item_type
        else:
            selected_item_type = None

        for item in items:
            if ItemLike.objects.filter(user=request.user,item=item):
                item.like_button = 'liked'
            else:
                item.like_button = 'like'

        for item in items:
            if Item.objects.filter(user=request.user,original_item=item):
                item.save_button = 'saved'
            else:
                item.save_button = 'save'


        #filter_params
        status_param = 'status=' + status
        if item_type != '':
            item_type_param = '&item_type=' + item_type
        else:
            item_type_param = ''
        if tags != '':
            tags_param = '&tags=' + tags
        else:
            tags_param = ''
        if query != '':
            query_param = '&q=' + query
        else:
            query_param = ''

        #pagination
        paginator = Paginator(items, 20) 
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    
        context = {
            'items': page_obj,
            'item_type_param': item_type_param,
            'selected_item_type': selected_item_type,
            'selected_tags': selected_tags,
            'selected_status': selected_status,
            'status_param': status_param,
            'query_param': query_param,
            'tags_param': tags_param,
            'item_types': Item.item_type.field.choices,
            'statuses': Item.status.field.choices,
            'has_new_activity': has_new_activity,
            'tags': ItemTag.objects.filter(item__user = request.user).values('tag').order_by('tag').distinct()
        }
        return context




class UserFollowersView(UserCheckMixin,TemplateView):

    def get(self, request, username, **kwargs):

        user = get_object_or_404(User, username = username)
        
        if username == 'gummy':
            context = {'user': user
                        ,'has_new_activity': request.user.has_new_activity() 
            }
            return render(request, 'users/gummy.html', context)
        elif user.is_private and request.user.is_following(user) == False and request.user != user:
            return redirect(to='home')
        else:
            followers = user.follower_list()
            for follower in followers:
                #follower.is_following = request.user.is_following(follower)
                follower.button_text = get_button_text(request.user,follower)

            #pagination
            paginator = Paginator(followers, 25)  # Show 25 posts per page.
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)

            context = {
                'users': page_obj,
                'title': 'followers',
                'user': user,
                'has_new_activity': request.user.has_new_activity() 
            }
            return render(request, 'users/followers.html', context)


class UserFollowingView(UserCheckMixin,TemplateView):

    def get(self, request, username, **kwargs):

        user = get_object_or_404(User, username = username)

        if username == 'gummy':
            context = {'user': user
                        ,'has_new_activity': request.user.has_new_activity() 
            }
            return render(request, 'users/gummy.html', context)
        elif user.is_private and request.user.is_following(user) == False and request.user != user:
            return redirect(to='home')
        else:
            followers = user.following_list()
            for follower in followers:
                #follower.is_following = request.user.is_following(follower)
                follower.button_text = get_button_text(request.user,follower)

            #pagination
            paginator = Paginator(followers, 25)  # Show 25 posts per page.
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)

            context = {
                'users': page_obj,
                'user': user,
                'title': 'following',
                'has_new_activity': request.user.has_new_activity() 
            }
            return render(request, 'users/followers.html', context)


class UserView(UserCheckMixin,FilterableItemsMixin,TemplateView):

    def get(self, request, username, **kwargs):
        user = get_object_or_404(User, username = username)
        raw_feed = Item.objects.filter(user=user)
        context = self.make_filtered_context(raw_feed,request)
        context["user"] = user

        if user == request.user:
            context["include_logout"] = True
            context['show_tags'] = True
        else:
            context["is_following"] = request.user.is_following(user)
            context["button_text"] = get_button_text(request.user,user)

        return render(request, 'users/user.html', context)


def FollowUser(request,username):

    if request.method == 'POST' and request.user.is_authenticated:
        user = get_object_or_404(User, username = username)

        if user != request.user:
            new_follow = Follow.toggleFollow(user=request.user, following=user)
            # low log the activity if its a new follow only. Unfollows will delete via cascade
            if new_follow:
                Activity.objects.create(user=user,follow=new_follow,action='follow')
            text = get_button_text(request.user,user)

        return HttpResponse(text) # Sending an success response
    else:
        return redirect(to='login')


class UserEditView(LoginRequiredMixin,TemplateView):

    def get(self, request, **kwargs):
        context = {
            'form': UserEditForm(instance = request.user),
            'include_logout': True,
            'user': request.user
        }
        return render(request, 'users/edit-user.html', context)

    def post(self, request, **kwargs):

        f = UserEditForm(request.POST, instance=request.user)

        if f.is_valid():
            updated_user = f.save()
            return redirect(to='activity')
        else:
            for field in f.errors:
                f[field].field.widget.attrs['class'] = 'error'
            context = {
                'form': f,
                'include_logout': True,
                'user': request.user
            }
            return render(request, "users/edit-user.html", context)


class WelcomeView(LoginRequiredMixin,TemplateView):

    def get(self, request, **kwargs):
        if request.user.username:
            return redirect('home')
        else:
            context = {
                'form': UserEditForm(instance = request.user),
                'include_logout': True,
                'user': request.user
            }
            return render(request, 'users/welcome.html', context)

    def post(self, request, **kwargs):

        f = UserEditForm(request.POST, instance=request.user)

        if f.is_valid():
            updated_user = f.save()
            return redirect(to='suggested-welcome')
        else:
            for field in f.errors:
                f[field].field.widget.attrs['class'] = 'error'
            context = {
                'form': f,
                'user': request.user
            }
            return render(request, 'users/welcome.html', context)


class LoginView(LoginView):
    redirect_authenticated_user = True
    template_name = 'users/login.html'
    
    def get_success_url(self):
        return reverse_lazy('home') 
    
    def form_invalid(self, form):
        messages.error(self.request,'Invalid username or password')
        return self.render_to_response(self.get_context_data(form=form))


class RegisterView(View):
    form_class = RegisterForm
    initial = {'key': 'value'}
    template_name = 'users/signup.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            new_user = form.save()

            new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'],
                                    )
            messages.success(request, "welcome " + form.cleaned_data['username'] + "! we started you off by following gummy, but click search to find other people to follow.")
            login(request, new_user)
            return redirect(to='home')

        return render(request, self.template_name, {'form': form})



class SearchUsersList(UserCheckMixin,TemplateView):

    def get(self, request, **kwargs):
        
        context = {}
        query = request.GET.get("q",'')
        if len(query) > 2:
            results = User.objects.filter((Q(username__icontains=query) 
            | Q(bio__icontains=query)
            | Q(email__icontains=query))
            & Q(username__isnull=False))

            for u in results:
                u.button_text = get_button_text(request.user,u)
            context = {
                'users': results,
                'has_new_activity': request.user.has_new_activity()
            }
        elif query != '':
            context['messages'] = ["Search more than 2 characters"]

        context['is_search'] = True
        context['query'] = query

        return render(request, 'search/search-users.html', context)



class SearchItemsView(UserCheckMixin,FilterableItemsMixin,TemplateView):

    def get(self, request, **kwargs):

        context = {}
        query = request.GET.get("q",'')
        mode = request.GET.get("mode",'')
        if len(query) > 2:
            if mode == 'strict':
                raw_feed = Item.objects.filter(Q(name=query) #strict match
                    & (Q(user=request.user) #owned by user
                    | Q(user__is_private=False) #public user
                    | Q(user__followers__user=request.user)),).distinct() #or one we're following
            elif mode == 'author':
                raw_feed = Item.objects.filter(Q(author=query) #strict match
                    & (Q(user=request.user) #owned by user
                    | Q(user__is_private=False) #public user
                    | Q(user__followers__user=request.user)),).distinct() #or one we're following
            else:
                raw_feed = Item.objects.filter(
                    (Q(name__icontains=query) #term matches
                        | Q(author__icontains=query)
                        | Q(note__icontains=query)
                    )
                    & (Q(user=request.user) #owned by user
                    | Q(user__is_private=False) #public user
                    | Q(user__followers__user=request.user)),).distinct() #or one we're following
            stats = raw_feed.aggregate(count=Count("id"),ratings=Count("rating"),avg_rating=Avg("rating"))
            context = self.make_filtered_context(raw_feed,request)
        else:
            context = self.make_filtered_context(Item.objects.filter(name=''),request) #no results
            if query != '':
                context['messages'] = ["Search more than 2 characters"]
            stats = None

        context['is_search'] = True
        context['query'] = query
        context['stats'] = stats

        return render(request, 'search/search-items.html', context) 

class ActivityView(UserCheckMixin,TemplateView):

    def get(self, request, **kwargs):

        user = request.user
        activities = Activity.objects.filter(user = user)
        for a in activities:
            a.original_seen = a.seen #dont lose the original setting
        activities.filter(user = user, seen = False).update(seen=True) #mark that we saw em

        paginator = Paginator(activities, 25)  
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            'activities': page_obj,
            'user': user,
            'include_logout': True,
            'follow_request_count': user.count_follow_requests()
        }

        return render(request, 'users/activity.html', context)


class UserFollowRequestsView(UserCheckMixin,TemplateView):

    def get(self, request, **kwargs):
        user = request.user
        follow_requests = FollowRequest.objects.filter(following=user,is_approved=None,auto_denied = False)
        context = {
                    'user': user,
                    'follow_requests': follow_requests
        }

        return render(request, 'users/follow-requests.html', context)

    def post(self, request, **kwargs):

            user = request.user
            f_id = request.POST['follow_request_id']
            follow_request = get_object_or_404(FollowRequest, id = f_id)
            if request.POST['response'] == 'approve':
                follow_request.is_approved = True 
                follow_request.save() # in the save function, this will make a follow
            else:
                follow_request.is_approved = False 
                follow_request.save() # in the save function, this will NOT make a follow

            follow_requests = FollowRequest.objects.filter(following=user,is_approved=None,auto_denied = False)
            if follow_requests: #if dealing with the final one, go back to activity view
                context = {
                            'user': user,
                            'follow_requests': follow_requests
                }
            else:
                return redirect('activity')

            return render(request, 'users/follow-requests.html', context)


class SuggestedView(UserCheckMixin,TemplateView):

    def get(self, request, **kwargs):
        user_list = request.user.suggested_users()
        for u in user_list:
            u.button_text = get_button_text(request.user,u)
        context = {
                        'users': user_list,
                        'has_new_activity': request.user.has_new_activity() 
            }

        return render(request, 'search/suggested.html', context)


class SuggestedWelcomeView(UserCheckMixin,TemplateView):

    def get(self, request, **kwargs):
        user_list = request.user.suggested_users()
        context = {
                        'users': user_list
            }

        return render(request, 'search/suggested-welcome.html', context)


class ItemsView(UserCheckMixin,FilterableItemsMixin,TemplateView):

    def get(self, request, **kwargs):

        items = Item.objects.filter(user=request.user)
        context = self.make_filtered_context(items,request)
        new_item = Item(user=request.user,status=1)
        form = ItemFormMain(instance=new_item)
        context['form']= form
        context['show_tags'] = True
        context['from'] = 'items'
        return render(request, 'items/items.html', context)

    def post(self,request, **kwargs):

        f = ItemFormMain(request.POST)
        if f.is_valid():                
            new_item = f.save()

            # log activity if its a save
            # if new_item.original_item:
            #     Activity.objects.create(user=new_item.original_item.user,item=new_item,action='item_save')
            if request.GET.get('status', '') == 'done':
                return redirect(to='finish-item',item_id=new_item.id)
            else:
                if request.GET.get('from', 'items') == '':
                    dest = 'items'
                else:
                    dest = request.GET.get('from', 'items')
                return redirect(to=dest)
        else:
            for field in f.errors:
                f[field].field.widget.attrs['class'] = 'error'
            context = {
                        'form': f
                        ,'messages': ["U forgot some fields"]
                    }
            return render(request, "items/item_form_main.html", context)

class ItemAddView(UserCheckMixin,FilterableItemsMixin,TemplateView):

    def get(self, request, **kwargs):

        new_item = Item(user=request.user,status=1)
        form = ItemFormMain(instance=new_item)
        context = {
            'form': form,
            'has_new_activity': request.user.has_new_activity()
        }
        return render(request, 'items/item-form-solo.html', context)

    def post(self,request, **kwargs):

        f = ItemFormMain(request.POST)
        if f.is_valid():                
            new_item = f.save()

            # log activity if its a save
            if new_item.original_item:
                Activity.objects.create(user=new_item.original_item.user,item=new_item,action='item_save')
            if request.GET.get('status', '') == 'done':
                return redirect(to='finish-item',item_id=new_item.id)
            else:
                return redirect(to='home')
        else:
            for field in f.errors:
                f[field].field.widget.attrs['class'] = 'error'
            context = {
                        'form': f
                        ,'messages': ["U forgot some fields"]
                    }
            return render(request, "items/item-form-solo.html", context)


class ItemsFeedView(UserCheckMixin,FilterableItemsMixin,TemplateView):

    def get(self, request, **kwargs):
        items = request.user.item_feed()
        context = self.make_filtered_context(items,request)
        new_item = Item(user=request.user,status=1)
        form = ItemFormMain(instance=new_item)
        context['form']= form
        context['show_tags'] = False
        context['from'] = 'home'

        popular = Item.objects.all().values('name').annotate(total=Count('name')
            ,avg_rating=Avg('rating')
            ,max_date=Max('last_date')).order_by('-total','-avg_rating','-max_date').exclude(total=1)[:3]

         # highest avg rating, at least 2 ratings i'll make that higher later
        highest_rated = Item.objects.filter(rating__gte=1).values('name').annotate(total=Count('rating')
            ,avg_rating=Avg('rating')
            ,max_date=Max('last_date')).filter(total__gte=2).order_by('-avg_rating','-total','-max_date')[:3]

        context['popular'] = popular
        context['highest_rated'] = highest_rated

        return render(request, 'items/feed.html', context)


class FinishItemView(UserCheckMixin,TemplateView):

    def get(self, request, item_id, **kwargs):
        item = get_object_or_404(Item, id = item_id)
        if item.user == request.user:
            if item.started_date is None:
                item.started_date = timezone.localdate()
            item.ended_date = timezone.localdate()
            form = ItemFormFinished(instance=item)
            context= {
                'form': form
            }

            return render(request, 'items/item_form_finished.html', context)
        else:
            return redirect(to='home')

    def post(self,request, item_id, **kwargs):
        item = get_object_or_404(Item, id = item_id)
        f = ItemFormFinished(request.POST, instance=item)

        if f.is_valid():                
            new_item = f.save(commit=False)
            if request.GET.get('status', '') == 'abandoned':
                new_item.status = 4
            else:
                new_item.status = 3
            new_item.save()
            return redirect(to='home')
        else:
            for field in f.errors:
                f[field].field.widget.attrs['class'] = 'error'
            context = {
                        'form': f
                        ,'messages': ["U forgot some fields"]
                    }
            return render(request, "items/item_form_finished.html", context)


class ItemEditView(UserCheckMixin,TemplateView):

    def get(self, request, item_id, **kwargs):

        item = get_object_or_404(Item, id = item_id)
        if item.user == request.user:
            form = ItemEditForm(instance=item)
            context= {
                'form': form,
                'item': item
            }

            return render(request, 'items/edit_item2.html', context)
        else:
            return redirect(to='home')

    def post(self,request, item_id, **kwargs):
        item = get_object_or_404(Item, id = item_id)
        f = ItemEditForm(request.POST, instance=item)

        if f.is_valid():                
            new_item = f.save(commit=False)
            if (item.status == 4 or item.status == 3) and item.ended_date is None:
                item.ended_date = datetime.now()
            if (item.status == 1 or item.status == 2):
                item.ended_date = None
                item.rating = None
            if item.ended_date is not None and item.started_date is None:
                item.started_date = item.ended_date
            new_item.save()
            return redirect(to='home')
        else:
            for field in f.errors:
                f[field].field.widget.attrs['class'] = 'error'
            context = {
                        'form': f
                        ,'messages': ["U forgot some fields"]
                        , 'item': item
                    }
            return render(request, "items/edit_item.html", context)


class ItemDetailView(UserCheckMixin,TemplateView):

    def get(self, request, item_id, **kwargs):

        item = get_object_or_404(Item, id = item_id)
        if ItemLike.objects.filter(user=request.user,item=item):
            item.like_button = 'liked'
        else:
            item.like_button = 'like'
        new_comment = Comment(item=item,user=request.user)
        f = CommentForm(instance=new_comment)
        comments = Comment.objects.filter(item=item)
        other_ratings = Item.objects.filter(name=item.name).exclude(id=item.id).aggregate(count=Count("id"),ratings=Count("rating"),avg_rating=Avg("rating"))

        context = {
            'item': item,
            'form': f,
            'comments': comments,
            'other_ratings': other_ratings
        }

        return render(request, 'items/view_item.html', context)

    def post(self,request, item_id, **kwargs):
        item = get_object_or_404(Item, id = item_id)
        if ItemLike.objects.filter(user=request.user,item=item):
            item.like_button = 'liked'
        else:
            item.like_button = 'like'

        f = CommentForm(request.POST)
        comments = Comment.objects.filter(item=item)

        if f.is_valid():                
            new_item = f.save()
            new_comment = Comment(item=item,user=request.user)
            f = CommentForm(instance=new_comment)
            context = {
                        'form': f
                        , 'item': item
                        , 'comments': comments
                    }
        else:
            for field in f.errors:
                f[field].field.widget.attrs['class'] = 'error'
            context = {
                        'form': f
                        ,'messages': ["U forgot some fields"]
                        , 'item': item
                        , 'comments': comments
                    }
        return render(request, "items/view_item.html", context)


class ItemDeleteView(UserCheckMixin,TemplateView):

    def get(self, request, item_id, **kwargs):
        item = get_object_or_404(Item, id = item_id)
        back_to = request.GET.get('from', 'items')
        if item.user == request.user:
            context = {
                'item': item
                }
            return render(request, 'items/delete-item.html', context)
        else:
            return redirect(to=back_to)

    def post(self, request, item_id, **kwargs):

        item = get_object_or_404(Item, id = item_id)
        back_to = request.GET.get('from', 'items')
        if item.user == request.user:
            item.delete()

        return redirect(to=back_to)


class SaveItemView(UserCheckMixin,TemplateView):

    def get(self, request, item_id, *args, **kwargs):

        item = get_object_or_404(Item, id = item_id)
        new_item = Item(user = request.user
            ,name = item.name
            ,author = item.author
            ,item_type = item.item_type
            ,original_item = item
            )
        form = ItemFormMain(instance = new_item)

        context = {
            'form': form,
            'has_new_activity': request.user.has_new_activity() ,
            'original_item': item,
            'from': request.GET.get('from', '')
        }

        return render(request, 'items/save-item.html', context)


def ItemLikes(request,item_id):
    # request.is_ajax() is deprecated since django 3.1
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if is_ajax:
        if request.method == 'POST' and request.user.is_authenticated:
            item = get_object_or_404(Item, id = item_id)
            ItemLike.objects.create(user=request.user,item=item)
            return JsonResponse({'status': 'Like added'})
        return JsonResponse({'status': 'Invalid request'}, status=400)
    else:
        return HttpResponseBadRequest('Invalid request')


def LikeItem(request,item_id):
    if request.method == 'GET' and request.user.is_authenticated:
        item = get_object_or_404(Item, id = item_id)
        existing_like = ItemLike.objects.filter(user=request.user,item=item)
        if existing_like:
            existing_like.delete()
            return HttpResponse("like") # Sending an success response
        else:
            m = ItemLike(user=request.user,item=item) # Creating Like Object
            m.save()  # saving it to store in database
            return HttpResponse("liked") # Sending an success response
    else:
        return HttpResponse("Request method is not a GET")


def StartItem(request,item_id):
    if request.method == 'GET' and request.user.is_authenticated:
        item = get_object_or_404(Item, id = item_id)
        if item.user == request.user:
            item.status = 2
            item.started_date = datetime.now()
            item.save()
            return HttpResponse("disabled") # Sending an success response
        else:
            return HttpResponse("") # dont change the class
    else:
        return HttpResponse("Request method is not a GET")

def CreateItem(request):
    if request.method == 'POST':
        #user = User.objects.first()
        return HttpResponse("got it")
        #item = Item.create(user=user,name=request.post.get('name', 'name'),item_type="BOOK",status=1)
        #return JsonResponse(item.values_list('name',flat=True))
    else:
        return HttpResponse("Request method is not a POST")


def AutocompleteNames(request):
    if request.method == 'GET' and request.user.is_authenticated:
        term = request.GET.get('term', 'xxx')
        # search for it containing the term, order by name (need that for distinct to work), only get 5
        names = list(Item.objects.filter(Q(name__icontains=term)).order_by('name').values_list('name',flat=True).distinct()[:5])
        return JsonResponse(names,safe=False)


def AutocompleteAuthors(request):
    if request.method == 'GET' and request.user.is_authenticated:
        term = request.GET.get('term', 'xxx')
        # search for it containing the term, order by name (need that for distinct to work), only get 5
        names = list(Item.objects.filter(Q(author__icontains=term)).order_by('author').values_list('author',flat=True).distinct()[:5])
        return JsonResponse(names,safe=False)


class StatsView(UserCheckMixin,TemplateView):

    def get(self, request, *args, **kwargs):

        year = request.GET.get('year','1900')
        if year == '1900':
            year_end = '2099-12-31'
        else:
            year_end = year + '-12-31'
        base_items = Item.objects.filter(user=request.user
            ,ended_date__gte=year + '-01-01'
            ,ended_date__lte=year_end
            ,status=3)

        item_types_count = base_items.values("item_type").annotate(count=Count("id"),rating=Avg("rating")).order_by('-count')
        item_types_rating = base_items.values("item_type").exclude(rating__isnull=True).annotate(rating=Avg("rating")).order_by('-rating')
        items = base_items.annotate(month=Trunc("ended_date","month")).order_by("-ended_date")
        months = base_items.dates("ended_date", "month","DESC")
        years = base_items.dates("ended_date", "year","DESC")
        item_type_months = base_items.annotate(month=Trunc("ended_date","month"),year=Trunc("ended_date","year")
            ).values("item_type","month").annotate(count=Count("id")).order_by("-count")
        year_options = Item.objects.filter(user=request.user,status=3).dates("ended_date", "year","DESC")
        #starts = Item.objects.filter(user=request.user,started_date__gte="2024-01-01").annotate(month=Trunc("started_date","month")
        #    ,end_month=Trunc("ended_date","month")).filter(
        #        Q(ended_date__isnull=True)
        #        | ~Q(month=F("end_month"))
        #    )

        context = {
            'item_types_count':item_types_count,
            'item_types_rating': item_types_rating,
            'items': items,
            'months': months,
            'years': years,
            'item_type_months': item_type_months,
            'period': int(year),
            'year_options': year_options
            #'starts': starts.order_by("started_date"),
            #'start_months': starts.order_by("month").distinct("month")
        }

        return render(request, 'items/stats.html', context)


class CommentDeleteView(UserCheckMixin,TemplateView):

    def post(self, request, comment_id, **kwargs):

        comment = get_object_or_404(Comment, id = comment_id)
        item = comment.item
        if item.user == request.user or comment.user == request.user:
            comment.delete()

        return redirect(to='view-item',item_id=item.id)
