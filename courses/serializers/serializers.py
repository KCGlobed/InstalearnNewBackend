from rest_framework import serializers
from courses.models import *
from subscription.models import *
from mini_lms.validator import *
from django.core.validators import FileExtensionValidator
import os
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




class StudentTopicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topics
        fields = ["name"]


class StudentTopicListSerializer(serializers.ModelSerializer):
    topic_detail = serializers.SerializerMethodField('get_topic_detail')
    def get_topic_detail(self, obj):
        category = Topics.objects.filter(id=obj.topic.id).first()
        return StudentTopicInfoSerializer(category).data
    
    class Meta:
        model = ChapterTopics
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
    class Meta:
        model = Categories
        fields = ['id',"name"]


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