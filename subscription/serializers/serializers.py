from rest_framework import serializers
from subscription.models import *
from courses.models import *
from users.models import *
from django.conf import settings
from django.core.mail import send_mail
from mini_lms.roles import Student
from rolepermissions.roles import assign_role
import random
import math
from django.template import loader
from datetime import datetime
import random, string
import razorpay


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
        fields = ['name',"image","price"]


class CartSerializer(serializers.ModelSerializer):
    course_info = serializers.SerializerMethodField('get_course_info')
    
    def get_course_info(self, obj):
        category = Course.objects.filter(id=obj.course.id).first()
        return CourseInfoListSerializer(category).data
    
    class Meta:
        model = Cart
        fields = ['id',"course_info","created_at"]


class GatewayListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = ['gateway_type',"gateway_logo"]


class StartPaymentSerializer(serializers.ModelSerializer) :
    first_name = serializers.CharField(max_length = 100, required=True)
    last_name = serializers.CharField(max_length = 100, required=True)
    email = serializers.EmailField(max_length = 100, required=True)
    mobile = serializers.CharField(max_length = 12, required=True)
    address = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    city = serializers.CharField(max_length = 100, required=False, allow_blank=True)
    state = serializers.CharField(max_length = 100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length = 12, required=False, allow_blank=True)
    country = serializers.CharField(max_length = 100, required=False, allow_blank=True)
    gateway_type = serializers.CharField(max_length = 100, write_only=True,required=True)
    user_id = serializers.CharField(max_length = 100, allow_blank=True)
    device_id = serializers.CharField(max_length = 255, write_only=True,required=True)
    code = serializers.CharField(max_length = 255, required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = "__all__"
        
    def validate(self, data):

        gateway_type = data.get('gateway_type')
        gateway_count = Settings.objects.filter(gateway_type=gateway_type).count()
        if gateway_count == 0:
            raise serializers.ValidationError("Invalid Payment Gateway")
        
        course = data.get('code')
        if course is not None and len(course) > 0:
            course_count = Coupon.objects.filter(code=course).count()
            if course_count == 0:
                raise serializers.ValidationError("Invalid Coupon Code!")
            
            cart_count = Coupon.objects.filter(code=course,is_active=1).count()
            if cart_count == 0:
                raise serializers.ValidationError("Coupon is Inactive!")
            
            coupon = Coupon.objects.filter(code=course,is_active=1).first()
            if coupon.expiration_date < timezone.now():
                raise serializers.ValidationError("Coupon has expired!")
        
        return data


    def create(self , validate_data):

        gateway_type = validate_data.get('gateway_type')
        razorpay_key = Settings.objects.filter(gateway_type=gateway_type).first()


        cart_count = Cart.objects.filter(device_id=validate_data.get('device_id'))
        if len(cart_count) == 0:
            raise serializers.ValidationError('No course found in cart')

        cart_items = Cart.objects.filter(device_id=validate_data.get('device_id'))
        total_amount = 0
        for item in cart_items:
            total_amount += item.course.price
        
        if validate_data.get('user_id') is not None and validate_data.get('user_id') != "":
            user = User.objects.filter(id=validate_data.get('user_id')).first()
            if user is None:
                raise serializers.ValidationError('Invalid User ID')
        else:
            user = User.objects.filter(email=validate_data.get('email')).first()
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
        
        tax = math.ceil(total_amount * 0.18)
        total_cost = total_amount

        code = validate_data.get('code')
        discounted_amount = 0
        final_amount = math.ceil(total_cost)
        
        if code is not None and len(code) > 0:
            coupon = Coupon.objects.filter(code=code, is_active=1).first()
            if coupon is not None:
                if coupon.discount_type == 'percentage':
                    discount = (math.ceil(coupon.discount_value) / 100) * total_cost
                elif coupon.discount_type == 'fixed':
                    discount = coupon.discount_value
                else:
                    raise serializers.ValidationError("Invalid discount type!")
                discounted_amount = math.ceil(discount)
                final_amount = math.ceil(total_cost) - math.ceil(discount)
            else:
                raise serializers.ValidationError("Invalid Coupon!")

        order_total_amount = final_amount + tax

        book_order = Order(
            orderID = order_id,
            user = user,
            discount_amount = discounted_amount,
            coupon_code = validate_data.get('code'),
            first_name = validate_data.get('first_name'),
            last_name = validate_data.get('last_name'),
            email = validate_data.get('email'),
            mobile = validate_data.get('mobile'),
            address = validate_data.get('address'),
            city = validate_data.get('city'),
            state = validate_data.get('state'),
            country = validate_data.get('country'),
            postal_code = validate_data.get('postal_code'),
            payment_gateway = validate_data.get('gateway_type'),
            amount = total_amount,
            tax_amount = tax,
            total_amount = order_total_amount,
        )
        book_order.save()
        if code is not None and len(code) > 0:
            book_order.coupon = Coupon.objects.filter(code=code, is_active=1).first()
            book_order.save()
            
        if cart_count:
            for cart in cart_count:
                cart_order = UserCourses(
                    order = book_order,
                    course = Course.objects.get(id = cart.course.id),
                    user = user
                )
                cart_order.save()
        
        if razorpay_key.gateway_type == "razorpay":
            if total_amount > 0 :
                client = razorpay.Client(auth=(razorpay_key.public_key, razorpay_key.secret_key))
                payment = client.order.create({"amount": book_order.total_amount * 100, 
                                        "currency": "INR", 
                                        "payment_capture": "1",
                                        "notes":{
                                            "name": book_order.first_name+" "+book_order.last_name,
                                            "email": book_order.email,
                                            "phone_number": book_order.mobile,
                                            "payment_type":"mini_course_payment",
                                            "coupon":code
                                        }})
                book_order.razorpay_order_id = payment['id']
                book_order.save()
        else:
            raise serializers.ValidationError('Invalid Payment Gateway')

        return book_order
    

class CompletePaymentSerializer(serializers.ModelSerializer) :
    razorpay_payment_id = serializers.CharField(required=True,write_only = True)
    razorpay_order_id = serializers.CharField(required=True,write_only = True)
    razorpay_signature = serializers.CharField(required=True,write_only = True)
    gateway_type = serializers.CharField(max_length = 100, required=True)
    class Meta:
        model = Order
        fields = ['razorpay_payment_id','razorpay_order_id','razorpay_signature',"gateway_type"]
        
    def validate(self, data):
        gateway_type = data.get('gateway_type')
        gateway_count = Settings.objects.filter(gateway_type=gateway_type).count()
        if gateway_count == 0:
            raise serializers.ValidationError("Invalid Payment Gateway")
        
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
        
        gateway_type = validate_data.get('gateway_type')
        razorpay_key = Settings.objects.filter(gateway_type=gateway_type).first()
        if razorpay_key.gateway_type == "razorpay":
            try:
                client = razorpay.Client(auth=(razorpay_key.public_key, razorpay_key.secret_key))
                check = client.utility.verify_payment_signature(data)
                if check == False:
                    raise serializers.ValidationError('Invalid Signature')
            except Exception as error:
                raise serializers.ValidationError("Unale to verify your Payment")
        else:
            raise serializers.ValidationError("Invalid Payment Gateway")
        
        order.isPaid = True
        order.payment_status = "completed"
        order.save()
        ordered_course = UserCourses.objects.filter(order_id = order.id)
        for ord in ordered_course:
            ord.paid = 1
            ord.save()

        return order
    


class CourseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"


class CourseListsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id',"name","image"]



class ApplyCouponSerializer(serializers.ModelSerializer) :
    code = serializers.CharField(max_length = 255, required=True)
    total_amount = serializers.IntegerField(required=True)
    class Meta:
        model = Cart
        fields = ['code','total_amount']
        
    def validate(self, data):
        
        course = data.get('code')
        course_count = Coupon.objects.filter(code=course).count()
        if course_count == 0:
            raise serializers.ValidationError("Invalid Coupon Code!")
        
        cart_count = Coupon.objects.filter(code=course,is_active=1).count()
        if cart_count == 0:
            raise serializers.ValidationError("Coupon is Inactive!")
        
        coupon = Coupon.objects.filter(code=course,is_active=1).first()
        if coupon.expiration_date < timezone.now():
            raise serializers.ValidationError("Coupon has expired!")
        
        return data



class StartSubscriptionSerializer(serializers.ModelSerializer) :
    first_name = serializers.CharField(max_length = 100, required=True)
    last_name = serializers.CharField(max_length = 100, required=True)
    email = serializers.EmailField(max_length = 100, required=True)
    mobile = serializers.CharField(max_length = 12, required=True)
    address = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    city = serializers.CharField(max_length = 100, required=False, allow_blank=True)
    state = serializers.CharField(max_length = 100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length = 12, required=False, allow_blank=True)
    country = serializers.CharField(max_length = 100, required=False, allow_blank=True)
    gateway_type = serializers.CharField(max_length = 100, write_only=True,required=True)
    user_id = serializers.CharField(max_length = 100, allow_blank=True)
    plan_id = serializers.IntegerField(required=True,write_only=True)

    class Meta:
        model = Order
        fields = "__all__"
        
    def validate(self, data):

        gateway_type = data.get('gateway_type')
        gateway_count = Settings.objects.filter(gateway_type=gateway_type).count()
        if gateway_count == 0:
            raise serializers.ValidationError("Invalid Payment Gateway")
        
        plan_id = data.get('plan_id')
        plan_count = SubscriptionPlans.objects.filter(id=plan_id).count()
        if plan_count == 0:
            raise serializers.ValidationError("Invalid Subscription Plan")
        
        return data


    def create(self , validate_data):

        gateway_type = validate_data.get('gateway_type')
        razorpay_key = Settings.objects.filter(gateway_type=gateway_type).first()
        subscription_plan = SubscriptionPlans.objects.filter(id=validate_data.get('plan_id')).first()

        
        if validate_data.get('user_id') is not None and validate_data.get('user_id') != "":
            user = User.objects.filter(id=validate_data.get('user_id')).first()
            if user is None:
                raise serializers.ValidationError('Invalid User ID')
        else:
            user = User.objects.filter(email=validate_data.get('email')).first()
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
        
        tax = subscription_plan.gst_amount
        total_amount = subscription_plan.amount_without_gst
        order_total_amount = subscription_plan.amount

        book_order = Order(
            orderID = order_id,
            user = user,
            coupon_code = validate_data.get('code'),
            first_name = validate_data.get('first_name'),
            last_name = validate_data.get('last_name'),
            email = validate_data.get('email'),
            mobile = validate_data.get('mobile'),
            address = validate_data.get('address'),
            city = validate_data.get('city'),
            state = validate_data.get('state'),
            country = validate_data.get('country'),
            postal_code = validate_data.get('postal_code'),
            payment_gateway = validate_data.get('gateway_type'),
            payment_type = "subscription",
            subscription_plan = subscription_plan,
            amount = total_amount,
            tax_amount = tax,
            total_amount = order_total_amount,
        )
        book_order.save()

        if razorpay_key.gateway_type == "razorpay":
            if total_amount > 0 :
                client = razorpay.Client(auth=(razorpay_key.public_key, razorpay_key.secret_key))
                payment = client.order.create({"amount": book_order.total_amount * 100, 
                                        "currency": "INR", 
                                        "payment_capture": "1",
                                        "notes":{
                                            "name": book_order.first_name+" "+book_order.last_name,
                                            "email": book_order.email,
                                            "phone_number": book_order.mobile,
                                            "payment_type":"mini_course_payment",
                                            "plan_name":subscription_plan.plan_name
                                        }})
                book_order.razorpay_order_id = payment['id']
                book_order.save()
        else:
            raise serializers.ValidationError('Invalid Payment Gateway')

        return book_order
    

class CompleteSubscriptionSerializer(serializers.ModelSerializer) :
    razorpay_payment_id = serializers.CharField(required=True,write_only = True)
    razorpay_order_id = serializers.CharField(required=True,write_only = True)
    razorpay_signature = serializers.CharField(required=True,write_only = True)
    gateway_type = serializers.CharField(max_length = 100, required=True)
    class Meta:
        model = Order
        fields = ['razorpay_payment_id','razorpay_order_id','razorpay_signature',"gateway_type"]
        
    def validate(self, data):
        gateway_type = data.get('gateway_type')
        gateway_count = Settings.objects.filter(gateway_type=gateway_type).count()
        if gateway_count == 0:
            raise serializers.ValidationError("Invalid Payment Gateway")
        
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
        
        gateway_type = validate_data.get('gateway_type')
        razorpay_key = Settings.objects.filter(gateway_type=gateway_type).first()
        if razorpay_key.gateway_type == "razorpay":
            try:
                client = razorpay.Client(auth=(razorpay_key.public_key, razorpay_key.secret_key))
                check = client.utility.verify_payment_signature(data)
                if check == False:
                    raise serializers.ValidationError('Invalid Signature')
            except Exception as error:
                raise serializers.ValidationError("Unale to verify your Payment")
        else:
            raise serializers.ValidationError("Invalid Payment Gateway")
        
        order.isPaid = True
        order.payment_status = "completed"
        order.save()

        cart_count = SubscriptionCourses.objects.filter(subscription_plan_id = order.subscription_plan.id)
        for cart in cart_count:
            order_c = UserCourses.objects.filter(course = cart.course,user = order.user).first()
            if order_c is not None:
                order_c.order = order
                order_c.save()
            else:
                cart_order = UserCourses(
                    order = order,
                    course = cart.course,
                    user = order.user,
                    paid = 1
                )
                cart_order.save()

        return order