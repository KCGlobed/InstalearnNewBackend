from rest_framework import serializers
from universities.models import *
from rolepermissions.checkers import has_role
from django.conf import settings
from django.core.mail import send_mail
from rolepermissions.roles import assign_role
from django.template import loader
from datetime import datetime, timedelta, date
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator 
from django.utils.encoding import smart_str, force_bytes
from mini_lms.utils import *
from rolepermissions.permissions import grant_permission,revoke_permission
import re


