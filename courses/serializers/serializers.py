from rest_framework import serializers
from courses.models import *
from subscription.models import *
from mini_lms.validator import *
from django.core.validators import FileExtensionValidator
import os
from instructor.models import *
from cms.models import *
from django.conf import settings
from google.cloud import storage
client = settings.GS_CREDENTIALS
import calendar
import time
from mini_lms.utils import *
from datetime import datetime,timezone, timedelta




class PlansListingSerializer(serializers.ModelSerializer) :
    class Meta:
        model = SubscriptionPlans
        fields = ['id','plan_name',"text_1","text_2","text_3","text_4","feature","status"]


class StudentChapterInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapters
        fields = ["name"]



class StudentTopicListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapters
        fields = ['id',"topic_detail"]


class CourseInstructorSerializer(serializers.ModelSerializer) :
    instructor = serializers.SerializerMethodField()

    def get_instructor(self, parent):
        info = InstructorProfile.objects.get(id = parent.instructor.id)
        return InstructorSerializer(info).data

    class Meta:
        model = CourseInstructors
        fields = ['id','instructor']


class InstructorSerializer(serializers.ModelSerializer) :
    class Meta:
        model = InstructorProfile
        fields = ['id','text_1',"text_2","text_3","experience","linkedin_url","description","image","company_image_1","company_image_2"]


class SearchCategorySerializer(serializers.ModelSerializer):
    subcategory = serializers.SerializerMethodField('get_subcategory')
    
    def get_subcategory(self, obj):
        category = Categories.objects.filter(parent_id=obj.id)
        return SearchCategorySerializer(category,many=True).data
    
    class Meta:
        model = Categories
        fields = ['id',"name","subcategory","icon","status"]


class SearchCourseSerializer(serializers.ModelSerializer):
    course_instructor = serializers.SerializerMethodField()

    def get_course_instructor(self, parent):
        info = CourseInstructors.objects.filter(course_id = parent.id)
        return CourseInstructorSerializer(info, many=True).data
    
    class Meta:
        model = Course
        fields = ['id',"name","image","course_instructor"]


    
class PartnerImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerImages
        fields = "__all__"


class GetLMStestimonialSerializer(serializers.ModelSerializer) :
    class Meta:
        model = Testimonials
        fields = ['id',"testimonials_type",'name',"image","college","qualification","content","featured"]


class AddCommentInCourseAnnouncementsSerializer(serializers.ModelSerializer) :
    announcement_id = serializers.IntegerField(required=True)
    content = serializers.CharField(required=True)
    class Meta:
        model = AnnouncementComments
        fields = ['announcement_id','content']
        
        
    def validate(self, data):

        return data

    def create(self , validate_data):
        announcement = CourseAnnouncements.objects.filter(id=validate_data.get('announcement_id')).first()
        
        announcement_obj = AnnouncementComments.objects.create(
            content=validate_data.get('content'),
            announcement=announcement,
            user=self.context.get('user')
        )
        
        return announcement_obj