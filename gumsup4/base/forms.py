from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Post, User

class PostForm(forms.ModelForm):
   class Meta:
     model = Post
     fields = {'what','why','category','url','superlike','original_post','user'}
     widgets = {
            "what": forms.TextInput(attrs={'placeholder': 'what are you into'
              }),
            "why": forms.Textarea(attrs={'placeholder': 'why do you like it'
              ,"rows": 3}),
            "url": forms.TextInput(attrs={"placeholder": "url if you have one"
              }),
            "category": forms.RadioSelect(attrs={"class":"tab-input","name":"tab-input"}),
            "superlike": forms.CheckboxInput(attrs={"class":"tab-input","name":"tab-input"})
      }

class UserEditForm(forms.ModelForm):
   class Meta:
     model = User
     fields = {'bio'}
     widgets = {"bio": forms.Textarea(attrs={'placeholder': 'tell me about yourself'
              ,"rows": 3}),
      }


class RegisterForm(UserCreationForm):
    username = forms.CharField(max_length=100,
                               required=True,
                               widget=forms.TextInput(attrs={'placeholder': 'Username',
                                                             'class': 'form-control',
                                                             }))
    email = forms.EmailField(required=True,
                             widget=forms.TextInput(attrs={'placeholder': 'Email',
                                                           'class': 'form-control',
                                                           }))
    password1 = forms.CharField(max_length=50,
                                required=True,
                                widget=forms.PasswordInput(attrs={'placeholder': 'Password',
                                                                  'class': 'form-control',
                                                                  'data-toggle': 'password',
                                                                  'id': 'password',
                                                                  }))
    password2 = forms.CharField(max_length=50,
                                required=True,
                                widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password',
                                                                  'class': 'form-control',
                                                                  'data-toggle': 'password',
                                                                  'id': 'password',
                                                                  }))
    bio = forms.CharField(max_length=140,
                               required=False,
                               widget=forms.TextInput(attrs={'placeholder': 'bio',
                                                             'class': 'form-control',
                                                             }))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2','bio']
