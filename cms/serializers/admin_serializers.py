from rest_framework import serializers
from cms.models import *
from courses.models import *
from django.db import transaction
from django.core.validators import FileExtensionValidator
from mini_lms.utils import *


class FaqTopicListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQTopic
        fields = ["id","title","description","status","created_at"]


class CreateFaqTopicSerializer(serializers.ModelSerializer) :
    title = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = FAQTopic
        fields = ['title',"description"]
        
    def validate(self, data):
        name_count = FAQTopic.objects.filter(title = data.get('title')).count()
        if name_count > 0:
            raise serializers.ValidationError("Title Already Exists!")

        return data

    def create(self , validate_data):
        topic = FAQTopic(
            title = validate_data.get('title'),
            description = validate_data.get('description'),
            status = True
        )
        topic.save()

        return topic
    


class EditFAQTopicSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = FAQTopic
        fields = ['title',"description"]
        
    def validate(self, data):
        return data


    def update(self , category, validate_data):
        category.title = validate_data.get('title', category.title)
        category.description = validate_data.get('description', category.description)
        category.save()

        return category
    

class ChangeFAQTopicStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = FAQTopic
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    


class FaqListingSerializer(serializers.ModelSerializer):
    faq_topic = serializers.SerializerMethodField('get_faq_topic')
    
    def get_faq_topic(self, obj):
        if obj.faq_topic is not None:
            category = FAQTopic.objects.filter(id=obj.faq_topic.id).first()
            return FaqTopicListingSerializer(category).data
        return {}
    
    class Meta:
        model = FAQs
        fields = ["id","faq_topic","title","description","status","created_at"]



class CreateFaqSerializer(serializers.ModelSerializer) :
    title = serializers.CharField(max_length = 255, required=True)
    faq_topic_id = serializers.IntegerField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = FAQs
        fields = ['title',"description","faq_topic_id"]
        
    def validate(self, data):
        name_count = FAQTopic.objects.filter(id = data.get('faq_topic_id')).count()
        if name_count == 0:
            raise serializers.ValidationError("Invalid FAQ Topic ID!")

        return data

    def create(self , validate_data):
        topic = FAQs(
            title = validate_data.get('title'),
            description = validate_data.get('description'),
            faq_topic = FAQTopic.objects.filter(id = validate_data.get('faq_topic_id')).first(),
            status = True
        )
        topic.save()

        return topic
    

class EditFAQSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length = 255, required=True)
    faq_topic_id = serializers.IntegerField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = FAQTopic
        fields = ['title',"description","faq_topic_id"]
        
    def validate(self, data):
        name_count = FAQTopic.objects.filter(id = data.get('faq_topic_id')).count()
        if name_count == 0:
            raise serializers.ValidationError("Invalid FAQ Topic ID!")
        
        return data


    def update(self , category, validate_data):
        category.title = validate_data.get('title', category.title)
        category.description = validate_data.get('description', category.description)
        category.faq_topic = FAQTopic.objects.filter(id = validate_data.get('faq_topic_id')).first()
        category.save()

        return category
    


class ChangeFAQStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = FAQs
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category