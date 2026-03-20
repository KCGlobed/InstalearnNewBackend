from rest_framework import serializers
from courses.models import *
from instructor.models import *
from mini_lms.validator import *
from django.core.validators import FileExtensionValidator
import os
from django.conf import settings
from google.cloud import storage
client = settings.GS_CREDENTIALS
import json
from google.oauth2 import service_account

from google.cloud.video.transcoder_v1 import TranscoderServiceClient
import calendar
import time
from mini_lms.utils import *
from datetime import datetime,timezone, timedelta

class ChapterListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapters
        fields = ["id","name","description"]


class ChaptersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapters
        fields = ["id","name","status","created_at"]



class ViewChapterDetailSerializer(serializers.ModelSerializer):
    topic_info = serializers.SerializerMethodField('get_topic_info')
    
    class Meta:
        model = Chapters
        fields = ["id","name","status","created_at","topic_info"]


class CreateChapterSerializer(serializers.ModelSerializer) :
    name = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(required=False)
    topic_id = serializers.ListField(child=serializers.IntegerField(required=True))
    
    class Meta:
        model = Chapters
        fields = ['name',"topic_id","description"]

    def validate(self, data):
        return data

    def create(self , validate_data):
        chapter_info = Chapters(
            name = validate_data.get('name'),
            description = validate_data.get('description'),
            status = True
        )
        chapter_info.save()
        topics_data = validate_data.pop('topic_id', []) 

        return chapter_info
    

class EditChapterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(required=False)
    topic_id = serializers.ListField(child=serializers.IntegerField(required=True))

    class Meta:
        model = Chapters
        fields = ['name',"topic_id","description"]
    
    def validate(self, data):
        return data


    def update(self , chapter_info, validate_data):
        
        chapter_info.name = validate_data.get('name', chapter_info.name)
        chapter_info.description = validate_data.get('description', chapter_info.description)
        chapter_info.save()

        topics_data = validate_data.pop('topic_id', None) 

        
        return chapter_info
    


class ChangeChapterstatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = Chapters
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    


class SubjectsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapters
        fields = ["id","name","status","created_at"]



class SubjectChapterInfoSerializer(serializers.ModelSerializer):
    chapter_detail = serializers.SerializerMethodField('get_chapter_detail')
    
    def get_chapter_detail(self, obj):
        category = Chapters.objects.filter(id=obj.chapter.id).first()
        return ChaptersSerializer(category).data
    
    class Meta:
        model = CourseChapters
        fields = ['id','order',"chapter_detail"]



class VideosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Videos
        fields = ["id","name","video_duration","status","created_at","include_in_reference"]



class VideoTopicInfoSerializer(serializers.ModelSerializer):
    chapter_detail = serializers.SerializerMethodField('get_chapter_detail')
    
    
    def get_chapter_detail(self, obj):
        if obj.chapter is not None:
            category = Chapters.objects.filter(id=obj.chapter.id).first()
            return ChaptersSerializer(category).data
        return []
    
    
    class Meta:
        model = Videos
        fields = ['id','order',"topic_detail","chapter_detail"]


class ViewVideoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Videos
        fields = ["id","uuid","name","video_file","video_caption","transcoded_video","video_duration","status","is_uploaded","is_completed","created_at","include_in_reference"]


class CreateVideoSerializer(serializers.ModelSerializer) :
    name = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    duration = serializers.IntegerField(required=True)
    include_in_reference = serializers.BooleanField(required=True)

    class Meta:
        model = Videos
        fields = ['name',"duration","description","include_in_reference"]
    
    def validate(self, data):
        return data

    def create(self , validate_data):
        
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
        unique_file_name = str(ts)+".mp4"
        file_name = validate_data.get('name')
        
        path = "mini_lms/videos"
        blob_path = f"media/{path}/{unique_file_name}"
        blob = bucket.blob(blob_path)

        content_type = 'video/mp4'
        
        signed_url = blob.generate_signed_url(
            version='v4',
            expiration=86400,
            method='PUT',
            content_type=content_type
        )

       
        
        video_info = Videos()
        video_info.name = file_name
        video_info.description = validate_data.get('description')
        video_info.include_in_reference = validate_data.get('include_in_reference')
        video_info.signed_url = signed_url
        video_info.file_name = unique_file_name
        video_info.video_file = path+"/"+unique_file_name
        video_info.video_duration = validate_data.get('duration')
        video_info.save()
                    
        return video_info
            

class MarkVideoUploadCompleteSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = Videos
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , video_info, validate_data):
        video_info.is_uploaded = validate_data.get('status', video_info.is_uploaded)
        video_info.save()

        client = TranscoderServiceClient(credentials=settings.GS_CREDENTIALS)
            
        bucketName, file_name = parse_gcs_url(video_info.video_file.url)
        
        input_uri = f'gs://public-media-files/'+str(file_name)
        output_uri = f'gs://public-media-files/media/mini_lms/transcoder/'

        current_GMT = time.gmtime()
        unique_id = str(calendar.timegm(current_GMT))

        video_file_name = "video_"+str(unique_id)
        job = {
            "input_uri": input_uri,
            "output_uri": output_uri,
            "template_id": "preset/web-hd",
            "config": {
                "elementary_streams": [
                    {
                        "key": "video-stream0",
                        "video_stream": {
                            "h264": {
                                "bitrate_bps": 5500000,
                                "frame_rate": 30,
                                "height_pixels": 720,
                                "width_pixels": 1280,
                                "gop_duration": "15.0s"
                            }
                        }
                    },
                    {
                        "key": "audio-stream0",
                        "audio_stream": {
                            "codec": "aac",
                            "bitrate_bps": 64000
                        }
                    }
                ],
                "mux_streams": [
                    {
                        "key": video_file_name,
                        "container": "ts",
                        "elementary_streams": [
                            "video-stream0","audio-stream0"
                        ],
                        "segment_settings": {
                            "segment_duration": "15.0s",
                            "individual_segments": True
                        }
                    }
                ],
                "manifests": [
                    {
                        "file_name": str(unique_id) + ".m3u8",
                        "mux_streams": [
                            video_file_name
                        ]
                    }
                ]
            }
        }
        
        job = client.create_job(
            parent=f'projects/{settings.GS_PROJECT_ID}/locations/asia-south1',
            job=job,
        )
        
        
        video_info.transcoded_video = 'media/mini_lms/transcoder/'+f'{video_file_name}.m3u8'
        video_info.is_completed = True
        video_info.save()
        


        return video_info



class EditVideoserializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length = 255, required=True)
    topic_id = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_empty=True
    )
    chapter_id = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_empty=True
    )
    update_video = serializers.BooleanField(required=True)
    duration = serializers.IntegerField(required=True)
    description = serializers.CharField(required=False)
    include_in_reference = serializers.BooleanField(required=True)
    
    class Meta:
        model = Videos
        fields = ['name',"topic_id","update_video","description","duration","chapter_id","include_in_reference"]
    

    def validate(self, data):
        return data


    def update(self , video_info, validate_data):
        
        if validate_data.pop('update_video') == True:
            
            storage_client = client
            bucket_name = settings.GS_BUCKET_NAME
            bucket = storage_client.bucket(bucket_name)

            current_GMT = time.gmtime()
            ts = calendar.timegm(current_GMT)
            unique_file_name = str(ts)+".mp4"
            file_name = validate_data.get('nam+e')
            
            path = "lms_2/videos"
            blob_path = f"media/{path}/{unique_file_name}"
            blob = bucket.blob(blob_path)

            content_type = 'video/mp4'


            # Generate the signed URL for a PUT request (uploading)
            signed_url = blob.generate_signed_url(
                version='v4',
                expiration=86400,
                method='PUT',
                content_type=content_type
            )

            
            
            video_info.name = file_name
            video_info.description = validate_data.get('description')
            video_info.include_in_reference = validate_data.get('include_in_reference')
            video_info.signed_url = signed_url
            video_info.file_name = unique_file_name
            video_info.video_file = path+"/"+unique_file_name
            video_info.video_duration = validate_data.get('duration')
            video_info.is_uploaded = False
            video_info.is_completed = False
            video_info.save()

        else:

            video_info.name = validate_data.get('name', video_info.name)
            video_info.duration = validate_data.get('duration', video_info.duration)
            video_info.include_in_reference = validate_data.get('include_in_reference', video_info.description)
            video_info.description = validate_data.get('description', video_info.description)
            video_info.save()

        return video_info
    


class ChangeVideostatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = Videos
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    

class ChapterBooksSerializer(serializers.ModelSerializer):
    chapter_detail = serializers.SerializerMethodField('get_chapter_detail')
    
    def get_chapter_detail(self, obj):
        category = Chapters.objects.filter(id=obj.chapter.id).first()
        return ChapterListSerializer(category).data
    
    class Meta:
        model = ChapterBooks
        fields = ['id',"name","chapter_detail","status","created_at"]



class ViewChapterBooksSerializer(serializers.ModelSerializer):
    chapter_detail = serializers.SerializerMethodField('get_chapter_detail')
    book_file = serializers.SerializerMethodField('get_book_file')
    
    def get_chapter_detail(self, obj):
        category = Chapters.objects.filter(id=obj.chapter.id).first()
        return ChapterListSerializer(category).data

    def get_book_file(self, obj):
        if obj.book_file is not None:
            bucket_name, object_name = parse_gcs_url(obj.book_file.url)
            expiration_time = datetime.now(timezone.utc) + timedelta(minutes=30)
            bucket = client.get_bucket(settings.GS_BUCKET_NAME_2)
            blob = bucket.blob(object_name)
            return blob.generate_signed_url(expiration=expiration_time)
        return None
    
    class Meta:
        model = ChapterBooks
        fields = ['id',"name","book_file","chapter_detail","status","created_at"]



class CreateChapterBookSerializer(serializers.ModelSerializer) :
    name = serializers.CharField(max_length = 255, required=True)
    chapter_id = serializers.IntegerField(required=True)
    book_file = serializers.FileField(required=True, validators=[FileExtensionValidator( ['pdf'])])
    
    class Meta:
        model = ChapterBooks
        fields = ['name',"chapter_id","book_file"]
        
    def validate(self, data):
        chapter_info = Chapters.objects.filter(id=data.get('chapter_id')).count()
            
        if chapter_info == 0:
            raise serializers.ValidationError("Invalid Chapter ID")
    
        return data

    def create(self , validate_data):
        chapter = Chapters.objects.filter(id=validate_data.get('chapter_id')).first()
        topic = ChapterBooks(
            name = validate_data.get('name'),
            chapter = chapter,
            book_file = validate_data.get('book_file'),
            status = True
        )
        topic.save()

        return topic
    

class EditChapterBookSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length = 255, required=True)
    chapter_id = serializers.IntegerField(required=False, allow_null=True)
    book_file = serializers.FileField(required=False, validators=[FileExtensionValidator( ['pdf'])])
    
    class Meta:
        model = ChapterBooks
        fields = ['name',"chapter_id","book_file"]
        
    def validate(self, data):
        return data


    def update(self , category, validate_data):
        
        category.name = validate_data.get('name', category.name)
        if validate_data.get('chapter_id') is not None:
            category.chapter = Chapters.objects.filter(id=validate_data.get('chapter_id')).first()
        if validate_data.get('book_file') is not None:
            category.book_file = validate_data.get('book_file')
        category.save()

        return category
    

class ChangeChapterBookstatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = ChapterBooks
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    


class HomepageCategorySerializer(serializers.ModelSerializer):
    total_courses = serializers.SerializerMethodField('get_total_courses')
    
    def get_total_courses(self, obj):
        return CourseCategories.objects.filter(category_id = obj.id).count()
    
    class Meta:
        model = Categories
        fields = ["id","name","total_courses","status","created_at"]


class HomepageTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ["id","name","status"]


class TagsListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ["id","name","status","created_at"]


class ParentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ["id","name","description"]


class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField('get_parent')
    
    def get_parent(self, obj):
        if obj.parent is not None:
            category = Categories.objects.filter(id=obj.parent.id).first()
            return ParentCategorySerializer(category).data
        return {}
    
    class Meta:
        model = Categories
        fields = ["id","name","parent","description","status","created_at"]



class CourseInstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","first_name","last_name","image"]


class HomepageCourseCategorySerializer(serializers.ModelSerializer):
    category_info = serializers.SerializerMethodField('get_category_info')
    def get_category_info(self, obj):
        category = Categories.objects.filter(id=obj.category.id).first()
        return ParentCategorySerializer(category).data
    
    class Meta:
        model = Course
        fields = ["id","category_info"]

class HomepageCourseDetailSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField('get_categories')
    created_by = serializers.SerializerMethodField('get_created_by')

    def get_categories(self, obj):
        category = CourseCategories.objects.filter(course_id=obj.id)
        return HomepageCourseCategorySerializer(category, many=True).data

    def get_created_by(self, obj):
        category = User.objects.filter(id=obj.created_by.id).first()
        return CourseInstructorSerializer(category).data
    
    class Meta:
        model = Course
        fields = ['name',"price","discount","objectives_summary","image","categories","duration","level","created_by","avg_rating"]


class HomepageTagWiseCoursesSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField('get_courses')
    
    def get_courses(self, obj):
        category = Course.objects.filter(id=obj.course.id).first()
        return HomepageCourseDetailSerializer(category).data
        
    class Meta:
        model = Categories
        fields = ["id","courses"]


class CreateTagsSerializer(serializers.ModelSerializer) :
    name = serializers.CharField(max_length = 255, required=True)
    
    class Meta:
        model = Tags
        fields = ['name']
        
    def validate(self, data):
        name_count = Tags.objects.filter(name = data.get('name')).count()
        if name_count > 0:
            raise serializers.ValidationError("Tag Name Already Exists!")

        return data

    def create(self , validate_data):
        topic = Tags(
            name = validate_data.get('name'),
            status = True
        )
        topic.save()

        return topic
    


class EditTagsSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length = 255, required=True)
    
    class Meta:
        model = Categories
        fields = ['name']
        
    def validate(self, data):
        return data


    def update(self , category, validate_data):
        category.name = validate_data.get('name', category.name)
        category.save()

        return category
    

class ChangeTagStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = Tags
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category


class CreateCategorySerializer(serializers.ModelSerializer) :
    name = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    
    class Meta:
        model = Categories
        fields = ['name',"description"]
        
    def validate(self, data):
        name_count = Categories.objects.filter(name = data.get('name')).count()
        if name_count > 0:
            raise serializers.ValidationError("Category Name Already Exists!")

        return data

    def create(self , validate_data):
        topic = Categories(
            name = validate_data.get('name'),
            description = validate_data.get('description'),
            status = True
        )
        topic.save()

        return topic
    


class EditCategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    
    class Meta:
        model = Categories
        fields = ['name',"description"]
        
    def validate(self, data):
        return data


    def update(self , category, validate_data):
        category.name = validate_data.get('name', category.name)
        category.description = validate_data.get('description', category.description)
        category.save()

        return category
    


class CreateSubCategorySerializer(serializers.ModelSerializer) :
    name = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    parent = serializers.IntegerField(required=True)
    
    class Meta:
        model = Categories
        fields = ['name',"parent","description"]
        
    def validate(self, data):
        parent = data.get('parent', None) 
        if parent is not None:
            parent_category = Categories.objects.filter(id = parent).count()
            if parent_category == 0:
                raise serializers.ValidationError("Invalid Parent Category ID!")
            
        
        name_count = Categories.objects.filter(name = data.get('name')).count()
        if name_count > 0:
            raise serializers.ValidationError("Category Name Already Exists!")

        return data

    def create(self , validate_data):
        parent = validate_data.get('parent', None) 
        parent_category = None
        if parent is not None:
            parent_category = Categories.objects.filter(id = parent).first()

        
        topic = Categories(
            name = validate_data.get('name'),
            parent = parent_category,
            description = validate_data.get('description'),
            status = True
        )
        topic.save()

        return topic
    


class EditSubCategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(max_length = 255, required=False, allow_blank=True)
    parent = serializers.IntegerField(required=True)
    
    class Meta:
        model = Categories
        fields = ['name',"parent","description"]
        
    def validate(self, data):
        parent = data.get('parent', None) 
        if parent is not None:
            parent_category = Categories.objects.filter(id = parent).count()
            if parent_category == 0:
                raise serializers.ValidationError("Invalid Parent Category ID!")

        return data


    def update(self , category, validate_data):
        parent = validate_data.get('parent', None) 
        parent_category = None
        if parent is not None:
            parent_category = Categories.objects.filter(id = parent).first()
        
        category.name = validate_data.get('name', category.name)
        category.parent = parent_category
        category.description = validate_data.get('description', category.description)
        category.save()

        return category
    

class ChangeCategoryStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = Categories
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    


class CourseInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id",'name','description',"short_description","duration","requirements","price","discount","feature_json","image","banner_image","objectives_summary","status","created_at"]


class CourseCategorySerializer(serializers.ModelSerializer):
    category_info = serializers.SerializerMethodField('get_category_info')
    course_info = serializers.SerializerMethodField('get_course_info')
    
    def get_course_info(self, obj):
        category = Course.objects.filter(id=obj.course.id).first()
        return CourseInfoSerializer(category).data
    
    def get_category_info(self, obj):
        category = Categories.objects.filter(id=obj.category.id).first()
        return ParentCategorySerializer(category).data
    
    class Meta:
        model = Course
        fields = ["id","category_info","course_info","created_at"]


class CourseSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField('get_categories')
    
    def get_categories(self, obj):
        category = CourseCategories.objects.filter(id=obj.id)
        return CourseCategorySerializer(category, many=True).data
    
    class Meta:
        model = Course
        fields = ["id","name","duration","categories","status","created_at"]


class CourseSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id"]


class CourseTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseTags
        fields = ["id","name"]

class ViewCourseDetailSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField('get_categories')
    tags = serializers.SerializerMethodField('get_tags')
    subject_info = serializers.SerializerMethodField('get_subject_info')
    
    def get_subject_info(self, obj):
        category = CourseChapters.objects.filter(course_id=obj.id)
        return CourseSubjectSerializer(category, many=True).data
    

    def get_tags(self, obj):
        category = CourseTags.objects.filter(course_id=obj.id)
        return CourseTagsSerializer(category, many=True).data
    
    def get_categories(self, obj):
        category = CourseCategories.objects.filter(course_id=obj.id)
        return CourseCategorySerializer(category, many=True).data
    
    class Meta:
        model = Course
        fields = ['name','description',"short_description","requirements","price","discount","feature_json","image","banner_image","categories","objectives_summary","tags","duration", "subject_info","mock_test_pattern","assessment_test_testlets","assessment_test_each_testlet_questions"]



class CreateCourseSerializer(serializers.ModelSerializer) :
    name = serializers.CharField(max_length=255, required=True)
    short_description = serializers.CharField(max_length=255, required=True)
    duration = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=True)
    requirements = serializers.CharField(required=False)
    price = serializers.IntegerField(required=True)
    discount = serializers.FloatField(required=False,allow_null=True)
    feature_json = serializers.JSONField(required=False)
    objectives_summary = serializers.JSONField(required=False)
    tags = serializers.ListField(required=True)
    image = serializers.ImageField(required=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp"])])
    banner_image = serializers.ImageField(required=False,allow_null=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp"])])
    category_id = serializers.ListField(child=serializers.IntegerField(required=True), required=True)
    
    class Meta:
        model = Course
        fields = ['name','description',"short_description","requirements","price","discount","feature_json","image","banner_image","category_id","objectives_summary","tags","duration"]

    # def validate_category_id(self, value):
    #     return validate_category_id_list(value)
        
    def validate(self, data):
        if data.get('discount') is not None:
            if int(data.get('price')) < int(data.get('discount')):
                raise serializers.ValidationError("Invalid Discounted price, because price will not greater than discounted price!")
        

        course_list = Course.objects.filter(name = data.get("name")).count()
        if course_list > 0:
            raise serializers.ValidationError("Course already exists with this name:"+str(data.get("name")))
    
        return data

    def create(self , validate_data):
        course = Course(
            name = validate_data.get('name'),
            description = validate_data.get('description'),
            short_description = validate_data.get('short_description'),
            requirements = validate_data.get('requirements'),
            price = validate_data.get('price'),
            discount = validate_data.get('discount'),
            feature_json = validate_data.get('feature_json'),
            image = validate_data.get('image'),
            banner_image = validate_data.get('banner_image'),
            objectives_summary = validate_data.get('objectives_summary'),
            duration = validate_data.get('duration')
        )
        course.save()

        category_data = validate_data.get('category_id')

        if len(category_data) > 0:
            for index , category_id in enumerate(category_data):
                cat = CourseCategories(
                        course = course,
                        category = Categories.objects.get(id = category_id)
                    )
                cat.save()

        
        tags_data = validate_data.get('tags') 

        if len(tags_data) > 0:
            for index , tags in enumerate(tags_data):
                tag = CourseTags(
                        course = course,
                        name = tags
                    )
                tag.save()


        return course
    


class CourseTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseTags
        fields = ["id","name","created_at"]


class CourseDetailSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField('get_categories')
    tags = serializers.SerializerMethodField('get_tags')
    
    def get_tags(self, obj):
        category = CourseTags.objects.filter(course_id=obj.id)
        return CourseTagsSerializer(category, many=True).data
    
    def get_categories(self, obj):
        category = CourseCategories.objects.filter(course_id=obj.id)
        return CourseCategorySerializer(category, many=True).data
    
    
    class Meta:
        model = Course
        fields = ["id",'name','description',"short_description","duration","requirements","price","discount","feature_json","image","banner_image","categories","objectives_summary","tags","status","created_at","mock_test_pattern","assessment_test_testlets","assessment_test_each_testlet_questions"]



class EditCourseSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, required=True)
    short_description = serializers.CharField(max_length=255, required=False)
    duration = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False)
    requirements = serializers.CharField(required=False)
    price = serializers.IntegerField(required=True)
    mock_test_pattern = serializers.JSONField(required=False)
    assessment_test_each_testlet_questions = serializers.IntegerField(required=False)
    assessment_test_testlets = serializers.IntegerField(required=False)
    discount = serializers.FloatField(required=False,allow_null=True)
    feature_json = serializers.JSONField(required=False)
    objectives_summary = serializers.JSONField(required=False)
    tags = serializers.ListField(required=False)
    image = serializers.ImageField(required=False,allow_null=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp"])])
    banner_image = serializers.ImageField(required=False,allow_null=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp"])])
    category_id = serializers.CharField(required=False)
    
    class Meta:
        model = Course
        fields = ['name','description',"short_description","requirements","price","discount","feature_json","image","banner_image","category_id","objectives_summary","tags","duration","mock_test_pattern","assessment_test_testlets","assessment_test_each_testlet_questions"]
        
    def validate(self, data):
        return data


    def update(self , course, validate_data):
        
        course.name = validate_data.get('name', course.name)
        course.description = validate_data.get('description', course.description)
        course.short_description = validate_data.get('short_description', course.short_description)
        course.requirements = validate_data.get('requirements', course.requirements)
        course.mock_test_pattern = validate_data.get('mock_test_pattern', course.mock_test_pattern)
        course.assessment_test_testlets = validate_data.get('assessment_test_testlets', course.assessment_test_testlets)
        course.assessment_test_each_testlet_questions = validate_data.get('assessment_test_each_testlet_questions', course.assessment_test_each_testlet_questions)
        course.price = validate_data.get('price', course.price)
        course.duration = validate_data.get('duration', course.duration)
        course.discount = validate_data.get('discount', course.discount)
        course.feature_json = validate_data.get('feature_json', course.feature_json)
        if validate_data.get('image') is not None:
            course.image = validate_data.get('image')
        if validate_data.get('banner_image') is not None:
            course.banner_image = validate_data.get('banner_image', course.banner_image)
        course.objectives_summary = validate_data.get('objectives_summary', course.objectives_summary)
        course.save()


        category_data = validate_data.get('category_id').split(",")

        if len(category_data) > 0:
            CourseCategories.objects.filter(course_id = course.id).delete()
            for index , category_id in enumerate(category_data):
                cat = CourseCategories(
                        course = course,
                        category = Categories.objects.get(id = category_id)
                    )
                cat.save()

        
        tags_data = validate_data.get('tags') 

        if len(tags_data) > 0:
            CourseTags.objects.filter(course_id = course.id).delete()
            for index , tags in enumerate(tags_data):
                tag = CourseTags(
                        course = course,
                        name = tags
                    )
                tag.save()


        return course
    

class ChangeCourseStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = Categories
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    

class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ["id","name"]



class CategoriesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ["id","name"]


class CourseSampleVideoListSerializer(serializers.ModelSerializer) :
    class Meta:
        model = CourseSampleVideos
        fields = ['id','name',"thumbnail","videos","duration"]


class AssignChapterCourseSerializer(serializers.ModelSerializer):
    chapter_id = serializers.ListField(child=serializers.IntegerField(required=True))

    class Meta:
        model = Chapters
        fields = ['name',"chapter_id"]
    
    def validate(self, data):
        return data


    def update(self , course_info, validate_data):

        chapter_data = validate_data.pop('chapter_id', None) 

        if chapter_data is not None:
            current_topic_links = {
                link.chapter_id: link for link in course_info.coursechapterss_set.all()
            }

            # Lists for batch operations
            links_to_create = []
            links_to_update = []
            received_chapter_ids = set()

           
            for index, topic_link_data in enumerate(chapter_data):
                subject_obj = Chapters.objects.get(id = topic_link_data)
                order_for_chapter = index + 1
                received_chapter_ids.add(subject_obj.id) 

                if subject_obj.id in current_topic_links:
                    link_instance = current_topic_links[subject_obj.id]
                    if link_instance.order != order_for_chapter:
                        link_instance.order = order_for_chapter
                        links_to_update.append(link_instance)
                else:
                    links_to_create.append(
                        CourseChapters(
                            course=course_info,
                            subject=subject_obj,
                            order=order_for_chapter
                        )
                    )
            
            # Perform bulk operations
            if links_to_create:
                CourseChapters.objects.bulk_create(links_to_create)
            
            if links_to_update:
                CourseChapters.objects.bulk_update(links_to_update, ['order'])
            
            chapter_ids_to_delete = current_topic_links.keys() - received_chapter_ids
            if chapter_ids_to_delete:
                CourseChapters.objects.filter(
                    course=course_info,
                    chapter_id__in=chapter_ids_to_delete
                ).delete()

        return course_info


        
class SubjectInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapters
        fields = ["id","name"]


class CourseSubjectInfoSerializer(serializers.ModelSerializer):
    subject_detail = serializers.SerializerMethodField('get_subject_detail')
    def get_subject_detail(self, obj):
        category = Chapters.objects.filter(id=obj.subject.id).first()
        return SubjectInfoSerializer(category).data
    
    class Meta:
        model = CourseChapters
        fields = ['id',"subject_detail"]


class CourseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id",'name']


class CreateTrailCourseSerializer(serializers.ModelSerializer) :
    course_id = serializers.IntegerField(required=True)
    chapter_id = serializers.ListField(child=serializers.IntegerField(required=True))

    class Meta:
        model = TrailCourses
        fields = ["course_id", "chapter_id"]
    
    def validate(self, data):
        course = data.get('course_id')
        trail = Course.objects.filter(id = course).count()
        if trail == 0:
            raise serializers.ValidationError(
                "Course ID not exists."
            )
            
        return data


    def create(self, validate_data):
        
        course_instance = Course.objects.get(id=validate_data.get('course_id'))
        chapter_data = validate_data.get('chapter_id', []) 
        chap, created = TrailCourses.objects.update_or_create(
                            course=course_instance,
                            defaults={'course': course_instance}
                        )

        info = []
        if len(chapter_data) > 0:
            processed_chapter_ids = []

            for index, chapter_id in enumerate(chapter_data):
                chapter_obj = CourseChapters.objects.get(id=chapter_id)
                
                chap_instance, created = TrailCourseChapters.objects.update_or_create(
                    chapter=chapter_obj,
                    trail_course=chap,
                    defaults={
                        'trail_course': chap,
                        "chapter":chapter_obj,
                    }
                )
                
                processed_chapter_ids.append(chap_instance.id)

            TrailCourseChapters.objects.filter(course_id=course_data).exclude(id__in=processed_chapter_ids).delete()
           
        return info
    


class SubjectsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapters
        fields = ["id","name","status","created_at"]



class SubjectChapterInfoSerializer(serializers.ModelSerializer):
    chapter_detail = serializers.SerializerMethodField('get_chapter_detail')
    
    def get_chapter_detail(self, obj):
        category = Chapters.objects.filter(id=obj.chapter.id).first()
        return ChaptersSerializer(category).data
    
    class Meta:
        model = CourseChapters
        fields = ['id','chapter',"chapter_detail"]


class TrailCoursesSerializer(serializers.ModelSerializer):
    course_detail = serializers.SerializerMethodField('get_course_detail')
    chapter_detail = serializers.SerializerMethodField('get_chapter_detail')

    def get_chapter_detail(self, obj):
        category = CourseChapters.objects.filter(trail_course_id=obj.id)
        return CourseListSerializer(category).data
    
    def get_course_detail(self, obj):
        category = Course.objects.filter(id=obj.course.id).first()
        return CourseListSerializer(category).data
    
    class Meta:
        model = TrailCourses
        fields = ['id',"course_detail","chapter_detail"]



class GenerateUploadSignedUrlSerializer(serializers.ModelSerializer) :
    name = serializers.CharField(max_length = 255, required=True)

    class Meta:
        model = Videos
        fields = ['name']

    def validate(self, data):
        return data

    def create(self , validate_data):
        
        storage_client = client
        bucket_name = settings.GS_BUCKET_NAME
        bucket = storage_client.bucket(bucket_name)

        file_name = validate_data.get('name')
        content_type = 'video/mp4'

        blob_path = f"media/lms_2/videos/{file_name}"
        blob = bucket.blob(blob_path)

        # Generate the signed URL for a PUT request (uploading)
        signed_url = blob.generate_signed_url(
            version='v4',
            expiration=3600,  # URL is valid for 10 minutes (600 seconds)
            method='PUT',
            content_type=content_type
        )

        return signed_url


class ChapterDropdownListSerializer(serializers.ModelSerializer):
    topic_list = serializers.SerializerMethodField('get_topic_list')

    class Meta:
        model = Chapters
        fields = ["id","name","topic_list"]




class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id',"first_name","last_name","email"]





class ChaptersHistorySerializer(serializers.ModelSerializer):
    history_user = UserMinimalSerializer(read_only=True)
    history_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Chapters.history.model 
        fields = ['id',"history_id","history_change_reason","history_type","history_user","history_date"]



class CourseHistorySerializer(serializers.ModelSerializer):
    history_user = UserMinimalSerializer(read_only=True)
    history_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Course.history.model 
        fields = ['id',"history_id","history_change_reason","history_type","history_user","history_date"]


class EbooksHistorySerializer(serializers.ModelSerializer):
    history_user = UserMinimalSerializer(read_only=True)
    history_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = ChapterBooks.history.model 
        fields = ['id',"history_id","history_change_reason","history_type","history_user","history_date"]


class VideoHistorySerializer(serializers.ModelSerializer):
    history_user = UserMinimalSerializer(read_only=True)
    history_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Videos.history.model 
        fields = ['id',"history_id","history_change_reason","history_type","history_user","history_date"]




class UpdateCoursesSampleVideoSerializer(serializers.ModelSerializer) :
    course_id = serializers.IntegerField(required=True)
    thumbnail = serializers.ImageField(required=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp"])])
    videos = serializers.FileField(required=False,allow_null=True, validators=[FileExtensionValidator( ['mp4', 'avi', 'mov', 'mkv'])])
    duration = serializers.IntegerField(required=True)
    name = serializers.CharField(required=True)
    class Meta:
        model = CourseSampleVideos
        fields = ['course_id','thumbnail',"videos","duration","name"]
        
        
    def validate(self, data):
        course = Course.objects.filter(id = data.get('course_id')).count()
        if course == 0:
            raise serializers.ValidationError("Invalid Course ID ")
        return data
        

    def create(self , validate_data):
        
        categ = CourseSampleVideos(
            course = Course.objects.get(id = validate_data.get('course_id')),
            name = validate_data.get('name'),
            thumbnail = validate_data.get('thumbnail'),
            videos = validate_data.get('videos'),
            duration = validate_data.get('duration')
        )
        categ.save()

        return True
    


class CourseInstructorsListSerializer(serializers.ModelSerializer) :
    instructor_info = serializers.SerializerMethodField()
    def get_instructor_info(self, parent):
        info = Instructor.objects.get(id = parent.instructor.id)
        return InstructorInfoserializer(info).data
    
    class Meta:
        model = CourseInstructors
        fields = ['id','instructor_info']


class InstructorInfoserializer(serializers.ModelSerializer) :
    class Meta:
        model = Instructor
        fields = ['id',"text_1","text_2","text_3","image","experience"]



class AddCourseInstructorsSerializer(serializers.ModelSerializer) :
    course_id = serializers.IntegerField(required=True)
    instructor_id = serializers.CharField(required = True)
    class Meta:
        model = CourseInstructors
        fields = ['instructor_id','course_id']
        
        
    def validate(self, data):
        category = data.get('instructor_id').split(",")
        for cat in category:
            course_list = Instructor.objects.filter(id = cat).count()
            if course_list == 0:
                raise serializers.ValidationError("Invalid Instructor ID: "+str(cat))
            
        return data

    def create(self , validate_data):
        category = validate_data.get('instructor_id').split(",")
        for cat in category:
            categ = CourseInstructors(
                instructor = Instructor.objects.get(id = cat),
                course = Course.objects.get(id = validate_data.get('course_id'))
            )
            categ.save()

        return True
    

class UpdateFAQStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)

    class Meta:
        model = CourseFaqs
        fields = ['status']
        

    def validate(self, data):
        return data

    def update(self, info, validate_data):

        info.visible = validate_data.get('status', info.visible)
        info.save()

        return info
    


class CourseFaqsListingSerializer(serializers.ModelSerializer) :
    class Meta:
        model = CourseFaqs
        fields = ['id','title','description','visible']


class CreateCourseFaqsSerializer(serializers.ModelSerializer) :
    course_id = serializers.IntegerField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=True)
    class Meta:
        model = CourseFaqs
        fields = ['title','description',"course_id"]
        
        
    def validate(self, data):

        return data

    def create(self , validate_data):
        chap = CourseFaqs(
            title = validate_data.get('title'),
            description = validate_data.get('description'),
            course = Course.objects.filter(id = validate_data.get('course_id')).first()
        )
        chap.save()
        return chap
    

class UpdateCourseFaqsSerializer(serializers.ModelSerializer) :
    course_id = serializers.IntegerField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=True)
    class Meta:
        model = CourseFaqs
        fields = ['title','description',"course_id"]
        
    def validate(self, data):
        return data


    def update(self , category, validate_data):
        category.title = validate_data.get('title', category.title)
        category.description = validate_data.get('description', category.description)
        category.course = Course.objects.filter(id = validate_data.get('course_id')).first()
        category.save()
        return category
    


class FrequentlyBoughtCourseListSerializer(serializers.ModelSerializer) :
    course_info = serializers.SerializerMethodField()
    def get_course_info(self, parent):
        info = Course.objects.get(id = parent.bought_course.id)
        return CourseInfoserializer(info).data
    
    class Meta:
        model = FrequentlyBoughtCourse
        fields = ['id','course_info']


class CourseInfoserializer(serializers.ModelSerializer) :
    class Meta:
        model = Course
        fields = ['id','name',"image"]




class AddRelatedCoursesSerializer(serializers.ModelSerializer) :
    course_id = serializers.IntegerField(required=True)
    related_course_id = serializers.CharField(required = True)
    class Meta:
        model = FrequentlyBoughtCourse
        fields = ['related_course_id','course_id']
        
        
    def validate(self, data):
        category = data.get('related_course_id').split(",")
        for cat in category:
            course_list = Course.objects.filter(id = cat).count()
            if course_list == 0:
                raise serializers.ValidationError("Invalid Topic ID: "+str(cat))
            
        return data

    def create(self , validate_data):
        category = validate_data.get('related_course_id').split(",")
        for cat in category:
            categ = FrequentlyBoughtCourse(
                bought_course = Course.objects.get(id = cat),
                course = Course.objects.get(id = validate_data.get('course_id'))
            )
            categ.save()

        return True