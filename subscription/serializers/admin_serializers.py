from rest_framework import serializers
from subscription.models import *
from courses.models import *
from users.models import *


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
    