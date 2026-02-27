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
]