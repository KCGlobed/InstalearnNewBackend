from django import template
import requests
import urllib.request
register = template.Library()
from django.contrib.humanize.templatetags.humanize import intcomma
import math
from datetime import datetime, date


@register.filter()
def today_date(text):
    return datetime.today()


@register.filter()
def round_score(score):
    return math.ceil(score)

@register.filter()
def overdue(score):
    if score > 0:
        return score
    if abs(score) == 1:
        return ""+str(abs(score)) +" Overdue Day"
    return ""+str(abs(score)) +" Overdue Days"

@register.filter()
def performance_status(score):
    if math.ceil(score) < 26:
        return "Fair"
    elif math.ceil(score) >25 and math.ceil(score) < 51:
        return "Good"
    elif math.ceil(score) >50 and math.ceil(score) < 71:
        return "Very Good"
    elif math.ceil(score) >70:
        return "Excellent"

@register.filter()
def date_only(datetime1):
    date_format = '%Y-%m-%d'
    date_obj = datetime.strptime(datetime1[:-15], date_format).date()

    return date_obj

@register.filter()
def date_only_date(datetime1):
    date_format = '%Y-%m-%d'
    date_obj = datetime.strptime(datetime1[:-22], date_format).date()

    return date_obj


@register.filter()
def date_only_time(datetime1):
    varl = datetime.fromisoformat(datetime1)

    return varl.strftime('%I:%M %p')
    date_format = '%I:%M %p'
    date_obj = datetime.strptime(datetime1[:-22], date_format).time()

    return date_obj


@register.filter()
def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    
    return "%02d:%02d:%02d" % (hour, minutes, seconds)

@register.filter()
def convert_minutes(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    format = ""
    if hour > 0:
        format += str(hour)+"h "
    if minutes > 0:
        format += str(minutes)+"m "
    
    format += str(seconds)+"s"
    
    return format



@register.filter()
def order_id_convert(price):
    return str(price).zfill(6)
    

@register.filter()
def convert_price(price):
    if price != '':
        dollars = int(price / 100)
        return "%s%s" % (intcomma(int(dollars)), ("%0.2f" % dollars)[-3:])
    else:
        return '-'
    

@register.filter()
def calculate_discount(price, ttoal):
    cal =  int(ttoal) -  int(price)
    if cal > 0:
        dollars = int(cal / 100)
        return dollars
    else:
        return 0
    

@register.filter()
def calculate_actual_amount(total_amount):
    total_a = total_amount / 100
    gst_amount = total_a - (total_a * (100/(100 + 18)))
    gst_amount = total_a - int(gst_amount)
    return "%s%s" % (intcomma(int(gst_amount)), ("%0.2f" % gst_amount)[-3:])


@register.filter()
def calculate_gst(total_amount):
    total_a = total_amount / 100
    gst_amount = total_a - (total_a * (100/(100 + 18)))
    return "%s%s" % (intcomma(int(gst_amount)), ("%0.2f" % int(gst_amount))[-3:])
    

@register.filter()
def calculate_discount_with_sign(price, ttoal):
    cal =  int(ttoal) -  int(price)
    if cal > 0:
        dollars = int(cal / 100)
        return "%s%s" % (intcomma(int(dollars)), ("%0.2f" % dollars)[-3:])
    else:
        return 0
