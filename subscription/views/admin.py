from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from subscription.serializers import *
from subscription.models import *
from courses.models import *
from subscription.renderers import SubscriptionRenderer
from rest_framework.permissions import IsAuthenticated
from mini_lms.permissions import RoleOrPermissionCheck
from mini_lms.utils import *


class GetSettingView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "manage_setting",
                            [SuperAdmin]
                        )]
    def get(self, request, cid=None):
        setting = Settings.objects.all().first()
        if setting is None:
            return success_response(message="Success", data={}, status_code=status.HTTP_200_OK)
        serializer = SettingSerializer(setting)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class UpdateSettingView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "manage_setting",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = UpdateSettingSerializer(data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Setting Updated Successfully", data=SettingSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)