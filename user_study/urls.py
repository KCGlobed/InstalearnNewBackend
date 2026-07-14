from django.urls import path , include
from user_study.views import *

urlpatterns = [
    path('purchased-courses/', PurchasedCoursesView.as_view(), name="purchased-courses"),
    path('mark-course-started/', MarkCourseStartedView.as_view(), name="mark-course-started"),
    path('get-course-progress/<int:id>', GetCourseProgressView.as_view(), name="get-course-progress"),
    path('dashboard-chapters/<int:id>', DashboardCourseChaptersView.as_view(), name="dashboard-chapters"),
    path('chapter-lectures/<int:id>', DashboardChapterLecturesView.as_view(), name="chapter-lectures"),
    path('watch-video/', WatchVideoView.as_view(), name="watch-video"),
    path('get-book-signed-url/<int:cid>', ViewBookSignedUrlView.as_view(), name="get-book-signed-url"),

    
    path('get-video-report/<int:id>', GetVideoReportView.as_view(), name="dashboard-chapters"),
    path('download-video-report/<int:cid>', DownloadChapterVideoReportView.as_view(), name="download-videos-report"),
    path('download-video-report-csv/<int:cid>', DownloadChapterVideoReportCSVView.as_view(), name="download-videos-report"),
    
    path('performance-report/<int:id>', PerformaceReportView.as_view(), name="performance-report"),
    
    path('create-note/', CreateNoteView.as_view(), name="create-note"),
    path('update-note/<int:cid>', EditNoteView.as_view(), name="edit-note"),
    path('get-user-notes/<int:cid>', GetUserNotesView.as_view(), name="get-user-notes"),
    path('get-lecture-notes/<int:cid>', GetLectureNotesView.as_view(), name="get-lecture-notes"),
    path('delete-note/<int:cid>', DeleteNoteView.as_view(), name="delete-my-list"),

    path('get-course-certificate/<int:id>', GetCourseCertificateView.as_view(), name="get-course-certificate"),

    path('mylist/create/', CreateMyListView.as_view(), name="create-my-list"),
    path('mylist/update/', UpdateMyListView.as_view(), name="create-my-list"),
    path('mylist/get-my-list/', GetMyListView.as_view(), name="get-my-list"),
    path('mylist/delete/<cid>', DeleteMyListView.as_view(), name="delete-my-list"),
    
    path('add-review-rating/', AddReviewAndRatingView.as_view(), name="add-review-rating"),
    path('get-course-review/<int:cid>', GetCourseReviewView.as_view(), name="get-course-review"),
    path('update-review-rating/<int:cid>', UpdateCourseReviewRatingView.as_view(), name="edit-note"),
    
    path('get-user-wishlist/', GetUserWishlistView.as_view(), name="user-wishlist"),
    path('check-course-wishlist/', CheckCourseInWishlistView.as_view(), name="check-course-wishlist"),
    path('update-wishlist/', AddUserWishlistView.as_view(), name="add-user-wishlist"),

    
    path('get-user-notification-setting/', GetUserNotificationSettingView.as_view(), name="get-user-notification-setting"),
    path('update-user-notification-setting/', UpdateUserNotificationSettingView.as_view(), name="update-user-notification-setting"),

    path('get-user-notification/', GetUserNotificationView.as_view(), name="user-notification"),
    path('get-all-notification/', GetAllNotificationView.as_view(), name="all-notification"),
    path('change-notification-status/', ChangeNotificationStatusView.as_view(), name="change-notification-status"),


    path('reminder/create/', CreateRemindersView.as_view(), name="create-reminder"),
    path('reminder/update/', UpdateRemindersView.as_view(), name="update-reminder"),
    path('reminder/get-reminders/', GetRemindersView.as_view(), name="get-reminder"),
    path('reminder/delete/<cid>', DeleteRemindersView.as_view(), name="delete-reminder"),

    path('get-dashboard-counters/', GetDashboardCountersView.as_view(), name="get-dashboard-counters"),
]