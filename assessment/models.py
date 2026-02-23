from django.db import models
from questions.models import *

class AssessmentTests(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.SET_NULL)
    total_question = models.IntegerField(null=True, blank=True,default=0)
    total_right_answer_given = models.IntegerField(null=True, blank=True,default=0)
    total_wrong_answer_given = models.IntegerField(null=True, blank=True,default=0)
    total_never_attempt_question = models.IntegerField(null=True, blank=True,default=0)
    total_flag_marked = models.IntegerField(null=True, blank=True,default=0)
    total_time_taken = models.IntegerField(null=True, blank=True,default=0)
    avg_time_per_question = models.IntegerField(null=True, blank=True,default=0)
    score = models.IntegerField(null=True, blank=True,default=0)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    
    class Meta:
        verbose_name = 'Assessment Tests'
        verbose_name_plural = 'Assessment Tests'
        
    def __str__(self):
        return '%s' % self.id

class AssessmentTestQuestions(models.Model):
    assessment_test = models.ForeignKey('AssessmentTests', null=True, blank=True, on_delete=models.CASCADE)
    question = models.ForeignKey('questions.TestQuestions', null=True, blank=True, on_delete=models.CASCADE)
    selected_option = models.ForeignKey('questions.QuestionOptions', null=True, blank=True, on_delete=models.CASCADE)
    chapter = models.ForeignKey('courses.CourseChapters', null=True, blank=True, on_delete=models.SET_NULL)
    test_type = models.IntegerField(choices=QuestionType.choices,default=QuestionType.MCQ)
    result = models.BooleanField(default=False)
    attempted = models.BooleanField(default=False)
    guess_marked = models.BooleanField(default=False)
    time_taken = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Assessment Attempt Questions'
        verbose_name_plural = 'Assessment Attempt Questions'
        
    def __str__(self):
        return '%s' % self.id