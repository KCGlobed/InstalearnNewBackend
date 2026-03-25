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


]   