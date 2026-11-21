from django.template.defaultfilters import register


@register.filter
def hash(h, key):
    return h[key]


@register.filter
def pluralize(value, arg="contact,contacts,contacts"):
    args = arg.split(',')
    number = abs(int(value))
    a = number % 10
    b = number % 100

    if a == 1 and b != 11:
        return args[0]
    elif a in (2, 3, 4) and (b < 10 or b >= 20):
        return args[1]
    return args[2]


@register.filter
def multiply(value, multiplier):
    return value * multiplier
