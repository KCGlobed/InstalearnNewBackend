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

    path('get-job-application-list/', GetJobApplicationsListingView.as_view(), name="get-job-application-list"),
    path('get-job-application-csv-report/', CSVJobApplicationsReportView.as_view(), name="get-job-application-csv-report"),
    path('get-job-application-pdf-report/', PDFJobApplicationsReportView.as_view(), name="get-job-application-pdf-report"),

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

    path('admin-dashboard-counters/', GetAdminDashboardCountersView.as_view(), name="admin-dashboard-counters"),
    path('admin-dashboard-students-graph/<str:interval>', GetAdminDashboardStudentGraphsView.as_view(), name="admin-dashboard-students-graph"),
    path('admin-dashboard-corporate-admin-graph/<str:interval>', GetAdminDashboardCorporateAdminGraphsView.as_view(), name="admin-dashboard-corporate-admin-graph"),
    path('admin-dashboard-students-video-lecture-graph/<str:interval>', GetAdminDashboardStudentVideoLectureGraphsView.as_view(), name="admin-dashboard-students-video-lecture-graph"),
    path('admin-dashboard-students-order-graph/<str:interval>', GetAdminDashboardStudentOrderGraphsView.as_view(), name="admin-dashboard-students-order-graph"),
    path('admin-dashboard-revenue-graph/<str:interval>', GetAdminDashboardRevenueGraphsView.as_view(), name="admin-dashboard-revenue-graph"),

    path('get-corporare-admin-user-listing/', CorporateUserListingView.as_view(), name="get-corporare-admin-user-listing"),
    path('create-corporate-admin-user/', CreateCorporateAdminUserView.as_view(), name="create-corporate-admin-user"),
    path('update-corporare-admin-user-status/<int:cid>', UpdateCorporateAdminUserStatusView.as_view(), name="update-corporare-admin-user-status"),
    path('update-corporare-admin-user/<int:id>', UpdateCorporateAdminUserView.as_view(), name="update-corporare-admin-user"),
    path('get-corporare-admin-user-report-pdf/', ExportPDFCorporateAdminUserListingView.as_view(), name="get-corporare-admin-user-report-pdf"),
    path('get-corporare-admin-user-report-excel/', ExportExcelCorporateAdminUserListingView.as_view(), name="get-corporare-admin-user-report-excel"),
    path('assign-subscription-to-corporare-admin/<int:cid>', AssignSubscriptiontoCorporateAdminUserView.as_view(), name="assign-subscription-to-corporare-admin"),

    path('view-corporare-admin-user/<id>', ViewCorporateAdminUserDetailView.as_view(), name="view-corporare-admin-user"),
    path('get-subscription-listing/', GetSubscriptionListingView.as_view(), name="get-subscription-listing"),
    path('get-subscription-report-pdf/', ExportPDFsubscriptionOrderListingView.as_view(), name="get-subscription-report-pdf"),
    path('get-subscription-report-excel/', ExportExcelsubscriptionOrderListingView.as_view(), name="get-subscription-report-excel"),

    path('view-corporate-user-detail/<sid>', ViewCorporateUserDetailView.as_view(), name="view-corporate-user-detail"),
    path('view-student-video-report/<int:id>/<int:sid>', GetStudentVideoReportView.as_view(), name="view-student-video-report"),
    path('get-student-notes-listing/<int:id>/<int:cid>', GetStudentNotesListingView.as_view(), name="get-student-notes-listing"),
    path('get-attempted-quiz-list/<int:id>/<int:cid>', GetAttemptedTestsListingView.as_view(), name="get-attempted-quiz-list"),

    path('download-student-video-report-pdf/<int:id>/<int:cid>', DownloadStudentVideoReportView.as_view(), name="download-student-video-report"),
    path('download-student-video-report-csv/<int:id>/<int:cid>', DownloadStudentVideoReportCSVView.as_view(), name="download-student-video-report-csv"),

    path('get-notes-listing-report-pdf/<int:id>/<int:cid>', GetNotesListingReportPDFView.as_view(), name="get-notes-listing-report"),
    path('get-notes-listing-report-excel/<int:id>/<int:cid>', GetNotesListingReportExcelView.as_view(), name="get-notes-listing-report-excel"),

    path('get-students-activity-log/<int:id>', GetCorporateStudentsActivityLogListView.as_view(), name="get-students-activity-log"),
    path('export-students-activity-log-pdf/<int:id>', GetCorporateStudentsActivityLogPDFReportView.as_view(), name="export-students-activity-log-pdf"),
    path('export-students-activity-log-excel/<int:id>', GetCorporateStudentsActivityLogExcelReportView.as_view(), name="export-students-activity-log-excel"),
]   