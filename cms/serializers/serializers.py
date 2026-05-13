from rest_framework import serializers
from cms.models import *
from courses.models import *
from django.db import transaction
from django.core.validators import FileExtensionValidator
from mini_lms.utils import *
from django.template import loader
from django.core.mail import EmailMessage


class ContactUsSerializer(serializers.ModelSerializer) :
    first_name = serializers.CharField(max_length = 255, required=True)
    last_name = serializers.CharField(max_length = 255, required=True)
    email = serializers.CharField(max_length = 255, required=True)
    phone = serializers.CharField(max_length = 255, required=True)
    message = serializers.CharField(required=True)
    class Meta:
        model = ContactUs
        fields = ['first_name','last_name','message','email','phone']
        
    def validate(self, data):

        return data


    def create(self , validate_data):
        
        course_category = ContactUs(
            first_name = validate_data.get('first_name'),
            last_name = validate_data.get('last_name'),
            email = validate_data.get('email'),
            phone = validate_data.get('phone'),
            message = validate_data.get('message'),

        )
        course_category.save()
        
        subject = 'Contact Us'
        message = f'Hi you have got a contact us'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [settings.ADMIN_EMAIL,]

        html_message = loader.render_to_string(
            'contactEmail.html',
            {
                'first_name': validate_data.get('first_name'),
                'last_name':validate_data.get('last_name'),
                'email': validate_data.get('email'),
                'phone': validate_data.get('phone'),
                'message': validate_data.get('message')
            }
        )
        email = EmailMessage(
            subject, html_message, email_from, recipient_list)
        
        email.content_subtype = "html"
        email.send()

        return course_category