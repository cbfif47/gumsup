from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
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
