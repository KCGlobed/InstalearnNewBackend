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
from rolepermissions.checkers import has_role
from rest_framework.permissions import IsAuthenticated
import time , calendar
import pandas as pd
from mini_lms.permissions import RoleOrPermissionCheck
import json
from google.cloud import storage
from google.oauth2 import service_account
info = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
credentials = service_account.Credentials.from_service_account_info(info)
client = storage.Client(credentials=credentials, project=credentials.project_id)

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
    
    

class DashboardCourseChaptersView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, id = None, format=None):
        
        course_list = UserCourses.objects.filter(course_id = id, paid = 1).count()
        if course_list == 0:
            return error_response(message="Invalid Course ID", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        
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
        
        course_list = UserCourses.objects.filter(course_id = id, paid = 1).count()
        if course_list == 0:
            return error_response(message="Invalid Course ID", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        
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
        course_list = UserCourses.objects.filter(course_id = cid, paid = 1).count()
        if course_list == 0:
            return error_response(message="Invalid Course ID", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        
        course = Course.objects.get(id = cid)
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
        result = BytesIO()
        destination = settings.MEDIA_ROOT+ 'pdf_reports/'
        if not os.path.exists(destination):
            os.makedirs(destination)
        current_GMT = time.gmtime()
        ts = calendar.timegm(current_GMT)

        file = open(destination + str(request.user.id) +"_"+str(ts)+'_video_report.pdf', "w+b")
        html = html.encode('latin-1', 'replace').decode('latin-1')
        pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), dest=file)
        file.close()
        
        bucket = client.get_bucket(settings.GS_BUCKET_NAME)
        blob = bucket.blob(destination + str(request.user.id) +"_"+str(ts)+'_video_report.pdf')
        
        blob.upload_from_filename(destination + str(request.user.id) +"_"+str(ts)+'_video_report.pdf')

        return success_response(message="Success", data={'file_url':blob.public_url}, status_code=status.HTTP_200_OK)
    
    


class DownloadChapterVideoReportCSVView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, cid = None,  format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)

        course_subject = Course.objects.filter(id = cid).first()
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

        current_GMT = time.gmtime()
        ts = calendar.timegm(current_GMT)

        df = pd.DataFrame.from_dict(lis)
        destination = settings.MEDIA_ROOT+ 'pdf_reports/'
        path = destination + str(request.user.id) +"_"+str(ts)+'_video_report.csv'
        df.to_csv(path, encoding="UTF-8", header=False, index=False)
        
        if not os.path.exists(destination):
            os.makedirs(destination)

        bucket = client.get_bucket(settings.GS_BUCKET_NAME)
        blob = bucket.blob(destination + str(request.user.id) +"_"+str(ts)+'_video_report.csv')
        
        blob.upload_from_filename(destination + str(request.user.id) +"_"+str(ts)+'_video_report.csv')

        return success_response(message="Success", data={'file_url':blob.public_url}, status_code=status.HTTP_200_OK)



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
    

class CreateNoteView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        serializer = CreateNoteSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return success_response(message="Note created successfully", data={}, status_code=status.HTTP_200_OK)
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
            return success_response(message="Note Updated successfully", data={}, status_code=status.HTTP_200_OK)

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
        return Response({"status":"success",'message':'',"data":data}, status = status.HTTP_200_OK)
    


class GetCourseCertificateView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, id = None, format=None):
        
        course_list = OrderCourses.objects.filter(course_id = id, paid = 1).count()
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

        if video_duration_progress < 95:
            return Response({"status":"failed","message":"You can't eligible for certificate","data":[]}, status=status.HTTP_400_BAD_REQUEST)
        
        get_certificate = UserCertificates.objects.filter(user_id = request.user.id, course_id = id).first()
        if get_certificate is None:
            destination = settings.MEDIA_ROOT+ 'mini_lms/certificate/'
            if not os.path.exists(destination):
                os.makedirs(destination)
            input_file = "reports/templates/certificate/2477188_343489-PAOJU9-140.svg"  # Path to your SVG file
            output_file = destination + str(request.user.id)+"_certificate.svg"  # Path to save the updated SVG file

            text_to_find = "student_name"
            new_text = request.user.first_name+" "+request.user.last_name
            from datetime import date

            text_to_find1 = "certificate_date"
            new_text1 = str(date.today())


            with open(input_file, "r", encoding="utf-8") as file:
                svg_content = file.read()

            soup = BeautifulSoup(svg_content, "xml")

            for text_element in soup.find_all("text"):
                if text_element.string == text_to_find:
                    text_element.string = new_text
                
                if text_element.string == text_to_find1:
                    text_element.string = new_text1

            with open(output_file, "w", encoding="utf-8") as file:
                file.write(str(soup))

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(output_file)
            blob.upload_from_filename(output_file)

            chap = UserCertificates(
                user = request.user,
                course = course,
                certificate_url = blob.public_url
            )
            chap.save()
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
    


class GetUserWishlistView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)

        category = UserWishlist.objects.filter(user=request.user).order_by("-id")
        serializer = WishlistSerializer(category, many=True)
        return Response({"status":"success",'message':'',"data":serializer.data}, status = status.HTTP_200_OK)


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
            return Response({"status":"success",'message':'Success',"data":[]}, status = status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST) 
    


class GetUserNotificationSettingView(APIView):
    renderer_classes = [UserStudyRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
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
                            [Student]
                        )]
    def post(self, request, format=None):
        serializer = UpdateUserNotificationSettingSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Setting Updated successfully!", data=UserNotificationSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)