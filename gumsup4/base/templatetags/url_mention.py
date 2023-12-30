from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils import timezone
import re
register = template.Library()
from ..models import User

@register.filter(name='url_mention', is_safe=True)
@stringfilter
def url_mention(text):
    mentions = re.findall("@[-\w]*",text)
    for mention in mentions:
        username = mention.replace("@","")
        user = User.objects.filter(username=username)
        if user:
            text = text.replace(mention
                            ,"""<a href="/users/""" + username + '" class="mention">'
                            + mention + '</a>')
    return mark_safe(text)


@register.filter(name='dayssince', is_safe=True)
def dayssince(value):
    "Returns number of days between today and value."
    today = timezone.now().date()
    diff  = today - value
    if diff.days > 1:
        return '%s days ago' % diff.days
    elif diff.days == 1:
        return 'yesterday'
    elif diff.days == 0:
        return 'today'
    else:
        # Date is in the future; return formatted date.
        return value.strftime("%B %d, %Y")


@register.filter(name='statustoaction', is_safe=True)
def statustoaction(status):
    if status == 1:
        return 'saved'
    elif status == 2:
        return 'started'
    elif status == 3:
        return 'finished'
    elif status == 4:
        return 'quit'

@register.filter(name='statustoemoji', is_safe=True)
def statustoemoji(status):
    if status == 1:
        return ''
    elif status == 2:
        return '⏳'
    elif status == 3:
        return '✅'
    elif status == 4:
        return '❌'
