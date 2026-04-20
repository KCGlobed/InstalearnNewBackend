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
    


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = "__all__"



class UpdateSettingSerializer(serializers.ModelSerializer):
    payment_type = serializers.IntegerField(required=True)
    test_public_key = serializers.CharField(max_length = 255, required=False)
    test_secret_key = serializers.CharField(max_length = 255, required=False)
    live_public_key = serializers.CharField(max_length = 255, required=False)
    live_secret_key = serializers.CharField(max_length = 255, required=False)
    no_days_trail = serializers.IntegerField(required=False, allow_null=True)
    try_for_free = serializers.IntegerField(required=False, allow_null=True)
    allow_device_restriction = serializers.BooleanField(required=False, allow_null=True)
    allowed_desktop = serializers.IntegerField(required=False, allow_null=True)
    allowed_tablet = serializers.IntegerField(required=False, allow_null=True)
    allowed_phone = serializers.IntegerField(required=False, allow_null=True)
    
    
    class Meta:
        model = Settings
        fields =  ["payment_type","test_public_key","test_secret_key","live_public_key","live_secret_key","no_days_trail","try_for_free","allow_device_restriction","allowed_desktop","allowed_tablet","allowed_phone"]
        
    def validate(self, data):
        return data


    def create(self , validate_data):
        setting = Settings.objects.all().first()
        if setting is None:
            setting = Settings()
        setting.payment_type = validate_data.get('payment_type', setting.payment_type)
        setting.test_public_key = validate_data.get('test_public_key', setting.test_public_key)
        setting.test_secret_key = validate_data.get('test_secret_key', setting.test_secret_key)
        setting.live_public_key = validate_data.get('live_public_key', setting.live_public_key)
        setting.live_secret_key = validate_data.get('live_secret_key', setting.live_secret_key)
        setting.no_days_trail = validate_data.get('no_days_trail', setting.no_days_trail)
        setting.try_for_free = validate_data.get('try_for_free', setting.try_for_free)
        setting.allow_device_restriction = validate_data.get('allow_device_restriction', setting.allow_device_restriction)
        setting.allowed_tablet = validate_data.get('allowed_tablet', setting.allowed_tablet)
        setting.allowed_phone = validate_data.get('allowed_phone', setting.try_for_free)
        setting.allowed_desktop = validate_data.get('allowed_desktop', setting.allowed_desktop)
        setting.save()

        return setting