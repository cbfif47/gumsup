from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils import timezone
import re
register = template.Library()
from ..models import User
import math

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
    tags = re.findall("#[-\w]*",text)
    for tag in tags:
        text = text.replace(tag
                            ,'<a href="?tags=' + tag.replace("#","") +'" class="item-tag">'
                            + tag + '</a>')
    return mark_safe(text)


@register.filter(name='dayssince', is_safe=True)
def dayssince(value):
    "Returns number of days between today and value."
    today = timezone.localdate()
    diff  = today - value
    if diff.days > 7:
        return value.strftime("%B %d, %Y")
    elif diff.days > 1:
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
        return ''

@register.filter(name='statustoimage', is_safe=True)
def statustoimage(status):
    if status == 1:
        return 'later.png'
    elif status == 2:
        return 'now.png'
    elif status == 3:
        return 'check.png'
    elif status == 4:
        return 'x.png'


@register.filter(name='itemtypeverb', is_safe=True)
def itemtypeverb(item_type):
    if item_type == "MOVIE":
        return 'watching'
    elif item_type == "BOOK":
        return 'reading'
    elif item_type == "TV":
        return 'watching'
    elif item_type == "LIFE":
        return 'living'
    elif item_type == "FOOD":
        return 'eating'

@register.filter(name='itemtypepast', is_safe=True)
def itemtypepast(item_type):
    if item_type == "MOVIE":
        return 'watched'
    elif item_type == "BOOK":
        return 'read'
    elif item_type == "TV":
        return 'watched'
    elif item_type == "LIFE":
        return 'lived'
    elif item_type == "FOOD":
        return 'ate'

@register.filter(name="ratingtoimage",is_safe=True)
def ratingtoimage(rating):
    return '''<img src="{% static 'starsmall.png' %}" height="14px">'''

@register.filter(name="ratingtobar",is_safe=True)
def ratingtobar(rating):
    r = rating - 1
    r = r * 6
    r = math.floor(r)
    txt = ''

    for i in range(r):
        txt = txt + '-'

    return txt

@register.filter(name='commentcount', is_safe=True)
def commentcount(count):
    if count == 1:
        return '1 reply'
    else:
        return str(count) + ' replies'

@register.filter(name='likecount', is_safe=True)
def likecount(count):
    if count == 1:
        return '1 like'
    else:
        return str(count) + ' likes'


import datetime

from django.utils.html import avoid_wrapping
from django.utils.timezone import is_aware
from django.utils.translation import gettext, ngettext_lazy

TIME_STRINGS = {
    "year": ngettext_lazy("%(num)d year", "%(num)d years", "num"),
    "month": ngettext_lazy("%(num)d month", "%(num)d months", "num"),
    "week": ngettext_lazy("%(num)d week", "%(num)d weeks", "num"),
    "day": ngettext_lazy("%(num)d day", "%(num)d days", "num"),
    "hour": ngettext_lazy("%(num)d hour", "%(num)d hours", "num"),
    "minute": ngettext_lazy("%(num)d minute", "%(num)d minutes", "num"),
}

TIME_STRINGS_KEYS = list(TIME_STRINGS.keys())

TIME_CHUNKS = [
    60 * 60 * 24 * 7,  # week
    60 * 60 * 24,  # day
    60 * 60,  # hour
    60,  # minute
]

MONTHS_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


@register.filter(name='mytimesince', is_safe=True)
def mytimesince(d, now=None, reversed=False, time_strings=None, depth=2):
    if time_strings is None:
        time_strings = TIME_STRINGS
    if depth <= 0:
        raise ValueError("depth must be greater than 0.")
    # Convert datetime.date to datetime.datetime for comparison.
    if not isinstance(d, datetime.datetime):
        d = datetime.datetime(d.year, d.month, d.day)
    if now and not isinstance(now, datetime.datetime):
        now = datetime.datetime(now.year, now.month, now.day)

    # Compared datetimes must be in the same time zone.
    if not now:
        now = datetime.datetime.now(d.tzinfo if is_aware(d) else None)
    elif is_aware(now) and is_aware(d):
        now = now.astimezone(d.tzinfo)

    if reversed:
        d, now = now, d
    delta = now - d

    # Ignore microseconds.
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 60:
        # d is in the future compared to now, stop processing.
        return avoid_wrapping(time_strings["minute"] % {"num": 0}) + ' ago'

    # Get years and months.
    total_months = (now.year - d.year) * 12 + (now.month - d.month)
    if d.day > now.day or (d.day == now.day and d.time() > now.time()):
        total_months -= 1
    years, months = divmod(total_months, 12)

    # Calculate the remaining time.
    # Create a "pivot" datetime shifted from d by years and months, then use
    # that to determine the other parts.
    if years or months:
        pivot_year = d.year + years
        pivot_month = d.month + months
        if pivot_month > 12:
            pivot_month -= 12
            pivot_year += 1
        pivot = datetime.datetime(
            pivot_year,
            pivot_month,
            min(MONTHS_DAYS[pivot_month - 1], d.day),
            d.hour,
            d.minute,
            d.second,
            tzinfo=d.tzinfo,
        )
    else:
        pivot = d
    remaining_time = (now - pivot).total_seconds()
    partials = [years, months]
    for chunk in TIME_CHUNKS:
        count = int(remaining_time // chunk)
        partials.append(count)
        remaining_time -= chunk * count

    # Find the first non-zero part (if any) and then build the result, until
    # depth.
    i = 0
    for i, value in enumerate(partials):
        if value != 0:
            break
    else:
        return avoid_wrapping(time_strings["minute"] % {"num": 0})

    result = []
    current_depth = 0
    while i < len(TIME_STRINGS_KEYS) and current_depth < depth:
        value = partials[i]
        if value == 0:
            break
        name = TIME_STRINGS_KEYS[i]
        result.append(avoid_wrapping(time_strings[name] % {"num": value}))
        current_depth += 1
        i += 1

    if delta.days > 14:
        return d.strftime("%b %d %Y")
    else:
        return gettext(", ").join(result) + ' ago'
