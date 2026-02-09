from rest_framework import serializers
from subscription.models import *
from courses.models import *
from users.models import *
from mini_lms.utils import *
import razorpay


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