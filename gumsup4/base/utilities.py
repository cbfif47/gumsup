from .models import User
import datetime
from django.utils import timezone

def get_button_text(user,following):
        if user.is_following(following):
            button_text = 'unfollow'
        elif user.has_requested(following) == True:
            button_text = 'requested'
        elif following.is_private == True:
            button_text = 'request'
        else:
            button_text = 'follow'
        return button_text

def cbtimesince(d):

    # Compared datetimes must be in the same time zone.
    now = timezone.now()
    delta = now - d
    result = ""
    if delta.days > 14:
        result = d.strftime("%b %d %Y")
    elif delta.days > 1:
        result = str(delta.days) + " days ago"
    elif delta.days == 1:
        result = "1 day ago"
    elif round(delta.seconds / 60 / 60) == 1:
        result = "1 hour ago"
    elif delta.seconds > 60 * 60:
        result = str(round(delta.seconds / 60 / 60)) + " hours ago"
    elif round(delta.seconds / 60) == 1:
        "1 minute ago"
    elif round(delta.seconds / 60) > 1:
        result = str(round(delta.seconds / 60)) + " minutes ago"
    else:
        result = "a few seconds ago"

    return result