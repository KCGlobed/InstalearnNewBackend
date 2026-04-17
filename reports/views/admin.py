from rest_framework import status
from rest_framework.views import APIView
from reports.serializers import *
from reports.models import *
from subscription.models import *
from reports.renderers import ReportsRenderer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from mini_lms.utils import *
from mini_lms.roles import *
from rest_framework.exceptions import ValidationError , ValidationError
from mini_lms.permissions import RoleOrPermissionCheck
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import get_template
import time
import calendar
from django.conf import settings
import tempfile
import os
import json
import re
from google.cloud import storage
from google.oauth2 import service_account
info = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
credentials = service_account.Credentials.from_service_account_info(info)
client = storage.Client(credentials=credentials, project=credentials.project_id)
import pandas as pd
import tempfile
import re
from mini_lms.permissions import RoleOrPermissionCheck
from mini_lms.pagination import CustomPageNumberPagination
from rest_framework import filters
from dateutil.relativedelta import relativedelta
from datetime import datetime,timezone, timedelta



class GetUserReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_user_reports_pdf",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name',"last_name","email","is_active","created_at"]
    ordering_fields = ["id",'first_name',"last_name","email","is_active","created_at"] 
    def get(self, request, user_type=None):
        
        user_role = get_url_role(user_type)
        if user_role is None:
            raise ValidationError("Invalid User Type!")
        
        topics = User.objects.only("id",'first_name',"last_name","email","is_active","created_at").filter(role = user_role)
        
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
        topics = search_filter.filter_queryset(request, topics, self)

        ordering_filter = filters.OrderingFilter()
        topics = ordering_filter.filter_queryset(request, topics, self)

        if not topics.ordered:
            topics = topics.order_by('-id')

        serializer = StaffUserListSerializer(topics, many=True)

        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/user_list_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "user_list_report"
            gcs_folder_name = "media/mini_lms/reports"
            gcs_file_name = f"{gcs_folder_name}/{user_type}_{report_name}_{timestamp}.pdf"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)
    


class GetUserReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_user_reports_excel",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name',"last_name","email","is_active","created_at","category"]
    ordering_fields = ["id",'first_name',"last_name","email","is_active","created_at","category"] 
    def get(self, request, user_type=None):
        
        user_role = get_url_role(user_type)
        if user_role is None:
            raise ValidationError("Invalid User Type!")
        
        topics = User.objects.only("id",'first_name',"last_name","email","is_active","created_at").filter(role = user_role)
        
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
        topics = search_filter.filter_queryset(request, topics, self)

        ordering_filter = filters.OrderingFilter()
        topics = ordering_filter.filter_queryset(request, topics, self)

        if not topics.ordered:
            topics = topics.order_by('-id')

        serializer = StaffUserListSerializer(topics, many=True)
        
        lis = []
        
        lis.append({
                "name":"User List Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":'',
                "courses":"",
                "status":"",
                "date":""
            })

        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":'',
                "courses":"",
                "status":"",
                "date":""
            })
        
        
        lis.append({
                "name":"First Name",
                "email":'Last Name',
                "subject":'Email',
                "Chapter":'Role',
                "Topic":'Is Active',
                "total_videos":'Registration Date',
                "total_watched_videos":'',
                "total_time_spend":'',
                "courses":"",
                "status":"",
                "date":""
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['first_name'],
                "email":order_info['last_name'],
                "subject":order_info['email'],
                "Chapter":user_role_report(order_info['role']),
                "Topic":order_info['is_active'],
                "total_videos":order_info['created_at'],
                "total_watched_videos":"",
                "total_time_spend":"",
                "courses":"",
                "status":"",
                "date":""
            })
            
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "user_list_report"
            gcs_folder_name = "media/mini_lms/reports"
            gcs_file_name = f"{gcs_folder_name}/{user_type}_{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)




class GetRolePermissionPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_role_permission_reports_pdf",
                            [SuperAdmin]
                        )]
    def get(self, request, user_role=None):
        
        role_class = get_role(user_role)
        if role_class is None:
            raise ValidationError(f"Role '{user_role}' not found.")

        permissions = RolePermissions.objects.filter(role = user_role).order_by("id")
        serializer = RolePermissionSerializer(permissions,many=True)
    
        data = {
                    "user_data":serializer.data,
                    "user_role":user_role
                }
        
        template = get_template('pdf/permission_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "permission_report"
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
            os.remove(pdf_path)
    


class GetRolePermissionExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_role_permission_reports_excel",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, user_role=None):
        
        role_class = get_role(user_role)
        if role_class is None:
            raise ValidationError(f"Role '{user_role}' not found.")

        permissions = RolePermissions.objects.filter(role = user_role).order_by("id")
        serializer = RolePermissionSerializer(permissions,many=True)
    
        lis = []
        
        lis.append({
                "name":"Permission Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        lis.append({
                "name":"Role Name",
                "email":user_role,
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Permission Name",
                "email":'Permission Code',
                "subject":'Is Active?',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "email":order_info['code'],
                "subject":order_info['status'],
                "Chapter":"",
                "Topic":"",
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "permission_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)



class GetAdminDashboardCountersView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):

        now = timezone.now()
        current_year = now.year
        current_month = now.month


        user_counts = User.objects.aggregate(
            total_students=Count('id', filter=Q(role=User.Student)),
            total_corporate_admin=Count('id', filter=Q(role=User.CorporateAdmin)),
            total_atp_admins=Count('id', filter=Q(role=User.ATPAdmin)),
            total_university_admins=Count('id', filter=Q(role=User.UniversityAdmin)),
            new_students_current_month=Count('id', filter=Q(
                role=User.Student,
                date_joined__year=current_year,
                date_joined__month=current_month
            ))
        )

        subscription_counts = Order.objects.aggregate(
            total_active_subscriptions=Count('id', filter=Q(subscription_status=OrderStatus.Active)),

            expiring_subscription_current_month=Count('id', filter=Q(
                subscription_status=OrderStatus.Active,
                end_date__year=current_year,
                end_date__month=current_month
            ))
        )
        
        total_duration = Videos.objects.filter(is_completed=True).aggregate(
            total_duration=Sum('video_duration')
        )['total_duration']
        
        info = {
            "total_students": user_counts['total_students'],
            "total_corporate_admin": user_counts['total_corporate_admin'],
            "total_atp_admins": user_counts['total_atp_admins'],
            "total_university_admins": user_counts['total_university_admins'],
            "total_duration": total_duration,
            "total_active_subscriptions" : subscription_counts['total_active_subscriptions'],
            "expiring_subscription_current_month" : subscription_counts['expiring_subscription_current_month'],
            "new_students_current_month":user_counts['new_students_current_month']
        }

        return success_response(message="", data=info, status_code=status.HTTP_200_OK)
    

class GetAdminDashboardSourceStudentsView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):

        user_counts = User.objects.aggregate(
            atp_students=Count('id', filter=Q(role=User.Student , category = "ATP")),
            corporate_students=Count('id', filter=Q(role=User.Student , category = "CORPORATE")),
            insitution_students=Count('id', filter=Q(role=User.Student , category = "INSTITUTION")),
            gov_students=Count('id', filter=Q(role=User.Student , category = "GOV")),
            direct_students=Count('id', filter=Q(role=User.Student , category = "DIRECT")),
            others_students=Count('id', filter=Q(role=User.Student , category = "OTHERS")),
        )
        
        
        info = {
            "atp_students": user_counts['atp_students'],
            "corporate_students": user_counts['corporate_students'],
            "insitution_students": user_counts['insitution_students'],
            "gov_students": user_counts['gov_students'],
            "direct_students": user_counts['direct_students'],
            "others_students": user_counts['others_students'],
        }

        return success_response(message="", data=info, status_code=status.HTTP_200_OK)
    

class GetAdminDashboardStudentGraphsView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, interval=None):

        if interval == "year":
            current_year = timezone.now().year
    
            date_list = []
            for i in range(5):
                target_year = current_year - (4 - i) 
                start_date = datetime(target_year, 1, 1)
                end_date = datetime(target_year, 12, 31)
                
                date_list.append({
                    'start_date': start_date.strftime("%Y-%m-%d"),
                    "end_date":end_date.strftime("%Y-%m-%d"),
                    'total_student_registered': User.objects.filter(
                                                role=User.Student,
                                            date_joined__range=(start_date, end_date)).count()
                })


        elif interval == "month":
            now = timezone.now().date()
            current_month_start = now.replace(day=1)
            
            date_list = []
            for i in range(12):
                month_start = current_month_start - relativedelta(months=i)
                
                if i == 0:
                    month_end = now
                else:
                    next_month_start = current_month_start - relativedelta(months=i-1)
                    month_end = next_month_start - timedelta(days=1)
                date_list.append({
                    'start_date': month_start.strftime("%Y-%m-%d"),
                    "end_date":month_end.strftime("%Y-%m-%d"),
                    'total_student_registered': User.objects.filter(
                                                role=User.Student,
                                            date_joined__range=(month_start, month_end)).count()
                })

        elif interval == "week":
            now = datetime.now()
            date_list = []
            for week in range(4):
                end_date = now - timedelta(weeks=week)
                start_date = end_date - timedelta(days=6)

                date_list.append({
                    'start_date': start_date.strftime("%Y-%m-%d"),
                    "end_date":end_date.strftime("%Y-%m-%d"),
                    'total_student_registered': User.objects.filter(
                                                role=User.Student,
                                            date_joined__range=(start_date, end_date)).count()
                })
        else:
            today = timezone.now().date()
            date_list = []
            for i in range(7):
                past_date = today - timedelta(days=i)
                date_list.append({
                    "start_date":past_date.strftime("%Y-%m-%d"),
                    "end_date":None,
                    'total_student_registered': User.objects.filter(
                                                role=User.Student,
                                            date_joined=past_date).count()
                }) 
        
        return success_response(message="", data=date_list, status_code=status.HTTP_200_OK)
    

class GetAdminDashboardPracticeTestGraphsView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, interval=None):

        if interval == "year":
            current_year = timezone.now().year
    
            date_list = []
            for i in range(5):
                target_year = current_year - (4 - i) 
                start_date = datetime(target_year, 1, 1)
                end_date = datetime(target_year, 12, 31)
                
                date_list.append({
                    'start_date': start_date.strftime("%Y-%m-%d"),
                    "end_date":end_date.strftime("%Y-%m-%d"),
                    'total_practice_test_created': PracticeTests.objects.filter(
                                                practice_retake__isnull=True,
                                            created_at__range=(start_date, end_date)).count()
                })


        elif interval == "month":
            now = timezone.now().date()
            current_month_start = now.replace(day=1)
            
            date_list = []
            for i in range(12):
                month_start = current_month_start - relativedelta(months=i)
                
                if i == 0:
                    month_end = now
                else:
                    next_month_start = current_month_start - relativedelta(months=i-1)
                    month_end = next_month_start - timedelta(days=1)
                date_list.append({
                    'start_date': month_start.strftime("%Y-%m-%d"),
                    "end_date":month_end.strftime("%Y-%m-%d"),
                    'total_practice_test_created': PracticeTests.objects.filter(
                                                practice_retake__isnull=True,
                                            created_at__range=(month_start, month_end)).count()
                })

        elif interval == "week":
            now = datetime.now()
            date_list = []
            for week in range(4):
                end_date = now - timedelta(weeks=week)
                start_date = end_date - timedelta(days=6)

                date_list.append({
                    'start_date': start_date.strftime("%Y-%m-%d"),
                    "end_date":end_date.strftime("%Y-%m-%d"),
                    'total_practice_test_created': PracticeTests.objects.filter(
                                                practice_retake__isnull=True,
                                            created_at__range=(start_date, end_date)).count()
                })
        else:
            today = timezone.now().date()
            date_list = []
            for i in range(7):
                past_date = today - timedelta(days=i)
                date_list.append({
                    "start_date":past_date.strftime("%Y-%m-%d"),
                    "end_date":None,
                    'total_practice_test_created': PracticeTests.objects.filter(
                                                practice_retake__isnull=True,
                                            created_at__date=past_date).count()
                }) 
        
        return success_response(message="", data=date_list, status_code=status.HTTP_200_OK)
    


class GetAdminDashboardMockTestGraphsView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, interval=None):

        if interval == "year":
            current_year = timezone.now().year
    
            date_list = []
            for i in range(5):
                target_year = current_year - (4 - i) 
                start_date = datetime(target_year, 1, 1)
                end_date = datetime(target_year, 12, 31)
                
                date_list.append({
                    'start_date': start_date.strftime("%Y-%m-%d"),
                    "end_date":end_date.strftime("%Y-%m-%d"),
                    'total_practice_test_created': MockTests.objects.filter(
                                            created_at__range=(start_date, end_date)).count()
                })


        elif interval == "month":
            now = timezone.now().date()
            current_month_start = now.replace(day=1)
            
            date_list = []
            for i in range(12):
                month_start = current_month_start - relativedelta(months=i)
                
                if i == 0:
                    month_end = now
                else:
                    next_month_start = current_month_start - relativedelta(months=i-1)
                    month_end = next_month_start - timedelta(days=1)
                date_list.append({
                    'start_date': month_start.strftime("%Y-%m-%d"),
                    "end_date":month_end.strftime("%Y-%m-%d"),
                    'total_practice_test_created': MockTests.objects.filter(
                                            created_at__range=(month_start, month_end)).count()
                })

        elif interval == "week":
            now = datetime.now()
            date_list = []
            for week in range(4):
                end_date = now - timedelta(weeks=week)
                start_date = end_date - timedelta(days=6)

                date_list.append({
                    'start_date': start_date.strftime("%Y-%m-%d"),
                    "end_date":end_date.strftime("%Y-%m-%d"),
                    'total_practice_test_created': MockTests.objects.filter(
                                            created_at__range=(start_date, end_date)).count()
                })
        else:
            today = timezone.now().date()
            date_list = []
            for i in range(7):
                past_date = today - timedelta(days=i)
                date_list.append({
                    "start_date":past_date.strftime("%Y-%m-%d"),
                    "end_date":None,
                    'total_practice_test_created': MockTests.objects.filter(created_at__date=past_date).count()
                }) 
        
        return success_response(message="", data=date_list, status_code=status.HTTP_200_OK)
    



class GetGlossaryReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_glossary_reports_pdf",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, tid=None):
        
        topics = Glossary.objects.only("id","name","alphabet","status","created_at").filter(subject_id = tid).order_by('name')
        serializer = GlossaryListSerializer(topics, many=True)

        data = {
                    "user_data":serializer.data,
                    "subject_info":Subjects.objects.filter(id = tid).first()
                }
        
        template = get_template('pdf/glossary_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "glossary_report"
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
            os.remove(pdf_path)
    


class GetGlossaryReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_glossary_reports_excel",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, tid=None):
        
        topics = Glossary.objects.only("id","name","alphabet","status","created_at").filter(subject_id = tid).order_by('name')
        serializer = GlossaryListSerializer(topics, many=True)

        subject_info = Subjects.objects.filter(id = tid).first()

        lis = []
        
        lis.append({
                "name":"Glossary Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        lis.append({
                "name":"Subject Name",
                "email":subject_info.name,
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Alphabet",
                "email":'Name',
                "subject":'Is Active?',
                "Chapter":'Created At',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['alphabet'].upper(),
                "email":order_info['name'],
                "subject":order_info['status'],
                "Chapter":order_info['created_at'],
                "Topic":"",
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "glossary_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)



class GetSubscriptionPlanReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_subscription_plan_reports_pdf",
                            [SuperAdmin]
                        )]
    def get(self, request):
        
        topics = SubscriptionPlans.objects.all().order_by('-id')
        serializer = SubscriptionPlansSerializer(topics, many=True)

        data = {
                    "user_data":serializer.data
                }
        
        template = get_template('pdf/subscription_plan_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "subscription_plan_report"
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
            os.remove(pdf_path)
    


class GetSubscriptionPlanReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_subscription_plan_reports_excel",
                            [SuperAdmin]
                        )]
    def get(self, request):
        
        topics = SubscriptionPlans.objects.all().order_by('-id')
        serializer = SubscriptionPlansSerializer(topics, many=True)

        lis = []
        
        lis.append({
                "name":"Subscription Plan Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Plan Name",
                "email":'Monthly Amount',
                "subject":'Amount',
                "Chapter":'Plan Type',
                "Topic":'Currency',
                "total_videos":'Is Active?',
                "total_watched_videos":'Created At',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['plan_name'],
                "email":order_info['monthly_amount'],
                "subject":order_info['amount'],
                "Chapter":plan_type(order_info['plan_type']),
                "Topic":currency_type(order_info['currency']),
                "total_videos":order_info['status'],
                "total_watched_videos":order_info['created_at'],
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "subscription_plan_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)



class GetTagsReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_tag_reports_pdf",
                            [SuperAdmin]
                        )]
    def get(self, request):
        
        topics = TagDetail.objects.all().order_by('-id')
        serializer = TagDetailSerializer(topics, many=True)

        data = {
                    "user_data":serializer.data
                }
        
        template = get_template('pdf/tags_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "tags_report"
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
            os.remove(pdf_path)
    


class GetTagsReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_tag_reports_excel",
                            [SuperAdmin]
                        )]
    def get(self, request):
        
        topics = TagDetail.objects.all().order_by('-id')
        serializer = TagDetailSerializer(topics, many=True)

        lis = []
        
        lis.append({
                "name":"Tags Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "email":'Is Active?',
                "subject":'Created At',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "email":order_info['status'],
                "subject":order_info['created_at'],
                "Chapter":"",
                "Topic":"",
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "tags_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)




class GetBatchesReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_batches_reports_pdf",
                            [SuperAdmin]
                        )]
    def get(self, request):
        
        topics = BatchDetail.objects.all().order_by('-id')
        serializer = BatchDetailSerializer(topics, many=True)

        data = {
                    "user_data":serializer.data
                }
        
        template = get_template('pdf/batch_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "batch_report"
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
            os.remove(pdf_path)
    


class GetBatchesReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_batches_reports_excel",
                            [SuperAdmin]
                        )]
    def get(self, request):
        
        topics = BatchDetail.objects.all().order_by('-id')
        serializer = BatchDetailSerializer(topics, many=True)

        lis = []
        
        lis.append({
                "name":"Batches Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Batch Name",
                "email":'Start Date',
                "subject":'Periods',
                "Chapter":'Is Active?',
                "Topic":'Created At',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "email":order_info['start_date'],
                "subject":order_info['period'],
                "Chapter":order_info['status'],
                "Topic":order_info['created_at'],
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "batches_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)



class GetInstitutionReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_institute_reports_pdf",
                            [SuperAdmin]
                        )]
    def get(self, request):
        
        topics = Institution.objects.all().order_by('-id')
        serializer = institutionSerializer(topics, many=True)

        data = {
                    "user_data":serializer.data
                }
        
        template = get_template('pdf/institution_report.html')

        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "institution_report"
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
            os.remove(pdf_path)
    


class GetInstitutionReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_institute_reports_excel",
                            [SuperAdmin]
                        )]
    def get(self, request):
        
        topics = Institution.objects.all().order_by('-id')
        serializer = institutionSerializer(topics, many=True)

        lis = []
        
        lis.append({
                "name":"Institution Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "email":'Collaboration Type',
                "subject":'Location',
                "Chapter":'Min. Student Committed',
                "Topic":'Student Category',
                "total_videos":'Mode',
                "total_watched_videos":'Is Active?',
                "total_time_spend":'Created At'
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "email":order_info['collaboration_type'],
                "subject":order_info['location'],
                "Chapter":order_info['min_students_committed'],
                "Topic":order_info['category_student'],
                "total_videos":order_info['mode'],
                "total_watched_videos":order_info['status'],
                "total_time_spend":order_info['created_at']
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "institution_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)



class GetDeletedTopicsView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        topics = Topics.deleted_objects.all()
        topics = topics.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = DeletedTopicsSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class GetDeletedTopicHistoryView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = Topics.deleted_objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid Topic ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = DeletedTopicsHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    
class RestoreDeletedTopicsView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        topic = Topics.deleted_objects.filter(id=cid).first()
        if topic is None:
            raise ValidationError("Invalid Topic ID!")
        
        serializer = RestoreTopicsSerializer(topic, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Topic Restored Successfully", data={"topic_id":cid}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetDeletedTopicsReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        topics = Topics.deleted_objects.all()
        topics = topics.order_by('-id')

        serializer = DeletedTopicsSerializer(topics, many=True)
    
        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/deleted/deleted_topic_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_topic_report"
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
            os.remove(pdf_path)
    


class GetDeletedTopicsReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        topics = Topics.deleted_objects.all()
        topics = topics.order_by('-id')

        serializer = DeletedTopicsSerializer(topics, many=True)
        
        lis = []
        
        lis.append({
                "name":"Deleted Topics Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "email":'Deleted At',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "email":order_info['deleted_at'],
                "subject":"",
                "Chapter":"",
                "Topic":"",
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_topic_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)




class GetDeletedChaptersView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        topics = Chapters.deleted_objects.all()
        topics = topics.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = DeletedChaptersSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class GetDeletedChaptersHistoryView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = Chapters.deleted_objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid Chapter ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = DeletedChaptersHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    
class RestoreDeletedChaptersView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        topic = Chapters.deleted_objects.filter(id=cid).first()
        if topic is None:
            raise ValidationError("Invalid Chapter ID!")
        
        serializer = RestoreChaptersSerializer(topic, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Chapter Restored Successfully", data={"chapter_id":cid}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetDeletedChaptersReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        topics = Chapters.deleted_objects.all()
        topics = topics.order_by('-id')

        serializer = DeletedChaptersSerializer(topics, many=True)
    
        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/deleted/deleted_chapter_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_chapter_report"
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
            os.remove(pdf_path)
    


class GetDeletedChaptersReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        topics = Chapters.deleted_objects.all()
        topics = topics.order_by('-id')

        serializer = DeletedChaptersSerializer(topics, many=True)
        
        lis = []
        
        lis.append({
                "name":"Deleted Chapters Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "email":'Deleted At',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "email":order_info['deleted_at'],
                "subject":"",
                "Chapter":"",
                "Topic":"",
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_chapters_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)



class GetDeletedSubjectsView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        topics = Subjects.deleted_objects.all()
        topics = topics.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = DeletedSubjectsSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class GetDeletedSubjectsHistoryView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = Subjects.deleted_objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid Subject ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = DeletedSubjectsHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    
class RestoreDeletedSubjectsView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        topic = Subjects.deleted_objects.filter(id=cid).first()
        if topic is None:
            raise ValidationError("Invalid Subject ID!")
        
        serializer = RestoreSubjectsSerializer(topic, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Subject Restored Successfully", data={"subject_id":cid}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetDeletedSubjectsReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        topics = Subjects.deleted_objects.all()
        topics = topics.order_by('-id')

        serializer = DeletedSubjectsSerializer(topics, many=True)
    
        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/deleted/deleted_subject_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_subject_report"
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
            os.remove(pdf_path)
    


class GetDeletedSubjectsReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        topics = Subjects.deleted_objects.all()
        topics = topics.order_by('-id')

        serializer = DeletedSubjectsSerializer(topics, many=True)
        
        lis = []
        
        lis.append({
                "name":"Deleted Subjects Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "email":'Deleted At',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "email":order_info['deleted_at'],
                "subject":"",
                "Chapter":"",
                "Topic":"",
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_subjects_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)




class GetDeletedCourseView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        topics = Course.deleted_objects.all()
        topics = topics.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = DeletedCourseSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class GetDeletedCourseHistoryView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = Course.deleted_objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid Course ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = DeletedCourseHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    
class RestoreDeletedCourseView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        topic = Course.deleted_objects.filter(id=cid).first()
        if topic is None:
            raise ValidationError("Invalid Course ID!")
        
        serializer = RestoreCourseSerializer(topic, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Course Restored Successfully", data={"course_id":cid}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetDeletedCourseReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        topics = Course.deleted_objects.all()
        topics = topics.order_by('-id')

        serializer = DeletedCourseSerializer(topics, many=True)
    
        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/deleted/deleted_course_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_course_report"
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
            os.remove(pdf_path)
    


class GetDeletedCourseReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        topics = Course.deleted_objects.all()
        topics = topics.order_by('-id')

        serializer = DeletedCourseSerializer(topics, many=True)
        
        lis = []
        
        lis.append({
                "name":"Deleted Course Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "email":'Deleted At',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "email":order_info['deleted_at'],
                "subject":"",
                "Chapter":"",
                "Topic":"",
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_course_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)



class GetDeletedEbookView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        topics = ChapterBooks.deleted_objects.all()
        topics = topics.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = DeletedEbookSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class GetDeletedEbookHistoryView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = ChapterBooks.deleted_objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid EBook ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = DeletedEbooksHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    
class RestoreDeletedEbookView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        topic = ChapterBooks.deleted_objects.filter(id=cid).first()
        if topic is None:
            raise ValidationError("Invalid Ebook ID!")
        
        serializer = RestoreEbookSerializer(topic, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Ebook Restored Successfully", data={"ebook_id":cid}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetDeletedEbookReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        topics = ChapterBooks.deleted_objects.all()
        topics = topics.order_by('-id')

        serializer = DeletedEbookSerializer(topics, many=True)
    
        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/deleted/deleted_ebook_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_ebook_report"
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
            os.remove(pdf_path)
    


class GetDeletedEbookReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        topics = ChapterBooks.deleted_objects.all()
        topics = topics.order_by('-id')

        serializer = DeletedEbookSerializer(topics, many=True)
        
        lis = []
        
        lis.append({
                "name":"Deleted Ebook Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "email":'Chapter Name',
                "subject":'Deleted At',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "email":order_info['chapter_detail']['name'],
                "subject":order_info['deleted_at'],
                "Chapter":"",
                "Topic":"",
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_ebook_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)



class GetDeletedVideoView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        topics = Videos.deleted_objects.all()
        topics = topics.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = DeletedVideoSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class GetDeletedVideoHistoryView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = Videos.deleted_objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid Video ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = DeletedVideoHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    

class RestoreDeletedVideoView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        topic = Videos.deleted_objects.filter(id=cid).first()
        if topic is None:
            raise ValidationError("Invalid Video ID!")
        
        serializer = RestoreVideoSerializer(topic, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Video Restored Successfully", data={"video_id":cid}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetDeletedVideoReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        topics = Videos.deleted_objects.all()
        topics = topics.order_by('-id')

        serializer = DeletedVideoSerializer(topics, many=True)
    
        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/deleted/deleted_video_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_video_report"
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
            os.remove(pdf_path)
    


class GetDeletedVideoReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        topics = Videos.deleted_objects.all()
        topics = topics.order_by('-id')

        serializer = DeletedVideoSerializer(topics, many=True)
        
        lis = []
        
        lis.append({
                "name":"Deleted Videos Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "email":'Deleted At',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "email":order_info['deleted_at'],
                "subject":"",
                "Chapter":"",
                "Topic":"",
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_videos_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)



class GetDeletedMCQView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        topics = TestQuestions.deleted_objects.filter(question_type = QuestionType.MCQ)
        topics = topics.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = DeletedTestQuestionsSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class GetDeletedMCQHistoryView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = TestQuestions.deleted_objects.filter(id = tid , question_type = QuestionType.MCQ).first()
        if topics is None:
            raise ValidationError("Invalid MCQ ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = DeletedTestQuestionsHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    

class RestoreDeletedMCQView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        topics = TestQuestions.deleted_objects.filter(id = cid , question_type = QuestionType.MCQ).first()
        if topics is None:
            raise ValidationError("Invalid MCQ ID")
        
        serializer = RestoreTestQuestionserializer(topics, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="MCQ Restored Successfully", data={"question_id":cid}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetDeletedMCQReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        topics = TestQuestions.deleted_objects.filter(question_type = QuestionType.MCQ)
        topics = topics.order_by('-id')

        serializer = DeletedTestQuestionsSerializer(topics, many=True)
    
        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/deleted/deleted_mcq_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_mcq_report"
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
            os.remove(pdf_path)
    


class GetDeletedMCQReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        topics = TestQuestions.deleted_objects.filter(question_type = QuestionType.MCQ)
        topics = topics.order_by('-id')

        serializer = DeletedTestQuestionsSerializer(topics, many=True)
        
        lis = []
        
        lis.append({
                "name":"Deleted MCQs Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "email":'Level',
                "subject":'Topic Name',
                "Chapter":'Deleted At',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['id_number'],
                "email":difficulty_level(order_info['level']),
                "subject":order_info['topic_detail']['name'],
                "Chapter":order_info['deleted_at'],
                "Topic":"",
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_mcq_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)




class GetDeletedSimulationView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        topics = TestQuestions.deleted_objects.filter(question_type = QuestionType.SIMULATION)
        topics = topics.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = DeletedSimulationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class GetDeletedSimulationHistoryView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = TestQuestions.deleted_objects.filter(id = tid , question_type = QuestionType.SIMULATION).first()
        if topics is None:
            raise ValidationError("Invalid Simulation ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = DeletedTestQuestionsHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    

class RestoreDeletedSimulationView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        topics = TestQuestions.deleted_objects.filter(id = cid , question_type = QuestionType.SIMULATION).first()
        if topics is None:
            raise ValidationError("Invalid Simulation ID")
        
        serializer = RestoreTestQuestionserializer(topics, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Simulation Restored Successfully", data={"question_id":cid}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetDeletedSimulationReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        topics = TestQuestions.deleted_objects.filter(question_type = QuestionType.SIMULATION)
        topics = topics.order_by('-id')

        serializer = DeletedSimulationSerializer(topics, many=True)
    
        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/deleted/deleted_simulation_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_simulation_report"
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
            os.remove(pdf_path)
    


class GetDeletedSimulationReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        topics = TestQuestions.deleted_objects.filter(question_type = QuestionType.SIMULATION)
        topics = topics.order_by('-id')

        serializer = DeletedSimulationSerializer(topics, many=True)
        
    
        lis = []
        
        lis.append({
                "name":"Deleted Simulations Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "email":'Level',
                "subject":'Simulation Type',
                "Chapter":'Chapter Name',
                "Topic":'Deleted At',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['id_number'],
                "email":difficulty_level(order_info['level']),
                "subject": simulation_type(order_info['simulation_type']),
                "Chapter":order_info['chapter_detail']['name'],
                "Topic":order_info['deleted_at'],
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_simulation_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)



class GetDeletedGlossaryView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        topics = Glossary.deleted_objects.all()
        topics = topics.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = DeletedGlossarySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class GetDeletedGlossaryHistoryView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = Glossary.deleted_objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid Glossary ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = DeletedGlossaryHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    
class RestoreDeletedGlossaryView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        topic = Glossary.deleted_objects.filter(id=cid).first()
        if topic is None:
            raise ValidationError("Invalid Ebook ID!")
        
        serializer = RestoreGlossarySerializer(topic, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Glossary Restored Successfully", data={"glossary_id":cid}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetDeletedGlossaryReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        topics = Glossary.deleted_objects.all()
        topics = topics.order_by('-id')

        serializer = DeletedGlossarySerializer(topics, many=True)
    
        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/deleted/deleted_glossary_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_glossary_report"
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
            os.remove(pdf_path)
    


class GetDeletedGlossaryReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        topics = Glossary.deleted_objects.all()
        topics = topics.order_by('-id')

        serializer = DeletedGlossarySerializer(topics, many=True)
        
        lis = []
        
        lis.append({
                "name":"Deleted Glossary Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "email":'Subject Name',
                "subject":'Deleted At',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "email":order_info['subject_detail']['name'],
                "subject":order_info['deleted_at'],
                "Chapter":"",
                "Topic":"",
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "deleted_glossary_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)


class GetAdminStudyPlanReportView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_study_plan_report_pdf",
                            [SuperAdmin]
                        )]
    def get(self, request, uid, sid):
        
        subject = CourseSubjects.objects.select_related("course", "subject").filter(id=sid).first()
        if subject is None:
            raise ValidationError("Invalid Subject ID")
        
        user = User.objects.get(id = uid)

        uncompleted_study_plans = StudyPlans.objects.filter(subject_id = sid, user_id = uid, is_complete=False).order_by("-id")
        uncompleted_study_plan = StudyPlansListingSerializer(uncompleted_study_plans, many=True)

        completed_study_plans = StudyPlans.objects.filter(subject_id = sid, user_id = uid, is_complete=True).order_by("-id")
        completed_study_plan = StudyPlansListingSerializer(completed_study_plans, many=True)
        
    
        data = {
                    "uncompleted_study_plan":uncompleted_study_plan.data,
                    "completed_study_plan":completed_study_plan.data
                }
        
        return success_response(
                message="Success",
                data=data,
                status_code=status.HTTP_200_OK
            )
        


class GetAdminStudyPlanReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_study_plan_report_pdf",
                            [SuperAdmin]
                        )]
    def get(self, request, uid, sid):
        
        subject = CourseSubjects.objects.select_related("course", "subject").filter(id=sid).first()
        if subject is None:
            raise ValidationError("Invalid Subject ID")
        
        user = User.objects.get(id = uid)

        uncompleted_study_plans = StudyPlans.objects.filter(subject_id = sid, user_id = uid, is_complete=False).order_by("-id")
        uncompleted_study_plan = StudyPlansListingSerializer(uncompleted_study_plans, many=True)

        completed_study_plans = StudyPlans.objects.filter(subject_id = sid, user_id = uid, is_complete=True).order_by("-id")
        completed_study_plan = StudyPlansListingSerializer(completed_study_plans, many=True)
        
    
        data = {
                    "uncompleted_study_plan":uncompleted_study_plan.data,
                    "completed_study_plan":completed_study_plan.data,
                    'username':user.first_name +' '+user.last_name,
                    'user_id':user.email,
                    "course":subject.course.name,
                    "subject":subject.subject.name
                }
        

        template = get_template('pdf/study_plan_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "stud_plan_report"
            username = re.sub(r'\s+', '_', f"{user.first_name} {user.last_name}")
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{username}_{report_name}_{timestamp}.pdf"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)
    


class GetAdminStudyPlanReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_study_plan_report_excel",
                            [SuperAdmin]
                        )]
    def get(self, request, uid, sid):
        
        subject = CourseSubjects.objects.select_related("course", "subject").filter(id=sid).first()
        if subject is None:
            raise ValidationError("Invalid Subject ID")

        user = User.objects.get(id = uid)

        uncompleted_study_plans = StudyPlans.objects.filter(subject_id = sid, user_id = uid, is_complete=False).order_by("-id")
        uncompleted_study_plan = StudyPlansListingSerializer(uncompleted_study_plans, many=True)

        completed_study_plans = StudyPlans.objects.filter(subject_id = sid, user_id = uid, is_complete=True).order_by("-id")
        completed_study_plan = StudyPlansListingSerializer(completed_study_plans, many=True)

        lis = []
        
        lis.append({
                "name":"Study Plan Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        lis.append({
                "name":"Name:",
                "email":user.first_name +' '+user.last_name,
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        lis.append({
                "name":"User ID:",
                "email":user.email,
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        lis.append({
                "name":"Course:",
                "email":subject.course.name,
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        lis.append({
                "name":"Subject ",
                "email":subject.subject.name,
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        lis.append({
                "name":"On-Going Study Plan",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        lis.append({
                "name":"Chapter Name",
                "email":'Topic Name',
                "subject":'Start Date',
                "Chapter":'End Date',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        for chapter_data in uncompleted_study_plan.data:

            lis.append({
                "name":chapter_data['chapter']['chapter_detail']['name'],
                "email":chapter_data['topic']['topic_detail']['name'],
                "subject":chapter_data['start_date'],
                "Chapter":chapter_data['end_date'],
                "Topic":"",
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })

            
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        lis.append({
                "name":"Completed Study Plan",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        lis.append({
                "name":"Chapter Name",
                "email":'Topic Name',
                "subject":'Start Date',
                "Chapter":'End Date',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        for chapter_data in completed_study_plan.data:

            lis.append({
                "name":chapter_data['chapter']['chapter_detail']['name'],
                "email":chapter_data['topic']['topic_detail']['name'],
                "subject":chapter_data['start_date'],
                "Chapter":chapter_data['end_date'],
                "Topic":"",
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })

            


        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "study_plan_report"
            username = re.sub(r'\s+', '_', f"{user.first_name} {user.last_name}")
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{username}_{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)



class UpdateStudentAccountStatusView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_student_account_status",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        subject = User.objects.filter(id=cid, role = User.Student).first()
        if subject is None:
            raise ValidationError("Invalid User ID!")
        
        serializer = ChangeUserAccounttatusSerializer(subject, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="User Account Updated Successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class GetStudentActivityReportView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_activity_report_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    def get(self, request, uid=None):
        
        topics = UserLoginActivity.objects.filter(user_id = uid, user__role = User.Student)
        
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
        topics = search_filter.filter_queryset(request, topics, self)

        if not topics.ordered:
            topics = topics.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = StudentLoginActivitySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class GetAdminChangePasswordReportView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_activity_report_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, uid=None):
        
        topics = PasswordChangeLog.objects.filter(user_id = uid, user__role = User.Student)
        
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
            

        if not topics.ordered:
            topics = topics.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = StudentPasswordChangeRecordSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    



class GetAdminChangePasswordReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_study_plan_report_pdf",
                            [SuperAdmin]
                        )]
    def get(self, request, uid):
        
        user = User.objects.get(id = uid)

        topics = PasswordChangeLog.objects.filter(user_id = uid, user__role = User.Student)
        
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
            

        if not topics.ordered:
            topics = topics.order_by('-id')


        serializer = StudentPasswordChangeRecordSerializer(topics, many=True)

        data = {
                    "records":serializer.data,
                    'username':user.first_name +' '+user.last_name,
                    'user_id':user.email
                }
        

        template = get_template('pdf/password_log_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "password_log_report"
            username = re.sub(r'\s+', '_', f"{user.first_name} {user.last_name}")
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{username}_{report_name}_{timestamp}.pdf"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)
    


class GetAdminChangePasswordReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_study_plan_report_excel",
                            [SuperAdmin]
                        )]
    def get(self, request, uid):
        
        user = User.objects.get(id = uid)

        topics = PasswordChangeLog.objects.filter(user_id = uid, user__role = User.Student)
        
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
            

        if not topics.ordered:
            topics = topics.order_by('-id')


        serializer = StudentPasswordChangeRecordSerializer(topics, many=True)

        lis = []
        
        lis.append({
                "name":"Student Password Log Report",
                "email":''
            })

        lis.append({
                "name":"Name:",
                "email":user.first_name +' '+user.last_name
            })
        lis.append({
                "name":"User ID:",
                "email":user.email
            })
        
        lis.append({
                "name":"",
                "email":''
            })
        
        lis.append({
                "name":"Description",
                "email":'Updated At'
            })
        
        
        for chapter_data in serializer.data:
            info = chapter_data['user_detail']['first_name']+" "+chapter_data['user_detail']['last_name']+ " Changed on "+chapter_data['created_at']
            lis.append({
                "name":info,
                "email":chapter_data['created_at'],
            })

            
            
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "password_log_report"
            username = re.sub(r'\s+', '_', f"{user.first_name} {user.last_name}")
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{username}_{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)
            


class GetStudentAssessmentTestReportlistingView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_activity_report_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    def get(self, request, uid=None):
        
        topics = AssessmentTests.objects.all()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id = course_id.split(',')
            topics = topics.filter(course_id__in =course_id)

        subject_id = request.query_params.get('subject_id')
        if subject_id:
            subject_id = subject_id.split(',')
            topics = topics.filter(subject_id__in =subject_id)

        if category:
            category = category.split(',')
            topics = topics.filter(user__category__in = category)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(user__student_type__in =student_type)


        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'user__reference_id__icontains': term})
                
                topics = topics.filter(q_objects)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)

        if not topics.ordered:
            topics = topics.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = StudentAssessmentTestListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class GetStudentStudyPlanReportlistingView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_activity_report_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    def get(self, request, uid=None):
        
        
        topics = StudyPlans.objects.all()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id = course_id.split(',')
            topics = topics.filter(course_id__in =course_id)

        subject_id = request.query_params.get('subject_id')
        if subject_id:
            subject_id = subject_id.split(',')
            topics = topics.filter(subject_id__in =subject_id)

        if category:
            category = category.split(',')
            topics = topics.filter(user__category__in = category)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(user__student_type__in =student_type)


        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'user__reference_id__icontains': term})
                
                topics = topics.filter(q_objects)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)


        topics = topics.values('user','user__first_name','user__last_name','user__email','user__category','user__phone1','user__reference_id', "user__student_type",'course','course__name', 'subject', 'subject__subject__name').annotate(
            completed_studyplan_count=Count('id', filter=Q(is_complete=True)),
            uncompleted_studyplan_count=Count('id', filter=Q(is_complete=False))
        ).order_by('user', 'course', 'subject')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = StudentStudyPlanListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)



class GetStudentNotesReportlistingView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_activity_report_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    def get(self, request, uid=None):
        
        
        topics = UserNotes.objects.all()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id = course_id.split(',')
            topics = topics.filter(course_id__in =course_id)

        subject_id = request.query_params.get('subject_id')
        if subject_id:
            subject_id = subject_id.split(',')
            topics = topics.filter(subject_id__in =subject_id)

        if category:
            category = category.split(',')
            topics = topics.filter(user__category__in = category)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(user__student_type__in =student_type)


        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'user__reference_id__icontains': term})
                
                topics = topics.filter(q_objects)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)


        topics = topics.values('user','user__first_name','user__last_name','user__email','user__category','user__phone1','user__reference_id', "user__student_type",'course','course__name', 'subject', 'subject__subject__name').annotate(
            notes_count=Count('id')
        ).order_by('user', 'course', 'subject')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = StudentNoteListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class GetStudentMockReportlistingView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_activity_report_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    def get(self, request, uid=None):
        
        
        topics = MockTests.objects.all()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id = course_id.split(',')
            topics = topics.filter(course_id__in =course_id)

        subject_id = request.query_params.get('subject_id')
        if subject_id:
            subject_id = subject_id.split(',')
            topics = topics.filter(subject_id__in =subject_id)

        if category:
            category = category.split(',')
            topics = topics.filter(user__category__in = category)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(user__student_type__in =student_type)


        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'user__reference_id__icontains': term})
                
                topics = topics.filter(q_objects)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)


        topics = topics.values('user','user__first_name','user__last_name','user__email','user__category','user__phone1','user__reference_id', "user__student_type",'course','course__name', 'subject', 'subject__subject__name').annotate(
            mock_test_count=Count('id')
        ).order_by('user', 'course', 'subject')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = StudentMockTestListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    



class GetAdminMockTestListingReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_study_plan_report_pdf",
                            [SuperAdmin]
                        )]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    def get(self, request):
        
        topics = MockTests.objects.all()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id = course_id.split(',')
            topics = topics.filter(course_id__in =course_id)

        subject_id = request.query_params.get('subject_id')
        if subject_id:
            subject_id = subject_id.split(',')
            topics = topics.filter(subject_id__in =subject_id)

        if category:
            category = category.split(',')
            topics = topics.filter(user__category__in = category)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(user__student_type__in =student_type)


        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'user__reference_id__icontains': term})
                
                topics = topics.filter(q_objects)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)


        topics = topics.values('user','user__first_name','user__last_name','user__email','user__category','user__phone1','user__reference_id', "user__student_type",'course','course__name', 'subject', 'subject__subject__name').annotate(
            mock_test_count=Count('id')
        ).order_by('user', 'course', 'subject')

        serializer = StudentMockTestListingSerializer(topics, many=True)

        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/mock_test_listing_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "mock_test_report"
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
            os.remove(pdf_path)
    


class GetAdminMockTestListingReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_study_plan_report_excel",
                            [SuperAdmin]
                        )]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    def get(self, request):
        
        topics = MockTests.objects.all()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id = course_id.split(',')
            topics = topics.filter(course_id__in =course_id)

        subject_id = request.query_params.get('subject_id')
        if subject_id:
            subject_id = subject_id.split(',')
            topics = topics.filter(subject_id__in =subject_id)

        if category:
            category = category.split(',')
            topics = topics.filter(user__category__in = category)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(user__student_type__in =student_type)


        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'user__reference_id__icontains': term})
                
                topics = topics.filter(q_objects)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)


        topics = topics.values('user','user__first_name','user__last_name','user__email','user__category','user__phone1','user__reference_id', "user__student_type",'course','course__name', 'subject', 'subject__subject__name').annotate(
            mock_test_count=Count('id')
        ).order_by('user', 'course', 'subject')

        serializer = StudentMockTestListingSerializer(topics, many=True)

        lis = []
        
        lis.append({
                "name":"Mock test Report",
                "last_name":"",
                "email":'',
                "phone":'',
                "category":'',
                "type":'',
                "reference":'',
                "course":'',
                "subject":'',
                "count":''
            })

        lis.append({
                "name":"",
                "last_name":"",
                "email":'',
                "phone":'',
                "category":'',
                "type":'',
                "reference":'',
                "course":'',
                "subject":'',
                "count":''
            })
        
        lis.append({
                "name":"",
                "last_name":"",
                "email":'',
                "phone":'',
                "category":'',
                "type":'',
                "reference":'',
                "course":'',
                "subject":'',
                "count":''
            })
        
        lis.append({
                "name":"First Name",
                "last_name":"Last Name",
                "email":'Email',
                "phone":'Phone',
                "category":'Student Category',
                "type":'Student Type',
                "reference":'Reference ID',
                "course":'Course Name',
                "subject":'Subject Name',
                "count":'No. of Mock Test'
            })
        
        
        for chapter_data in serializer.data:
            lis.append({
                "name":chapter_data['user__first_name'],
                "last_name":chapter_data['user__last_name'],
                "email":chapter_data['user__email'],
                "phone":chapter_data['user__phone1'],
                "category":chapter_data['user__category'],
                "type":chapter_data['user__student_type'],
                "reference":chapter_data['user__reference_id'],
                "course":chapter_data['course__name'],
                "subject":chapter_data['subject__subject__name'],
                "count":chapter_data['mock_test_count']
            })

            
            
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "mock_test_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)



class GetAdminNotesListingReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_study_plan_report_pdf",
                            [SuperAdmin]
                        )]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    def get(self, request):
        
        topics = UserNotes.objects.all()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id = course_id.split(',')
            topics = topics.filter(course_id__in =course_id)

        subject_id = request.query_params.get('subject_id')
        if subject_id:
            subject_id = subject_id.split(',')
            topics = topics.filter(subject_id__in =subject_id)

        if category:
            category = category.split(',')
            topics = topics.filter(user__category__in = category)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(user__student_type__in =student_type)


        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'user__reference_id__icontains': term})
                
                topics = topics.filter(q_objects)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)


        topics = topics.values('user','user__first_name','user__last_name','user__email','user__category','user__phone1','user__reference_id', "user__student_type",'course','course__name', 'subject', 'subject__subject__name').annotate(
            notes_count=Count('id')
        ).order_by('user', 'course', 'subject')

        serializer = StudentNoteListingSerializer(topics, many=True)

        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/user_notes_listing_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "notes_report"
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
            os.remove(pdf_path)
    


class GetAdminNotesListingReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_study_plan_report_excel",
                            [SuperAdmin]
                        )]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    def get(self, request):
        
        topics = UserNotes.objects.all()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id = course_id.split(',')
            topics = topics.filter(course_id__in =course_id)

        subject_id = request.query_params.get('subject_id')
        if subject_id:
            subject_id = subject_id.split(',')
            topics = topics.filter(subject_id__in =subject_id)

        if category:
            category = category.split(',')
            topics = topics.filter(user__category__in = category)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(user__student_type__in =student_type)


        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'user__reference_id__icontains': term})
                
                topics = topics.filter(q_objects)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)


        topics = topics.values('user','user__first_name','user__last_name','user__email','user__category','user__phone1','user__reference_id', "user__student_type",'course','course__name', 'subject', 'subject__subject__name').annotate(
            notes_count=Count('id')
        ).order_by('user', 'course', 'subject')

        serializer = StudentNoteListingSerializer(topics, many=True)

        lis = []
        
        lis.append({
                "name":"Notes Listing Report",
                "last_name":"",
                "email":'',
                "phone":'',
                "category":'',
                "type":'',
                "reference":'',
                "course":'',
                "subject":'',
                "count":''
            })

        lis.append({
                "name":"",
                "last_name":"",
                "email":'',
                "phone":'',
                "category":'',
                "type":'',
                "reference":'',
                "course":'',
                "subject":'',
                "count":''
            })
        
        lis.append({
                "name":"",
                "last_name":"",
                "email":'',
                "phone":'',
                "category":'',
                "type":'',
                "reference":'',
                "course":'',
                "subject":'',
                "count":''
            })
        
        lis.append({
                "name":"First Name",
                "last_name":"Last Name",
                "email":'Email',
                "phone":'Phone',
                "category":'Student Category',
                "type":'Student Type',
                "reference":'Reference ID',
                "course":'Course Name',
                "subject":'Subject Name',
                "count":'No. of Notes'
            })
        
        
        for chapter_data in serializer.data:
            lis.append({
                "name":chapter_data['user__first_name'],
                "last_name":chapter_data['user__last_name'],
                "email":chapter_data['user__email'],
                "phone":chapter_data['user__phone1'],
                "category":chapter_data['user__category'],
                "type":chapter_data['user__student_type'],
                "reference":chapter_data['user__reference_id'],
                "course":chapter_data['course__name'],
                "subject":chapter_data['subject__subject__name'],
                "count":chapter_data['notes_count']
            })

            
            
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "notes_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)




class GetAdminAssessmentTestListingReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_study_plan_report_pdf",
                            [SuperAdmin]
                        )]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    def get(self, request):
        
        topics = AssessmentTests.objects.all()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id = course_id.split(',')
            topics = topics.filter(course_id__in =course_id)

        subject_id = request.query_params.get('subject_id')
        if subject_id:
            subject_id = subject_id.split(',')
            topics = topics.filter(subject_id__in =subject_id)

        if category:
            category = category.split(',')
            topics = topics.filter(user__category__in = category)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(user__student_type__in =student_type)


        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'user__reference_id__icontains': term})
                
                topics = topics.filter(q_objects)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)

        if not topics.ordered:
            topics = topics.order_by('-id')

        serializer = StudentAssessmentTestListingSerializer(topics, many=True)

        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/user_assessment_test_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "assessment_test_report"
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
            os.remove(pdf_path)
    


class GetAdminAssessmentTestListingReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_study_plan_report_excel",
                            [SuperAdmin]
                        )]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    def get(self, request):
        
        topics = AssessmentTests.objects.all()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id = course_id.split(',')
            topics = topics.filter(course_id__in =course_id)

        subject_id = request.query_params.get('subject_id')
        if subject_id:
            subject_id = subject_id.split(',')
            topics = topics.filter(subject_id__in =subject_id)

        if category:
            category = category.split(',')
            topics = topics.filter(user__category__in = category)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(user__student_type__in =student_type)


        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'user__reference_id__icontains': term})
                
                topics = topics.filter(q_objects)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)

        if not topics.ordered:
            topics = topics.order_by('-id')

        serializer = StudentAssessmentTestListingSerializer(topics, many=True)

        lis = []
        
        lis.append({
                "name":"Assessment Test Report",
                "last_name":"",
                "email":'',
                "phone":'',
                "category":'',
                "type":'',
                "reference":'',
                "course":'',
                "subject":'',
                "score":'',
                "start_date":"",
                "end_date":"",
                "status":""
            })

        lis.append({
                "name":"",
                "last_name":"",
                "email":'',
                "phone":'',
                "category":'',
                "type":'',
                "reference":'',
                "course":'',
                "subject":'',
                "score":'',
                "start_date":"",
                "end_date":"",
                "status":""
            })
        
        lis.append({
                "name":"",
                "last_name":"",
                "email":'',
                "phone":'',
                "category":'',
                "type":'',
                "reference":'',
                "course":'',
                "subject":'',
                "score":'',
                "start_date":"",
                "end_date":"",
                "status":""
            })
        
        lis.append({
                "name":"First Name",
                "last_name":"Last Name",
                "email":'Email',
                "phone":'Phone',
                "category":'Student Category',
                "type":'Student Type',
                "reference":'Reference ID',
                "course":'Course Name',
                "subject":'Subject Name',
                "score":'Score',
                "start_date":"Start Date & Time",
                "end_date":"End Date & Time",
                "status":"Is Completed?"
            })
        
        
        for chapter_data in serializer.data:
            lis.append({
                "name":chapter_data['user_detail']['first_name'],
                "last_name":chapter_data['user_detail']['last_name'],
                "email":chapter_data['user_detail']['email'],
                "phone":chapter_data['user_detail']['phone1'],
                "category":chapter_data['user_detail']['category'],
                "type":chapter_data['user_detail']['student_type'],
                "reference":chapter_data['user_detail']['reference_id'],
                "course":chapter_data['course_detail']['name'],
                "subject":chapter_data['subject_detail']['name'],
                "score":chapter_data['score'],
                "start_date":chapter_data['start_time'],
                "end_date":chapter_data['end_time'],
                "status":chapter_data['status']
            })

            
            
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "assessment_test_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)




class GetAdminStudyplanListingReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_study_plan_report_pdf",
                            [SuperAdmin]
                        )]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    def get(self, request):
        
        topics = StudyPlans.objects.all()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id = course_id.split(',')
            topics = topics.filter(course_id__in =course_id)

        subject_id = request.query_params.get('subject_id')
        if subject_id:
            subject_id = subject_id.split(',')
            topics = topics.filter(subject_id__in =subject_id)

        if category:
            category = category.split(',')
            topics = topics.filter(user__category__in = category)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(user__student_type__in =student_type)


        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'user__reference_id__icontains': term})
                
                topics = topics.filter(q_objects)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)


        topics = topics.values('user','user__first_name','user__last_name','user__email','user__category','user__phone1','user__reference_id', "user__student_type",'course','course__name', 'subject', 'subject__subject__name').annotate(
            completed_studyplan_count=Count('id', filter=Q(is_complete=True)),
            uncompleted_studyplan_count=Count('id', filter=Q(is_complete=False))
        ).order_by('user', 'course', 'subject')

        serializer = StudentStudyPlanListingSerializer(topics, many=True)

        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/user_studyplans_listing_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "studyplan_report"
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
            os.remove(pdf_path)
    


class GetAdminStudyplanListingReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_study_plan_report_excel",
                            [SuperAdmin]
                        )]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    def get(self, request):
        
        topics = StudyPlans.objects.all()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id = course_id.split(',')
            topics = topics.filter(course_id__in =course_id)

        subject_id = request.query_params.get('subject_id')
        if subject_id:
            subject_id = subject_id.split(',')
            topics = topics.filter(subject_id__in =subject_id)

        if category:
            category = category.split(',')
            topics = topics.filter(user__category__in = category)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(user__student_type__in =student_type)


        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'user__reference_id__icontains': term})
                
                topics = topics.filter(q_objects)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(user__created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)


        topics = topics.values('user','user__first_name','user__last_name','user__email','user__category','user__phone1','user__reference_id', "user__student_type",'course','course__name', 'subject', 'subject__subject__name').annotate(
            completed_studyplan_count=Count('id', filter=Q(is_complete=True)),
            uncompleted_studyplan_count=Count('id', filter=Q(is_complete=False))
        ).order_by('user', 'course', 'subject')

        serializer = StudentStudyPlanListingSerializer(topics, many=True)

        lis = []
        
        lis.append({
                "name":"Student Study Plan Report",
                "last_name":"",
                "email":'',
                "phone":'',
                "category":'',
                "type":'',
                "reference":'',
                "course":'',
                "subject":'',
                "count":'',
                "count1":''
            })

        lis.append({
                "name":"",
                "last_name":"",
                "email":'',
                "phone":'',
                "category":'',
                "type":'',
                "reference":'',
                "course":'',
                "subject":'',
                "count":'',
                "count1":''
            })
        
        lis.append({
                "name":"",
                "last_name":"",
                "email":'',
                "phone":'',
                "category":'',
                "type":'',
                "reference":'',
                "course":'',
                "subject":'',
                "count":'',
                "count1":''
            })
        
        lis.append({
                "name":"First Name",
                "last_name":"Last Name",
                "email":'Email',
                "phone":'Phone',
                "category":'Student Category',
                "type":'Student Type',
                "reference":'Reference ID',
                "course":'Course Name',
                "subject":'Subject Name',
                "count":'No. of Completed Study Plans',
                "count1":'No. of Incomplete Study Plans'
            })
        
        
        for chapter_data in serializer.data:
            lis.append({
                "name":chapter_data['user__first_name'],
                "last_name":chapter_data['user__last_name'],
                "email":chapter_data['user__email'],
                "phone":chapter_data['user__phone1'],
                "category":chapter_data['user__category'],
                "type":chapter_data['user__student_type'],
                "reference":chapter_data['user__reference_id'],
                "course":chapter_data['course__name'],
                "subject":chapter_data['subject__subject__name'],
                "count":chapter_data['completed_studyplan_count'],
                "count1":chapter_data['uncompleted_studyplan_count'],
            })

            
            
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "studyplan_report"
            gcs_folder_name = "media/lms_2/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)