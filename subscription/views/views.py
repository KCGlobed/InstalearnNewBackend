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
from django.template.loader import get_template, render_to_string
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
        
        data = request.data
        event = data.get('event')

        if event == 'order.paid':
            payload = data.get('payload', {})
            order_entity = payload.get('order', {}).get('entity', {})
            payment_entity = payload.get('payment', {}).get('entity', {})

            razorpay_order_id = order_entity.get('id')
            if not razorpay_order_id:
                return success_response(message="Missing order ID", data={}, status_code=status.HTTP_400_BAD_REQUEST)

            try:
                # 3. Retrieve and Validate Order
                order_info = Order.objects.filter(razorpay_order_id=razorpay_order_id).first()
                if not order_info:
                    return success_response(message="Order not found", data={}, status_code=status.HTTP_200_OK)

                # Idempotency check: Ensure we don't process a duplicate webhook
                has_already_paid = OrderSubscriptionPayments.objects.filter(
                    order_id=order_info.id, 
                    isPaid=True
                ).exists()

                if has_already_paid:
                    return success_response(message="Payment successfully received!", data={}, status_code=status.HTTP_200_OK)

                # 4. Save Payment details
                OrderSubscriptionPayments.objects.create(
                    order=order_info,
                    payment_id=payment_entity.get('id'),
                    razorpay_order_id=payment_entity.get('order_id'),
                    invoice_id=payment_entity.get('invoice_id'),
                    amount=(payment_entity.get('amount', 0) / 100),
                    status=event,
                    isPaid=True
                )

                # 5. Update Order Properties
                one_year_later = date.today() + timedelta(days=365)
                order_info.isPaid = True
                order_info.subscription_status = OrderStatus.Active
                order_info.start_date = date.today()
                order_info.end_date = one_year_later
                order_info.next_due = one_year_later
                order_info.save()

                # 6. Fetch Cart Items & Build Order Summary List
                order_list = []
                user_courses = UserCourses.objects.filter(order_id=order_info.id).select_related('course')
                
                for item in user_courses:
                    # Collect item meta
                    order_list.append({
                        'book_name': item.course.name if item.course else "Unknown Course",
                        'total_price': item.course.price if item.course else 0,
                        'book_price': item.course.price if item.course else 0,
                        "qunatity": 1
                    })
                
                # Bulk update the items to paid state rather than calling .save() per iteration
                user_courses.update(paid=1)

                # 7. Generate PDF Invoice 
                ts = calendar.timegm(time.gmtime())
                destination = os.path.join(settings.MEDIA_ROOT, 'reports/')
                os.makedirs(destination, exist_ok=True)
                pdf_filename = f"{ts}_invoice.pdf"
                pdf_path = os.path.join(destination, pdf_filename)

                template_ctx = {
                    'invoice_info': None,
                    'order_info': order_info,
                    "order_list": order_list,
                    'isssue_date': order_info.order_date
                }
                
                html_template = get_template('pdf/invoice.html')
                rendered_html = html_template.render(template_ctx).encode('latin-1', 'replace').decode('latin-1')

                with open(pdf_path, "w+b") as file_handle:
                    pisa.pisaDocument(BytesIO(rendered_html.encode("ISO-8859-1")), dest=file_handle)

                # 8. Send Communications (User Email)
                user_full_name = f"{order_info.first_name} {order_info.last_name}".strip()
                email_from = settings.EMAIL_HOST_USER
                
                user_html = render_to_string('course_order_email.html', {
                    'user_name': user_full_name,
                    'order_list': order_list,
                    "order_info": order_info,
                    'total_price': order_info.total_amount,
                    'price': order_info.total_amount,
                    'tax': order_info.gst_amount,
                    'raz_pay_id': order_info.orderID
                })
                
                user_email = EmailMessage('Order Detail', user_html, email_from, [order_info.email])
                user_email.attach_file(pdf_path)
                user_email.content_subtype = "html"
                user_email.send()

                # Send Communications (Admin Notification Email)
                admin_html = render_to_string('admin_order_email.html', {
                    'user_name': user_full_name,
                    'order_list': order_list,
                    "order_info": order_info,
                    'tax': order_info.gst_amount,
                    'total_price': order_info.total_amount,
                    'price': order_info.total_amount,
                    'raz_pay_id': order_info.orderID
                })
                
                admin_email = EmailMessage('Course Order Detail', admin_html, email_from, [settings.ADMIN_EMAIL])
                admin_email.content_subtype = "html"
                admin_email.send()

            except Exception as inner_error:
                logger.error(f"Error executing webhook logic: {str(inner_error)}", exc_info=True)
                # Fail gracefully by sending a 200 OK so Razorpay doesn't trigger continuous retries
                return success_response(message="Error processing webhook event internally", data={}, status_code=status.HTTP_200_OK)

        return success_response(message="Payment successfully received!", data={}, status_code=status.HTTP_200_OK)



class StartSubscriptionView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def post(self, request, format=None):
        serializer = StartSubscriptionSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Subscription Created Successfully!", data=serializer.data, status_code=status.HTTP_200_OK)
        
        return error_response(message="", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class CompleteSubscriptionView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def post(self, request, format=None):
        serializer = CompleteSubscriptionSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            order_info  = serializer.save()

            order = Order.objects.filter(id = order_info.id).first()
            order_data = CourseOrderSerializer(order)

            return success_response(message="Payment successfully received!", data={"order_info":order_data.data}, status_code=status.HTTP_200_OK)

        return error_response(message="", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class TrailRegistrationView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def post(self, request, format=None):
        serializer = TrailRegistrationSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Registration Done! Please Check your email for account detail", data={"id":user.id}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class SubscriptionPlanListView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def get(self, request, format=None):
        plans = SubscriptionPlans.objects.filter(plan_for = PlanFor.Corporates, status = True)
        serializer = SubscriptionPlanDetailSerializer(plans, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class ManageBackgroundTaskView(APIView):
    renderer_classes = [SubscriptionRenderer]
    def get(self, request, format=None):
        
        calculate_video_duration_and_questions()

        info = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
        credentials = service_account.Credentials.from_service_account_info(info)

        storage_client = storage.Client(credentials=credentials, project=credentials.project_id)

        client = TranscoderServiceClient(credentials=credentials)

        video_list = Videos.objects.filter(is_uploaded = True, is_completed = True, transcoded_video = "") | Videos.objects.filter(is_uploaded = True, is_completed = True, transcoded_video__isnull = True)
        
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
        course = Order.objects.filter(user = request.user, isPaid = True, payment_type = PaymentType.Course)
        serializer = UserOrderListingSerializer(course, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class GetMyActiveSubscriptionView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request,format=None):
        course = Order.objects.filter(user = request.user, isPaid = True, payment_type = PaymentType.Subscription)
        serializer = UserSubscriptionListingSerializer(course, many=True)
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
        

class PaymentResponseView(APIView):
    renderer_classes = [SubscriptionRenderer]

    def post(self, request, format=None):
        data = request.data
        event = data.get('event')
        payload = data.get('payload', {})
        
        subscription_entity = payload.get('subscription', {}).get('entity', {})
        payment_entity = payload.get('payment', {}).get('entity', {})

        subscription_id = subscription_entity.get('id')
        
        if not event or not subscription_id:
            return error_response(message="Malformed payload", data=[], status_code=status.HTTP_400_BAD_REQUEST)

        # Fetch Order info once if subscription_id is present
        order_info = Order.objects.filter(razorpay_order_id=subscription_id).first()

        # Helper variables for timestamps
        current_end_ts = subscription_entity.get('current_end')
        end_at_ts = subscription_entity.get('end_at')
        next_due_date = datetime.fromtimestamp(current_end_ts).strftime('%Y-%m-%d') if current_end_ts else None
        end_date_val = datetime.fromtimestamp(end_at_ts).strftime('%Y-%m-%d') if end_at_ts else None

        # 3. Handle Events
        # try:
        # --- EVENT: SUBSCRIPTION ACTIVATED ---
        if event == 'subscription.activated':
            # Create payment record
            OrderSubscriptionPayments.objects.create(
                order=order_info,
                payment_id=payment_entity.get('id'),
                razorpay_order_id=payment_entity.get('order_id'),
                invoice_id=payment_entity.get('invoice_id'),
                amount=(payment_entity.get('amount', 0) / 100),
                response=data,
                status=event,
                isPaid=True
            )

            if order_info:
                order_info.subscription_status = OrderStatus.Active
                if next_due_date: order_info.next_due = next_due_date
                if end_date_val: order_info.end_date = end_date_val
                order_info.save()

                # Send User Subscription Email
                plan_info = SubscriptionPlans.objects.filter(id=order_info.plan.id).first()
                if plan_info:
                    html_message = loader.render_to_string('subscription_email.html', {
                        'username': f"{order_info.first_name} {order_info.last_name}",
                        'plan_name': plan_info.plan_name,
                        'price': plan_info.amount,
                        'price_with_sign': plan_info.currency
                    })
                    email = EmailMessage('Subscription Activated', html_message, settings.EMAIL_HOST_USER, [order_info.email])
                    email.content_subtype = "html"
                    email.send()

            # User Payment Received Email
            user_email = order_info.email
            if user_email:
                html_user = loader.render_to_string('subscription_payment_email.html', {'subscription_id': subscription_id})
                email_user = EmailMessage('Payment Received!', html_user, settings.EMAIL_HOST_USER, [order_info.email])
                email_user.content_subtype = "html"
                email_user.send()

                # Admin Notification Email
                html_admin = loader.render_to_string('subscription_payment_email_admin.html', {
                    'subscription_id': subscription_id,
                    "email": user_email
                })
                email_admin = EmailMessage('Subscription Payment Received!', html_admin, settings.EMAIL_HOST_USER, [settings.ADMIN_EMAIL])
                email_admin.content_subtype = "html"
                email_admin.send()

        # --- EVENT: SUBSCRIPTION CHARGED ---
        elif event == 'subscription.charged':
            today = datetime.today().date()
            payment_id = payment_entity.get('id')
            rp_order_id = payment_entity.get('order_id')
            invoice_id = payment_entity.get('invoice_id')

            # Check if already processed
            already_processed = OrderSubscriptionPayments.objects.filter(
                payment_date__date=today, 
                payment_id=payment_id, 
                razorpay_order_id=rp_order_id, 
                invoice_id=invoice_id,
                status='subscription.charged'
            ).exists()

            if not already_processed:
                order_subscription = OrderSubscriptionPayments.objects.create(
                    order=order_info,
                    payment_id=payment_id,
                    razorpay_order_id=rp_order_id,
                    invoice_id=invoice_id,
                    amount=(payment_entity.get('amount', 0) / 100),
                    response=data,
                    status=event,
                    isPaid=True
                )

                if order_info:
                    if next_due_date: order_info.next_due = next_due_date
                    if end_date_val: order_info.end_date = end_date_val
                    order_info.save()
                    
                    # Generate Razorpay Client for Invoice Download
                    razorpay_key = GeneralSettings.objects.first()
                    if razorpay_key:
                        if razorpay_key.payment_type == 1:
                            client = razorpay.Client(auth=(razorpay_key.test_public_key, razorpay_key.test_secret_key))
                        else:
                            client = razorpay.Client(auth=(razorpay_key.live_public_key, razorpay_key.live_secret_key))
                        
                        if invoice_id:
                            plan_info = SubscriptionPlans.objects.filter(id=order_info.plan.id).first()

                            invoice_info = client.invoice.fetch(invoice_id)
                            result = {
                                'invoice_info': invoice_info,
                                'order_info': order_info,
                                'isssue_date': datetime.fromtimestamp(invoice_info.get('issued_at', 0)),
                                "plan_info":plan_info,
                                "order_subscription":order_subscription.id
                            }

                            template = get_template('pdf/invoice.html')
                            html = template.render(result).encode('latin-1', 'replace').decode('latin-1')
                            
                            destination = os.path.join(settings.MEDIA_ROOT, 'pdf_reports/')
                            os.makedirs(destination, exist_ok=True)
                            
                            pdf_path = os.path.join(destination, f"{order_info.user.id}_invoice.pdf")
                            with open(pdf_path, "w+b") as file:
                                pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), dest=file)

                            # Send Invoice Email
                            html_message = loader.render_to_string('invoice.html', {
                                'username': f"{order_info.first_name} {order_info.last_name}",
                                "plan_info":plan_info,
                                'order_info': order_info,
                                "order_subscription":order_subscription.id
                            })
                            email = EmailMessage('Subscription Invoice', html_message, settings.EMAIL_HOST_USER, [order_info.email])
                            email.attach_file(pdf_path)
                            email.content_subtype = "html"
                            email.send()

        # --- STATUS EVENT HANDLING MAPPING ---
        elif event in ['subscription.cancelled', 'subscription.paused', 'subscription.resumed', 'subscription.completed']:
            status_mapping = {
                'subscription.cancelled': OrderStatus.Cancelled,
                'subscription.paused': OrderStatus.Paused,
                'subscription.resumed': OrderStatus.Active,
                'subscription.completed': OrderStatus.Expired,
            }
            
            OrderSubscriptionPayments.objects.create(
                order=order_info,
                response=data,
                status=event,
                isPaid=False
            )

            if order_info:
                order_info.subscription_status = status_mapping[event]
                if event == 'subscription.resumed':
                    if next_due_date: order_info.next_due = next_due_date
                    if end_date_val: order_info.end_date = end_date_val
                order_info.save()

        # except Exception as exc:
        #     # Logs the exact line number and problem without failing entirely
        #     logger.error(f"Error executing webhook event logic ({event}): {str(exc)}", exc_info=True)
        #     # We still return a 200/Success to Razorpay so it doesn't queue duplicate retry requests
        #     return success_response(message="Handled with internal log errors", data=[], status_code=status.HTTP_200_OK)

        return success_response(message="Success", data=[], status_code=status.HTTP_200_OK)