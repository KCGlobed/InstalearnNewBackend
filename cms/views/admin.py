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
from datetime import datetime,timezone
from rest_framework import serializers
from django.conf import settings
import os
from google.cloud import storage


class BlogsListingView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "blogs_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title',"category__title"]
    ordering_fields = ['title', 'created_at', 'id', 'status', 'feature_status',"category__title"] 
    def get(self, request, format=None):
        blog_list = Blog.objects.select_related("category").all()
        
        title = request.query_params.get('title')
        if title:
            blog_list = blog_list.filter(title__icontains=title)

        category = request.query_params.get('category')
        if category:
            blog_list = blog_list.filter(category__title__icontains=category)
        
        active = request.query_params.get('status')
        if active:
            blog_list = blog_list.filter(status=active)


        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                blog_list = blog_list.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                blog_list = blog_list.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        blog_list = search_filter.filter_queryset(request, blog_list, self)

        ordering_filter = filters.OrderingFilter()
        blog_list = ordering_filter.filter_queryset(request, blog_list, self)

        if not blog_list.ordered:
            blog_list = blog_list.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(blog_list, request, view=self)
        serializer = BlogsListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class ViewBlogInfoView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "view_blog",
                            [SuperAdmin]
                        )]
    def get(self, request,  cid , format=None):
        category = Blog.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Category ID!")
        serializer = BlogInfoSerializer(category)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class CreateBlogView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_blog",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateBlogSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Blog Created Successfully", data=BlogInfoSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class EditBlogView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_blog",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = Blog.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Blog ID!")
        
        serializer = EditBlogSerializer(category, data = request.data, partial=True, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Blog Category Updated Successfully", data=BlogInfoSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class UpdateBlogStatusView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_blog_status",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = Blog.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Blog ID!")
        
        serializer = ChangeBlogStatusSerializer(category, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Blog Status Updated Successfully", data=BlogInfoSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateBlogFeatureStatusView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_blog_status",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = Blog.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Blog ID!")
        
        serializer = ChangeBlogFeatureStatusSerializer(category, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Blog Status Updated Successfully", data=BlogInfoSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteBlogView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_blog",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = Blog.objects.get(id = cid)
            course.delete()
            return success_response(message="Blog Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except Blog.DoesNotExist:
            return error_response(message="Blog not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
       


class BlogCategoryListingView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "blog_category_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['title', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        category = BlogCategories.objects.all()
        
        title = request.query_params.get('title')
        if title:
            category = category.filter(title__icontains=title)

        description = request.query_params.get('description')
        if description:
            category = category.filter(description__icontains=description)
        
        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)


        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(category, request, view=self)
        serializer = BlogCategoriesListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class CreateBlogCategoryView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_blog_category",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateBlogCategorySerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Blog Category Created Successfully", data=BlogCategoriesListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class EditBlogCategoryView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_blog_category",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = BlogCategories.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Category ID!")
        
        serializer = EditBlogCategorySerializer(category, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Blog Category Updated Successfully", data=BlogCategoriesListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateBlogCategoryStatusView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_blog_category_status",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = BlogCategories.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Category ID!")
        
        serializer = ChangeBlogCategoryStatusSerializer(category, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Blog Category Status Updated Successfully", data=BlogCategoriesListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteBlogCategoryView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_blog_category",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = BlogCategories.objects.get(id = cid)
            course.delete()
            return success_response(message="Blog Category Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except BlogCategories.DoesNotExist:
            return error_response(message="Blog Category not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        


class BlogsCommentListingView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "blogs_comment_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name','last_name',"email","blog__title"]
    ordering_fields = ['first_name','last_name',"email","blog__title",'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        category = BlogComment.objects.select_related("blog").all()
        
        first_name = request.query_params.get('first_name')
        if first_name:
            category = category.filter(first_name__icontains=first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            category = category.filter(last_name__icontains=last_name)

        email = request.query_params.get('email')
        if email:
            category = category.filter(email__icontains=email)

        blog_title = request.query_params.get('blog_title')
        if blog_title:
            category = category.filter(blog__title__icontains=blog_title)
        
        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(category, request, view=self)
        serializer = BlogsCommentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class UpdateBlogCommentStatusView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_blog_comment_status",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = BlogComment.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Blog Comment ID!")
        
        serializer = ChangeBlogFeatureStatusSerializer(category, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Blog Comment Status Updated Successfully", data=BlogsCommentSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class CMSPagesListingView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "blogs_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title',"page_type"]
    ordering_fields = ['title', 'created_at', 'id', 'status',"page_type"] 
    def get(self, request, format=None):
        blog_list = CMSPages.objects.all()
        
        title = request.query_params.get('title')
        if title:
            blog_list = blog_list.filter(title__icontains=title)

        page_type = request.query_params.get('page_type')
        if page_type:
            blog_list = blog_list.filter(page_type__icontains=page_type)
        
        active = request.query_params.get('status')
        if active:
            blog_list = blog_list.filter(status=active)


        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                blog_list = blog_list.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                blog_list = blog_list.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        blog_list = search_filter.filter_queryset(request, blog_list, self)

        ordering_filter = filters.OrderingFilter()
        blog_list = ordering_filter.filter_queryset(request, blog_list, self)

        if not blog_list.ordered:
            blog_list = blog_list.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(blog_list, request, view=self)
        serializer = CMSPagesListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class CreateUpdateCMSPageView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_blog_category",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateUpdateCMSPageSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="CMS Pages Updated Successfully", data=CMSPagesListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateCMSPageStatusView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_blog_category_status",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = CMSPages.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Page ID!")
        
        serializer = ChangeCMSPageStatusSerializer(category, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Page Status Updated Successfully", data=CMSPagesListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class FaqTopicListingView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "faq_topic_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['title', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        category = FAQTopic.objects.all()
        
        title = request.query_params.get('title')
        if title:
            category = category.filter(title__icontains=title)

        description = request.query_params.get('description')
        if description:
            category = category.filter(description__icontains=description)
        
        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)


        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(category, request, view=self)
        serializer = FaqTopicListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class FaqTopicListView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request, format=None):
        category = FAQTopic.objects.filter(status = True)
        serializer = FaqTopicListingSerializer(category, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class CreateFaqTopicView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_faq_topic",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateFaqTopicSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="FAQ Topic Created Successfully", data=FaqTopicListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class EditFaqTopicView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_faq_topic",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = FAQTopic.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid FAQ Topic ID!")
        
        serializer = EditFAQTopicSerializer(category, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="FAQ Topic Updated Successfully", data=FaqTopicListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateFaqTopicStatusView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_faq_topic_status",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = FAQTopic.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid FAQ Topic ID!")
        
        serializer = ChangeFAQTopicStatusSerializer(category, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="FAQ Topic Status Updated Successfully", data=FaqTopicListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteFaqTopicView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_faq_topic",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = FAQTopic.objects.get(id = cid)
            course.delete()
            return success_response(message="FAQ Topic Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except FAQTopic.DoesNotExist:
            return error_response(message="FAQ Topic not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        


class FaqListingView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "faq_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['title', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        category = FAQs.objects.all()
        
        faq_topic = request.query_params.get('topic_id')
        if faq_topic:
            category = category.filter(faq_topic_id = faq_topic)

        
        title = request.query_params.get('title')
        if title:
            category = category.filter(title__icontains=title)

        description = request.query_params.get('description')
        if description:
            category = category.filter(description__icontains=description)
        
        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)


        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            

        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(category, request, view=self)
        serializer = FaqListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class CreateFaqView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_faq",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateFaqSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="FAQ Created Successfully", data=FaqListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class EditFaqView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_faq",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = FAQs.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid FAQ ID!")
        
        serializer = EditFAQSerializer(category, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="FAQ Updated Successfully", data=FaqListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UpdateFaqStatusView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_faq_status",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = FAQs.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid FAQ ID!")
        
        serializer = ChangeFAQStatusSerializer(category, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="FAQ Status Updated Successfully", data=FaqListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteFaqView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_faq",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = FAQs.objects.get(id = cid)
            course.delete()
            return success_response(message="FAQ Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except FAQs.DoesNotExist:
            return error_response(message="FAQ not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        


class GetSettingView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "manage_setting",
                            [SuperAdmin]
                        )]
    def get(self, request, cid=None):
        setting = GeneralSettings.objects.all().first()
        if setting is None:
            return success_response(message="Success", data={}, status_code=status.HTTP_200_OK)
        serializer = SettingSerializer(setting)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class UpdateSettingView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_setting",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = UpdateSettingSerializer(data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Setting Updated Successfully", data=SettingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class TestimonialsListingView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "testimonials_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'id', 'status',"qualification","testimonials_type"] 
    def get(self, request, format=None):
        category = Testimonials.objects.all()
        
        name = request.query_params.get('name')
        if name:
            category = category.filter(name__icontains=name)

        testimonials_type = request.query_params.get('testimonials_type')
        if testimonials_type:
            category = category.filter(testimonials_type=testimonials_type)
        
        active = request.query_params.get('status')
        if active:
            category = category.filter(status=active)


        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                category = category.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                category = category.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(category, request, view=self)
        serializer = TestimonialsListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class CreateTestimonialsView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_testimonials",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateTestimonialsSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Testimonials Created Successfully", data=TestimonialsListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class EditTestimonialsView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_testimonials",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = Testimonials.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Testimonials ID!")
        
        serializer = EditTestimonialsSerializer(category, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Testimonials Updated Successfully", data=TestimonialsListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateTestimonialsStatusView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_testimonials_status",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = Testimonials.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Testimonials ID!")
        
        serializer = ChangeTestimonialsStatusSerializer(category, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Testimonials Status Updated Successfully", data=BlogCategoriesListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteTestimonialsView(APIView):
    renderer_classes = [CMSRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_testimonials",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = Testimonials.objects.get(id = cid)
            course.delete()
            return success_response(message="Testimonials Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except Testimonials.DoesNotExist:
            return error_response(message="Testimonials not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)