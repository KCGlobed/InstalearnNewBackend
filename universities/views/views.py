from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from universities.serializers import *
from cms.models import *
from universities.renderers import UniversityRenderer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import update_last_login
from rolepermissions.checkers import has_role
from django.db.models import Q
from mini_lms.utils import *
from rolepermissions import roles
from rolepermissions.permissions import available_perm_status
from mini_lms.roles import *
from rest_framework.exceptions import NotFound, ValidationError
from mini_lms.permissions import RoleOrPermissionCheck
from mini_lms.pagination import CustomPageNumberPagination
from rest_framework import filters


class InstitutionTypeChoicesView(APIView):
    renderer_classes = [UniversityRenderer]
    def get(self, request, format=None):
        choices = [
            {"value": value, "label": label}
            for value, label in INSTITUTION_TYPE_CHOICES
        ]
        return success_response(message="", data=choices, status_code=status.HTTP_200_OK)


class JobRolesChoicesView(APIView):
    renderer_classes = [UniversityRenderer]
    def get(self, request, format=None):
        choices = [
            {"value": value, "label": label}
            for value, label in JOB_ROLE_CHOICES
        ]
        return success_response(message="", data=choices, status_code=status.HTTP_200_OK)


class DepartmentTypeChoicesView(APIView):
    renderer_classes = [UniversityRenderer]
    def get(self, request, format=None):
        choices = [
            {"value": value, "label": label}
            for value, label in DEPARTMENT_CHOICES
        ]
        return success_response(message="", data=choices, status_code=status.HTTP_200_OK)
    
    
class SubmitUniversityRequestsView(APIView):
    renderer_classes = [UniversityRenderer]
    def post(self, request, format=None):
        serializer = SubmitUniversityRequestSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Application Submitted Successfully", data=serializer.data, status_code=status.HTTP_200_OK)

        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)



class GetDashboardCountersView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [UniversityAdmin]
                        )]
    def get(self, request,format=None):
        
        course_order = Order.objects.filter(
            user=request.user, 
            isPaid=True, 
            payment_type=PaymentType.Subscription
        ).first()

        no_of_licences = course_order.no_of_licence if course_order else 0 

        corporate_users = User.objects.filter(university=request.user.university, role = User.Student)
        users_id = list(corporate_users.values_list("id", flat=True))
        license_used = len(users_id)  # Avoids another .count() query

        course_count = UserCourses.objects.filter(user_id__in=users_id).count()

        video_stats = UserLectureProgress.objects.filter(user_id__in=users_id).aggregate(
            total_watched=Count('id'),
            total_duration=Sum('total_duration')
        )

        total_video_watched = video_stats['total_watched'] or 0
        total_duration_video_watched = video_stats['total_duration'] or 0

        data = {
            "no_of_licences": no_of_licences,
            "license_used": license_used,
            "remaning_licence": no_of_licences - license_used,
            "registered_users": license_used,
            "assigned_courses": course_count,
            "total_video_watched": total_video_watched,
            "total_duration_video_watched": total_duration_video_watched
        }
        return success_response(message="Success", data=data, status_code=status.HTTP_200_OK)



class ShareCourseAccessView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [UniversityAdmin]
                        )]
    def post(self, request, format=None):
        serializer = ShareCourseAccessSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Course Access Shared Successfully", data=StudentListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)



class GetCorporateUsersListView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [UniversityAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name',"last_name","email", 'date_joined', 'id', 'is_active',"phone1","category"]
    ordering_fields = ['first_name',"last_name","email", 'date_joined', 'id', 'is_active',"phone1","category"] 
    def get(self, request, format=None):
        
        users_list = User.objects.filter(corporate = request.user)

        first_name = request.query_params.get('first_name')
        if first_name:
            users_list = users_list.filter(first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            users_list = users_list.filter(last_name__icontains = last_name)

        email = request.query_params.get('email')
        if email:
            users_list = users_list.filter(email__icontains = email)

        phone1 = request.query_params.get('phone')
        if phone1:
            users_list = users_list.filter(phone1__icontains = phone1)

        is_active = request.query_params.get('status')
        if is_active:
            users_list = users_list.filter(is_active = is_active)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                users_list = users_list.filter(created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                users_list = users_list.filter(created_at__lte=end_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")
            

        search_filter = filters.SearchFilter()
        users_list = search_filter.filter_queryset(request, users_list, self)

        ordering_filter = filters.OrderingFilter()
        users_list = ordering_filter.filter_queryset(request, users_list, self)

        if not users_list.ordered:
            users_list = users_list.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(users_list, request, view=self)
        serializer = StudentListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AssignCourseAccessView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [UniversityAdmin]
                        )]
    def post(self, request, format=None):
        serializer = AssignCourseAccessSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Course Access Shared Successfully", data=StudentListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class RemoveCourseAccessView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [UniversityAdmin]
                        )]
    def post(self, request, format=None):
        serializer = RemoveCourseAccessSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Course Access Removed Successfully", data=StudentListingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)