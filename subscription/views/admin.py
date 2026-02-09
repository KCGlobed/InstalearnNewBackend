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
from rest_framework.exceptions import NotFound
from mini_lms.pagination import CustomPageNumberPagination
from rest_framework import filters

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
    



class SubscriptionPlanListingView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "subscription_plan_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['plan_name']
    ordering_fields = ['plan_name', 'created_at', 'id', 'status'] 
    def get(self, request, format=None):
        
        plans = SubscriptionPlans.objects.filter(plan_for = PlanFor.Students)
        
        search_filter = filters.SearchFilter()
        plans = search_filter.filter_queryset(request, plans, self)

        ordering_filter = filters.OrderingFilter()
        plans = ordering_filter.filter_queryset(request, plans, self)

        if not plans.ordered:
            plans = plans.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(plans, request, view=self)
        serializer = SubscriptionPlanDetailSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class SubscriptionPlanDetailView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "subscription_plan_listing",
                            [SuperAdmin]
                        )]
    def get(self, request, cid=None):
        topic = SubscriptionPlans.objects.filter(id=cid, plan_for = PlanFor.Students).first()
        if topic is None:
            raise NotFound("Invalid Plan ID!")
        
        serializer = SubscriptionPlanDetailSerializer(topic)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
        

class CreateSubscriptionPlanView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_subscription_plan",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateSubscriptionPlanSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Plan Created Successfully", data=SubscriptionPlanDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class EditSubscriptionPlanView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_subscription_plan",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        plan = SubscriptionPlans.objects.filter(id=cid).first()
        if plan is None:
            raise NotFound("Invalid Plan ID!")
        
        serializer = EditSubscriptionPlanSerializer(plan, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user= serializer.save()
            return success_response(message="Plan Updated Successfully", data=SubscriptionPlanDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateSubscriptionPlanStatusView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_subscription_plan",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        plan = SubscriptionPlans.objects.filter(id=cid).first()
        if plan is None:
            raise NotFound("Invalid Plan ID!")
        
        serializer = ChangeSubscriptionPlanStatusSerializer(plan, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Plan Status Updated Successfully", data=SubscriptionPlanDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteSubscriptionPlanView(APIView):
    renderer_classes = [SubscriptionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_subscription_plan",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            course = SubscriptionPlans.objects.get(id = cid)
            course.delete()
            return success_response(message="Plan Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except SubscriptionPlans.DoesNotExist:
            return error_response(message="Plan not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)