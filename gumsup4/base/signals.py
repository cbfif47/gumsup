from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from push_notifications.models import APNSDevice
from django.db.models.signals import post_save
from .models import Activity
import threading

@receiver(user_signed_up)
def populate_profile(sociallogin, user, **kwargs):    
    user.username = None
    user.save()

def send_push_async(user_id, message_text, badge = 1):
    # Fetch devices and send APNs push outside the HTTP request thread!
    devices = APNSDevice.objects.filter(user_id=user_id, active=True)
    device_num = devices.count()
    print(device_num)
    if device_num == 0:
        print("no device to notify")
        return
    devices.send_message(message=message_text, badge = badge)
    print("push sent")

@receiver(post_save, sender=Activity)
def send_activity_push_notification(sender, instance, created, **kwargs):
    # Only send a push when the Activity record is first created
    if not created:
        return
    # 1. Determine target user
    target_user = instance.user
    # 2. Build the notification text based on the relation fields
    message = ""
    extra_data = {
        "activity_id": str(instance.id),
        "action": instance.action or ""
    }
    if instance.comment:
        commenter = instance.comment.user.username
        item_name = instance.comment.item.name
        message = f"{commenter} commented on your post about {item_name}"
        extra_data["item_id"] = str(instance.comment.item.id)
        # extra_data["type"] = "comment"
    elif instance.item_like:
        liker = instance.item_like.user.username
        item_name = instance.item_like.item.name
        message = f"{liker} liked your post about {item_name}"
        extra_data["item_id"] = str(instance.item_like.item.id)
        # extra_data["type"] = "like"
    elif instance.follow:
        # Assuming follow model relates to the acting user
        follower = instance.follow.user.username 
        message = f"{follower} followed you"
        # extra_data["type"] = "follow"
        
    elif instance.follow_request:
        requester = instance.follow_request.user.username 
        message = f"{requester} requested to follow you"
        # extra_data["type"] = "follow_request"
        
    else:
        # Fallback to action string
        message = instance.action or "New action in Rex!"
    # Avoid sending empty messages
    if not message:
        return
    # 3. Calculate unseen activity count to update the app's badge count
    unread_badge_count = Activity.objects.filter(user=target_user, seen=False).count()
    # 5. Dispatch the message
    try:
        print("sending push")
        print(message)
        print(unread_badge_count)
        thread = threading.Thread(
            target=send_push_async,
            args=(target_user, message, unread_badge_count)
        )
        thread.start()
    except Exception as e:
        # Catch network or key issues so it doesn't crash the database save operation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send push notification to {target_user}: {e}")
    return True