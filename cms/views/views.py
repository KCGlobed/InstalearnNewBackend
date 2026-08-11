from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from cms.serializers import *
from cms.renderers import CMSRenderer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from mini_lms.utils import *
from mini_lms.roles import *
from mini_lms.permissions import RoleOrPermissionCheck
from mini_lms.pagination import CustomPageNumberPagination
from rest_framework import filters
import pandas as pd
from django.utils import timezone
from rest_framework import serializers
from django.conf import settings
import os
from google.cloud import storage
from django.db.models import F
from django.shortcuts import get_object_or_404


class FaqTopicListView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request, format=None):
        category = FAQTopic.objects.filter(status = True)
        serializer = FaqTopicListingSerializer(category, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class FaqsListView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request, cid=None):
        topic = FAQTopic.objects.filter(id=cid).first()
        if topic is None:
            raise ValidationError("Invalid FAQ Topic ID!")
        
        category = FAQs.objects.filter(status = True, faq_topic_id = cid)
        serializer = FaqListingSerializer(category, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class ContactUsView(APIView):
    renderer_classes = [CMSRenderer]
    def post(self, request, format=None):

        serializer = ContactUsSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Message sent Successfully", data=serializer.data, status_code=status.HTTP_200_OK)

        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class BlogCategoriesView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request, format=None):
        category = BlogCategories.objects.filter(status = True).order_by("-id")
        serializer = BlogCategoriesListSerializer(category, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class BlogCategoryWiseView(APIView):
    renderer_classes = [CMSRenderer]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['title', 'created_at', 'id'] 
    def get(self, request, cid=None):
        now = timezone.now()
        category = Blog.objects.filter(category_id = cid, status =True).filter(Q(live_date__isnull=True) | Q(live_date__lt=now)).order_by("-id")

        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(category, request, view=self)
        serializer = BlogListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class GetFeaturedBlogListingView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request):
        now = timezone.now()
        category = Blog.objects.filter(status =True, feature_status=True).filter(Q(live_date__isnull=True) | Q(live_date__lt=now))
        serializer = BlogListingSerializer(category, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    


class BlogListingView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request):
        now = timezone.now()
        category = Blog.objects.filter(status =True).filter(Q(live_date__isnull=True) | Q(live_date__lt=now))
        serializer = BlogListingSerializer(category, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class ViewBlogDetailView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request, slug=None):
        now = timezone.now()
        category = Blog.objects.filter(slug = slug, status =True).filter(Q(live_date__isnull=True) | Q(live_date__lt=now)).first()
        serializer = BlogInfoSerializer(category)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class ViewBlogCommentsView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request, id=None):
        category = BlogComment.objects.filter(blog_id = id, status =1)
        serializer = BlogCommentsSerializer(category, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    


class AddBlogCommentView(APIView):
    renderer_classes = [CMSRenderer]
    def post(self, request, format=None):
        serializer = AddBlogCommentSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Comment Added Successfully", data=serializer.data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class ViewCMSPageView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request, page_type=None):
        category = CMSPages.objects.filter(page_type = page_type, status =True).first()
        serializer = CMSPagesListingSerializer(category)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class ViewTestimonialsListView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request, testimonials_type=None):
        category = Testimonials.objects.filter(testimonials_type = testimonials_type, status =True)
        serializer = TestimonialsListSerializer(category, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class HelpSupportTopicView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request):
        category = HelpSupportTopics.objects.filter(status =True)
        serializer = HelpSupportTopicsSerializer(category, many =True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class HelpSupportSubTopicView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request, slug=None):
        category = HelpSupportSubTopics.objects.filter(status =True, main_topic__slug = slug)
        serializer = HelpSupportSubTopicsSerializer(category, many =True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class HelpSupportArticlesView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request, slug=None):
        category = HelpSupportArticle.objects.filter(status =True, sub_topic__slug = slug)
        serializer = HelpSupportArticleInfoSerializer(category, many =True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    
class HelpSupportArticleDetailView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request, slug=None):
        category = HelpSupportArticle.objects.filter(status =True, slug = slug).first()
        serializer = HelpSupportArticleDetailSerializer(category)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class SubmitApplicationFormView(APIView):
    renderer_classes = [CMSRenderer]
    def post(self, request, format=None):
        serializer = SubmitApplicationFormSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Application Submitted Successfully", data=serializer.data, status_code=status.HTTP_200_OK)

        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class PromotionalBannerListView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request):
        now = timezone.now()
        category = PromotionalBannerCampaign.objects.filter(
                            status=True,
                            start_time__lte=now,
                            end_time__gte=now
                        ).first()
        serializer = PromotionalBannerListingSerializer(category)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)



class CommunityCategoryListView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request):
        category = CommunityCategories.objects.filter(status =True)
        serializer = CommunityCategoriesListSerializer(category, many =True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)



class CommunityPostListView(APIView):
    renderer_classes = [CMSRenderer]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['title', 'created_at', 'id', 'status'] 

    def get(self, request, slug=None):
        queryset = CommunityPosts.objects.filter(status=True)

        if slug:
            queryset = queryset.filter(category__slug=slug)

        title_param = request.query_params.get('title')
        if title_param:
            queryset = queryset.filter(title__icontains=title_param)

        category_param = request.query_params.get('category')
        if category_param:
            queryset = queryset.filter(category__title__icontains=category_param)

        search_filter = filters.SearchFilter()
        queryset = search_filter.filter_queryset(request, queryset, self)

        ordering_filter = filters.OrderingFilter()
        queryset = ordering_filter.filter_queryset(request, queryset, self)

        if queryset is not None and hasattr(queryset, 'ordered') and not queryset.ordered:
            queryset = queryset.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset or [], request, view=self)
        serializer = CommunityPostsListSerializer(page, many=True)
        
        return paginator.get_paginated_response(serializer.data)


class ViewCommunityPostDetailView(APIView):
    renderer_classes = [CMSRenderer]

    def get(self, request, slug=None):
        post = CommunityPosts.objects.filter(status=True, slug=slug).first()
        if not post:
            return error_response(message="Post not found", status_code=status.HTTP_404_NOT_FOUND)

        CommunityPosts.objects.filter(pk=post.pk).update(total_views=F('total_views') + 1)
        post.refresh_from_db()

        serializer = ViewCommunityPostsDetailSerializer(post)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)


class ViewCommunityPostCommentsView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request, slug=None):
        category = CommunityPostComments.objects.filter(post__slug = slug)
        serializer = CommunityPostCommentsSerializer(category, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    


class AddCommunityPostCommentView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        serializer = AddCommunityPostCommentSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Comment Added Successfully", data=serializer.data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class ToggleLikeView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        post_id = request.data.get('post_id')
        comment_id = request.data.get('comment_id')

        if not post_id and not comment_id:
            return Response({"error": "Either 'post_id' or 'comment_id' is required."}, status=status.HTTP_400_BAD_REQUEST)

        if post_id:
            post_obj = get_object_or_404(CommunityPosts, pk=post_id)
            like, created = CommunityPostLikes.objects.get_or_create(user=user, post=post_obj)

            if not created:
                like.delete()
                liked = False
                message = "Post unliked successfully."
            else:
                liked = True
                message = "Post liked successfully."

            total_likes = CommunityPostLikes.objects.filter(post=post_obj).count()
            CommunityPosts.objects.filter(pk=post_obj.pk).update(total_likes=total_likes)

            return Response({
                "message": message,
                "liked": liked,
                "total_likes": total_likes
            }, status=status.HTTP_200_OK)

        else:
            comment_obj = get_object_or_404(CommunityPostComments, pk=comment_id)
            like, created = CommunityPostLikes.objects.get_or_create(user=user, comment=comment_obj)

            if not created:
                like.delete()
                liked = False
                message = "Comment unliked successfully."
            else:
                liked = True
                message = "Comment liked successfully."

            total_likes = CommunityPostLikes.objects.filter(comment=comment_obj).count()
            CommunityPostComments.objects.filter(pk=comment_obj.pk).update(total_likes=total_likes)

            return Response({
                "message": message,
                "liked": liked,
                "total_likes": total_likes
            }, status=status.HTTP_200_OK)