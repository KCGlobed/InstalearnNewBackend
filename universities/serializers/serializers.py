from rest_framework import serializers
from universities.models import *
from subscription.models import *
from rolepermissions.checkers import has_role
from django.conf import settings
from django.core.mail import send_mail
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
        user.university = course_category
        user.email_verified = 1
        user.is_active = False
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



class ShareCourseAccessSerializer(serializers.ModelSerializer) :
    first_name = serializers.CharField(max_length = 255, required=True)
    last_name = serializers.CharField(max_length = 255, required=True)
    email = serializers.EmailField(max_length = 255, required=True)
    phone = serializers.CharField(max_length = 255, required=True)
    course_id = serializers.ListField(required=True)
    
    class Meta:
        model = Order
        fields = ['first_name',"last_name","email","phone",'course_id']
        
    def validate_course_id(self, value):
        if not value:
            raise serializers.ValidationError("Course ID list cannot be empty.")

        existing_ids = set(
            Course.objects.filter(id__in=value).values_list('id', flat=True)
        )
        
        missing_ids = set(value) - existing_ids
        
        if missing_ids:
            raise serializers.ValidationError(
                f"The following course IDs do not exist: {list(missing_ids)}"
            )
        return value
    

    def validate(self, data):

        course_order = Order.objects.filter(
            user_id=self.context.get('user').id, 
            isPaid=True, 
            payment_type=PaymentType.Subscription, 
            subscription_status=OrderStatus.Active
        ).order_by('-created_at').first()
        if course_order is None:
            raise serializers.ValidationError("You do not have an active subscription plan. Please subscribe to gain access.")

        no_of_licences = course_order.no_of_licence if course_order else 0 

        used_licences_count = User.objects.filter(
            corporate_id = self.context.get('user').id
        ).count()

        if used_licences_count >= no_of_licences:
            raise serializers.ValidationError("You have used all the student seats available under this subscription. Please upgrade your plan or purchase additional licenses to add more users.")
        
        return data


    def create(self , validate_data):

        password = generate_random_password(8)

        email_to_check = validate_data.get('email', '').lower()
        email_exists = User.objects.filter(email=email_to_check).exists()
        if email_exists:
            user_info = User.objects.filter(email=email_to_check).first()
            assign_role(user_info, "Student")
            user_info.email_verified = 1
            user_info.is_active = True
            user_info.save()

        else:
            info = { "first_name": validate_data.get('first_name'),"last_name": validate_data.get('last_name'), 'email': validate_data.get('email').lower(), 'password': password}

            user_info = User.objects.create_user(**info)
            assign_role(user_info, "Student")

            user_info.role = User.Student
            user_info.email_verified = 1
            user_info.university = self.context.get('user').university
            user_info.is_active = True
            user_info.save()
        
        url = settings.BASE_URL+"/login"

        subject = 'Thank you for registering!'

        message = f''
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user_info.email, ]
        html_message = loader.render_to_string(
            'new_user_email.html',
            {
                'name': user_info.first_name +' '+ user_info.last_name,
                'verification_link': url,
                "email": user_info.email,
                "password": password,

            }
        )

        send_mail( subject, message, email_from, recipient_list,html_message=html_message )

        course_order = Order.objects.filter(
            user_id=self.context.get('user').id, 
            isPaid=True, 
            payment_type=PaymentType.Subscription, 
            subscription_status=OrderStatus.Active
        ).order_by('-created_at').first()

        cart_items = Course.objects.filter(id__in=validate_data.get('course_id'))
        for cart_course in cart_items:
            cart_order = UserCourses(
                order = course_order,
                course = cart_course,
                user = user_info,
                paid=True

            )
            cart_order.save()

        return user_info



class AssignCourseAccessSerializer(serializers.ModelSerializer) :
    user_id = serializers.IntegerField(required=True)
    course_id = serializers.ListField(required=True)
    
    class Meta:
        model = Order
        fields = ["user_id",'course_id']
    
    def validate_course_id(self, value):
        if not value:
            raise serializers.ValidationError("Course ID list cannot be empty.")

        existing_ids = set(
            Course.objects.filter(id__in=value).values_list('id', flat=True)
        )
        
        missing_ids = set(value) - existing_ids
        
        if missing_ids:
            raise serializers.ValidationError(
                f"The following course IDs do not exist: {list(missing_ids)}"
            )
        return value
    
    def validate(self, data):
        user_info = User.objects.get(id = data.get('user_id'))
        course_order = Order.objects.filter(
            user_id=self.context.get('user').id, 
            isPaid=True, 
            payment_type=PaymentType.Subscription, 
            subscription_status=OrderStatus.Active
        ).order_by('-created_at').first()

        cart_items = Course.objects.filter(id__in=data.get('course_id'))
        for cart_course in cart_items:
            if UserCourses.objects.filter(user=user_info, course=cart_course).exists():
                raise serializers.ValidationError(f"User have a already course access of x: {cart_course.name}")
            
        return data


    def create(self , validate_data):

        user_info = User.objects.get(id = validate_data.get('user_id'))
        course_order = Order.objects.filter(
            user_id=self.context.get('user').id, 
            isPaid=True, 
            payment_type=PaymentType.Subscription, 
            subscription_status=OrderStatus.Active
        ).order_by('-created_at').first()

        cart_items = Course.objects.filter(id__in=validate_data.get('course_id'))
        for cart_course in cart_items:
            cart_order = UserCourses(
                order = course_order,
                course = cart_course,
                user = user_info,
                paid=True

            )
            cart_order.save()

        return user_info




class RemoveCourseAccessSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=True)
    course_id = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )
    
    class Meta:
        model = Order
        fields = ["user_id", "course_id"]
    
    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User does not exist.")
        return value

    def validate_course_id(self, value):
        if not value:
            raise serializers.ValidationError("Course ID list cannot be empty.")

        existing_ids = set(
            Course.objects.filter(id__in=value).values_list('id', flat=True)
        )
        
        missing_ids = set(value) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(
                f"The following course IDs do not exist: {list(missing_ids)}"
            )
        return value
    
    def validate(self, data):
        user_id = data.get('user_id')
        course_ids = data.get('course_id')
        
        user_info = User.objects.get(id=user_id)
        
        assigned_course_ids = set(
            UserCourses.objects.filter(
                user=user_info, 
                course_id__in=course_ids
            ).values_list('course_id', flat=True)
        )
        
        not_assigned = set(course_ids) - assigned_course_ids
        
        if not_assigned:
            course_names = list(Course.objects.filter(id__in=not_assigned).values_list('name', flat=True))
            raise serializers.ValidationError(
                f"User does not have access to these courses: {', '.join(course_names)}"
            )
            
        return data

    def create(self, validated_data):
        user_id = validated_data.get('user_id')
        course_ids = validated_data.get('course_id')
        
        user_info = User.objects.get(id=user_id)

        UserCourses.objects.filter(
            user=user_info, 
            course_id__in=course_ids
        ).delete()

        return user_info