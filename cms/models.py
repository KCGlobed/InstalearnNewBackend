from django.db import models
from django_softdelete.models import SoftDeleteModel
from mini_lms.gcloud import GoogleCloudPrivateMediaFileStorage
import uuid
from django.utils import timezone 
from simple_history.models import HistoricalRecords


class PartnerImages(SoftDeleteModel):
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image = models.FileField(upload_to="landing/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Partner Images'
        verbose_name_plural = 'Partner Images'



class Testimonials(SoftDeleteModel):
    testimonials_type = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    qualification = models.CharField(max_length=255, null=True, blank=True)
    college = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    image = models.FileField(upload_to="landing/", null=True, blank=True)
    featured = models.IntegerField(default=0)
    visible = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Testimonials'
        verbose_name_plural = 'Testimonials'


class FAQTopic(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQ Topic'
        verbose_name_plural = 'FAQ Topic'


class FAQs(models.Model):
    faq_topic = models.ForeignKey('FAQTopic', null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQs'
        verbose_name_plural = 'FAQs'