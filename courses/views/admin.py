from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from courses.serializers import *
from courses.renderers import CourseRenderer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import update_last_login
from rolepermissions.checkers import has_role
from django.db.models import Q
from mini_lms.utils import *
from rolepermissions import roles
from mini_lms.roles import *
from django.core.exceptions import ValidationError
from mini_lms.permissions import RoleOrPermissionCheck
from mini_lms.pagination import CustomPageNumberPagination
from rest_framework import filters


class ChapterListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        
        chapters = Chapters.objects.all()

        course_id = request.query_params.get('course_id')
        if course_id:
            chapter_list = CourseChapters.objects.filter(course_id = course_id).values_list("chapter",flat=True)
            chapters = chapters.filter(id__in=chapter_list)

        status = request.query_params.get('status')
        if status:
            videos = videos.filter(status=status)

        
        search_filter = filters.SearchFilter()
        chapters = search_filter.filter_queryset(request, chapters, self)

        ordering_filter = filters.OrderingFilter()
        chapters = ordering_filter.filter_queryset(request, chapters, self)

        if not chapters.ordered:
            chapters = chapters.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(chapters, request, view=self)
        serializer = ChaptersSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class ChapterListView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        chapter = Chapters.objects.filter(status=True).order_by("-id")
        chapter_type = request.query_params.get('chapter_type')
        if chapter_type:
            chapter = chapter.filter(chapter_type=chapter_type)

        serializer = ChapterListSerializer(chapter, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class ViewChapterView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_listing",
                            [SuperAdmin]
                        )]
    def get(self, request,  cid , format=None):
        chapter = Chapters.objects.filter(id=cid).first()
        if chapter is None:
            raise ValidationError("Invalid Chapter ID!")
        
        serializer = ViewChapterDetailSerializer(chapter)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class CreateChapterView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_chapter",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateChapterSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Chapter Created Successfully", data=ViewChapterDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class EditChapterView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        chapter = Chapters.objects.filter(id=cid).first()
        if chapter is None:
            raise ValidationError("Invalid Chapter ID!")
        
        serializer = EditChapterSerializer(chapter, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Chapter Updated Successfully", data=ViewChapterDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UpdateChapterStatusView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        chapter = Chapters.objects.filter(id=cid).first()
        if chapter is None:
            raise ValidationError("Invalid Chapter ID!")
        
        serializer = ChangeChapterstatusSerializer(chapter, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Chapter Status Updated Successfully", data=ViewChapterDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class DeleteChapterView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_chapter",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = Chapters.objects.get(id = cid)
            course.delete()
            return success_response(message="Chapter Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except Chapters.DoesNotExist:
            return error_response(message="Chapter not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        


class VideosListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_video_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        
        videos = Videos.objects.all()
        
        course_id = request.query_params.get('course_id')
        subject_id = request.query_params.get('subject_id')
        chapter_id = request.query_params.get('chapter_id')
        if course_id:
            if subject_id:
                if chapter_id:
                    topic_list = Chapters.objects.filter(chapter_id = chapter_id).values_list("topic",flat=True)
                    topic_condition = Q(topicvideos__topic_id__in=topic_list)
                    chapter_condition = Q(topicvideos__chapter_id=chapter_id)
                    videos = videos.filter(topic_condition | chapter_condition).distinct()
                else:
                    chapter_list = CourseChapters.objects.filter(course_id = course_id).values_list("chapter",flat=True)
                    topic_list = Chapters.objects.filter(chapter_id__in = chapter_list).values_list("topic",flat=True)
                    topic_condition = Q(topicvideos__topic_id__in=topic_list)
                    chapter_condition = Q(topicvideos__chapter_id__in=chapter_list)
                    videos = videos.filter(topic_condition | chapter_condition).distinct()
            else:
                chapter_list = CourseChapters.objects.filter(course_id__in = course_id).values_list("chapter",flat=True)
                topic_list = Chapters.objects.filter(chapter_id__in = chapter_list).values_list("topic",flat=True)
                topic_condition = Q(topicvideos__topic_id__in=topic_list)
                chapter_condition = Q(topicvideos__chapter_id__in=chapter_list)
                videos = videos.filter(topic_condition | chapter_condition).distinct()

        
        status = request.query_params.get('status')
        if status:
            videos = videos.filter(status=status)

        search_filter = filters.SearchFilter()
        videos = search_filter.filter_queryset(request, videos, self)

        ordering_filter = filters.OrderingFilter()
        videos = ordering_filter.filter_queryset(request, videos, self)

        if not videos.ordered:
            videos = videos.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(videos, request, view=self)
        serializer = VideosSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class ViewVideoDetailView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_video_listing",
                            [SuperAdmin]
                        )]
    def get(self, request,  cid , format=None):
        video = Videos.objects.filter(id=cid).first()
        if video is None:
            raise ValidationError("Invalid Video ID!")
        
        serializer = ViewVideoDetailSerializer(video)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class UploadVideoView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_chapter_video",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateVideoSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Video Created Successfully", data=ViewVideoDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class MarkVideoUploadCompleteView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter_video",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        video = Videos.objects.filter(id=cid).first()
        if video is None:
            raise ValidationError("Invalid Video ID!")
        
        serializer = MarkVideoUploadCompleteSerializer(video, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Video Updated Successfully", data=ViewVideoDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateVideoView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter_video",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        video = Videos.objects.filter(id=cid).first()
        if video is None:
            raise ValidationError("Invalid Video ID!")
        
        serializer = EditVideoserializer(video, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Video Updated Successfully", data=ViewVideoDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UpdateVideoStatusView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter_video",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        video = Videos.objects.filter(id=cid).first()
        if video is None:
            raise ValidationError("Invalid Video ID!")
        
        serializer = ChangeVideostatusSerializer(video, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Video Upload Completed Successfully", data=ViewVideoDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class DeleteVideoView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_chapter_video",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            video = Videos.objects.get(id = cid)
            video.delete()
            return success_response(message="Video Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except Videos.DoesNotExist:
            return error_response(message="Video not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        

class CategoryListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "category_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        category = Categories.objects.all()
        
        search_filter = filters.SearchFilter()
        category = search_filter.filter_queryset(request, category, self)

        ordering_filter = filters.OrderingFilter()
        category = ordering_filter.filter_queryset(request, category, self)

        if not category.ordered:
            category = category.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(category, request, view=self)
        serializer = CategorySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    

class CreateCategoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_category",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateCategorySerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Category Created Successfully", data=CategorySerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class EditCategoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_category",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = Categories.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Category ID!")
        
        serializer = EditCategorySerializer(category, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Category Updated Successfully", data=CategorySerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateCategoryStatusView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_category",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = Categories.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Category ID!")
        
        serializer = ChangeCategoryStatusSerializer(category, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Category Status Updated Successfully", data=CategorySerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteCategoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_category",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = Categories.objects.get(id = cid)
            course.delete()
            return success_response(message="Category Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except Categories.DoesNotExist:
            return error_response(message="Category not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        


class CourseListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "course_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        
        course = Course.objects.all()
        
        search_filter = filters.SearchFilter()
        course = search_filter.filter_queryset(request, course, self)

        ordering_filter = filters.OrderingFilter()
        course = ordering_filter.filter_queryset(request, course, self)

        if not course.ordered:
            course = course.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(course, request, view=self)
        serializer = CourseSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class ViewCourseDetailView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "course_listing",
                            [SuperAdmin]
                        )]
    def get(self, request,  cid , format=None):
        course = Course.objects.filter(id=cid).first()
        if course is None:
            raise ValidationError("Invalid Course ID!")
        
        serializer = ViewCourseDetailSerializer(course)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class CreateCourseView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_course",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateCourseSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Course Created Successfully", data=CourseDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
class EditCourseView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_category",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        course = Course.objects.filter(id=cid).first()
        if course is None:
            raise ValidationError("Invalid Course ID!")
        
        serializer = EditCourseSerializer(course, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Course Updated Successfully", data=CourseDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateCourseStatusView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_course",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        course = Course.objects.filter(id=cid).first()
        if course is None:
            raise ValidationError("Invalid Course ID!")
        
        serializer = ChangeCourseStatusSerializer(course, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Course Status Updated Successfully", data=CourseDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteCourseView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_course",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = Course.objects.get(id = cid)
            course.delete()
            return success_response(message="Course Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return error_response(message="Course not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        

class CategoryListView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        subject = Categories.objects.filter(status=True, parent__isnull=True).order_by("-id")
        serializer = CategoryListSerializer(subject, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class SubCategoryListView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, cid=None):
        subject = Categories.objects.filter(status=True, parent_id = cid).order_by("-id")
        serializer = CategoryListSerializer(subject, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class AssignChapterCourseView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_course",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        course = Course.objects.filter(id=cid).first()
        if course is None:
            raise ValidationError("Invalid Course ID!")
        
        serializer = AssignChapterCourseSerializer(course, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Chapter Assigned Successfully", data=CourseDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)



class ChapterBookListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_book_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        
        chapters = ChapterBooks.objects.all()
        
        course_id = request.query_params.get('course_id')
        chapter_id = request.query_params.get('chapter_id')
        if course_id:
            if chapter_id:
                chapters = chapters.filter(chapter_id=chapter_id)
            else:
                chapter_list = CourseChapters.objects.filter(course_id = course_id).values_list("chapter",flat=True)
                chapters = chapters.filter(chapter_id__in=chapter_list)
        
        status = request.query_params.get('status')
        if status:
            chapters = chapters.filter(status=status)


        search_filter = filters.SearchFilter()
        chapters = search_filter.filter_queryset(request, chapters, self)

        ordering_filter = filters.OrderingFilter()
        chapters = ordering_filter.filter_queryset(request, chapters, self)

        if not chapters.ordered:
            chapters = chapters.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(chapters, request, view=self)
        serializer = ChapterBooksSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class ViewChapterBookView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_book_listing",
                            [SuperAdmin]
                        )]
    def get(self, request,  cid , format=None):
        chapter = ChapterBooks.objects.filter(id=cid).first()
        if chapter is None:
            raise ValidationError("Invalid Chapter ID!")
        
        serializer = ViewChapterBooksSerializer(chapter)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class CreateChapterBookView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_chapter_book",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateChapterBookSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Chapter Book Created Successfully", data=ViewChapterBooksSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class EditChapterBookView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter_book",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        chapter = ChapterBooks.objects.filter(id=cid).first()
        if chapter is None:
            raise ValidationError("Invalid Chapter ID!")
        
        serializer = EditChapterBookSerializer(chapter, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Chapter Book Updated Successfully", data=ViewChapterBooksSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UpdateChapterBookStatusView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter_book",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        chapter = ChapterBooks.objects.filter(id=cid).first()
        if chapter is None:
            raise ValidationError("Invalid Chapter ID!")
        
        serializer = ChangeChapterBookstatusSerializer(chapter, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Chapter Status Updated Successfully", data=ViewChapterBooksSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class DeleteChapterBookView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_chapter_book",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = ChapterBooks.objects.get(id = cid)
            course.delete()
            return success_response(message="Chapter Book Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except ChapterBooks.DoesNotExist:
            return error_response(message="Chapter Book not found", data = [], status_code=status.HTTP_204_NO_CONTENT)
        

class ParentCategoryListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, format=None):
        topic = Categories.objects.filter(parent__isnull=True).order_by("-id")
        serializer = CategoriesListSerializer(topic, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class CourseListView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, format=None):
        topic = Course.objects.filter(status=True).order_by("-id")
        serializer = CourseListSerializer(topic, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class CourseSubjectListView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, cid, format=None):
        subject = CourseChapters.objects.filter(course_id=cid, chapter__status = True).order_by("order")
        serializer = CourseSubjectInfoSerializer(subject, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    



class GenerateUploadSignedUrlView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_course",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = GenerateUploadSignedUrlSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Success", data=user, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class GetTopicHistoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = Topics.objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid Topic ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = TopicsHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    


class GetChaptersHistoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = Chapters.objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid Chapter ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = ChaptersHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    

class GetCourseHistoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = Course.objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid Course ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = CourseHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    


class GetEbookHistoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = ChapterBooks.objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid EBook ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = EbooksHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    

class GetVideoHistoryView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, tid=None):
        
        topics = Videos.objects.filter(id = tid).first()
        if topics is None:
            raise ValidationError("Invalid Video ID")
        
        history_queryset = topics.history.all().order_by('-history_date')

        serializer = VideoHistorySerializer(history_queryset, many=True)
        return success_response(
                message="Success",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
    




class GetCourseSampleVideoView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, cid =None, format=None):
        category = CourseSampleVideos.objects.filter(course_id = cid).order_by("name")
        serializer = CourseSampleVideoListSerializer(category, many=True)
        return Response({"status":"success",'message':'',"data":serializer.data }, status = status.HTTP_200_OK)
    


class DeleteCourseSampleVideoView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = CourseSampleVideos.objects.get(id = cid)
            course.delete()
            return success_response(message="success", data={}, status_code=status.HTTP_200_OK)
        except CourseSampleVideos.DoesNotExist:
            return error_response(message="failed", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        


class UploadCourseSampleVideoView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        
        serializer = UpdateCoursesSampleVideoSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return success_response(message="Sample video uploaded successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class GetInstructorListView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, cid =None, format=None):
        category = InstructorProfile.objects.all().order_by("-id")
        serializer = InstructorInfoserializer(category, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class GetCourseInstructorsView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, cid =None, format=None):
        category = CourseInstructors.objects.filter(course_id = cid).order_by("-id")
        serializer = CourseInstructorsListSerializer(category, many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class AddCourseInstructorsView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = AddCourseInstructorsSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return success_response(message="Instructor added successfully", data=serializer.data, status_code=status.HTTP_200_OK)
        
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class DeleteCourseInstructorView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = CourseInstructors.objects.get(id = cid)
            course.delete()
            return success_response(message="Instructor Deleted Successfully", data={}, status_code=status.HTTP_200_OK)
        
        except CourseInstructors.DoesNotExist: 
            return error_response(message="No Instructor found!", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        


class GetRelatedCoursesView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def get(self, request, cid =None, format=None):
        category = FrequentlyBoughtCourse.objects.filter(course_id = cid).order_by("-id")
        serializer = FrequentlyBoughtCourseListSerializer(category, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class AddRelatedCoursesView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        
        serializer = AddRelatedCoursesSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return success_response(message="Course added successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class DeleteRelatedCourseView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        
        try:
            course = FrequentlyBoughtCourse.objects.get(id = cid)
            course.delete()
            return success_response(message="Related Course Deleted Successfully", data={}, status_code=status.HTTP_200_OK)
            
        except FrequentlyBoughtCourse.DoesNotExist:
            return error_response(message="No Record Found!", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        


class GetCoursesFAQsListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, cid=None, format=None):
        
        category = CourseFaqs.objects.filter(course_id = cid).order_by("-id")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(category, request, view=self)
        serializer = CourseFaqsListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    


class AddCourseFAQView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        
        serializer = CreateCourseFaqsSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return success_response(message="FAQ created successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class UpdateCourseFAQView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        
        course = CourseFaqs.objects.filter(id=cid).first()
        if course is None:
            return Response({"status": "failed","message": "error","errors": {"non_field_errors": "Invalid FAQ ID"}}, status.HTTP_403_FORBIDDEN)
        
        serializer = UpdateCourseFaqsSerializer(course, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="FAQ updated successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class DeleteCoursFAQeView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        
        try:
            course = CourseFaqs.objects.get(id = cid)
            course.delete()
            return success_response(message="FAQ deleted successfully", data={}, status_code=status.HTTP_200_OK)
            
        except CourseFaqs.DoesNotExist: 
            return error_response(message="No Record Found!", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        

class UpdateFAQStatusView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [SuperAdmin]
                        )]
    def post(self, request, id=None, format=None):
        
        user_info = CourseFaqs.objects.filter(id = id).first()
        if user_info is None:
            return error_response(message="Invalid FAQ ID", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        
        serializer = UpdateFAQStatusSerializer(user_info ,data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="FAQ Status Updated successfully", data={}, status_code=status.HTTP_200_OK)
            
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class TrailCourseListView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "manage_trail_course",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    def get(self, request, format=None):
        
        chapters = TrailCourses.objects.all().order_by('-id')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(chapters, request, view=self)
        serializer = TrailCoursesSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class CreateTrailCourseView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "manage_trail_course",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateTrailCourseSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Course Added Successfully for trail", data=TrailCoursesSerializer(user,many=True).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteTrailCourseView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "manage_trail_course",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = TrailCourses.objects.get(id = cid)
            course.delete()
            return success_response(message="Trial Course Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except TrailCourses.DoesNotExist:
            return error_response(message="Trial Course not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)