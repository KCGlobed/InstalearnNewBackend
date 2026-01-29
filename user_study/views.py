from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from user_study.serializers import *
from user_study.renderers import ReportRenderer
from django.template import loader
from django.core.mail import send_mail
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import get_template
from django.template import loader
from django.core.mail import EmailMessage
import os
from rolepermissions.checkers import has_role
from rest_framework.permissions import IsAuthenticated
import time , calendar
import pandas as pd
from google.cloud import storage
client = storage.Client.from_service_account_json(os.path.join(settings.BASE_DIR, 'credentail_bucket.json'))

class PurchasedCoursesView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request,format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
        
        course_list = UserCourses.objects.filter(user__email = request.user.email, paid = 1).values_list('course', flat=True)
        category = Course.objects.filter(id__in=course_list)
        serializer = OrderCoursesSerializer(category, many=True, context={'user':request.user})

        info = FrequentlyBoughtCourse.objects.filter(course_id__in = course_list).exclude(bought_course_id__in = course_list)
        frequntly = FrequentlyBoughtCourseSerializer(info, many=True)
    

        return Response({"status":"success",'message':'',"data":{"purchased_courses":serializer.data,"suggested_courses":frequntly.data}}, status = status.HTTP_200_OK)
    

class DashboardCoursesView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, id = None, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
        
        course_list = UserCourses.objects.filter(course_id = id, paid = 1).count()
        if course_list == 0:
            return Response({"errors": {"non_field_errors": ["Invalid Course ID"]}}, status.HTTP_403_FORBIDDEN)
        
        category = CourseChapters.objects.filter(course_id=id)
        serializer = DashboardCourseChapterListingSerializer(category, many=True, context={'user':request.user})
        return Response({"status":"success",'message':'',"data":serializer.data}, status = status.HTTP_200_OK)
    

class DashboardCoursesCounterView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, id = None, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
        
        course_list = UserCourses.objects.filter(course_id = id, paid = 1).count()
        if course_list == 0:
            return Response({"errors": {"non_field_errors": ["Invalid Course ID"]}}, status.HTTP_403_FORBIDDEN)
        
        category = CourseChapters.objects.only('id').filter(course_id=id).count()
        course = Course.objects.filter(id = id).first()
        total_duration_video_watched = UserWatchedTopicVideos.objects.filter(course_id = id, user = request.user).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        total_video_watched = UserWatchedTopicVideos.objects.filter(course_id = id, user = request.user).count()
        
        video_duration_progress = 0

        if total_duration_video_watched > course.total_video_duration:
            video_duration_progress =  100
        else:
            if course.total_video_duration > 0:
                video_duration_progress =  math.ceil(total_duration_video_watched * 100 / course.total_video_duration)
        
        data = {
            "total_chapters" : category,
            "total_videos": course.total_video,
            "total_video_duration": course.total_video_duration,
            "total_watched_video": total_video_watched,
            "total_duration_video_watched":total_duration_video_watched,
            "total_video_progress":video_duration_progress
        }
        return Response({"status":"success",'message':'',"data":data}, status = status.HTTP_200_OK)
    

    
class GetTopicVideosView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, cid = None, tid=None, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
        
        if cid is None:
            return Response({"errors": {"non_field_errors": ["Chapter ID is required"]}}, status.HTTP_403_FORBIDDEN)

        if tid is not None:
            category = TopicVideos.objects.filter(chapter_topics_id = tid).order_by('order','id')
        else:
            chapter_list = ChapterTopics.objects.filter(course_chapters_id__in = cid).values_list('id', flat=True)
            category = TopicVideos.objects.filter(chapter_topics_id__in = chapter_list).order_by('order','id')
        
        serializer = TopicVideosSerializer(category, many=True)
        return Response({"status":"success",'message':'',"data":serializer.data}, status=status.HTTP_200_OK)
    

class GetChapterVideoReportView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, cid = None, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
        
        category = CourseChapters.objects.filter(course_id=cid)
        serializer = ChapterVideoReportSerializer(category, many=True,context={'user':request.user})
        watch_videos = UserWatchedTopicVideos.objects.filter(course_id = cid, user = request.user).count()
        total_duration_video_watched = UserWatchedTopicVideos.objects.filter(course_id = cid, user = request.user).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        
        result = {
                'watched_videos':watch_videos,
                'watch_video_duration':total_duration_video_watched,
                'video_report': serializer.data,
            }
        
        return Response({"status":"success","message":"","data":result}, status=status.HTTP_200_OK)
    


class DownloadChapterVideoReportView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, cid = None, sid = None, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)

        course = Course.objects.filter(id=cid).first()
        category = CourseChapters.objects.filter(course_id=cid)
        serializer = ChapterVideoReportSerializer(category, many=True,context={'user':request.user})
        watch_videos = UserWatchedTopicVideos.objects.filter(course_id = cid, user = request.user).count()
        total_duration_video_watched = UserWatchedTopicVideos.objects.filter(course_id = cid, user = request.user).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        
        result = {
                'watched_videos':watch_videos,
                'watch_video_duration':total_duration_video_watched,
                'video_report': serializer.data,
                'username':request.user.first_name +' '+request.user.last_name,
                'user_id':request.user.email,
                'course':course.name,
            }

        template = get_template('pdf/video_report.html')
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

        return Response({"status":"success","message":"","data":{'file_url':blob.public_url}}, status=status.HTTP_200_OK)
    


class DownloadChapterVideoReportCSVView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, cid = None,  format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)

        course_subject = Course.objects.filter(id = cid).first()
        category = CourseChapters.objects.filter(course_id=cid)
        serializer = ChapterVideoReportSerializer(category, many=True,context={'user':request.user})
        watch_videos = UserWatchedTopicVideos.objects.filter(course_id = cid, user = request.user).count()
        total_duration_video_watched = UserWatchedTopicVideos.objects.filter(course_id = cid, user = request.user).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0

        def convert(seconds):
            seconds = seconds % (24 * 3600)
            hour = seconds // 3600
            seconds %= 3600
            minutes = seconds // 60
            seconds %= 60
            
            return "%02d:%02d:%02d" % (hour, minutes, seconds)
        
        def convert_minutes(seconds):
            seconds = seconds % (24 * 3600)
            hour = seconds // 3600
            seconds %= 3600
            minutes = seconds // 60
            seconds %= 60
            format = ""
            if hour > 0:
                format += str(hour)+"h "
            if minutes > 0:
                format += str(minutes)+"m "
            
            format += str(seconds)+"s"
            
            return format

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
                "email":watch_videos,
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
                "email":'Topic Name',
                "subject":'Total Videos',
                "Chapter":'Videos Watched',
                "Topic":'Watch Time',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":''
            })
        
        
        for info in serializer.data:
            if info['total_duration_watched_videos'] is not None:
                time = convert_minutes(info['total_duration_watched_videos'])
            else :
                time = "0s"

            lis.append({
                "name":info['chapter_info']['name'],
                "email":'',
                "subject":info['no_of_videos'],
                "Chapter":info['total_watched_videos'],
                "Topic":time,
                "total_videos":"",
                "total_watched_videos":"",
                "total_time_spend":""
            })

            if len(info['topics']) > 0:
                for top in info['topics']:
                    if top['total_duration_watched_videos'] is not None:
                        time1 = convert_minutes(top['total_duration_watched_videos'])
                    else :
                        time1 = "0s"
                        
                    lis.append({
                        "name":'',
                        "email":top['topic_info']['name'],
                        "subject":top['no_of_videos'],
                        "Chapter":top['total_watched_videos'],
                        "Topic":time1,
                        "total_videos":"",
                        "total_watched_videos":"",
                        "total_time_spend":""
                    })


        
        import time
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

        return Response({"status":"success","message":"","data":{'file_url':blob.public_url}}, status=status.HTTP_200_OK)


class GetChapterVideoDetailView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, cid = None, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
            
        category = TopicVideos.objects.filter(id = cid).first()
        serializer = ChapterSingleVideosSerializer(category,context={'user':request.user})
        return Response({"status":"success","message":"","data":serializer.data}, status=status.HTTP_200_OK)
    
class WatchVideoView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)

        serializer = WatchVideoSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return Response({"status":"success",'message':'',"data":[] }, status = status.HTTP_201_CREATED)

        return Response({"status":"failed","message":"","data":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class CreateNoteView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)

        serializer = CreateNoteSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return Response({"status":"success",'message':'Note created successfully',"data":[] }, status = status.HTTP_201_CREATED)

        return Response({"status":"failed","message":"","data":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class EditNoteView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def post(self, request,  cid , format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
        
        course = Notes.objects.get(id=cid)
        serializer = EditNoteSerializer(course, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return Response({"status":"success",'message':'Note updated successfully',"data":[]}, status = status.HTTP_200_OK)

        return Response({"status":"failed",'message':'',"data":serializer.errors}, status.HTTP_400_BAD_REQUEST)
    
    
class GetUserNotesView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, cid=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)

        notes = Notes.objects.filter(user = request.user, course_id = cid)
        serializer = GetUserNotesSerializer(notes, many= True)
        return Response({"status":"success","message":"",'data': serializer.data}, status = status.HTTP_200_OK)
    


class PerformaceReportView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, id = None, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
        
        course_list = OrderCourses.objects.filter(course_id = id, paid = 1).count()
        if course_list == 0:
            return Response({"errors": {"non_field_errors": ["Invalid Course ID"]}}, status.HTTP_403_FORBIDDEN)
        
        course = Course.objects.filter(id = id).first()
        total_duration_video_watched = UserWatchedTopicVideos.objects.filter(course_id = id, user = request.user).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        total_video_watched = UserWatchedTopicVideos.objects.filter(course_id = id, user = request.user).count()
        total_completed_videos = UserWatchedTopicVideos.objects.filter(course_id = id, user = request.user,completed = 1).count()
        
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
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, id = None, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
        
        course_list = OrderCourses.objects.filter(course_id = id, paid = 1).count()
        if course_list == 0:
            return Response({"errors": {"non_field_errors": ["Invalid Course ID"]}}, status.HTTP_403_FORBIDDEN)
        
        course = Course.objects.filter(id = id).first()
        total_duration_video_watched = UserWatchedTopicVideos.objects.filter(course_id = id, user = request.user).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        
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
        

class GetCompleteVideoListView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, cid = None, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
        
        course_list = OrderCourses.objects.filter(course_id = cid, paid = 1).count()
        if course_list == 0:
            return Response({"errors": {"non_field_errors": ["Invalid Course ID"]}}, status.HTTP_403_FORBIDDEN)
        
        category = CourseChapters.objects.filter(course_id=cid)
        serializer = CompleteVideoListingSerializer(category, many=True, context={'user':request.user})
        return Response({"status":"success",'message':'',"data":serializer.data}, status = status.HTTP_200_OK)
    

class CreateMyListView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
        
        serializer = CreateMyListSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return Response({"status":"success",'message':'List created successfully',"data":[] }, status = status.HTTP_201_CREATED)

        return Response({"status":"failed","message":"","data":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    


class CreateMyListView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
        
        serializer = CreateMyListSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return Response({"status":"success",'message':'List created successfully',"data":[] }, status = status.HTTP_201_CREATED)

        return Response({"status":"failed","message":"","data":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class UpdateMyListView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def post(self, request, cid = None, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
        
        serializer = UpdateMyListSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return Response({"status":"success",'message':'List updated successfully',"data":[] }, status = status.HTTP_201_CREATED)

        return Response({"status":"failed","message":"","data":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class GetMyListView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request,format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
        
        info = MyList.objects.filter(user_id = request.user)
        serializer = MyListCourseSerializer(info, many=True)
    
        return Response({"status":"success",'message':'',"data":serializer.data}, status = status.HTTP_200_OK)
    


class DeleteMyListView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def delete(self, request, cid, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
        
        try:
            course = MyList.objects.get(id = cid)
            course.delete()
            return Response({"status":"success",'message':'My List Deleted Successfully',"data":[]}, status=status.HTTP_204_NO_CONTENT)
        except MyList.DoesNotExist:
            return Response({"status":"failed","message":"My List no found!","data":[]}, status=status.HTTP_400_BAD_REQUEST)
        

class AddReviewAndRatingView(APIView):
    renderer_classes = [ReportRenderer]
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        if not has_role(request.user, [Student]):
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "you have not a required role to access this api"}}, status.HTTP_403_FORBIDDEN)
        
        serializer = AddReviewAndReviewSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return Response({"status":"success",'message':'Review added successfully',"data":[] }, status = status.HTTP_201_CREATED)

        return Response({"status":"failed","message":"","data":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)