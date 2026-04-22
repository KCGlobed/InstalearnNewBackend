from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from subscription.serializers import *
from subscription.models import *
from courses.models import *
from subscription.renderers import SubscriptionRenderer
from django.template import loader
from django.core.mail import send_mail
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import get_template
from django.template import loader
from django.core.mail import EmailMessage
import os
from mini_lms.utils import *
from datetime import date, datetime, timedelta


class AddtoCartView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def post(self, request,format=None):
        serializer = AddtoCartSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Course added in Cart Successfully", data={}, status_code=status.HTTP_200_OK)

        return error_response(message="", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class ViewCartView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def post(self, request,format=None):
        course = Cart.objects.filter(device_id = request.data.get('device_id'))
        serializer = CartSerializer(course, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
        

# Remove Book From Cart
class RemoveCartView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def delete(self, request, cid, format=None):
        try:
            cart = Cart.objects.get(id = cid)
            cart.delete()
            return success_response(message="Course removed from Cart Successfully", data=[], status_code=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return error_response(message="Invalid Cart ID", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        

# Check Course In Cart Frontend
class CheckCourseInCartView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def post(self, request,format=None):
        cart_count = Cart.objects.filter(device_id = request.data.get('device_id'), course_id = request.data.get('course_id')).count()
        if cart_count > 0:
            course = Cart.objects.filter(device_id = request.data.get('device_id'), course_id = request.data.get('course_id')).first()
            serializer = CartSerializer(course)
            return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
        else:
            return success_response(message="", data=[], status_code=status.HTTP_200_OK)
        


class StartPaymentView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def post(self, request, format=None):
        serializer = StartPaymentSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Order Created Successfully", data=serializer.data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class CompletePaymentView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def post(self, request, format=None):
        serializer = CompletePaymentSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            order_info  = serializer.save()

            order = Order.objects.filter(id = order_info.id).first()
            order_data = CourseOrderSerializer(order)
            
            book_list = UserCourses.objects.filter(order_id = order_info.id, paid = 1).values_list('course', flat=True)
            category = Course.objects.filter(id__in=book_list)
            book_info = CourseListsSerializer(category,many =True)

            return success_response(message="Payment successfully received!", data={"order_info":order_data.data, "ordered_courses": book_info.data}, status_code=status.HTTP_200_OK)

        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class WebhookResponseView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def post(self, request, format=None):

        if request.data['event'] == 'order.paid':

            order_info = Order.objects.filter(razorpay_order_id = request.data['payload']['order']['entity']['id']).first()

            if order_info is not None:

                payment = OrderSubscriptionPayments()
                payment.order = order_info    
                payment.payment_id = request.data['payload']['payment']['entity']['id']
                payment.razorpay_order_id = request.data['payload']['payment']['entity']['order_id']
                payment.invoice_id = request.data['payload']['payment']['entity']['invoice_id']
                payment.amount = (request.data['payload']['payment']['entity']['amount'] / 100)
                payment.status = request.data['event']
                payment.isPaid = True
                payment.save()
            
                order_info.isPaid = True
                order_info.payment_status = 'completed'
                order_info.end_date = date.today() + timedelta(days=365)
                order_info.next_due = date.today() + timedelta(days=365)
                order_info.save()

                order_list = []

                invoice_info = None
                cart_count = UserCourses.objects.filter(order_id = order_info.id)
                for cart in cart_count:
                    cart.paid = 1
                    cart.save()

                    order_list.append({
                        'book_name': cart.course.name,
                        'total_price': cart.course.price,
                        'book_price': cart.course.price,
                        "qunatity": 1
                    })

                result = {
                        'invoice_info': invoice_info,
                        'order_info':order_info,
                        "order_list":order_list,
                        'isssue_date' : order_info.order_date
                    }
                

                import time
                import calendar
                current_GMT = time.gmtime()
                ts = calendar.timegm(current_GMT)
                
                template = get_template('pdf/invoice.html')
                html  = template.render(result)
                result = BytesIO()
                destination = settings.MEDIA_ROOT+ 'pdf_reports/'
                if not os.path.exists(destination):
                    os.makedirs(destination)
                file = open(destination + str(ts) +'_invoice.pdf', "w+b")
                html = html.encode('latin-1', 'replace').decode('latin-1')
                pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), dest=file)
                
                subject = 'Order Detail'
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [order_info.email, ]
                html_message = loader.render_to_string(
                    'course_order_email.html',
                    {
                        'user_name': order_info.first_name + order_info.last_name,
                        'order_list':order_list,
                        "order_info":order_info,
                        'total_price': order_info.total_amount,
                        'price': order_info.total_amount,
                        'tax': order_info.gst_amount,
                        'raz_pay_id':order_info.orderID
                    }
                )
                email = EmailMessage(
                    subject, html_message, email_from, recipient_list)
                
                email.attach_file(destination + str(ts) +'_invoice.pdf')
                email.content_subtype = "html"
                email.send()


                subject = 'Course Order Detail'
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [settings.ADMIN_EMAIL, ]
                html_message = loader.render_to_string(
                    'admin_order_email.html',
                    {
                        'user_name': order_info.first_name + order_info.last_name,
                        'order_list':order_list,
                        "order_info":order_info,
                        'tax': order_info.gst_amount,
                        'total_price': order_info.total_amount,
                        'price': order_info.total_amount,
                        'raz_pay_id':order_info.orderID
                    }
                )
                email = EmailMessage(
                    subject, html_message, email_from, recipient_list)
                
                # email.attach_file(destination + str(ts) +'_invoice.pdf')
                email.content_subtype = "html"
                email.send()
                
        return success_response(message="Payment successfully received!", data={}, status_code=status.HTTP_200_OK)



class StartSubscriptionView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def post(self, request, format=None):
        serializer = StartSubscriptionSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Subscription Created Successfully!", data={}, status_code=status.HTTP_200_OK)
        
        return error_response(message="", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class CompleteSubscriptionView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def post(self, request, format=None):
        serializer = CompleteSubscriptionSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            order_info  = serializer.save()

            order = Order.objects.filter(id = order_info.id).first()
            order_data = CourseOrderSerializer(order)
            
            book_list = UserCourses.objects.filter(order_id = order_info.id, paid = 1).values_list('course', flat=True)
            category = Course.objects.filter(id__in=book_list)
            book_info = CourseListsSerializer(category,many =True)

            return success_response(message="Payment successfully received!", data={"order_info":order_data.data, "ordered_courses": book_info.data}, status_code=status.HTTP_200_OK)

        return error_response(message="", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class TrailRegistrationView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def post(self, request, format=None):
        serializer = TrailRegistrationSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Registration Done! Please Check your email for account detail", data={"id":user.id}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)