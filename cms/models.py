from django.db import models
from django_softdelete.models import SoftDeleteModel
from mini_lms.gcloud import GoogleCloudPrivateMediaFileStorage
import uuid
from django.utils import timezone 
from simple_history.models import HistoricalRecords
from django.utils.text import slugify


class PartnerImages(models.Model):
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


class Testimonials(models.Model):
    testimonials_type = models.IntegerField(choices=TestimonialsType.choices,default=TestimonialsType.Student)
    name = models.CharField(max_length=255, null=True, blank=True)
    qualification = models.CharField(max_length=255, null=True, blank=True)
    college = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    image = models.FileField(upload_to="landing/", null=True, blank=True)
    status = models.BooleanField(default=True)
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
    facebook_url = models.CharField(max_length=255, null=True, blank=True)
    instagram_url = models.CharField(max_length=255, null=True, blank=True)
    linkedin_url = models.CharField(max_length=255, null=True, blank=True)
    twitter_url = models.CharField(max_length=255, null=True, blank=True)
    youtube_url = models.CharField(max_length=255, null=True, blank=True)
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

    def save(self, *args, **kwargs):
        if self.pk:
            old_title = CMSPages.objects.get(pk=self.pk).title
            if self.title != old_title:
                self.slug = None
                
        if not self.slug:
            original_slug = slugify(self.title)
            queryset = CMSPages.objects.all()
            next_num = 1
            slug = original_slug
            
            # Loop until a unique slug is found
            while queryset.filter(slug=slug).exists():
                slug = f"{original_slug}-{next_num}"
                next_num += 1
                
            self.slug = slug
            
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class HelpSupportTopics(models.Model):
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to="mini_lms/support_images/", null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Help & Support Topics'
        verbose_name_plural = 'Help & Support Topics'
    
    def save(self, *args, **kwargs):
        if self.pk:
            old_title = HelpSupportTopics.objects.get(pk=self.pk).title
            if self.title != old_title:
                self.slug = None
                
        if not self.slug:
            original_slug = slugify(self.title)
            queryset = HelpSupportTopics.objects.all()
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



class HelpSupportSubTopics(models.Model):
    main_topic = models.ForeignKey('HelpSupportTopics', null=True, blank=True, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Help Support Sub Topics'
        verbose_name_plural = 'Help Support Sub Topics'

    def save(self, *args, **kwargs):
        if self.pk:
            old_title = HelpSupportSubTopics.objects.get(pk=self.pk).title
            if self.title != old_title:
                self.slug = None

        if not self.slug:
            original_slug = slugify(self.title)
            queryset = HelpSupportSubTopics.objects.all()
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
    


class HelpSupportArticle(models.Model):
    main_topic = models.ForeignKey('HelpSupportTopics', null=True, blank=True, on_delete=models.CASCADE)
    sub_topic = models.ForeignKey('HelpSupportSubTopics', null=True, blank=True, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Help Support Article'
        verbose_name_plural = 'Help Support Article'

    def save(self, *args, **kwargs):
        if self.pk:
            old_title = HelpSupportArticle.objects.get(pk=self.pk).title
            if self.title != old_title:
                self.slug = None

        if not self.slug:
            original_slug = slugify(self.title)
            queryset = HelpSupportArticle.objects.all()
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



class JobApplications(models.Model):
    # Choice Lists based on the form's radio buttons
    EMPLOYMENT_STATUS_CHOICES = [
        ('student', 'Student'),
        ('fresher', 'Fresher'),
        ('self_employed', 'Self-Employed'),
        ('working_professional', 'Working Professional'),
    ]

    EXPERIENCE_CHOICES = [
        ('0-1', '0-1 Year'),
        ('1-3', '1-3 Years'),
        ('3-5', '3-5 Years'),
        ('5+', '5+ Years'),
    ]

    ROLE_CHOICES = [
        ('academic', 'Academic / Training'),
        ('sales_marketing', 'Sales & Marketing'),
        ('operations', 'Operations'),
        ('tech_it', 'Technology / IT'),
        ('content_design', 'Content / Design'),
        ('other', 'Other (Please specify)'),
    ]

    NOTICE_PERIOD_CHOICES = [
        ('immediate', 'Immediate'),
        ('15_days', '15 Days'),
        ('30_days', '30 Days'),
        ('more_than_30', 'More than 30 Days'),
    ]
    full_name = models.CharField(max_length=255,null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(max_length=20,null=True, blank=True)
    state = models.CharField(max_length=100,null=True, blank=True)
    city = models.CharField(max_length=100)
    highest_qualification = models.CharField(max_length=255, null=True, blank=True)
    current_employment_status = models.CharField(max_length=30, choices=EMPLOYMENT_STATUS_CHOICES,default='student')
    total_years_of_experience = models.CharField(max_length=10, choices=EXPERIENCE_CHOICES,default='0-1')
    role_applying_for = models.CharField(max_length=30, choices=ROLE_CHOICES,default='academic')
    other_role_specification = models.CharField(max_length=255, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    resume = models.FileField(upload_to="resume/", null=True, blank=True)
    linkedin_portfolio = models.URLField(max_length=500, blank=True, null=True)
    notice_period = models.CharField(max_length=20, choices=NOTICE_PERIOD_CHOICES,default='immediate')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Job Applications'
        verbose_name_plural = 'Job Applications'

    def __str__(self):
        return f"{self.full_name}"



class PromotionalBannerCampaign(models.Model):
    title = models.CharField(max_length=100, help_text="Internal name, e.g., Summer Sale 2026")
    display_text = models.CharField(max_length=255, help_text="e.g., Summer Sale is On!")
    coupons = models.ForeignKey('courses.Coupon', null=True, blank=True, on_delete=models.CASCADE)
    thumbnail = models.ImageField(upload_to='mini_lms/images/', null=True, blank=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(help_text="The exact date/time when the countdown hits zero")
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Promotional Banner Campaign'
        verbose_name_plural = 'Promotional Banner Campaign'

    def __str__(self):
        return f"{self.title}"



class CommunityCategories(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image = models.FileField(upload_to="landing/", null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Community Categories'
        verbose_name_plural = 'Community Categories'

    def save(self, *args, **kwargs):
        if self.pk:
            old_title = CommunityCategories.objects.get(pk=self.pk).title
            if self.title != old_title:
                self.slug = None

        if not self.slug:
            original_slug = slugify(self.title)
            queryset = CommunityCategories.objects.all()
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
    


class CommunityPosts(models.Model):
    category = models.ForeignKey('CommunityCategories', null=True, blank=True, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Help Support Article'
        verbose_name_plural = 'Help Support Article'

    def save(self, *args, **kwargs):
        if self.pk:
            old_title = CommunityPosts.objects.get(pk=self.pk).title
            if self.title != old_title:
                self.slug = None

        if not self.slug:
            original_slug = slugify(self.title)
            queryset = CommunityPosts.objects.all()
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



class CommunityPostComments(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    post = models.ForeignKey('CommunityPosts', null=True, blank=True, on_delete=models.CASCADE)
    comment = models.TextField(null=True, blank=True)
    status = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Community Post Comments'
        verbose_name_plural = 'Community Post Comments'

    def __str__(self):
        return '%s' % self.id