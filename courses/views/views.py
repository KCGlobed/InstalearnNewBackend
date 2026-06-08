from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from courses.serializers import *
from subscription.models import *
from courses.renderers import CourseRenderer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import update_last_login
from rolepermissions.checkers import has_role
from django.db.models import Q
from mini_lms.utils import *
from rolepermissions import roles
from mini_lms.roles import *
from rest_framework.exceptions import NotFound
from mini_lms.permissions import RoleOrPermissionCheck
from mini_lms.pagination import CustomPageNumberPagination
from rest_framework import filters
from django.db.models import Count, Case, When, IntegerField



class GetHomepageCategoryListing(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, format=None):
        category = Categories.objects.filter(
                            status=True, 
                            parent__isnull=True
                        ).order_by('?')[:12]
        serializer = HomepageCategorySerializer(category, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class GetHomepageTagsListing(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, format=None):
        category = Tags.objects.filter(
                            status=True,
                        ).order_by('?')[:6]
        serializer = HomepageTagsSerializer(category, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class GetHomepageTagWiseCoursesListing(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, id=None):
        category = CourseTags.objects.filter(
                            tags__status=True,
                            tags_id = id,
                            course__status=True,
                        ).order_by('?')[:10]
        serializer = HomepageTagWiseCoursesSerializer(category, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class GetHomepageRecentCoursesListing(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, id=None):
        category = Course.objects.filter(
                            status=True
                        ).order_by('created_by')[:4]
        serializer = HomepageCourseDetailSerializer(category, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class GetCourseCategory(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, format=None):
        category = Categories.objects.filter(status = True, parent__isnull = True).order_by("order")
        serializer = CategorySerializer(category, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
        

class GetSubCourseCategory(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, id =None, format=None):
        category = Categories.objects.filter(status = True, parent_id = id).order_by("order")
        serializer = CategorySerializer(category, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
        

class GetCourseListingCategoryWise(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, id=None, format=None):
        category = CourseCategories.objects.filter(category_id = id, course__status = True)
        serializer = CourseCategorySerializer(category, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
        

class GetLearnerCourseView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, format=None):
        category = Course.objects.filter(status = True).order_by('?')[:8]
        serializer = CourseSerializer(category, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)


class GetPlansListingView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, id=None, format=None):
        category = SubscriptionPlans.objects.filter(status = True).order_by("id")
        serializer = PlansListingSerializer(category, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)


class GetRelatedCoursesListView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, id=None, format=None):
        
        course_id = request.query_params.get('course_id')
        if course_id:
            course_id_list = course_id.split(",")
            info = FrequentlyBoughtCourse.objects.filter(course_id__in = course_id_list)
            serializer = FrequentlyBoughtCourseSerializer(info, many=True)
            return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
        return success_response(message="success", data={}, status_code=status.HTTP_200_OK)
    

class GetCourseDetailView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, id=None, format=None):
        category = Course.objects.filter(id = id).first()
        if category is None:
            raise serializers.ValidationError('Invalid Course ID')
        serializer = CourseDetailSerializer(category)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class GetCourseReviewRatingView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, id=None, format=None):
        category = CourseReviewRating.objects.filter(course_id = id,approved = 1, status=True).order_by("-id")
        serializer = CourseReviewRatingSerializer(category, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class SearchDropdownView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, format=None):
        name = request.query_params.get('name', None)
        data = {
            "category": [],
            "course": []
        }

        if name:
            categories = Categories.objects.filter(
                status=1,
                parent__isnull=True
            ).filter(
                Q(name__icontains=name) | Q(categories__name__icontains=name)
            ).distinct().order_by("name")
            
            courses = Course.objects.filter(
                name__icontains=name, 
                status=1
            ).order_by("name")

            # Serialize the data
            category_serializer = SearchCategorySerializer(categories, many=True)
            course_serializer = SearchCourseSerializer(courses, many=True)
            
            data["category"] = category_serializer.data
            data["course"] = course_serializer.data

        return success_response(
            message="success", 
            data=data, 
            status_code=status.HTTP_200_OK
        )

    
class SearchCourseView(APIView):
    renderer_classes = [CourseRenderer]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'id',"total_reviews","avg_rating"]
    def get(self, request, format=None):
        queryset = Course.objects.filter(status=1)

        name = request.query_params.get('name')
        rating = request.query_params.get('rating')
        duration = request.query_params.get('duration')
        level = request.query_params.get('level')
        subcategories = request.query_params.get('subcategories')
        tags = request.query_params.get('tags')

        if name:
            # Optimize by combining filters into one complex Q object
            instructor_matches = CourseInstructors.objects.filter(
                instructor__text_1__icontains=name
            ).values_list('course', flat=True)

            queryset = queryset.filter(
                Q(name__icontains=name) |  
                Q(id__in=instructor_matches)
            )

        if rating:
            queryset = queryset.filter(avg_rating__gte=rating)

        if duration:
            duration_list = duration.split(",")
            queryset = queryset.filter(video_duration_type__in=duration_list)

        if level:
            level_list = level.split(",")
            queryset = queryset.filter(level__in=level_list)

        if subcategories:
            cat_list = subcategories.split(",")
            cat_matches = CourseCategories.objects.filter(
                category_id__in=cat_list
            ).values_list('course', flat=True)
            queryset = queryset.filter(id__in=cat_matches)

        if tags:
            tag_list = tags.split(",")
            tag_matches = CourseTags.objects.filter(
                tags_id__in=tag_list
            ).values_list('course', flat=True)
            queryset = queryset.filter(id__in=tag_matches)

        search_filter = filters.SearchFilter()
        queryset = search_filter.filter_queryset(request, queryset, self)

        ordering_filter = filters.OrderingFilter()
        queryset = ordering_filter.filter_queryset(request, queryset, self)

        # 4. Pagination and Serialization
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)

        serializer = CourseSearchSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class CategoryCourseView(APIView):
    renderer_classes = [CourseRenderer]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'id',"total_reviews","avg_rating"]
    def get(self, request, id=None):
        queryset = Course.objects.filter(status=True)
        cat_list = Categories.objects.filter(parent_id = id, status=True).values_list("id",flat =True)
        cat_matches = CourseCategories.objects.filter(
            category_id__in=cat_list,
            category__status = True
        ).values_list('course', flat=True)
        print(cat_matches)
        queryset = queryset.filter(id__in=cat_matches)

        search_filter = filters.SearchFilter()
        queryset = search_filter.filter_queryset(request, queryset, self)

        ordering_filter = filters.OrderingFilter()
        queryset = ordering_filter.filter_queryset(request, queryset, self)

        # 4. Pagination and Serialization
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)

        serializer = CourseSearchSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class SearchFiltersListView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, format=None):
        category = Categories.objects.filter(status = True, parent__isnull = True).order_by("name")
        serializer = SearchCategorySerializer(category, many=True)

        category = Tags.objects.filter(
                            status=True,
                        ).order_by('name')
        tags_serializer = HomepageTagsSerializer(category, many=True)


        counts = Course.objects.filter(status=1).aggregate(
            r1=Count(Case(When(avg_rating__gte=5.0, then=1), output_field=IntegerField())),
            r2=Count(Case(When(avg_rating__gte=4.0, then=1), output_field=IntegerField())),
            r3=Count(Case(When(avg_rating__gte=3.0, then=1), output_field=IntegerField())),
            r4=Count(Case(When(avg_rating__gte=2.0, then=1), output_field=IntegerField())),
            r5=Count(Case(When(avg_rating__gte=1.0, then=1), output_field=IntegerField())),
        )

        rating = [{"5":counts['r1']}, {"4":counts['r2']}, {"3":counts['r3']}, {"2":counts['r4']}, {"1":counts['r5']}]

        data = [
            {'value': choice.value, 'label': choice.label} 
            for choice in CourseLevel
        ]
        level_serializer = CourseLevelSerializer(data, many=True)


        return success_response(message="success", data={"category_filter":serializer.data,"tags_filter":tags_serializer.data,"level_filter":level_serializer.data,"rating":rating}, status_code=status.HTTP_200_OK)
    


class GetPartnerListingView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, format=None):
        category = PartnerImages.objects.all()
        serializer = PartnerImagesSerializer(category, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class GetLMSTestimonialView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, format=None):
        content = Testimonials.objects.filter(status = 1)
        serializer = GetLMStestimonialSerializer(content, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class GetCourseAnnouncementListingView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request,  cid , format=None):
        course = CourseAnnouncements.objects.filter(course_id=cid).order_by("-id")
        serializer = ViewCourseAnnouncementSerializer(course,many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class AddCommentCourseAnnouncementsView(APIView):
    renderer_classes = [CourseRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        
        serializer = AddCommentInCourseAnnouncementsSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return success_response(message="Comment Added in Announcement successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)