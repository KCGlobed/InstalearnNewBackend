from rest_framework import serializers
from universities.models import *
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
from django.utils import timezone
from dateutil.relativedelta import relativedelta


class UniversityRequestsSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    class Meta:
        model = University
        fields = "__all__"


class AdminUserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','first_name','last_name', 'email','phone1',"is_active","date_joined","last_login","image"]


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

class StudentListingSerializer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    courses = serializers.SerializerMethodField('get_courses')
    courses_progress = serializers.SerializerMethodField('get_courses_progress')
    
    def get_courses_progress(self, obj):
        users_courses = UserCourses.objects.filter(user=obj, paid=True).values_list("course")
        total_video_duration = Course.objects.filter(id__in = users_courses).aggregate(Sum('total_video_duration')).get('total_video_duration__sum')  or 0

        total_duration_video_watched = UserLectureProgress.objects.filter(course_id__in = users_courses, user_id = obj.id).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        video_duration_progress = 0
        if total_duration_video_watched > total_video_duration:
            video_duration_progress =  100
        else:
            if total_video_duration > 0:
                video_duration_progress =  math.ceil(total_duration_video_watched * 100 / total_video_duration)

        return video_duration_progress
    
    def get_courses(self, obj):
        users_courses = UserCourses.objects.filter(user=obj, paid=True).select_related("course").order_by("-id")
        return UserCoursesListSerializer(users_courses, many=True, context={"user": obj.id}).data
    
    class Meta:
        model = User
        fields = ['id','first_name','last_name', 'email','phone1',"is_active","date_joined","last_login","image","courses","courses_progress"]


class PlanInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlans
        fields = ["id",'plan_name']
        
class OrderListingSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    plan_info = serializers.SerializerMethodField('get_plan_info')
    
    def get_plan_info(self, obj):
        return PlanInfoSerializer(obj.plan).data
    
    class Meta:
        model = Order
        fields = ["id","first_name","last_name","email","phone","total_amount","gst_amount","amount","start_date","next_due","end_date","no_of_licence","subscription_type","subscription_status","created_at","plan_info"]


class UniversityRequestsDetailSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    admin_user = serializers.SerializerMethodField('get_admin_user')
    student_lists = serializers.SerializerMethodField('get_student_lists')
    active_subscription = serializers.SerializerMethodField('get_active_subscription')
            
    def get_active_subscription(self, obj):
        users_list = Order.objects.filter(university = obj.id)
        serializer = OrderListingSerializer(users_list, many=True)
        return serializer.data
        
    def get_student_lists(self, obj):
        users_list = User.objects.filter(university = obj.id, role = User.Student)
        serializer = StudentListingSerializer(users_list, many=True)
        return serializer.data
        
    def get_admin_user(self, obj):
        university_admin = User.objects.filter(university = obj, role = User.UniversityAdmin).first()
        return AdminUserInfoSerializer(university_admin).data
    
    class Meta:
        model = University
        fields = "__all__"

class ChangeUniversitystatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = University
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category


class ApproveRejectUniversitystatusSerializer(serializers.ModelSerializer) :
    approved_status = serializers.IntegerField(required=True)
    class Meta:
        model = University
        fields = ['approved_status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.approved_status = validate_data.get('approved_status', category.approved_status)
        category.approved_by = self.context.get('user')
        category.save()

        if category.approved_status == UniversityStatus.Approved:
            university_admin = User.objects.filter(university = category, role = User.UniversityAdmin)
            if university_admin is not None:
                for user in university_admin:
                    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                    user.set_password(password)
                    user.is_active = True
                    user.save()

                    subject = 'Approved: Your University Account Access & Admin Credentials!'

                    url = settings.BASE_URL+"/login"
                    message = f''
                    email_from = settings.EMAIL_HOST_USER
                    recipient_list = [user.email, ]
                    html_message = loader.render_to_string(
                        'approve_university_email.html',
                        {
                            'name': user.first_name +' '+ user.last_name,
                            'verification_link': url,
                            "email": user.email,
                            "password": password,
                        }
                    )
                    user = user
                    send_mail( subject, message, email_from, recipient_list,html_message=html_message )

        return category



class AssignSubscriptiontoUniversitySerializer(serializers.ModelSerializer) :
    plan_id = serializers.IntegerField(required=True)
    no_of_licence = serializers.IntegerField(required=True)

    class Meta:
        model = Order
        fields = ["plan_id","no_of_licence"]
        
    def validate(self, data):
        plan_id = data.get('plan_id')
        plan_count = SubscriptionPlans.objects.filter(id=plan_id).count()
        if plan_count == 0:
            raise serializers.ValidationError("Invalid Subscription Plan ID")
        
        university_admin = User.objects.filter(university = self.context.get('university'), role = User.UniversityAdmin).first()

        course = Order.objects.filter(user = university_admin, isPaid = True, payment_type = PaymentType.Subscription, subscription_status=OrderStatus.Active).order_by('-created_at').first()

        if course is not None:
            raise serializers.ValidationError('You have a already active subscription')
        
        return data

    def create(self , validate_data):

        subscription_plan = SubscriptionPlans.objects.filter(id=validate_data.get('plan_id')).first()
        user = User.objects.filter(university = self.context.get('university'), role = User.UniversityAdmin).first()
        current_year = datetime.now().year
        count = Order.objects.all().count()
        order_id = f"{current_year}-{str(count + 1).zfill(4)}"  


        tax = subscription_plan.gst_amount
        total_amount = subscription_plan.amount_without_gst
        order_total_amount = subscription_plan.amount

        book_order = Order(
            orderID = order_id,
            user = user,
            university = self.context.get('university'),
            first_name = user.first_name,
            last_name = user.last_name,
            email = user.email,
            phone = user.phone1,
            payment_type = PaymentType.Subscription,
            plan = subscription_plan,
            subscription_id = subscription_plan.id,
            subscription_type = subscription_plan.plan_type,
            no_of_licence = validate_data.get('no_of_licence'),
            amount = total_amount,
            gst_amount = tax,
            total_amount = order_total_amount,
            isPaid = True,
            subscription_status = OrderStatus.Active,
            payment_method = PaymentMethod.Offline
        )
        book_order.save()

        
        start_date = timezone.now()  # Or timezone.now().date() if you only use DateField
    
        # 2. Calculate end_date based on plan_type
        if subscription_plan.plan_type == PlanType.Monthly:
            end_date = start_date + relativedelta(months=1)
            
        elif subscription_plan.plan_type == PlanType.Half_Yearly:
            end_date = start_date + relativedelta(months=6)
            
        elif subscription_plan.plan_type == PlanType.Yearly:
            end_date = start_date + relativedelta(years=1)
            
        else:
            end_date = start_date

        book_order.next_due = end_date
        book_order.end_date = end_date
        book_order.save()
        return user



class ImportStudentsSerializer(serializers.ModelSerializer) :
    excel_file = serializers.FileField(required=True, validators=[FileExtensionValidator( ['xlsx','xls'])])
    university_id = serializers.IntegerField(required=True)
    
    class Meta:
        model = User
        fields = ['excel_file',"university_id"]

    def validate_university_id(self, value):
        if not University.objects.filter(id=value).exists():
            raise serializers.ValidationError("University with the provided ID does not exist.")
        return value
    
    def validate(self, data):
        return data