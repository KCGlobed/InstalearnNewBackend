from rest_framework import serializers
from users.models import *
from instructor.models import *
from courses.models import *
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
import random
import string
import re
from mini_lms.utils import *
from subscription.models import *
from django.core.validators import FileExtensionValidator


class StudentListingSerializer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = User
        fields = ['id','first_name','last_name', 'email','phone1',"is_active","date_joined","reference_id","category","student_type"]


class UserListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','email','first_name','last_name',"address","city","state","country","pincode","dob""is_active"]



class OrderListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id","total_amount","start_date","next_due","end_date","subscription_status","created_at"]




class UserDevicesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevices
        fields = ["id", "device_id","device_type","created_at"]



class UserListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','first_name','last_name', 'email','address',"city","state","country","pincode","dob","is_active","role","created_at",]



class CreateUserSerializer(serializers.ModelSerializer) :
    first_name = serializers.CharField(max_length = 255, required=True)
    last_name = serializers.CharField(max_length = 255, required=True)
    email = serializers.EmailField(max_length = 255, required=True)
    address = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    city = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    state = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    country = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    dob = serializers.DateField(required=False)
    pincode = serializers.CharField(max_length = 8, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['email','first_name','last_name',"address","city","state","country","pincode","dob"]
        

    def validate(self, data):
        user_count = User.objects.filter(email = data.get('email').lower()).count()
        if user_count > 0:
            raise serializers.ValidationError('Email address is already registered with Us')
        
        return data


    def create(self, validate_data):
        password = generate_random_password(8)

        info = { "first_name": validate_data.get('first_name'),"last_name": validate_data.get('last_name'), 'email': validate_data.get('email').lower(), 'password': password}

        user = User.objects.create_user(**info)
        assign_role(user, get_url_role_class(self.context.get('user_type')))

        user.role = get_url_role(self.context.get('user_type'))
        user.email_verified = 1
        user.is_active = True
        user.address = validate_data.get('address')
        user.country = validate_data.get('country')
        user.state = validate_data.get('state')
        user.city = validate_data.get('city')
        user.pincode = validate_data.get('pincode')
        user.dob = validate_data.get('dob')
        user.save()

        subject = 'Welcome to KCGLOBED!'

        message = f''
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user.email, ]
        html_message = loader.render_to_string(
            'user_login_detail_email.html',
            {
                'name': user.first_name +' '+ user.last_name,
                'verification_link': settings.BASE_URL,
                "email": user.email,
                "password": password,

            }
        )

        send_mail( subject, message, email_from, recipient_list,html_message=html_message )

        return user
    


class UpdateUserSerializer(serializers.ModelSerializer) :
    first_name = serializers.CharField(max_length = 255, required=True)
    last_name = serializers.CharField(max_length = 255, required=True)
    address = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    city = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    state = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    country = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    pincode = serializers.CharField(max_length = 8, required=False, allow_blank=True)
    dob = serializers.DateField(required=True)

    class Meta:
        model = User
        fields = ['first_name','last_name',"address","city","state","country","pincode","dob"]
        

    def validate(self, data):
        
        return data

    def update(self, info, validate_data):

        info.first_name = validate_data.get('first_name', info.first_name)
        info.last_name = validate_data.get('last_name', info.last_name)
        info.address = validate_data.get('address', info.address)
        info.city = validate_data.get('city', info.city)
        info.state = validate_data.get('state', info.state)
        info.country = validate_data.get('country', info.country)
        info.pincode = validate_data.get('pincode', info.pincode)
        info.dob = validate_data.get('dob', info.dob)
        info.save()
        return info
    


class ChangeUserStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = User
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.is_active = validate_data.get('status', category.is_active)
        category.save()

        return category
    


class StaffProfileSerializer(serializers.ModelSerializer):
    user_devices = serializers.SerializerMethodField('get_user_devices')
    
    def get_user_devices(self, obj):
        users_courses = UserDevices.objects.only("id","device_id","device_type","created_at").filter(user=obj).order_by("-id")
        return UserDevicesListSerializer(users_courses, many=True, context={"user": obj.id}).data
    
    class Meta:
        model = User
        fields = ['id','first_name','last_name', 'email','phone1','phone2','address','city','state','country','image','banner_image','pincode',"dob","user_devices","is_active"]



class UpdateInstructorPublicProfileSerializer(serializers.ModelSerializer) :
    title_1 = serializers.CharField(max_length = 255, required=True)
    title_2 = serializers.CharField(max_length = 255, required=True)
    title_3 = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    experience = serializers.CharField(max_length = 255, required=True)
    linkedin_url = serializers.URLField(max_length = 255, required=False, allow_blank=True)
    image = serializers.ImageField(required=True, validators=[FileExtensionValidator( ['png','jpg','jpeg'])])
    company_image_1 = serializers.ImageField(required=True, allow_null=True, validators=[FileExtensionValidator( ['png','jpg','jpeg'])])
    company_image_2 = serializers.ImageField(required=True, allow_null=True, validators=[FileExtensionValidator( ['png','jpg','jpeg'])])

    class Meta:
        model = User
        fields = ['title_1','title_2',"title_3","linkedin_url","image","company_image_1","company_image_2","experience"]
        

    def validate(self, data):
        return data

    def update(self, info, validate_data):
        instructor = InstructorProfile.objects.filter(user_id = info.id).first()
        if instructor is None:
            instructor = InstructorProfile()
            instructor.user = info

        instructor.text_1 = validate_data.get('title_1', instructor.text_1)
        instructor.text_2 = validate_data.get('title_2', instructor.text_2)
        instructor.text_3 = validate_data.get('title_3', instructor.text_3)
        instructor.experience = validate_data.get('experience', instructor.experience)
        instructor.linkedin_url = validate_data.get('linkedin_url', instructor.linkedin_url)
        instructor.image = validate_data.get('image', instructor.image)
        instructor.company_image_1 = validate_data.get('company_image_1', instructor.company_image_1)
        instructor.company_image_2 = validate_data.get('company_image_2', instructor.company_image_2)
        instructor.save()

        return info
    



class MyCourseDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id",'name']



class UserCoursesListSerializer(serializers.ModelSerializer):
    course_detail = MyCourseDetailSerializer(source="course", read_only=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pass the context to the nested serializer
        if 'context' in kwargs:
            self.fields['course_detail'].context.update(kwargs['context'])

    class Meta:
        model = UserCourses
        fields = ["id", "course_detail"]


class UserDevicesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevices
        fields = ["id", "device_id","device_type","created_at"]


class StudentProfileSerializer(serializers.ModelSerializer):
    active_orders = serializers.SerializerMethodField('get_active_orders')
    courses = serializers.SerializerMethodField('get_courses')
    user_devices = serializers.SerializerMethodField('get_user_devices')
    
    def get_user_devices(self, obj):
        users_courses = UserDevices.objects.only("id","device_id","device_type","created_at").filter(user=obj).order_by("-id")
        return UserDevicesListSerializer(users_courses, many=True, context={"user": obj.id}).data
    
    
    def get_courses(self, obj):
        users_courses = UserCourses.objects.filter(user=obj, paid=True).select_related("course").order_by("-id")
        return UserCoursesListSerializer(users_courses, many=True, context={"user": obj.id}).data
    
    
    def get_active_orders(self, obj):
        order_list = Order.objects.filter(user = obj, subscription_status = OrderStatus.Active).order_by("-id").first()
        if order_list is not None:
            return OrderListingSerializer(order_list).data
        return {}
    

    class Meta:
        model = User
        fields = ['id','first_name','last_name', 'email','phone1','phone2','address','city','state','country','image','banner_image','pincode',"dob","active_orders","courses","user_devices"]


class CreateStudentSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length = 255, required=True)
    last_name = serializers.CharField(max_length = 255, required=True)
    email = serializers.EmailField(max_length = 255, required=True)
    phone = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    address = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    city = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    state = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    country = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    dob = serializers.DateField(required=False)
    pincode = serializers.CharField(max_length = 8, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['email','first_name','last_name',"address","city","state","country","pincode","dob","phone"]
        

    def validate(self, data):
        user_count = User.objects.filter(email = data.get('email').lower()).count()
        if user_count > 0:
            raise serializers.ValidationError('Email address is already registered with Us')
        
        return data


    def create(self, validate_data):
        password = generate_random_password(8)
        info = { "first_name": validate_data.get('first_name'),"last_name": validate_data.get('last_name'), 'email': validate_data.get('email').lower(), 'password': password}
        user = User.objects.create_user(**info)
        assign_role(user, "Student")

        user.role = User.Student
        user.email_verified = 1
        user.is_active = True
        user.phone1 = validate_data.get('phone')
        user.address = validate_data.get('address')
        user.country = validate_data.get('country')
        user.state = validate_data.get('state')
        user.city = validate_data.get('city')
        user.pincode = validate_data.get('pincode')
        user.dob = validate_data.get('dob')
        user.save()

        subject = 'Welcome to KCGLOBED!'

        message = f''
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user.email, ]
        html_message = loader.render_to_string(
            'user_login_detail_email.html',
            {
                'name': user.first_name +' '+ user.last_name,
                'verification_link': settings.BASE_URL,
                "email": user.email,
                "password": password,               

            }
        )

        send_mail( subject, message, email_from, recipient_list,html_message=html_message )

        return user
    


class UpdateStudentSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length = 255, required=True)
    last_name = serializers.CharField(max_length = 255, required=True)
    phone = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    address = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    city = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    state = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    country = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    pincode = serializers.CharField(max_length = 8, required=False, allow_blank=True)
    dob = serializers.DateField(required=True)

    class Meta:
        model = User
        fields = ['first_name','last_name',"address","city","state","country","pincode","dob","phone"]
        

    def validate(self, data):
        
        return data

    def update(self, info, validate_data):

        info.first_name = validate_data.get('first_name', info.first_name)
        info.last_name = validate_data.get('last_name', info.last_name)
        info.phone1 = validate_data.get('phone', info.phone1)
        info.address = validate_data.get('address', info.address)
        info.city = validate_data.get('city', info.city)
        info.state = validate_data.get('state', info.state)
        info.country = validate_data.get('country', info.country)
        info.pincode = validate_data.get('pincode', info.pincode)
        info.dob = validate_data.get('dob', info.dob)
        info.save()
        return info


class ChangeStudentStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = User
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.is_active = validate_data.get('status', category.is_active)
        category.save()

        return category    



class AdminUpdateStudentPasswordSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=False)
    password = serializers.CharField(style = { 'input_type': 'password'}, write_only = True, min_length=6)
    confirm_password = serializers.CharField(style = { 'input_type': 'password'}, write_only = True,min_length=6)
    class Meta:
        model = User
        fields = ['password','confirm_password','user_id']

    def validate_password(self, value):
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        return value

    
    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        if password != confirm_password:
            raise serializers.ValidationError("Password and confirm password doesn't match")
        
        return data
    
    
    def create(self , validate_data):
        user = User.objects.get(id = validate_data.get('user_id'))
        user.set_password(validate_data.get('password'))
        user.save()

        return user