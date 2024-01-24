from django import forms
from django.contrib.auth.forms import UserCreationForm
from datetime import datetime

from .models import Post, User, FollowRequest, Item

class PostForm(forms.ModelForm):
   class Meta:
     model = Post
     fields = {'what','why','category','url','superlike','original_post','user'}
     widgets = {
            "what": forms.TextInput(attrs={'placeholder': 'what are you into'
              }),
            "why": forms.Textarea(attrs={'placeholder': 'why do you like it'
              ,"rows": 3}),
            "url": forms.TextInput(attrs={"placeholder": "url (optional)"
              }),
            "category": forms.RadioSelect(attrs={"class":"tab-input"}),
            "superlike": forms.CheckboxInput(attrs={"class":"tab-input"})
      }

class UserEditForm(forms.ModelForm):

    field_order = ['username', 'bio', 'is_private']
    class Meta:
        model = User
        fields = {'bio','username','is_private'}
        labels = {'username': 'username','bio':'bio','is_private': 'private profile'}
        widgets = {"bio": forms.Textarea(attrs={'placeholder': 'tell me about yourself'
              ,"rows": 2}),
            "username": forms.TextInput(attrs={'placeholder': 'username'
              }),
            "is_private": forms.CheckboxInput()
        }


class RegisterForm(UserCreationForm):
    username = forms.CharField(max_length=100,
                               required=True,
                               widget=forms.TextInput(attrs={'placeholder': 'username',
                                                             'class': 'form-control',
                                                             }))
    email = forms.EmailField(required=True,
                             widget=forms.TextInput(attrs={'placeholder': 'email',
                                                           'class': 'form-control',
                                                           }))
    password1 = forms.CharField(max_length=50,
                                required=True,
                                label="Password",
                                widget=forms.PasswordInput(attrs={'placeholder': 'password',
                                                                  'class': 'form-control',
                                                                  }))
    password2 = forms.CharField(max_length=50,
                                required=True,
                                label="Confirm Password",
                                widget=forms.PasswordInput(attrs={'placeholder': 'confirm Password',
                                                                  }))
    bio = forms.CharField(max_length=140,
                               required=False,
                               widget=forms.Textarea(attrs={'placeholder': 'tell me about yourself',
                                                             'rows':3,
                                                             }))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2','bio']


class ItemFormMain(forms.ModelForm):

  class Meta:
   model = Item
   fields = {'name','item_type','note','user','original_item','author'}
   widgets = {
          "name": forms.TextInput(attrs={'placeholder': "title",'class': 'ui-autocomplete-input', 'id':"id_name_item"
            }),
          "author": forms.TextInput(attrs={'placeholder': '(version, year etc)','class': 'ui-autocomplete-input'}),
          "note": forms.Textarea(attrs={'placeholder': 'note/review. use @ to mention someone, # to tag stuff'
            ,"rows": 4}),
          "item_type": forms.RadioSelect(attrs={"class":"tab-input"})
    }



class ItemFormFinished(forms.ModelForm):
   class Meta:
     model = Item
     fields = {'name','note','rating','ended_date', 'started_date','hide_from_feed','author','item_type'}
     widgets = {
            "name": forms.TextInput(attrs={'placeholder': 'what is it','class': 'ui-autocomplete-input', 'id':"id_name_item"
              }),
          "author": forms.TextInput(attrs={'placeholder': 'who wrote it','class': 'ui-autocomplete-input'}),
            "note": forms.Textarea(attrs={'placeholder': 'what did you think?'
              ,"rows": 5}),
            "ended_date": forms.TextInput(),
            "started_date": forms.TextInput(),
            "rating": forms.RadioSelect(attrs={"class":"tab-input"})
      }


class ItemEditForm(forms.ModelForm):
   class Meta:
     model = Item
     fields = {'name','rating','ended_date', 'started_date','item_type','note','status','hide_from_feed','author'}
     widgets = {
            "name": forms.TextInput(attrs={'placeholder': 'what is it','class': 'ui-autocomplete-input', 'id':"id_name_item"
              }),
          "author": forms.TextInput(attrs={'placeholder': 'optional secondary info','class': 'ui-autocomplete-input'}),
            "note": forms.Textarea(attrs={'placeholder': 'note/review'
              ,"rows": 5}),
            "ended_date": forms.TextInput(),
            "started_date": forms.TextInput(),
            "item_type": forms.RadioSelect(attrs={"class":"tab-input"}),
            "status": forms.RadioSelect(attrs={"class":"tab-input"}),
            "item_type": forms.RadioSelect(attrs={"class":"tab-input"}),
            "rating": forms.RadioSelect(attrs={"class":"tab-input"})
      }

