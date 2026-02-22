#group_tags.py
from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter
def in_groups(user, group_list):
    """
    Usage:
    {% if request.user|in_groups:"Staff,Custodian" %}
    """
    groups = [g.strip() for g in group_list.split(",")]
    return user.groups.filter(name__in=groups).exists()
