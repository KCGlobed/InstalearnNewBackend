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
    approved_status = serializers.BooleanField(required=True)
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

    class Meta:
        model = Order
        fields = ["plan_id"]
        
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