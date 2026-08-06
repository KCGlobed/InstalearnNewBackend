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
    chapter_lecture = models.ForeignKey('courses.ChapterLectures', null=True, blank=True, on_delete=models.SET_NULL)
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
    

class UserNotificationSetting(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    promotional = models.BooleanField(default=False)
    announcements = models.BooleanField(default=False)
    reminders = models.BooleanField(default=False)
    instructor_notification = models.BooleanField(default=False)
    new_login = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    
    class Meta:
        verbose_name = 'User Notification Setting'
        verbose_name_plural = 'User Notification Setting'
        
    def __str__(self):
        return '%s' % self.id
    

class UserNotifications(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.CASCADE)
    announcement = models.ForeignKey('courses.CourseAnnouncements', null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=False)
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
    


class Frequency(models.IntegerChoices):
    Daily = 1, 'Daily'
    Weekly = 2, 'Weekly'
    Once = 3, 'Once'

class LearningReminders(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, null=True, blank=True)
    frequency = models.IntegerField(choices=Frequency.choices,default=Frequency.Daily)
    time = models.TimeField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    days = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 
    
    class Meta:
        verbose_name = 'Learning Reminders'
        verbose_name_plural = 'Learning Reminders'
        
    def __str__(self):
        return '%s' % self.id



class UserCurrentCourseLearning(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User Current Course Learning'
        verbose_name_plural = 'User Current Course Learning'
        
    def __str__(self):
        return '%s' % self.id


class LearningTargets(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.CASCADE)
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    @property
    def total_target_days(self) -> int:
        return sum([
            self.monday, self.tuesday, self.wednesday, 
            self.thursday, self.friday, self.saturday, self.sunday
        ])

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}'s Learning Target ({self.total_target_days} days)"