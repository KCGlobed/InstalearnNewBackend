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