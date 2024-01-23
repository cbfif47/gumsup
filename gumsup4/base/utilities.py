from .models import User

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