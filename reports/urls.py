from django.urls import path , include
from reports.views import *

urlpatterns = [
    
    path('get-user-report-pdf/<str:user_type>', GetUserReportPDFView.as_view(), name="get-user-report-pdf"),
    path('get-user-report-excel/<str:user_type>', GetUserReportExcelView.as_view(), name="get-user-report-excel"),

]