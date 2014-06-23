from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
@stringfilter
def trim(value):
    return value.strip()


@register.filter(name='obscure_except_ending')
def obscure_except_ending(string, trailing_chars_to_show=5):
    """
    Obscures the beginning of a string with *s and leaves
    `trailing_chars_to_show` in plaintext.
    """
    if not string:
        return ""

    string_len = len(string)

    if string_len <= trailing_chars_to_show:
        # Less to hide than exists
        return string

    reveal_len = string_len-trailing_chars_to_show

    return '*' * reveal_len + string[reveal_len:]


@register.filter(name='format_status_string')
def format_status_string(string):
    GREEN_STATUSES = ['complete', 'valid']
    # YELLOW_STATUSES = ['waiting for verifications']
    RED_STATUSES = ['canceled', 'invalid']

    if string.lower() in GREEN_STATUSES:
        return mark_safe('<span class ="text-green">%s</span> ' % (string))
    # if string.lower() in YELLOW_STATUSES:
    #     return mark_safe('<span class ="text-amethyst">%s</span>' % (string))
    elif string.lower() in RED_STATUSES:
        return mark_safe('<span class ="text-red">%s</span>' % (string))
    else:
        return mark_safe('%s' % (string))