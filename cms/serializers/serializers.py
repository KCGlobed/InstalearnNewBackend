from rest_framework import serializers
from cms.models import *
from courses.models import *
from django.db import transaction
from django.core.validators import FileExtensionValidator
from mini_lms.utils import *
from django.template import loader
from django.db.models import Q
from django.core.mail import EmailMessage
from django.contrib.humanize.templatetags.humanize import naturaltime


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


class SubmitApplicationFormSerializer(serializers.ModelSerializer) :
    full_name = serializers.CharField(max_length = 255, required=True)
    mobile = serializers.CharField(max_length = 255, required=True)
    email = serializers.CharField(max_length = 255, required=True)
    state = serializers.CharField(max_length = 255, required=True)
    city = serializers.CharField(max_length = 255, required=True)
    highest_qualification = serializers.CharField(max_length = 255, required=True)
    current_employment_status = serializers.CharField(max_length = 255, required=True)
    total_years_of_experience = serializers.CharField(max_length = 255, required=True)
    role_applying_for = serializers.CharField(max_length = 255, required=True)
    other_role_specification = serializers.CharField(required=False, allow_blank=True)
    linkedin_portfolio = serializers.CharField(max_length = 255, required=True)
    notice_period = serializers.CharField(max_length = 255, required=True)
    summary = serializers.CharField(required=False, allow_blank=True)
    resume = serializers.FileField(required=False,allow_null=True, validators=[FileExtensionValidator( ['pdf','doc','docx'])])
    
    class Meta:
        model = JobApplications
        fields = ['full_name','mobile','email','state','city',"highest_qualification","current_employment_status","total_years_of_experience","role_applying_for","other_role_specification","linkedin_portfolio","notice_period","summary","resume"]
        
    def validate(self, data):

        return data


    def create(self , validate_data):
        
        course_category = JobApplications(
            full_name = validate_data.get('full_name'),
            mobile = validate_data.get('mobile'),
            email = validate_data.get('email'),
            state = validate_data.get('state'),
            city = validate_data.get('city'),
            highest_qualification = validate_data.get('highest_qualification'),
            current_employment_status = validate_data.get('current_employment_status'),
            total_years_of_experience = validate_data.get('total_years_of_experience'),
            role_applying_for = validate_data.get('role_applying_for'),
            other_role_specification = validate_data.get('other_role_specification'),
            linkedin_portfolio = validate_data.get('linkedin_portfolio'),
            notice_period = validate_data.get('notice_period'),
            summary = validate_data.get('summary'),
            resume = validate_data.get('resume'),
        )
        course_category.save()

        return course_category




class CommunityCategoriesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityCategories
        fields = ['id',"title","slug","description","image"]


class CommunityPostsListSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    
    def get_category(self, parent):
        info = CommunityCategories.objects.get(id = parent.category.id)
        return CommunityCategoriesListSerializer(info).data
    
    class Meta:
        model = CommunityPosts
        fields = ['id',"slug","title","status","total_comments","total_likes","total_views","category","created_at"]


class ViewCommunityPostsDetailSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    
    def get_category(self, parent):
        info = CommunityCategories.objects.get(id = parent.category.id)
        return CommunityCategoriesListSerializer(info).data
    
    class Meta:
        model = CommunityPosts
        fields = ['id',"slug","title","description","total_comments","total_likes","total_views","status","category","created_at"]



class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id',"first_name","last_name","email","image"]


class CommunityPostCommentsSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    def get_time_ago(self, obj):
        if obj.created_at:
            return naturaltime(obj.created_at)
        return None
        
    def get_user_info(self, parent):
        info = User.objects.get(id = parent.user.id)
        return UserInfoSerializer(info).data
    
    class Meta:
        model = CommunityPostComments
        fields = ["id","comment","total_likes","user_info","created_at","time_ago"]


class AddCommunityPostCommentSerializer(serializers.ModelSerializer) :
    post_id = serializers.IntegerField(required=True)
    comment = serializers.CharField(required=True)
    class Meta:
        model = CommunityPostComments
        fields = ['post_id','comment']
        
    def validate(self, data):

        post_id = data.get('post_id')
        course_count = CommunityPostComments.objects.filter(post_id=post_id, user = self.context.get('user')).count()
        if course_count > 0:
            raise serializers.ValidationError("You have already given comment to this post")
        
        return data


    def create(self , validate_data):
        post = CommunityPosts.objects.filter(id = validate_data.get('post_id')).first()
        course_category = CommunityPostComments(
            post = post,
            user = self.context.get('user'),
            comment = validate_data.get('comment'),

        )
        course_category.save()
    
        return course_category