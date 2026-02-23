from django.db import models
from django_softdelete.models import SoftDeleteModel
from simple_history.models import HistoricalRecords
from django.utils import timezone 


class QuestionForum(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.CASCADE)
    question_title = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Question Forum'
        verbose_name_plural = 'Question Forum'
        
    def __str__(self):
        return '%s' % self.id
    

class Answers(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    question = models.ForeignKey('QuestionForum', null=True, blank=True, on_delete=models.CASCADE)
    question_title = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Answers'
        verbose_name_plural = 'Answers'
        
    def __str__(self):
        return '%s' % self.id
    


class TicketStatus(models.IntegerChoices):
    New = 1, 'New'
    Open = 2, 'Open'
    OnHold = 3, 'OnHold'
    Closed = 4, 'Closed'


class SupportTickets(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    subject = models.TextField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    status = models.IntegerField(choices=TicketStatus.choices,default=TicketStatus.New)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Support Tickets'
        verbose_name_plural = 'Support Tickets'
        
    def __str__(self):
        return '%s' % self.id
    

class TicketReplies(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    ticket = models.ForeignKey('SupportTickets', null=True, blank=True, on_delete=models.CASCADE)
    message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Ticket Replies'
        verbose_name_plural = 'Ticket Replies'
        
    def __str__(self):
        return '%s' % self.id
    
