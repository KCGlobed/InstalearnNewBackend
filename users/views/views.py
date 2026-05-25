from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from users.serializers import *
from cms.models import *
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
from rest_framework.exceptions import NotFound, ValidationError
from mini_lms.permissions import RoleOrPermissionCheck


class UserLoginView(APIView):
    renderer_classes = [UserRenderer]
    def post(self, request, format=None):
        serializer = UserLoginSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            email = serializer.data.get('email').lower()
            password = serializer.data.get('password')
            user = authenticate(email = email, password = password)
            if user is not None:

                if not check_domain_match(user.email):
                    if user.is_locked():
                        return error_response(message=f"Account is locked. Please Contact to support.", data = {}, status_code=status.HTTP_400_BAD_REQUEST)


                    setting = GeneralSettings.objects.all().first()
                    if setting.allow_device_restriction:
                        
                        if not check_devices_login(user, serializer.data.get('device_type'), serializer.data.get('device_id'), setting):
                            user.failed_login_attempts += 1
                            
                            if user.failed_login_attempts >= 3:
                                user.locked_until = timezone.now() + timedelta(days=365)
                                user.unlocked_on = None

                                UserAccountLockDetail.objects.create(
                                    ip_address=get_client_ip(request), 
                                    user=user,
                                    device_type = serializer.data.get('device_type'),
                                    device_id = serializer.data.get('device_id')
                                )
                            user.save()
                            raise ValidationError("You have reached upto to allowed devices login limit")
                
                    
                UserDevices.objects.update_or_create(
                    user=user,
                    device_id=serializer.data.get('device_id'),
                    defaults={
                        'device_type': serializer.data.get('device_type'),
                        "ip_address":get_client_ip(request),
                        "status":DeviceStatus.Active
                    }
                )

                
                token = get_tokens_for_user(user)
                update_last_login(None, user)

                if user.current_refresh is not None:
                    try:
                        RefreshToken(user.current_refresh).blacklist()
                    except TokenError:
                        pass
                
                user.current_refresh = token['refresh']
                user.save()

                UserLoginActivity.objects.create(
                    login_IP=get_client_ip(request), 
                    user=user,
                    status='Success', 
                    country = get_country_from_ip(get_client_ip(request)),
                    device_type = serializer.data.get('device_type'),
                    device_id = serializer.data.get('device_id'),
                    user_agent_info = request.META['HTTP_USER_AGENT']
                )

                UserSession.objects.filter(user = user).delete()
                UserSession.objects.create(
                    login_IP=get_client_ip(request), 
                    user=user,
                    token=token['access'],
                )
                
                new_alert_login(user, get_client_ip(request))
                
                user.failed_login_attempts = 0
                user.locked_until = None
                user.save()

                image_url = user.image.url if user.image else None

                return success_response(message="Login Success", data={'token': token, 'user_role': serializer.data.get('role'), "user_id":user.id,"email":user.email,"first_name":user.first_name,"last_name":user.last_name,"phone":user.phone1,"image":image_url}, status_code=status.HTTP_200_OK)
            else:
                return error_response(message="failed", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UserSocialLoginView(APIView):
    renderer_classes = [UserRenderer]
    def post(self, request, format=None):
        serializer = UserSocialLoginSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            login(request, user)
            if user is not None:

                if user.is_locked():
                    return error_response(message=f"Account locked. Please Contact to support.", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
                
                setting = GeneralSettings.objects.all().first()
                if setting.allow_device_restriction:
                    
                    if not check_devices_login(user, serializer.data.get('device_type'), serializer.data.get('device_id'), setting):
                        user.failed_login_attempts += 1
                        
                        if user.failed_login_attempts >= 3:
                            user.locked_until = timezone.now() + timedelta(days=365)
                            user.unlocked_on = None
                            
                            UserAccountLockDetail.objects.create(
                                ip_address=get_client_ip(request), 
                                user=user,
                                device_type = serializer.data.get('device_type'),
                                device_id = serializer.data.get('device_id')
                            )
                        user.save()
                        
                        raise ValidationError("You have reached upto to allowed devices login limit")
                    
                    UserDevices.objects.update_or_create(
                        user=user,
                        device_id=serializer.data.get('device_id'),
                        defaults={
                            'device_type': serializer.data.get('device_type'),
                            "ip_address":get_client_ip(request),
                            "status":DeviceStatus.Active
                        }
                    )


                token = get_tokens_for_user(user)
                update_last_login(None, user)

                if user.current_refresh is not None:
                    try:
                        RefreshToken(user.current_refresh).blacklist()
                    except TokenError:
                        pass
                
                user.current_refresh = token['refresh']
                user.save()

                UserLoginActivity.objects.create(
                    login_IP=get_client_ip(request), 
                    user=user,
                    status='Success', 
                    device_type = serializer.data.get('device_type'),
                    device_id = serializer.data.get('device_id'),
                    user_agent_info = request.META['HTTP_USER_AGENT']
                )
                UserSession.objects.filter(user = user).delete()
                UserSession.objects.create(
                    login_IP=get_client_ip(request), 
                    user=user,
                    token=token['access'],
                )
                
                user.failed_login_attempts = 0
                user.locked_until = None
                user.save()

                image_url = user.image.url if user.image else None

                return success_response(message="Login Success", data={'token': token, 'user_role': get_user_role(user), "user_id":user.id,"email":user.email,"first_name":user.first_name,"last_name":user.last_name,"phone":user.phone1,"image":image_url}, status_code=status.HTTP_200_OK)
            else:
                return error_response(message="failed", data = {}, status_code=status.HTTP_400_BAD_REQUEST)
        
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class UserRegistrationView(APIView):
    renderer_classes = [UserRenderer]
    def post(self, request, format=None):
        serializer = UserRegistrationSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Please check your mailbox for the OTP.", data=[], status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UserVerifyOTPView(APIView):
    renderer_classes = [UserRenderer]
    def post(self, request, format=None):
        serializer = UserVerifyOTPSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user = User.objects.get(email=serializer.data.get('email').lower())
            token = get_tokens_for_user(user)
            UserSession.objects.filter(user = user).delete()
            UserSession.objects.create(
                login_IP=get_client_ip(request), 
                user=user,
                token=token['access'],
            )

            image_url = user.image.url if user.image else None

            return success_response(message="Email Verified Successfully!", data={'token':token, 'user_role': get_user_role(user), "user_id":user.id,"email":user.email,"first_name":user.first_name,"last_name":user.last_name,"phone":user.phone1,"image":image_url}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
            
    


class UserSendVerificationOTPView(APIView):
    renderer_classes = [UserRenderer]
    def post(self, request, format=None):
        serializer = UserVerificationOTPSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Verification OTP sent successfully!", data=[], status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)



class UserForgotPasswordView(APIView):
    renderer_classes = [UserRenderer]
    def post(self, request, format=None):
        serializer = UserForgotPasswordSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            return success_response(message="Reset password link sent on email successfully!", data=[], status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class AdminForgotPasswordView(APIView):
    renderer_classes = [UserRenderer]
    def post(self, request, format=None):
        serializer = AdminForgotPasswordSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            return success_response(message="Reset password link sent on email successfully!", data=[], status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


# User Reset Password
class UserResetPasswordView(APIView):
    renderer_classes = [UserRenderer]
    def post(self, request, format=None):
        serializer = UserResetPasswordSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            return success_response(message="Password reset successfully!", data=[], status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class GetRolesActiveView(APIView):
    renderer_classes = [UserRenderer]
    def get(self, request,format=None):
        all_role_classes = roles.RolesManager.get_roles()

        # Define the roles you want to exclude
        excluded_roles = {
            "Student", "Mentor", "Instructor", "ATPStaff", "ATPAdmin", 
            "CorporateStaff", "CorporateAdmin", "UniversityStaff", 
            "UniversityAdmin", "FinanceUser", "SubAdmin", "Manager"
        }

        # Keep the objects, just filter them
        roles_to_serialize = [
            role for role in all_role_classes 
            if role.get_name() not in excluded_roles
        ]

        # Pass the objects to the serializer
        serializer = RoleSerializer(roles_to_serialize, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class CheckLMSResetPermissionView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, format=None):

        permi = AccountResetPermission.objects.filter(user_id = request.user.id).count()
        if permi > 0 or check_domain_match(request.user.email):
            return success_response(message="", data={"permission_status":True}, status_code=status.HTTP_200_OK)
        return success_response(message="", data={"permission_status":False}, status_code=status.HTTP_200_OK)
    


class UserProfileView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, format=None):
        serializer = UserProfileSerializer(request.user)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class UpdateUserProfileView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        serializer = UpdateUserProfileSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            return success_response(message="Profile Updated Successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateUserProfileImageView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        serializer = UpdateUserProfileImageSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            return success_response(message="Profile Image Updated Successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class RemoveUserProfileImageView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        serializer = RemoveUserProfileSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            return success_response(message="Profile Image Removed Successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateUserBannerImageView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        serializer = UpdateUserBannerImageSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            return success_response(message="Banner Image Updated Successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)