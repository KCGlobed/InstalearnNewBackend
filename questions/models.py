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