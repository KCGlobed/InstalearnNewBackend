from rest_framework import serializers
from users.models import *
from subscription.models import *
from mini_lms.utils import *
from itertools import chain
import pytz
from django.db.models import Q, Count



class StaffUserListSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = User
        fields = ["id",'first_name',"last_name","email","role","is_active","created_at"]

