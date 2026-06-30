from django.urls import path , include
from questions.views import *

urlpatterns = [

    path('get-mcqs-listing/', MCQsListingView.as_view(), name="mcqs-listing"),
    path('get-mcqs-listing/<int:sid>', MCQsListingView.as_view(), name="mcqs-listing"),
    path('view-mcq-detail/<int:cid>', ViewMCQDetailView.as_view(), name="view-mcq-detail"),
    path('create-mcq/', CreateMCQView.as_view(), name="create-mcq"),
    path('edit-mcq/<int:cid>', EditMCQView.as_view(), name="edit-mcq"),
    path('update-mcq-status/<int:cid>', UpdateMCQStatusView.as_view(), name="update-mcq-status"),
    path('delete-mcq/<int:cid>', DeleteMCQView.as_view(), name="delete-mcq"),
    path('import-mcqs/', ImportMCQsView.as_view(), name="import-mcqs"),
    path('export-mcqs-listing-excel/', ExportMCQsListingExcelView.as_view(), name="export-mcqs-listing-excel"),

    path('get-chapter-quiz-listing/', GetChapterQuizListingView.as_view(), name="get-chapter-quiz-listing"),
    path('view-chapter-quiz-detail/<int:cid>', ViewChapterQuizDetailView.as_view(), name="view-chapter-quiz-detail"),
    path('create-chapter-quiz/', CreateChapterQuizView.as_view(), name="create-chapter-quiz"),
    path('edit-chapter-quiz/<int:cid>', EditChapterQuizView.as_view(), name="edit-chapter-quiz"),
    path('update-chapter-quiz-status/<int:cid>', UpdateChapterQuizStatusView.as_view(), name="update-chapter-quiz-status"),
    path('delete-chapter-quiz/<int:cid>', DeleteChapterQuizView.as_view(), name="delete-chapter-quiz"),
    path('get-mcqs-lists/<int:cid>', GetMCQsListView.as_view(), name="get-mcqs-lists"),
    path('assign-mcqs-chapter-quiz/', AssignMCQChapterQuizView.as_view(), name="assign-mcqs-chapter-quiz"),


    path('get-chapter-quiz-list/<int:cid>', GetChapterQuizListView.as_view(), name="get-chapter-quiz-list"),
    path('start-chapter-quiz/', StartPracticeTestView.as_view(), name="start-chapter-quiz"),

]   