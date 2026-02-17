from rest_framework import serializers
from subscription.models import *
from courses.models import *
from users.models import *
from django.conf import settings
from django.core.mail import send_mail
from mini_lms.roles import Student
from mini_lms.utils import *
from rolepermissions.roles import assign_role
import random
import math
from django.template import loader
from datetime import datetime, date, timedelta
import random, string
import razorpay
from django.db import transaction

class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = ["id","public_key","secret_key","no_days_trail","try_for_free","allow_device_restriction","allowed_desktop","allowed_tablet","allowed_phone","auto_logout_restriction"]



class UpdateSettingSerializer(serializers.ModelSerializer):
    public_key = serializers.CharField(max_length = 255, required=False)
    secret_key = serializers.CharField(max_length = 255, required=False)
    no_days_trail = serializers.IntegerField(required=False, allow_null=True)
    try_for_free = serializers.IntegerField(required=False, allow_null=True)
    allow_device_restriction = serializers.BooleanField(required=False, allow_null=True)
    auto_logout_restriction = serializers.BooleanField(required=False, allow_null=True)
    allowed_desktop = serializers.IntegerField(required=False, allow_null=True)
    allowed_tablet = serializers.IntegerField(required=False, allow_null=True)
    allowed_phone = serializers.IntegerField(required=False, allow_null=True)
    
    
    class Meta:
        model = Settings
        fields =  ["public_key","secret_key","no_days_trail","try_for_free","allow_device_restriction","allowed_desktop","allowed_tablet","allowed_phone","auto_logout_restriction"]
        
    def validate(self, data):
        return data


    def create(self , validate_data):
        setting = Settings.objects.all().first()
        if setting is None:
            setting = Settings()
        setting.public_key = validate_data.get('public_key', setting.public_key)
        setting.secret_key = validate_data.get('secret_key', setting.secret_key)
        setting.no_days_trail = validate_data.get('no_days_trail', setting.no_days_trail)
        setting.try_for_free = validate_data.get('try_for_free', setting.try_for_free)
        setting.allow_device_restriction = validate_data.get('allow_device_restriction', setting.allow_device_restriction)
        setting.auto_logout_restriction = validate_data.get('auto_logout_restriction', setting.auto_logout_restriction)
        setting.allowed_tablet = validate_data.get('allowed_tablet', setting.allowed_tablet)
        setting.allowed_phone = validate_data.get('allowed_phone', setting.try_for_free)
        setting.allowed_desktop = validate_data.get('allowed_desktop', setting.allowed_desktop)
        setting.save()

        return setting
    


class SubscriptionPlansSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlans
        fields = ["id","plan_name","amount","currency","plan_type","status","created_at"]


class SubscriptionPlanDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlans
        fields = ["id","plan_id","plan_name","plan_description","banner_text","original_price","monthly_amount","amount","currency","plan_type","status","feature","created_at"]


class CreateSubscriptionPlanSerializer(serializers.ModelSerializer) :
    plan_name = serializers.CharField(max_length = 255, required=True)
    plan_description = serializers.CharField(required=True)
    banner_text = serializers.CharField(max_length = 255, required=False)
    amount = serializers.IntegerField(required=True)
    monthly_amount = serializers.IntegerField(required=False, allow_null=True)
    original_price = serializers.IntegerField(required=False, allow_null=True)
    currency = serializers.CharField(max_length = 10, required=True)
    feature = serializers.JSONField(required=True)
    plan_type = serializers.IntegerField(required=True)
    

    class Meta:
        model = SubscriptionPlans
        fields =  ["plan_name","plan_description","banner_text","original_price","monthly_amount","amount","currency","plan_type","feature"]
        
    def validate(self, data):
        return data

    def create(self , validate_data):
        razorpay_key = Settings.objects.all().first()
        if razorpay_key is None:
            raise serializers.ValidationError("Razorpay Key is not added in setting!")
        
        plan_detail = plan_interval(validate_data.get('plan_type'))
        
        try:
            client = razorpay.Client(auth=(razorpay_key.public_key, razorpay_key.secret_key))
           
            plan_info = client.plan.create({
            'period': plan_detail['period'],
            'interval': plan_detail['interval'],
            'item': {
                'name': validate_data.get('plan_name'),
                'amount': validate_data.get('amount') * 100,
                'currency': validate_data.get('currency'),
                'description': validate_data.get('plan_description'),
                }
            })
        except Exception as error:
            raise serializers.ValidationError("Unale to create subscription plan : " + str(error))

        sub_plan = SubscriptionPlans(
                plan_id = plan_info['id'],
                plan_name = validate_data.get('plan_name'),
                plan_description = validate_data.get('plan_description'),
                banner_text = validate_data.get('banner_text'),
                original_price = validate_data.get('original_price'),
                monthly_amount = validate_data.get('monthly_amount'),
                amount = validate_data.get('amount'),
                currency = validate_data.get('currency'),
                plan_type = validate_data.get('plan_type'),
                feature = validate_data.get('feature')
            )
        sub_plan.save()

        return sub_plan
    

class EditSubscriptionPlanSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(max_length = 255, required=True)
    plan_description = serializers.CharField(required=True)
    banner_text = serializers.CharField(max_length = 255, required=False)
    monthly_amount = serializers.IntegerField(required=False, allow_null=True)
    original_price = serializers.IntegerField(required=False, allow_null=True)
    feature = serializers.JSONField(required=False)
    
    class Meta:
        model = SubscriptionPlans
        fields =  ["plan_name","plan_description","banner_text","original_price","monthly_amount","amount","feature"]
        
    def validate(self, data):
        return data


    def update(self , plan_info, validate_data):
        
        plan_info.plan_name = validate_data.get('plan_name', plan_info.plan_name)
        plan_info.plan_description = validate_data.get('plan_description', plan_info.plan_description)
        plan_info.banner_text = validate_data.get('banner_text', plan_info.banner_text)
        plan_info.original_price = validate_data.get('original_price', plan_info.original_price)
        plan_info.monthly_amount = validate_data.get('monthly_amount', plan_info.monthly_amount)
        plan_info.amount = validate_data.get('amount', plan_info.amount)
        plan_info.feature = validate_data.get('feature', plan_info.feature)
        plan_info.save()

        return plan_info


class ChangeSubscriptionPlanStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = SubscriptionPlans
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , plan_info, validate_data):
        plan_info.status = validate_data.get('status', plan_info.status)
        plan_info.save()

        return plan_info
    



class CourseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id",'name']


class UserCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id',"reference_id","category","student_type"]


class OrderDetailAdminSerializer(serializers.ModelSerializer):
    plan = serializers.SerializerMethodField('get_plan')
    user_detail = UserCategorySerializer(source="user", read_only=True)
    ordered_courses = serializers.SerializerMethodField('get_ordered_courses')
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    def get_ordered_courses(self, obj):
        category = Course.objects.filter(usercourses__user_id=obj.user.id).distinct()
        return CourseListSerializer(category, many=True).data
    

    def get_plan(self, obj):
        if obj.plan is not None:
            return {
                "id":obj.plan.id,
                "plan_name":obj.plan.plan_name,
                "currency":obj.plan.currency,
                "plan_type":obj.plan.plan_type
            }

        return {
            "id":None,
            "plan_name":"Trail",
            "currency":1,
            "plan_type":"Trail"
        }
    
    class Meta:
        model = Order
        fields = ["id","first_name","last_name","email","phone","billing_address","state","city","country","plan","total_amount","start_date","next_due","end_date","subscription_type","subscription_status","created_at","ordered_courses","user_detail","trail_mode"]


class RegisterForTrailSerializer(serializers.ModelSerializer) :
    first_name = serializers.CharField(max_length = 255, required=True)
    last_name = serializers.CharField(max_length = 255, required=True)
    email = serializers.EmailField(max_length = 255, required=False)
    phone = serializers.CharField(max_length = 13, min_length=10, required=True)
    course_id = serializers.ListField(required=True, child=serializers.IntegerField(required=True))
    billing_address = serializers.CharField(required=True)
    state = serializers.CharField(max_length = 255, required=True)
    city = serializers.CharField(max_length = 255, required=True)
    country = serializers.CharField(max_length = 255, required=True)

    class Meta:
        model = TrailUser
        fields =  ["first_name","last_name","email","phone","course_id","billing_address","state","city","country"]
    
    def validate_course_id(self, value):
        return validate_course_id_list(value)
    
    def validate(self, data):
        
        user = User.objects.filter(email = data.get('email').lower()).count()
        if user > 0:
            raise serializers.ValidationError("Email Already Registered With Us")
        
        trail_user = TrailUser.objects.filter(email = data.get('email').lower()).count()
        if trail_user > 0:
            raise serializers.ValidationError("Email Already Used for Trail Period")
        

        return data


    def create(self , validate_data):
        
        with transaction.atomic():
            trail_user = TrailUser(
                first_name = validate_data.get('first_name'),
                last_name = validate_data.get('last_name'),
                email = validate_data.get('email').lower(),
                phone = validate_data.get('phone'),
            )
            trail_user.save()
            
            password = generate_random_password(8)

            info = { "first_name": validate_data.get('first_name'),"last_name": validate_data.get('last_name'), 'email': validate_data.get('email'), 'phone': validate_data.get('phone'), 'password': password}

            user = User.objects.create_user(**info)
            assign_role(user, "Student")

            user.role = User.Student
            user.email_verified = 1
            user.is_active = True
            user.save()
            
            trail_user.user =  user
            trail_user.save()

            trail_setting = Settings.objects.all().first()


            url = settings.BASE_URL+"/login"
            subject = 'Thank you for registering!'
            message = f''
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [user.email, ]
            html_message = loader.render_to_string(
                'trail_user_login_email.html',
                {
                    'name': user.first_name +' '+ user.last_name,
                    'verification_link': url,
                    "email": user.email,
                    "password": password,
                    "trail_days":trail_setting.no_days_trail,

                }
            )

            send_mail( subject, message, email_from, recipient_list,html_message=html_message )

            
            
            Begindatestring = date.today()
            Enddate = Begindatestring + timedelta(days=trail_setting.no_days_trail)

            order_info = Order(
                user = user,
                first_name = validate_data.get('first_name'),
                last_name = validate_data.get('last_name'),
                email = validate_data.get('email'),
                phone = validate_data.get('phone'),
                billing_address = validate_data.get('billing_address'),
                state = validate_data.get('state'),
                city = validate_data.get('city'),
                country = validate_data.get('country'),
                amount = 0,
                gst_amount = 0,
                total_amount = 0,
                payment_method = PaymentMethod.Online,
                trail_mode = True,
                start_date = Begindatestring,
                next_due = Enddate,
                end_date = Enddate,
                subscription_status = OrderStatus.Active
            )
            order_info.save()

            course_data = validate_data.get('course_id', []) 
            
            if len(course_data) > 0:
                for index , course_id in enumerate(course_data):
                    course = Course.objects.get(id = course_id)
                    chap = TrailUserCourses(
                            course=course,
                            trail_user = trail_user
                        )
                    chap.save()

                    user_course = UserCourses(
                        order = order_info,
                        user = user,
                        course = course,
                        trail = True
                    )
                    user_course.save()


        return trail_user