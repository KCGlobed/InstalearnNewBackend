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


    path('get-trail-user-listing/', TrailUserListingView.as_view(), name="trail-user-listing"),
    path('get-trail-user-report-pdf/', ExportPDFTrailUserListingView.as_view(), name="get-trail-user-report-pdf"),
    path('get-trail-user-report-excel/', ExportExcelTrailUserListingView.as_view(), name="get-trail-user-report-excel"),

    path('get-student-registration-report-pdf/', GetStudentRegistrationReportPDFView.as_view(), name="get-student-registration-report-pdf"),
    path('get-student-registration-report-excel/', GetStudentRegistrationReportExcelView.as_view(), name="get-student-registration-report-excel"),

    path('get-active-order-listing/', ActiveOrderListingView.as_view(), name="get-order-listing"),
    path('get-active-report-pdf/', ExportPDFActiveOrderListingView.as_view(), name="get-active-report-pdf"),
    path('get-active-report-excel/', ExportExcelActiveOrderListingView.as_view(), name="get-active-report-excel"),

    path('get-contact-us-list/', GetContactUSView.as_view(), name="get-contact-us-list"),
    path('get-contact-us-csv-report/', CSVContactUsReportView.as_view(), name="get-contact-us-csv-report"),
    path('get-contact-us-pdf-report/', PDFContactUsReportView.as_view(), name="get-contact-us-pdf-report"),

    path('get-student-performance-report/', GetStudentPerformanceReportView.as_view(), name="get-student-performance-report"),
    path('get-student-performance-report-pdf/', GetStudentPerformanceReportPDFView.as_view(), name="get-student-performance-report-pdf"),
    path('get-student-performance-report-excel/', GetStudentPerformanceReportExcelView.as_view(), name="get-student-performance-report-excel"),

    path('view-admin-user-notes-report/<uid>/<sid>', GetAdminUserNoteReportView.as_view(), name="view-admin-user-notes-report"),
    path('get-student-notes-listing/', GetStudentNotesReportlistingView.as_view(), name="get-student-notes-listing"),
    path('get-admin-notes-listing-report-pdf/', GetAdminNotesListingReportPDFView.as_view(), name="get-admin-notes-listing-report"),
    path('get-admin-notes-listing-report-excel/', GetAdminNotesListingReportExcelView.as_view(), name="get-admin-notes-listing-report-excel"),

    path('get-student-login-activity/<uid>', GetStudentActivityReportView.as_view(), name="get-student-login-activity"),
    path('get-student-login-activity-pdf-report/<uid>', GetStudentActivityPDFReportView.as_view(), name="get-student-login-activity-pdf-report"),
    path('get-student-login-activity-excel-report/<uid>', GetStudentActivityExcelReportView.as_view(), name="get-student-login-activity-excel-report"),
]