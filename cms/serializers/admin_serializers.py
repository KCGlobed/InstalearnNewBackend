from rest_framework import serializers
from cms.models import *
from courses.models import *
from django.db import transaction
from django.core.validators import FileExtensionValidator
from mini_lms.utils import *

class BlogCategoryInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategories
        fields = ["id","title"]

class BlogsListingSerializer(serializers.ModelSerializer):
    category_info = BlogCategoryInfoSerializer(source='category', read_only=True)

    class Meta:
        model = Blog
        fields = ["id","title","feature_status","status","image","created_at","category_info"]


class BlogInfoSerializer(serializers.ModelSerializer):
    category_info = BlogCategoryInfoSerializer(source='category', read_only=True)
    
    class Meta:
        model = Blog
        fields = "__all__"


class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = ["id","title"]

class BlogsCommentSerializer(serializers.ModelSerializer):
    blog_info = BlogSerializer(source='blog', read_only=True)
    
    class Meta:
        model = BlogComment
        fields = "__all__"


class CMSPagesListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CMSPages
        fields = "__all__"


class TestimonialsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonials
        fields = "__all__"


class ChangeBlogCommentStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = BlogComment
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    

class CreateBlogSerializer(serializers.ModelSerializer) :
    category_id = serializers.IntegerField(required=True)
    title = serializers.CharField(max_length = 255,required=True)
    canonical_url = serializers.CharField(max_length = 255,required=True)
    schema_markup = serializers.CharField(max_length = 255,required=True)
    reading_time = serializers.CharField(max_length = 255,required=False)
    tags = serializers.CharField(required=False)
    description = serializers.CharField(required=True)
    meta_title = serializers.CharField(required=True)
    meta_description = serializers.CharField(required=True)
    meta_keys = serializers.CharField(required=True)
    img_alt_tag = serializers.CharField(required=True)
    live_date = serializers.DateTimeField(required=True)
    created_by = serializers.CharField(max_length = 255,required=True)
    image = serializers.FileField(required=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp","svg"])])

    class Meta:
        model = Blog
        fields = ['title','description','created_by','image','category_id',"tags","reading_time","live_date","meta_title","meta_description","meta_keys","img_alt_tag","canonical_url","schema_markup"]
        
    def validate(self, data):
        course = data.get('category_id')
        course_count = BlogCategories.objects.filter(id=course).count()
        if course_count == 0:
            raise serializers.ValidationError("Blog Category does not exists")
        
        return data

    def create(self , validate_data):

        category = BlogCategories.objects.get(id = validate_data.get('category_id'))
        tags = None
        if validate_data.get('tags') is not None:
            tags = validate_data.get('tags').split(",")
        
        chap = Blog(
            user = self.context.get('user'),
            category = category,
            title = validate_data.get('title'),
            canonical_url = validate_data.get('canonical_url'),
            image = validate_data.get('image'),
            reading_time = validate_data.get('reading_time'),
            tags = tags,
            description = validate_data.get('description'),
            live_date = validate_data.get('live_date'),
            created_by = validate_data.get('created_by'),
            meta_title = validate_data.get('meta_title'),
            meta_description = validate_data.get('meta_description'),
            meta_keys = validate_data.get('meta_keys'),
            img_alt_tag = validate_data.get('img_alt_tag'),
            schema_markup = validate_data.get('schema_markup'),
        )
        chap.save()

        return chap
    

class EditBlogSerializer(serializers.ModelSerializer) :
    category_id = serializers.IntegerField(required=True)
    title = serializers.CharField(max_length = 255,required=True)
    description = serializers.CharField(required=True)
    tags = serializers.CharField(required=False)
    reading_time = serializers.CharField(max_length = 255,required=False)
    created_by = serializers.CharField(max_length = 255,required=True)
    meta_title = serializers.CharField(required=False, allow_blank=True)
    schema_markup = serializers.CharField(required=False, allow_blank=True)
    meta_description = serializers.CharField(required=False, allow_blank=True)
    meta_keys = serializers.CharField(required=False, allow_blank=True)
    img_alt_tag = serializers.CharField(required=False, allow_blank=True)
    live_date = serializers.DateTimeField(required=False)
    canonical_url = serializers.CharField(max_length = 255,required=True, allow_blank=True)
    image = serializers.FileField(required=False,allow_null=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp","svg"])])
    class Meta:
        model = Blog
        fields = ['title','description','created_by','image','category_id',"reading_time","tags","live_date","meta_title","meta_description","meta_keys","img_alt_tag","canonical_url","schema_markup"]
        
    def validate(self, data):
        return data


    def update(self , category, validate_data):

        tags = None
        if validate_data.get('tags') is not None:
            tags = validate_data.get('tags').split(",")

        category.title = validate_data.get('title', category.title)
        category.image = validate_data.get('image', category.image)
        category.canonical_url = validate_data.get('canonical_url', category.canonical_url)
        category.description = validate_data.get('description', category.description)
        category.created_by = validate_data.get('created_by', category.created_by)
        category.live_date = validate_data.get('live_date', category.live_date)
        category.tags = tags
        category.reading_time = validate_data.get('reading_time', category.reading_time)
        category.meta_title = validate_data.get('meta_title', category.meta_title)
        category.schema_markup = validate_data.get('schema_markup', category.schema_markup)
        category.meta_description = validate_data.get('meta_description', category.meta_description)
        category.meta_keys = validate_data.get('meta_keys', category.meta_keys)
        category.img_alt_tag = validate_data.get('img_alt_tag', category.img_alt_tag)
        category.save()

        return category
    
class ChangeBlogStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = Blog
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    
class ChangeBlogFeatureStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = Blog
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.feature_status = validate_data.get('status', category.feature_status)
        category.save()

        return category
    

class CreateUpdateCMSPageSerializer(serializers.ModelSerializer) :
    title = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    page_type = serializers.CharField(max_length = 255, required=True)
    meta_title = serializers.CharField(max_length = 255, required=True)
    meta_description = serializers.CharField(required=False, allow_blank=True)
    meta_keys = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = CMSPages
        fields = ['title',"description","page_type","meta_title","meta_description","meta_keys"]
        
    def validate(self, data):
        return data

    def create(self , validate_data):
        cms_page = CMSPages.objects.filter(page_type = validate_data.get('page_type')).first()
        if cms_page is not None:
            cms_page.title = validate_data.get('title', cms_page.title)
            cms_page.description = validate_data.get('description', cms_page.description)
            cms_page.page_type = validate_data.get('page_type', cms_page.page_type)
            cms_page.meta_title = validate_data.get('meta_title', cms_page.meta_title)
            cms_page.meta_description = validate_data.get('meta_description', cms_page.meta_description)
            cms_page.meta_keys = validate_data.get('meta_keys', cms_page.meta_keys)
            cms_page.save()
        else:
            cms_page = CMSPages(
                title = validate_data.get('title'),
                description = validate_data.get('description'),
                page_type = validate_data.get('page_type'),
                meta_title = validate_data.get('meta_title'),
                meta_description = validate_data.get('meta_description'),
                meta_keys = validate_data.get('meta_keys'),
                status = True
            )
            cms_page.save()

        return cms_page
    

class ChangeCMSPageStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = CMSPages
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    

class BlogCategoriesListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategories
        fields = ["id","title","description","status","image","created_at"]


class CreateBlogCategorySerializer(serializers.ModelSerializer) :
    title = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    image = serializers.FileField(required=False,allow_null=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp","svg"])])
    
    class Meta:
        model = BlogCategories
        fields = ['title',"description","image"]
        
    def validate(self, data):
        name_count = BlogCategories.objects.filter(title = data.get('title')).count()
        if name_count > 0:
            raise serializers.ValidationError("Title Already Exists!")

        return data

    def create(self , validate_data):
        category = BlogCategories(
            title = validate_data.get('title'),
            description = validate_data.get('description'),
            image = validate_data.get('image'),
            status = True
        )
        category.save()

        return category
    

class EditBlogCategorySerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    image = serializers.FileField(required=False,allow_null=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp","svg"])])
    
    class Meta:
        model = BlogCategories
        fields = ['title',"description","image"]
        
    def validate(self, data):
        return data


    def update(self , category, validate_data):
        category.title = validate_data.get('title', category.title)
        category.description = validate_data.get('description', category.description)
        category.image = validate_data.get('image', category.image)
        category.save()

        return category
    

class ChangeBlogCategoryStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = BlogCategories
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    

class FaqTopicListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQTopic
        fields = ["id","title","description","status","created_at"]


class CreateFaqTopicSerializer(serializers.ModelSerializer) :
    title = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = FAQTopic
        fields = ['title',"description"]
        
    def validate(self, data):
        name_count = FAQTopic.objects.filter(title = data.get('title')).count()
        if name_count > 0:
            raise serializers.ValidationError("Title Already Exists!")

        return data

    def create(self , validate_data):
        topic = FAQTopic(
            title = validate_data.get('title'),
            description = validate_data.get('description'),
            status = True
        )
        topic.save()

        return topic
    


class EditFAQTopicSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = FAQTopic
        fields = ['title',"description"]
        
    def validate(self, data):
        return data


    def update(self , category, validate_data):
        category.title = validate_data.get('title', category.title)
        category.description = validate_data.get('description', category.description)
        category.save()

        return category
    

class ChangeFAQTopicStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = FAQTopic
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    


class FaqListingSerializer(serializers.ModelSerializer):
    faq_topic = serializers.SerializerMethodField('get_faq_topic')
    
    def get_faq_topic(self, obj):
        if obj.faq_topic is not None:
            category = FAQTopic.objects.filter(id=obj.faq_topic.id).first()
            return FaqTopicListingSerializer(category).data
        return {}
    
    class Meta:
        model = FAQs
        fields = ["id","faq_topic","title","description","status","created_at"]



class CreateFaqSerializer(serializers.ModelSerializer) :
    title = serializers.CharField(max_length = 255, required=True)
    faq_topic_id = serializers.IntegerField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = FAQs
        fields = ['title',"description","faq_topic_id"]
        
    def validate(self, data):
        name_count = FAQTopic.objects.filter(id = data.get('faq_topic_id')).count()
        if name_count == 0:
            raise serializers.ValidationError("Invalid FAQ Topic ID!")

        return data

    def create(self , validate_data):
        topic = FAQs(
            title = validate_data.get('title'),
            description = validate_data.get('description'),
            faq_topic = FAQTopic.objects.filter(id = validate_data.get('faq_topic_id')).first(),
            status = True
        )
        topic.save()

        return topic
    

class EditFAQSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length = 255, required=True)
    faq_topic_id = serializers.IntegerField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = FAQTopic
        fields = ['title',"description","faq_topic_id"]
        
    def validate(self, data):
        name_count = FAQTopic.objects.filter(id = data.get('faq_topic_id')).count()
        if name_count == 0:
            raise serializers.ValidationError("Invalid FAQ Topic ID!")
        
        return data


    def update(self , category, validate_data):
        category.title = validate_data.get('title', category.title)
        category.description = validate_data.get('description', category.description)
        category.faq_topic = FAQTopic.objects.filter(id = validate_data.get('faq_topic_id')).first()
        category.save()

        return category
    


class ChangeFAQStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = FAQs
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralSettings
        fields = "__all__"



class UpdateSettingSerializer(serializers.ModelSerializer):
    payment_type = serializers.IntegerField(required=True)
    test_public_key = serializers.CharField(max_length = 255, required=False)
    test_secret_key = serializers.CharField(max_length = 255, required=False)
    live_public_key = serializers.CharField(max_length = 255, required=False)
    live_secret_key = serializers.CharField(max_length = 255, required=False)
    no_days_trail = serializers.IntegerField(required=False, allow_null=True)
    try_for_free = serializers.IntegerField(required=False, allow_null=True)
    allow_device_restriction = serializers.BooleanField(required=False, allow_null=True)
    allowed_desktop = serializers.IntegerField(required=False, allow_null=True)
    allowed_tablet = serializers.IntegerField(required=False, allow_null=True)
    allowed_phone = serializers.IntegerField(required=False, allow_null=True)
    
    
    class Meta:
        model = GeneralSettings
        fields =  ["payment_type","test_public_key","test_secret_key","live_public_key","live_secret_key","no_days_trail","try_for_free","allow_device_restriction","allowed_desktop","allowed_tablet","allowed_phone"]
        
    def validate(self, data):
        return data


    def create(self , validate_data):
        setting = GeneralSettings.objects.all().first()
        if setting is None:
            setting = GeneralSettings()
        setting.payment_type = validate_data.get('payment_type', setting.payment_type)
        setting.test_public_key = validate_data.get('test_public_key', setting.test_public_key)
        setting.test_secret_key = validate_data.get('test_secret_key', setting.test_secret_key)
        setting.live_public_key = validate_data.get('live_public_key', setting.live_public_key)
        setting.live_secret_key = validate_data.get('live_secret_key', setting.live_secret_key)
        setting.no_days_trail = validate_data.get('no_days_trail', setting.no_days_trail)
        setting.try_for_free = validate_data.get('try_for_free', setting.try_for_free)
        setting.allow_device_restriction = validate_data.get('allow_device_restriction', setting.allow_device_restriction)
        setting.allowed_tablet = validate_data.get('allowed_tablet', setting.allowed_tablet)
        setting.allowed_phone = validate_data.get('allowed_phone', setting.try_for_free)
        setting.allowed_desktop = validate_data.get('allowed_desktop', setting.allowed_desktop)
        setting.save()

        return setting
    


class TestimonialsListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonials
        fields = "__all__"


class CreateTestimonialsSerializer(serializers.ModelSerializer) :
    name = serializers.CharField(max_length = 255, required=True)
    testimonials_type = serializers.IntegerField(required=True)
    qualification = serializers.CharField(max_length = 255, required=True)
    college = serializers.CharField(max_length = 255, required=True)
    content = serializers.CharField(required=True)
    image = serializers.FileField(required=False,allow_null=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp","svg"])])
    
    class Meta:
        model = Testimonials
        fields = ['name',"testimonials_type","image","qualification","college","content"]
        
    def validate(self, data):
        return data

    def create(self , validate_data):
        category = Testimonials(
            name = validate_data.get('name'),
            testimonials_type = validate_data.get('testimonials_type'),
            qualification = validate_data.get('qualification'),
            college = validate_data.get('college'),
            content = validate_data.get('content'),
            image = validate_data.get('image'),
            status = True
        )
        category.save()

        return category
    

class EditTestimonialsSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length = 255, required=True)
    testimonials_type = serializers.IntegerField(required=True)
    qualification = serializers.CharField(max_length = 255, required=True)
    college = serializers.CharField(max_length = 255, required=True)
    content = serializers.CharField(required=True)
    image = serializers.FileField(required=False,allow_null=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp","svg"])])
    
    class Meta:
        model = Testimonials
        fields = ['name',"testimonials_type","image","qualification","college","content"]
        
    def validate(self, data):
        return data


    def update(self , category, validate_data):
        category.name = validate_data.get('name', category.name)
        category.qualification = validate_data.get('qualification', category.qualification)
        category.college = validate_data.get('college', category.college)
        category.content = validate_data.get('content', category.content)
        category.testimonials_type = validate_data.get('testimonials_type', category.testimonials_type)
        category.image = validate_data.get('image', category.image)
        category.save()

        return category
    

class ChangeTestimonialsStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = Testimonials
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    

class HelpSupportTopicListSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpSupportTopics
        fields = ['id',"title"]


class HelpSupportTopicListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpSupportTopics
        fields = "__all__"


class CreateHelpSupportTopicSerializer(serializers.ModelSerializer) :
    title = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(required=True)
    image = serializers.FileField(required=True,validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp","svg"])])
    
    class Meta:
        model = HelpSupportTopics
        fields = ['title',"description","image"]
        
    def validate(self, data):
        name_count = HelpSupportTopics.objects.filter(title = data.get('title')).count()
        if name_count > 0:
            raise serializers.ValidationError("Title Already Exists!")

        return data

    def create(self , validate_data):
        topic = HelpSupportTopics(
            title = validate_data.get('title'),
            description = validate_data.get('description'),
            image = validate_data.get('image'),
            status = True
        )
        topic.save()

        return topic
    


class EditHelpSupportTopicSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    image = serializers.FileField(required=False,allow_null=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp","svg"])])

    class Meta:
        model = HelpSupportTopics
        fields = ['title',"description","image"]
        
    def validate(self, data):
        return data


    def update(self , category, validate_data):
        category.title = validate_data.get('title', category.title)
        category.description = validate_data.get('description', category.description)
        category.image = validate_data.get('image', category.image)
        category.save()

        return category
    

class ChangeHelpSupportTopicStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = HelpSupportTopics
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    

class HelpSupportSubTopicListSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpSupportSubTopics
        fields = ['id',"title"]

class HelpSupportSubTopicListingSerializer(serializers.ModelSerializer):
    main_topic = serializers.SerializerMethodField()
    
    def get_main_topic(self, parent):
        info = HelpSupportTopics.objects.get(id = parent.main_topic.id)
        return HelpSupportTopicListSerializer(info).data
    
    class Meta:
        model = HelpSupportSubTopics
        fields = "__all__"


class CreateHelpSupportSubTopicSerializer(serializers.ModelSerializer) :
    title = serializers.CharField(max_length = 255, required=True)
    main_topic = serializers.IntegerField(required=True)
    
    class Meta:
        model = HelpSupportSubTopics
        fields = ['title',"main_topic"]
        
    def validate(self, data):
        name_count = HelpSupportSubTopics.objects.filter(title = data.get('title')).count()
        if name_count > 0:
            raise serializers.ValidationError("Title Already Exists!")

        return data

    def create(self , validate_data):
        topic = HelpSupportSubTopics(
            title = validate_data.get('title'),
            main_topic = HelpSupportTopics.objects.filter(id = validate_data.get('main_topic')).first(),
            status = True
        )
        topic.save()

        return topic
    


class EditHelpSupportSubTopicserializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length = 255, required=True)
    main_topic = serializers.IntegerField(required=True)

    class Meta:
        model = HelpSupportSubTopics
        fields = ['title',"main_topic"]
        
    def validate(self, data):
        return data


    def update(self , category, validate_data):
        category.title = validate_data.get('title', category.title)
        category.main_topic = HelpSupportTopics.objects.filter(id = validate_data.get('main_topic')).first()
        category.save()

        return category
    

class ChangeHelpSupportSubTopicstatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = HelpSupportSubTopics
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    



class HelpSupportArticleListingSerializer(serializers.ModelSerializer):
    main_topic = serializers.SerializerMethodField()
    sub_topic = serializers.SerializerMethodField()
    
    def get_main_topic(self, parent):
        info = HelpSupportTopics.objects.get(id = parent.sub_topic.id)
        return HelpSupportTopicListSerializer(info).data
    
    def get_sub_topic(self, parent):
        info = HelpSupportSubTopics.objects.get(id = parent.sub_topic.id)
        return HelpSupportSubTopicListSerializer(info).data
    
    class Meta:
        model = HelpSupportArticle
        fields = ['id',"slug","title","description","status","main_topic","sub_topic","created_at"]


class CreateHelpSupportArticleSerializer(serializers.ModelSerializer) :
    title = serializers.CharField(max_length = 255, required=True)
    main_topic = serializers.IntegerField(required=True)
    sub_topic = serializers.IntegerField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = HelpSupportArticle
        fields = ['title',"main_topic","sub_topic","description"]
        
    def validate(self, data):
        name_count = HelpSupportArticle.objects.filter(title = data.get('title')).count()
        if name_count > 0:
            raise serializers.ValidationError("Title Already Exists!")

        return data

    def create(self , validate_data):
        topic = HelpSupportArticle(
            title = validate_data.get('title'),
            description = validate_data.get('description'),
            main_topic = HelpSupportTopics.objects.filter(id = validate_data.get('main_topic')).first(),
            sub_topic = HelpSupportSubTopics.objects.filter(id = validate_data.get('sub_topic')).first(),
            status = True
        )
        topic.save()

        return topic
    


class EditHelpSupportArticleserializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length = 255, required=True)
    main_topic = serializers.IntegerField(required=True)
    sub_topic = serializers.IntegerField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = HelpSupportArticle
        fields = ['title',"main_topic","sub_topic","description"]
        
    def validate(self, data):
        return data


    def update(self , category, validate_data):
        category.title = validate_data.get('title', category.title)
        category.description = validate_data.get('description', category.description)
        category.main_topic = HelpSupportTopics.objects.filter(id = validate_data.get('main_topic')).first()
        category.sub_topic = HelpSupportSubTopics.objects.filter(id = validate_data.get('sub_topic')).first()
        category.save()

        return category
    

class ChangeHelpSupportArticlestatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = HelpSupportArticle
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()

        return category
    

class CouponListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id',"code"]


class PromotionalBannerListingSerializer(serializers.ModelSerializer):
    coupon_info = CouponListSerializer(source='coupons', read_only=True)

    class Meta:
        model = PromotionalBannerCampaign
        fields = ["id","title","display_text","start_time","end_time","status","created_at","coupon_info"]



class PromotionalBannerSerializer(serializers.ModelSerializer) :
    coupons_id = serializers.IntegerField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    display_text = serializers.CharField(max_length=255, required=True)
    start_time = serializers.DateTimeField(required=False, default=timezone.now)
    end_time = serializers.DateTimeField(required=True)

    class Meta:
        model = PromotionalBannerCampaign
        fields = ['title','display_text','coupons_id','start_time','end_time']
        
    def validate(self, data):
        coupon_id = data.get('coupons_id')
        if coupon_id:
            if not Coupon.objects.filter(id=coupon_id).exists():
                raise serializers.ValidationError({"coupons_id": "The requested Coupon does not exist."})

        start_time = data.get('start_time', timezone.now())
        end_time = data.get('end_time')
        if end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "The end time must be later than the start time."})
        
        return data

    def create(self , validate_data):

        coupon_id = validate_data.pop('coupons_id', None)
        coupon_instance = Coupon.objects.get(id=coupon_id) if coupon_id else None

        banner_campaign = PromotionalBannerCampaign(
            title=validate_data.get('title'),
            display_text=validate_data.get('display_text'),
            coupons=coupon_instance,
            start_time=validate_data.get('start_time', timezone.now()),
            end_time=validate_data.get('end_time'),
            status=False
        )
        banner_campaign.save()

        return banner_campaign
    

class PromotionalBannerSerializer(serializers.ModelSerializer) :
    coupons_id = serializers.IntegerField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    display_text = serializers.CharField(max_length=255, required=True)
    start_time = serializers.DateTimeField(required=False, default=timezone.now)
    end_time = serializers.DateTimeField(required=True)

    class Meta:
        model = PromotionalBannerCampaign
        fields = ['title','display_text','coupons_id','start_time','end_time']
        
    def validate(self, data):
        coupon_id = data.get('coupons_id')
        if coupon_id:
            if not Coupon.objects.filter(id=coupon_id).exists():
                raise serializers.ValidationError({"coupons_id": "The requested Coupon does not exist."})

        start_time = data.get('start_time', timezone.now())
        end_time = data.get('end_time')
        if end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "The end time must be later than the start time."})
        
        return data


    def update(self , category, validate_data):

        coupon_id = validate_data.pop('coupons_id', None)
        coupon_instance = Coupon.objects.get(id=coupon_id) if coupon_id else None

        category.title = validate_data.get('title', category.title)
        category.display_text = validate_data.get('display_text', category.display_text)
        category.coupons = coupon_instance
        category.start_time = validate_data.get('start_time', category.start_time)
        category.end_time = validate_data.get('end_time', category.end_time)
        category.save()

        return category
    

class ChangePromotionalBannerStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = PromotionalBannerCampaign
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        if validate_data.get('status'):
            PromotionalBannerCampaign.objects.filter(status=True).update(status=False)

        category.status = validate_data.get('status', category.status)
        category.save()

        return category