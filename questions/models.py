from django.db import models
from django_softdelete.models import SoftDeleteModel
from simple_history.models import HistoricalRecords
from django.utils import timezone 


class Level(models.IntegerChoices):
    LOW = 1, 'Low'
    MEDIUM = 2, 'Medium'
    HIGH = 3, 'High'

class QuestionType(models.IntegerChoices):
    MCQ = 1, 'MCQ'


class TestQuestions(SoftDeleteModel):
    id_number = models.CharField(max_length=255, null=True, blank=True)
    question_type = models.IntegerField(choices=QuestionType.choices,default=QuestionType.MCQ)
    level = models.IntegerField(choices=Level.choices,default=Level.LOW)
    pass_percentage = models.FloatField(default=0.0, null=True)
    chapter = models.ForeignKey('courses.Chapters', null=True, blank=True, on_delete=models.CASCADE)
    right_option = models.ForeignKey('QuestionOptions', null=True, blank=True, on_delete=models.SET_NULL)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Test Questions'
        verbose_name_plural = 'Test Questions'
        
    def __str__(self):
        return '%s' % self.id
    
    def restore(self, *args, **kwargs):
        self.deleted_at = None 
        self.restored_at = timezone.now()

        self.save()
    

class QuestionContents(SoftDeleteModel):
    test_question = models.ForeignKey('TestQuestions', null=True, blank=True, on_delete=models.CASCADE)
    question = models.TextField(null=True, blank=True)
    question_json = models.JSONField(null=True, blank=True)
    solution_description = models.TextField(null=True, blank=True)
    sub_questions = models.IntegerField(null=True, blank=True,default=1)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Question Contents'
        verbose_name_plural = 'Question Contents'
        
    def __str__(self):
        return '%s' % self.id
    

class QuestionOptions(SoftDeleteModel):
    test_question = models.ForeignKey('TestQuestions', null=True, blank=True, on_delete=models.CASCADE)
    option = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Question Options'
        verbose_name_plural = 'Question Options'
        
    def __str__(self):
        return '%s' % self.id
    


class ChapterQuizs(models.Model):
    chapter = models.ForeignKey('courses.Chapters', null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    thumbnail = models.ImageField(upload_to='mini_lms/images/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    pass_percentage = models.FloatField(default=0.0, null=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = 'Chapter Quizs'
        verbose_name_plural = 'Chapter Quizs'

    def __str__(self):
        return '%s' % self.name
    


class QuizQuestions(models.Model):
    test_question = models.ForeignKey('TestQuestions', null=True, blank=True, on_delete=models.CASCADE)
    chapter_quiz = models.ForeignKey('ChapterQuizs', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name = 'Quiz Questions'
        verbose_name_plural = 'Quiz Questions'
        
    def __str__(self):
        return '%s' % self.id
    


class PracticeTests(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.SET_NULL)
    chapter = models.ForeignKey('courses.Chapters', null=True, blank=True, on_delete=models.SET_NULL)
    quiz = models.ForeignKey('ChapterQuizs', null=True, blank=True, on_delete=models.SET_NULL)
    total_question = models.IntegerField(null=True, blank=True,default=0)
    total_right_answer_given = models.IntegerField(null=True, blank=True,default=0)
    total_wrong_answer_given = models.IntegerField(null=True, blank=True,default=0)
    total_never_attempt_question = models.IntegerField(null=True, blank=True,default=0)
    total_flag_marked = models.IntegerField(null=True, blank=True,default=0)
    total_time_taken = models.IntegerField(null=True, blank=True,default=0)
    score = models.IntegerField(null=True, blank=True,default=0)
    avg_time_per_question = models.IntegerField(null=True, blank=True,default=0)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    
    class Meta:
        verbose_name = 'Practice Tests'
        verbose_name_plural = 'Practice Tests'
        
    def __str__(self):
        return '%s' % self.id
    

class PracticeTestQuestions(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    practice_test = models.ForeignKey('PracticeTests', null=True, blank=True, on_delete=models.CASCADE)
    question = models.ForeignKey('questions.TestQuestions', null=True, blank=True, on_delete=models.CASCADE)
    selected_option = models.ForeignKey('questions.QuestionOptions', null=True, blank=True, on_delete=models.CASCADE)
    result = models.IntegerField(null=True, blank=True, default=0)  
    guess_marked = models.BooleanField(default=False)
    attempted = models.BooleanField(default=False)
    time_taken = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Practice Test Questions'
        verbose_name_plural = 'Practice Test Questions'
        
    def __str__(self):
        return '%s' % self.id