from django.db import models

class UserLectureProgress(models.Model):
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.CASCADE)
    course_chapters = models.ForeignKey('courses.CourseChapters', null=True, blank=True, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    chapter_lecture = models.ForeignKey('courses.ChapterLectures', null=True, blank=True, on_delete=models.CASCADE)
    video = models.ForeignKey('courses.Videos', null=True, blank=True, on_delete=models.CASCADE)
    total_duration = models.IntegerField(default=0,null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    completed = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Lecture Progress'
        verbose_name_plural = 'User Lecture Progress'

    def __str__(self):
        return '%s' % self.id
    

class Notes(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.CASCADE)
    chapter_video = models.ForeignKey('courses.ChapterLectures', null=True, blank=True, on_delete=models.SET_NULL)
    note_type = models.CharField(max_length=255, null=True, blank=True,default="video")
    note_content = models.TextField(null=True, blank=True)
    duration = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Notes'
        verbose_name_plural = 'Notes'
        
    def __str__(self):
        return '%s' % self.id
    

class UserCertificates(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.CASCADE)
    certificate_url = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User Certificates'
        verbose_name_plural = 'User Certificates'
        
    def __str__(self):
        return '%s' % self.id
    


class UserNotifications(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User Notifications'
        verbose_name_plural = 'User Notifications'
        
    def __str__(self):
        return '%s' % self.id
    

class MyList(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'My List'
        verbose_name_plural = 'My List'
        
    def __str__(self):
        return '%s' % self.id
    

class MyListCourses(models.Model):
    my_list = models.ForeignKey('MyList', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'My List Courses'
        verbose_name_plural = 'My List Courses'
        
    def __str__(self):
        return '%s' % self.id
    


class UserWishlist(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User Whishlist'
        verbose_name_plural = 'User Whishlist'
        
    def __str__(self):
        return '%s' % self.id
    