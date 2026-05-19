from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from courses.serializers import *
from user_study.models import *
from courses.renderers import CourseRenderer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from mini_lms.utils import *
from rolepermissions import roles
from mini_lms.roles import *
from rest_framework.exceptions import ValidationError
from mini_lms.permissions import RoleOrPermissionCheck
from mini_lms.pagination import CustomPageNumberPagination
from rest_framework import filters
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import get_template
import pandas as pd
import tempfile
import re
from google.cloud import storage
from google.oauth2 import service_account
info = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
credentials = service_account.Credentials.from_service_account_info(info)
client = storage.Client(credentials=credentials, project=credentials.project_id)
from datetime import datetime,timezone, timedelta



class ChapterListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_listing_pdf_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name',"description"]
    ordering_fields = ['name', 'created_at', 'id', 'status',"description"] 
    def get(self, request, format=None):
        
        chapters = Chapters.objects.all()

        name = request.query_params.get('name')
        if name:
            chapters = chapters.filter(name__icontains = name)

        description = request.query_params.get('description')
        if description:
            chapters = chapters.filter(description__icontains = description)

        active = request.query_params.get('status')
        if active:
            chapters = chapters.filter(status=active)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                chapters = chapters.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                chapters = chapters.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")

        
        search_filter = filters.SearchFilter()
        chapters = search_filter.filter_queryset(request, chapters, self)

        ordering_filter = filters.OrderingFilter()
        chapters = ordering_filter.filter_queryset(request, chapters, self)

        if not chapters.ordered:
            chapters = chapters.order_by('-id')
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(chapters, request, view=self)
        serializer = ChaptersSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class ExportChapterListingPDFView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_listing_excel_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name',"description"]
    ordering_fields = ['name', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        
        chapters = Chapters.objects.all()

        name = request.query_params.get('name')
        if name:
            chapters = chapters.filter(name__icontains = name)

        description = request.query_params.get('description')
        if description:
            chapters = chapters.filter(description__icontains = description)


        active = request.query_params.get('status')
        if active:
            chapters = chapters.filter(status=active)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                chapters = chapters.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                chapters = chapters.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")

        
        search_filter = filters.SearchFilter()
        chapters = search_filter.filter_queryset(request, chapters, self)

        ordering_filter = filters.OrderingFilter()
        chapters = ordering_filter.filter_queryset(request, chapters, self)

        if not chapters.ordered:
            chapters = chapters.order_by('-id')
        
        serializer = ChaptersSerializer(chapters, many=True)

        data = {
                    "user_data":serializer.data
                }
        
        template = get_template('pdf/chapter_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "chapter_report"
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

    

class ExportChapterListingExcelView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name',"description"]
    ordering_fields = ['name', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        
        chapters = Chapters.objects.all()

        name = request.query_params.get('name')
        if name:
            chapters = chapters.filter(name__icontains = name)

        description = request.query_params.get('description')
        if description:
            chapters = chapters.filter(description__icontains = description)

        active = request.query_params.get('status')
        if active:
            chapters = chapters.filter(status=active)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                chapters = chapters.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                chapters = chapters.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")

        
        search_filter = filters.SearchFilter()
        chapters = search_filter.filter_queryset(request, chapters, self)

        ordering_filter = filters.OrderingFilter()
        chapters = ordering_filter.filter_queryset(request, chapters, self)

        if not chapters.ordered:
            chapters = chapters.order_by('-id')

        serializer = ChaptersSerializer(chapters, many=True)

        lis = []
        
        lis.append({
                "name":"Chapters Report",
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "Topic":'Description',
                "total_videos":'Is Active?',
                "total_watched_videos":'Created At',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "Topic":order_info['description'],
                "total_videos":order_info['status'],
                "total_watched_videos":order_info['created_at'],
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "chapters_report"
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
    


class GetVideoListView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        chapter = Videos.objects.filter(status=True, is_uploaded = True, is_completed = True).order_by("-id")
        serializer = VideoListSerializer(chapter, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class GetEbookListView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        chapter = ChapterBooks.objects.filter(status=True).order_by("-id")
        serializer = ChapterBooksSerializer(chapter, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    
    

class ChapterListView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        chapter = Chapters.objects.filter(status=True).order_by("-id")
        chapter_type = request.query_params.get('chapter_type')
        if chapter_type:
            chapter = chapter.filter(chapter_type=chapter_type)

        serializer = ChapterListSerializer(chapter, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class ViewChapterView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_listing",
                            [SuperAdmin]
                        )]
    def get(self, request,  cid , format=None):
        chapter = Chapters.objects.filter(id=cid).first()
        if chapter is None:
            raise ValidationError("Invalid Chapter ID!")
        
        serializer = ViewChapterDetailSerializer(chapter)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class CreateChapterView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_chapter",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateChapterSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Chapter Created Successfully", data=ViewChapterDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class AssignChapterLectureView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter",
                            [SuperAdmin]
                        )]
    def post(self, request,  format=None):
        serializer = AssignChapterLectureSerializer(data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Chapter Lecture Updated Successfully", data=[], status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class EditChapterView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        chapter = Chapters.objects.filter(id=cid).first()
        if chapter is None:
            raise ValidationError("Invalid Chapter ID!")
        
        serializer = EditChapterSerializer(chapter, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Chapter Updated Successfully", data=ViewChapterDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UpdateChapterStatusView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        chapter = Chapters.objects.filter(id=cid).first()
        if chapter is None:
            raise ValidationError("Invalid Chapter ID!")
        
        serializer = ChangeChapterstatusSerializer(chapter, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Chapter Status Updated Successfully", data=ViewChapterDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class DeleteChapterView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_chapter",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = Chapters.objects.get(id = cid)
            course.delete()
            return success_response(message="Chapter Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except Chapters.DoesNotExist:
            return error_response(message="Chapter not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        


class VideosListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_video_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name',"description"]
    ordering_fields = ['name', 'created_at', 'id', 'status',"description"] 
    def get(self, request, format=None):
        
        videos = Videos.objects.all()
        
        name = request.query_params.get('name')
        if name:
            videos = videos.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            videos = videos.filter(status=active)

        description = request.query_params.get('description')
        if description:
            videos = videos.filter(description__icontains = description)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                videos = videos.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                videos = videos.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")

        search_filter = filters.SearchFilter()
        videos = search_filter.filter_queryset(request, videos, self)

        ordering_filter = filters.OrderingFilter()
        videos = ordering_filter.filter_queryset(request, videos, self)

        if not videos.ordered:
            videos = videos.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(videos, request, view=self)
        serializer = VideosSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class ExportVideoListingPDFView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_video_listing_pdf_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name',"description"]
    ordering_fields = ['name', 'created_at', 'id', 'status',"description"] 
    def get(self, request, format=None):
        
        videos = Videos.objects.all()
        
        name = request.query_params.get('name')
        if name:
            videos = videos.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            videos = videos.filter(status=active)

        description = request.query_params.get('description')
        if description:
            videos = videos.filter(description__icontains = description)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                videos = videos.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                videos = videos.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")

        search_filter = filters.SearchFilter()
        videos = search_filter.filter_queryset(request, videos, self)

        ordering_filter = filters.OrderingFilter()
        videos = ordering_filter.filter_queryset(request, videos, self)

        if not videos.ordered:
            videos = videos.order_by('-id')

        serializer = VideosSerializer(videos, many=True)

        data = {
                    "user_data":serializer.data
                }
        
        template = get_template('pdf/video_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "video_report"
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

    

class ExportVideoListingExcelView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_video_listing_excel_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name',"description"]
    ordering_fields = ['name', 'created_at', 'id', 'status',"description"] 
    def get(self, request, format=None):
        
        videos = Videos.objects.all()
        
        name = request.query_params.get('name')
        if name:
            videos = videos.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            videos = videos.filter(status=active)

        description = request.query_params.get('description')
        if description:
            videos = videos.filter(description__icontains = description)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                videos = videos.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                videos = videos.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")

        search_filter = filters.SearchFilter()
        videos = search_filter.filter_queryset(request, videos, self)

        ordering_filter = filters.OrderingFilter()
        videos = ordering_filter.filter_queryset(request, videos, self)

        if not videos.ordered:
            videos = videos.order_by('-id')

        serializer = VideosSerializer(videos, many=True)

        lis = []
        
        lis.append({
                "name":"Video Report",
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "Topic":'Description',
                "total_videos":'Is Active?',
                "total_watched_videos":'Created At',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "Topic":order_info['description'],
                "total_videos":order_info['status'],
                "total_watched_videos":order_info['created_at'],
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
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

    

class ViewVideoDetailView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_video_listing",
                            [SuperAdmin]
                        )]
    def get(self, request,  cid , format=None):
        video = Videos.objects.filter(id=cid).first()
        if video is None:
            raise ValidationError("Invalid Video ID!")
        
        serializer = ViewVideoDetailSerializer(video)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class UploadVideoView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_chapter_video",
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):

        info = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
        credentials = service_account.Credentials.from_service_account_info(info)

        storage_client = storage.Client(credentials=credentials, project=credentials.project_id)

        bucket_name = settings.GS_BUCKET_NAME
        bucket = storage_client.bucket(bucket_name)
        bucket.cors = [
            {
                "origin": ["*"],
                "responseHeader": [
                    "Content-Type",
                    "x-goog-resumable"],
                "method": ['PUT', 'POST'],
                "maxAgeSeconds": 36000
            }
        ]
        bucket.patch()

        current_GMT = time.gmtime()
        ts = calendar.timegm(current_GMT)
        unique_file_name = f"{ts}.mp4"
        
        path = "mini_lms/videos"
        blob_path = f"media/{path}/{unique_file_name}"
        blob = bucket.blob(blob_path)

        content_type = 'video/mp4'

        try:
            # Generate the signed URL
            signed_url = blob.generate_signed_url(
                version='v4',
                expiration=36000, # 1 hour is usually plenty for an upload start
                method='PUT',
                content_type=content_type
            )

            # This is the final URL where the file will live
            public_url = f"https://storage.googleapis.com/{bucket_name}/{blob_path}"

            return success_response(message="Video Created Successfully", data={
                'signed_url': signed_url,
                "video_file_url": path+"/"+unique_file_name
            }, status_code=status.HTTP_200_OK)
        
        except Exception as e:
            return error_response(message="failed", data = str(e), status_code=status.HTTP_400_BAD_REQUEST)
            

class UploadVideoView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_chapter_video",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateVideoSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Video Created Successfully", data=ViewVideoDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class MarkVideoUploadCompleteView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter_video",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        video = Videos.objects.filter(id=cid).first()
        if video is None:
            raise ValidationError("Invalid Video ID!")
        
        serializer = MarkVideoUploadCompleteSerializer(video, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Video Updated Successfully", data=ViewVideoDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateVideoView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter_video",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        video = Videos.objects.filter(id=cid).first()
        if video is None:
            raise ValidationError("Invalid Video ID!")
        
        serializer = EditVideoserializer(video, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Video Updated Successfully", data=ViewVideoDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UpdateVideoStatusView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter_video",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        video = Videos.objects.filter(id=cid).first()
        if video is None:
            raise ValidationError("Invalid Video ID!")
        
        serializer = ChangeVideostatusSerializer(video, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Video Upload Completed Successfully", data=ViewVideoDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class DeleteVideoView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_chapter_video",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            video = Videos.objects.get(id = cid)
            video.delete()
            return success_response(message="Video Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except Videos.DoesNotExist:
            return error_response(message="Video not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)


class TagsListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "tags_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        category = Tags.objects.all()
        
        name = request.query_params.get('name')
        if name:
            category = category.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(category, request, view=self)
        serializer = TagsListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ExportTagsListingPDFView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "tags_listing_pdf_report",
                            [SuperAdmin]
                        )]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        category = Tags.objects.all()
        
        name = request.query_params.get('name')
        if name:
            category = category.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        serializer = TagsListingSerializer(category, many=True)

        data = {
                    "user_data":serializer.data
                }
        
        template = get_template('pdf/tag_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "tags_report"
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



class ExportTagsListingExcelView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "tags_listing_excel_report",
                            [SuperAdmin]
                        )]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        category = Tags.objects.all()
        
        name = request.query_params.get('name')
        if name:
            category = category.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
        
        serializer = TagsListingSerializer(category, many=True)

        lis = []
        
        lis.append({
                "name":"Tags Report",
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "Topic":'Is Active?',
                "total_videos":'Created At',
                "total_watched_videos":'',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "Topic":order_info['status'],
                "total_videos":order_info['created_at'],
                "total_watched_videos":"",
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "tags_report"
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


class CategoryListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "category_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name',"description"]
    ordering_fields = ['name', 'created_at', 'id', 'status',"description"] 
    def get(self, request, format=None):
        category = Categories.objects.filter(parent__isnull = True)
        
        name = request.query_params.get('name')
        if name:
            category = category.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            print("active",active)
            category = category.filter(status=active)

        description = request.query_params.get('description')
        if description:
            category = category.filter(description__icontains = description)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(category, request, view=self)
        serializer = CategorySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class ExportCategoryListingPDFView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "category_listing_pdf_report",
                            [SuperAdmin]
                        )]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name',"description"]
    ordering_fields = ['name', 'created_at', 'id', 'status',"description"] 
    def get(self, request, format=None):
        category = Categories.objects.filter(parent__isnull = True)
        
        name = request.query_params.get('name')
        if name:
            category = category.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)

        description = request.query_params.get('description')
        if description:
            category = category.filter(description__icontains = description)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        serializer = CategorySerializer(category, many=True)
        
        data = {
                    "user_data":serializer.data
                }
        
        template = get_template('pdf/category_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "category_report"
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


class ExportCategoryListingExcelView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "category_listing_excel_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name',"description"]
    ordering_fields = ['name', 'created_at', 'id', 'status',"description"] 
    def get(self, request, format=None):
        category = Categories.objects.filter(parent__isnull = True)
        
        name = request.query_params.get('name')
        if name:
            category = category.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)

        description = request.query_params.get('description')
        if description:
            category = category.filter(description__icontains = description)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        
        serializer = CategorySerializer(category, many=True)

        lis = []
        
        lis.append({
                "name":"Category Report",
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "Topic":'Description',
                "total_videos":'Is Active?',
                "total_watched_videos":'Created At',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "Topic":order_info['description'],
                "total_videos":order_info['status'],
                "total_watched_videos":order_info['created_at'],
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "category_report"
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


class SubCategoryListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "subcategory_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name',"description","parent__name"]
    ordering_fields = ['name', 'created_at', 'id', 'status',"description","parent__name"] 
    def get(self, request, format=None):
        category = Categories.objects.filter(parent__isnull = False)
        
        name = request.query_params.get('name')
        if name:
            category = category.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)

        parent = request.query_params.get('parent')
        if parent:
            category = category.filter(parent__name__icontains = parent)

        description = request.query_params.get('description')
        if description:
            category = category.filter(description__icontains = description)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(category, request, view=self)
        serializer = CategorySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ExportSubCategoryListingPDFView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "subcategory_listing_pdf_report",
                            [SuperAdmin]
                        )]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name',"description","parent__name"]
    ordering_fields = ['name', 'created_at', 'id', 'status',"description","parent__name"] 
    def get(self, request, format=None):
        category = Categories.objects.filter(parent__isnull = False)
        
        name = request.query_params.get('name')
        if name:
            category = category.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)

        parent = request.query_params.get('parent')
        if parent:
            category = category.filter(parent__name__icontains = parent)

        description = request.query_params.get('description')
        if description:
            category = category.filter(description__icontains = description)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        serializer = CategorySerializer(category, many=True)
        
        data = {
                    "user_data":serializer.data
                }
        
        template = get_template('pdf/subcategory_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "subcategory_report"
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


class ExportSubCategoryListingExcelView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "subcategory_listing_excel_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name',"description","parent__name"]
    ordering_fields = ['name', 'created_at', 'id', 'status',"description","parent__name"] 
    def get(self, request, format=None):
        category = Categories.objects.filter(parent__isnull = False)
        
        name = request.query_params.get('name')
        if name:
            category = category.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)

        parent = request.query_params.get('parent')
        if parent:
            category = category.filter(parent__name__icontains = parent)

        description = request.query_params.get('description')
        if description:
            category = category.filter(description__icontains = description)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        
        serializer = CategorySerializer(category, many=True)

        lis = []
        
        lis.append({
                "name":"SubCategory Report",
                "parent":"",
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "parent":"",
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "parent":"Parent Category",
                "Topic":'Description',
                "total_videos":'Is Active?',
                "total_watched_videos":'Created At',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "parent":order_info['parent']['name'],
                "Topic":order_info['description'],
                "total_videos":order_info['status'],
                "total_watched_videos":order_info['created_at'],
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "subcategory_report"
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


    
class CreateTagsView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_tag",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateTagsSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Tag Created Successfully", data=TagsListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class EditTagsView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_tag",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = Tags.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Tag ID!")
        
        serializer = EditTagsSerializer(category, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Tag Updated Successfully", data=TagsListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateTagsStatusView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_tag",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = Tags.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Tag ID!")
        
        serializer = ChangeTagStatusSerializer(category, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Tag Status Updated Successfully", data=TagsListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteTagsView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_Tag",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = Tags.objects.get(id = cid)
            course.delete()
            return success_response(message="Tags Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except Tags.DoesNotExist:
            return error_response(message="Tags not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        

class CreateCategoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_category",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateCategorySerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Category Created Successfully", data=CategorySerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class EditCategoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_category",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = Categories.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Category ID!")
        
        serializer = EditCategorySerializer(category, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Category Updated Successfully", data=CategorySerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class CreateSubCategoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_category",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateSubCategorySerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Category Created Successfully", data=CategorySerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class EditSubCategoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_category",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = Categories.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Category ID!")
        
        serializer = EditSubCategorySerializer(category, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Category Updated Successfully", data=CategorySerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
    

class UpdateCategoryStatusView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_category",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = Categories.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Category ID!")
        
        serializer = ChangeCategoryStatusSerializer(category, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Category Status Updated Successfully", data=CategorySerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteCategoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_category",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = Categories.objects.get(id = cid)
            course.delete()
            return success_response(message="Category Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except Categories.DoesNotExist:
            return error_response(message="Category not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        


class CourseListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "course_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'id', 'status',"level","price"] 
    def get(self, request, format=None):
        
        course = Course.objects.all()
        
        name = request.query_params.get('name')
        if name:
            chapters = chapters.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            chapters = chapters.filter(status=active)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                chapters = chapters.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                chapters = chapters.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        course = search_filter.filter_queryset(request, course, self)

        ordering_filter = filters.OrderingFilter()
        course = ordering_filter.filter_queryset(request, course, self)

        if not course.ordered:
            course = course.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(course, request, view=self)
        serializer = CourseSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class ViewCourseDetailView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "course_listing",
                            [SuperAdmin]
                        )]
    def get(self, request,  cid , format=None):
        course = Course.objects.filter(id=cid).first()
        if course is None:
            raise ValidationError("Invalid Course ID!")
        
        serializer = ViewCourseDetailSerializer(course)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class CreateCourseView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_course",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateCourseSerializer(data = request.data,context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Course Created Successfully", data=CourseDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class EditCourseView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_category",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        course = Course.objects.filter(id=cid).first()
        if course is None:
            raise ValidationError("Invalid Course ID!")
        
        serializer = EditCourseSerializer(course, data = request.data, partial=True, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Course Updated Successfully", data=CourseDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateCourseStatusView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_course",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        course = Course.objects.filter(id=cid).first()
        if course is None:
            raise ValidationError("Invalid Course ID!")
        
        serializer = ChangeCourseStatusSerializer(course, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Course Status Updated Successfully", data=CourseDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteCourseView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_course",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = Course.objects.get(id = cid)
            course.delete()
            return success_response(message="Course Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return error_response(message="Course not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        

class CategoryListView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        subject = Categories.objects.filter(status=True, parent__isnull=True).order_by("-id")
        serializer = CategoryListSerializer(subject, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class SubCategoryListView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, cid=None):
        subject = Categories.objects.filter(status=True, parent_id = cid).order_by("-id")
        serializer = CategoryListSerializer(subject, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class SubCategoryListDetailView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, cid=None):
        subject = Categories.objects.filter(status=True, parent__isnull=False).order_by("-id")
        serializer = CategoryListSerializer(subject, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class TagsListView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, cid=None):
        subject = Tags.objects.filter(status=True).order_by("-id")
        serializer = CourseTagsSerializer(subject, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class AssignChapterCourseView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_course",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        course = Course.objects.filter(id=cid).first()
        if course is None:
            raise ValidationError("Invalid Course ID!")
        
        serializer = AssignChapterCourseSerializer(course, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Chapter Assigned Successfully", data=ViewCourseDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)



class ChapterBookListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_book_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        
        chapters = ChapterBooks.objects.all()
        
        name = request.query_params.get('name')
        if name:
            chapters = chapters.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            chapters = chapters.filter(status=active)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                chapters = chapters.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                chapters = chapters.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        chapters = search_filter.filter_queryset(request, chapters, self)

        ordering_filter = filters.OrderingFilter()
        chapters = ordering_filter.filter_queryset(request, chapters, self)

        if not chapters.ordered:
            chapters = chapters.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(chapters, request, view=self)
        serializer = ChapterBooksSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class ExportEbookListingPDFView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_book_listing_pdf_report",
                            [SuperAdmin]
                        )]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        category = ChapterBooks.objects.all()
        
        name = request.query_params.get('name')
        if name:
            category = category.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)

        # description = request.query_params.get('description')
        # if description:
        #     category = category.filter(description__icontains = description)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        serializer = ChapterBooksSerializer(category, many=True)
        
        data = {
                    "user_data":serializer.data
                }
        
        template = get_template('pdf/ebook_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "ebook_report"
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


class ExportEbookListingExcelView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_book_listing_excel_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        category = ChapterBooks.objects.all()
        
        name = request.query_params.get('name')
        if name:
            category = category.filter(name__icontains = name)

        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)

        # description = request.query_params.get('description')
        # if description:
        #     category = category.filter(description__icontains = description)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        
        serializer = ChapterBooksSerializer(category, many=True)

        lis = []
        
        lis.append({
                "name":"Ebook Report",
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })

        
        lis.append({
                "name":"",
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        lis.append({
                "name":"Name",
                "total_videos":'Is Active?',
                "total_watched_videos":'Created At',
                "total_time_spend":''
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['name'],
                "total_videos":order_info['status'],
                "total_watched_videos":order_info['created_at'],
                "total_time_spend":""
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "ebook_report"
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


class ViewChapterBookView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_book_listing",
                            [SuperAdmin]
                        )]
    def get(self, request,  cid , format=None):
        chapter = ChapterBooks.objects.filter(id=cid).first()
        if chapter is None:
            raise ValidationError("Invalid Book ID!")
        
        serializer = ViewChapterBooksSerializer(chapter)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class ViewBookSignedUrlView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_book_listing",
                            [SuperAdmin]
                        )]
    def get(self, request,  cid , format=None):
        chapter = ChapterBooks.objects.filter(id=cid).first()
        if chapter is None:
            raise ValidationError("Invalid Book ID!")
        
        bucket_name, object_name = parse_gcs_url(chapter.book_file.url)
        expiration_time = datetime.now(timezone.utc) + timedelta(minutes=30)
        bucket = client.get_bucket(settings.GS_BUCKET_NAME_2)
        blob = bucket.blob(object_name)
        
        return success_response(message="Success", data=blob.generate_signed_url(expiration=expiration_time), status_code=status.HTTP_200_OK)
    

class CreateChapterBookView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_chapter_book",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateChapterBookSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Chapter Book Created Successfully", data=ViewChapterBooksSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class EditChapterBookView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter_book",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        chapter = ChapterBooks.objects.filter(id=cid).first()
        if chapter is None:
            raise ValidationError("Invalid Chapter ID!")
        
        serializer = EditChapterBookSerializer(chapter, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Chapter Book Updated Successfully", data=ViewChapterBooksSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UpdateChapterBookStatusView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter_book",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        chapter = ChapterBooks.objects.filter(id=cid).first()
        if chapter is None:
            raise ValidationError("Invalid Chapter ID!")
        
        serializer = ChangeChapterBookstatusSerializer(chapter, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Chapter Status Updated Successfully", data=ViewChapterBooksSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class DeleteChapterBookView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_chapter_book",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = ChapterBooks.objects.get(id = cid)
            course.delete()
            return success_response(message="Chapter Book Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except ChapterBooks.DoesNotExist:
            return error_response(message="Chapter Book not found", data = [], status_code=status.HTTP_204_NO_CONTENT)
        

class ParentCategoryListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        topic = Categories.objects.filter(parent__isnull=True).order_by("-id")
        serializer = CategoriesListSerializer(topic, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class CourseListView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, format=None):
        topic = Course.objects.filter(status=True).order_by("-id")
        serializer = CourseListSerializer(topic, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class CourseChapterListView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, cid, format=None):
        subject = CourseChapters.objects.filter(course_id=cid, chapter__status = True).order_by("order")
        serializer = CourseChapterInfoSerializer(subject, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    



class GenerateUploadSignedUrlView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_course",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = GenerateUploadSignedUrlSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Success", data=user, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class GetTopicHistoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = Topics.objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid Topic ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = TopicsHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    


class GetChaptersHistoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = Chapters.objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid Chapter ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = ChaptersHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    

class GetCourseHistoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = Course.objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid Course ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = CourseHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    


class GetEbookHistoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = ChapterBooks.objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid EBook ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = EbooksHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    

class GetVideoHistoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = Videos.objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid Video ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = VideoHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    




class GetCourseSampleVideoView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, cid =None, format=None):
        category = CourseSampleVideos.objects.filter(course_id = cid).order_by("name")
        serializer = CourseSampleVideoListSerializer(category, many=True)
        return Response({"status":"success",'message':'',"data":serializer.data }, status = status.HTTP_200_OK)
    


class DeleteCourseSampleVideoView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = CourseSampleVideos.objects.get(id = cid)
            course.delete()
            return success_response(message="success", data={}, status_code=status.HTTP_200_OK)
        except CourseSampleVideos.DoesNotExist:
            return error_response(message="failed", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        


class UploadCourseSampleVideoView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        
        serializer = UpdateCoursesSampleVideoSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return success_response(message="Sample video uploaded successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetInstructorListView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, cid =None, format=None):
        category = InstructorProfile.objects.all().order_by("-id")
        serializer = InstructorInfoserializer(category, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class GetCourseListView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, cid =None, format=None):
        category = Course.objects.filter(status = True).order_by("-id")
        serializer = CourseInfoserializer(category, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class GetCourseInstructorsView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, cid =None, format=None):
        category = CourseInstructors.objects.filter(course_id = cid).order_by("-id")
        serializer = CourseInstructorsListSerializer(category, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class AddCourseInstructorsView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = AddCourseInstructorsSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return success_response(message="Instructor added successfully", data={}, status_code=status.HTTP_200_OK)
        
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class DeleteCourseInstructorView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = CourseInstructors.objects.get(id = cid)
            course.delete()
            return success_response(message="Instructor Deleted Successfully", data={}, status_code=status.HTTP_200_OK)
        
        except CourseInstructors.DoesNotExist: 
            return error_response(message="No Instructor found!", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        


class GetRelatedCoursesView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, cid =None, format=None):
        category = FrequentlyBoughtCourse.objects.filter(course_id = cid).order_by("-id")
        serializer = FrequentlyBoughtCourseListSerializer(category, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class AddRelatedCoursesView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        
        serializer = AddRelatedCoursesSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return success_response(message="Course added successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class DeleteRelatedCourseView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        
        try:
            course = FrequentlyBoughtCourse.objects.get(id = cid)
            course.delete()
            return success_response(message="Related Course Deleted Successfully", data={}, status_code=status.HTTP_200_OK)
            
        except FrequentlyBoughtCourse.DoesNotExist:
            return error_response(message="No Record Found!", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        


class GetCoursesFAQsListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, cid=None, format=None):
        
        category = CourseFaqs.objects.filter(course_id = cid).order_by("-id")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(category, request, view=self)
        serializer = CourseFaqsListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    


class AddCourseFAQView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        
        serializer = CreateCourseFaqsSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return success_response(message="FAQ created successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class UpdateCourseFAQView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        
        course = CourseFaqs.objects.filter(id=cid).first()
        if course is None:
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "Invalid FAQ ID"}}, status.HTTP_403_FORBIDDEN)
        
        serializer = UpdateCourseFaqsSerializer(course, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="FAQ updated successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class DeleteCoursFAQeView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        
        try:
            course = CourseFaqs.objects.get(id = cid)
            course.delete()
            return success_response(message="FAQ deleted successfully", data={}, status_code=status.HTTP_200_OK)
            
        except CourseFaqs.DoesNotExist: 
            return error_response(message="No Record Found!", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        

class UpdateFAQStatusView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request, id=None, format=None):
        
        user_info = CourseFaqs.objects.filter(id = id).first()
        if user_info is None:
            return error_response(message="Invalid FAQ ID", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        
        serializer = UpdateFAQStatusSerializer(user_info ,data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="FAQ Status Updated successfully", data={}, status_code=status.HTTP_200_OK)
            
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class TrailCourseListView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "manage_trail_course",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    search_fields = ['course__name']
    ordering_fields = ['course__name', 'created_at', 'id'] 
    def get(self, request, format=None):
        
        chapters = TrailCourses.objects.select_related('course').all()
        
        name = request.query_params.get('name')
        if name:
            chapters = chapters.filter(course__name__icontains = name)

        search_filter = filters.SearchFilter()
        chapters = search_filter.filter_queryset(request, chapters, self)

        ordering_filter = filters.OrderingFilter()
        chapters = ordering_filter.filter_queryset(request, chapters, self)

        if not chapters.ordered:
            chapters = chapters.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(chapters, request, view=self)
        serializer = TrailCoursesSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class CreateTrailCourseView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "manage_trail_course",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateTrailCourseSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Course Added Successfully for trail", data=TrailCoursesSerializer(user,many=True).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteTrailCourseView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "manage_trail_course",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = TrailCourses.objects.get(id = cid)
            course.delete()
            return success_response(message="Trial Course Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except TrailCourses.DoesNotExist:
            return error_response(message="Trial Course not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        


class GetTrailCoursesView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, cid =None, format=None):
        course_list = TrailCourses.objects.values_list("course", flat=True)
        category = Course.objects.filter(status = True, id__in = course_list).order_by("-id")
        serializer = CourseInfoserializer(category, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class GetCourseIncludesView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, cid =None, format=None):
        category = CourseIncludes.objects.filter(course_id = cid).order_by("id")
        serializer = CourseIncludesListSerializer(category, many=True)
        return Response({"status":"success",'message':'',"data":serializer.data }, status = status.HTTP_200_OK)
    


class DeleteCourseIncludesView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = CourseIncludes.objects.get(id = cid)
            course.delete()
            return success_response(message="success", data={}, status_code=status.HTTP_200_OK)
        except CourseIncludes.DoesNotExist:
            return error_response(message="failed", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        


class AddCourseIncludesView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        
        serializer = AddCoursesIncludesSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return success_response(message="Course Include uploaded successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class GetCoursesAnnouncementsListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "get_course_announcements_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['title', 'created_at', 'id', 'status',"course__name","instructor__text_1"] 
    def get(self, request, format=None):
        category = CourseAnnouncements.objects.all()
        
        title = request.query_params.get('title')
        if title:
            category = category.filter(title__icontains = title)

        course_name = request.query_params.get('course')
        if course_name:
            category = category.filter(course__name__icontains = course_name)

        instructor = request.query_params.get('instructor')
        if instructor:
            category = category.filter(instructor__text_1__icontains = instructor)

        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(category, request, view=self)
        serializer = CourseAnnouncementsListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class CourseListingWithInstructorView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        topic = Course.objects.filter(status=True).order_by("-id")
        serializer = CourseListWithInstructorSerializer(topic, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class AddCourseAnnouncementsView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_course_announcements",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        
        serializer = CreateCourseAnnouncementsSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return success_response(message="Course Announcement created successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UpdateCourseAnnouncementView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_course_announcements",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        
        course = CourseAnnouncements.objects.filter(id=cid).first()
        if course is None:
            return error_response(message="Invalid Announcement ID", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
            
        serializer = UpdateCourseAnnouncementSerializer(course, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Announcement updated successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class ViewCourseAnnouncementView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "get_course_announcements_listing",
                            [SuperAdmin]
                        )]
    def get(self, request,  cid , format=None):
        
        course = CourseAnnouncements.objects.filter(id=cid).first()
        if course is None:
            return error_response(message="Invalid Announcement ID", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        serializer = ViewCourseAnnouncementSerializer(course)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
        

class UpdateCourseAnnouncementStatusView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_course_announcements",
                            [SuperAdmin]
                        )]
    def post(self, request, id=None, format=None):
        
        course = CourseAnnouncements.objects.filter(id=id).first()
        if course is None:
            return error_response(message="Invalid Announcement ID", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        
        serializer = UpdateAnnouncementStatusSerializer(course ,data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Announcement Status Updated successfully", data={}, status_code=status.HTTP_200_OK)
            
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class DeleteCoursAnnouncementView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_course_announcements",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = CourseAnnouncements.objects.get(id = cid)
            course.delete()
            return success_response(message="Announcement deleted successfully", data={}, status_code=status.HTTP_200_OK)
            
        except CourseAnnouncements.DoesNotExist: 
            return error_response(message="No Record Found!", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        


class GetCoursesReviewRatingListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "get_course_review_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['title', 'created_at', 'id', 'status',"course__name","user__first_name","user__last_name","approvad"] 
    def get(self, request, format=None):
        category = CourseReviewRating.objects.all().order_by("-id")
        
        course_name = request.query_params.get('course')
        if course_name:
            category = category.filter(course__name__icontains = course_name)

        first_name = request.query_params.get('first_name')
        if first_name:
            category = category.filter(user__first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            category = category.filter(user__last_name__icontains = last_name)

        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)

        approved = request.query_params.get('approved')
        if approved:
            category = category.filter(approved=approved)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(category, request, view=self)
        serializer = CourseReviewRatingListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class ApproveRejectCoursesReviewRatingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_course_review_rating",
                            [SuperAdmin]
                        )]
    def post(self, request, id=None, format=None):
        
        course = CourseReviewRating.objects.filter(id=id).first()
        if course is None:
            return error_response(message="Invalid Review ID", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        
        serializer = ApproveRejectCoursesReviewRatingSerializer(course ,data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Review Status Updated successfully", data={}, status_code=status.HTTP_200_OK)
            
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)