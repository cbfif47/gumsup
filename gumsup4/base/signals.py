from django.dispatch import receiver
from allauth.account.signals import user_signed_up

@receiver(user_signed_up)
def populate_profile(sociallogin, user, **kwargs):    
    user.username = None
    user.save()