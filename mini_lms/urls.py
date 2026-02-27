from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/',include('users.urls')),
    path('api/course/',include('courses.urls')),
    path('api/subscription/',include('subscription.urls')),
    path('api/user_study/',include('user_study.urls')),

    #admin panel urls
    path('', include('adminpanel.authentication.urls')),
    path('', include('adminpanel.course_app.urls')),
]
