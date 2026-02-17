from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from subscription.serializers import *
from subscription.models import *
from courses.models import *
from subscription.renderers import SubscriptionRenderer
from rest_framework.permissions import IsAuthenticated
from mini_lms.permissions import RoleOrPermissionCheck
from mini_lms.utils import *
from rest_framework.exceptions import NotFound
from mini_lms.pagination import CustomPageNumberPagination
from rest_framework import filters
import os
from django.conf import settings
from google.cloud import storage
client = settings.GS_CREDENTIALS
import pandas as pd
import tempfile
import re
import time
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import get_template

class GetSettingView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "manage_setting",
                            [SuperAdmin]
                        )]
    def get(self, request, cid=None):
        setting = Settings.objects.all().first()
        if setting is None:
            return success_response(message="Success", data={}, status_code=status.HTTP_200_OK)
        serializer = SettingSerializer(setting)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class UpdateSettingView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "manage_setting",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = UpdateSettingSerializer(data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Setting Updated Successfully", data=SettingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    



class SubscriptionPlanListingView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "subscription_plan_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['plan_name']
    ordering_fields = ['plan_name', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        
        plans = SubscriptionPlans.objects.filter(plan_for = PlanFor.Students)
        
        search_filter = filters.SearchFilter()
        plans = search_filter.filter_queryset(request, plans, self)

        ordering_filter = filters.OrderingFilter()
        plans = ordering_filter.filter_queryset(request, plans, self)

        if not plans.ordered:
            plans = plans.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(plans, request, view=self)
        serializer = SubscriptionPlanDetailSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class SubscriptionPlanDetailView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "subscription_plan_listing",
                            [SuperAdmin]
                        )]
    def get(self, request, cid=None):
        topic = SubscriptionPlans.objects.filter(id=cid, plan_for = PlanFor.Students).first()
        if topic is None:
            raise NotFound("Invalid Plan ID!")
        
        serializer = SubscriptionPlanDetailSerializer(topic)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
        

class CreateSubscriptionPlanView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_subscription_plan",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateSubscriptionPlanSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Plan Created Successfully", data=SubscriptionPlanDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class EditSubscriptionPlanView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_subscription_plan",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        plan = SubscriptionPlans.objects.filter(id=cid).first()
        if plan is None:
            raise NotFound("Invalid Plan ID!")
        
        serializer = EditSubscriptionPlanSerializer(plan, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Plan Updated Successfully", data=SubscriptionPlanDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateSubscriptionPlanStatusView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_subscription_plan",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        plan = SubscriptionPlans.objects.filter(id=cid).first()
        if plan is None:
            raise NotFound("Invalid Plan ID!")
        
        serializer = ChangeSubscriptionPlanStatusSerializer(plan, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Plan Status Updated Successfully", data=SubscriptionPlanDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteSubscriptionPlanView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_subscription_plan",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = SubscriptionPlans.objects.get(id = cid)
            course.delete()
            return success_response(message="Plan Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except SubscriptionPlans.DoesNotExist:
            return error_response(message="Plan not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        


class TrailUserListingView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "subscription_plan_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name','last_name',"email"]
    ordering_fields = ['first_name', 'created_at', 'id', 'last_name',"email"] 
    def get(self, request, format=None):
        
        plans = Order.objects.filter(trail_mode = True, subscription_status__in = [OrderStatus.Active , OrderStatus.Expired],corporate__isnull=True, user__isnull=False)
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id = course_id.split(',')
            plans = plans.filter(usercourses__course_id__in =course_id)

        category_id = request.query_params.get('category')
        if category_id:
            category_id = category_id.split(',')
            plans = plans.filter(user__category__in =category_id)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            plans = plans.filter(user__student_type__in =student_type)

        subscription_status = request.query_params.get('subscription_status')
        if subscription_status:
            plans = plans.filter(subscription_status = subscription_status)

        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'user__reference_id__icontains': term})
                
                plans = plans.filter(q_objects)

        country = request.query_params.get('country')
        if country:
            plans = plans.filter(country = country)

        state = request.query_params.get('state')
        if state:
            plans = plans.filter(state = state)

        city = request.query_params.get('city')
        if city:
            plans = plans.filter(city = city)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                plans = plans.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                plans = plans.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")


        search_filter = filters.SearchFilter()
        plans = search_filter.filter_queryset(request, plans, self)

        ordering_filter = filters.OrderingFilter()
        plans = ordering_filter.filter_queryset(request, plans, self)

        if not plans.ordered:
            plans = plans.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(plans, request, view=self)
        serializer = OrderDetailAdminSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class ExportPDFTrailUserListingView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "subscription_payment_listing",
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        plans = Order.objects.filter(trail_mode = True, subscription_status__in = [OrderStatus.Active , OrderStatus.Expired],corporate__isnull=True, user__isnull=False)
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id = course_id.split(',')
            plans = plans.filter(usercourses__course_id__in =course_id)

        category_id = request.query_params.get('category')
        if category_id:
            category_id = category_id.split(',')
            plans = plans.filter(user__category__in =category_id)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            plans = plans.filter(user__student_type__in =student_type)

        subscription_status = request.query_params.get('subscription_status')
        if subscription_status:
            plans = plans.filter(subscription_status = subscription_status)


        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'user__reference_id__icontains': term})
                
                plans = plans.filter(q_objects)


        country = request.query_params.get('country')
        if country:
            plans = plans.filter(country = country)

        state = request.query_params.get('state')
        if state:
            plans = plans.filter(state = state)

        city = request.query_params.get('city')
        if city:
            plans = plans.filter(city = city)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                plans = plans.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                plans = plans.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")


        search_filter = filters.SearchFilter()
        plans = search_filter.filter_queryset(request, plans, self)

        ordering_filter = filters.OrderingFilter()
        plans = ordering_filter.filter_queryset(request, plans, self)

        if not plans.ordered:
            plans = plans.order_by('-id')


        serializer = OrderDetailAdminSerializer(plans, many=True)
        
        data = {
            "order_data":serializer.data
        }


        template = get_template('pdf/trail_user_report.html')
        html  = template.render(data)
        # Use tempfile to create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "trail_user_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.pdf"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            # Ensure the temporary file is deleted from the server's disk
            os.remove(pdf_path)
    


class ExportExcelTrailUserListingView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "subscription_payment_listing",
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        plans = Order.objects.filter(trail_mode = True, subscription_status__in = [OrderStatus.Active , OrderStatus.Expired],corporate__isnull=True, user__isnull=False)
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id = course_id.split(',')
            plans = plans.filter(usercourses__course_id__in =course_id)

        category_id = request.query_params.get('category')
        if category_id:
            category_id = category_id.split(',')
            plans = plans.filter(user__category__in =category_id)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            plans = plans.filter(user__student_type__in =student_type)

        subscription_status = request.query_params.get('subscription_status')
        if subscription_status:
            plans = plans.filter(subscription_status = subscription_status)

        
        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'user__reference_id__icontains': term})
                
                plans = plans.filter(q_objects)


        country = request.query_params.get('country')
        if country:
            plans = plans.filter(country = country)

        state = request.query_params.get('state')
        if state:
            plans = plans.filter(state = state)

        city = request.query_params.get('city')
        if city:
            plans = plans.filter(city = city)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                plans = plans.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                plans = plans.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")


        search_filter = filters.SearchFilter()
        plans = search_filter.filter_queryset(request, plans, self)

        ordering_filter = filters.OrderingFilter()
        plans = ordering_filter.filter_queryset(request, plans, self)

        if not plans.ordered:
            plans = plans.order_by('-id')


        serializer = OrderDetailAdminSerializer(plans, many=True)
        
        lis = []
        
        lis.append({
                "first_name":"Free Trial Report",
                "last_name":'',
                "email":'',
                "phone":'',
                "category":"",
                "student_type":"",
                "reference_id":"",
                "billing_address":'',
                "state":'',
                "city":'',
                "country":'',
                "start_date":'',
                "end_date":'',
                "subscription_status":'',
                "ordered_courses":'',
                "created_at":'',
            })
        
        lis.append({
                "first_name":"",
                "last_name":'',
                "email":'',
                "phone":'',
                "category":"",
                "student_type":"",
                "reference_id":"",
                "billing_address":'',
                "state":'',
                "city":'',
                "country":'',
                "start_date":'',
                "end_date":'',
                "subscription_status":'',
                "ordered_courses":'',
                "created_at":'',
            })
        
        lis.append({
                "first_name":"Start Date",
                "last_name":start_date,
                "email":'',
                "phone":'',
                "category":"",
                "student_type":"",
                "reference_id":"",
                "billing_address":'End Date',
                "state":end_date,
                "city":'',
                "country":'',
                "start_date":'',
                "end_date":'',
                "subscription_status":'',
                "ordered_courses":'',
                "created_at":'',
            })
        
        lis.append({
                "first_name":"",
                "last_name":'',
                "email":'',
                "phone":'',
                "category":"",
                "student_type":"",
                "reference_id":"",
                "billing_address":'',
                "state":'',
                "city":'',
                "country":'',
                "start_date":'',
                "end_date":'',
                "subscription_status":'',
                "ordered_courses":'',
                "created_at":'',
            })
        
        lis.append({
                "first_name":"First Name",
                "last_name":'Last Name',
                "email":'Email',
                "phone":'Phone',
                "category":"Student Category",
                "student_type":"Student Type",
                "reference_id":"Student Reference ID",
                "billing_address":'Billing Address',
                "state":'State',
                "city":'City',
                "country":'Country',
                "start_date":'Start Date',
                "end_date":'End Date',
                "subscription_status":'Subscription Status',
                "ordered_courses":'Courses List',
                "created_at":'Created At',
            })
        for order in serializer.data:

            course = [item['name'] for item in order['ordered_courses']]
            course_list = ", ".join(course)

            lis.append({
                "first_name":order['first_name'],
                "last_name":order['last_name'],
                "email":order['email'],
                "phone":order['phone'],
                "category":order['user_detail']['category'],
                "student_type":order['user_detail']['student_type'],
                "reference_id":order['user_detail']['reference_id'],
                "billing_address":order['billing_address'],
                "state":order['state'],
                "city":order['city'],
                "country":order['country'],
                "start_date":order['start_date'],
                "end_date":order['end_date'],
                "subscription_status":OrderStatus(order['subscription_status']).label,
                "ordered_courses":course_list,
                "created_at":order['created_at'],
            })

        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            # GCS file naming logic
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "trail_user_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            # Upload the temporary file to GCS
            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            # Ensure the temporary file is deleted
            os.remove(pdf_path)


class RegisterTrailUserView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "register_for_trial",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = RegisterForTrailSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Registration Done! Account detail is shared on email", data={"id":user.id}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)