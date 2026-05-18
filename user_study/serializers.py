from rest_framework import serializers
from subscription.models import *
from courses.models import *
from users.models import *
from user_study.models import *
from django.conf import settings
from django.core.mail import send_mail
from mini_lms.roles import Student
from rolepermissions.roles import assign_role
import random
import math
from django.template import loader
from datetime import datetime
import random, string
import razorpay
from django.db.models import Sum, Avg, Count



class CourseProgressSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField('get_progress')
    def get_progress(self, obj):
        total_duration_video_watched = UserLectureProgress.objects.filter(course_id = obj.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        video_duration_progress = 0
        if total_duration_video_watched > obj.total_video_duration:
            video_duration_progress =  100
        else:
            if obj.total_video_duration > 0:
                    video_duration_progress =  math.ceil(total_duration_video_watched * 100 / obj.total_video_duration)
        return video_duration_progress

    class Meta:
        model = Course
        fields = ['id',"name","progress"]


class OrderCoursesSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField('get_progress')
    def get_progress(self, obj):
        total_duration_video_watched = UserLectureProgress.objects.filter(course_id = obj.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        video_duration_progress = 0
        if total_duration_video_watched > obj.total_video_duration:
            video_duration_progress =  100
        else:
            if obj.total_video_duration > 0:
                    video_duration_progress =  math.ceil(total_duration_video_watched * 100 / obj.total_video_duration)
        return video_duration_progress

    class Meta:
        model = Course
        fields = ['id',"name","short_description","image","avg_rating","total_reviews","updated_at","progress"]


class FrequentlyBoughtCourseSerializer(serializers.ModelSerializer):
    course = serializers.SerializerMethodField()
    
    def get_course(self, parent):
        info = Course.objects.get(id = parent.bought_course.id)
        return CourseSerializer(info).data

    class Meta:
        model = FrequentlyBoughtCourse
        fields = ["id",'course']


class CourseSerializer(serializers.ModelSerializer):
    updated_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d")
    
    class Meta:
        model = Course
        fields = ['id',"name","short_description","image","price","discount","objectives_summary","total_video_duration","avg_rating","total_reviews","updated_at"]


class CourseInstructorSerializer(serializers.ModelSerializer) :
    instructor = serializers.SerializerMethodField()

    def get_instructor(self, parent):
        info = Instructor.objects.get(id = parent.instructor.id)
        return InstructorSerializer(info).data

    class Meta:
        model = CourseInstructors
        fields = ['id','instructor']


class InstructorSerializer(serializers.ModelSerializer) :
    class Meta:
        model = Instructor
        fields = ['id','text_1',"text_2","text_3","experience","linkedin_url","description","image","company_image_1","company_image_2"]

class TopicSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField('get_progress')
    def get_progress(self, obj):
        total_video_watched = UserLectureProgress.objects.filter(chapter_topic = obj, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        if total_video_watched > obj.no_of_video_duration:
            return 100
        else:
            if obj.no_of_video_duration == 0:
                return 0
            return math.ceil(total_video_watched * 100 / obj.no_of_video_duration)
        
    class Meta:
        model = Chapters
        fields = ['id','name',"no_of_video_duration","no_of_videos","progress"]



class ChapterTopicsSerializer(serializers.ModelSerializer) :
    topic_info = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField('get_progress')
    topic_videos = serializers.SerializerMethodField()
    
    def get_progress(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(chapter_topic_id = parent.id, course_chapters_id = parent.course_chapters.id, course_id = parent.course_chapters.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        if total_video_watched > parent.no_of_video_duration:
            return 100
        else:
            if parent.no_of_video_duration == 0:
                return 0
            return math.ceil(total_video_watched * 100 / parent.no_of_video_duration)
    
    class Meta:
        model = Chapters
        fields = ['id','topic_info',"progress","topic_videos","no_of_videos","no_of_video_duration"]


class EbookDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChapterBooks
        fields = ["id",'name']


class ChapterLectureSerializer(serializers.ModelSerializer) :
    video_info = serializers.SerializerMethodField('get_video')
    ebook_info = serializers.SerializerMethodField('get_ebook')
   
    def get_ebook(self, obj):
        if obj.ebook:
            ebook_detail = ChapterBooks.objects.filter(id = obj.ebook.id).first()
            return EbookDetailSerializer(ebook_detail).data
        return {}
    
    def get_video(self, obj):
        if obj.video:
            video_detail = Videos.objects.filter(id = obj.video.id).first()
            return VideoDetailSerializer(video_detail).data
        return {}
    
    class Meta:
        model = ChapterLectures
        fields = "__all__"


class ChapterInfoSerializer(serializers.ModelSerializer) :
    class Meta:
        model = Chapters
        fields = ["id",'name',"no_of_videos","no_of_videos_duration"]


class DashboardCourseChapterListingSerializer(serializers.ModelSerializer) :
    chapter_info = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField('get_progress')
    video_watched = serializers.SerializerMethodField('get_video_watched')
    total_video_watched = serializers.SerializerMethodField('get_total_video_watched')

    def get_total_video_watched(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).count()
        return total_video_watched

    def get_video_watched(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        return total_video_watched
    
    def get_progress(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        if total_video_watched > parent.chapter.no_of_videos_duration:
            return 100
        else:
            if parent.chapter.no_of_videos_duration == 0:
                return 0
            return math.ceil(total_video_watched * 100 / parent.chapter.no_of_videos_duration)

    
    def get_chapter_info(self, parent):
        info = Chapters.objects.get(id = parent.chapter.id)
        return ChapterInfoSerializer(info).data

    class Meta:
        model = CourseChapters
        fields = ['id','chapter_info',"progress","video_watched","total_video_watched"]



class CourseVideoReportSerializer(serializers.ModelSerializer) :
    chapter_info = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField('get_progress')
    video_watched = serializers.SerializerMethodField('get_video_watched')
    total_video_watched = serializers.SerializerMethodField('get_total_video_watched')

    def get_total_video_watched(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).count()
        return total_video_watched

    def get_video_watched(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        return total_video_watched
    
    def get_progress(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        if total_video_watched > parent.chapter.no_of_videos_duration:
            return 100
        else:
            if parent.chapter.no_of_videos_duration == 0:
                return 0
            return math.ceil(total_video_watched * 100 / parent.chapter.no_of_videos_duration)

    
    def get_chapter_info(self, parent):
        info = Chapters.objects.get(id = parent.chapter.id)
        return ChapterInfoSerializer(info).data

    class Meta:
        model = CourseChapters
        fields = ['id','chapter_info',"progress","video_watched","total_video_watched"]



class TopicVideosRelationSerializer(serializers.ModelSerializer):
    total_videos = serializers.SerializerMethodField('get_total_videos')
    total_watched_videos = serializers.SerializerMethodField('get_total_watched_videos')
    total_watched_duration = serializers.SerializerMethodField('get_total_watched_duration')

    def get_total_videos(self, parent):
        count = Videos.objects.filter(chapter_topic = parent.id).count()
        return count

    def get_total_watched_videos(self, parent):
        count = UserLectureProgress.objects.filter(chapter_topic = parent.id, user = self.context.get('user')).count()
        return count

    def get_total_watched_duration(self, parent):
        count = UserLectureProgress.objects.filter(chapter_topic = parent.id, user = self.context.get('user')).aggregate(Sum('total_duration'))['total_duration__sum']
        return count

    class Meta:
        model = Videos
        fields = ['id','name','total_videos','total_watched_videos','total_watched_duration']


class ChapterTopicsReportSerializer(serializers.ModelSerializer) :
    topic_info = serializers.SerializerMethodField()
    total_watched_videos = serializers.SerializerMethodField('get_total_watched_videos')
    total_duration_watched_videos = serializers.SerializerMethodField('get_total_duration_watched_videos')

    def get_total_watched_videos(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(chapter_topic_id = parent.id, course_chapters_id = parent.course_chapters.id, course_id = parent.course_chapters.course.id, user = self.context.get('user')).count()
        return total_video_watched
    
    def get_total_duration_watched_videos(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(chapter_topic_id = parent.id, course_chapters_id = parent.course_chapters.id, course_id = parent.course_chapters.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        return total_video_watched
    
    class Meta:
        model = Chapters
        fields = ['id','topic_info',"total_watched_videos","total_duration_watched_videos","no_of_videos","no_of_video_duration"]


class ChapterVideoReportSerializer(serializers.ModelSerializer):
    chapter_info = serializers.SerializerMethodField()
    topics = serializers.SerializerMethodField()
    total_watched_videos = serializers.SerializerMethodField('get_total_watched_videos')
    total_duration_watched_videos = serializers.SerializerMethodField('get_total_duration_watched_videos')
    
    def get_total_duration_watched_videos(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        return total_video_watched
        
    def get_total_watched_videos(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).count()
        return total_video_watched
        

    def get_topics(self, parent):
        info = Chapters.objects.filter(course_chapters_id = parent.id)
        return ChapterTopicsReportSerializer(info,many=True, context={'user':self.context.get('user')}).data

    def get_chapter_info(self, parent):
        info = Chapters.objects.get(id = parent.chapters.id)
        return ChapterInfoSerializer(info).data

    class Meta:
        model = CourseChapters
        fields = ['id','chapter_info',"topics","total_watched_videos","total_duration_watched_videos","no_of_videos","no_of_video_duration"]

        

class VideoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Videos
        fields = ["id",'name',"transcoded_video","video_caption","video_duration"]


class SingleVideoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Videos
        fields = ['name',"description","vtt_file_path","transcode_video_file"]


class ChapterSingleVideosSerializer(serializers.ModelSerializer):
    last_watch_videos = serializers.SerializerMethodField('get_last_watch_videos')
    video_info = serializers.SerializerMethodField('get_video')
    def get_video(self, obj):
        video_detail  = Videos.objects.filter(id = obj.videos.id).first()
        return SingleVideoDetailSerializer(video_detail).data

    def get_last_watch_videos(self, parent):
        count_video = UserLectureProgress.objects.filter(video = parent.id, user = self.context.get('user')).count()
        if count_video > 0:
            count = UserLectureProgress.objects.filter(video = parent.id, user = self.context.get('user')).first()
            return count.total_duration
        return 0

    class Meta:
        model = Videos
        fields = ['id','video_info','last_watch_videos']



class GetUserNotesSerializer(serializers.ModelSerializer):
    lecture_info = serializers.SerializerMethodField('get_lecture_info')
    def get_lecture_info(self, obj):
        category = ChapterLectures.objects.filter(id=obj.chapter_lecture.id).first()
        serializer = ChapterLectureSerializer(category, context={'user':self.context.get('user')})
        return serializer.data

    class Meta:
        model = Notes
        fields = "__all__"



class CreateNoteSerializer(serializers.ModelSerializer) :
    course_id = serializers.IntegerField(required=True)
    lecture_id = serializers.IntegerField(required=True)
    note_content = serializers.CharField(required=True)
    duration = serializers.IntegerField(required=True)

    class Meta:
        model = Notes
        fields = ['lecture_id','course_id','note_content',"duration"]
        
        
    def validate(self, data):

        course = data.get('course_id')
        course_count = Course.objects.filter(id=course).count()
        if course_count == 0:
            raise serializers.ValidationError("Course does not exists")

        chapter_id = data.get('lecture_id')
        chapter_count = ChapterLectures.objects.filter(id=chapter_id).count()
        if chapter_count == 0:
            raise serializers.ValidationError("Lecture ID "+str(chapter_id)+" does not exists")

        return data

    def create(self , validate_data):

        courseInfo = Course.objects.get(id=validate_data.get('course_id'))
        chapter_lecture = ChapterLectures.objects.get(id=validate_data.get('lecture_id'))
        
        user = User.objects.get(id = self.context.get('user').id)

        chap = Notes(
            user = user,
            course = courseInfo,
            chapter_lecture = chapter_lecture,
            note_content = validate_data.get('note_content'),
            duration = validate_data.get('duration'),
        )
        chap.save()
        return chap
    

class EditNoteSerializer(serializers.ModelSerializer) :
    note_content = serializers.CharField(max_length = 255, required=True)
    duration = serializers.IntegerField(required=True)
    class Meta:
        model = Notes
        fields = ['note_content',"duration"]
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):    
        category.note_content = validate_data.get('note_content', category.note_content)
        category.duration = validate_data.get('duration', category.duration)
        category.save()

        return category
    

class WatchVideoSerializer(serializers.ModelSerializer) :
    duration = serializers.IntegerField(required=True)
    course_id = serializers.CharField(required=True)
    lecture_id = serializers.CharField(required=True)
    
    class Meta:
        model = Videos
        fields = ['duration','course_id',"lecture_id"]
        
    def validate(self, data):
        return data


    def create(self, validate_data):
        
        category = ChapterLectures.objects.get(id=validate_data.get('lecture_id'))
        course_chapter = CourseChapters.objects.get(course_id=validate_data.get('course_id'), chapter_id = category.chapter.id)

        watch_video_count = UserLectureProgress.objects.filter(video_id=category.video.id,user_id = self.context.get('user').id, course_chapters_id = course_chapter.id, course_id=validate_data.get('course_id'), chapter_lecture_id = category.id).count()

        if watch_video_count > 0:
            
            watch_video_info = UserLectureProgress.objects.filter(video_id=category.video.id,user_id = self.context.get('user').id, course_chapters_id = course_chapter.id, course_id=validate_data.get('course_id'), chapter_lecture_id = category.id).first()

            if watch_video_info.completed == 0:
                if validate_data.get('duration') > watch_video_info.total_duration:
                    watch_video_info.total_duration = validate_data.get('duration')
            if validate_data.get('duration') >= category.video.video_duration:
                watch_video_info.completed = 1
        else:
            watch_video_info = UserLectureProgress()
            watch_video_info.total_duration = validate_data.get('duration')
        
        watch_video_info.course = course_chapter.course
        watch_video_info.course_chapters = course_chapter
        watch_video_info.chapter_lecture = category
        watch_video_info.user = self.context.get('user')
        watch_video_info.video = category.video

        if validate_data.get('duration') >= category.video.video_duration:
            watch_video_info.total_duration = validate_data.get('duration')
            watch_video_info.end_time = datetime.now()
            watch_video_info.completed = 1
      
        watch_video_info.save()

        return watch_video_info
    

class PerformanceCourseChapterListingSerializer(serializers.ModelSerializer) :
    chapter_info = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField('get_progress')
    
    def get_progress(self, parent):
        total_video_watched = UserLectureProgress.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        if total_video_watched > parent.no_of_video_duration:
            return 100
        else:
            if parent.no_of_video_duration == 0:
                return 0
            return math.ceil(total_video_watched * 100 / parent.no_of_video_duration)

    def get_chapter_info(self, parent):
        info = Chapters.objects.get(id = parent.chapters.id)
        return ChapterInfoSerializer(info).data

    class Meta:
        model = CourseChapters
        fields = ['id','chapter_info',"progress"]



class CreateMyListSerializer(serializers.ModelSerializer) :
    title = serializers.CharField(max_length=255, required=True)
    course_id = serializers.CharField(required = True)
    class Meta:
        model = MyList
        fields = ['course_id','title']
        
        
    def validate(self, data):
        category = data.get('course_id').split(",")
        for cat in category:
            course_list = Course.objects.filter(id = cat).count()
            if course_list == 0:
                raise serializers.ValidationError("Invalid Course ID: "+str(cat))
            
        return data

    def create(self , validate_data):

        categ = MyList(
            user = self.context.get('user'),
            title = validate_data.get('title')
        )
        categ.save()
    

        category = validate_data.get('course_id').split(",")
        for cat in category:
            categ_ist = MyListCourses(
                my_list = categ,
                course = Course.objects.get(id = cat)
            )
            categ_ist.save()

        return True
    


class UpdateMyListSerializer(serializers.ModelSerializer) :
    list_id = serializers.IntegerField(required = True)
    course_id = serializers.CharField(required = True)
    class Meta:
        model = MyList
        fields = ['course_id',"list_id"]
        
        
    def validate(self, data):
        category = data.get('list_id')
        course_list = MyList.objects.filter(id = category).count()
        if course_list == 0:
            raise serializers.ValidationError("Invalid List ID")
            
        return data

    def create(self , validate_data):

        course_le = MyListCourses.objects.filter(course_id = validate_data.get('course_id'), my_list__user = self.context.get('user'), my_list_id = validate_data.get('list_id')).first()
        if course_le is None:
            cat = validate_data.get('course_id')
            categ = MyList.objects.filter(id = validate_data.get('list_id')).first()
            categ_ist = MyListCourses(
                my_list = categ,
                course = Course.objects.get(id = cat)
            )
            categ_ist.save()
        else:
            course_le.delete()

        return True
    


class MyListCourseSerializer(serializers.ModelSerializer):
    my_courses = serializers.SerializerMethodField()
    
    def get_my_courses(self, parent):
        info = MyListCourses.objects.filter(my_list_id = parent.id)
        return MyListCourseListingSerializer(info, many=True).data

    class Meta:
        model = MyList
        fields = ["id","title",'my_courses']


class MyListCourseListingSerializer(serializers.ModelSerializer):
    course = serializers.SerializerMethodField()
    
    def get_course(self, parent):
        info = Course.objects.get(id = parent.course.id)
        return CourseSerializer(info).data

    class Meta:
        model = MyListCourses
        fields = ["id",'course']


class AddReviewAndReviewSerializer(serializers.ModelSerializer) :
    review = serializers.CharField(required=True)
    rating = serializers.FloatField(required = True)
    course_id = serializers.IntegerField(required = True)

    class Meta:
        model = CourseReviewRating
        fields = ['review','rating',"course_id"]
        
        
    def validate(self, data):
        category = data.get('course_id')
        course_list = CourseReviewRating.objects.filter(course_id = category, user = self.context.get('user')).count()
        if course_list > 0:
            raise serializers.ValidationError("You have already given review for this course")
        
        return data

    def create(self , validate_data):
        
        categ = CourseReviewRating(
            user = self.context.get('user'),
            course = Course.objects.get(id = validate_data.get('course_id')),
            review = validate_data.get('review'),
            rating = validate_data.get('rating'),
            status = 0
        )
        categ.save()

        return True
    

class UpdateCourseReviewSerializer(serializers.ModelSerializer) :
    review = serializers.CharField(required=True)
    rating = serializers.FloatField(required = True)
    class Meta:
        model = CourseReviewRating
        fields = ['review',"rating"]
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):    
        
        category.review = validate_data.get('review', category.review)
        category.rating = validate_data.get('rating', category.rating)
        category.approved = 0
        category.save()

        stats = CourseReviewRating.objects.filter(course_id=category.course_id,approved = 1).aggregate(
                avg_rating=Avg('rating'),
                review_count=Count('id')
            )
        
        Course.objects.filter(id=category.course_id).update(
            avg_rating=stats['avg_rating'] or 0,
            total_reviews=stats['review_count']
        )

        return category
    

class GetUserCourseReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseReviewRating
        fields = ['id',"review","rating"]


class CourseInfoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id','name',"image","avg_rating","total_reviews","price","discount"]


class WishlistSerializer(serializers.ModelSerializer):
    course_info = serializers.SerializerMethodField('get_course_info')
    def get_course_info(self, obj):
        category = Course.objects.filter(id=obj.course.id).first()
        return CourseInfoListSerializer(category).data
    
    class Meta:
        model = UserWishlist
        fields = ['id',"course_info"]



class AddUserWishlistSerializer(serializers.ModelSerializer) :
    course_id = serializers.IntegerField(required=True)
    class Meta:
        model = UserWishlist
        fields = ['course_id']

    def validate(self, data):
        return data


    def create(self , validate_data):
        course = Course.objects.filter(id = validate_data.get("course_id")).first()
        if course is None:
            raise serializers.ValidationError("Invalid course ID")

        user = self.context.get('user')
        wishlist = UserWishlist.objects.filter(course_id = validate_data.get("course_id"), user = self.context.get('user')).count()
        if wishlist > 0:
            UserWishlist.objects.filter(course_id = validate_data.get("course_id"), user = self.context.get('user')).delete()
        else:
            noti = UserWishlist()
            noti.user = user
            noti.course = Course.objects.filter(id = validate_data.get("course_id")).first()
            noti.save()

        return True
    


class UserNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationSetting
        fields = ["id",'promotional',"announcements","reminders","instructor_notification","new_login"]


class UpdateUserNotificationSettingSerializer(serializers.ModelSerializer):
    promotional = serializers.BooleanField(required=True)
    announcements = serializers.BooleanField(required=True)
    reminders = serializers.BooleanField(required=True)
    instructor_notification = serializers.BooleanField(required=True)
    new_login = serializers.BooleanField(required=True)

    class Meta:
        model = UserNotificationSetting
        fields = ['promotional','announcements','reminders','instructor_notification','new_login']

    def validate(self, data):
        return data
    
    
    def create(self , validate_data):
        user = self.context.get('user')

        try:
            noti = UserNotificationSetting.objects.get(user = user)
        except UserNotificationSetting.DoesNotExist:
            noti = UserNotificationSetting()
            noti.user = user

        noti.promotional = validate_data.get('promotional')
        noti.announcements = validate_data.get('announcements')
        noti.reminders = validate_data.get('reminders')
        noti.instructor_notification = validate_data.get('instructor_notification')
        noti.new_login = validate_data.get('new_login')
        noti.save()

        return noti
    

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotifications
        fields = '__all__'


class ChangeNotificationSerializer(serializers.ModelSerializer):
    notification_id = serializers.ListField(required=True)
    class Meta:
        model = UserNotifications
        fields = ["notification_id"]
        
    def validate(self, data):
        return data

    def create(self , validate_data):
        UserNotifications.objects.filter(id__in=validate_data.get('notification_id')).update(status=True)
        return True