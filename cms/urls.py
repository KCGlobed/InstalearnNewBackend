from django.urls import path , include
from cms.views import *

urlpatterns = [

    path('get-blogs-listing/', BlogsListingView.as_view(), name="get-blogs-listing"), 
    path('view-blog-info/<int:cid>', ViewBlogInfoView.as_view(), name="view-blog-info"),
    path('create-blog/', CreateBlogView.as_view(), name="create-blog"),
    path('edit-blog/<int:cid>', EditBlogView.as_view(), name="edit-blog"),
    path('update-blog-status/<int:cid>', UpdateBlogStatusView.as_view(), name="update-blog-status"),
    path('update-blog-feature-status/<int:cid>', UpdateBlogFeatureStatusView.as_view(), name="update-blog-feature-status"),
    path('delete-blog/<int:cid>', DeleteBlogView.as_view(), name="delete-blog"),


    path('get-blog-category-listing/', BlogCategoryListingView.as_view(), name="get-blog-category-listing"), 
    path('create-blog-category/', CreateBlogCategoryView.as_view(), name="create-blog-category"),
    path('edit-blog-category/<int:cid>', EditBlogCategoryView.as_view(), name="edit-blog-category"),
    path('update-blog-category-status/<int:cid>', UpdateBlogCategoryStatusView.as_view(), name="update-blog-category-status"),
    path('delete-blog-category/<int:cid>', DeleteBlogCategoryView.as_view(), name="delete-blog-category"),


    path('get-faq-topic-listing/', FaqTopicListingView.as_view(), name="get-faq-topic-listing"), 
    path('create-faq-topic/', CreateFaqTopicView.as_view(), name="create-faq-topic"),
    path('edit-faq-topic/<int:cid>', EditFaqTopicView.as_view(), name="edit-faq-topic"),
    path('update-faq-topic-status/<int:cid>', UpdateFaqTopicStatusView.as_view(), name="update-faq-topic-status"),
    path('delete-faq-topic/<int:cid>', DeleteFaqTopicView.as_view(), name="delete-faq-topic"),

    path('get-faq-listing/', FaqListingView.as_view(), name="get-faq-listing"), 
    path('get-faq-topic-list/', FaqTopicListView.as_view(), name="get-faq-topic-list"), 
    path('create-faq/', CreateFaqView.as_view(), name="create-faq"),
    path('edit-faq/<int:cid>', EditFaqView.as_view(), name="edit-faq"),
    path('update-faq-status/<int:cid>', UpdateFaqStatusView.as_view(), name="update-faq-status"),
    path('delete-faq/<int:cid>', DeleteFaqView.as_view(), name="delete-faq"),

    path('get-setting/', GetSettingView.as_view(), name="get-setting"),
    path('update-setting/', UpdateSettingView.as_view(), name="update-setting"),
    

    path('get-homepage-faq-topic-list/', FaqTopicListView.as_view(), name="get-homepage-faq-topic-list"),
    path('get-homepage-faq-list/<int:cid>', FaqsListView.as_view(), name="get-homepage-faq-list"), 

    path('contact-us/', ContactUsView.as_view(), name="contact-us"),
]   