from django.urls import path , include
from cms.views import *

urlpatterns = [

    path('get-faq-topic-listing/', FaqTopicListingView.as_view(), name="get-faq-topic-listing"), 
    path('create-faq-topic/', CreateFaqTopicView.as_view(), name="create-faq-topic"),
    path('edit-faq-topic/<int:cid>', EditFaqTopicView.as_view(), name="edit-faq-topic"),
    path('update-faq-topic-status/<int:cid>', UpdateFaqTopicStatusView.as_view(), name="update-faq-topic-status"),
    path('delete-faq-topic/<int:cid>', DeleteFaqTopicView.as_view(), name="delete-faq-topic"),

    path('get-faq-listing/', FaqListingView.as_view(), name="get-faq-listing"), 
    path('create-faq/', CreateFaqView.as_view(), name="create-faq"),
    path('edit-faq/<int:cid>', EditFaqView.as_view(), name="edit-faq"),
    path('update-faq-status/<int:cid>', UpdateFaqStatusView.as_view(), name="update-faq-status"),
    path('delete-faq/<int:cid>', DeleteFaqView.as_view(), name="delete-faq"),


    path('get-homepage-faq-topic-list/', FaqTopicListView.as_view(), name="get-homepage-faq-topic-list"),
    path('get-homepage-faq-list/<int:cid>', FaqsListView.as_view(), name="get-homepage-faq-list"), 

]   