from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from user_study.serializers import *
from user_study.renderers import UserStudyRenderer
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import get_template
import os
from mini_lms.utils import *
import tempfile
from rolepermissions.checkers import has_role
from rest_framework.permissions import IsAuthenticated
from datetime import timedelta 
from django.utils import timezone
import pandas as pd
from mini_lms.permissions import RoleOrPermissionCheck
import json
from google.cloud import storage
from google.oauth2 import service_account
info = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
credentials = service_account.Credentials.from_service_account_info(info)
client = storage.Client(credentials=credentials, project=credentials.project_id)
from mini_lms.pagination import CustomPageNumberPagination
from rest_framework import filters
from django.db.models import Count, Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncYear, TruncWeek

class PurchasedCoursesView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request,format=None):
        
        course_list = UserCourses.objects.filter(user__email = request.user.email, paid = 1).values_list('course', flat=True)
        category = Course.objects.filter(id__in=course_list)
        serializer = OrderCoursesSerializer(category, many=True, context={'user':request.user})

        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)


class GetCurrentCoursesView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request,format=None):
        
        course_list = UserCurrentCourseLearning.objects.filter(user = request.user).first()
        if course_list is not None:
            category = Course.objects.get(id=course_list.course.id)
            serializer = UserCurrentCourseInfoSerializer(category, context={'user':request.user})
            return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
        return success_response(message="Success", data=[], status_code=status.HTTP_200_OK)
    

class UpdateLearningDaysView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        serializer = UpdateLearningDaysSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Learning Days Updated successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    
class MarkCourseStartedView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        serializer = MarkCourseStartedSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Course Started successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetCourseProgressView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request,id=None):
        
        course_list = UserCourses.objects.filter(course_id = id, paid = 1,user = request.user).count()
        if course_list == 0:
            return error_response(message="Invalid Course ID", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        category = Course.objects.filter(id = id).first()
        serializer = CourseProgressSerializer(category, context={'user':request.user})

        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class DashboardCourseChaptersView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, id = None, format=None):
        
        course_list = UserCourses.objects.filter(course_id = id, paid = 1,user = request.user).count()
        if course_list == 0:
            return error_response(message="Invalid Course ID", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        
        course_info = UserCourses.objects.filter(course_id = id, paid = 1,user = request.user).first()

        UserCurrentCourseLearning.objects.update_or_create(
            user=request.user,
            defaults={
                'course_id': id,
            }
        )

        if course_info.trail == True:
            chapters = TrailCourseChapters.objects.filter(trail_course__course_id = id).values_list("chapter", flat=True)
            category = CourseChapters.objects.filter(course_id=id, chapter_id__in = chapters)
            serializer = DashboardCourseChapterListingSerializer(category, many=True, context={'user':request.user})

        else:

            category = CourseChapters.objects.filter(course_id=id)
            serializer = DashboardCourseChapterListingSerializer(category, many=True, context={'user':request.user})

        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class GetVideoReportView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, id = None, format=None):
        
        course_list = UserCourses.objects.filter(course_id = id, paid = 1, user = request.user).count()
        if course_list == 0:
            return error_response(message="Invalid Course ID", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        
        course_info = UserCourses.objects.filter(course_id = id, paid = 1,user = request.user).first()

        if course_info.trail == True:
            chapters = TrailCourseChapters.objects.filter(trail_course__course_id = id).values_list("chapter", flat=True)
            category = CourseChapters.objects.filter(course_id=id, chapter_id__in = chapters)
            serializer = DashboardCourseChapterListingSerializer(category, many=True, context={'user':request.user})

        else:

            category = CourseChapters.objects.filter(course_id=id)
            serializer = CourseVideoReportSerializer(category, many=True, context={'user':request.user})
        total_video_watched = UserLectureProgress.objects.filter( course_id = id, user = request.user).count()
        total_duration_video_watched = UserLectureProgress.objects.filter( course_id = id, user = request.user).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0

        return success_response(message="Success", data={"report_data":serializer.data, "total_video_watched":total_video_watched, "total_duration_video_watched":total_duration_video_watched}, status_code=status.HTTP_200_OK)


class DashboardChapterLecturesView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, id = None, format=None):
        category = ChapterLectures.objects.filter(chapter_id=id)
        serializer = ChapterLectureSerializer(category, many=True, context={'user':request.user})
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class DownloadChapterVideoReportView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, cid = None, format=None):
        course_list = UserCourses.objects.filter(course_id = id, paid = 1, user = request.user).count()
        if course_list == 0:
            return error_response(message="Invalid Course ID", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        
        course_info = UserCourses.objects.filter(course_id = id, paid = 1,user = request.user).first()
        course = Course.objects.get(id = cid)
        if course_info.trail == True:
            chapters = TrailCourseChapters.objects.filter(trail_course__course_id = id).values_list("chapter", flat=True)
            category = CourseChapters.objects.filter(course_id=id, chapter_id__in = chapters)
            serializer = DashboardCourseChapterListingSerializer(category, many=True, context={'user':request.user})

        else:
            category = CourseChapters.objects.filter(course_id=cid)
            serializer = CourseVideoReportSerializer(category, many=True, context={'user':request.user})

        total_video_watched = UserLectureProgress.objects.filter( course_id = cid, user = request.user).count()
        total_duration_video_watched = UserLectureProgress.objects.filter( course_id = cid, user = request.user).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0

        
        result = {
                'video_report': serializer.data,
                'username':request.user.first_name +' '+request.user.last_name,
                'user_id':request.user.email,
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
    
    


class DownloadChapterVideoReportCSVView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, cid = None,  format=None):
        
        course_list = UserCourses.objects.filter(course_id = id, paid = 1, user = request.user).count()
        if course_list == 0:
            return error_response(message="Invalid Course ID", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        
        course_info = UserCourses.objects.filter(course_id = id, paid = 1,user = request.user).first()
        course = Course.objects.get(id = cid)
        if course_info.trail == True:
            chapters = TrailCourseChapters.objects.filter(trail_course__course_id = id).values_list("chapter", flat=True)
            category = CourseChapters.objects.filter(course_id=id, chapter_id__in = chapters)
            serializer = DashboardCourseChapterListingSerializer(category, many=True, context={'user':request.user})

        else:
            category = CourseChapters.objects.filter(course_id=cid)
            serializer = CourseVideoReportSerializer(category, many=True, context={'user':request.user})
            
        total_video_watched = UserLectureProgress.objects.filter( course_id = cid, user = request.user).count()
        total_duration_video_watched = UserLectureProgress.objects.filter( course_id = cid, user = request.user).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0


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
                "email":request.user.first_name +' '+request.user.last_name,
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        lis.append({
                "name":"User ID:",
                "email":request.user.email,
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



class WatchVideoView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        
        serializer = WatchVideoSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return success_response(message="Success", data={}, status_code=status.HTTP_200_OK)

        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class ViewBookSignedUrlView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request,  cid , format=None):
        chapter = ChapterLectures.objects.filter(id=cid).first()
        if chapter is None:
            raise ValidationError("Invalid Lecture ID!")
        
        from datetime import timezone

        bucket_name, object_name = parse_gcs_url(chapter.ebook.book_file.url)
        expiration_time = datetime.now(timezone.utc) + timedelta(seconds=10)
        bucket = client.get_bucket(settings.GS_BUCKET_NAME_2)
        blob = bucket.blob(object_name)

        log_activity(
            user=request.user,
            action=ActivityLog.ActionType.LESSON_STARTED,
            entity_type='Course',
            metadata=request.user.first_name+" "+request.user.last_name + "started reading ebook "+ chapter.ebook.name+"."
        )
        
        return success_response(message="Success", data=blob.generate_signed_url(expiration=expiration_time), status_code=status.HTTP_200_OK)
    

class CreateNoteView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        serializer = CreateNoteSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Note created successfully", data=GetUserNotesSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class EditNoteView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request,  cid , format=None):
        
        course = Notes.objects.get(id=cid)
        serializer = EditNoteSerializer(course, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Note Updated successfully", data=GetUserNotesSerializer(user).data, status_code=status.HTTP_200_OK)

        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
    
class GetUserNotesView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, cid=None):
        notes = Notes.objects.filter(user = request.user, course_id = cid)
        serializer = GetUserNotesSerializer(notes, many= True, context={'user':request.user})
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class GetLectureNotesView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, cid=None):
        notes = Notes.objects.filter(chapter_lecture_id = cid)
        serializer = GetUserNotesSerializer(notes, many= True, context={'user':request.user})
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class DeleteNoteView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def delete(self, request, cid=None, format=None):
        try:
            note = Notes.objects.get(id = cid)

            if note.chapter_lecture.lecture_type == 1:
                content_name = note.chapter_lecture.video.name
            else:
                content_name = note.chapter_lecture.ebook.name
                
            log_activity(
                user=note.user,
                action=ActivityLog.ActionType.NOTE_DELETED,
                entity_type='Course',
                entity_id = note.id,
                metadata=note.user.first_name+" "+note.user.last_name + " note deleted in "+ content_name+"."
            )

            note.delete()

            
            return success_response(message="Note Deleted Successfully!", data={}, status_code=status.HTTP_200_OK)
        except MyList.DoesNotExist:
            return error_response(message="Note not found!", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        

class PerformaceReportView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, id = None, format=None):
        
        course_list = UserCourses.objects.filter(course_id = id, paid = 1).count()
        if course_list == 0:
            return Response({"errors": {"non_field_errors": ["Invalid Course ID"]}}, status.HTTP_403_FORBIDDEN)
        
        course = Course.objects.filter(id = id).first()
        total_duration_video_watched = UserLectureProgress.objects.filter(course_id = id, user = request.user).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        total_video_watched = UserLectureProgress.objects.filter(course_id = id, user = request.user).count()
        total_completed_videos = UserLectureProgress.objects.filter(course_id = id, user = request.user,completed = 1).count()
        
        video_duration_progress = 0

        if total_duration_video_watched > course.total_video_duration:
            video_duration_progress =  100
        else:
            if course.total_video_duration > 0:
                video_duration_progress =  math.ceil(total_duration_video_watched * 100 / course.total_video_duration)
        
        category = CourseChapters.objects.filter(course_id=id)
        serializer = PerformanceCourseChapterListingSerializer(category, many=True, context={'user':request.user})

        data = {
            "total_videos": course.total_video,
            "total_video_duration": course.total_video_duration,
            "total_completed_videos":total_completed_videos,
            "total_watched_video": total_video_watched,
            "total_duration_video_watched":total_duration_video_watched,
            "class_viewed":video_duration_progress,
            "chapter_wise_report":serializer.data
        }

        log_activity(
            user=request.user,
            action=ActivityLog.ActionType.PROGRESS,
            entity_type='Course',
            entity_id = id,
            metadata=request.user.first_name+" "+request.user.last_name + " progress reached "+ video_duration_progress+"% in course"+ course.name +"!"
        )
        return Response({"status":"success",'message':'',"data":data}, status = status.HTTP_200_OK)
    


class GetCourseCertificateView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, id = None, format=None):
        
        course_list = UserCourses.objects.filter(course_id = id, paid = 1).count()
        if course_list == 0:
            return Response({"errors": {"non_field_errors": ["Invalid Course ID"]}}, status.HTTP_403_FORBIDDEN)
        
        course = Course.objects.filter(id = id).first()
        total_duration_video_watched = UserLectureProgress.objects.filter(course_id = id, user = request.user).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        
        video_duration_progress = 0

        if total_duration_video_watched > course.total_video_duration:
            video_duration_progress =  100
        else:
            if course.total_video_duration > 0:
                video_duration_progress =  math.ceil(total_duration_video_watched * 100 / course.total_video_duration)

        if video_duration_progress < 50:
            return Response({"status":"failed","message":"You can't eligible for certificate","data":[]}, status=status.HTTP_400_BAD_REQUEST)
        
        import html

        get_certificate = UserCertificates.objects.filter(user_id = request.user.id, course_id = id).first()
        if get_certificate is None:
            timestamp = int(datetime.now().timestamp() * 1000)
            input_file = "user_study/templates/certificate/dummy_certificate_template.svg"
            filename = f"mini_lms/certificate/{timestamp}_certificate.svg" # Clean cloud path for GCS

            # 2. Prepare the dynamic text (escaped to prevent breaking the SVG XML)
            new_name = html.escape(f"{request.user.first_name} {request.user.last_name}")
            current_year = datetime.now().strftime("%y")
            cert_count = UserCertificates.objects.count() + 1

            certificate_id = html.escape(f"{current_year}-{cert_count:04d}")
            new_date = html.escape(str(datetime.today().date()))
            course_name = html.escape(course.name)

            # 3. Read the SVG template content as a regular string
            with open(input_file, "r", encoding="utf-8") as file:
                svg_content = file.read()

            # 4. Replace the text placeholders directly
            svg_content = svg_content.replace("{{name}}", new_name)
            svg_content = svg_content.replace("{{course_name}}", course_name)
            svg_content = svg_content.replace("{{date}}", new_date)
            svg_content = svg_content.replace("{{certificate_id}}", certificate_id)

            # 5 & 6. Create temp file, write content, and upload to GCS
            # delete=False ensures the file stays intact until we explicitly delete it after upload
            with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as temp_svg:
                try:
                    # Write the updated content to the temp file
                    temp_svg.write(svg_content.encode('utf-8'))
                    temp_svg.close()  # Close the file handle so GCS can safely read it

                    # Upload to Google Cloud Storage
                    bucket = client.get_bucket(settings.GS_BUCKET_NAME)
                    blob = bucket.blob(filename)  # Use the clean relative cloud path here
                    blob.upload_from_filename(temp_svg.name)
                    
                finally:
                    # Step 7. Ensure the local temp file is deleted no matter what happens during upload
                    if os.path.exists(temp_svg.name):
                        os.remove(temp_svg.name)

            # 7. Save metadata into the database
            chap = UserCertificates(
                user=request.user,
                course=course,
                certificate_url=blob.public_url
            )
            chap.save()

            log_activity(
                user=request.user,
                action=ActivityLog.ActionType.CERTIFICATE_GENERATED,
                entity_type='Course',
                entity_id = chap.id,
                metadata=request.user.first_name+" "+request.user.last_name + " has completed the course & generated the certificate for "+ course.name+"."
            )

            return Response({"status":"success",'message':'',"data":blob.public_url}, status = status.HTTP_200_OK)
        
        else:
            return Response({"status":"success",'message':'',"data":get_certificate.certificate_url}, status = status.HTTP_200_OK)
        


class CreateMyListView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        
        serializer = CreateMyListSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return Response({"status":"success",'message':'List created successfully',"data":[] }, status = status.HTTP_201_CREATED)

        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class CreateMyListView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        
        serializer = CreateMyListSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return Response({"status":"success",'message':'List created successfully',"data":[] }, status = status.HTTP_201_CREATED)

        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateMyListView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, cid = None, format=None):
        
        serializer = UpdateMyListSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return Response({"status":"success",'message':'List updated successfully',"data":[] }, status = status.HTTP_201_CREATED)

        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetMyListView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request,format=None):
        
        info = MyList.objects.filter(user_id = request.user)
        serializer = MyListCourseSerializer(info, many=True)
    
        return Response({"status":"success",'message':'',"data":serializer.data}, status = status.HTTP_200_OK)
    


class DeleteMyListView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def delete(self, request, cid, format=None):
        
        try:
            course = MyList.objects.get(id = cid)
            course.delete()
            return Response({"status":"success",'message':'My List Deleted Successfully',"data":[]}, status=status.HTTP_204_NO_CONTENT)
        except MyList.DoesNotExist:
            return Response({"status":"failed","message":"My List no found!","data":[]}, status=status.HTTP_400_BAD_REQUEST)
        

class AddReviewAndRatingView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        
        serializer = AddReviewAndReviewSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return Response({"status":"success",'message':'Review added successfully',"data":[] }, status = status.HTTP_201_CREATED)

        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateCourseReviewRatingView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, cid=None):
        review = CourseReviewRating.objects.filter(id = cid).first()
        serializer = UpdateCourseReviewSerializer(review, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Review Updated successfully", data={}, status_code=status.HTTP_200_OK)

        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetCourseReviewView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, cid=None):
        notes = CourseReviewRating.objects.filter(user = request.user, course_id = cid).first()
        if notes is None:
            return success_response(message="Success", data={}, status_code=status.HTTP_200_OK)
        serializer = GetUserCourseReviewSerializer(notes, context={'user':request.user})
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)


class GetUserWishlistView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, format=None):
        
        category = UserWishlist.objects.filter(user=request.user).order_by("-id")
        serializer = WishlistSerializer(category, many=True)
        return Response({"status":"success",'message':'',"data":serializer.data}, status = status.HTTP_200_OK)


class CheckCourseInWishlistView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request,format=None):
        cart_count = UserWishlist.objects.filter(user=request.user, course_id = request.data.get('course_id')).count()
        if cart_count > 0:
            course = UserWishlist.objects.filter(user=request.user, course_id = request.data.get('course_id')).first()
            serializer = WishlistSerializer(course)
            return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
        else:
            return success_response(message="", data=[], status_code=status.HTTP_200_OK)
        

class AddUserWishlistView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        serializer = AddUserWishlistSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            course = UserWishlist.objects.filter(user=request.user, course_id = request.data.get('course_id')).first()
            serializer1 = WishlistSerializer(course)

            return Response({"status":"success",'message':'Success',"data":serializer1.data}, status = status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST) 
    


class GetUserNotificationSettingView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student, CorporateAdmin]
                        )]
    def get(self, request, format=None):
        notification = UserNotificationSetting.objects.filter(user_id = request.user.id).first()
        if notification is None:
            return success_response(message="", data={}, status_code=status.HTTP_200_OK)
        serializer = UserNotificationSerializer(notification)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class UpdateUserNotificationSettingView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student, CorporateAdmin]
                        )]
    def post(self, request, format=None):
        serializer = UpdateUserNotificationSettingSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Setting Updated successfully!", data=UserNotificationSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetUserNotificationView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student, CorporateAdmin]
                        )]
    def get(self, request, sid = None, format=None):
        category = UserNotifications.objects.filter(user=request.user, status = False).order_by("-id")
        serializer = NotificationSerializer(category, many=True)
        return success_response(message="Success!", data={"count": len(category), "notifications":serializer.data}, status_code=status.HTTP_200_OK)
    

class GetAllNotificationView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student, CorporateAdmin]
                        )]
    def get(self, request, sid = None, format=None):
        category = UserNotifications.objects.filter(user=request.user).order_by("-id")
        serializer = NotificationSerializer(category, many=True)
        return success_response(message="Success!", data={"count": len(category), "notifications":serializer.data}, status_code=status.HTTP_200_OK)


class ChangeNotificationStatusView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student, CorporateAdmin]
                        )]
    def post(self, request,  format=None):
        serializer = ChangeNotificationSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Notification Status Updated Successfully!", data={}, status_code=status.HTTP_200_OK)

        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)



class CreateRemindersView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        
        serializer = CreateRemindersSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            info = serializer.save()
            return success_response(message="Reminder Created Successfully!", data=RemindersListingSerializer(info).data, status_code=status.HTTP_200_OK)

        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateRemindersView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, cid = None, format=None):
        
        serializer = UpdateReminderSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            info = serializer.save()
            return success_response(message="Reminder Updated Successfully!", data=RemindersListingSerializer(info).data, status_code=status.HTTP_200_OK)

        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetRemindersView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request,format=None):
        
        info = LearningReminders.objects.filter(user_id = request.user).order_by("-id")
        serializer = RemindersListingSerializer(info, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)


class DeleteRemindersView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def delete(self, request, cid, format=None):
        
        try:
            course = LearningReminders.objects.get(id = cid)
            log_activity(
                    user=course.user,
                    action=ActivityLog.ActionType.NOTE_DELETED,
                    entity_type='Course',
                    entity_id = course.id,
                    metadata=course.user.first_name+" "+course.user.last_name + " reminder deleted in "+ course.course.name+"."
                )
    
            course.delete()
            return success_response(message="Reminder Deleted Successfully!", data={}, status_code=status.HTTP_200_OK)
        except LearningReminders.DoesNotExist:
            return error_response(message="Reminder not Found!", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        

class GetDashboardCountersView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def get(self, request,format=None):
        
        course_order = Order.objects.filter(
            user=request.user, 
            isPaid=True, 
            payment_type=PaymentType.Subscription
        ).first()

        no_of_licences = course_order.no_of_licence if course_order else 0 

        corporate_users = User.objects.filter(corporate=request.user)
        users_id = list(corporate_users.values_list("id", flat=True))
        license_used = len(users_id)  # Avoids another .count() query

        course_count = UserCourses.objects.filter(user_id__in=users_id).count()

        video_stats = UserLectureProgress.objects.filter(user_id__in=users_id).aggregate(
            total_watched=Count('id'),
            total_duration=Sum('total_duration')
        )

        total_video_watched = video_stats['total_watched'] or 0
        total_duration_video_watched = video_stats['total_duration'] or 0

        data = {
            "no_of_licences": no_of_licences,
            "license_used": license_used,
            "remaning_licence": no_of_licences - license_used,
            "registered_users": license_used,
            "assigned_courses": course_count,
            "total_video_watched": total_video_watched,
            "total_duration_video_watched": total_duration_video_watched
        }
        return success_response(message="Success", data=data, status_code=status.HTTP_200_OK)
    

class ShareCourseAccessView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def post(self, request, format=None):
        serializer = ShareCourseAccessSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Course Access Shared Successfully", data=StudentListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetCorporateUsersListView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name',"last_name","email", 'date_joined', 'id', 'is_active',"phone1","category"]
    ordering_fields = ['first_name',"last_name","email", 'date_joined', 'id', 'is_active',"phone1","category"] 
    def get(self, request, format=None):
        
        users_list = User.objects.filter(corporate = request.user)

        first_name = request.query_params.get('first_name')
        if first_name:
            users_list = users_list.filter(first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            users_list = users_list.filter(last_name__icontains = last_name)

        email = request.query_params.get('email')
        if email:
            users_list = users_list.filter(email__icontains = email)

        phone1 = request.query_params.get('phone')
        if phone1:
            users_list = users_list.filter(phone1__icontains = phone1)

        is_active = request.query_params.get('status')
        if is_active:
            users_list = users_list.filter(is_active = is_active)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                users_list = users_list.filter(created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                users_list = users_list.filter(created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            

        search_filter = filters.SearchFilter()
        users_list = search_filter.filter_queryset(request, users_list, self)

        ordering_filter = filters.OrderingFilter()
        users_list = ordering_filter.filter_queryset(request, users_list, self)

        if not users_list.ordered:
            users_list = users_list.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(users_list, request, view=self)
        serializer = StudentListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class AssignCourseAccessView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def post(self, request, format=None):
        serializer = AssignCourseAccessSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Course Access Shared Successfully", data=StudentListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetCourseStudentsView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def post(self, request, format=None):
        serializer = GetCourseAccessStudentsSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            course_id = serializer.data.get('course_id')
            usercourses = UserCourses.objects.filter(course_id = course_id, user__corporate_id = request.user.id).values_list("user",flat=True)
            users = User.objects.filter(id__in = usercourses)
            
            return success_response(message="", data=StudentBasicDetailSerializer(users, many=True).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class RemoveCourseAccessView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def post(self, request, format=None):
        serializer = RemoveCourseAccessSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Course Access Removed Successfully", data=StudentListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class GetUserStudyProgressView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [
        IsAuthenticated, 
        RoleOrPermissionCheck.for_roles([CorporateAdmin])
    ]

    def get(self, request, format=None):
        corporate_users = User.objects.filter(corporate=request.user)
        users_id = list(corporate_users.values_list("id", flat=True))

        period = request.query_params.get('period', 'daily').lower()
        now = timezone.now()
        
        # Base query layout mapping
        progress_qs = UserLectureProgress.objects.filter(user_id__in=users_id)
        
        if period == 'daily':
            start_date = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
            
            stats = (
                progress_qs.filter(created_at__gte=start_date)
                .annotate(day=TruncDay('created_at'))
                .values('day')
                .annotate(watched=Count('id'), duration=Sum('total_duration'))
                .order_by('day')
            )

            result_data = []
            for i in range(7):
                day_date = start_date + timedelta(days=i)
                day_label = day_date.strftime('%a')
                
                match = next((item for item in stats if item['day'].date() == day_date.date()), None)
                result_data.append({
                    "label": day_label,
                    "video_watched": match['watched'] if match else 0,
                    "duration": match['duration'] if match and match['duration'] else 0
                })

        elif period == 'weekly':
            start_date = (now - timedelta(weeks=4)).replace(hour=0, minute=0, second=0, microsecond=0)
            
            stats = (
                progress_qs.filter(created_at__gte=start_date)
                .annotate(week=TruncWeek('created_at'))
                .values('week')
                .annotate(watched=Count('id'), duration=Sum('total_duration'))
                .order_by('week')
            )
            
            result_data = []
            for i in range(4):
                weeks_ago = 3 - i
                w_start = (now - timedelta(weeks=weeks_ago)).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
                w_end = w_start + timedelta(days=7)
                
                label = "Current Week" if weeks_ago == 0 else f"Last Week {weeks_ago}"
                match = next((item for item in stats if w_start.date() <= item['week'].date() < w_end.date()), None)
                
                result_data.append({
                    "label": label,
                    "video_watched": match['watched'] if match else 0,
                    "duration": match['duration'] if match and match['duration'] else 0
                })

        elif period == 'monthly':
            start_date = (now - timedelta(days=365)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            stats = (
                progress_qs.filter(created_at__gte=start_date)
                .annotate(month=TruncMonth('created_at'))
                .values('month')
                .annotate(watched=Count('id'), duration=Sum('total_duration'))
                .order_by('month')
            )

            result_data = []
            for i in reversed(range(12)):
                target_month_date = now - timedelta(days=30 * i)
                month_label = target_month_date.strftime('%B')
                
                match = next((item for item in stats if item['month'].month == target_month_date.month and item['month'].year == target_month_date.year), None)
                
                result_data.append({
                    "label": month_label,
                    "video_watched": match['watched'] if match else 0,
                    "duration": match['duration'] if match and match['duration'] else 0
                })

        elif period == 'yearly':
            current_year = now.year
            start_date = now.replace(year=current_year - 4, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            
            stats = (
                progress_qs.filter(created_at__gte=start_date)
                .annotate(year=TruncYear('created_at'))
                .values('year')
                .annotate(watched=Count('id'), duration=Sum('total_duration'))
                .order_by('year')
            )

            result_data = []
            for i in reversed(range(5)):
                target_year = current_year - i
                match = next((item for item in stats if item['year'].year == target_year), None)
                
                result_data.append({
                    "label": str(target_year),
                    "video_watched": match['watched'] if match else 0,
                    "duration": match['duration'] if match and match['duration'] else 0
                })
        
        else:
            return success_response(message="Invalid period value", data=[], status_code=status.HTTP_400_BAD_REQUEST)

        return success_response(message="Success", data=result_data, status_code=status.HTTP_200_OK)
    


class GetUserCoursesProgressView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [
        IsAuthenticated, 
        RoleOrPermissionCheck.for_roles([CorporateAdmin])
    ]

    def get(self, request, format=None):
        corporate_users = User.objects.filter(corporate=request.user)
        users_id = list(corporate_users.values_list("id", flat=True))
        user_courses_list = UserCourses.objects.filter(user_id__in = users_id).values_list("course",flat=True)
        
        category = Course.objects.filter(id__in=user_courses_list)
        
        name = request.query_params.get('name')
        if name:
            category = category.filter(name__icontains = name)

        serializer = GetUserProgressSerializer(category, many=True, context={'user':request.user,"users_id":users_id})

        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)


class GetCoursesWiseUserProgressView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [
        IsAuthenticated, 
        RoleOrPermissionCheck.for_roles([CorporateAdmin])
    ]

    def get(self, request, format=None):
        corporate_users = User.objects.filter(corporate=request.user)
        users_id = list(corporate_users.values_list("id", flat=True))
        user_courses_list = UserCourses.objects.filter(user_id__in = users_id).values_list("course",flat=True)
        
        category = Course.objects.filter(id__in=user_courses_list)
        
        name = request.query_params.get('name')
        if name:
            category = category.filter(name__icontains = name)

        serializer = GetUserCoursewiseProgressSerializer(category, many=True, context={'user':request.user,"users_id":users_id})

        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)


class ReshareUserLoginDetailView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def post(self, request, format=None):
        serializer = ReshareUserLoginDetailSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Course Access Removed Successfully", data=StudentListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class AssignSingleCourseAccessView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def post(self, request, format=None):
        serializer = AssignSingleCourseAccessSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Course Access Shared Successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class GetCorporateStudentsListView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def get(self, request, format=None):
        users_list = User.objects.filter(corporate = request.user)
        serializer = StudentListingSerializer(users_list, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)


class ViewCorporateUserDetailView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def get(self, request, sid=None):
        users_list = User.objects.filter(corporate = request.user, id = sid).first()
        if users_list is None:
            raise ValidationError("Invalid User ID!")
        
        serializer = GetStudentDetailSerializer(users_list)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)



class GetStudentVideoReportView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def get(self, request, id = None, sid=None):
        
        course_list = UserCourses.objects.filter(course_id = sid, paid = 1, user = id).count()
        if course_list == 0:
            return error_response(message="Invalid Course ID", data = [], status_code=status.HTTP_400_BAD_REQUEST)

        category = CourseChapters.objects.filter(course_id=sid)
        serializer = CourseVideoReportSerializer(category, many=True, context={'user':id})
        total_video_watched = UserLectureProgress.objects.filter( course_id = sid, user = id).count()
        total_duration_video_watched = UserLectureProgress.objects.filter( course_id = sid, user = id).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0

        return success_response(message="Success", data={"report_data":serializer.data, "total_video_watched":total_video_watched, "total_duration_video_watched":total_duration_video_watched}, status_code=status.HTTP_200_OK)


class GetStudentNotesListingView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def get(self, request, cid=None, id=None):
        notes = Notes.objects.filter(user_id = id, course_id = cid)
        serializer = GetUserNotesSerializer(notes, many= True, context={'user':id})
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)



class GetNotesListingReportPDFView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                            RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def get(self, request, cid=None, id=None):
        
        notes = Notes.objects.filter(user_id = id, course_id = cid)
        serializer = GetUserNotesSerializer(notes, many= True, context={'user':id})
        user_info = User.objects.filter(id = id).first()
        course = Course.objects.filter(id = cid).first()
        data = {
                    "user_data":serializer.data,
                    'username':user_info.first_name +' '+user_info.last_name,
                    'user_id':user_info.email,
                    'course':course.name,
                }
        

        template = get_template('pdf/student_notes_listing_report.html')
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
    


class GetNotesListingReportExcelView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                            RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def get(self, request, cid=None, id=None):
            
        notes = Notes.objects.filter(user_id = id, course_id = cid)
        serializer = GetUserNotesSerializer(notes, many= True, context={'user':id})
        user_info = User.objects.filter(id = id).first()
        course = Course.objects.filter(id = cid).first()
        data = {
                    "user_data":serializer.data,
                    'username':user_info.first_name +' '+user_info.last_name,
                    'user_id':user_info.email,
                    'course':course.name,
                }

        lis = []
        
        lis.append({
                "name":"Notes Detail Report",
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
                "last_name":user_info.first_name +' '+user_info.last_name,
                "email":'',
                "phone":'User ID',
                "category":user_info.email,
                "type":'',
                "reference":'Course',
                "course":course.name,
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
                "name":"Lecture Name",
                "last_name":"Note Detail",
                "email":'',
                "phone":'',
                "category":'',
                "type":'',
                "reference":'',
                "course":'',
                "count":''
            })
        
        
        for chapter_data in serializer.data:
            lecture_info = chapter_data.get('lecture_info', {})
            video_info = lecture_info.get('video_info', {})
            ebook_info = lecture_info.get('ebook_info', {})

            if video_info and video_info.get('name'):
                chapter_data['display_title'] = video_info['name']
            elif ebook_info and ebook_info.get('name'):
                chapter_data['display_title'] = ebook_info['name']
            else:
                chapter_data['display_title'] = "No Title Available"
                
            lis.append({
                "name":chapter_data['display_title'],
                "last_name":chapter_data['note_content'],
                "email":"",
                "phone":"",
                "category":"",
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


class GetAttemptedTestsListingView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def get(self, request, cid=None, id=None):
        test = PracticeTests.objects.filter(course_id = cid, user = id).order_by("-id")
        serializer = PracticeTestListingSerializer(test,many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)


class GetStudentActivityReportView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                              RoleOrPermissionCheck.for_roles(
                                [CorporateAdmin]
                            )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name',"user__last_name","user__email"]
    ordering_fields = ['user__first_name','user__last_name',"user__email"]
    def get(self, request, cid=None):
        
        topics = UserLoginActivity.objects.filter(user_id = cid)
        
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



class DownloadStudentVideoReportView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def get(self, request, cid = None, id=None):
        course_list = UserCourses.objects.filter(course_id = cid, paid = 1, user__corporate = request.user,user_id = id).count()
        if course_list == 0:
            return error_response(message="Invalid Course ID", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        
        course_info = UserCourses.objects.filter(course_id = cid, paid = 1, user__corporate = request.user,user_id = id).first()
        course = Course.objects.get(id = cid)
        user_info = User.objects.get(id = id)
        if course_info.trail == True:
            chapters = TrailCourseChapters.objects.filter(trail_course__course_id = cid).values_list("chapter", flat=True)
            category = CourseChapters.objects.filter(course_id=cid, chapter_id__in = chapters)
            serializer = DashboardCourseChapterListingSerializer(category, many=True, context={'user':user_info})

        else:
            category = CourseChapters.objects.filter(course_id=cid)
            serializer = CourseVideoReportSerializer(category, many=True, context={'user':user_info})

        total_video_watched = UserLectureProgress.objects.filter( course_id = cid, user = user_info).count()
        total_duration_video_watched = UserLectureProgress.objects.filter( course_id = cid, user = user_info).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0

        
        result = {
                'video_report': serializer.data,
                'username':user_info.first_name +' '+user_info.last_name,
                'user_id':user_info.email,
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
    
    


class DownloadStudentVideoReportCSVView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def get(self, request, cid = None,  id=None):
        
        course_list = UserCourses.objects.filter(course_id = cid, paid = 1, user__corporate = request.user,user_id = id).count()
        if course_list == 0:
            return error_response(message="Invalid Course ID", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        
        course_info = UserCourses.objects.filter(course_id = cid, paid = 1, user__corporate = request.user,user_id = id).first()
        course = Course.objects.get(id = cid)
        user_info = User.objects.get(id = id)
        if course_info.trail == True:
            chapters = TrailCourseChapters.objects.filter(trail_course__course_id = cid).values_list("chapter", flat=True)
            category = CourseChapters.objects.filter(course_id=cid, chapter_id__in = chapters)
            serializer = DashboardCourseChapterListingSerializer(category, many=True, context={'user':user_info})

        else:
            category = CourseChapters.objects.filter(course_id=cid)
            serializer = CourseVideoReportSerializer(category, many=True, context={'user':user_info})

        total_video_watched = UserLectureProgress.objects.filter( course_id = cid, user = user_info).count()
        total_duration_video_watched = UserLectureProgress.objects.filter( course_id = cid, user = user_info).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0


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
                "email":user_info.first_name +' '+user_info.last_name,
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        lis.append({
                "name":"User ID:",
                "email":user_info.email,
                "subject":'',
                "Chapter":'',
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        lis.append({
                "name":"Course:",
                "email":course.name,
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


class GetCorporateStudentsActivityLogLatestListView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def get(self, request, format=None):
        users_list = User.objects.filter(corporate = request.user).values_list("id",flat=True)
        activity_log = ActivityLog.objects.filter(
                user_id__in=users_list
            ).order_by('-created_at')[:10]
        serializer = ActivityLogListingSerializer(activity_log, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)


class GetCorporateStudentsActivityLogListView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, id=None):

        if id is not None:
            activity_log = ActivityLog.objects.filter(
                                    user_id=id
                                ).order_by('-created_at')
        else:
            users_list = User.objects.filter(corporate = request.user).values_list("id",flat=True)
            activity_log = ActivityLog.objects.filter(
                        user_id__in=users_list
                    ).order_by('-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(activity_log, request, view=self)
        serializer = ActivityLogListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)



class GetCorporateStudentsActivityLogPDFReportView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                            RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def get(self, request, id=None):

        if id is not None:
            users_list = User.objects.filter(id = id).first()
            activity_log = ActivityLog.objects.filter(
                    user_id=id
                ).order_by('-created_at')
            serializer = ActivityLogListingSerializer(activity_log, many=True)
            data = {
                        "user_data":serializer.data,
                        'username':users_list.first_name +' '+users_list.last_name,
                        'user_id':users_list.email,
                    }
        else:
            users_list = User.objects.filter(corporate = request.user).values_list("id",flat=True)
            activity_log = ActivityLog.objects.filter(
                    user_id__in=users_list
                ).order_by('-created_at')
            serializer = ActivityLogListingSerializer(activity_log, many=True)
            data = {
                        "user_data":serializer.data
                    }
            

        template = get_template('pdf/student_activity_log_listing_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "activity_log_report"
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
    


class GetCorporateStudentsActivityLogExcelReportView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                            RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin]
                        )]
    def get(self, request, cid=None, id=None):
        user_info = None
        if id is not None:
            user_info = User.objects.filter(id = id).first()
            activity_log = ActivityLog.objects.filter(
                    user_id=id
                ).order_by('-created_at')
            serializer = ActivityLogListingSerializer(activity_log, many=True)
            
        else:
            users_list = User.objects.filter(corporate = request.user).values_list("id",flat=True)
            activity_log = ActivityLog.objects.filter(
                    user_id__in=users_list
                ).order_by('-created_at')
            serializer = ActivityLogListingSerializer(activity_log, many=True)
            
        lis = []
        
        lis.append({
                "name":"Student Activity Log Report",
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

        if id is not None:
            lis.append({
                    "name":"Name",
                    "last_name":user_info.first_name +' '+user_info.last_name,
                    "email":'',
                    "phone":'User ID',
                    "category":user_info.email,
                    "type":'',
                    "reference":'',
                    "course":"",
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
                "name":"Activity",
                "last_name":"Time",
                "email":'',
                "phone":'',
                "category":'',
                "type":'',
                "reference":'',
                "course":'',
                "count":''
            })
        
        
        for chapter_data in serializer.data:
            lis.append({
                "name":chapter_data['metadata'],
                "last_name":chapter_data['time_ago'],
                "email":"",
                "phone":"",
                "category":"",
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
            report_name = "activity_log_report"
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


class GetStudentReminderListingView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin, SuperAdmin]
                        )]
    def get(self, request, cid=None, id=None):
        notes = LearningReminders.objects.filter(user_id = id, course_id = cid)
        serializer = GetLearningRemindersSerializer(notes, many= True, context={'user':id})
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)



class GetStudentReminderListingReportPDFView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                            RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin, SuperAdmin]
                        )]
    def get(self, request, cid=None, id=None):
        
        notes = LearningReminders.objects.filter(user_id = id, course_id = cid)
        serializer = GetLearningRemindersSerializer(notes, many= True, context={'user':id})
        user_info = User.objects.filter(id = id).first()
        course = Course.objects.filter(id = cid).first()
        data = {
                    "user_data":serializer.data,
                    'username':user_info.first_name +' '+user_info.last_name,
                    'user_id':user_info.email,
                    'course':course.name,
                }
        

        template = get_template('pdf/student_reminder_listing_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "learning_reminder_report"
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
    


class GetStudentReminderListingReportExcelView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                            RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin, SuperAdmin]
                        )]
    def get(self, request, cid=None, id=None):
            
        notes = LearningReminders.objects.filter(user_id = id, course_id = cid)
        serializer = GetLearningRemindersSerializer(notes, many= True, context={'user':id})
        user_info = User.objects.filter(id = id).first()
        course = Course.objects.filter(id = cid).first()
       
        lis = []
        
        lis.append({
                "name":"Learning Reminder Detail Report",
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
                "last_name":user_info.first_name +' '+user_info.last_name,
                "email":'',
                "phone":'User ID',
                "category":user_info.email,
                "type":'',
                "reference":'Course',
                "course":course.name,
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

        FREQUENCY_MAP = {
            1: "Daily",
            2: "Weekly",
            3: "Once"
        }

        lis.append({
            "name": "Title",
            "last_name": "Frequency",
            "email": "Time",
            "phone": "Date/Days",
            "category": "",
            "type": "",
            "reference": "",
            "course": "",
            "count": ""
        })

        for item in serializer.data:
            frequency_label = FREQUENCY_MAP.get(item.get("frequency"), "")

            date_or_days = ""
            if item.get("date"):
                date_or_days = str(item.get("date"))
            elif item.get("days"):
                date_or_days = item.get("days").title()

            lis.append({
                "name": item.get("title", ""),
                "last_name": frequency_label,
                "email": item.get("time", ""),
                "phone": date_or_days,
                "category": "",
                "type": "",
                "reference": "",
                "course": "",
                "count": ""
            })

            
            
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "learning_reminder_report"
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



class GetStudentQuizListingReportPDFView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                            RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin, SuperAdmin]
                        )]
    def get(self, request, cid=None, id=None):
        
        test = PracticeTests.objects.filter(course_id = cid, user = id).order_by("-id")
        serializer = PracticeTestListingSerializer(test,many=True)
        user_info = User.objects.filter(id = id).first()
        course = Course.objects.filter(id = cid).first()
        data = {
                    "user_data":serializer.data,
                    'username':user_info.first_name +' '+user_info.last_name,
                    'user_id':user_info.email,
                    'course':course.name,
                }
        

        template = get_template('pdf/student_quiz_listing_report.html')
        html  = template.render(data)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "quiz_report"
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
    


class GetStudentQuizListingReportExcelView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                            RoleOrPermissionCheck.for_roles(
                            [CorporateAdmin, SuperAdmin]
                        )]
    def get(self, request, cid=None, id=None):
            
        test = PracticeTests.objects.filter(course_id = cid, user = id).order_by("-id")
        serializer = PracticeTestListingSerializer(test,many=True)
        user_info = User.objects.filter(id = id).first()
        course = Course.objects.filter(id = cid).first()
       
        lis = []
        
        lis.append({
                "name":"Student Quiz Detail Report",
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
                "last_name":user_info.first_name +' '+user_info.last_name,
                "email":'',
                "phone":'User ID',
                "category":user_info.email,
                "type":'',
                "reference":'Course',
                "course":course.name,
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
            "name": "Quiz Name",
            "last_name": "Chapter Name",
            "email": "Total Questions",
            "phone": "Right Answer / Wrong Answer",
            "category": "Total Time Taken",
            "type": "Start Time / End Time",
            "reference": "Score",
            "course": "Result",
            "count": "",
        })

        for item in serializer.data:
            quiz = item.get("quiz") or {}
            chapter = quiz.get("chapter") or {}

            # Extract right/wrong answers
            right_ans = item.get("total_right_answer_given", 0)
            wrong_ans = item.get("total_wrong_answer_given", 0)
            right_wrong_str = f"{right_ans} / {wrong_ans}"

            # Extract and format time/duration
            time_taken_str = format_seconds(item.get("total_time_taken"))

            # Extract and format start/end timestamps
            start_str = format_iso_time(item.get("start_time"))
            end_str = format_iso_time(item.get("end_time"))
            time_range_str = f"{start_str} - {end_str}"

            lis.append({
                "name": quiz.get("name", "N/A"),
                "last_name": chapter.get("name", "N/A"),
                "email": item.get("total_question", 0),
                "phone": right_wrong_str,
                "category": time_taken_str,
                "type": time_range_str,
                "reference": item.get("score", 0),
                "course": item.get("result", "N/A"),
                "count": "",
            })

            
            
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M")
            report_name = "learning_reminder_report"
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