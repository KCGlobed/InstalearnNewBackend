from django.urls import path , include
from subscription.views import *

urlpatterns = [
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

]