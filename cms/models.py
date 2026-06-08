from django.db import models
from django_softdelete.models import SoftDeleteModel
from mini_lms.gcloud import GoogleCloudPrivateMediaFileStorage
import uuid
from django.utils import timezone 
from simple_history.models import HistoricalRecords
from django.utils.text import slugify


class PartnerImages(SoftDeleteModel):
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image = models.FileField(upload_to="landing/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Partner Images'
        verbose_name_plural = 'Partner Images'


class TestimonialsType(models.IntegerChoices):
    Placement = 1, 'Placement'
    Institutions = 2, 'Institutions'
    Corporate = 3, 'Corporate'
    Student = 4, 'Student'


class Testimonials(SoftDeleteModel):
    testimonials_type = models.IntegerField(choices=TestimonialsType.choices,default=TestimonialsType.Student)
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
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Contact Us'
        verbose_name_plural = 'Contact Us'
        
    def __str__(self):
        return '%s' % self.id
    


class BlogCategories(SoftDeleteModel):
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image = models.FileField(upload_to="mini_lms/blog_images/", null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Blog Categories'
        verbose_name_plural = 'Blog Categories'


class Blog(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    category = models.ForeignKey('BlogCategories', null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    canonical_url = models.CharField(max_length=255, null=True, blank=True)
    schema_markup  = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    meta_title = models.TextField(null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    meta_keys = models.TextField(null=True, blank=True)
    img_alt_tag = models.TextField(null=True, blank=True)
    reading_time = models.CharField(max_length=255, null=True, blank=True)
    tags = models.JSONField(null=True, blank=True)
    image = models.ImageField(upload_to="mini_lms/blog_images/", null=True, blank=True)
    feature_status = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    live_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Blog '
        verbose_name_plural = 'Blog '

    def save(self, *args, **kwargs):
        if not self.slug:
            original_slug = slugify(self.title)
            queryset = Blog.objects.all()
            next_num = 1
            slug = original_slug
            
            # Loop until a unique slug is found
            while queryset.filter(slug=slug).exists():
                slug = f"{original_slug}-{next_num}"
                next_num += 1
                
            self.slug = slug
            
        super().save(*args, **kwargs)
        
    def __str__(self):
        return '%s' % self.title
    

class BlogComment(models.Model):
    blog = models.ForeignKey('Blog', null=True, blank=True, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    status = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Blog Comment'
        verbose_name_plural = 'Blog Comment'

    def __str__(self):
        return '%s' % self.id
    


class CMSPages(models.Model):
    
    SOCIAL_LOGIN_CHOICES = (
        ('privacy_policy', 'privacy_policy'),
        ('about_us', 'about_us'),
        ('terms_conditions', 'terms_conditions')
    )

    title = models.CharField(max_length=255, null=True, blank=True)
    page_type = models.CharField(max_length=20, choices=SOCIAL_LOGIN_CHOICES, default='privacy_policy')
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(null=True, blank=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keys = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'CMS Pages'
        verbose_name_plural = 'CMS Pages'

    def __str__(self):
        return self.title
