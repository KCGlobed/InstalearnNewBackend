from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='login'),
    path('forgot-password', views.forgot_password, name='forgot-password'),
    path('admin-reset-password', views.reset_password, name='admin-reset-password'),
    path('dashboard', views.dashboard, name='dashboard'),
]