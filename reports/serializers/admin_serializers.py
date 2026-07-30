from rest_framework import serializers
from users.models import *
from cms.models import *
from subscription.models import *
from mini_lms.utils import *
from itertools import chain
import pytz
from datetime import timedelta, datetime
from django.db.models import Q, Count
from django.core.validators import FileExtensionValidator
from django.core.mail import send_mail
from django.template import loader
from django.contrib.humanize.templatetags.humanize import naturaltime


class StaffUserListSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = User
        fields = ["id",'first_name',"last_name","email","role","is_active","created_at"]


class ChapterInfoSerializer(serializers.ModelSerializer) :
    class Meta:
        model = Chapters
        fields = ["id",'name',"no_of_videos","no_of_videos_duration"]


class CourseVideoReportSerializer(serializers.ModelSerializer) :
    chapter_info = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField('get_progress')
    video_watched = serializers.SerializerMethodField('get_video_watched')
    total_video_watched = serializers.SerializerMethodField('get_total_video_watched')

    def get_total_video_watched(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).count()
        return total_video_watched

    def get_video_watched(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        return total_video_watched
    
    def get_progress(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        if total_video_watched > parent.chapter.no_of_videos_duration:
            return 100
        else:
            if parent.chapter.no_of_videos_duration == 0:
                return 0
            return math.ceil(total_video_watched * 100 / parent.chapter.no_of_videos_duration)

    
    def get_chapter_info(self, parent):
        info = Chapters.objects.get(id = parent.chapter.id)
        return ChapterInfoSerializer(info).data

    class Meta:
        model = CourseChapters
        fields = ['id','chapter_info',"progress","video_watched","total_video_watched"]



class StudentSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    date_joined = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = User
        fields = ["id", "first_name","last_name","email","phone1","category","reference_id","student_type","date_joined","created_at","is_locked","unlocked_on"]


class UserDevicesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevices
        fields = ["id", "device_id","device_type","created_at"]

class StudentAccessLockReportSerializer(serializers.ModelSerializer):
    user_detail = StudentSerializer(source="user", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    user_devices = serializers.SerializerMethodField('get_user_devices')
    
    def get_user_devices(self, obj):
        users_devices = UserDevices.objects.filter(user=obj.user).order_by("-id")
        return UserDevicesListSerializer(users_devices, many=True).data
    
    class Meta:
        model = UserAccountLockDetail
        fields = ["id","user_detail","device_id","device_type","ip_address","user_devices","created_at"]


class ChangeUserAccounttatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = User
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):

        if validate_data.get('status'):
            category.failed_login_attempts = 0
            category.locked_until = None
            category.unlocked_on = timezone.now()
            
            user_devices = UserDevices.objects.filter(
                status = DeviceStatus.Active, 
                user_id = category.id
            )
            user_devices.update(status=DeviceStatus.Inactive)

        else:
            category.locked_until = timezone.now() + timedelta(days=365)
            category.unlocked_on = None
        category.save()

        return category
    



class CourseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id",'name']

class CouponListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ["id",'name']


class StudentRegistrationSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    class Meta:
        model = User
        fields = ["id",'first_name',"last_name","email","phone1","category","reference_id","student_type","is_active","created_at"]


class OrderDetailAdminSerializer(serializers.ModelSerializer):
    ordered_courses = serializers.SerializerMethodField('get_ordered_courses')
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    coupons = serializers.SerializerMethodField('get_coupons')
    
    def get_coupons(self, obj):
        if obj.coupon is not None:
            category = Coupon.objects.filter(id=obj.coupon.id).first()
            return CouponListSerializer(category).data
        return {}

    def get_ordered_courses(self, obj):
        category = Course.objects.filter(usercourses__user_id=obj.user.id).distinct()
        return CourseListSerializer(category, many=True).data

    
    class Meta:
        model = Order
        fields = ["id","first_name","last_name","email","phone","total_amount","start_date","next_due","end_date","subscription_type","subscription_status","created_at","ordered_courses","trail_mode","coupons","discount_amount"]


class JobApplicationsListSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d")
    
    class Meta:
        model = JobApplications
        fields = "__all__"


class ContactListSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")
    
    class Meta:
        model = ContactUs
        fields = ['id',"first_name","last_name",'email',"phone","message","created_at"]


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "name"]

class StudentPerformaceReportSerializer(serializers.ModelSerializer):
    user_detail = StudentSerializer(source="user", read_only=True)
    course_detail = CourseSerializer(source="course", read_only=True)
    performance_report = serializers.SerializerMethodField('get_performance_report')

    
    def get_performance_report(self, obj):
        user = obj.user
        
        no_of_videos_duration = obj.course.total_video_duration

        watch_video_duration = UserLectureProgress.objects.filter(course_id = obj.course.id,user = user, video__status=True).aggregate(Sum('total_duration'))['total_duration__sum'] or 0

        total_watch_video = UserLectureProgress.objects.filter(course_id = obj.course.id,user = user, video__status=True).count()

        study_completed = 0
        if watch_video_duration > 0 and no_of_videos_duration > 0:
            study_completed =  watch_video_duration * 100 / no_of_videos_duration

        return {
            "watch_time":watch_video_duration,
            "total_video_watched":total_watch_video,
        }


    class Meta:
        model = UserCourses
        fields = ["id",'user_detail',"course_detail","performance_report"]



class StudentNoteListingSerializer(serializers.Serializer):
    user = serializers.IntegerField(read_only=True)
    course = serializers.IntegerField(read_only=True)
    subject = serializers.IntegerField(read_only=True)
    user__first_name = serializers.CharField(read_only=True)
    user__last_name = serializers.CharField(read_only=True)
    user__email = serializers.EmailField(read_only=True)
    user__phone1 = serializers.EmailField(read_only=True)
    user__category = serializers.EmailField(read_only=True)
    user__reference_id = serializers.EmailField(read_only=True)
    user__student_type = serializers.EmailField(read_only=True)
    
    # --- Course/Subject Names ---
    course__name = serializers.CharField(read_only=True)

    # --- The Count ---
    notes_count = serializers.IntegerField()

    class Meta:
        model = Notes
        fields = "__all__"



class ChapterDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapters
        fields = ["id",'name']

class UserNoteDetailSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    chapter_lecture = serializers.SerializerMethodField()

    def get_chapter_lecture(self, parent):
        if parent.chapter_lecture is not None:
            serializer = ChapterDetailSerializer(parent.chapter_lecture.chapter)
            return serializer.data
        return {}

    class Meta:
        model = Notes
        fields = ['id',"chapter_lecture","duration","note_content","created_at"]


class StudentLoginActivitySerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    
    class Meta:
        model = UserLoginActivity
        fields = ["id","login_IP","device_id","country","device_type","created_at"]



class PlanInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlans
        fields = ["id",'plan_name']


class OrderInfoSerializer(serializers.ModelSerializer):
    plan_info = serializers.SerializerMethodField('get_plan_info')
    
    def get_plan_info(self, obj):
        return PlanInfoSerializer(obj.plan).data
        
    class Meta:
        model = Order
        fields = ["id",'start_date',"next_due","end_date","subscription_type","subscription_status","plan_info"]


class SubscriptionOrderDetailSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    plan_info = serializers.SerializerMethodField('get_plan_info')
    
    def get_plan_info(self, obj):
        return PlanInfoSerializer(obj.plan).data
    
    class Meta:
        model = Order
        fields = ["id","first_name","last_name","email","phone","total_amount","gst_amount","amount","start_date","next_due","end_date","subscription_type","subscription_status","created_at","plan_info"]


class CorproateUserListingSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    counters = serializers.SerializerMethodField('get_counters')
    active_suscription = serializers.SerializerMethodField('get_active_suscription')
    
    def get_active_suscription(self, obj):
        course_order = Order.objects.filter(
            user=obj.id, 
            isPaid=True, 
            payment_type=PaymentType.Subscription
        ).first()

        if course_order is not None:
            return OrderInfoSerializer(course_order).data
        return {}
    
    def get_counters(self, obj):
        course_order = Order.objects.filter(
            user=obj.id, 
            isPaid=True, 
            payment_type=PaymentType.Subscription
        ).first()

        no_of_licences = course_order.no_of_licence if course_order else 0 

        corporate_users = User.objects.filter(corporate=obj.id)
        users_id = list(corporate_users.values_list("id", flat=True))
        license_used = len(users_id)  # Avoids another .count() query

        course_count = UserCourses.objects.filter(user_id__in=users_id).count()

        data = {
            "no_of_licences": no_of_licences,
            "license_used": license_used,
            "remaning_licence": no_of_licences - license_used,
            "registered_users": license_used,
            "assigned_courses": course_count,
        }
        return data
    
    class Meta:
        model = User
        fields = ["id",'first_name',"last_name","email","is_active","address","city","state","country","pincode","phone1","image","created_at","counters","active_suscription"]




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


class CorproateUserDetailSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    counters = serializers.SerializerMethodField('get_counters')
    active_suscription = serializers.SerializerMethodField('get_active_suscription')
    student_lists = serializers.SerializerMethodField('get_student_lists')
    
    def get_student_lists(self, obj):
        users_list = User.objects.filter(corporate = obj.id)
        serializer = StudentListingSerializer(users_list, many=True)
        return serializer.data
    

    def get_active_suscription(self, obj):
        course_order = Order.objects.filter(
            user=obj.id, 
            isPaid=True, 
            payment_type=PaymentType.Subscription
        ).first()

        if course_order is not None:
            return OrderInfoSerializer(course_order).data
        return {}
    
    def get_counters(self, obj):
        course_order = Order.objects.filter(
            user=obj.id, 
            isPaid=True, 
            payment_type=PaymentType.Subscription
        ).first()

        no_of_licences = course_order.no_of_licence if course_order else 0 

        corporate_users = User.objects.filter(corporate=obj.id)
        users_id = list(corporate_users.values_list("id", flat=True))
        license_used = len(users_id)  # Avoids another .count() query

        course_count = UserCourses.objects.filter(user_id__in=users_id).count()

        data = {
            "no_of_licences": no_of_licences,
            "license_used": license_used,
            "remaning_licence": no_of_licences - license_used,
            "registered_users": license_used,
            "assigned_courses": course_count,
        }
        return data
    
    class Meta:
        model = User
        fields = ["id",'first_name',"last_name","email","is_active","created_at","counters","active_suscription","student_lists"]



class ChangeCorporateAdminUserStatusSerializer(serializers.ModelSerializer) :
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
    

class CreateCorporateAdminUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length = 255, required=True)
    last_name = serializers.CharField(max_length = 255, required=True)
    email = serializers.EmailField(max_length = 255, required=True)
    phone = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    address = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    city = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    state = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    country = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    pincode = serializers.CharField(max_length = 8, required=False, allow_blank=True)
    image = serializers.FileField(required=False,allow_null=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp","svg"])])
    
    class Meta:
        model = User
        fields = ['email','first_name','last_name',"address","city","state","country","pincode","phone","image"]
        

    def validate(self, data):
        user_count = User.objects.filter(email = data.get('email').lower()).count()
        if user_count > 0:
            raise serializers.ValidationError('Email address is already registered with Us')
        
        return data


    def create(self, validate_data):
        password = generate_random_password(8)
        info = { "first_name": validate_data.get('first_name'),"last_name": validate_data.get('last_name'), 'email': validate_data.get('email').lower(), 'password': password}
        user = User.objects.create_user(**info)
        assign_role(user, "CorporateAdmin")

        user.role = User.CorporateAdmin
        user.email_verified = 1
        user.is_active = True
        user.phone1 = validate_data.get('phone')
        user.address = validate_data.get('address')
        user.country = validate_data.get('country')
        user.state = validate_data.get('state')
        user.city = validate_data.get('city')
        user.pincode = validate_data.get('pincode')
        user.image = validate_data.get('image')
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
    

class UpdateCoporateAdminUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length = 255, required=True)
    last_name = serializers.CharField(max_length = 255, required=True)
    phone = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    address = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    city = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    state = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    country = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    pincode = serializers.CharField(max_length = 8, required=False, allow_blank=True)
    image = serializers.FileField(required=False,allow_null=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp","svg"])])

    class Meta:
        model = User
        fields = ['first_name','last_name',"address","city","state","country","pincode","phone","image"]
        

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
        info.image = validate_data.get('image', info.image)
        info.save()
        return info
    


class AssignSubscriptiontoCorporateAdminUserSerializer(serializers.ModelSerializer) :
    user_id = serializers.IntegerField(required=True)
    plan_id = serializers.IntegerField(required=True)

    class Meta:
        model = Order
        fields = ['user_id',"plan_id"]
        
    def validate(self, data):
        plan_id = data.get('plan_id')
        plan_count = SubscriptionPlans.objects.filter(id=plan_id).count()
        if plan_count == 0:
            raise serializers.ValidationError("Invalid Subscription Plan ID")
        

        course = Order.objects.filter(user = data.get('user_id'), isPaid = True, payment_type = PaymentType.Subscription, subscription_status=OrderStatus.Active).order_by('-created_at').first()

        if course is not None:
            raise serializers.ValidationError('You have a already active subscription')
        
        return data

    def create(self , validate_data):

        subscription_plan = SubscriptionPlans.objects.filter(id=validate_data.get('plan_id')).first()
        user = User.objects.filter(id = validate_data.get('user_id')).first()
        current_year = datetime.now().year
        count = Order.objects.all().count()
        order_id = f"{current_year}-{str(count + 1).zfill(4)}"  


        tax = subscription_plan.gst_amount
        total_amount = subscription_plan.amount_without_gst
        order_total_amount = subscription_plan.amount

        book_order = Order(
            orderID = order_id,
            user = user,
            first_name = user.first_name,
            last_name = user.last_name,
            email = user.email,
            phone = user.phone1,
            payment_type = PaymentType.Subscription,
            plan = subscription_plan,
            subscription_id = subscription_plan.id,
            subscription_type = subscription_plan.plan_type,
            no_of_licence = subscription_plan.no_of_licence,
            amount = total_amount,
            gst_amount = tax,
            total_amount = order_total_amount,
            isPaid = True,
            subscription_status = OrderStatus.Active,
            payment_method = PaymentMethod.Offline
        )
        book_order.save()

        from django.utils import timezone
        from dateutil.relativedelta import relativedelta
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



class UserCoursesDetailSerializer(serializers.ModelSerializer):
    course_detail = MyCourseDetailSerializer(source="course", read_only=True)
    courses_progress = serializers.SerializerMethodField('get_courses_progress')
    certificate = serializers.SerializerMethodField('get_certificate')
            
    def get_certificate(self, obj):
        get_certificate = UserCertificates.objects.filter(user_id = obj.user.id, course_id = obj.course.id).first()
        if get_certificate is not None:
            return get_certificate.certificate_url
        return None
        
    def get_courses_progress(self, obj):
        total_video_duration = Course.objects.filter(id = obj.course.id).aggregate(Sum('total_video_duration')).get('total_video_duration__sum')  or 0

        total_duration_video_watched = UserLectureProgress.objects.filter(course_id = obj.course.id, user_id = obj.user.id).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        video_duration_progress = 0
        if total_duration_video_watched > total_video_duration:
            video_duration_progress =  100
        else:
            if total_video_duration > 0:
                video_duration_progress =  math.ceil(total_duration_video_watched * 100 / total_video_duration)

        return video_duration_progress
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pass the context to the nested serializer
        if 'context' in kwargs:
            self.fields['course_detail'].context.update(kwargs['context'])

    class Meta:
        model = UserCourses
        fields = ["id", "course_detail","courses_progress","is_started","certificate"]


class GetStudentDetailSerializer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    courses = serializers.SerializerMethodField('get_courses')
    
    def get_courses(self, obj):
        users_courses = UserCourses.objects.filter(user=obj, paid=True).select_related("course").order_by("-id")
        return UserCoursesDetailSerializer(users_courses, many=True, context={"user": obj.id}).data
    
    class Meta:
        model = User
        fields = ['id','first_name','last_name', 'email','phone1',"is_active","date_joined","last_login","image","courses"]



class GetChapterQuizListSerializer(serializers.ModelSerializer):
    chapter = serializers.SerializerMethodField('get_chapter')
    total_question = serializers.SerializerMethodField('get_total_question')
    
    def get_total_question(self, obj):
        option = QuizQuestions.objects.filter(chapter_quiz_id=obj.id).count()
        return option
    
    
    def get_chapter(self, obj):
        if obj.chapter is None:
            return []
        category = Chapters.objects.filter(id=obj.chapter.id).first()
        return ChapterInfoSerializer(category).data
    
    class Meta:
        model = ChapterQuizs
        fields = ["id","name","description","thumbnail","chapter","status","pass_percentage","total_question","created_at"]


class PracticeTestListingSerializer(serializers.ModelSerializer):
    quiz = serializers.SerializerMethodField('get_quiz')
    def get_quiz(self, obj):
        users_courses = ChapterQuizs.objects.filter(id=obj.quiz.id).first()
        return GetChapterQuizListSerializer(users_courses).data

    result = serializers.SerializerMethodField('get_result')
    def get_result(self, obj):
        if obj.quiz.pass_percentage > obj.score:
            return "Fail"
        return "Pass"

    class Meta:
        model = PracticeTests
        fields = ['id','start_time',"end_time",'status',"result","total_question","total_right_answer_given","total_wrong_answer_given","total_time_taken",'score',"created_at","quiz"]


class VideoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Videos
        fields = ["id",'name',"transcoded_video","video_caption","video_duration"]

        
class EbookDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChapterBooks
        fields = ["id",'name']


class ChapterLectureSerializer(serializers.ModelSerializer) :
    video_info = serializers.SerializerMethodField('get_video')
    ebook_info = serializers.SerializerMethodField('get_ebook')
   
    def get_ebook(self, obj):
        if obj.ebook:
            ebook_detail = ChapterBooks.objects.filter(id = obj.ebook.id).first()
            return EbookDetailSerializer(ebook_detail).data
        return {}
    
    def get_video(self, obj):
        if obj.video:
            video_detail = Videos.objects.filter(id = obj.video.id).first()
            return VideoDetailSerializer(video_detail).data
        return {}
    
    class Meta:
        model = ChapterLectures
        fields = "__all__"

class GetUserNotesSerializer(serializers.ModelSerializer):
    lecture_info = serializers.SerializerMethodField('get_lecture_info')
    def get_lecture_info(self, obj):
        category = ChapterLectures.objects.filter(id=obj.chapter_lecture.id).first()
        serializer = ChapterLectureSerializer(category, context={'user':self.context.get('user')})
        return serializer.data

    class Meta:
        model = Notes
        fields = "__all__"



class ChapterInfoSerializer(serializers.ModelSerializer) :
    class Meta:
        model = Chapters
        fields = ["id",'name',"no_of_videos","no_of_videos_duration"]


class DashboardCourseChapterListingSerializer(serializers.ModelSerializer) :
    chapter_info = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField('get_progress')
    video_watched = serializers.SerializerMethodField('get_video_watched')
    total_video_watched = serializers.SerializerMethodField('get_total_video_watched')

    def get_total_video_watched(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).count()
        return total_video_watched

    def get_video_watched(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        return total_video_watched
    
    def get_progress(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        if total_video_watched > parent.chapter.no_of_videos_duration:
            return 100
        else:
            if parent.chapter.no_of_videos_duration == 0:
                return 0
            return math.ceil(total_video_watched * 100 / parent.chapter.no_of_videos_duration)

    
    def get_chapter_info(self, parent):
        info = Chapters.objects.get(id = parent.chapter.id)
        return ChapterInfoSerializer(info).data

    class Meta:
        model = CourseChapters
        fields = ['id','chapter_info',"progress","video_watched","total_video_watched"]



class ActivityLogListingSerializer(serializers.ModelSerializer):
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = ["id", "action", "entity_type", "metadata", "created_at", "time_ago"]

    def get_time_ago(self, obj):
        if obj.created_at:
            return naturaltime(obj.created_at)
        return None