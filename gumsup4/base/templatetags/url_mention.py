from django import template
register = template.Library()

def url_mention(text):
    return text.replace('@', "{% url 'home' %}")

url_mention = register.filter(url_mention, is_safe = True)