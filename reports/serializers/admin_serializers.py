from rest_framework import serializers
from users.models import *
from cms.models import *
from subscription.models import *
from mini_lms.utils import *
from itertools import chain
import pytz
from datetime import timedelta
from django.db.models import Q, Count



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


class StudentRegistrationSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    class Meta:
        model = User
        fields = ["id",'first_name',"last_name","email","phone1","category","reference_id","student_type","is_active","created_at"]


class OrderDetailAdminSerializer(serializers.ModelSerializer):
    ordered_courses = serializers.SerializerMethodField('get_ordered_courses')
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    def get_ordered_courses(self, obj):
        category = Course.objects.filter(usercourses__user_id=obj.user.id).distinct()
        return CourseListSerializer(category, many=True).data

    
    class Meta:
        model = Order
        fields = ["id","first_name","last_name","email","phone","total_amount","start_date","next_due","end_date","subscription_type","subscription_status","created_at","ordered_courses","trail_mode"]


class ContactListSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d")
    
    class Meta:
        model = ContactUs
        fields = ['id',"first_name","last_name",'email',"phone","message","created_at"]