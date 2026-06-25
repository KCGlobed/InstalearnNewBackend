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
import pandas as pd
import tempfile
import re
from rest_framework.permissions import IsAuthenticated
import calendar
import time
import json
from google.cloud import storage
from google.oauth2 import service_account
info = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
credentials = service_account.Credentials.from_service_account_info(info)
client = storage.Client(credentials=credentials, project=credentials.project_id)
from google.cloud.video.transcoder_v1 import TranscoderServiceClient
import whisper


class AddtoCartView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def post(self, request,format=None):
        serializer = AddtoCartSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            course = Cart.objects.filter(device_id = request.data.get('device_id'), course_id = request.data.get('course_id')).first()
            serializer = CartSerializer(course)
            return success_response(message="Course added in Cart Successfully", data=serializer.data, status_code=status.HTTP_200_OK)

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
                subscription_payment = OrderSubscriptionPayments.objects.filter(order_id = order_info.id, isPaid = True).count()
                if subscription_payment > 0:
                    return success_response(message="Payment successfully received!", data={}, status_code=status.HTTP_200_OK)

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
                order_info.subscription_status = OrderStatus.Active
                order_info.start_date = date.today()
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
                

                current_GMT = time.gmtime()
                ts = calendar.timegm(current_GMT)
                
                template = get_template('pdf/invoice.html')
                html  = template.render(result)
                result = BytesIO()
                destination = settings.MEDIA_ROOT+ 'reports/'
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
    


class ManageBackgroundTaskView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def get(self, request, format=None):
        
        calculate_video_duration_and_questions()

        info = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
        credentials = service_account.Credentials.from_service_account_info(info)

        storage_client = storage.Client(credentials=credentials, project=credentials.project_id)

        client = TranscoderServiceClient(credentials=credentials)

        video_list = Videos.objects.filter(is_uploaded = True, is_completed = True, transcoded_video = "")
        print(video_list)
        if video_list is not None:
            for video_info in video_list:
                    
                bucketName, file_name = parse_gcs_url(video_info.video_file.url)
                
                input_uri = f'gs://instalearn-public-bucket/'+str(file_name)
                output_uri = f'gs://instalearn-public-bucket/media/mini_lms/transcoder/'

                current_GMT = time.gmtime()
                unique_id = str(calendar.timegm(current_GMT))

                video_file_name = "video_"+str(unique_id)
                job = {
                    "input_uri": input_uri,
                    "output_uri": output_uri,
                    "template_id": "preset/web-hd",
                    "config": {
                        "elementary_streams": [
                            {
                                "key": "video-stream0",
                                "video_stream": {
                                    "h264": {
                                        "bitrate_bps": 5500000,
                                        "frame_rate": 30,
                                        "height_pixels": 720,
                                        "width_pixels": 1280,
                                        "gop_duration": "15.0s"
                                    }
                                }
                            },
                            {
                                "key": "audio-stream0",
                                "audio_stream": {
                                    "codec": "aac",
                                    "bitrate_bps": 64000
                                }
                            }
                        ],
                        "mux_streams": [
                            {
                                "key": video_file_name,
                                "container": "ts",
                                "elementary_streams": [
                                    "video-stream0","audio-stream0"
                                ],
                                "segment_settings": {
                                    "segment_duration": "15.0s",
                                    "individual_segments": True
                                }
                            }
                        ],
                        "manifests": [
                            {
                                "file_name": str(unique_id) + ".m3u8",
                                "mux_streams": [
                                    video_file_name
                                ]
                            }
                        ]
                    }
                }
                
                job = client.create_job(
                    parent=f'projects/{settings.GS_PROJECT_ID}/locations/asia-south1',
                    job=job,
                )
                
                
                video_info.transcoded_video = 'media/lms_2/transcoder/'+f'{video_file_name}.m3u8'
                video_info.is_completed = True
                video_info.save()
                
                time.sleep(2)


        
        caption_video = Videos.objects.filter(is_uploaded = True, is_completed = True, video_caption__isnull = True) | Videos.objects.filter(is_uploaded = True, is_completed = True, video_caption = "")
        print(caption_video)
        if caption_video is not None:
            
            MODEL_DIR = os.path.join(settings.BASE_DIR, 'media')
            os.makedirs(MODEL_DIR, exist_ok=True)

            for video in caption_video:

                model = whisper.load_model("turbo",download_root=MODEL_DIR)
                option = whisper.DecodingOptions(language="en", fp16=False)
                result = model.transcribe(video.video_file.url)
                print(result)
                with tempfile.NamedTemporaryFile(suffix='.vtt', delete=False) as temp_file:
                    vtt_file_path = temp_file.name # This is correct, it gets the path
                    if result['segments']:
                        # Write directly to the temp_file object, which is already open
                        temp_file.write(b"WEBVTT \n\n")
                        
                        for seg in result['segments']:
                            temp_file.write(b"\n")
                            # Use .format() with .encode() to get bytes for the file
                            temp_file.write(
                                "{} --> {}\n".format(caption_time(seg['start']), caption_time(seg['end'])).encode('utf-8')
                            )
                            temp_file.write("{}\n".format(seg['text']).encode('utf-8'))
                

                # After the 'with' block, the file is closed, but not deleted yet
                try:
                    # GCS file naming logic
                    timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
                    report_name = "transcribe"
                    gcs_folder_name = "media/mini_lms/video_transcribe"
                    gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.vtt"

                    # Upload the temporary file to GCS
                    bucket = storage_client.get_bucket(settings.GS_BUCKET_NAME)
                    blob = bucket.blob(gcs_file_name)
                    blob.upload_from_filename(vtt_file_path)

                finally:
                    # Ensure the temporary file is deleted from the server's disk
                    os.remove(vtt_file_path)

                video.video_caption = "/"+gcs_file_name
                video.save()

        
        return success_response(message="Success", data={}, status_code=status.HTTP_200_OK)
    


class ManageLearningRemindersView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def get(self, request, format=None):
        now = timezone.localtime(timezone.now())
        current_time = now.time()
        current_date = now.date()
        current_day_slug = now.strftime('%a').lower()

        base_reminders = LearningReminders.objects.filter(
            time__hour=current_time.hour,
            time__minute=current_time.minute
        ).select_related('user', 'course')

        print(current_time.hour)
        print(current_time.minute)
        print(base_reminders)

        reminders_to_send = []

        # 2. Filter down based on Frequency
        for reminder in base_reminders:
            if not reminder.user or not reminder.user.email:
                continue

            if reminder.frequency == Frequency.Daily:
                reminders_to_send.append(reminder)

            elif reminder.frequency == Frequency.Weekly:
                if reminder.days:
                    # Clean up spaces and convert to a list: "mon, tue" -> ['mon', 'tue']
                    saved_days = [day.strip().lower() for day in reminder.days.split(',')]
                    
                    if current_day_slug in saved_days:
                        reminders_to_send.append(reminder)

            elif reminder.frequency == Frequency.Once:
                if reminder.date == current_date:
                    reminders_to_send.append(reminder)
                    # Optional: Delete or deactivate OneTime reminders so they don't fire again
                    # reminder.delete()

        # 3. Send the emails
        for reminder in reminders_to_send:
            try:

                subject = reminder.title or f"Reminder: Continue learning {reminder.course.name if reminder.course else ''}"
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [reminder.user.email, ]
                html_message = loader.render_to_string(
                    'reminder_email.html',
                    {
                        'user_name': reminder.user.first_name + reminder.user.last_name,
                        'course':reminder.course.name if reminder.course else '',
                    }
                )
                email = EmailMessage(
                    subject, html_message, email_from, recipient_list)
                
                email.content_subtype = "html"
                email.send()

            except Exception as e:
                pass
        
        return success_response(message="Success", data={}, status_code=status.HTTP_200_OK)
    

class GetPurchaseHistoryView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request,format=None):
        course = Order.objects.filter(user = request.user, isPaid = True)
        serializer = UserOrderListingSerializer(course, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class ValidateCouponView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def post(self, request,format=None):
        serializer = ValidateDeviceCouponSerializer(data=request.data)
        
        if serializer.is_valid():
            coupon = serializer.validated_data['coupon_obj']
            cart_items = serializer.validated_data['cart_items']
            
            total_cart_price = sum(item.course.price for item in cart_items if hasattr(item, 'course'))
            
            # Calculate discount
            discount_amount = 0.00
            if coupon.discount_type == 'percentage':
                discount_amount = (float(coupon.discount_value) / 100) * total_cart_price
            else:
                # Fixed price discount
                discount_amount = float(coupon.discount_value)

            # Ensure discount doesn't exceed total cost
            discount_amount = min(discount_amount, total_cart_price)
            final_price = total_cart_price - discount_amount

            return success_response(message="", data={
                "coupon_code": coupon.code,
                "discount_type": coupon.discount_type,
                "discount_value": float(coupon.discount_value),
                "summary": {
                    "original_total": float(total_cart_price),
                    "discount_applied": float(discount_amount),
                    "final_total": float(final_price)
                }
            }, status_code=status.HTTP_200_OK)
        
        return error_response(message="", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        