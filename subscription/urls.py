from django.urls import path , include
from subscription.views import *

urlpatterns = [

    path('get-subscription-plan-listing/', SubscriptionPlanListingView.as_view(), name="plan-listing"),
    path('get-subscription-plan-detail/<int:cid>', SubscriptionPlanDetailView.as_view(), name="plan-detail"),
    path('create-subscription-plan/', CreateSubscriptionPlanView.as_view(), name="create-subscription-Plan"),
    path('edit-subscription-plan/<int:cid>', EditSubscriptionPlanView.as_view(), name="edit-subscription-plan"),
    path('update-subscription-plan-status/<int:cid>', UpdateSubscriptionPlanStatusView.as_view(), name="update-plan-status"),
    path('delete-subscription-plan/<int:cid>', DeleteSubscriptionPlanView.as_view(), name="delete-plan"),

    
    path('add-to-cart/', AddtoCartView.as_view(), name="add-to-cart"),
    path('remove-to-cart/<cid>', RemoveCartView.as_view(), name="remove-to-cart"),
    path('view-cart/', ViewCartView.as_view(), name="view-cart"),
    
    path('check-course-cart/', CheckCourseInCartView.as_view(), name="check-course-cart"),
    path('get-payment-gateway/', GetPaymentGatewayView.as_view(), name="get-payment-gateway"),
    path('start-course-payment/', StartPaymentView.as_view(), name="start-course-payment"),
    path('complete-course-payment/', CompletePaymentView.as_view(), name="complete-course-payment"),
    path('webhook-response/', WebhookResponseView.as_view(), name="webhook-response"),
    path('apply-coupon/', ApplyCouponView.as_view(), name='apply-coupon'),

    path('start-subscription/', StartSubscriptionView.as_view(), name="start-subscription"),
    path('complete-subscription/', CompleteSubscriptionView.as_view(), name="complete-subscription"),

    path('get-setting/', GetSettingView.as_view(), name="get-setting"),
    path('update-setting/', UpdateSettingView.as_view(), name="update-setting"),

]