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



class PaymentMode(models.IntegerChoices):
    Test_Mode = 1, 'Test Mode'
    Live_Mode = 2, 'Live Mode'

class GeneralSettings(models.Model):
    payment_type = models.IntegerField(choices=PaymentMode.choices,default=PaymentMode.Test_Mode)
    test_public_key = models.CharField(max_length=255, null=True, blank=True)
    test_secret_key = models.CharField(max_length=255, null=True, blank=True)
    live_public_key = models.CharField(max_length=255, null=True, blank=True)
    live_secret_key = models.CharField(max_length=255, null=True, blank=True)
    no_days_trail = models.IntegerField(null=True, blank=True, default=7)
    try_for_free = models.IntegerField(null=True, blank=True, default=30)
    allow_device_restriction = models.BooleanField(default=False)
    allowed_desktop = models.IntegerField(null=True, blank=True, default=1)
    allowed_tablet = models.IntegerField(null=True, blank=True, default=1)
    allowed_phone = models.IntegerField(null=True, blank=True, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)
    
    class Meta:
        verbose_name = 'General Settings'
        verbose_name_plural = 'General Settings'
        
    def __str__(self):
        return '%s' % self.id



class ContactUs(models.Model):
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    attach_file = models.FileField(upload_to='landing/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Contact Us'
        verbose_name_plural = 'Contact Us'
        
    def __str__(self):
        return '%s' % self.id