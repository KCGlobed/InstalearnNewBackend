from rest_framework import serializers
from subscription.models import *
from courses.models import *
from users.models import *
from cms.models import *
from django.conf import settings
from django.core.mail import send_mail
from mini_lms.roles import Student
from mini_lms.utils import *
from rolepermissions.roles import assign_role
import random
import math
from django.template import loader
from datetime import datetime, date, timedelta
import random, string
import razorpay
from django.db import transaction
from django.db.models import F
from decimal import Decimal

class AddtoCartSerializer(serializers.ModelSerializer) :
    course_id = serializers.IntegerField(required=True)
    device_id = serializers.CharField(max_length = 255, required=True)
    class Meta:
        model = Cart
        fields = ['device_id','course_id']
        
    def validate(self, data):
        
        course = data.get('course_id')
        course_count = Course.objects.filter(id=course).count()
        if course_count == 0:
            raise serializers.ValidationError("course does not exists with ID:"+str(course))
        
        cart_count = Cart.objects.filter(course_id=data.get('course_id'), device_id = data.get('device_id')).count()
        if cart_count > 0:
            raise serializers.ValidationError("Course already exists in your cart")

        return data


    def create(self , validate_data):
        
        book_cart = Cart(
                        device_id = validate_data.get('device_id'),
                        course = Course.objects.get(id = validate_data.get('course_id'))
                    )
        book_cart.save()

        return True
    

class CourseInfoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id",'name',"image","price","discount","total_reviews","avg_rating","total_video_duration"]


class CartSerializer(serializers.ModelSerializer):
    course_info = serializers.SerializerMethodField('get_course_info')
    
    def get_course_info(self, obj):
        category = Course.objects.filter(id=obj.course.id).first()
        return CourseInfoListSerializer(category).data
    
    class Meta:
        model = Cart
        fields = ['id',"course_info","created_at"]



class StartPaymentSerializer(serializers.ModelSerializer) :
    first_name = serializers.CharField(max_length = 100, required=True)
    last_name = serializers.CharField(max_length = 100, required=True)
    email = serializers.EmailField(max_length = 100, required=True)
    phone = serializers.CharField(max_length = 12, required=True)
    billing_address = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    city = serializers.CharField(max_length = 100, required=False, allow_blank=True)
    state = serializers.CharField(max_length = 100, required=False, allow_blank=True)
    pincode = serializers.CharField(max_length = 12, required=False, allow_blank=True)
    country = serializers.CharField(max_length = 100, required=False, allow_blank=True)
    user_id = serializers.CharField(max_length = 100, allow_blank=True)
    device_id = serializers.CharField(max_length = 255, write_only=True,required=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    
    class Meta:
        model = Order
        fields = "__all__"
        
    def validate(self, data):
        device_id = data.get('device_id')
        coupon_code = data.get('coupon_code')
        now = timezone.now()

        # 1. Ensure the device actually has items to checkout
        cart_items = Cart.objects.filter(device_id=device_id)
        if not cart_items.exists():
            raise serializers.ValidationError({"device_id": "Your cart is empty."})
        data['cart_items'] = cart_items

        # 2. If a coupon code is provided, validate it completely
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code.strip())
            except Coupon.DoesNotExist:
                raise serializers.ValidationError({"coupon_code": "This coupon code does not exist."})

            if not coupon.status or not (coupon.valid_from <= now <= coupon.valid_to):
                raise serializers.ValidationError({"coupon_code": "This coupon has expired or is inactive."})

            if coupon.usages_count >= coupon.max_usages:
                raise serializers.ValidationError({"coupon_code": "This coupon has reached its maximum usage limit."})

            total_cart_price = sum(item.course.price for item in cart_items if hasattr(item, 'course'))
            if Decimal(total_cart_price) < coupon.minimum_cart_value:
                raise serializers.ValidationError({
                    "coupon_code": f"This coupon requires a minimum cart total of ${coupon.minimum_cart_value}."
                })
            
            data['coupon_obj'] = coupon

        
        user_id = data.get('user_id')
        if user_id and str(user_id).strip():
            user = User.objects.filter(id=user_id).first()
            if user is None:
                raise serializers.ValidationError('Invalid User ID')
            
            if has_role(user, CorporateAdmin):
                raise serializers.ValidationError("Direct course purchases are unavailable. You may only access this content via an active subscription.!")
            
            course = Order.objects.filter(user = user, isPaid = True, payment_type = PaymentType.Subscription, subscription_status=OrderStatus.Active).order_by('-created_at').first()

            if course is not None:
                raise serializers.ValidationError('You have a already active subscription')
            
            
        
        email = data.get('email')
        if email and str(email).strip():
            user = User.objects.filter(email=email.lower()).first()
            if user is not None:
                if has_role(user, CorporateAdmin):
                    raise serializers.ValidationError("Direct course purchases are unavailable. You may only access this content via an active subscription.!")
            
                course = Order.objects.filter(user = user, isPaid = True, payment_type = PaymentType.Subscription, subscription_status=OrderStatus.Active).order_by('-created_at').first()

                if course is not None:
                    raise serializers.ValidationError('You have a already active subscription')

        return data


    def create(self , validate_data):

        if validate_data.get('user_id') is not None and validate_data.get('user_id') != "":
            user = User.objects.filter(id=validate_data.get('user_id')).first()
            if user is None:
                raise serializers.ValidationError('Invalid User ID')
        else:
            user = User.objects.filter(email=validate_data.get('email').lower()).first()
            if user is None:
                
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                info = { "first_name": validate_data.get('first_name'),"last_name": validate_data.get('last_name'), 'email': validate_data.get('email').lower(), 'phone': validate_data.get('phone'), 'password': password}

                user_info = User.objects.create_user(**info)
                assign_role(user_info, Student)

                user_info.email_verified = 1
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
                user = user_info
                send_mail( subject, message, email_from, recipient_list,html_message=html_message )

        current_year = datetime.now().year
        count = Order.objects.all().count()
        order_id = f"{current_year}-{str(count + 1).zfill(4)}"  
        
        cart_items = Cart.objects.filter(device_id=validate_data.get('device_id'))
        
        total_original_price = sum(item.course.price for item in cart_items)
        total_discount = 0.00
        coupon = None
        if validate_data.get('coupon_code'):
            coupon = Coupon.objects.get(code__iexact=validate_data.get('coupon_code').strip())
            if coupon.discount_type == 'percentage':
                total_discount = (float(coupon.discount_value) / 100) * total_original_price
            else:
                total_discount = float(coupon.discount_value)

            total_discount = min(total_discount, total_original_price)
        
        final_total = total_original_price - total_discount

        tax = round(final_total * 0.18)
        final_amount = round(final_total)

        order_total_amount = final_amount + tax

        book_order = Order(
            orderID = order_id,
            user = user,
            discount_amount = total_discount,
            first_name = validate_data.get('first_name'),
            last_name = validate_data.get('last_name'),
            email = validate_data.get('email'),
            phone = validate_data.get('phone'),
            billing_address = validate_data.get('billing_address'),
            city = validate_data.get('city'),
            state = validate_data.get('state'),
            country = validate_data.get('country'),
            pincode = validate_data.get('pincode'),
            amount = total_original_price,
            gst_amount = tax,
            total_amount = order_total_amount,
        )
        book_order.save()

        if coupon:
            book_order.coupon = coupon
            book_order.save()

            Coupon.objects.filter(id=coupon.id).update(usages_count=F('usages_count') + 1)
            

        cart_count = Cart.objects.filter(device_id=validate_data.get('device_id'))
        for cart in cart_count:
            cart_order = UserCourses(
                order = book_order,
                course = Course.objects.get(id = cart.course.id),
                user = user
            )
            cart_order.save()

        setting = GeneralSettings.objects.all().first()
        if order_total_amount > 0 :
            if setting.payment_type == 1:
                client = razorpay.Client(auth=(setting.test_public_key, setting.test_secret_key))
            else:
                client = razorpay.Client(auth=(setting.live_public_key, setting.live_secret_key))
                
            payment = client.order.create({"amount": book_order.total_amount * 100, 
                                    "currency": "INR", 
                                    "payment_capture": "1",
                                    "notes":{
                                        "name": book_order.first_name+" "+book_order.last_name,
                                        "email": book_order.email,
                                        "phone_number": book_order.phone,
                                        "payment_type":"instalearn_course_payment",
                                    }})
            book_order.razorpay_order_id = payment['id']
            book_order.save()
        

        return book_order
    

class CompletePaymentSerializer(serializers.ModelSerializer) :
    razorpay_payment_id = serializers.CharField(required=True,write_only = True)
    razorpay_order_id = serializers.CharField(required=True,write_only = True)
    razorpay_signature = serializers.CharField(required=True,write_only = True)
    device_id = serializers.CharField(max_length = 255, write_only=True,required=True)

    class Meta:
        model = Order
        fields = ['razorpay_payment_id','razorpay_order_id','razorpay_signature',"device_id"]
        
    def validate(self, data):
        return data


    def create(self , validate_data):
        
        ord_id = validate_data.get("razorpay_order_id")
        raz_pay_id = validate_data.get("razorpay_payment_id")
        raz_signature = validate_data.get("razorpay_signature")

        try:
            order = Order.objects.get(razorpay_order_id=ord_id)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Invalid Razorpay order ID")
        
        data = {
            'razorpay_order_id': ord_id,
            'razorpay_payment_id': raz_pay_id,
            'razorpay_signature': raz_signature
        }

        order.razorpay_payment_id = raz_pay_id
        order.razorpay_signature = raz_signature
        order.save()
        
        setting = GeneralSettings.objects.all().first()
        try:
            if setting.payment_type == 1:
                client = razorpay.Client(auth=(setting.test_public_key, setting.test_secret_key))
            else:
                client = razorpay.Client(auth=(setting.live_public_key, setting.live_secret_key))
            check = client.utility.verify_payment_signature(data)
            if check == False:
                raise serializers.ValidationError('Invalid Signature')
        except Exception as error:
            raise serializers.ValidationError("Unale to verify your Payment")
        
        order.isPaid = True
        order.subscription_status = OrderStatus.Active
        order.start_date = date.today()
        order.end_date = date.today() + timedelta(days=1825)
        order.next_due = date.today() + timedelta(days=1825)
        order.save()
        ordered_course = UserCourses.objects.filter(order_id = order.id)
        for ord in ordered_course:
            ord.paid = 1
            ord.save()

        cart_count = Cart.objects.filter(device_id=validate_data.get('device_id'))
        cart_count.delete()

        return order
    


class CourseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"


class CourseListsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id',"name","image"]



class StartSubscriptionSerializer(serializers.ModelSerializer) :
    first_name = serializers.CharField(max_length = 100, required=True)
    last_name = serializers.CharField(max_length = 100, required=True)
    email = serializers.EmailField(max_length = 100, required=True)
    phone = serializers.CharField(max_length = 100, required=True)
    user_id = serializers.IntegerField(allow_null=True, required=False)
    compnay_name = serializers.CharField(required=False, allow_blank=True)
    plan_id = serializers.IntegerField(required=True,write_only=True)

    class Meta:
        model = Order
        fields = "__all__"
        
    def validate(self, data):

        plan_id = data.get('plan_id')
        plan_count = SubscriptionPlans.objects.filter(id=plan_id).count()
        if plan_count == 0:
            raise serializers.ValidationError("Invalid Subscription Plan ID")
        
        user_id = data.get('user_id')
        if user_id and str(user_id).strip():
            user = User.objects.filter(id=user_id).first()
            if user is None:
                raise serializers.ValidationError('Invalid User ID')
            
            course = Order.objects.filter(user = user, isPaid = True, payment_type = PaymentType.Subscription, subscription_status=OrderStatus.Active).order_by('-created_at').first()

            if course is not None:
                raise serializers.ValidationError('You have a already active subscription')
            
        email = data.get('email')
        if email and str(email).strip():
            user = User.objects.filter(email=email).first()
            if user is not None:

                course = Order.objects.filter(user = user, isPaid = True, payment_type = PaymentType.Subscription, subscription_status=OrderStatus.Active).order_by('-created_at').first()

                if course is not None:
                    raise serializers.ValidationError('You have a already active subscription')

        return data


    def create(self , validate_data):

        general_settings = GeneralSettings.objects.all().first()
        subscription_plan = SubscriptionPlans.objects.filter(id=validate_data.get('plan_id')).first()

        
        if validate_data.get('user_id') is not None and validate_data.get('user_id') != "":
            user = User.objects.filter(id=validate_data.get('user_id')).first()
            if user is None:
                raise serializers.ValidationError('Invalid User ID')
            assign_role(user_info, CorporateAdmin)
        else:
            user = User.objects.filter(email=validate_data.get('email').lower()).first()
            if user is None:
                
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                info = { "first_name": validate_data.get('first_name'),"last_name": validate_data.get('last_name'), 'email': validate_data.get('email').lower(), 'phone': validate_data.get('phone'), 'password': password}

                user_info = User.objects.create_user(**info)
                assign_role(user_info, CorporateAdmin)

                user_info.role = User.CorporateAdmin
                user_info.email_verified = 1
                user_info.company_name = validate_data.get('compnay_name')
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
                user = user_info
                send_mail( subject, message, email_from, recipient_list,html_message=html_message )
            else:
                assign_role(user, CorporateAdmin)
        current_year = datetime.now().year
        count = Order.objects.all().count()
        order_id = f"{current_year}-{str(count + 1).zfill(4)}"  
        
        tax = subscription_plan.gst_amount
        total_amount = subscription_plan.amount_without_gst
        order_total_amount = subscription_plan.amount

        book_order = Order(
            orderID = order_id,
            user = user,
            first_name = validate_data.get('first_name'),
            last_name = validate_data.get('last_name'),
            email = validate_data.get('email'),
            phone = validate_data.get('phone'),
            payment_type = PaymentType.Subscription,
            plan = subscription_plan,
            subscription_id = subscription_plan.id,
            subscription_type = subscription_plan.plan_type,
            no_of_licence = subscription_plan.no_of_licence,
            amount = total_amount,
            gst_amount = tax,
            total_amount = order_total_amount,
        )
        book_order.save()

        if total_amount > 0 :
            if general_settings.payment_type == 1:
                client = razorpay.Client(auth=(general_settings.test_public_key, general_settings.test_secret_key))
            else:
                client = razorpay.Client(auth=(general_settings.live_public_key, general_settings.live_secret_key))
            
            if subscription_plan.plan_type == 1:
                quantity = 60
            elif subscription_plan.plan_type == 2:
                quantity = 10
            else:
                quantity = 5

            payment = client.subscription.create({
                            'plan_id': subscription_plan.plan_id,
                            'customer_notify': True,
                            'quantity': 1,
                            'total_count': quantity,
                            'notes': {'payment_type': 'instalearn_subscription_payment'}
                        })
            book_order.razorpay_order_id = payment['id']
            book_order.subscription_url = payment['short_url']
            book_order.subscription_id = payment['id']
            book_order.save()
        

        return book_order
    

class CompleteSubscriptionSerializer(serializers.ModelSerializer) :
    razorpay_payment_id = serializers.CharField(required=True,write_only = True)
    razorpay_order_id = serializers.CharField(required=True,write_only = True)
    razorpay_signature = serializers.CharField(required=True,write_only = True)
    class Meta:
        model = Order
        fields = ['razorpay_payment_id','razorpay_order_id','razorpay_signature']
        
    def validate(self, data):
        
        return data


    def create(self , validate_data):
        
        ord_id = validate_data.get("razorpay_order_id")
        raz_pay_id = validate_data.get("razorpay_payment_id")
        raz_signature = validate_data.get("razorpay_signature")

        try:
            order = Order.objects.get(razorpay_order_id=ord_id)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Invalid Razorpay order ID")
        
        data = {
            'razorpay_subscription_id': ord_id,
            'razorpay_payment_id': raz_pay_id,
            'razorpay_signature': raz_signature
        }

        order.razorpay_payment_id = raz_pay_id
        order.razorpay_signature = raz_signature
        order.save()
        
        setting = GeneralSettings.objects.all().first()
        try:
            if setting.payment_type == 1:
                client = razorpay.Client(auth=(setting.test_public_key, setting.test_secret_key))
            else:
                client = razorpay.Client(auth=(setting.live_public_key, setting.live_secret_key))
            check = client.utility.verify_subscription_payment_signature(data)
            if check == False:
                raise serializers.ValidationError('Invalid Signature')
        except Exception as error:
            raise serializers.ValidationError("Unale to verify your Payment")
        
        order.isPaid = True
        order.subscription_status = OrderStatus.Active
        order.save()

        return order
    


class TrailRegistrationSerializer(serializers.ModelSerializer) :
    first_name = serializers.CharField(max_length = 255, required=True)
    last_name = serializers.CharField(max_length = 255, required=True)
    email = serializers.EmailField(max_length = 255, required=False)
    phone = serializers.CharField(max_length = 13, min_length=10, required=True)
    course_id = serializers.ListField(required=True, child=serializers.IntegerField(required=True))

    class Meta:
        model = TrailUser
        fields =  ["first_name","last_name","email","phone","course_id"]
    
    def validate_course_id(self, value):
        return validate_course_id_list(value)
    
    def validate(self, data):
        
        user = User.objects.filter(email = data.get('email').lower()).count()
        if user > 0:
            raise serializers.ValidationError("Email Already Registered With Us")
        
        trail_user = TrailUser.objects.filter(email = data.get('email').lower()).count()
        if trail_user > 0:
            raise serializers.ValidationError("Email Already Used for Trail Period")
        

        return data


    def create(self , validate_data):
        
        with transaction.atomic():
            trail_user = TrailUser(
                first_name = validate_data.get('first_name'),
                last_name = validate_data.get('last_name'),
                email = validate_data.get('email').lower(),
                phone = validate_data.get('phone'),
            )
            trail_user.save()
            
            password = generate_random_password(8)

            info = { "first_name": validate_data.get('first_name'),"last_name": validate_data.get('last_name'), 'email': validate_data.get('email'), 'phone': validate_data.get('phone'), 'password': password}

            user = User.objects.create_user(**info)
            assign_role(user, "Student")

            user.role = User.Student
            user.email_verified = 1
            user.is_active = True
            user.save()
            
            trail_user.user =  user
            trail_user.save()

            trail_setting = GeneralSettings.objects.all().first()


            url = settings.BASE_URL+"/login"
            subject = 'Thank you for registering!'
            message = f''
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [user.email, ]
            html_message = loader.render_to_string(
                'trail_user_login_email.html',
                {
                    'name': user.first_name +' '+ user.last_name,
                    'verification_link': url,
                    "email": user.email,
                    "password": password,
                    "trail_days":trail_setting.no_days_trail,

                }
            )

            send_mail( subject, message, email_from, recipient_list,html_message=html_message )

            
            Begindatestring = date.today()
            Enddate = Begindatestring + timedelta(days=trail_setting.no_days_trail)

            current_year = datetime.now().year
            count = Order.objects.all().count()
            order_id = f"{current_year}-{str(count + 1).zfill(4)}" 
            
            order_info = Order(
                orderID = order_id,
                user = user,
                first_name = validate_data.get('first_name'),
                last_name = validate_data.get('last_name'),
                email = validate_data.get('email'),
                phone = validate_data.get('phone'),
                amount = 0,
                gst_amount = 0,
                total_amount = 0,
                payment_method = PaymentMethod.Online,
                trail_mode = True,
                start_date = Begindatestring,
                next_due = Enddate,
                end_date = Enddate,
                subscription_status = OrderStatus.Active,
                isPaid = True
            )
            order_info.save()

            course_data = validate_data.get('course_id', []) 
            
            if len(course_data) > 0:
                for index , course_id in enumerate(course_data):
                    course = Course.objects.get(id = course_id)
                    chap = TrailUserCourses(
                            course=course,
                            trail_user = trail_user
                        )
                    chap.save()

                    user_course = UserCourses(
                        order = order_info,
                        user = user,
                        course = course,
                        trail = True,
                        paid = True
                    )
                    user_course.save()


        return trail_user
    


class CourseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id",'name']


class UserOrderListingSerializer(serializers.ModelSerializer):
    ordered_courses = serializers.SerializerMethodField('get_ordered_courses')
    order_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    def get_ordered_courses(self, obj):
        category = Course.objects.filter(usercourses__user_id=obj.user.id, usercourses__order_id = obj.id).distinct()
        return CourseListSerializer(category, many=True).data

    
    class Meta:
        model = Order
        fields = ["id","first_name","last_name","email","phone","total_amount","gst_amount","amount","razorpay_order_id","payment_method","subscription_status","created_at","ordered_courses","order_date","isPaid"]


class PlanInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlans
        fields = ["id",'plan_name']

class UserSubscriptionListingSerializer(serializers.ModelSerializer):
    plan_info = serializers.SerializerMethodField('get_plan_info')
    order_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    def get_plan_info(self, obj):
        category = SubscriptionPlans.objects.filter(id=obj.plan.id).first()
        return PlanInfoSerializer(category).data

    
    class Meta:
        model = Order
        fields = ["id","first_name","last_name","email","phone","total_amount","no_of_licence","razorpay_order_id","payment_method","subscription_status","created_at","plan_info","order_date","isPaid","start_date","next_due"]



class ValidateDeviceCouponSerializer(serializers.Serializer):
    device_id = serializers.CharField(required=True, trim_whitespace=True)
    code = serializers.CharField(required=True, trim_whitespace=True)

    def validate(self, data):
        device_id = data.get('device_id')
        code = data.get('code').upper()
        now = timezone.now()

        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError({"code": "This coupon code does not exist."})

        if not coupon.status or not (coupon.valid_from <= now <= coupon.valid_to):
            raise serializers.ValidationError({"code": "This coupon has expired or is inactive."})

        if coupon.usages_count >= coupon.max_usages:
            raise serializers.ValidationError({"code": "This coupon has reached its maximum usage limit."})

        cart_items = Cart.objects.filter(device_id=device_id)
        if not cart_items.exists():
            raise serializers.ValidationError({"device_id": "No items found in the cart for this device."})

        total_cart_price = sum(item.course.price for item in cart_items if hasattr(item, 'course'))

        if Decimal(total_cart_price) < coupon.minimum_cart_value:
            raise serializers.ValidationError({
                "coupon_code": f"This coupon requires a minimum cart total of ${coupon.minimum_cart_value}."
            })
    
        # Pass both variables forward to the view
        data['coupon_obj'] = coupon
        data['cart_items'] = cart_items
        return data
    


class CancelSubscriptionSerializer(serializers.ModelSerializer) :
    order_id = serializers.CharField(required=True,write_only = True)
    
    class Meta:
        model = Order
        fields = ['order_id']
        
    def validate(self, data):
        return data


    def create(self , validate_data):
        
        ord_id = validate_data.get("order_id")

        try:
            order = Order.objects.get(id=ord_id)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Invalid order ID")
       
        setting = GeneralSettings.objects.all().first()
        try:
            if setting.payment_type == 1:
                client = razorpay.Client(auth=(setting.test_public_key, setting.test_secret_key))
            else:
                client = razorpay.Client(auth=(setting.live_public_key, setting.live_secret_key))
            subscriptionId = order.subscription_id

            client.subscription.cancel(subscriptionId, {
            "cancel_at_cycle_end": False
            })
        except Exception as error:
            raise serializers.ValidationError("Unale to verify your Payment")
        
        order.subscription_status = OrderStatus.Cancelled
        order.isPaid = False
        order.save()

        return order
    

class UpgradeSubscriptionSerializer(serializers.ModelSerializer) :
    order_id = serializers.CharField(required=True,write_only = True)
    plan_id = serializers.CharField(required=True,write_only = True)

    class Meta:
        model = Order
        fields = ['order_id',"plan_id"]
        
    def validate(self, data):
        return data


    def create(self , validate_data):
        
        ord_id = validate_data.get("order_id")

        try:
            order = Order.objects.get(id=ord_id)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Invalid order ID")
       
        subscription_plan = SubscriptionPlans.objects.filter(id=validate_data.get('plan_id')).first()
    
        setting = GeneralSettings.objects.all().first()
        try:
            if setting.payment_type == 1:
                client = razorpay.Client(auth=(setting.test_public_key, setting.test_secret_key))
            else:
                client = razorpay.Client(auth=(setting.live_public_key, setting.live_secret_key))
            subscriptionId = order.subscription_id

            client.subscription.edit(subscriptionId, {
                "plan_id": subscription_plan.plan_id,
                "customer_notify":True,
                "schedule_change_at":"now"
            })
        except razorpay.errors.BadRequestError as error:
            raise serializers.ValidationError(f"Razorpay Error: {str(error)}")

        except Exception as error:
            raise serializers.ValidationError("Unable to verify your payment.")
        
        order.subscription_status = OrderStatus.Active
        order.no_of_licence = subscription_plan.no_of_licence

        order.save()

        return order