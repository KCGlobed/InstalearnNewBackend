from django import template
from subscription.models import *
from user_study.models import *
from users.models import *
from questions.models import *
from mini_lms.utils import custom_round
import math
register = template.Library()
from datetime import datetime, date


@register.filter("convert_time_format")
def convert_time_format(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    
    return "%02d:%02d:%02d" % (hour, minutes, seconds)
    

@register.filter("convert_minutes")
def convert_minutes(seconds):
    seconds = custom_round(seconds) % (24 * 3600)
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

@register.filter("report_date")
def report_date(text):
    date_time = datetime.today()
    return date_time.strftime("%B %d, %Y, %I:%M %p")


@register.filter("exam_days_left")
def exam_days_left(score):
    if score > 0:
        return score
    if abs(score) == 1:
        return ""+str(abs(score)) +" Overdue Day"
    return ""+str(abs(score)) +" Overdue Days"



@register.filter("subscription_status")
def subscription_status(value):
    if value is None:
        return OrderStatus(1).label
    return OrderStatus(value).label

@register.filter("subscription_type")
def subscription_type(value):
    return PlanType(value).label


@register.filter("currency_type")
def currency_type(value):
    return Currency(value).label


@register.filter("user_role")
def user_role(value):
    role_map = dict(User.ROLE_CHOICES)
    return role_map.get(value, None)


@register.filter("course_comma_seprated")
def course_comma_seprated(value):
    course = [item['name'] for item in value]
    return ", ".join(course)


@register.filter("difficulty_level")
def difficulty_level(value):
    return Level(value).label

