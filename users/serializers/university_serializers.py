from rest_framework import serializers
from users.models import *
from rolepermissions.checkers import has_role
import phonenumbers
import random
import math
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



class UniversityLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length = 255,required=True)
    password = serializers.CharField(max_length = 255,required=True)
    device_type = serializers.CharField(max_length = 255, required=True)
    device_id = serializers.CharField(max_length = 255, required=True)

    class Meta:
        model = User
        fields = ['email', 'password','device_type','device_id']

    def validate(self, data):
        user = User.objects.filter(email =data.get('email').lower(), email_verified = 1).first()
        if user is None:
            raise serializers.ValidationError("User Not found with this email!")
        
        if user.is_active is False:
            raise serializers.ValidationError("User is not active!")
        
        if user.email_verified == 0:
            raise serializers.ValidationError("User email is not verified!")
        
        try:
            if not has_role(user, UniversityAdmin):
                raise serializers.ValidationError("Invalid User Role!")
        except KeyError:
            raise serializers.ValidationError("Invalid User Role!")
    
        if user:
            if not user.check_password(data.get('password')):
                raise serializers.ValidationError("Invalid Password!")
        
        return data



class UniversityForgotPasswordSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length = 255,required=True)
    class Meta:
        model = User
        fields = ['email']

    
    def validate(self, data):
        email = data.get('email')
        if User.objects.filter(email = email.lower()).exists():
            user = User.objects.get(email = email.lower())

            try:
                if not has_role(user, UniversityAdmin):
                    raise serializers.ValidationError("Invalid User!")
            except KeyError:
                raise serializers.ValidationError("Invalid User!")

    
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            
            url = settings.UNIVERSITY_BASE_URL+"/user/reset/?uid="+uid+'&token='+token

            subject = 'Reset Password Link'
            message = f'Hi {user.first_name} {user.last_name}, Here is the your reset password link: '+url
            
            message = f'Hi you have got a quick contact us'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [user.email, ]
            html_message = loader.render_to_string(
                'reset_email.html',
                {
                    'name': user.first_name +' '+ user.last_name,
                    'verification_link': url,
                }
            )

            send_mail( subject, message, email_from, recipient_list,html_message=html_message )

            return data
        else:
            raise serializers.ValidationError('Email Not found!')
      

class UniversityResetPasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(style = { 'input_type': 'password'}, write_only = True, required = True , max_length = 20, min_length=6)
    confirm_password = serializers.CharField(style = { 'input_type': 'password'}, write_only = True, required = True, max_length = 20, min_length=6)
    uid = serializers.CharField(max_length = 255,required=True)
    token = serializers.CharField(max_length = 255,required=True)
    class Meta:
        model = User
        fields = ['password','confirm_password',"uid","token"]

    
    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        if password != confirm_password:
            raise serializers.ValidationError("Password and confirm password doesn't match")

        uid = data.get('uid')
        token = data.get('token')

        id = smart_str(urlsafe_base64_decode(uid))
        user = User.objects.filter(id=id).first()
        if user is None:
            raise serializers.ValidationError('Invalid Token')
        
        if not PasswordResetTokenGenerator().check_token(user, token):
            raise serializers.ValidationError('Invalid Token')
        user.set_password(password)
        user.save()

        PasswordChangeLog.objects.create(
            user=user
        )
        
        return data