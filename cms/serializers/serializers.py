from rest_framework import serializers
from cms.models import *
from courses.models import *
from django.db import transaction
from django.core.validators import FileExtensionValidator
from mini_lms.utils import *
from django.template import loader
from django.db.models import Q
from django.core.mail import EmailMessage


class ContactUsSerializer(serializers.ModelSerializer) :
    first_name = serializers.CharField(max_length = 255, required=True)
    last_name = serializers.CharField(max_length = 255, required=True)
    email = serializers.CharField(max_length = 255, required=True)
    phone = serializers.CharField(max_length = 255, required=True)
    message = serializers.CharField(required=True)
    class Meta:
        model = ContactUs
        fields = ['first_name','last_name','message','email','phone']
        
    def validate(self, data):

        return data


    def create(self , validate_data):
        
        course_category = ContactUs(
            first_name = validate_data.get('first_name'),
            last_name = validate_data.get('last_name'),
            email = validate_data.get('email'),
            phone = validate_data.get('phone'),
            message = validate_data.get('message'),

        )
        course_category.save()
        
        subject = 'Contact Us'
        message = f'Hi you have got a contact us'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [settings.ADMIN_EMAIL,]

        html_message = loader.render_to_string(
            'contactEmail.html',
            {
                'first_name': validate_data.get('first_name'),
                'last_name':validate_data.get('last_name'),
                'email': validate_data.get('email'),
                'phone': validate_data.get('phone'),
                'message': validate_data.get('message')
            }
        )
        email = EmailMessage(
            subject, html_message, email_from, recipient_list)
        
        email.content_subtype = "html"
        email.send()

        return course_category
    

class BlogCategoriesListSerializer(serializers.ModelSerializer):
    blog_count = serializers.SerializerMethodField()
    
    def get_blog_count(self, parent):
        now = timezone.now()
        count = Blog.objects.filter(category_id = parent.id, status =True).filter(Q(live_date__isnull=True) | Q(live_date__lt=now)).count()
        return count
    
    class Meta:
        model = BlogCategories
        fields = ["id","title","blog_count"]



class BlogListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = ["id","title","slug","img_alt_tag","image","tags","reading_time"]


class BlogCommentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogComment
        fields = ["id","first_name","last_name","email","comment","created_at"]



class AddBlogCommentSerializer(serializers.ModelSerializer) :
    blog_id = serializers.IntegerField(required=True)
    first_name = serializers.CharField(max_length = 255, required=True)
    last_name = serializers.CharField(max_length = 255, required=True)
    email = serializers.CharField(max_length = 255, required=True)
    comment = serializers.CharField(required=True)
    class Meta:
        model = BlogComment
        fields = ['first_name','last_name','comment','email',"blog_id"]
        
    def validate(self, data):

        blog_id = data.get('blog_id')
        course_count = BlogComment.objects.filter(blog_id=blog_id, email = data.get('email')).count()
        if course_count > 0:
            raise serializers.ValidationError("You have already given comment to this blog")
        
        return data


    def create(self , validate_data):
        blog = Blog.objects.filter(id = validate_data.get('blog_id')).first()
        course_category = BlogComment(
            blog = blog,
            first_name = validate_data.get('first_name'),
            last_name = validate_data.get('last_name'),
            email = validate_data.get('email'),
            comment = validate_data.get('comment'),

        )
        course_category.save()
        
        subject = 'New Blog Comment'
        message = f'Hi you have got a new blog comment'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [settings.ADMIN_EMAIL,]

        html_message = loader.render_to_string(
            'blog_comment_email.html',
            {
                'blog_name': blog.title,
                'first_name': validate_data.get('first_name'),
                'last_name':validate_data.get('last_name'),
                'email': validate_data.get('email'),
                'comment': validate_data.get('comment')
            }
        )
        email = EmailMessage(
            subject, html_message, email_from, recipient_list)
        
        email.content_subtype = "html"
        email.send()

        return course_category
    

class HelpSupportTopicsSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    class Meta:
        model = HelpSupportTopics
        fields = ['id',"title","slug","description","image","created_at"]


class HelpSupportArticleDetailSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    class Meta:
        model = HelpSupportArticle
        fields = ['id',"title","slug","description","created_at"]


class HelpSupportArticleInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpSupportArticle
        fields = ['id',"title","slug"]

class HelpSupportSubTopicsSerializer(serializers.ModelSerializer):
    articles = serializers.SerializerMethodField()
    
    def get_articles(self, parent):
        info = HelpSupportArticle.objects.filter(sub_topic_id = parent.id)
        return HelpSupportArticleInfoSerializer(info, many=True).data
    
    class Meta:
        model = HelpSupportSubTopics
        fields = ['id',"title","slug","articles"]