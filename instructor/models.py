from django.db import models
from django_softdelete.models import SoftDeleteModel
from mini_lms.gcloud import GoogleCloudPrivateMediaFileStorage
import uuid
from django.utils import timezone 
from simple_history.models import HistoricalRecords


class InstructorProfile(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    text_1 = models.CharField(max_length=255, null=True, blank=True)
    text_2 = models.CharField(max_length=255, null=True, blank=True)
    text_3 = models.CharField(max_length=255, null=True, blank=True)
    experience = models.CharField(max_length=255, null=True, blank=True)
    linkedin_url = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image = models.FileField(upload_to="landing/", null=True, blank=True)
    company_image_1 = models.FileField(upload_to="landing/", null=True, blank=True)
    company_image_2 = models.FileField(upload_to="landing/", null=True, blank=True)
    visible = models.IntegerField(default=1)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Instructor Profile'
        verbose_name_plural = 'Instructor Profile'

    def __str__(self):
        return '%s' % self.id
    


    