from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.views.generic import TemplateView, CreateView, ListView, DetailView, DeleteView, UpdateView
from django.views import View
from django.db.models import Count, Avg, Max
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib import messages
from .base.models import Post, User, Follow, SavedPost, Activity, FollowRequest, Item, ItemList, ItemLike, ItemTag
from .base.forms import PostForm, RegisterForm, UserEditForm, ItemFormMain, ItemFormFinished, ItemEditForm
from django.contrib.auth import get_user_model
from django.db.models import Q, F
from django.db.models.functions import Trunc
from .base.utilities import get_button_text
from datetime import datetime
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.utils import timezone

class HomePageView(TemplateView):
    template_name = "base.html"

class FilterablePostsMixin:

    def make_filtered_context(self,raw_feed,request):
        superlike = request.GET.get('superlike', 'n')
        category = request.GET.get('category', '')
        query = request.GET.get('q', '')
        feed = Post.filter_posts(raw_feed,superlike, category)
        has_new_activity = request.user.has_new_activity() 

        #filter_params
        superlike_param = 'superlike=' + superlike
        if category != '':
            category_param = '&category=' + category
        else:
            category_param = ''
        if query != '':
            query_param = '&q=' + query
        else:
            query_param = ''

        for p in feed:
            p.is_saved = p.is_saved(request.user)

        #pagination
        paginator = Paginator(feed, 25)  # Show 25 posts per page.
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    
        context = {
            'posts': page_obj,
            'category_param': category_param,
            'selected_category': category,
            'superlike_param': superlike_param,
            'query_param': query_param,
            'categories': Post.category.field.choices,
            'has_new_activity': has_new_activity
        }
        return context


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
                item.like_button = 'unlike'
            else:
                item.like_button = 'like'

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
        paginator = Paginator(items, 25)  # Show 25 posts per page.
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


class PostsPageView(FilterablePostsMixin,TemplateView):

    def get(self, request, **kwargs):

        if request.user.is_authenticated:
            user = request.user
            context = self.make_filtered_context(user.feed(),request)

            # for form
            new_post = Post(user=user)
            form = PostForm(instance = new_post)
            context['form'] = form
            context['is_feed'] = True

            return render(request, 'posts/posts.html', context)
        else:
            return redirect(to='login')

    def post(self,request, **kwargs):

        if request.user.is_authenticated:
            f = PostForm(request.POST)

            if f.is_valid():
                f.save()
            else:
                for field in f.errors:
                    f[field].field.widget.attrs['class'] = 'error'
                user = request.user
                context = self.make_filtered_context(user.feed(),request)
                context['form'] = f
                context['messages'] = ["U forgot some fields"]
                return render(request, "posts/posts.html", context)

            return redirect(to='home') 


class PostView(TemplateView):

    def post(self, request, post_id, *args, **kwargs):

        if request.user.is_authenticated:
            context = {}

            post = get_object_or_404(Post, id = post_id)

            if request.user == post.user:
                post.delete()

            return redirect(to='home')
        else:
            return redirect(to='login')

    # todo single post view
    def get(self, request, post_id,**kwargs):
        if request.user.is_authenticated:
            post = get_object_or_404(Post, id = post_id)
            post.is_saved = post.is_saved(request.user)
            context = {
                'post': post,
                'has_new_activity': request.user.has_new_activity() 
            }

            return render(request, 'posts/post.html', context)
        else:
            return redirect(to='login')


class SavedPostView(TemplateView):

    def post(self, request, post_id, *args, **kwargs):
        if request.user.is_authenticated:
            context = {}

            post = get_object_or_404(Post, id = post_id)

            if request.user != post.user:
                if SavedPost.objects.filter(user=request.user,post=post).exists():
                    # if it exists, this is an unsave
                    SavedPost.objects.filter(user=request.user,post=post).delete()
                else:
                    sp = SavedPost(user=request.user,post=post)
                    sp.save()
                    Activity.objects.create(user=post.user,saved_post=sp)

            return redirect(to='home')
        else:
            return redirect(to='login')


class SavedPostsView(FilterablePostsMixin,TemplateView):

    def get(self, request, **kwargs):

        if request.user.is_authenticated:
            raw_feed = request.user.saved_posts()
            context = self.make_filtered_context(raw_feed,request)
            context['is_saves'] = True

            return render(request, 'posts/saved_posts.html', context)
        else:
            return redirect(to='login')



class RePostView(TemplateView):

    def get(self, request, post_id, *args, **kwargs):

        if request.user.is_authenticated:
            context = {}

            post = get_object_or_404(Post, id = post_id)
            new_post = Post(what = post.what
                , user = request.user
                ,url = post.url
                ,category = post.category
                ,original_post = post)
            form = PostForm(instance = new_post)

            context = {
                'form': form
                ,'original_post': post,
                'has_new_activity': request.user.has_new_activity() 
            }

            return render(request, 'posts/repost.html', context)
        else:
            return redirect(to='login')

    def post(self,request,post_id, *args, **kwargs):

        if request.user.is_authenticated:
            f = PostForm(request.POST)

            if f.is_valid():
                f.save()
            else:
                for field in f.errors:
                    f[field].field.widget.attrs['class'] = 'error'
                post = get_object_or_404(Post, id = post_id)
                context = {
                            'form': f
                            ,'original_post': post
                            ,'messages': ["U forgot some fields"]
                        }
                return render(request, "posts/repost.html", context)

            return redirect(to='home') 
        else:
            return redirect(to='login')


class UserFollowersView(TemplateView):

    def get(self, request, username, **kwargs):

        if request.user.is_authenticated:

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
                    follower.is_following = request.user.is_following(follower)

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
        else:
            return redirect(to='login')


class UserFollowingView(TemplateView):

    def get(self, request, username, **kwargs):
        
        if request.user.is_authenticated:

            user = get_object_or_404(User, username = username)

            if username == 'gummy':
                context = {'user': user
                            ,'has_new_activity': request.user.has_new_activity() 
                }
                return render(request, 'users/gummy.html', context)
            elif user.is_private and request.user.is_following(user) == False:
                return redirect(to='home')
            else:
                followers = user.following_list()
                for follower in followers:
                    follower.is_following = request.user.is_following(follower)

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
        else:
            return redirect(to='login')


class UserView(FilterableItemsMixin,TemplateView):

    def get(self, request, username, **kwargs):
        if request.user.is_authenticated:
            user = get_object_or_404(User, username = username)
            raw_feed = Item.objects.filter(user=user)
            context = self.make_filtered_context(raw_feed,request)
            context["user"] = user

            if user == request.user:
                context["include_logout"] = True
                context["has_lists"] = user.has_lists()
            else:
                context["is_following"] = request.user.is_following(user)
                context["button_text"] = get_button_text(request.user,user)

            return render(request, 'users/user.html', context)
        else:
            return redirect(to='login')


def FollowUser(request,username):

    if request.method == 'POST' and request.user.is_authenticated:
        user = get_object_or_404(User, username = username)

        if user != request.user:
            new_follow = Follow.toggleFollow(user=request.user, following=user)
            # low log the activity if its a new follow only. Unfollows will delete via cascade
            if new_follow:
                Activity.objects.create(user=user,follow=new_follow)
            text = get_button_text(request.user,user)

        return HttpResponse(text) # Sending an success response
    else:
        return redirect(to='login')


class UserEditView(TemplateView):

    def get(self, request, **kwargs):
        if request.user.is_authenticated:
            context = {
                'form': UserEditForm(instance = request.user),
                'include_logout': True,
                'user': request.user
            }
            return render(request, 'users/edit-user.html', context)
        else:
            return redirect(to='login')

    def post(self, request, **kwargs):

        if request.user.is_authenticated:
            f = UserEditForm(request.POST, instance=request.user)

            if f.is_valid():
                updated_user = f.save()
                return redirect(to='user',username = updated_user.username)
            else:
                for field in f.errors:
                    f[field].field.widget.attrs['class'] = 'error'
                context = {
                    'form': f,
                    'include_logout': True,
                    'user': request.user
                }
                return render(request, "users/edit-user.html", context)
        else:
            return redirect(to='login')


class WelcomeView(TemplateView):

    def get(self, request, **kwargs):
        if request.user.is_authenticated:
            if request.user.username:
                return redirect('home')
            else:
                context = {
                    'form': UserEditForm(instance = request.user),
                    'include_logout': True,
                    'user': request.user
                }
                return render(request, 'users/welcome.html', context)
        else:
            return redirect(to='login')

    def post(self, request, **kwargs):

        if request.user.is_authenticated:
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
        else:
            return redirect(to='login')


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



class SearchUsersList(TemplateView):

    def get(self, request, **kwargs):
        
        context = {}
        if request.user.is_authenticated:
            query = request.GET.get("q",'')
            if len(query) > 2:
                results = User.objects.filter(Q(username__icontains=query) 
                | Q(bio__icontains=query)
                | Q(email=query))
                context = {
                    'users': results,
                    'has_new_activity': request.user.has_new_activity()
                }
            elif query != '':
                context['messages'] = ["Search more than 2 characters"]

            context['is_search'] = True
            context['query'] = query

            return render(request, 'search/search-users.html', context)
        else:
            return redirect(to='login')


class SearchPostsView(FilterablePostsMixin,TemplateView):

    def get(self, request, **kwargs):

        context = {}
        if request.user.is_authenticated:
            query = request.GET.get("q",'')
            if len(query) > 2:
                raw_feed = Post.objects.filter(Q(what__icontains=query)
            | Q(why__icontains=query))
                context = self.make_filtered_context(raw_feed,request)
            else:
                context = self.make_filtered_context(Post.objects.filter(what=''),request) #no results
                if query != '':
                    context['messages'] = ["Search more than 2 characters"]

            context['is_search'] = True
            context['query'] = query

            return render(request, 'search/search-posts.html', context)
        else:
            return redirect(to='login')


class SearchItemsView(FilterableItemsMixin,TemplateView):

    def get(self, request, **kwargs):

        context = {}
        if request.user.is_authenticated:
            query = request.GET.get("q",'')
            mode = request.GET.get("mode",'')
            if len(query) > 2:
                if mode == 'strict':
                    raw_feed = Item.objects.filter(Q(name=query) #strict match
                        & (Q(user=request.user) #owned by user
                        | Q(user__is_private=False) #public user
                        | Q(user__followers__user=request.user)),).distinct() #or one we're following
                else:
                    raw_feed = Item.objects.filter(Q(name__icontains=query) #term matches
                        & (Q(user=request.user) #owned by user
                        | Q(user__is_private=False) #public user
                        | Q(user__followers__user=request.user)),).distinct() #or one we're following
                context = self.make_filtered_context(raw_feed,request)
            else:
                context = self.make_filtered_context(Item.objects.filter(name=''),request) #no results
                if query != '':
                    context['messages'] = ["Search more than 2 characters"]

            context['is_search'] = True
            context['query'] = query

            return render(request, 'search/search-items.html', context)
        else:
            return redirect(to='login')

class ActivityView(TemplateView):

    def get(self, request, **kwargs):

        if request.user.is_authenticated:

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

        else:
            return redirect(to='login')

class UserPrivacyView(TemplateView):

    def post(self, request, username, **kwargs):

        user = get_object_or_404(User, username = username)

        if user == request.user:
            if user.is_private == False: #this means were taking it private
                user.is_private = True
                user.save()
            else:
                user.is_private = False
                user.save()

                # auto approve all follow requests
                for fr in FollowRequest.objects.filter(following=user):
                    fr.is_approved = True
                    fr.save()    # the save method will create the follows

            return redirect(to='user',username = username)
        else:
            return redirect(to='home')


class UserFollowRequestsView(TemplateView):

    def get(self, request, username, **kwargs):
        if request.user.is_authenticated:
            user = get_object_or_404(User, username = username)
            if user == request.user:
                follow_requests = FollowRequest.objects.filter(following=user,is_approved=None,auto_denied = False)
                context = {
                            'user': user,
                            'follow_requests': follow_requests
                }

                return render(request, 'users/follow-requests.html', context)
            else:
                return redirect(to='login')
        else:
            return redirect(to='login')

    def post(self, request, username, **kwargs):

        if request.user.is_authenticated:
            user = get_object_or_404(User, username = username)

            if user == request.user:
                f_id = request.POST['follow_request_id']
                follow_request = get_object_or_404(FollowRequest, id = f_id)
                if request.POST['response'] == 'approve':
                    follow_request.is_approved = True 
                    follow_request.save() # in the save function, this will make a follow
                else:
                    follow_request.is_approved = False 
                    follow_request.save() # in the save function, this will NOT make a follow

                follow_requests = FollowRequest.objects.filter(following=user,is_approved=None,auto_denied = False)
                context = {
                            'user': user,
                            'follow_requests': follow_requests
                }

                return render(request, 'users/follow-requests.html', context)


        else:
            return redirect(to='login')


class SuggestedView(TemplateView):

    def get(self, request, **kwargs):
        if request.user.is_authenticated:
            user_list = request.user.suggested_users()
            context = {
                            'users': user_list,
                            'has_new_activity': request.user.has_new_activity() 
                }

            return render(request, 'search/suggested.html', context)
        else:
            return redirect(to='login')


class SuggestedWelcomeView(TemplateView):

    def get(self, request, **kwargs):
        if request.user.is_authenticated:
            user_list = request.user.suggested_users()
            context = {
                            'users': user_list
                }

            return render(request, 'search/suggested-welcome.html', context)
        else:
            return redirect(to='login')


class ItemsView(FilterableItemsMixin,TemplateView):

    def get(self, request, **kwargs):

        if request.user.is_authenticated:
            items = Item.objects.filter(user=request.user)
            context = self.make_filtered_context(items,request)
            new_item = Item(user=request.user,status=1)
            form = ItemFormMain(instance=new_item)
            context['form']= form
            context['show_tags'] = True
            context['from'] = 'items'

            return render(request, 'items/items.html', context)
        else:
            return redirect(to='login')

    def post(self,request, **kwargs):
        if request.user.is_authenticated:

            f = ItemFormMain(request.POST)
            if f.is_valid():                
                new_item = f.save()

                # log activity if its a save
                if new_item.original_item:
                    Activity.objects.create(user=new_item.original_item.user,save_item=new_item)
                if request.GET.get('status', '') == 'done':
                    return redirect(to='finish-item',item_id=new_item.id)
                else:
                    return redirect(to=request.GET.get('from', ''))
            else:
                for field in f.errors:
                    f[field].field.widget.attrs['class'] = 'error'
                context = {
                            'form': f
                            ,'messages': ["U forgot some fields"]
                        }
                return render(request, "items/item_form_main.html", context)
        else:
            return redirect(to='login')


class ItemsFeedView(FilterableItemsMixin,TemplateView):

    def get(self, request, **kwargs):

        if request.user.is_authenticated:
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
        else:
            return redirect(to='login')


class FinishItemView(TemplateView):

    def get(self, request, item_id, **kwargs):

        if request.user.is_authenticated:
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
        else:
            return redirect(to='login')

    def post(self,request, item_id, **kwargs):
        if request.user.is_authenticated:
            item = get_object_or_404(Item, id = item_id)
            f = ItemFormFinished(request.POST, instance=item)

            if f.is_valid():                
                new_item = f.save(commit=False)
                if request.GET.get('status', '') == 'abandoned':
                    item.status = 4
                else:
                    item.status = 3
                new_item.save()
                return redirect(to='items')
            else:
                for field in f.errors:
                    f[field].field.widget.attrs['class'] = 'error'
                context = {
                            'form': f
                            ,'messages': ["U forgot some fields"]
                        }
                return render(request, "items/item_form_finished.html", context)
        else:
            return redirect(to='login')


class ItemEditView(TemplateView):

    def get(self, request, item_id, **kwargs):

        if request.user.is_authenticated:
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
        else:
            return redirect(to='login')

    def post(self,request, item_id, **kwargs):
        if request.user.is_authenticated:
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
                return redirect(to='items')
            else:
                for field in f.errors:
                    f[field].field.widget.attrs['class'] = 'error'
                context = {
                            'form': f
                            ,'messages': ["U forgot some fields"]
                            , 'item': item
                        }
                return render(request, "items/edit_item.html", context)
        else:
            return redirect(to='login')


class ItemDetailView(TemplateView):

    def get(self, request, item_id, **kwargs):

        if request.user.is_authenticated:
            item = get_object_or_404(Item, id = item_id)
            if ItemLike.objects.filter(user=request.user,item=item):
                item.like_button = 'unlike'
            else:
                item.like_button = 'like'

            context = {
                'item': item
            }

            return render(request, 'items/view_item.html', context)
        else:
            return redirect(to='login')


class ItemDeleteView(TemplateView):

    def get(self, request, item_id, **kwargs):

        if request.user.is_authenticated:
            item = get_object_or_404(Item, id = item_id)
            back_to = request.GET.get('from', 'items')
            if item.user == request.user:
                context = {
                    'item': item
                    }
                return render(request, 'items/delete-item.html', context)
            else:
                return redirect(to=back_to)
        else:
            return redirect(to='login')

    def post(self, request, item_id, **kwargs):

        if request.user.is_authenticated:
            item = get_object_or_404(Item, id = item_id)
            back_to = request.GET.get('from', 'items')
            if item.user == request.user:
                item.delete()

            return redirect(to=back_to)
        else:
            return redirect(to='login')


class ItemListView(FilterableItemsMixin,TemplateView):
    
    def post(self, request, item_list_id, **kwargs):
        if request.user.is_authenticated:
            item_list = get_object_or_404(ItemList, id = item_list_id)
            back_to = request.GET.get('from', 'items')
            if item.user == request.user:
                item.status = 2
                item.started_date = datetime.now()
                item.save()

            return redirect(to=back_to)
        else:
            return redirect(to='login')

    def get(self, request, item_list_id, **kwargs):
        if request.user.is_authenticated:
            item_list = get_object_or_404(ItemList, id = item_list_id)
            items = Item.objects.filter(item_list=item_list)
            if item_list.user == request.user:
                context = self.make_filtered_context(items,request)
                context['item_list'] = item_list

            return render(request, 'item_lists/view_item_list.html', context)
        else:
            return redirect(to='login')


class ItemListCreateView(CreateView):
    model = ItemList
    fields = ["name"]
    template_name = "item_lists/item_list_form.html"

    def get_success_url(self):
        return f'/items/'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ItemListDeleteView(DeleteView):
    # specify the model you want to use
    model = ItemList
    success_url ="/items"
     
    template_name = "item_lists/confirm_delete.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.user == request.user:
            #reassign to default list if needed
            default_list = ItemList.objects.get(user=request.user,is_default=True)
            items = Item.objects.filter(item_list=self.object)
            for item in items:
                item.item_list = default_list
                item.save()
            success_url = self.get_success_url()
            self.object.delete()
            return redirect(success_url)
        else:
            return http.HttpResponseForbidden("Cannot delete other's lists") #todo this doesnt work


class ItemListListView(ListView):
    # specify the model you want to use
    model = ItemList
    paginate_by = 100
    context_object_name = 'item_lists'
    template_name = "item_lists/item_lists.html"
    def get_queryset(self):
        return ItemList.objects.filter(user=self.request.user)


class ItemListEditView(UpdateView):
    model = ItemList
    fields = ["name"]
    template_name = "item_lists/item_list_form.html"

    def get_success_url(self):
        return f'/item-lists/{self.object.pk}/'


class SaveItemView(TemplateView):

    def get(self, request, item_id, *args, **kwargs):

        if request.user.is_authenticated:

            item = get_object_or_404(Item, id = item_id)
            new_item = Item(item = item
                , user = request.user
                ,name = item.name
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
        else:
            return redirect(to='login')

    def post(self,request,post_id, *args, **kwargs):
        # THIS ISNT ACTUALLY USED, THE SAVE POST FORM POINTS TO THE ITEMS VIEW

        if request.user.is_authenticated:

            f = ItemFormMain(request.POST)
            original_item = get_object_or_404(Item, id = item_id)
            f.original_item = original_item

            if f.is_valid():                
                new_item = f.save()

                #log activity
                Activity.objects.create(user=original_item.user,save_item=new_item)
                return redirect(to=request.GET.get('from', 'home'))
            else:
                for field in f.errors:
                    f[field].field.widget.attrs['class'] = 'error'
                context = {
                            'form': f
                            ,'messages': ["U forgot some fields"]
                        }
                return render(request, "items/save-item.html", context)
        else:
            return redirect(to='login')


def ItemLikes(request,item_id):
    # request.is_ajax() is deprecated since django 3.1
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if is_ajax:
        if request.method == 'POST':
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
            return HttpResponse("unlike") # Sending an success response
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


class ItemStartView(TemplateView):

    def post(self, request, item_id, **kwargs):

        if request.user.is_authenticated:
            item = get_object_or_404(Item, id = item_id)
            back_to = request.GET.get('from', 'items')
            if item.user == request.user:
                item.status = 2
                item.started_date = datetime.now()
                item.save()

            return redirect(to=back_to)
        else:
            return redirect(to='login')

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


class StatsView(TemplateView):

    def get(self, request, *args, **kwargs):

        if request.user.is_authenticated:

            item_types_count = Item.objects.filter(user=request.user,
                ended_date__gte="2024-01-01",status=3).values("item_type").annotate(count=Count("id"),rating=Avg("rating")).order_by('-count')
            item_types_rating = Item.objects.filter(user=request.user,
                ended_date__gte="2024-01-01",status=3).values("item_type").exclude(rating__isnull=True).annotate(rating=Avg("rating")).order_by('-rating')
            items = Item.objects.filter(user=request.user,ended_date__gte="2024-01-01",status=3).annotate(month=Trunc("ended_date","month")).order_by("ended_date")
            months = Item.objects.filter(user=request.user,ended_date__gte="2024-01-01",status=3).dates("ended_date", "month")
            item_type_months = Item.objects.filter(user=request.user,
                ended_date__gte="2024-01-01",status=3).annotate(month=Trunc("ended_date","month")
                ).values("item_type","month").annotate(count=Count("id")).order_by("-count")
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
                'item_type_months': item_type_months
                #'starts': starts.order_by("started_date"),
                #'start_months': starts.order_by("month").distinct("month")
            }

            return render(request, 'items/stats.html', context)
        else:
            return redirect(to='login')
