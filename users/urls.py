from django.urls import path , include
from users.views import *
from rest_framework_simplejwt.views import (
    TokenVerifyView,
    TokenRefreshView,
)

urlpatterns = [
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('get-roles/', GetRolesActiveView.as_view(), name="get-roles"),

    path('login/', UserLoginView.as_view(), name="user-login"),
    path('social-login/', UserSocialLoginView.as_view(), name="social-login"),
    path('register/', UserRegistrationView.as_view(), name="user-register"),
    path('verify-otp/', UserVerifyOTPView.as_view(), name="user-verify-OTP"),
    path('resend-verification-otp/', UserSendVerificationOTPView.as_view(), name="user-verification-otp"),
    path('forgot-password/', UserForgotPasswordView.as_view(), name="forgot-password"),
    path('admin-forgot-password/', AdminForgotPasswordView.as_view(), name="forgot-password"),
    path('reset-password/', UserResetPasswordView.as_view(), name="reset-password"),

    path('get-my-permission/', GetMyPermissionListingView.as_view(), name="get-my-permission-listing"),
    path('get-roles-listing/', GetRolesListingView.as_view(), name="get-roles-listing"),
    path('get-roles-permissions/<str:role_name>', GetRolesPermissionView.as_view(), name="get-roles-permission"),
    path('update-roles-permissions/', UpdateRolesPermissionView.as_view(), name="update-roles-permission"),
    path('get-user-permission/<int:id>', GetUserPermissionListingView.as_view(), name="get-user-permission-listing"),
    path('update-user-permission/<int:id>', UpdatetUserPermissionView.as_view(), name="update-user-permission"),
    path('check-lms-reset-permission/', CheckLMSResetPermissionView.as_view(), name="check-lms-reset-permission"),
    
    

    # Admin APIS
    path('get-user-listing/<str:user_type>', GetUserListingView.as_view(), name="get-user-listing"),
    path('create-user/<str:user_type>', CreateUserView.as_view(), name="create-user"),
    path('update-user/<str:user_type>/<int:id>', UpdateUserView.as_view(), name="update-user"),
    path('change-user-status/<str:user_type>/<int:id>', UpdateUserStatustView.as_view(), name="change-user-status"),
    path('admin-update-password/', AdminUpdateStudentPasswordView.as_view(), name="admin-update-password"),
    path('update-instructor-public-profile/<int:id>', UpdateInstructorPublicProfileView.as_view(), name="update-instructor-public-profile"),
    path('delete-user/<str:user_type>/<int:id>', DeleteUserstView.as_view(), name="change-user-status"),


    path('admin-reset-user-devices/<cid>', AdminResetUserDevicesView.as_view(), name="admin-reset-user-devices"),
    
    path('get-student-listing/', GetStudentListingView.as_view(), name="get-student"),
    path('view-student-detail/<int:id>', GetStudentDetailView.as_view(), name="get-student-detail"),
    path('create-student/', CreateStudentView.as_view(), name="create-student"),
    path('update-student/<int:id>', UpdateStudentView.as_view(), name="update-student"),
    path('change-student-status/<int:id>', UpdateStudenStatustView.as_view(), name="change-student-status"),
    
    
]