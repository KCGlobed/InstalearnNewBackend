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



class GetCourseDetailView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, id=None, format=None):
        category = Course.objects.filter(id = id).first()
        if category is None:
            raise serializers.ValidationError('Invalid Course ID')
        serializer = CourseDetailSerializer(category)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class SearchDropdownView(APIView):
    renderer_classes = [CourseRenderer]
    def post(self, request, format=None):
        
        if request.data:
            if request.data['name'] != "":
                category = Categories.objects.filter(name__icontains = request.data['name'], status = 1)
                category.order_by("name")
                
                serializer = SearchCategorySerializer(category, many=True)

                course = Course.objects.filter(name__icontains = request.data['name'], status = 1)
                course.order_by("name")

                serializer1 = SearchCourseSerializer(course, many=True)

                return success_response(message="success", data={"category":serializer.data, "course":serializer1.data}, status_code=status.HTTP_200_OK)
            
        return success_response(message="success", data={ }, status_code=status.HTTP_200_OK)

    
class SearchCourseView(APIView):
    renderer_classes = [CourseRenderer]
    pagination_class = CustomPageNumberPagination
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
    

class SearchFilterCountView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, format=None):
        rating_count_1 = Course.objects.filter(avg_rating__gte=4.5, status = 1).count()
        rating_count_2 = Course.objects.filter(avg_rating__gte=4.0, status = 1).count()
        rating_count_3 = Course.objects.filter(avg_rating__gte=3.5, status = 1).count()
        rating_count_4 = Course.objects.filter(avg_rating__gte=3.0, status = 1).count()

        duration_1 = Course.objects.filter(video_duration_type="extraShort", status = 1).count()
        duration_2 = Course.objects.filter(video_duration_type="short", status = 1).count()
        duration_3 = Course.objects.filter(video_duration_type="medium", status = 1).count()
        duration_4 = Course.objects.filter(video_duration_type="long", status = 1).count()
        duration_5 = Course.objects.filter(video_duration_type="extraLong", status = 1).count()
        rating = []
        rating.append(rating_count_1)
        rating.append(rating_count_2)
        rating.append(rating_count_3)
        rating.append(rating_count_4)
        duration = []
        duration.append(duration_1)
        duration.append(duration_2)
        duration.append(duration_3)
        duration.append(duration_4)
        duration.append(duration_5)

        return success_response(message="success", data={"rating":rating,"duration":duration}, status_code=status.HTTP_200_OK)
    


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