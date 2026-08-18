from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from universities.serializers import *
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
from rest_framework.exceptions import NotFound , ValidationError
from mini_lms.permissions import RoleOrPermissionCheck
from mini_lms.pagination import CustomPageNumberPagination
from rest_framework import filters
from django.utils import timezone
from datetime import timedelta



class GetUniversityRequestsListingView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "university_requests_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name','last_name',"email"]
    ordering_fields = ['first_name', 'created_at', 'id', 'last_name',"email"] 
    def get(self, request, format=None):
        
        plans = University.objects.all()
        
        first_name = request.query_params.get('first_name')
        if first_name:
            plans = plans.filter(first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            plans = plans.filter(last_name__icontains = last_name)

        work_email = request.query_params.get('work_email')
        if work_email:
            plans = plans.filter(work_email__icontains = work_email)

        country = request.query_params.get('country')
        if country:
            plans = plans.filter(country__icontains = country)

        institution_name = request.query_params.get('institution_name')
        if institution_name:
            plans = plans.filter(institution_name__icontains = institution_name)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                plans = plans.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                plans = plans.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")


        search_filter = filters.SearchFilter()
        plans = search_filter.filter_queryset(request, plans, self)

        ordering_filter = filters.OrderingFilter()
        plans = ordering_filter.filter_queryset(request, plans, self)

        if not plans.ordered:
            plans = plans.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(plans, request, view=self)
        serializer = UniversityRequestsSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)