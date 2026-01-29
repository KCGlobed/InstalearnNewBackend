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
from django.db.models import Sum



class OrderCoursesSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField('get_progress')
    def get_progress(self, obj):
        total_duration_video_watched = UserWatchedTopicVideos.objects.filter(course_id = obj.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
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
    course_instructor = serializers.SerializerMethodField()

    def get_course_instructor(self, parent):
        info = CourseInstructors.objects.filter(course_id = parent.id)
        return CourseInstructorSerializer(info, many=True).data

    class Meta:
        model = Course
        fields = ['id',"name","short_description","image","price","discount","objectives_summary","total_video_duration","total_video","avg_rating","total_reviews","updated_at","tags","course_instructor"]


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
        total_video_watched = UserWatchedTopicVideos.objects.filter(chapter_topic = obj, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        if total_video_watched > obj.no_of_video_duration:
            return 100
        else:
            if obj.no_of_video_duration == 0:
                return 0
            return math.ceil(total_video_watched * 100 / obj.no_of_video_duration)
        
    class Meta:
        model = ChapterTopics
        fields = ['id','name',"no_of_video_duration","no_of_videos","progress"]


class TopicsSerializer(serializers.ModelSerializer) :
    class Meta:
        model = Topics
        fields = ['name']


class ChapterTopicsSerializer(serializers.ModelSerializer) :
    topic_info = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField('get_progress')
    topic_videos = serializers.SerializerMethodField()
    
    def get_progress(self, parent):
        total_video_watched = UserWatchedTopicVideos.objects.filter(chapter_topic_id = parent.id, course_chapters_id = parent.course_chapters.id, course_id = parent.course_chapters.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        if total_video_watched > parent.no_of_video_duration:
            return 100
        else:
            if parent.no_of_video_duration == 0:
                return 0
            return math.ceil(total_video_watched * 100 / parent.no_of_video_duration)
        

    def get_topic_info(self, parent):
        info = Topics.objects.get(id = parent.topics.id)
        return TopicsSerializer(info).data
    
    def get_topic_videos(self, parent):
        info = TopicVideos.objects.filter(chapter_topics_id = parent.id).order_by('order','id')
        return TopicVideosSerializer(info,many=True).data
    
    class Meta:
        model = ChapterTopics
        fields = ['id','topic_info',"progress","topic_videos","no_of_videos","no_of_video_duration"]


class ChapterInfoSerializer(serializers.ModelSerializer) :
    class Meta:
        model = Chapters
        fields = ['name']


class DashboardCourseChapterListingSerializer(serializers.ModelSerializer) :
    chapter_info = serializers.SerializerMethodField()
    topics = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField('get_progress')
    
    def get_progress(self, parent):
        total_video_watched = UserWatchedTopicVideos.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        if total_video_watched > parent.no_of_video_duration:
            return 100
        else:
            if parent.no_of_video_duration == 0:
                return 0
            return math.ceil(total_video_watched * 100 / parent.no_of_video_duration)

    def get_topics(self, parent):
        info = ChapterTopics.objects.filter(course_chapters_id = parent.id)
        return ChapterTopicsSerializer(info,many=True,context={'user':self.context.get('user')}).data

    def get_chapter_info(self, parent):
        info = Chapters.objects.get(id = parent.chapters.id)
        return ChapterInfoSerializer(info).data

    class Meta:
        model = CourseChapters
        fields = ['id','chapter_info',"topics","progress","no_of_videos","no_of_video_duration"]



class TopicVideosRelationSerializer(serializers.ModelSerializer):
    total_videos = serializers.SerializerMethodField('get_total_videos')
    total_watched_videos = serializers.SerializerMethodField('get_total_watched_videos')
    total_watched_duration = serializers.SerializerMethodField('get_total_watched_duration')

    def get_total_videos(self, parent):
        count = TopicVideos.objects.filter(chapter_topic = parent.id).count()
        return count

    def get_total_watched_videos(self, parent):
        count = UserWatchedTopicVideos.objects.filter(chapter_topic = parent.id, user = self.context.get('user')).count()
        return count

    def get_total_watched_duration(self, parent):
        count = UserWatchedTopicVideos.objects.filter(chapter_topic = parent.id, user = self.context.get('user')).aggregate(Sum('total_duration'))['total_duration__sum']
        return count

    class Meta:
        model = TopicVideos
        fields = ['id','name','total_videos','total_watched_videos','total_watched_duration']


class ChapterTopicsReportSerializer(serializers.ModelSerializer) :
    topic_info = serializers.SerializerMethodField()
    total_watched_videos = serializers.SerializerMethodField('get_total_watched_videos')
    total_duration_watched_videos = serializers.SerializerMethodField('get_total_duration_watched_videos')

    def get_total_watched_videos(self, parent):
        total_video_watched = UserWatchedTopicVideos.objects.filter(chapter_topic_id = parent.id, course_chapters_id = parent.course_chapters.id, course_id = parent.course_chapters.course.id, user = self.context.get('user')).count()
        return total_video_watched
    
    def get_total_duration_watched_videos(self, parent):
        total_video_watched = UserWatchedTopicVideos.objects.filter(chapter_topic_id = parent.id, course_chapters_id = parent.course_chapters.id, course_id = parent.course_chapters.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        return total_video_watched
        

    def get_topic_info(self, parent):
        info = Topics.objects.get(id = parent.topics.id)
        return TopicsSerializer(info).data
    
    class Meta:
        model = ChapterTopics
        fields = ['id','topic_info',"total_watched_videos","total_duration_watched_videos","no_of_videos","no_of_video_duration"]


class ChapterVideoReportSerializer(serializers.ModelSerializer):
    chapter_info = serializers.SerializerMethodField()
    topics = serializers.SerializerMethodField()
    total_watched_videos = serializers.SerializerMethodField('get_total_watched_videos')
    total_duration_watched_videos = serializers.SerializerMethodField('get_total_duration_watched_videos')
    
    def get_total_duration_watched_videos(self, parent):
        total_video_watched = UserWatchedTopicVideos.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
        return total_video_watched
        
    def get_total_watched_videos(self, parent):
        total_video_watched = UserWatchedTopicVideos.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).count()
        return total_video_watched
        

    def get_topics(self, parent):
        info = ChapterTopics.objects.filter(course_chapters_id = parent.id)
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
        fields = ['name',"transcode_video_file","vtt_file_path"]


class TopicVideosSerializer(serializers.ModelSerializer):
    video_info = serializers.SerializerMethodField('get_video')
    def get_video(self, obj):
        video_detail  = Videos.objects.filter(id = obj.videos.id).first()
        return VideoDetailSerializer(video_detail).data
        
    class Meta:
        model = TopicVideos
        fields = ['id',"video_info"]

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
        count_video = UserWatchedTopicVideos.objects.filter(video = parent.id, user = self.context.get('user')).count()
        if count_video > 0:
            count = UserWatchedTopicVideos.objects.filter(video = parent.id, user = self.context.get('user')).first()
            return count.total_duration
        return 0

    class Meta:
        model = TopicVideos
        fields = ['id','video_info','last_watch_videos']



class GetUserNotesSerializer(serializers.ModelSerializer):
    video_title = serializers.SerializerMethodField('get_video')
    def get_video(self, obj):
        video_detail  = TopicVideos.objects.filter(id = obj.chapter_video.id).first()
        if video_detail is not None:
            return video_detail.name
        return ""

    class Meta:
        model = Notes
        fields = "__all__"



class CreateNoteSerializer(serializers.ModelSerializer) :
    course_id = serializers.IntegerField(required=True)
    video_id = serializers.IntegerField(required=True)
    note_content = serializers.CharField(required=True)
    duration = serializers.IntegerField(required=True)
    class Meta:
        model = Notes
        fields = ['video_id','course_id','note_content',"duration"]
        
        
    def validate(self, data):

        course = data.get('course_id')
        course_count = Course.objects.filter(id=course).count()
        if course_count == 0:
            raise serializers.ValidationError("Course does not exists")

        chapter_id = data.get('video_id')
        chapter_count = TopicVideos.objects.filter(id=chapter_id).count()
        if chapter_count == 0:
            raise serializers.ValidationError("Video ID "+str(chapter_id)+" does not exists")

        return data

    def create(self , validate_data):

        courseInfo = Course.objects.get(id=validate_data.get('course_id'))
        chaptervideo = TopicVideos.objects.get(id=validate_data.get('video_id'))
        
        user = User.objects.get(id = self.context.get('user').id)

        chap = Notes(
            user = user,
            course = courseInfo,
            chapter_video = chaptervideo,
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
    video_id = serializers.CharField(required=True)
    class Meta:
        model = TopicVideos
        fields = ['duration','video_id']
        
    def validate(self, data):
        return data


    def create(self, validate_data):
        
        category = TopicVideos.objects.get(id=validate_data.get('video_id'))

        watch_video_count = UserWatchedTopicVideos.objects.filter(video_id=category.id,user_id = self.context.get('user').id, chapter_topic_id = category.chapter_topics.id, course_chapters_id = category.chapter_topics.course_chapters.id, course_id = category.chapter_topics.course_chapters.course.id).count()

        if watch_video_count > 0:
            
            watch_video_info = UserWatchedTopicVideos.objects.get(video_id=category.id,user_id = self.context.get('user').id, chapter_topic_id = category.chapter_topics.id, course_chapters_id = category.chapter_topics.course_chapters.id, course_id = category.chapter_topics.course_chapters.course.id)

            if watch_video_info.completed == 0:
                if validate_data.get('duration') > watch_video_info.total_duration:
                    watch_video_info.total_duration = validate_data.get('duration')
            if validate_data.get('duration') >= category.no_of_video_duration:
                watch_video_info.completed = 1
        else:
            watch_video_info = UserWatchedTopicVideos()
            watch_video_info.total_duration = validate_data.get('duration')
        
        watch_video_info.course = category.chapter_topics.course_chapters.course
        watch_video_info.course_chapters = category.chapter_topics.course_chapters
        watch_video_info.chapter_topic = category.chapter_topics
        watch_video_info.user = self.context.get('user')
        watch_video_info.video = category

        if validate_data.get('duration') >= category.no_of_video_duration:
            watch_video_info.total_duration = validate_data.get('duration')
            watch_video_info.end_time = datetime.now()
            watch_video_info.completed = 1
      
        watch_video_info.save()

        return watch_video_info
    

class PerformanceCourseChapterListingSerializer(serializers.ModelSerializer) :
    chapter_info = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField('get_progress')
    
    def get_progress(self, parent):
        total_video_watched = UserWatchedTopicVideos.objects.filter(course_chapters_id = parent.id, course_id = parent.course.id, user = self.context.get('user')).aggregate(Sum('total_duration')).get('total_duration__sum')  or 0
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




class CompleteVideoListingSerializer(serializers.ModelSerializer) :
    chapter_info = serializers.SerializerMethodField()
    topics = serializers.SerializerMethodField()
    
    def get_topics(self, parent):
        info = ChapterTopics.objects.filter(course_chapters_id = parent.id)
        return CompleteVideoChapterTopicsSerializer(info,many=True,context={'user':self.context.get('user')}).data

    def get_chapter_info(self, parent):
        info = Chapters.objects.get(id = parent.chapters.id)
        return ChapterInfoSerializer(info).data

    class Meta:
        model = CourseChapters
        fields = ['id','chapter_info',"topics"]



class CompleteVideoChapterTopicsSerializer(serializers.ModelSerializer) :
    topic_info = serializers.SerializerMethodField()
    topic_videos = serializers.SerializerMethodField()
    
    def get_topic_info(self, parent):
        info = Topics.objects.get(id = parent.topics.id)
        return TopicsSerializer(info).data
    
    def get_topic_videos(self, parent):
        info = TopicVideos.objects.filter(chapter_topics_id = parent.id).order_by('order','id')
        return CompleteTopicVideosSerializer(info,many=True, context={'user':self.context.get('user')}).data
    
    class Meta:
        model = ChapterTopics
        fields = ['id','topic_info',"topic_videos"]


class CompleteTopicVideosSerializer(serializers.ModelSerializer):
    video_info = serializers.SerializerMethodField('get_video')
    video_progress = serializers.SerializerMethodField('get_video_progress')
    
    def get_video_progress(self, obj):
        total_video_watched = UserWatchedTopicVideos.objects.filter(video_id = obj.id, user = self.context.get('user')).first()
        if total_video_watched is not None:
            return total_video_watched.completed
        else:
            return 0
        
    def get_video(self, obj):
        video_detail  = Videos.objects.filter(id = obj.videos.id).first()
        return VideoDetailSerializer(video_detail).data
        
    class Meta:
        model = TopicVideos
        fields = ['id',"video_info","video_progress"]



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
    review = serializers.CharField(max_length=255, required=True)
    rating = serializers.IntegerField(required = True)
    course_id = serializers.IntegerField(required = True, min_value=5)
    class Meta:
        model = MyList
        fields = ['review','rating']
        
        
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
            name = self.context.get('user').first_name+" "+self.context.get('user').last_name,
            review = validate_data.get('review'),
            rating = validate_data.get('rating'),
            status = 0
        )
        categ.save()

        return True