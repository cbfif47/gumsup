from django.urls import path
from gumsup4 import chris_views

urlpatterns = [
    path('', chris_views.ChrisHomeView.as_view(), name='chris-home'),
]
