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
from mini_lms.utils import *



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

        log_activity(
            user=self.context.get('user'),
            action=ActivityLog.ActionType.PROGRESS,
            entity_type='Course',
            entity_id = obj.id,
            metadata=self.context.get('user').first_name+" "+self.context.get('user').last_name + " reached "+ video_duration_progress+"% in "+ obj.name +"!"
        )
        return video_duration_progress

    class Meta:
        model = Course
        fields = ['id',"name","progress"]


class OrderCoursesSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField('get_progress')
    course_started = serializers.SerializerMethodField('get_course_started')

    def get_course_started(self, obj):
        user_course =  UserCourses.objects.filter(user= self.context.get('user'), course_id = obj.id).first()
        return user_course.is_started
    
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
        fields = ['id',"name","short_description","image","avg_rating","total_reviews","updated_at","progress","course_started"]


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


class MarkCourseStartedSerializer(serializers.ModelSerializer) :
    course_id = serializers.IntegerField(required=True)
    
    class Meta:
        model = UserCourses
        fields = ['course_id']
        
        
    def validate(self, data):

        course = data.get('course_id')
        course_count = Course.objects.filter(id=course).count()
        if course_count == 0:
            raise serializers.ValidationError("Course does not exists")
        return data

    def create(self , validate_data):

        user_courses = UserCourses.objects.filter(
            user=self.context.get('user'), 
            course_id=validate_data.get('course_id')
        )
        user_courses.update(is_started=True)

        log_activity(
            user=self.context.get('user'),
            action=ActivityLog.ActionType.COURSE_STARTED,
            entity_type='Course',
            entity_id=validate_data.get('course_id'),
            metadata=self.context.get('user').first_name+" "+self.context.get('user').last_name + "started course "+ user_courses.course.name+"."
        )
        return True


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

        if chapter_lecture.lecture_type == 1:
            content_name = chapter_lecture.video.name
        else:
            content_name = chapter_lecture.ebook.name

        log_activity(
            user=self.context.get('user'),
            action=ActivityLog.ActionType.NOTE_CREATED,
            entity_type='Course',
            entity_id = validate_data.get('lecture_id'),
            metadata=self.context.get('user').first_name+" "+self.context.get('user').last_name + " note created in"+ content_name+"."
        )

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

        if category.chapter_lecture.lecture_type == 1:
            content_name = category.chapter_lecture.video.name
        else:
            content_name = category.chapter_lecture.ebook.name
            
        log_activity(
            user=category.user,
            action=ActivityLog.ActionType.NOTE_UPDATED,
            entity_type='Course',
            entity_id = category.chapter_lecture.id,
            metadata=category.user.first_name+" "+category.user.last_name + " note updated in"+ content_name+"."
        )

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
        print(category.chapter)
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

        log_activity(
            user=self.context.get('user'),
            action=ActivityLog.ActionType.LESSON_STARTED,
            entity_type='Course',
            entity_id = validate_data.get('lecture_id'),
            metadata=self.context.get('user').first_name+" "+self.context.get('user').last_name + "started lecture "+ category.video.name+"."
        )

        if validate_data.get('duration') >= category.video.video_duration:
            watch_video_info.total_duration = validate_data.get('duration')
            watch_video_info.end_time = datetime.now()
            watch_video_info.completed = 1
            log_activity(
                user=self.context.get('user'),
                action=ActivityLog.ActionType.LESSON_COMPLETED,
                entity_type='Course',
                entity_id = validate_data.get('lecture_id'),
                metadata=self.context.get('user').first_name+" "+self.context.get('user').last_name + "completed lecture "+ category.video.name+"."
            )
      
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
            status = True
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
        category.status = True
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
    

class AllowEmptyDateField(serializers.DateField):
    def to_internal_value(self, data):
        # If the data is an empty string, treat it as None
        if data == '':
            return None
        return super().to_internal_value(data)
    
class CreateRemindersSerializer(serializers.ModelSerializer) :
    title = serializers.CharField(max_length=255, required=True)
    course_id = serializers.IntegerField(required = True)
    frequency = serializers.IntegerField(required=True)
    time = serializers.TimeField(required=True)
    date = AllowEmptyDateField(required=False, allow_null=True)
    days = serializers.CharField(max_length=255, required=False, allow_blank=True)

    class Meta:
        model = LearningReminders
        fields = ['course_id','title',"frequency","time","date","days"]
        
        
    def validate(self, data):
        category = data.get('course_id')
        course_list = Course.objects.filter(id = category).count()
        if course_list == 0:
            raise serializers.ValidationError("Invalid Course ID: "+str(category))
        
        return data

    def create(self , validate_data):

        course_info = Course.objects.filter(id = validate_data.get('course_id')).first()

        categ = LearningReminders(
            course = course_info,
            user = self.context.get('user'),
            title = validate_data.get('title'),
            frequency = validate_data.get('frequency'),
            time = validate_data.get('time'),
            date = validate_data.get('date'),
            days = validate_data.get('days')
        )
        categ.save()

        return categ
    


class UpdateReminderSerializer(serializers.ModelSerializer) :
    reminder_id = serializers.IntegerField(required = True)
    title = serializers.CharField(max_length=255, required=True)
    course_id = serializers.IntegerField(required = True)
    frequency = serializers.IntegerField(required=True)
    time = serializers.TimeField(required=True)
    date = AllowEmptyDateField(required=False, allow_null=True)
    days = serializers.CharField(max_length=255, required=False, allow_blank=True)

    class Meta:
        model = LearningReminders
        fields = ['course_id','title',"frequency","time","date","days","reminder_id"]
        
        
    def validate(self, data):
        category = data.get('reminder_id')
        course_list = LearningReminders.objects.filter(id = category).count()
        if course_list == 0:
            raise serializers.ValidationError("Invalid Reminder ID")
            
        return data

    def create(self , validate_data):

        course_info = Course.objects.filter(id = validate_data.get('course_id')).first()
        reminder = LearningReminders.objects.filter(id = validate_data.get('reminder_id')).first()
        reminder.title = validate_data.get('title')
        reminder.course = course_info
        reminder.frequency = validate_data.get('frequency')
        reminder.time = validate_data.get('time')
        reminder.date = validate_data.get('date')
        reminder.days = validate_data.get('days')
        reminder.save()

        return reminder
    


class RemindersListingSerializer(serializers.ModelSerializer):
    course = serializers.SerializerMethodField()
    
    def get_course(self, parent):
        info = Course.objects.get(id = parent.course.id)
        return CourseSerializer(info).data

    class Meta:
        model = LearningReminders
        fields = "__all__"



class ShareCourseAccessSerializer(serializers.ModelSerializer) :
    first_name = serializers.CharField(max_length = 255, required=True)
    last_name = serializers.CharField(max_length = 255, required=True)
    email = serializers.EmailField(max_length = 255, required=True)
    phone = serializers.CharField(max_length = 255, required=True)
    course_id = serializers.ListField(required=True)
    
    class Meta:
        model = Order
        fields = ['first_name',"last_name","email","phone",'course_id']
        
    def validate_course_id(self, value):
        if not value:
            raise serializers.ValidationError("Course ID list cannot be empty.")

        existing_ids = set(
            Course.objects.filter(id__in=value).values_list('id', flat=True)
        )
        
        missing_ids = set(value) - existing_ids
        
        if missing_ids:
            raise serializers.ValidationError(
                f"The following course IDs do not exist: {list(missing_ids)}"
            )
        return value
    

    def validate(self, data):

        course_order = Order.objects.filter(
            user_id=self.context.get('user').id, 
            isPaid=True, 
            payment_type=PaymentType.Subscription, 
            subscription_status=OrderStatus.Active
        ).order_by('-created_at').first()
        if course_order is None:
            raise serializers.ValidationError("You do not have an active subscription plan. Please subscribe to gain access.")

        no_of_licences = course_order.no_of_licence if course_order else 0 

        used_licences_count = User.objects.filter(
            corporate_id = self.context.get('user').id
        ).count()

        if used_licences_count >= no_of_licences:
            raise serializers.ValidationError("You have used all the student seats available under this subscription. Please upgrade your plan or purchase additional licenses to add more users.")
        
        return data


    def create(self , validate_data):

        password = generate_random_password(8)

        email_to_check = validate_data.get('email', '').lower()
        email_exists = User.objects.filter(email=email_to_check).exists()
        if email_exists:
            user_info = User.objects.filter(email=email_to_check).first()
            assign_role(user_info, "Student")

            user_info.email_verified = 1
            user_info.corporate = self.context.get('user')
            user_info.is_active = True
            user_info.save()

        else:
            info = { "first_name": validate_data.get('first_name'),"last_name": validate_data.get('last_name'), 'email': validate_data.get('email').lower(), 'password': password}

            user_info = User.objects.create_user(**info)
            assign_role(user_info, "Student")

            user_info.role = User.Student
            user_info.email_verified = 1
            user_info.corporate = self.context.get('user')
            user_info.is_active = True
            user_info.save()
        
        url = settings.BASE_URL+"/login"

        subject = 'Thank you for registering!'

        message = f''
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user_info.email, ]
        html_message = loader.render_to_string(
            'new_user_email.html',
            {
                'name': user_info.first_name +' '+ user_info.last_name,
                'verification_link': url,
                "email": user_info.email,
                "password": password,

            }
        )

        send_mail( subject, message, email_from, recipient_list,html_message=html_message )

        course_order = Order.objects.filter(
            user_id=self.context.get('user').id, 
            isPaid=True, 
            payment_type=PaymentType.Subscription, 
            subscription_status=OrderStatus.Active
        ).order_by('-created_at').first()

        cart_items = Course.objects.filter(id__in=validate_data.get('course_id'))
        for cart_course in cart_items:
            cart_order = UserCourses(
                order = course_order,
                course = cart_course,
                user = user_info,
                paid=True

            )
            cart_order.save()

        return user_info
    

class MyCourseDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id",'name']



class UserCoursesListSerializer(serializers.ModelSerializer):
    course_detail = MyCourseDetailSerializer(source="course", read_only=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pass the context to the nested serializer
        if 'context' in kwargs:
            self.fields['course_detail'].context.update(kwargs['context'])

    class Meta:
        model = UserCourses
        fields = ["id", "course_detail"]


class StudentListingSerializer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    courses = serializers.SerializerMethodField('get_courses')
    courses_progress = serializers.SerializerMethodField('get_courses_progress')
    
    def get_courses_progress(self, obj):
        users_courses = UserCourses.objects.filter(user=obj, paid=True).values_list("course")
        total_video_duration = Course.objects.filter(id__in = users_courses).aggregate(Sum('total_video_duration')).get('total_video_duration__sum')  or 0

        total_duration_video_watched = UserLectureProgress.objects.filter(course_id__in = users_courses, user_id = obj.id).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        video_duration_progress = 0
        if total_duration_video_watched > total_video_duration:
            video_duration_progress =  100
        else:
            if total_video_duration > 0:
                video_duration_progress =  math.ceil(total_duration_video_watched * 100 / total_video_duration)

        return video_duration_progress
    
    def get_courses(self, obj):
        users_courses = UserCourses.objects.filter(user=obj, paid=True).select_related("course").order_by("-id")
        return UserCoursesListSerializer(users_courses, many=True, context={"user": obj.id}).data
    
    class Meta:
        model = User
        fields = ['id','first_name','last_name', 'email','phone1',"is_active","date_joined","last_login","image","courses","courses_progress"]



class AssignCourseAccessSerializer(serializers.ModelSerializer) :
    user_id = serializers.IntegerField(required=True)
    course_id = serializers.ListField(required=True)
    
    class Meta:
        model = Order
        fields = ["user_id",'course_id']
    
    def validate_course_id(self, value):
        if not value:
            raise serializers.ValidationError("Course ID list cannot be empty.")

        existing_ids = set(
            Course.objects.filter(id__in=value).values_list('id', flat=True)
        )
        
        missing_ids = set(value) - existing_ids
        
        if missing_ids:
            raise serializers.ValidationError(
                f"The following course IDs do not exist: {list(missing_ids)}"
            )
        return value
    
    def validate(self, data):
        user_info = User.objects.get(id = data.get('user_id'))
        course_order = Order.objects.filter(
            user_id=self.context.get('user').id, 
            isPaid=True, 
            payment_type=PaymentType.Subscription, 
            subscription_status=OrderStatus.Active
        ).order_by('-created_at').first()

        cart_items = Course.objects.filter(id__in=data.get('course_id'))
        for cart_course in cart_items:
            if UserCourses.objects.filter(user=user_info, course=cart_course).exists():
                raise serializers.ValidationError(f"User have a already course access of x: {cart_course.name}")
            
        return data


    def create(self , validate_data):

        user_info = User.objects.get(id = validate_data.get('user_id'))
        course_order = Order.objects.filter(
            user_id=self.context.get('user').id, 
            isPaid=True, 
            payment_type=PaymentType.Subscription, 
            subscription_status=OrderStatus.Active
        ).order_by('-created_at').first()

        cart_items = Course.objects.filter(id__in=validate_data.get('course_id'))
        for cart_course in cart_items:
            cart_order = UserCourses(
                order = course_order,
                course = cart_course,
                user = user_info,
                paid=True

            )
            cart_order.save()

        return user_info


class RemoveCourseAccessSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=True)
    course_id = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )
    
    class Meta:
        model = Order
        fields = ["user_id", "course_id"]
    
    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User does not exist.")
        return value

    def validate_course_id(self, value):
        if not value:
            raise serializers.ValidationError("Course ID list cannot be empty.")

        existing_ids = set(
            Course.objects.filter(id__in=value).values_list('id', flat=True)
        )
        
        missing_ids = set(value) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(
                f"The following course IDs do not exist: {list(missing_ids)}"
            )
        return value
    
    def validate(self, data):
        user_id = data.get('user_id')
        course_ids = data.get('course_id')
        
        user_info = User.objects.get(id=user_id)
        
        assigned_course_ids = set(
            UserCourses.objects.filter(
                user=user_info, 
                course_id__in=course_ids
            ).values_list('course_id', flat=True)
        )
        
        not_assigned = set(course_ids) - assigned_course_ids
        
        if not_assigned:
            course_names = list(Course.objects.filter(id__in=not_assigned).values_list('name', flat=True))
            raise serializers.ValidationError(
                f"User does not have access to these courses: {', '.join(course_names)}"
            )
            
        return data

    def create(self, validated_data):
        user_id = validated_data.get('user_id')
        course_ids = validated_data.get('course_id')
        
        user_info = User.objects.get(id=user_id)

        UserCourses.objects.filter(
            user=user_info, 
            course_id__in=course_ids
        ).delete()

        return user_info
    

class ParentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ["id","name","description","bg_code","text_code","icon"]
        
        
class CourseCategorySerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    category_info = serializers.SerializerMethodField('get_category_info')
    
    def get_category_info(self, obj):
        category = Categories.objects.filter(id=obj.category.id).first()
        return ParentCategorySerializer(category).data
    
    class Meta:
        model = Course
        fields = ["id","category_info","created_at"]


class GetUserProgressSerializer(serializers.ModelSerializer):
    avg_progress = serializers.SerializerMethodField('get_avg_progress')
    enrolled_students = serializers.SerializerMethodField('get_enrolled_students')
    categories = serializers.SerializerMethodField('get_categories')
    certificates = serializers.SerializerMethodField('get_certificates')

    def get_certificates(self, obj):
        user_course =  UserCertificates.objects.filter(user_id__in= self.context.get('users_id'), course_id = obj.id).count()
        return user_course
    
    def get_categories(self, obj):
        category = CourseCategories.objects.filter(course_id=obj.id)
        return CourseCategorySerializer(category, many=True).data
    

    def get_enrolled_students(self, obj):
        user_course =  UserCourses.objects.filter(user_id__in= self.context.get('users_id'), course_id = obj.id).count()
        return user_course
    
    def get_avg_progress(self, obj):
        users_id = UserCourses.objects.filter(user_id__in = self.context.get('users_id'), course_id = obj.id).values_list("user",flat=True)
        user_id_list = users_id
        num_users = len(user_id_list)
        
        if num_users == 0 or not obj.total_video_duration or obj.total_video_duration <= 0:
            return 0

        total_duration_watched_group = UserLectureProgress.objects.filter(
            course_id=obj.id, 
            user_id__in=user_id_list
        ).aggregate(total=Sum('total_duration')).get('total') or 0

        max_possible_duration_group = obj.total_video_duration * num_users

        if total_duration_watched_group >= max_possible_duration_group:
            overall_progress = 100
        else:
            overall_progress = math.ceil(
                (total_duration_watched_group * 100) / max_possible_duration_group
            )

        return overall_progress

    class Meta:
        model = Course
        fields = ['id',"name","short_description","image","avg_rating","total_reviews","updated_at","avg_progress","enrolled_students","categories","certificates"]



class ReshareUserLoginDetailSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=True)
    
    class Meta:
        model = User
        fields = ["user_id"]
    
    def validate_user_id(self, value):
        if not User.objects.filter(id=value, corporate_id = self.context.get('user')).exists():
            raise serializers.ValidationError("User does not exist.")
        return value

    def validate(self, data):
        return data

    def create(self, validated_data):
        user_id = validated_data.get('user_id')
        
        user_info = User.objects.get(id=user_id)

        url = settings.BASE_URL+"/login"
        
        password = generate_random_password(8)

        user_info.set_password(password)
        user_info.save()

        subject = 'Thank you for registering!'

        message = f''
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user_info.email, ]
        html_message = loader.render_to_string(
            'new_user_email.html',
            {
                'name': user_info.first_name +' '+ user_info.last_name,
                'verification_link': url,
                "email": user_info.email,
                "password": password,
            }
        )

        send_mail( subject, message, email_from, recipient_list,html_message=html_message )

        return user_info
    


class AssignSingleCourseAccessSerializer(serializers.ModelSerializer) :
    course_id = serializers.IntegerField(required=True)
    user_id = serializers.ListField(required=True)
    
    class Meta:
        model = Order
        fields = ["user_id",'course_id']
    
    def validate_course_id(self, value):
           
        if not Course.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f"The following course ID do not exist: {value}"
            )
        return value
    
    def validate(self, data):
        user_info = User.objects.filter(id__in = data.get('user_id'))
        cart_items = Course.objects.filter(id=data.get('course_id')).first()
        for user in user_info:
            if UserCourses.objects.filter(user=user, course=cart_items).exists():
                raise serializers.ValidationError(f"User have a already course access of : {cart_items.name}")
            
        return data


    def create(self , validate_data):

        user_info = User.objects.filter(id__in = validate_data.get('user_id'))
        course_order = Order.objects.filter(
            user_id=self.context.get('user').id, 
            isPaid=True, 
            payment_type=PaymentType.Subscription, 
            subscription_status=OrderStatus.Active
        ).order_by('-created_at').first()

        cart_items = Course.objects.filter(id=validate_data.get('course_id')).first()
        for user in user_info:
            cart_order = UserCourses(
                order = course_order,
                course = cart_items,
                user = user,
                paid=True
            )
            cart_order.save()

        return user_info
    


class GetCourseAccessStudentsSerializer(serializers.ModelSerializer) :
    course_id = serializers.IntegerField(required=True)
    
    class Meta:
        model = UserCourses
        fields = ['course_id']
    
    def validate_course_id(self, value):
           
        if not Course.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f"The following course ID do not exist: {value}"
            )
        return value
    
    def validate(self, data):
        return data
    

class StudentBasicDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','first_name','last_name', 'email']


class UserCoursesDetailSerializer(serializers.ModelSerializer):
    course_detail = MyCourseDetailSerializer(source="course", read_only=True)
    courses_progress = serializers.SerializerMethodField('get_courses_progress')
    certificate = serializers.SerializerMethodField('get_certificate')
            
    def get_certificate(self, obj):
        get_certificate = UserCertificates.objects.filter(user_id = obj.user.id, course_id = obj.course.id).first()
        if get_certificate is not None:
            return get_certificate.certificate_url
        return None
        
    def get_courses_progress(self, obj):
        total_video_duration = Course.objects.filter(id = obj.course.id).aggregate(Sum('total_video_duration')).get('total_video_duration__sum')  or 0

        total_duration_video_watched = UserLectureProgress.objects.filter(course_id = obj.course.id, user_id = obj.user.id).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        video_duration_progress = 0
        if total_duration_video_watched > total_video_duration:
            video_duration_progress =  100
        else:
            if total_video_duration > 0:
                video_duration_progress =  math.ceil(total_duration_video_watched * 100 / total_video_duration)

        return video_duration_progress
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pass the context to the nested serializer
        if 'context' in kwargs:
            self.fields['course_detail'].context.update(kwargs['context'])

    class Meta:
        model = UserCourses
        fields = ["id", "course_detail","courses_progress","is_started","certificate"]


class GetStudentDetailSerializer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    courses = serializers.SerializerMethodField('get_courses')
    
    def get_courses(self, obj):
        users_courses = UserCourses.objects.filter(user=obj, paid=True).select_related("course").order_by("-id")
        return UserCoursesDetailSerializer(users_courses, many=True, context={"user": obj.id}).data
    
    class Meta:
        model = User
        fields = ['id','first_name','last_name', 'email','phone1',"is_active","date_joined","last_login","image","courses"]



class GetChapterQuizListSerializer(serializers.ModelSerializer):
    chapter = serializers.SerializerMethodField('get_chapter')
    total_question = serializers.SerializerMethodField('get_total_question')
    
    def get_total_question(self, obj):
        option = QuizQuestions.objects.filter(chapter_quiz_id=obj.id).count()
        return option
    
    
    def get_chapter(self, obj):
        if obj.chapter is None:
            return []
        category = Chapters.objects.filter(id=obj.chapter.id).first()
        return ChapterInfoSerializer(category).data
    
    class Meta:
        model = ChapterQuizs
        fields = ["id","name","description","thumbnail","chapter","status","pass_percentage","total_question","created_at"]


class PracticeTestListingSerializer(serializers.ModelSerializer):
    quiz = serializers.SerializerMethodField('get_quiz')
    def get_quiz(self, obj):
        users_courses = ChapterQuizs.objects.filter(id=obj.quiz.id).first()
        return GetChapterQuizListSerializer(users_courses).data

    result = serializers.SerializerMethodField('get_result')
    def get_result(self, obj):
        if obj.quiz.pass_percentage > obj.score:
            return "Fail"
        return "Pass"

    class Meta:
        model = PracticeTests
        fields = ['id','start_time',"end_time",'status',"result","total_question","total_right_answer_given","total_wrong_answer_given","total_time_taken",'score',"created_at","quiz"]


class StudentLoginActivitySerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    
    class Meta:
        model = UserLoginActivity
        fields = ["id","login_IP","device_id","country","device_type","created_at"]