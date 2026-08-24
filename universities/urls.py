from django.urls import path , include
from universities.views import *


urlpatterns = [
   path('submit-university-requests/', SubmitUniversityRequestsView.as_view(), name="submit-university-requests"), 
   path('get-institution-types/', InstitutionTypeChoicesView.as_view(), name='get-institution-type'),
   path('get-job-roles/', JobRolesChoicesView.as_view(), name='get-job-role'),
   path('get-department-types/', DepartmentTypeChoicesView.as_view(), name='get-department-type'),


   path('get-university-requests-listing/', GetUniversityRequestsListingView.as_view(), name="university-requests-listing"),
   path('view-university-requests-detail/<sid>', ViewUniversityRequestDetailView.as_view(), name="view-university-requests-detail"),
   path('update-university-requests-status/<int:cid>', UpdateUniversityRequestStatusView.as_view(), name="update-university-requests-status"),
   path('approve-reject-university-requests-status/<int:cid>', ApproveRejectUniversityRequestStatusView.as_view(), name="approve-reject-university-requests-status"),
   path('assign-subscription-to-university/<int:cid>', AssignSubscriptiontoCorporateAdminUserView.as_view(), name="assign-subscription-to-university"),

   path('get-university-requests-csv-report/', CSVUniversityRequestsReportView.as_view(), name="get-university-requests-csv-report"),
   path('get-university-requests-pdf-report/', PDFUniversityRequestsReportView.as_view(), name="get-university-requests-pdf-report"),

   path('import-students/', ImportUniversityStudentsView.as_view(), name='import-users'),
   path('create-university-student/', CreateStudentView.as_view(), name="create-student"),

]