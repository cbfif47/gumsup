from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.views.generic import TemplateView, CreateView, ListView, DetailView, DeleteView
from django.views import View
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib import messages
from .base.models import Post, User, Follow, SavedPost, Activity, FollowRequest, Item, ItemList
from .base.forms import PostForm, RegisterForm, UserEditForm, ItemFormMain, ItemFormFinished, ItemEditForm
from django.contrib.auth import get_user_model
from django.db.models import Q
from .base.utilities import get_button_text
from datetime import datetime

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
        item_list = request.GET.get('item_list', '')
        query = request.GET.get('q', '')
        items = Item.filter_items(raw_items,status, item_type, item_list)
        has_new_activity = request.user.has_new_activity() 
        if item_list != '':
            selected_item_list = get_object_or_404(ItemList,id=item_list)
        else:
            selected_item_list = None
        if status != '':
            selected_status = Item.status.field.choices[int(status) - 1][1]
        else:
            selected_status = None

        #filter_params
        status_param = 'status=' + status
        if item_type != '':
            item_type_param = '&item_type=' + item_type
        else:
            item_type_param = ''
        if item_list != '':
            item_list_param = '&item_list=' + item_list
        else:
            item_list_param = ''
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
            'selected_item_type': item_type,
            'selected_item_list': selected_item_list,
            'selected_status': selected_status,
            'status_param': status_param,
            'query_param': query_param,
            'item_list_param': item_list_param,
            'item_types': Item.item_type.field.choices,
            'statuses': Item.status.field.choices,
            'has_new_activity': has_new_activity,
            'item_lists': ItemList.objects.filter(user = request.user)
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
            elif user.is_private and request.user.is_following(user) == False:
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


class UserView(FilterablePostsMixin,TemplateView):

    def get(self, request, username, **kwargs):
        if request.user.is_authenticated:
            user = get_object_or_404(User, username = username)
            raw_feed = Post.objects.filter(user=user)
            context = self.make_filtered_context(raw_feed,request)
            context["user"] = user

            if user == request.user:
                context["include_logout"] = True
            else:
                context["is_following"] = request.user.is_following(user)
                context["button_text"] = get_button_text(request.user,user)

            return render(request, 'users/user.html', context)
        else:
            return redirect(to='login')

    def post(self, request, username, **kwargs):

        if request.user.is_authenticated:
            user = get_object_or_404(User, username = username)

            if user != request.user:
                new_follow = Follow.toggleFollow(user=request.user, following=user)
                # low log the activity if its a new follow only. Unfollows will delete via cascade
                if new_follow:
                    Activity.objects.create(user=user,follow=new_follow)

            context = {
                'posts': Post.objects.filter(user=user),
                'user': user,
                'button_text': get_button_text(request.user,user),
            }
            return render(request, 'users/user.html', context)
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

class ActivityView(TemplateView):

    def get(self, request, username, **kwargs):

        if request.user.is_authenticated:

            user = get_object_or_404(User, username = username)

            if user == request.user:
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
                return redirect(to='home')

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


class ItemsView(FilterableItemsMixin,TemplateView):

    def get(self, request, **kwargs):

        if request.user.is_authenticated:
            items = Item.objects.filter(user=request.user)
            context = self.make_filtered_context(items,request)
            new_item = Item(user=request.user,status=1)
            form = ItemFormMain(instance=new_item)
            form.fields['item_list'].queryset = ItemList.objects.filter(user=request.user)
            form.fields['item_list'].empty_label="(choose list)"
            context['form']= form

            return render(request, 'items/items.html', context)
        else:
            return redirect(to='login')

    def post(self,request, **kwargs):
        if request.user.is_authenticated:

            f = ItemFormMain(request.POST)
            if f.is_valid():                
                new_item = f.save()
                if request.GET.get('status', '') == 'done':
                    return redirect(to='finish-item',item_id=new_item.id)
                else:
                    return redirect(to='items')
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


class FinishItemView(TemplateView):

    def get(self, request, item_id, **kwargs):

        if request.user.is_authenticated:
            item = get_object_or_404(Item, id = item_id)
            if item.user == request.user:
                if item.started_date is None:
                    item.started_date = datetime.now()
                item.ended_date = datetime.now()
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
                form.fields['item_list'].queryset = ItemList.objects.filter(user=request.user)
                form.fields['item_list'].empty_label="(choose list)"
                context= {
                    'form': form,
                    'item': item
                }

                return render(request, 'items/edit_item.html', context)
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
                        }
                return render(request, "items/edit_item.html", context)
        else:
            return redirect(to='login')


class ItemDetailView(TemplateView):

    def get(self, request, item_id, **kwargs):

        if request.user.is_authenticated:
            item = get_object_or_404(Item, id = item_id)
            context = {
                'item': item
            }

            return render(request, 'items/view_item.html', context)
        else:
            return redirect(to='login')


class ItemDeleteView(TemplateView):

    def post(self, request, item_id, **kwargs):

        if request.user.is_authenticated:
            item = get_object_or_404(Item, id = item_id)
            back_to = request.GET.get('from', 'items')
            if item.user == request.user:
                item.delete()

            return redirect(to=back_to)
        else:
            return redirect(to='login')


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


class ItemListView(TemplateView):
    
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
                context = {
                    'item_list': item_list,
                    'items': items
                }

            return render(request, 'item_lists/view_item_list.html', context)
        else:
            return redirect(to='login')


class ItemListCreateView(CreateView):
    model = ItemList
    fields = ["name"]
    template_name = "item_lists/item_list_form.html"

    def get_success_url(self):
        return f'/item-lists/{self.object.pk}/'

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
            success_url = self.get_success_url()
            self.object.delete()
            return redirect(success_url)
        else:
            return http.HttpResponseForbidden("Cannot delete other's lists") #todo this doesnt work
