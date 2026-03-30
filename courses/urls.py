from django.urls import path , include
from courses.views import *

urlpatterns = [
    
    # Manage Category SubCategory & Tags APIs
    path('get-tags-listing/', TagsListingView.as_view(), name="tags-listing"), 
    path('create-tags/', CreateTagsView.as_view(), name="create-tags"),
    path('edit-tags/<int:cid>', EditTagsView.as_view(), name="edit-tags"),
    path('update-tags-status/<int:cid>', UpdateTagsStatusView.as_view(), name="update-tags-status"),
    path('delete-tags/<int:cid>', DeleteTagsView.as_view(), name="delete-tags"),

    path('get-category-listing/', CategoryListingView.as_view(), name="category-listing"),
    path('create-category/', CreateCategoryView.as_view(), name="create-category"),
    path('edit-category/<int:cid>', EditCategoryView.as_view(), name="edit-category"),
    path('update-category-status/<int:cid>', UpdateCategoryStatusView.as_view(), name="update-category-status"),
    path('delete-category/<int:cid>', DeleteCategoryView.as_view(), name="delete-category"),

    path('get-subcategory-listing/', SubCategoryListingView.as_view(), name="category-listing"),
    path('get-parent-category/', ParentCategoryListingView.as_view(), name="parent-category-listing"),
    path('create-subcategory/', CreateSubCategoryView.as_view(), name="create-subcategory"),
    path('edit-subcategory/<int:cid>', EditSubCategoryView.as_view(), name="edit-subcategory"),
    path('update-subcategory-status/<int:cid>', UpdateCategoryStatusView.as_view(), name="update-subcategory-status"),
    path('delete-subcategory/<int:cid>', DeleteCategoryView.as_view(), name="delete-subcategory"),

    # Manage Chapters Books APIS
    path('get-book-listing/', ChapterBookListingView.as_view(), name="chapters-listing"),
    path('view-book-detail/<int:cid>', ViewChapterBookView.as_view(), name="view-book-detail"),
    path('create-book/', CreateChapterBookView.as_view(), name="create-book"),
    path('edit-book/<int:cid>', EditChapterBookView.as_view(), name="edit-book"),
    path('update-book-status/<int:cid>', UpdateChapterBookStatusView.as_view(), name="update-book-status"),
    path('delete-book/<int:cid>', DeleteChapterBookView.as_view(), name="delete-book"),

    # Manage Videos APIS
    path('get-videos-listing/', VideosListingView.as_view(), name="Videos-listing"),
    path('view-video-detail/<int:cid>', ViewVideoDetailView.as_view(), name="view-video-detail"),
    path('upload-video/', UploadVideoView.as_view(), name="create-video"),
    path('make-upload-complete/<int:cid>', MarkVideoUploadCompleteView.as_view(), name="make-upload-complete"),
    path('update-video/<int:cid>', UpdateVideoView.as_view(), name="edit-video"),
    path('update-video-status/<int:cid>', UpdateVideoStatusView.as_view(), name="update-video-status"),
    path('delete-video/<int:cid>', DeleteVideoView.as_view(), name="delete-video"),
    

    # Manage Chapters APIS
    path('get-chapter-listing/', ChapterListingView.as_view(), name="chapters-listing"),
    path('view-chapter-detail/<int:cid>', ViewChapterView.as_view(), name="view-chapter-detail"),
    path('create-chapter/', CreateChapterView.as_view(), name="create-chapter"),
    path('assign-chapter-lecture/', AssignChapterLectureView.as_view(), name="assign-chapter-lecture"),
    path('edit-chapter/<int:cid>', EditChapterView.as_view(), name="edit-chapter"),
    path('update-chapter-status/<int:cid>', UpdateChapterStatusView.as_view(), name="update-chapter-status"),
    path('delete-chapter/<int:cid>', DeleteChapterView.as_view(), name="delete-chapter"),

    path('get-chapters-list/', ChapterListView.as_view(), name="chapter-list"),
    path('get-video-list/', GetVideoListView.as_view(), name="get-video-list"),
    path('get-ebook-list/', GetEbookListView.as_view(), name="get-ebook-list"),


    path('get-course-listing/', CourseListingView.as_view(), name="course-listing"),
    path('get-sub-category-listing/', SubCategoryListDetailView.as_view(), name="category-list"),
    path('get-tags-list/', TagsListView.as_view(), name="tags-list"),
    path('view-course-detail/<int:cid>', ViewCourseDetailView.as_view(), name="view-course-detail"),
    path('create-course/', CreateCourseView.as_view(), name="create-course"),
    path('assign-chapter-course/<int:cid>', AssignChapterCourseView.as_view(), name="assign-chapter-course"),
    path('edit-course/<int:cid>', EditCourseView.as_view(), name="edit-course"),
    path('update-course-status/<int:cid>', UpdateCourseStatusView.as_view(), name="update-course-status"),
    path('delete-course/<int:cid>', DeleteCourseView.as_view(), name="delete-course"),

    path('get-courses-sample-video-listing/<int:cid>', GetCourseSampleVideoView.as_view(), name="get-course-sample-video"),
    path('delete-courses-sample-video/<int:cid>', DeleteCourseSampleVideoView.as_view(), name="delete-course-sample-video"),
    path('upload-course-sample-video/', UploadCourseSampleVideoView.as_view(), name="upload-course-sample-video"),

    path('get-instructor-list/', GetInstructorListView.as_view(), name="get-instructor-list"),
    path('get-course-instructor/<int:cid>', GetCourseInstructorsView.as_view(), name="get-course-instructor"),
    path('add-course-instructor/', AddCourseInstructorsView.as_view(), name="add-course-instructor"),
    path('delete-course-instructor/<cid>', DeleteCourseInstructorView.as_view(), name="delete-course-instructor"),

    path('get-subcategory-list/<int:cid>', SubCategoryListView.as_view(), name="subcategory-list"),
    
    path('generate-upload-signed-url/', GenerateUploadSignedUrlView.as_view(), name="generate-upload-signed-url"),
    path('get-trail-course-list/', TrailCourseListView.as_view(), name="get-trail-course-list"),
    path('create-trail-course/', CreateTrailCourseView.as_view(), name="create-trail-course"),
    path('delete-trail-course/<cid>', DeleteTrailCourseView.as_view(), name="delete-trail-course"),

    path('get-course-list/', CourseListView.as_view(), name="get-course-list"),
    path('get-subject-list/<cid>', CourseSubjectListView.as_view(), name="get-subject-list"),
    
    path('get-topics-history/<int:tid>', GetTopicHistoryView.as_view(), name="get-history-topics"),
    path('get-chapters-history/<int:tid>', GetChaptersHistoryView.as_view(), name="get-history-chapters"),
    path('get-course-history/<int:tid>', GetCourseHistoryView.as_view(), name="get-history-course"),
    path('get-ebook-history/<int:tid>', GetEbookHistoryView.as_view(), name="get-history-ebook"),
    path('get-video-history/<int:tid>', GetVideoHistoryView.as_view(), name="get-history-video"),
    

    path('get-related-courses/<int:cid>', GetRelatedCoursesView.as_view(), name="get-related-courses"),
    path('add-related-courses/', AddRelatedCoursesView.as_view(), name="add-related-courses"),
    path('delete-related-course/<cid>', DeleteRelatedCourseView.as_view(), name="delete-related-course"),

    path('get-courses-faqs/<int:cid>', GetCoursesFAQsListingView.as_view(), name="get-courses-faqs"),
    path('add-course-faq/', AddCourseFAQView.as_view(), name="add-courses-faq"),
    path('update-courses-faqs/<int:cid>', UpdateCourseFAQView.as_view(), name="update-courses-faqs"),
    path('update-faq-status/<int:id>', UpdateFAQStatusView.as_view(), name="update-faq-status"),
    path('delete-course-faq/<cid>', DeleteCoursFAQeView.as_view(), name="delete-course-faq"),

    
    #Student APIs
    path('homepage-category-list/', GetHomepageCategoryListing.as_view(), name="homepage-category-listing"),
    path('homepage-tags/', GetHomepageTagsListing.as_view(), name="homepage-tags-listing"),
    path('homepage-tag-wise-courses/<int:id>', GetHomepageTagWiseCoursesListing.as_view(), name="homepage-tag-wise-courses/"),
    path('homepage-recent-courses/', GetHomepageRecentCoursesListing.as_view(), name="homepage-recent-courses/"),

    path('category/listing/', GetCourseCategory.as_view(), name="category-listing"),
    path('sub-category/listing/<int:id>', GetSubCourseCategory.as_view(), name="subcategory-listing"),
    path('course-listing/<int:id>', GetCourseListingCategoryWise.as_view(), name="course-listing"),
    path('learner-course-view/', GetLearnerCourseView.as_view(), name="learner-course-view"),
    path('course-detail/<int:id>', GetCourseDetailView.as_view(), name="course-detail"),
    path('plans-listing/', GetPlansListingView.as_view(), name="plans-listing"),


    path('search/dropdown/', SearchDropdownView.as_view(), name="search-dropdown"),
    path('search/course/', SearchCourseView.as_view(), name="search-course"),
    path('search/category-list/', SearchCategoryListView.as_view(), name="search-category-listing"),
    path('search/filter-count/', SearchFilterCountView.as_view(), name="search-filter-count"),

    path('partner/listing/', GetPartnerListingView.as_view(), name="partner-listing"),
    path('get-testimonial-list/', GetLMSTestimonialView.as_view(), name="get-testimonial-list"),
]