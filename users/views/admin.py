from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from users.serializers import *
from users.renderers import UserRenderer
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


class GetUserListingView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                            "user_role_specific_permission_list",
                            [SuperAdmin],
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name','last_name',"email"]
    ordering_fields = ['first_name',"last_name","email", 'created_at', 'id', 'status'] 
    def get(self, request, user_type, format=None):
        
        user_role = get_url_role(user_type)
        if user_role is None:
            raise NotFound("Invalid User Type!")

        users_list = User.objects.filter(role = user_role)
        search_filter = filters.SearchFilter()
        users_list = search_filter.filter_queryset(request, users_list, self)

        ordering_filter = filters.OrderingFilter()
        users_list = ordering_filter.filter_queryset(request, users_list, self)

        if not users_list.ordered:
            users_list = users_list.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(users_list, request, view=self)
        serializer = UserListingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class CreateUserView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "user_role_specific_permission_create",
                            [SuperAdmin]
                        )]
    def post(self, request, user_type, format=None):
        user_role = get_url_role(user_type)
        if user_role is None:
            raise NotFound("Invalid User Type!")
        
        serializer = CreateUserSerializer(data = request.data, context={'user':request.user,"user_type":user_type})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="User Created Successfully", data=StaffProfileSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UpdateUserView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "user_role_specific_permission_update",
                            [SuperAdmin]
                        )]
    def post(self, request, user_type, id=None, format=None):

        user_role = get_url_role(user_type)
        if user_role is None:
            raise NotFound("Invalid User Type!")
        
        user_info = User.objects.filter(id = id , role = user_role).first()
        if user_info is None:
            raise NotFound("Invalid User ID!")
        
        serializer = UpdateUserSerializer(user_info ,data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="User Updated Successfully", data=StaffProfileSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UpdateUserStatustView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "user_role_specific_permission_update",
                            [SuperAdmin]
                        )]
    def post(self, request, user_type, id=None, format=None):

        user_role = get_url_role(user_type)
        if user_role is None:
            raise NotFound("Invalid User Type!")
        
        user_info = User.objects.filter(id = id , role = user_role).first()
        if user_info is None:
            raise NotFound("Invalid User ID!")
        
        serializer = ChangeUserStatusSerializer(user_info, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Student Status Updated Successfully", data=StaffProfileSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteUserstView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "user_role_specific_permission_update",
                            [SuperAdmin]
                        )]
    def delete(self, request, user_type, id=None, format=None):

        user_role = get_url_role(user_type)
        if user_role is None:
            raise NotFound("Invalid User Type!")
        
        user_info = User.objects.filter(id = id , role = user_role).first()
        if user_info is None:
            raise NotFound("Invalid User ID!")
        
        user_info.delete()
        return success_response(message="User Deleted Successfully", data={}, status_code=status.HTTP_200_OK)
        


class GetRolesListingView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "roles_permission",
                            [SuperAdmin]
                        )]
    def get(self, request,format=None):
        all_role_classes = roles.RolesManager.get_roles()
        roles_data = [
            role_class
            for role_class in all_role_classes
            if role_class.get_name() not in ['SuperAdmin']
        ]

        serializer = RoleSerializer(roles_data, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    


class GetRolesPermissionView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "roles_permission",
                            [SuperAdmin]
                        )]
    def get(self, request, role_name=None,format=None):
        role_class = get_role(role_name)
        if role_class is None:
            raise NotFound(f"Role '{role_name}' not found.")

        permissions = RolePermissions.objects.filter(role = role_name).order_by("id")
        serializer = RolePermissionSerializer(permissions,many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    


class UpdateRolesPermissionView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "roles_permission",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = UpdateRolesPermissionSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Permission Updated Successfully!", data=[], status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class GetMyPermissionListingView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        permissions = available_perm_status(request.user)
        return success_response(message="", data=permissions, status_code=status.HTTP_200_OK)
    

class GetUserPermissionListingView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "manage_user_permissions",
                            [SuperAdmin]
                        )]
    def get(self, request, id, format=None):
        user = User.objects.filter(id = id).first()
        if user is not None:
            permissions = available_perm_status(user)
            return success_response(message="", data=permissions, status_code=status.HTTP_200_OK)
        return error_response(message="Invalid User ID", data = [], status_code=status.HTTP_400_BAD_REQUEST)
    


class UpdateRolesPermissionView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "roles_permission",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = UpdateRolesPermissionSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Permission Updated Successfully!", data=[], status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UpdatetUserPermissionView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_roles_permission",
                            [SuperAdmin]
                        )]
    def post(self, request, id, format=None):
        user = User.objects.filter(id = id).first()
        if user is None:
            raise NotFound("Invalid User ID")
        
        serializer = UpdateUserPermissionSerializer(user, data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Permission Updated Successfully!", data=[], status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class AdminResetUserDevicesView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_roles_permission",
                            [SuperAdmin]
                        )]
    def get(self, request, cid, sid):

        user = User.objects.get(id = sid)
        
        UserDevices.objects.filter(user = user).update(status = DeviceStatus.Inactive)
        
        return success_response(message="Success", data={}, status_code=status.HTTP_200_OK)
    


class UpdateInstructorPublicProfileView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_roles_permission",
                            [SuperAdmin]
                        )]
    def post(self, request, id=None, format=None):
        user_info = User.objects.filter(id = id , role = User.Instructor).first()
        if user_info is None:
            raise NotFound("Invalid User ID")
        
        serializer = UpdateInstructorPublicProfileSerializer(user_info ,data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return Response({"status":"success",'message':'Instructor Updated Successfully',"data":[]}, status = status.HTTP_201_CREATED)
        return Response({"status":"failed",'message':'',"error":serializer.errors}, status.HTTP_400_BAD_REQUEST)



class GetStudentListingView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name',"last_name","email", 'date_joined', 'id', 'is_active',"phone1","category"]
    ordering_fields = ['first_name',"last_name","email", 'date_joined', 'id', 'is_active',"phone1","category"] 
    def get(self, request, format=None):
        
        users_list = User.objects.filter(role = User.Student)

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

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')

        reference_ids_param = request.query_params.get('reference_id')
        if reference_ids_param:
            search_terms = [
                term.strip() for term in reference_ids_param.split(',') if term.strip()
            ]
            if search_terms:
                q_objects = Q()
                for term in search_terms:
                    q_objects |= Q(**{'reference_id__icontains': term})
                
                users_list = users_list.filter(q_objects)


        if category:
            category = category.split(',')
            topics = topics.filter(user__category__in = category)

        student_type = request.query_params.get('student_type')
        if student_type:
            student_type = student_type.split(',')
            topics = topics.filter(user__student_type__in =student_type)

        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                start_datetime_aware = timezone.make_aware(start_datetime, timezone.get_current_timezone())
                topics = topics.filter(created_at__gte=start_datetime_aware)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                end_datetime_aware = timezone.make_aware(end_datetime, timezone.get_current_timezone())
                topics = topics.filter(created_at__lte=end_datetime_aware)
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
    


class GetStudentDetailView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_listing",
                            [SuperAdmin]
                        )]
    def get(self, request, id=None,format=None):
        subadmin_list = User.objects.filter(role = User.Student, id=id).first()
        serializer = StudentProfileSerializer(subadmin_list,context={'user':request.user})
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class CreateStudentView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_student",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateStudentSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="User Created Successfully", data=StudentProfileSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UpdateStudentView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_student",
                            [SuperAdmin]
                        )]
    def post(self, request, id=None, format=None):
        user_info = User.objects.filter(id = id , role = User.Student).first()
        if user_info is None:
            raise NotFound("Invalid User ID!")
        
        serializer = UpdateStudentSerializer(user_info ,data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="User Updated Successfully", data=StudentProfileSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UpdateStudenStatustView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_student",
                            [SuperAdmin]
                        )]
    def post(self, request,  id , format=None):
        user_info = User.objects.filter(id = id , role = User.Student).first()
        if user_info is None:
            raise NotFound("Invalid User ID!")
        
        serializer = ChangeStudentStatusSerializer(user_info, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Student Status Updated Successfully", data=StudentProfileSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class AdminUpdateStudentPasswordView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "student_change_password",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = AdminUpdateStudentPasswordSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Password Updated successfully!", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)