from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from subscription.models import *
from mini_lms.utils import *

def subscription_check(view_func):
    @wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return error_response(message="failed", data = {}, status_code=status.HTTP_400_BAD_REQUEST)

        active_subscription = Order.objects.filter(user = request.user,subscription_status = OrderStatus.Active).order_by("-id").first()
        if active_subscription is None:
            return success_response(message="No subscription found for this user.", data={}, status_code=status.HTTP_200_OK)
            
        return view_func(self, request, *args, **kwargs)
    return _wrapped_view


def auto_logout(view_func):
    @wraps(view_func)
    def _wrapped_view(self, *args, **kwargs):
        authHeader = self.request.META.get('HTTP_AUTHORIZATION')
        token = authHeader.replace('Bearer ','')
        setting = Settings.objects.all().first()
        if setting.auto_logout_restriction:
            user_session = UserSession.objects.filter(user_id = self.request.user).first()
            if user_session is not None:
                if user_session.token != token:
                    return error_response(message="New Login Detected on other system", data={'auto_logout' : True}, status_code=status.HTTP_400_BAD_REQUEST)
        
        return view_func(self.request, *args, **kwargs)
    return _wrapped_view

