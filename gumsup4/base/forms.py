from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Post, User, FollowRequest

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
            "category": forms.RadioSelect(attrs={"class":"tab-input","name":"tab-input"}),
            "superlike": forms.CheckboxInput(attrs={"class":"tab-input","name":"tab-input"})
      }

class UserEditForm(forms.ModelForm):

    field_order = ['username', 'bio', 'is_private']
    class Meta:
        model = User
        fields = {'bio','username','is_private'}
        labels = {'is_private': 'private profile'}
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

