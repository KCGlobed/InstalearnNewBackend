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
    def post(self, request, format=None):
        if request.data:
            category = Course.objects.all()
            if 'name' in request.data:
                if request.data['name'] != "":
                    course_cat = CourseInstructors.objects.filter(instructor__text_1__icontains = request.data['name']).values_list('course', flat=True)

                    course_cateor = CourseCategories.objects.filter(category_id__name__icontains = request.data['name']).values_list('course', flat=True)

                    category = category.filter(Q(name__icontains=request.data['name']) | Q(short_description__icontains=request.data['name']) | Q(id__in=course_cat) | Q(id__in=course_cateor))

                else:
                    return error_response(message="Name is required field!", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
                
            else:
                return error_response(message="Name is required field!", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
                
            if 'rating' in request.data:
                if request.data['rating'] != "":
                    category = category.filter(avg_rating__gte=request.data['rating'])

            if 'duration' in request.data:
                if request.data['duration'] != "":
                    duration_type = request.data['duration'].split(",")
                    category = category.filter(video_duration_type__in=duration_type)
                    
            if 'topics' in request.data:
                if request.data['topics'] != "":
                    cat = request.data['topics'].split(",")
                    course_cat = CourseCategories.objects.filter(category_id__in = cat).values_list('course', flat=True)
                    category = category.filter(id__in=course_cat)
            
            category = category.filter(status = 1)
            category.order_by("name")
            serializer1 = CourseSerializer(category, many=True)

            return success_response(message="success", data=serializer1.data, status_code=status.HTTP_200_OK)
        
        return success_response(message="success", data={}, status_code=status.HTTP_200_OK)
    

class SearchCategoryListView(APIView):
    renderer_classes = [CourseRenderer]
    def get(self, request, format=None):
        category = Categories.objects.filter(status = 1, parent__isnull = False).order_by("name")
        serializer = CategorySerializer(category, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    

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