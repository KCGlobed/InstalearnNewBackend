from rest_framework import serializers
from universities.models import *
from rolepermissions.checkers import has_role
from django.conf import settings
from django.template import loader
from mini_lms.utils import *
import re
from django.template import loader
from django.core.mail import EmailMessage



class SubmitUniversityRequestSerializer(serializers.ModelSerializer) :
    first_name = serializers.CharField(max_length = 255, required=True)
    last_name = serializers.CharField(max_length = 255, required=True)
    phone_number = serializers.CharField(max_length = 255, required=True)
    work_email = serializers.CharField(max_length = 255, required=True)
    institution_type = serializers.CharField(max_length = 255, required=True)
    institution_name = serializers.CharField(max_length = 255, required=True)
    country = serializers.CharField(max_length = 255, required=True)
    job_role = serializers.CharField(max_length = 255, required=True)
    department = serializers.CharField(max_length = 255, required=True)
    
    class Meta:
        model = University
        fields = ['first_name','last_name','phone_number','work_email','institution_type',"institution_name","country","job_role","department"]
        
    def validate(self, data):

        user = User.objects.filter(email =data.get('work_email').lower()).count()
        if user > 0:
            raise serializers.ValidationError("Email already registered with us")

        return data


    def create(self , validate_data):
        
        course_category = University(
            first_name = validate_data.get('first_name'),
            phone_number = validate_data.get('phone_number'),
            work_email = validate_data.get('work_email'),
            institution_type = validate_data.get('institution_type'),
            institution_name = validate_data.get('institution_name'),
            last_name = validate_data.get('last_name'),
            country = validate_data.get('country'),
            job_role = validate_data.get('job_role'),
            department = validate_data.get('department')
        )
        course_category.save()
        password = generate_random_password(8)

        info = { "first_name": validate_data.get('first_name'),"last_name": validate_data.get('last_name'), 'email': validate_data.get('work_email').lower(), 'password': password}
        user = User.objects.create_user(**info)
        assign_role(user, "UniversityAdmin")
        user.role = User.UniversityAdmin
        user.email_verified = 1
        user.is_active = True
        user.save()

        subject = 'New University Request'
        message = f'Hi you have got a contact us'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [settings.ADMIN_EMAIL,]

        html_message = loader.render_to_string(
            'university_request_email.html',
            {
                "first_name" : validate_data.get('first_name'),
                "phone_number" : validate_data.get('phone_number'),
                "work_email" : validate_data.get('work_email'),
                "institution_type" : validate_data.get('institution_type'),
                "institution_name" : validate_data.get('institution_name'),
                "last_name" : validate_data.get('last_name'),
                "country" : validate_data.get('country'),
                "job_role" : validate_data.get('job_role'),
                "department" : validate_data.get('department')
            }
        )
        email = EmailMessage(
            subject, html_message, email_from, recipient_list)
        
        email.content_subtype = "html"
        email.send()

        return course_category