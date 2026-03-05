from django.urls import path
from . import views

urlpatterns = [
    path('admin-manage-category', views.manage_category, name='admin-manage-category'),
    path('admin-get-category-listing', views.get_category_listing, name='admin-get-category-listing'),
    path('admin-manage-subcategory', views.manage_subcategory, name='admin-manage-subcategory'),
    path('admin-get-subcategory-listing', views.get_subcategory_listing, name='admin-get-subcategory-listing'),
    path('admin-delete-category/<int:pk>', views.delete_category, name='admin-delete-category'),
    path('admin-create-new-category', views.create_category, name='admin-create-category'),
    path('admin-create-new-category/<int:id>', views.create_category, name='admin-create-category'),
    path('admin-create-new-subcategory', views.create_subcategory, name='admin-create-subcategory'),
    path('admin-create-new-subcategory/<int:id>', views.create_subcategory, name='admin-create-subcategory'),
    path('admin-category-update-status', views.update_category_status, name='admin-update-category-status'),

    path('admin-manage-tags', views.manage_tags, name='admin-manage-tags'),
    path('admin-get-tags-listing', views.get_tags_listing, name='admin-get-tags-listing'),
    path('admin-delete-tags/<int:pk>', views.delete_tags, name='admin-delete-tags'),
    path('admin-create-new-tags', views.create_tags, name='admin-create-tags'),
    path('admin-create-new-tags/<int:id>', views.create_tags, name='admin-create-tags'),
    path('admin-tags-update-status', views.update_tags_status, name='admin-update-tags-status'),

    path('admin-manage-ebooks', views.manage_ebooks, name='admin-manage-ebooks'),
    path('admin-get-ebooks-listing', views.get_ebooks_listing, name='admin-get-ebooks-listing'),
    path('admin-create-new-ebooks', views.create_ebooks, name='admin-create-ebooks'),
    path('admin-create-new-ebooks/<int:id>', views.create_ebooks, name='admin-create-ebooks'),
    path('admin-delete-ebooks/<int:pk>', views.delete_ebooks, name='admin-delete-ebooks'),
    path('admin-ebook-update-status', views.update_ebooks_status, name='admin-update-ebook-status'),

    path('admin-manage-videos', views.manage_videos, name='admin-manage-videos'),
    path('admin-get-videos-listing', views.get_videos_listing, name='admin-get-videos-listing'),
    path('admin-create-new-videos', views.create_videos, name='admin-create-videos'),
    path('admin-get-video-signed-url/', views.get_signed_url, name='admin-get-signed-url'),
    path('admin-create-new-videos/<int:id>', views.create_videos, name='admin-create-videos'),

]