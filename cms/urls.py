from django.urls import path , include
from cms.views import *

urlpatterns = [

    path('get-coupon-list/', CouponListView.as_view(), name="get-coupon-list"), 
    path('get-promotional-banner-listing/', PromotionalBannerListingView.as_view(), name="get-promotional-banner-listing"), 
    path('create-promotional-banner/', CreatePromotionalBannerView.as_view(), name="create-promotional-banner"),
    path('update-promotional-banner/<int:cid>', UpdatePromotionalBannerView.as_view(), name="update-promotional-banner"),
    path('update-promotional-banner-status/<int:cid>', UpdatePromotionalBannerStatusView.as_view(), name="update-promotional-banner-status"),
    path('delete-promotional-banner/<int:cid>', DeletePromotionalBannerView.as_view(), name="delete-promotional-banner"),


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

    
    path('get-testimonials-listing/', TestimonialsListingView.as_view(), name="get-testimonials-listing"), 
    path('view-testimonials-info/<int:cid>', ViewTestimonialsInfoView.as_view(), name="view-testimonials-info"),
    path('create-testimonials/', CreateTestimonialsView.as_view(), name="create-testimonials"),
    path('edit-testimonials/<int:cid>', EditTestimonialsView.as_view(), name="edit-testimonials"),
    path('update-testimonials-status/<int:cid>', UpdateTestimonialsStatusView.as_view(), name="update-testimonials-status"),
    path('delete-testimonials/<int:cid>', DeleteTestimonialsView.as_view(), name="delete-testimonials"),


    path('get-blogs-comments-listing/', BlogsCommentListingView.as_view(), name="get-blogs-comments-listing"),
    path('update-blog-comment-status/<int:cid>', UpdateBlogCommentStatusView.as_view(), name="update-blog-comment-status"),
    path('delete-blog-comment/<int:cid>', DeleteBlogCommentView.as_view(), name="delete-blog-comment"),


    path('get-cms-pages-listing/', CMSPagesListingView.as_view(), name="get-cms-pages-listing"), 
    path('create-update-cms-page/', CreateUpdateCMSPageView.as_view(), name="create-update-cms-page"),
    path('update-cms-page-status/<int:cid>', UpdateCMSPageStatusView.as_view(), name="update-cms-page-status"),

    path('get-faq-topic-listing/', FaqTopicListingView.as_view(), name="get-faq-topic-listing"), 
    path('create-faq-topic/', CreateFaqTopicView.as_view(), name="create-faq-topic"),
    path('edit-faq-topic/<int:cid>', EditFaqTopicView.as_view(), name="edit-faq-topic"),
    path('update-faq-topic-status/<int:cid>', UpdateFaqTopicStatusView.as_view(), name="update-faq-topic-status"),
    path('delete-faq-topic/<int:cid>', DeleteFaqTopicView.as_view(), name="delete-faq-topic"),

    path('get-faq-listing/', FaqListingView.as_view(), name="get-faq-listing"), 
    path('view-faq-info/<int:cid>', ViewFAQInfoView.as_view(), name="view-faq-info"),
    path('get-faq-topic-list/', FaqTopicListView.as_view(), name="get-faq-topic-list"), 
    path('create-faq/', CreateFaqView.as_view(), name="create-faq"),
    path('edit-faq/<int:cid>', EditFaqView.as_view(), name="edit-faq"),
    path('update-faq-status/<int:cid>', UpdateFaqStatusView.as_view(), name="update-faq-status"),
    path('delete-faq/<int:cid>', DeleteFaqView.as_view(), name="delete-faq"),

    path('get-setting/', GetSettingView.as_view(), name="get-setting"),
    path('update-setting/', UpdateSettingView.as_view(), name="update-setting"),
    

    path('get-help-support-topic-listing/', HelpSupportTopicListingView.as_view(), name="get-help-support-topic-listing"), 
    path('create-help-support-topic/', CreateHelpSupportTopicView.as_view(), name="create-help-support-topic"),
    path('edit-help-support-topic/<int:cid>', EditHelpSupportTopicView.as_view(), name="edit-help-support-topic"),
    path('update-help-support-topic-status/<int:cid>', UpdateHelpSupportTopicStatusView.as_view(), name="update-help-support-topic-status"),
    path('delete-help-support-topic/<int:cid>', DeleteHelpSupportTopicView.as_view(), name="delete-help-support-topic"),


    path('get-help-support-topic-list/', HelpSupportTopicListView.as_view(), name="get-help-support-topic-list"),
    path('get-help-support-topic-and-sub-list/', HelpSupportTopicandSubTopicListView.as_view(), name="get-help-support-topic-and-sub-list"), 
    path('get-help-support-subtopic-listing/', HelpSupportSubTopicListingView.as_view(), name="get-help-support-subtopic-listing"), 
    path('create-help-support-subtopic/', CreateHelpSupportSubTopicView.as_view(), name="create-help-support-subtopic"),
    path('edit-help-support-subtopic/<int:cid>', EditHelpSupportSubTopicView.as_view(), name="edit-help-support-subtopic"),
    path('update-help-support-subtopic-status/<int:cid>', UpdateHelpSupportSubTopicStatusView.as_view(), name="update-help-support-subtopic-status"),
    path('delete-help-support-subtopic/<int:cid>', DeleteHelpSupportSubTopicView.as_view(), name="delete-help-support-subtopic"),

    path('get-help-support-subtopic-list/<int:cid>', HelpSupportSubTopicListView.as_view(), name="get-help-support-subtopic-list"), 


    path('get-help-support-article-listing/', HelpSupportArticleListingView.as_view(), name="get-help-support-article-listing"), 
    path('create-help-support-article/', CreateHelpSupportArticleView.as_view(), name="create-help-support-article"),
    path('edit-help-support-article/<int:cid>', EditHelpSupportArticleView.as_view(), name="edit-help-support-article"),
    path('update-help-support-article-status/<int:cid>', UpdateHelpSupportArticleStatusView.as_view(), name="update-help-support-article-status"),
    path('delete-help-support-article/<int:cid>', DeleteHelpSupportArticleView.as_view(), name="delete-help-support-article"),

    #Landing Page APIs
    path('get-homepage-faq-topic-list/', FaqTopicListView.as_view(), name="get-homepage-faq-topic-list"),
    path('get-homepage-faq-list/<int:cid>', FaqsListView.as_view(), name="get-homepage-faq-list"), 

    path('contact-us/', ContactUsView.as_view(), name="contact-us"),

    path('get-blog-categories/', BlogCategoriesView.as_view(), name="get-blog-categories"), 
    path('get-category-wise-blogs/<int:cid>', BlogCategoryWiseView.as_view(), name="get-category-wise-blogs"),
    path('get-all-blogs/', BlogListingView.as_view(), name="get-all-blogs"), 
    path('view-blog-detail/<str:slug>', ViewBlogDetailView.as_view(), name="view-blog-detail"),
    path('get-featured-blogs/', GetFeaturedBlogListingView.as_view(), name="get-featured-blogs"), 
    path('view-blog-comments/<int:id>', ViewBlogCommentsView.as_view(), name="view-blog-comment"),
    path('add-blog-comment/', AddBlogCommentView.as_view(), name="add-blog-comment"),
    path('view-cms-page/<str:page_type>', ViewCMSPageView.as_view(), name="view-cms-page"),
    
    path('get-user-testimonials/<int:testimonials_type>', ViewTestimonialsListView.as_view(), name="get-user-testimonials"),

    path('get-help-support-topics/', HelpSupportTopicView.as_view(), name="get-help-support-topic"), 
    path('get-help-support-subtopics/<str:slug>', HelpSupportSubTopicView.as_view(), name="get-help-support-subtopic"),
    path('get-help-support-articles/<str:slug>', HelpSupportArticlesView.as_view(), name="get-help-support-articles"), 
    path('get-help-support-article-detail/<str:slug>', HelpSupportArticleDetailView.as_view(), name="get-help-support-detail"),
    path('submit-application-form/', SubmitApplicationFormView.as_view(), name="submit-application-form"), 

    path('get-promotional-banner/', PromotionalBannerListView.as_view(), name="get-promotional-banner"), 

    path('get-community-category-listing/', CommunityCategoryListingView.as_view(), name="get-community-category-listing"), 
    path('create-community-category/', CreateCommunityCategoryView.as_view(), name="create-community-category"),
    path('edit-community-category/<int:cid>', EditCommunityCategoryView.as_view(), name="edit-community-category"),
    path('update-community-category-status/<int:cid>', UpdateCommunityCategoryStatusView.as_view(), name="update-community-category-status"),
    path('delete-community-category/<int:cid>', DeleteCommunityCategoryView.as_view(), name="delete-community-category"),


    path('get-community-post-listing/', CommunitPostListingView.as_view(), name="get-community-post-listing"), 
    path('get-community-post-detail/<int:id>', ViewCommunityPostDetailView.as_view(), name="view-community-post-detail"),
    path('create-community-post/', CreateCommunitPostView.as_view(), name="create-community-post"),
    path('edit-community-post/<int:cid>', EditCommunitPostView.as_view(), name="edit-community-post"),
    path('update-community-post-status/<int:cid>', UpdateCommunitPostStatusView.as_view(), name="update-community-post-status"),
    path('delete-community-post/<int:cid>', DeleteCommunitPostView.as_view(), name="delete-community-post"),

    path('get-community-category-list/', CommunityCategoryListView.as_view(), name="get-community-category-list"),
    path('get-community-post-list/<str:slug>', CommunityPostListView.as_view(), name="get-community-post-list"), 
    path('view-community-post-detail/<str:slug>', ViewCommunityPostDetailView.as_view(), name="view-community-post-detail"),
    path('view-community-post-comments/<str:slug>', ViewCommunityPostCommentsView.as_view(), name="view-community-post-comment"),
    path('add-community-post-comment/', AddCommunityPostCommentView.as_view(), name="add-community-post-comment"),
    path('community/like/toggle/', ToggleLikeView.as_view(), name='toggle-like'),

    path('get-community-post-comments-listing/', CommunityPostCommentListingView.as_view(), name="get-community-post-comments-listing"),
    path('update-community-post-comment-status/<int:cid>', UpdateCommunityPostCommentStatusView.as_view(), name="update-community-post-comment-status"),
    path('delete-community-post-comment/<int:cid>', DeleteCommunityPostCommentView.as_view(), name="delete-community-post-comment"),

    path('submit-partner-requests/', SubmitPartnerRequestsView.as_view(), name="submit-partner-requests"), 

]   