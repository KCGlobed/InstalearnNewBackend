from rest_framework import status
from rest_framework.views import APIView
from reports.serializers import *
from reports.models import *
from cms.models import *
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
import re
from mini_lms.permissions import RoleOrPermissionCheck
from mini_lms.pagination import CustomPageNumberPagination
from rest_framework import filters
from dateutil.relativedelta import relativedelta
from datetime import datetime,timezone, timedelta, timezone



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
            gcs_folder_name = "media/reports"
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
            gcs_folder_name = "media/reports"
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
    

class GetVideoReportView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_video_reports",
                            [SuperAdmin]
                        )]
    def get(self, request, cid = None, uid=None):
        
        category = CourseChapters.objects.filter(course_id=cid)
        user = User.objects.filter(id = uid).first()
        serializer = CourseVideoReportSerializer(category, many=True, context={'user':user})
        total_video_watched = UserLectureProgress.objects.filter( course_id = cid, user = user).count()
        total_duration_video_watched = UserLectureProgress.objects.filter( course_id = cid, user = user).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0

        return success_response(message="Success", data={"report_data":serializer.data, "total_video_watched":total_video_watched, "total_duration_video_watched":total_duration_video_watched}, status_code=status.HTTP_200_OK)


class DownloadChapterVideoReportView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_video_reports_pdf",
                            [SuperAdmin]
                        )]
    def get(self, request, cid = None, uid=None):
        
        course = Course.objects.get(id = cid)
        user = User.objects.filter(id = uid).first()
        category = CourseChapters.objects.filter(course_id=cid)
        serializer = CourseVideoReportSerializer(category, many=True, context={'user':user})
        total_video_watched = UserLectureProgress.objects.filter( course_id = cid, user = user).count()
        total_duration_video_watched = UserLectureProgress.objects.filter( course_id = cid, user = user).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0

        
        result = {
                'video_report': serializer.data,
                'username':user.first_name +' '+user.last_name,
                'user_id':user.email,
                "total_video_watched":total_video_watched,
                "total_duration_video_watched":total_duration_video_watched,
                'course':course.name,
            }

        template = get_template('pdf/video_progress_report.html')
        html  = template.render(result)

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "video_progress_report"
            gcs_folder_name = "media/reports"
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
            


class DownloadChapterVideoReportCSVView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_video_reports_excel",
                            [SuperAdmin]
                        )]
    def get(self, request, cid = None,  uid=None):
        
        course_subject = Course.objects.get(id = cid)
        user = User.objects.filter(id = uid).first()
        category = CourseChapters.objects.filter(course_id=cid)
        serializer = CourseVideoReportSerializer(category, many=True, context={'user':user})
        total_video_watched = UserLectureProgress.objects.filter( course_id = cid, user = user).count()
        total_duration_video_watched = UserLectureProgress.objects.filter( course_id = cid, user = user).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0


        lis = []
        
        lis.append({
                "name":"Video Report",
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
                "email":course_subject.name,
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
                "name":"Hours Watched",
                "email":convert(total_duration_video_watched),
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        lis.append({
                "name":"Video Watched",
                "email":total_video_watched,
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
                "name":"Chapter Name",
                "email":'Total Videos',
                "subject":'Videos Watched',
                "Chapter":'Watch Time',
                "Topic":'Watch Time',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        for info in serializer.data:
            if info['video_watched'] is not None:
                video_watched = convert_minutes(info['video_watched'])
            else :
                video_watched = "0s"

            lis.append({
                "name":info['chapter_info']['name'],
                "email":info['chapter_info']['no_of_videos'],
                "subject":info['total_video_watched'],
                "Chapter":video_watched,
                "Topic":"",
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })

        current_GMT = time.gmtime()
        ts = calendar.timegm(current_GMT)


        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "video_report"
            gcs_folder_name = "media/reports"
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



class GetStudentAccessLockReportView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_access_lock_reports",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    search_fields = ['user__first_name','user__last_name',"user__email"]
    def get(self, request, format=None):
        
        topics = UserAccountLockDetail.objects.only("id","user","device_id","device_type","ip_address","created_at").select_related("user").all()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
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
                
                users_list = users_list.filter(q_objects)

        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")

        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)
         
        topics = topics.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = StudentAccessLockReportSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class GetStudentAccessLockReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_access_lock_reports_pdf",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        topics = UserAccountLockDetail.objects.only("id","user","device_id","device_type","ip_address","created_at").select_related("user").all()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        if category:
            category = category.split(',')
            topics = topics.filter(user__category__in = category)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(user__student_type__in =student_type)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        topics = topics.order_by('-id')

        serializer = StudentAccessLockReportSerializer(topics, many=True)
    
        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/student_access_lock_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "student_access_lock_report"
            gcs_folder_name = "media/reports"
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
    


class GetStudentAccessLockReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_access_lock_reports_excel",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        topics = UserAccountLockDetail.objects.only("id","user","device_id","device_type","ip_address","created_at").select_related("user").all()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        if category:
            category = category.split(',')
            topics = topics.filter(user__category__in = category)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(user__student_type__in =student_type)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        topics = topics.order_by('-id')

        serializer = StudentAccessLockReportSerializer(topics, many=True)
        
        lis = []
        
        lis.append({
                "name":"Student Access Lock Report",
                "email":'',
                "subject":'',
                "phone":"",
                "category":"",
                "type":"",
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "device_list":"",
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "phone":"",
                "category":"",
                "type":"",
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "device_list":"",
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"First Name",
                "email":'Last Name',
                "subject":'Email',
                "phone":"Phone Number",
                "category":"Student Category",
                "type":"Student Type",
                "Chapter":'Reference ID',
                "Topic":'Device ID',
                "total_videos":'Device Type',
                "total_watched_videos":'IP Address',
                "device_list":"Devices List",
                "total_time_spend":'Locked At'
            })
  

        for order_info in serializer.data:
            device_list = ""
            for device in  order_info['user_devices']:
                device_list += device["device_id"]+" ,"
            
            lis.append({
                "name":order_info['user_detail']['first_name'],
                "email":order_info['user_detail']['last_name'],
                "subject":order_info['user_detail']['email'],
                "phone":order_info['user_detail']['phone1'],
                "category":order_info['user_detail']['category'],
                "type":order_info['user_detail']['student_type'],
                "Chapter":order_info['user_detail']['reference_id'],
                "Topic":order_info['device_id'],
                "total_videos":order_info['device_type'],
                "total_watched_videos":order_info['ip_address'],
                "device_list":device_list,
                "total_time_spend":order_info['created_at']
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "student_access_lock_report"
            gcs_folder_name = "media/reports"
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
    


class TrailUserListingView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "trail_user_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name','last_name',"email"]
    ordering_fields = ['first_name', 'created_at', 'id', 'last_name',"email"] 
    def get(self, request, format=None):
        
        plans = Order.objects.filter(trail_mode = True, subscription_status__in = [OrderStatus.Active , OrderStatus.Expired], user__isnull=False)
        
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
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "trail_user_listing_pdf_report",
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        plans = Order.objects.filter(trail_mode = True, subscription_status__in = [OrderStatus.Active , OrderStatus.Expired], user__isnull=False)
        
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
            gcs_folder_name = "media/reports"
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
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "trail_user_listing_excel_report",
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        
        plans = Order.objects.filter(trail_mode = True, subscription_status__in = [OrderStatus.Active , OrderStatus.Expired], user__isnull=False)
        
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
                "start_date":'End Date',
                "end_date":end_date,
                "subscription_status":'',
                "ordered_courses":'',
                "created_at":'',
            })
        
        lis.append({
                "first_name":"",
                "last_name":'',
                "email":'',
                "phone":'',
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
            gcs_folder_name = "media/reports"
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




class GetStudentRegistrationReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_registration_pdf_report",
                            [SuperAdmin]
                        )]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name',"last_name","email","is_active","created_at","category"]
    ordering_fields = ["id",'first_name',"last_name","email","is_active","created_at","category"] 
    def get(self, request, format=None):
        
        topics = User.objects.filter(role = User.Student)
        
        first_name = request.query_params.get('first_name')
        if first_name:
            topics = topics.filter(first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            topics = topics.filter(last_name__icontains = last_name)

        email = request.query_params.get('email')
        if email:
            topics = topics.filter(email__icontains = email)

        phone1 = request.query_params.get('phone')
        if phone1:
            topics = topics.filter(phone1__icontains = phone1)

        is_active = request.query_params.get('status')
        if is_active:
            topics = topics.filter(is_active = is_active)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        if category:
            category = category.split(',')
            topics = topics.filter(category__in = category)

        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'reference_id__icontains': term})
                
                topics = topics.filter(q_objects)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(student_type__in =student_type)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)

        ordering_filter = filters.OrderingFilter()
        topics = ordering_filter.filter_queryset(request, topics, self)

        if not topics.ordered:
            topics = topics.order_by('-id')

        serializer = StudentRegistrationSerializer(topics, many=True)

        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/student_registration_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "student_registration_report"
            gcs_folder_name = "media/reports"
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
    


class GetStudentRegistrationReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_registration_excel_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name',"last_name","email","is_active","created_at","category"]
    ordering_fields = ["id",'first_name',"last_name","email","is_active","created_at","category"] 
    def get(self, request, format=None):
        
        topics = User.objects.filter(role = User.Student)
        
        first_name = request.query_params.get('first_name')
        if first_name:
            topics = topics.filter(first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            topics = topics.filter(last_name__icontains = last_name)

        email = request.query_params.get('email')
        if email:
            topics = topics.filter(email__icontains = email)

        phone1 = request.query_params.get('phone')
        if phone1:
            topics = topics.filter(phone1__icontains = phone1)

        is_active = request.query_params.get('status')
        if is_active:
            topics = topics.filter(is_active = is_active)
              
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        if category:
            category = category.split(',')
            topics = topics.filter(category__in = category)

        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'reference_id__icontains': term})
                
                topics = topics.filter(q_objects)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(student_type__in =student_type)


        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)

        ordering_filter = filters.OrderingFilter()
        topics = ordering_filter.filter_queryset(request, topics, self)

        if not topics.ordered:
            topics = topics.order_by('-id')

        serializer = StudentRegistrationSerializer(topics, many=True)
        
        lis = []
        
        lis.append({
                "name":"Student Report",
                "email":'',
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":'',
                "courses":""
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
                "courses":""
            })
        
        
        lis.append({
                "name":"First Name",
                "email":'Last Name',
                "subject":'Email',
                "Chapter":'Phone Number',
                "Topic":'Category',
                "total_videos":'Student Type',
                "total_watched_videos":'Reference ID',
                "total_time_spend":'Is Active?',
                "courses":"Registration Date"
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['first_name'],
                "email":order_info['last_name'],
                "subject":order_info['email'],
                "Chapter":order_info['phone1'],
                "Topic":order_info['category'],
                "total_videos":order_info['student_type'],
                "total_watched_videos":order_info['reference_id'],
                "total_time_spend":order_info['is_active'],
                "courses":order_info['created_at']
            })
        

            

            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "student_registration_report"
            gcs_folder_name = "media/reports"
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



class ActiveOrderListingView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_order_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', "last_name","email"]
    ordering_fields = ['first_name', "last_name","email",'created_at', 'id'] 
    def get(self, request, format=None):
        
        plans = Order.objects.filter(subscription_status__in = [OrderStatus.Active , OrderStatus.Expired])
        
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

        country = request.query_params.get('country')
        if country:
            plans = plans.filter(country = country)

        state = request.query_params.get('state')
        if state:
            plans = plans.filter(state = state)

        city = request.query_params.get('city')
        if city:
            plans = plans.filter(city = city)

        subscription_type = request.query_params.get('subscription_type')
        if subscription_type:
            subscription_type = subscription_type.split(',')
            plans = plans.filter(subscription_type__in = subscription_type)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                plans = plans.filter(start_date__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                plans = plans.filter(end_date__lte=end_datetime)
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
    

class ExportPDFActiveOrderListingView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_order_report_pdf",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', "last_name","email","plan__plan_name"]
    ordering_fields = ['first_name', "last_name","email",'created_at', 'id'] 
    def get(self, request, format=None):
        
        plans = Order.objects.filter(subscription_status__in = [OrderStatus.Active , OrderStatus.Expired])
        
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

        subscription_type = request.query_params.get('subscription_type')
        if subscription_type:
            subscription_type = subscription_type.split(',')
            plans = plans.filter(subscription_type__in = subscription_type)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                plans = plans.filter(start_date__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                plans = plans.filter(end_date__lte=end_datetime)
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


        template = get_template('pdf/active_subscription_report.html')
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
            report_name = "subscription_report"
            gcs_folder_name = "media/reports"
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
    


class ExportExcelActiveOrderListingView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_order_report_excel",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', "last_name","email"]
    ordering_fields = ['first_name', "last_name","email",'created_at', 'id'] 
    def get(self, request, format=None):
        
        plans = Order.objects.filter(subscription_status__in = [OrderStatus.Active , OrderStatus.Expired])
        
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

        subscription_type = request.query_params.get('subscription_type')
        if subscription_type:
            subscription_type = subscription_type.split(',')
            plans = plans.filter(subscription_type__in = subscription_type)


        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                plans = plans.filter(start_date__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                plans = plans.filter(end_date__lte=end_datetime)
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
                "first_name":"Orders Report",
                "last_name":'',
                "email":'',
                "phone":'',
                "ordered_courses":'',
                "total_amount":'',
                "start_date":'',
                "end_date":'',
                "subscription_type":'',
                "subscription_status":'',
                
                "created_at":'',
            })
        
        lis.append({
                "first_name":"",
                "last_name":'',
                "email":'',
                "phone":'',
                "ordered_courses":'',
                "total_amount":'',
                "start_date":'',
                "end_date":'',
                "subscription_type":'',
                "subscription_status":'',
                
                "created_at":'',
            })
        
        lis.append({
                "first_name":"",
                "last_name":'',
                "email":'',
                "phone":'',
                "ordered_courses":'',
                "total_amount":'',
                "start_date":'',
                "end_date":'',
                "subscription_type":'',
                "subscription_status":'',
                
                "created_at":'',
            })
        
        lis.append({
                "first_name":"First Name",
                "last_name":'Last Name',
                "email":'Email',
                "phone":'Phone',
                "ordered_courses":'Courses List',
                "total_amount":'Total Amount',
                "start_date":'Start Date',
                "end_date":'End Date',
                "subscription_type":'Subscription Status',
                "subscription_status":'Is Trail',
                
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
                "ordered_courses":course_list,
                "total_amount":order['total_amount'],
                "start_date":order['start_date'],
                "end_date":order['end_date'],
                "subscription_type": OrderStatus(order['subscription_status']).label,
                "subscription_status":order['trail_mode'],
                "created_at":order['created_at'],
            })

        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            # GCS file naming logic
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "subscription_report"
            gcs_folder_name = "media/reports"
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



class GetContactUSView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "contact_us_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', "last_name","email","phone"]
    ordering_fields = ['first_name', "last_name","email",'created_at', 'id'] 
    def get(self, request, format=None):
        
        plans = ContactUs.objects.all()

        first_name = request.query_params.get('first_name')
        if first_name:
            plans = plans.filter(first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            plans = plans.filter(last_name__icontains = last_name)


        email = request.query_params.get('email')
        if email:
            plans = plans.filter(email__icontains = email)

        
        phone = request.query_params.get('phone')
        if phone:
            plans = plans.filter(phone__icontains = phone)

        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                plans = plans.filter(start_date__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                plans = plans.filter(end_date__lte=end_datetime)
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
        serializer = ContactListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class PDFContactUsReportView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "contact_us_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', "last_name","email","phone"]
    ordering_fields = ['first_name', "last_name","email",'created_at', 'id'] 
    def get(self, request, format=None):
        
        plans = ContactUs.objects.all()
        
        first_name = request.query_params.get('first_name')
        if first_name:
            plans = plans.filter(first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            plans = plans.filter(last_name__icontains = last_name)


        email = request.query_params.get('email')
        if email:
            plans = plans.filter(email__icontains = email)

        
        phone = request.query_params.get('phone')
        if phone:
            plans = plans.filter(phone__icontains = phone)
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                plans = plans.filter(start_date__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                plans = plans.filter(end_date__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")


        search_filter = filters.SearchFilter()
        plans = search_filter.filter_queryset(request, plans, self)

        ordering_filter = filters.OrderingFilter()
        plans = ordering_filter.filter_queryset(request, plans, self)

        if not plans.ordered:
            plans = plans.order_by('-id')


        serializer = ContactListSerializer(plans, many=True)
        
        data = {
            "info":serializer.data
        }


        template = get_template('pdf/contact_us_report.html')
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
            report_name = "contact_us_report"
            gcs_folder_name = "media/reports"
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
    


class CSVContactUsReportView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "contact_us_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', "last_name","email","phone"]
    ordering_fields = ['first_name', "last_name","email",'created_at', 'id'] 
    def get(self, request, format=None):
        
        plans = ContactUs.objects.all()
        
        first_name = request.query_params.get('first_name')
        if first_name:
            plans = plans.filter(first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            plans = plans.filter(last_name__icontains = last_name)


        email = request.query_params.get('email')
        if email:
            plans = plans.filter(email__icontains = email)

        
        phone = request.query_params.get('phone')
        if phone:
            plans = plans.filter(phone__icontains = phone)
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                plans = plans.filter(start_date__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                plans = plans.filter(end_date__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")


        search_filter = filters.SearchFilter()
        plans = search_filter.filter_queryset(request, plans, self)

        ordering_filter = filters.OrderingFilter()
        plans = ordering_filter.filter_queryset(request, plans, self)

        if not plans.ordered:
            plans = plans.order_by('-id')
        
        serializer = ContactListSerializer(plans, many=True)
        
        lis = []
        
        lis.append({
                "first_name":"Contact Us Report",
                "last_name":'',
                "email":'',
                "phone":'',
                "ordered_courses":'',
                "total_amount":'',
                "start_date":'',
                "end_date":'',
                "subscription_type":'',
                "subscription_status":'',
                
                "created_at":'',
            })
        
        lis.append({
                "first_name":"",
                "last_name":'',
                "email":'',
                "phone":'',
                "ordered_courses":'',
                "total_amount":'',
                "start_date":'',
                "end_date":'',
                "subscription_type":'',
                "subscription_status":'',
                
                "created_at":'',
            })
        
        lis.append({
                "first_name":"",
                "last_name":'',
                "email":'',
                "phone":'',
                "ordered_courses":'',
                "total_amount":'',
                "start_date":'',
                "end_date":'',
                "subscription_type":'',
                "subscription_status":'',
                
                "created_at":'',
            })
        
        lis.append({
                "first_name":"First Name",
                "last_name":'Last Name',
                "email":'Email',
                "phone":'Phone',
                "ordered_courses":'Message',
                "total_amount":'Created At',
                "start_date":'',
                "end_date":'',
                "subscription_type":'',
                "subscription_status":'',
                "created_at":'',
            })
        for order in serializer.data:

            
            lis.append({
                "first_name":order['first_name'],
                "last_name":order['last_name'],
                "email":order['email'],
                "phone":order['phone'],
                "ordered_courses":order['message'],
                "total_amount":order['created_at'],
                "start_date":"",
                "end_date":"",
                "subscription_type": "",
                "subscription_status":"",
                "created_at":"",
            })

        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            # GCS file naming logic
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "contact_us_report"
            gcs_folder_name = "media/reports"
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




class GetStudentPerformanceReportView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_performance_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    search_fields = ['user__first_name','user__last_name',"user__email","course__name"]
    ordering_fields = ['user__first_name','user__last_name',"user__email","course__name"]
    def get(self, request, format=None):
        
        topics = UserCourses.objects.only("id","user","course").select_related("user","course").filter(paid = True)
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_name = request.query_params.get('course_name')
        if course_name:
            topics = topics.filter(course__name__icontains =course_name)

        first_name = request.query_params.get('first_name')
        if first_name:
            topics = topics.filter(user__first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            topics = topics.filter(user__last_name__icontains = last_name)


        email = request.query_params.get('email')
        if email:
            topics = topics.filter(user__email__icontains = email)

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

        topics = topics.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = StudentPerformaceReportSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class GetStudentPerformanceReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_performance_report_pdf",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    search_fields = ['user__first_name','user__last_name',"user__email","course__name"]
    ordering_fields = ['user__first_name','user__last_name',"user__email","course__name"]
    def get(self, request, format=None):
        
        topics = UserCourses.objects.only("id","user","course").select_related("user","course").filter(paid = True)
        
        first_name = request.query_params.get('first_name')
        if first_name:
            topics = topics.filter(user__first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            topics = topics.filter(user__last_name__icontains = last_name)


        email = request.query_params.get('email')
        if email:
            topics = topics.filter(user__email__icontains = email)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_name = request.query_params.get('course_name')
        if course_name:
            topics = topics.filter(course__name__icontains =course_name)

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

        topics = topics.order_by('-id')

        serializer = StudentPerformaceReportSerializer(topics, many=True)
    
        data = {
                    "user_data":serializer.data
                }
        

        template = get_template('pdf/student_performance_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "student_performance_report"
            gcs_folder_name = "media/reports"
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
    


class GetStudentPerformanceReportExcelView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_performance_report_excel",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    search_fields = ['user__first_name','user__last_name',"user__email","course__name"]
    ordering_fields = ['user__first_name','user__last_name',"user__email","course__name"]
    def get(self, request, format=None):
        
        topics = UserCourses.objects.only("id","user","course").select_related("user","course").filter(paid = True)
        
        first_name = request.query_params.get('first_name')
        if first_name:
            topics = topics.filter(user__first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            topics = topics.filter(user__last_name__icontains = last_name)


        email = request.query_params.get('email')
        if email:
            topics = topics.filter(user__email__icontains = email)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_name = request.query_params.get('course_name')
        if course_name:
            topics = topics.filter(course__name__icontains =course_name)

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
            
        topics = topics.order_by('-id')

        serializer = StudentPerformaceReportSerializer(topics, many=True)
        
        lis = []
        
        lis.append({
                "name":"Student Performance Report",
                "email":'',
                "subject":'',
                "phone":'',
                "category":'',
                "type":'',
                "Chapter":'',
                "Topic":'',
                "total_watched_videos":'',
                "total_time_spend":'',
            })

        
        lis.append({
                "name":"",
                "email":'',
                "subject":'',
                "phone":'',
                "category":'',
                "type":'',
                "Chapter":'',
                "Topic":'',
                "total_watched_videos":'',
                "total_time_spend":'',
            })
        
        
        lis.append({
                "name":"First Name",
                "email":'Last Name',
                "subject":'Email',
                "phone":'Phone',
                "category":'Category',
                "type":'Student Type',
                "Chapter":'Reference ID',
                "Topic":'Course',
                "total_watched_videos":'Videos Watched',
                "total_time_spend":'Watch Time',
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['user_detail']['first_name'],
                "email":order_info['user_detail']['last_name'],
                "subject":order_info['user_detail']['email'],
                "phone":order_info['user_detail']['phone1'],
                "category":order_info['user_detail']['category'],
                "type":order_info['user_detail']['student_type'],
                "Chapter":order_info['user_detail']['reference_id'],
                "Topic":order_info['course_detail']['name'],
                "total_watched_videos":str(order_info['performance_report']['total_video_watched']),
                "total_time_spend":convert_minutes(order_info['performance_report']['watch_time']),
                
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "student_registration_report"
            gcs_folder_name = "media/reports"
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



class GetStudentNotesReportlistingView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_activity_report_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email","course__name"]
    ordering_fields = ['user__first_name','user__last_name',"user__email","course__name"]
    def get(self, request, uid=None):
        
        
        topics = Notes.objects.all()
        
        first_name = request.query_params.get('first_name')
        if first_name:
            topics = topics.filter(user__first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            topics = topics.filter(user__last_name__icontains = last_name)


        email = request.query_params.get('email')
        if email:
            topics = topics.filter(user__email__icontains = email)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_name = request.query_params.get('course_name')
        if course_name:
            topics = topics.filter(course__name__icontains =course_name)

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


        topics = topics.values('user','user__first_name','user__last_name','user__email','user__category','user__phone1','user__reference_id', "user__student_type",'course','course__name').annotate(
            notes_count=Count('id')
        ).order_by('user', 'course')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(topics, request, view=self)
        serializer = StudentNoteListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class GetAdminNotesListingReportPDFView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_study_plan_report_pdf",
                            [SuperAdmin]
                        )]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email","course__name"]
    ordering_fields = ['user__first_name','user__last_name',"user__email","course__name"]
    def get(self, request):
        
        topics = Notes.objects.all()
        
        first_name = request.query_params.get('first_name')
        if first_name:
            topics = topics.filter(user__first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            topics = topics.filter(user__last_name__icontains = last_name)


        email = request.query_params.get('email')
        if email:
            topics = topics.filter(user__email__icontains = email)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_name = request.query_params.get('course_name')
        if course_name:
            topics = topics.filter(course__name__icontains =course_name)

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


        topics = topics.values('user','user__first_name','user__last_name','user__email','user__category','user__phone1','user__reference_id', "user__student_type",'course','course__name').annotate(
            notes_count=Count('id')
        ).order_by('user', 'course')

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
            gcs_folder_name = "media/reports"
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
    search_fields = ['user__first_name',"user__last_name","user__email","course__name"]
    ordering_fields = ['user__first_name','user__last_name',"user__email","course__name"]
    def get(self, request):
        
        topics = Notes.objects.all()
        
        first_name = request.query_params.get('first_name')
        if first_name:
            topics = topics.filter(user__first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            topics = topics.filter(user__last_name__icontains = last_name)


        email = request.query_params.get('email')
        if email:
            topics = topics.filter(user__email__icontains = email)


        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        
        course_name = request.query_params.get('course_name')
        if course_name:
            topics = topics.filter(course__name__icontains =course_name)

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


        topics = topics.values('user','user__first_name','user__last_name','user__email','user__category','user__phone1','user__reference_id', "user__student_type",'course','course__name').annotate(
            notes_count=Count('id')
        ).order_by('user', 'course')

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
                "count":chapter_data['notes_count']
            })

            
            
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "notes_report"
            gcs_folder_name = "media/reports"
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


class GetAdminUserNoteReportView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_user_notes_report_pdf",
                            [SuperAdmin]
                        )]
    def get(self, request, uid, sid):
        
        user = User.objects.get(id = uid)
        
        user_notes = Notes.objects.filter(course_id=sid, user = user)
        subject = Course.objects.filter(id=sid).first()
        if subject is None:
            raise ValidationError("Invalid Course ID")

        serializer = UserNoteDetailSerializer(user_notes, many=True)


        data = {
                    "user_notes":serializer.data,
                    'username':user.first_name +' '+user.last_name,
                    'user_id':user.email,
                    "course":subject.name
                }
        
        return success_response(
            message="Success",
            data=data,
            status_code=status.HTTP_200_OK
        )
    


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
    ordering_fields = ['user__first_name','user__last_name',"user__email"]
    def get(self, request, uid=None):
        
        topics = UserLoginActivity.objects.filter(user_id = uid, user__role = User.Student)
        
        first_name = request.query_params.get('first_name')
        if first_name:
            topics = topics.filter(user__first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            topics = topics.filter(user__last_name__icontains = last_name)


        email = request.query_params.get('email')
        if email:
            topics = topics.filter(user__email__icontains = email)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                topics = topics.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                topics = topics.filter(created_at__lte=end_datetime)
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
    


class GetStudentActivityPDFReportView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_activity_pdf_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    ordering_fields = ['user__first_name','user__last_name',"user__email"]
    def get(self, request, uid=None):
        
        user = User.objects.filter(id = uid).first()
        topics = UserLoginActivity.objects.filter(user_id = uid, user__role = User.Student)
        
        first_name = request.query_params.get('first_name')
        if first_name:
            topics = topics.filter(user__first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            topics = topics.filter(user__last_name__icontains = last_name)


        email = request.query_params.get('email')
        if email:
            topics = topics.filter(user__email__icontains = email)
            
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                topics = topics.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                topics = topics.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)

        if not topics.ordered:
            topics = topics.order_by('-id')


        serializer = StudentLoginActivitySerializer(topics, many=True)

        data = {
                    "user_data":serializer.data,
                    "user":user
                }
        

        template = get_template('pdf/user_login_activity_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "student_login_activity_report"
            gcs_folder_name = "media/reports"
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
    


class GetStudentActivityExcelReportView(APIView):
    renderer_classes = [ReportsRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_activity_excel_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    ordering_fields = ['user__first_name','user__last_name',"user__email"]
    def get(self, request, uid=None):
        
        user = User.objects.filter(id = uid).first()
        topics = UserLoginActivity.objects.filter(user_id = uid, user__role = User.Student)
        
        first_name = request.query_params.get('first_name')
        if first_name:
            topics = topics.filter(user__first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            topics = topics.filter(user__last_name__icontains = last_name)


        email = request.query_params.get('email')
        if email:
            topics = topics.filter(user__email__icontains = email)
            
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                topics = topics.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                topics = topics.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        topics = search_filter.filter_queryset(request, topics, self)

        if not topics.ordered:
            topics = topics.order_by('-id')


        serializer = StudentLoginActivitySerializer(topics, many=True)

        data = {
                    "user_data":serializer.data,
                    "user":user
                }
        
        
        lis = []
        
        lis.append({
                "name":"Student Login Activty Report",
                "last_name":"",
                "email":'',
                "phone":'',
                "category":'',
                "type":'',
                "reference":'',
                "course":'',
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
                "count":''
            })
        
        lis.append({
                "name":"Name",
                "last_name":user.first_name +' '+user.last_name,
                "email":'',
                "phone":'Email',
                "category":user.email,
                "type":'',
                "reference":'',
                "course":'',
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
                "count":''
            })
        
        lis.append({
                "name":"Login IP",
                "last_name":"Device ID",
                "email":'Country',
                "phone":'Device Type',
                "category":'Created At',
                "type":'',
                "reference":'',
                "course":'',
                "count":''
            })
        
        
        for chapter_data in serializer.data:
            lis.append({
                "name":chapter_data['login_IP'],
                "last_name":chapter_data['device_id'],
                "email":chapter_data['country'],
                "phone":chapter_data['device_type'],
                "category":chapter_data['created_at'],
                "type":"",
                "reference":"",
                "course":"",
                "count":""
            })

            
            
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "student_login_activity_report"
            gcs_folder_name = "media/reports"
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