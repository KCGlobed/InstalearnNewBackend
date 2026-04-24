from django.urls import path , include
from user_study.views import *

urlpatterns = [
    path('purchased-courses/', PurchasedCoursesView.as_view(), name="purchased-courses"),
    path('dashboard-chapters/<int:id>', DashboardCourseChaptersView.as_view(), name="dashboard-chapters"),
    path('chapter-lectures/<int:id>', DashboardChapterLecturesView.as_view(), name="chapter-lectures"),
    path('watch-video/', WatchVideoView.as_view(), name="watch-video"),


    path('download-video-report/<cid>', DownloadChapterVideoReportView.as_view(), name="download-videos-report"),
    path('download-video-report-csv/<cid>', DownloadChapterVideoReportCSVView.as_view(), name="download-videos-report"),
    
    path('performance-report/<int:id>', PerformaceReportView.as_view(), name="performance-report"),
    
    path('create-note/', CreateNoteView.as_view(), name="create-note"),
    path('update-note/<cid>', EditNoteView.as_view(), name="edit-note"),
    path('get-user-notes/<cid>', GetUserNotesView.as_view(), name="get-user-notes"),
    path('get-course-certificate/<id>', GetCourseCertificateView.as_view(), name="get-course-certificate"),

    path('mylist/create/', CreateMyListView.as_view(), name="create-my-list"),
    path('mylist/update/', UpdateMyListView.as_view(), name="create-my-list"),
    path('mylist/get-my-list/', GetMyListView.as_view(), name="get-my-list"),
    path('mylist/delete/<cid>', DeleteMyListView.as_view(), name="delete-my-list"),
    path('review/add/', AddReviewAndRatingView.as_view(), name="add-review-rating"),


    path('get-user-wishlist/', GetUserWishlistView.as_view(), name="user-wishlist"),
    path('update-wishlist/', AddUserWishlistView.as_view(), name="add-user-wishlist"),

    
]