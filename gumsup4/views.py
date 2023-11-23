from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.views.generic import TemplateView, CreateView, ListView
from django.views import View
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib import messages
from .base.models import Post, User, Follow, SavedPost, Activity, FollowRequest
from .base.forms import PostForm, RegisterForm, UserEditForm
from django.contrib.auth import get_user_model
from django.db.models import Q
from .base.utilities import get_button_text

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
                new_repost = f.save()
                # now make the activity
                Activity.objects.create(user=new_repost.original_post.user,repost=new_repost)
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
                form = UserEditForm(instance = user)
                context["form"] = form
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
                form = None
            else:
                f = UserEditForm(request.POST, instance=user)

                if f.is_valid():
                    f.save()
                form = UserEditForm(instance = user)

            context = {
                'posts': Post.objects.filter(user=user),
                'user': user,
                'button_text': get_button_text(request.user,user),
                'form': form
            }
            return render(request, 'users/user.html', context)
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