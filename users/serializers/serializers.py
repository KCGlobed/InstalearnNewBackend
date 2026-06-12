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



class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length = 255,required=True)
    password = serializers.CharField(max_length = 255,required=True)
    role = serializers.CharField(max_length = 255,required=True)
    device_type = serializers.CharField(max_length = 255, required=True)
    device_id = serializers.CharField(max_length = 255, required=True)

    class Meta:
        model = User
        fields = ['email', 'password',"role",'device_type','device_id']

    def validate(self, data):
        user = User.objects.filter(email =data.get('email').lower(), email_verified = 1).first()
        if user is None:
            raise serializers.ValidationError("User Not found with this email!")
        
        if user.is_active is False:
            raise serializers.ValidationError("User is not active!")
        
        if user.email_verified == 0:
            raise serializers.ValidationError("User email is not verified!")
        
        try:
            if data.get('role') == "Student":
                assign_role(user, globals()[data.get('role')])
                
            if not has_role(user, globals()[data.get('role')]):
                if not has_role(user, data.get('role')):
                    raise serializers.ValidationError("Invalid User!")
        except KeyError:
            raise serializers.ValidationError("Invalid Role Type!")
        
        if user:
            if not user.check_password(data.get('password')):
                raise serializers.ValidationError("Invalid Password!")
        
        return data


class UserSocialLoginSerializer(serializers.ModelSerializer) :
    name = serializers.CharField(max_length = 255, required=True, source='first_name')
    email = serializers.CharField(max_length = 255, required=True)
    social_id = serializers.CharField(max_length = 255, required=True)
    social_type = serializers.CharField(max_length = 255, required=True)
    token = serializers.CharField(write_only=True)
    role = serializers.CharField(max_length = 255,required=True)
    device_type = serializers.CharField(max_length = 255, write_only=True)
    device_id = serializers.CharField(max_length = 255, write_only=True)

    class Meta:
        model = User
        fields = ['email','name','social_id','social_type',"role","token","device_type","device_id"]

    def validate(self, data):
        token = data.get("token")
        # if data.get("social_type") == "Google":
        #     google_login_token_check(token)
        # else:
        #     facebook_login_token_check(token)

        return data
    
    def create(self , validate_data):
        usercount = User.objects.filter(email = validate_data.get('email').lower()).count()
        if usercount == 0:
            data = {"email":validate_data.get('email').lower(), "name":validate_data.get('first_name'),"social_id":validate_data.get('social_id'),"social_type":validate_data.get('social_type')}
            user = User.objects.create_social_user(**data)
            assign_role(user, globals()[validate_data.get('role')])
            user.email_verified = 1
            user.save()

        else:
            user  = User.objects.filter(email = validate_data.get('email').lower()).first()
            user.email_verified = 1
            user.social_id = validate_data.get('social_id')
            user.social_type = validate_data.get('social_type')
            user.save()

            try:
                if not has_role(user, globals()[validate_data.get('role')]):
                    raise serializers.ValidationError("Invalid User!")
            except KeyError:
                raise serializers.ValidationError("Invalid Role Type!")

        return user 




class UserRegistrationSerializer(serializers.ModelSerializer) :
    confirm_password = serializers.CharField(max_length = 20,min_length = 6,style = { 'input_type': 'password'}, write_only = True)
    first_name = serializers.CharField(max_length = 100, required=True)
    last_name = serializers.CharField(max_length = 100, required=True)
    email = serializers.EmailField(max_length = 100, required=True)
    phone = serializers.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ['email','first_name','last_name','password','confirm_password','phone']
        extra_kwargs = {
            'password' : { 'write_only': True}
        }

    def validate_phone(self, value):
        try:
            parsed_number = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise serializers.ValidationError("Invalid phone number.")
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError("Invalid phone number format.")
        return value
    
    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        if password != confirm_password:
            raise serializers.ValidationError("Password and confirm password doesn't match")

        user = User.objects.filter(email =data.get('email').lower(), email_verified = 1).count()
        if user > 0:
            raise serializers.ValidationError("User already registered with this email")
        
        return data


    def create(self , validate_data):
        user = User.objects.filter(email =validate_data.get('email').lower(), email_verified = 0).first()
        if user is None:
            user = User.objects.create_user(**validate_data)
            assign_role(user, "Student")
            user.phone1 = validate_data.get('phone')
            user.save()

        digits = [i for i in range(0, 10)]
        random_str = ""
        for i in range(6):
            index = math.floor(random.random() * 10)
            if digits[index] == 0:
                random_str += str(5)
            else:
                random_str += str(digits[index])
            
        usercourse = UserOTP(
                otp = random_str,
                user = user,
            )
        usercourse.save()
        
        subject = 'Account Verification'

        message = f'Hi you have got a verification code'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user.email, ]
        html_message = loader.render_to_string(
            'verify_email_otp.html',
            {
                'name': user.first_name +' '+ user.last_name,
                'verification_link': random_str,
            }
        )

        send_mail( subject, message, email_from, recipient_list,html_message=html_message )

        return user 
    

class UserVerifyOTPSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length = 255, required=True)
    otp = serializers.CharField(required=True)
    class Meta:
        model = User
        fields = ['email','otp']

    
    def validate(self, data):
        
        user = User.objects.filter(email =data.get('email').lower()).count()
        if user == 0:
            raise serializers.ValidationError("User Not found with this email")
        
        user_info = User.objects.get(email = data.get('email').lower())
        user_otp = UserOTP.objects.filter(user = user_info).first()

        if data.get('otp') != user_otp.otp:
            raise serializers.ValidationError("Invalid OTP")

        time_difference = datetime.now().astimezone() - user_otp.created_at
        minutes = time_difference.seconds / 60
        if minutes > 15:
            raise serializers.ValidationError("OTP Expired")
        

        user_info.email_verified = 1
        user_info.save()
        
        UserOTP.objects.filter(user = user_info).delete()

        return data
    


class UserVerificationOTPSerializer(serializers.ModelSerializer) :
    email = serializers.EmailField(max_length = 255, required=True)
    class Meta:
        model = User
        fields = ['email']

    def validate(self, data):
        user = User.objects.filter(email =data.get('email').lower()).count()
        if user == 0:
            raise serializers.ValidationError("User Not found with this email")
        return data


    def create(self , validate_data):
        user = User.objects.get(email =validate_data.get('email').lower())
        
        digits = [i for i in range(0, 10)]
        random_str = ""
        for i in range(6):
            index = math.floor(random.random() * 10)
            if digits[index] == 0:
                random_str += str(5)
            else:
                random_str += str(digits[index])
        
        UserOTP.objects.filter(user = user).delete()
        usercourse = UserOTP(
                otp = random_str,
                user = user,
            )
        usercourse.save()
        
        
        subject = 'Account Verification'

        message = f'Hi you have got a verification code'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user.email, ]
        html_message = loader.render_to_string(
            'verify_email_otp.html',
            {
                'name': user.first_name +' '+ user.last_name,
                'verification_link': random_str,
            }
        )

        send_mail( subject, message, email_from, recipient_list,html_message=html_message )

        return user 
    

class UserForgotPasswordSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length = 255,required=True)
    class Meta:
        model = User
        fields = ['email']

    
    def validate(self, data):
        email = data.get('email')
        if User.objects.filter(email = email).exists():
            user = User.objects.get(email = email)
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            
            url = settings.BASE_URL+"/user/reset/?uid="+uid+'&token='+token

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
        

class AdminForgotPasswordSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length = 255,required=True)
    class Meta:
        model = User
        fields = ['email']

    
    def validate(self, data):
        email = data.get('email')
        if User.objects.filter(email = email).exists():
            user = User.objects.get(email = email)
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            
            url = settings.ADMIN_BASE_URL+"/user/reset/?uid="+uid+'&token='+token

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


class UserResetPasswordSerializer(serializers.ModelSerializer):
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
    


class RoleSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    def to_representation(self, instance):
        return {
            'name': instance.get_name()
        }


class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermissions
        fields = ['name','code',"status"]
    

class UpdateRolesPermissionSerializer(serializers.ModelSerializer) :
    role_name = serializers.CharField(max_length = 255, required=True)
    code = serializers.CharField(max_length = 255, required=True)
    status = serializers.BooleanField(required=True)

    class Meta:
        model = RolePermissions
        fields = ['role_name','code',"status"]


    def validate(self, data):
        role_name = data.get("role_name")
        role_class = get_role(role_name)
        if role_class is None:
            raise serializers.ValidationError(f"Role {role_name} not found.")
        
        system_permission =  RolePermissions.objects.filter(role = role_class.get_name(), code = data.get('code')).count()
        if system_permission == 0:
            raise serializers.ValidationError('Invalid Permission')
    
        return data


    def create(self, validate_data):

        system_permission =  RolePermissions.objects.filter(role = validate_data.get('role_name'), code = validate_data.get('code')).first()
        system_permission.status = validate_data.get('status')
        system_permission.save()

        role_id_found = 0
        for role_id, display_name in User.ROLE_CHOICES:
            if display_name.lower() == validate_data.get('role_name').lower():
                role_id_found = role_id
                break
        
        users = User.objects.filter(role = role_id_found)
        if users is not None:
            if validate_data.get('status') == True:
                for user in users:
                    grant_permission(user, system_permission.code)
            else:
                for user in users:
                    revoke_permission(user, system_permission.code)
        return True
    

class UpdateUserPermissionSerializer(serializers.ModelSerializer) :
    grant_permission = serializers.ListField(
                            child = serializers.CharField(max_length = 255, required=True))
    revoke_permission = serializers.ListField(
                            child = serializers.CharField(max_length = 255, required=True))
    
    class Meta:
        model = User
        fields = ['grant_permission','revoke_permission']
        

    def validate(self, data):
        return data

    def update(self, info, validate_data):
        for grant in validate_data.get('grant_permission'):
            grant_permission(info, grant)

        for revoke in validate_data.get('revoke_permission'):
            revoke_permission(info, revoke)


class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length = 255)
    class Meta:
        model = User
        fields = ['id','first_name','last_name', 'email','phone1','phone2','address','city','state','country','image','banner_image','pincode']


class UpdateUserProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length = 255, required=True)
    last_name = serializers.CharField(max_length = 255, required=True)
    phone_1 = serializers.CharField(required=True, allow_blank=True)
    phone_2 = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(max_length = 255, required=True)
    city = serializers.CharField(max_length = 255, required=True)
    state = serializers.CharField(max_length = 255, required=True)
    country = serializers.CharField(max_length = 255, required=True)
    pincode = serializers.CharField(max_length = 255, required=True)
    class Meta:
        model = User
        fields = ['first_name','last_name','phone_1','phone_2','address','city','state','country','pincode']

    
    def validate(self, data):
        user = self.context.get('user')
        user.first_name = data.get('first_name')
        user.last_name = data.get('last_name')
        user.phone1 = data.get('phone_1')
        user.phone2 = data.get('phone_2')
        user.address = data.get('address')
        user.city = data.get('city')
        user.state = data.get('state')
        user.country = data.get('country')
        user.pincode = data.get('pincode')
        user.save()
        return data


class UpdateUserProfileImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True)
    class Meta:
        model = User
        fields = ['image']

    
    def validate(self, data):
        user = self.context.get('user')
        user.image = data.get('image')
        user.save()
        return data
    

class RemoveUserProfileSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    class Meta:
        model = User
        fields = ['image']

    
    def validate(self, data):
        user = self.context.get('user')
        user.image = ''
        user.save()
        return data
    

class UpdateUserBannerImageSerializer(serializers.ModelSerializer):
    banner_image = serializers.ImageField(required=False)
    class Meta:
        model = User
        fields = ['banner_image']

    def validate(self, data):
        user = self.context.get('user')
        user.banner_image = data.get('banner_image')
        user.save()
        return data