# manual

from django.db import migrations, models
import django.db.models.deletion
from django.db.models import F

def move_activity(apps, schema_editor):
    Activity = apps.get_model("base", "Activity")
    ItemLike = apps.get_model("base", "ItemLike")

    activities = Activity.objects.all()

    Activity.objects.filter(follow__isnull=False).update(action="follow")
    Activity.objects.filter(follow_request__isnull=False).update(action="follow_request")
    Activity.objects.filter(mention_item__isnull=False).update(action="item_mention",item=F('mention_item'))
    Activity.objects.filter(save_item__isnull=False).update(action="item_save",item=F('save_item'))

    likes = Activity.objects.filter(like_item__isnull=False)
    for l in likes:
        l.item_like = l.like_item 
        l.item = l.like_item.item 
        l.action = 'like_item'
        l.save()


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0035_activity_item_like'),
    ]

    operations = [migrations.RunPython(move_activity),
    ]
