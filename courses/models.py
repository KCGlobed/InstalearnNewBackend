from django.db import models
from django_softdelete.models import SoftDeleteModel
from mini_lms.gcloud import GoogleCloudPrivateMediaFileStorage
import uuid
from django.utils import timezone 
from simple_history.models import HistoricalRecords


class Categories(SoftDeleteModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    parent = models.ForeignKey('Categories', null=True, blank=True, on_delete=models.SET_NULL)
    bg_code = models.CharField(max_length=255, null=True, blank=True)
    text_code = models.CharField(max_length=255, null=True, blank=True)
    icon = models.FileField(upload_to='mini_lms/images/', null=True, blank=True)
    order = models.IntegerField(default=0)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'Categories'
        verbose_name_plural = 'Categories'
        
    def __str__(self):
        return '%s' % self.id
    

class Tags(SoftDeleteModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tags'
        verbose_name_plural = 'Tags'
        
    def __str__(self):
        return '%s' % self.name
    

class CourseLevel(models.IntegerChoices):
    All = 1, 'All'
    Beginner = 2, 'Beginner'
    Intermediate = 3, 'Intermediate'
    Expert = 4, 'Expert'


class VideoDurationType(models.IntegerChoices):
    ExtraShort = 1, 'ExtraShort'
    Short = 2, 'Short'
    Medium = 3, 'Medium'
    Long = 4, 'Long'
    ExtraLong = 5, 'ExtraLong'
    

class Course(SoftDeleteModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    level = models.IntegerField(choices=CourseLevel.choices,default=CourseLevel.All)
    short_description = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    requirements = models.TextField(null=True, blank=True)
    duration = models.CharField(max_length=255,blank=True, null=True)
    job_info = models.CharField(max_length=255, null=True, blank=True)
    price = models.FloatField(default=0.0, null=True)
    discount = models.FloatField(default=0.0, null=True)
    total_reviews = models.IntegerField(default=0)
    total_video_duration = models.IntegerField(default=0)
    total_videos = models.IntegerField(default=0)
    avg_rating = models.FloatField(default=0.0)
    objectives_summary = models.JSONField(null=True, blank=True)
    feature_json = models.JSONField(null=True, blank=True)
    assessment_test_each_testlet_questions = models.IntegerField(default=30)
    assessment_test_testlets = models.IntegerField(default=10)
    mock_test_pattern = models.JSONField(null=True, blank=True)
    video_duration_type = models.IntegerField(choices=VideoDurationType.choices,default=VideoDurationType.ExtraShort)
    status = models.BooleanField(default=True)
    image = models.FileField(upload_to='mini_lms/images/', null=True, blank=True)
    banner_image = models.FileField(upload_to='mini_lms/images/', null=True, blank=True)
    created_by = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE, related_name="created_by")
    approved_by = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE, related_name="apporved_by")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  
    history = HistoricalRecords()  

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Course'
        
    def __str__(self):
        return '%s' % self.name
    
    

class CourseInstructors(SoftDeleteModel):
    course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.CASCADE)
    instructor = models.ForeignKey('instructor.InstructorProfile', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Course Instructors'
        verbose_name_plural = 'Course Instructors'

    def __str__(self):
        return '%s' % self.id
    

class CourseCategories(SoftDeleteModel):
    course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.CASCADE)
    category = models.ForeignKey('Categories', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Course Category'
        verbose_name_plural = 'Course Category'
        
    def __str__(self):
        return '%s' % self.id
    

class CourseTags(SoftDeleteModel):
    course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.CASCADE)
    tags = models.ForeignKey('Tags', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Course Tags'
        verbose_name_plural = 'Course Tags'
        
    def __str__(self):
        return '%s' % self.id
    

class FrequentlyBoughtCourse(SoftDeleteModel):
    course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.CASCADE, related_name="course")
    bought_course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.CASCADE, related_name="related_course")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Frequently Bought Course'
        verbose_name_plural = 'Frequently Bought Course'
        
    def __str__(self):
        return '%s' % self.id
    

class CourseSampleVideos(SoftDeleteModel):
    course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    thumbnail = models.ImageField(upload_to='mini_lms/images/', null=True, blank=True)
    videos = models.FileField(upload_to='mini_lms/videos/', null=True, blank=True)
    duration = models.CharField(max_length=255, null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    
    class Meta:
        verbose_name = 'Course Sample Vidoes'
        verbose_name_plural = 'Course Sample Vidoes'
        
    def __str__(self):
        return '%s' % self.id
    

class CourseImages(SoftDeleteModel):
    course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.CASCADE)
    image = models.FileField(upload_to='mini_lms/images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Course Images'
        verbose_name_plural = 'Course Images'
        
    def __str__(self):
        return '%s' % self.id
    

class CourseFaqs(SoftDeleteModel):
    course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.CASCADE)
    title = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    
    class Meta:
        verbose_name = 'Course FAQs'
        verbose_name_plural = 'Course FAQs'
        
    def __str__(self):
        return '%s' % self.id
    

class CourseReviewRating(SoftDeleteModel):
    course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    image = models.CharField(max_length=255, null=True, blank=True)
    review = models.TextField(null=True, blank=True)
    rating = models.FloatField(blank=True, null=True, default=0)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    
    class Meta:
        verbose_name = 'Course Reviews And Rating'
        verbose_name_plural = 'Course Reviews And Rating'
        
    def __str__(self):
        return '%s' % self.id
    
    
class Chapters(SoftDeleteModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    no_of_chapter_videos = models.IntegerField(default=0)
    no_of_videos = models.IntegerField(default=0)
    no_of_videos_duration = models.IntegerField(default=0)
    no_of_mcqs = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()


    class Meta:
        verbose_name = 'Chapters'
        verbose_name_plural = 'Chapters'

    def __str__(self):
        return '%s' % self.name
    


class LectureType(models.IntegerChoices):
    Video = 1, 'Video'
    Ebook = 2, 'Ebook'


class ChapterLectures(SoftDeleteModel):
    chapter = models.ForeignKey('Chapters', null=True, blank=True, on_delete=models.CASCADE)
    video = models.ForeignKey('Videos', null=True, blank=True, on_delete=models.CASCADE)
    ebook = models.ForeignKey('ChapterBooks', null=True, blank=True, on_delete=models.CASCADE)
    lecture_type = models.IntegerField(choices=LectureType.choices,default=LectureType.Video)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'Chapters Lectures'
        verbose_name_plural = 'Chapters Lectures'
        
    def __str__(self):
        return '%s' % self.id



class CourseChapters(SoftDeleteModel):
    chapter = models.ForeignKey('Chapters', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'Course Chapters'
        verbose_name_plural = 'Course Chapters'
        
    def __str__(self):
        return '%s' % self.id
    


class ChapterBooks(SoftDeleteModel):
    chapter = models.ForeignKey('Chapters', null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    book_file = models.FileField(storage=GoogleCloudPrivateMediaFileStorage(),upload_to='mini_lms/pdfs/', null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()


    class Meta:
        verbose_name = 'Chapter Books'
        verbose_name_plural = 'Chapter Books'

    def __str__(self):
        return '%s' % self.name
    


class Videos(SoftDeleteModel):
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4, blank=True, null=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    video_file = models.FileField(upload_to='mini_lms/videos/', null=True, blank=True)
    video_caption = models.CharField(max_length=255, null=True, blank=True)
    transcoded_video = models.CharField(max_length=255, null=True, blank=True)
    video_duration = models.IntegerField(default=0)
    status = models.BooleanField(default=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    signed_url = models.TextField(null=True, blank=True)
    is_uploaded = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    include_in_reference = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()


    class Meta:
        verbose_name = 'Videos'
        verbose_name_plural = 'Videos'

    def __str__(self):
        return '%s' % self.name



class TrailCourses(models.Model):
    course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    
    class Meta:
        verbose_name = 'Trail Courses'
        verbose_name_plural = 'Trail Courses'
        
    def __str__(self):
        return '%s' % self.id
    

class TrailCourseChapters(models.Model):
    trail_course = models.ForeignKey('TrailCourses', null=True, blank=True, on_delete=models.CASCADE)
    chapter = models.ForeignKey('CourseChapters', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Trail Course Chapters'
        verbose_name_plural = 'Trail Course Chapters'
        
    def __str__(self):
        return '%s' % self.id