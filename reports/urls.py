from django.urls import path , include
from reports.views import *

urlpatterns = [
    
    path('get-user-report-pdf/<str:user_type>', GetUserReportPDFView.as_view(), name="get-user-report-pdf"),
    path('get-user-report-excel/<str:user_type>', GetUserReportExcelView.as_view(), name="get-user-report-excel"),

    path('get-video-report/<int:uid>/<int:cid>', GetVideoReportView.as_view(), name="dashboard-chapters"),
    path('download-video-report/<int:uid>/<int:cid>', DownloadChapterVideoReportView.as_view(), name="download-videos-report"),
    path('download-video-report-csv/<int:uid>/<int:cid>', DownloadChapterVideoReportCSVView.as_view(), name="download-videos-report"),

    path('get-student-access-lock-report/', GetStudentAccessLockReportView.as_view(), name="get-student-access-lock-report"),
    path('get-student-access-lock-report-pdf/', GetStudentAccessLockReportPDFView.as_view(), name="get-student-access-lock-report-pdf"),
    path('get-student-access-lock-report-excel/', GetStudentAccessLockReportExcelView.as_view(), name="get-student-access-lock-report-excel"),
    path('update-student-account-status/<int:cid>', UpdateStudentAccountStatusView.as_view(), name="update-student-account-status"),
]