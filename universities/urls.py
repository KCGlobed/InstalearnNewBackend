from django.urls import path , include
from universities.views import *


urlpatterns = [
   path('submit-university-requests/', SubmitUniversityRequestsView.as_view(), name="submit-university-requests"), 
   path('get-institution-types/', InstitutionTypeChoicesView.as_view(), name='get-institution-type'),
   path('get-job-roles/', JobRolesChoicesView.as_view(), name='get-job-role'),
   path('get-department-types/', DepartmentTypeChoicesView.as_view(), name='get-department-type'),


   path('get-university-requests-listing/', GetUniversityRequestsListingView.as_view(), name="university-requests-listing"),
]