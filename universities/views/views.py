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