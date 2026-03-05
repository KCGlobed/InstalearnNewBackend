from django.shortcuts import render, redirect, get_object_or_404
from mini_lms.roles import *
from users.models import *
from courses.models import *
from mini_lms.utils import *
from django.contrib.auth.decorators import login_required
from django.utils.encoding import smart_str, force_bytes
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import os
from django.conf import settings
import json
from google.cloud import storage
from google.oauth2 import service_account
import calendar
import time


@login_required(login_url='/')
def manage_category(request):
    return render(request, 'category.html', locals())


@login_required(login_url='/')
def get_category_listing(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    
    column_mapping = {
        '0': 'id',
        '1': 'name',
        '2': 'created_at', 
        '3': 'status',
    }
    
    order_index = request.GET.get('order[0][column]', '0')
    order_dir = request.GET.get('order[0][dir]', 'desc')
    
    sort_field = column_mapping.get(order_index, 'id')
    
    if order_dir == 'desc':
        sort_field = '-' + sort_field

    queryset = Categories.objects.filter(parent__isnull = True)

    search_value = request.GET.get('search[value]', None)
    if search_value:
        # Filter by name or description
        queryset = queryset.filter(
            name__icontains=search_value
        ) | queryset.filter(
            description__icontains=search_value
        )


    queryset = queryset.order_by(sort_field)

    total_records = queryset.count()
    data_slice = queryset[start:start + length]

    data = []
    for obj in data_slice:
        data.append({
            "id": obj.id,
            "name": obj.name or "N/A",
            "date": obj.created_at.strftime("%Y-%m-%d, %I:%M%p"),
            "status": obj.status, # Sending as boolean to handle in JS
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records, # Update this if you add search functionality
        "data": data,
    })


@login_required(login_url='/')
def get_subcategory_listing(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    
    column_mapping = {
        '0': 'id',
        '1': 'name',
        '2': 'created_at', 
        '3': 'status',
    }
    
    order_index = request.GET.get('order[0][column]', '0')
    order_dir = request.GET.get('order[0][dir]', 'desc')
    
    sort_field = column_mapping.get(order_index, 'id')
    
    if order_dir == 'desc':
        sort_field = '-' + sort_field

    queryset = Categories.objects.filter(parent__isnull = False)

    search_value = request.GET.get('search[value]', None)
    if search_value:
        # Filter by name or description
        queryset = queryset.filter(
            name__icontains=search_value
        ) | queryset.filter(
            parent__name__icontains=search_value
        )

        
    queryset = queryset.order_by(sort_field)

    total_records = queryset.count()
    data_slice = queryset[start:start + length]

    data = []
    for obj in data_slice:
        print(obj.parent)
        data.append({
            "id": obj.id,
            "name": obj.name or "N/A",
            "parent": obj.parent.name or "N/A",
            "date": obj.created_at.strftime("%Y-%m-%d, %I:%M%p"),
            "status": obj.status, # Sending as boolean to handle in JS
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records, # Update this if you add search functionality
        "data": data,
    })


@login_required(login_url='/')
def manage_subcategory(request):
    return render(request, 'subcategory.html', locals())


@login_required(login_url='/')
def create_category(request, id=None):
    if id is not None:
        category_detail = Categories.objects.filter(id = id).first()
    if request.POST:
        request.session['data'] = request.POST
        if request.POST.get('id') != "":
            category = Categories.objects.filter(id=request.POST.get('id')).first()
            category.name = request.POST.get('name')
            category.description = request.POST.get('description')
            category.save()
            return JsonResponse({
                "status": "success",
                "message": "Category updated successfully"
            })
        
        else:
            category = Categories(
                name = request.POST.get('name'),
                description = request.POST.get('description'),
                status = True
            )
            category.save()

            return JsonResponse({
                "status": "success",
                "message": "Category created successfully"
            })
    
    return render(request, 'create_category.html', locals())


@require_POST
def delete_category(request, pk):
    try:
        category = Categories.objects.get(pk=pk)
        category.delete()
        return JsonResponse({'status': 'success', 'message': 'Deleted successfully'})
    except Categories.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Record not found'}, status=404)
    

@require_POST
def update_category_status(request):
    category_id = request.POST.get('id')
    new_status = request.POST.get('status') == 'true'

    try:
        # Fetch the object
        category = Categories.objects.get(id=category_id)
        category.status = new_status
        category.save()

        return JsonResponse({
            'status': 'success',
            'message': f'Category is now {"Active" if new_status else "Inactive"}.'
        })
    except Categories.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Category not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    

@login_required(login_url='/')
def create_subcategory(request, id=None):

    parent_category_listing = Categories.objects.filter(parent__isnull = True)
    if id is not None:
        category_detail = Categories.objects.filter(id = id).first()

    if request.POST:
        request.session['data'] = request.POST
        if request.POST.get('id') != "":
            category = Categories.objects.filter(id=request.POST.get('id')).first()
            category.name = request.POST.get('name')
            category.description = request.POST.get('description')
            category.parent = Categories.objects.filter(id=request.POST.get('parent')).first()
            category.save()
            return JsonResponse({
                "status": "success",
                "message": "SubCategory updated successfully"
            })
        
        else:
            category = Categories(
                name = request.POST.get('name'),
                description = request.POST.get('description'),
                parent = Categories.objects.filter(id=request.POST.get('parent')).first(),
                status = True
            )
            category.save()

            return JsonResponse({
                "status": "success",
                "message": "SubCategory created successfully"
            })

    return render(request, 'create_subcategory.html', locals())


@login_required(login_url='/')
def manage_tags(request):
    return render(request, 'tags.html', locals())


@login_required(login_url='/')
def get_tags_listing(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    
    column_mapping = {
        '0': 'id',
        '1': 'name',
        '2': 'created_at', 
        '3': 'status',
    }
    
    order_index = request.GET.get('order[0][column]', '0')
    order_dir = request.GET.get('order[0][dir]', 'desc')
    
    sort_field = column_mapping.get(order_index, 'id')
    
    if order_dir == 'desc':
        sort_field = '-' + sort_field

    queryset = Tags.objects.all()

    search_value = request.GET.get('search[value]', None)
    if search_value:
        # Filter by name or description
        queryset = queryset.filter(
            name__icontains=search_value
        ) | queryset.filter(
            description__icontains=search_value
        )


    queryset = queryset.order_by(sort_field)

    total_records = queryset.count()
    data_slice = queryset[start:start + length]

    data = []
    for obj in data_slice:
        data.append({
            "id": obj.id,
            "name": obj.name or "N/A",
            "date": obj.created_at.strftime("%Y-%m-%d, %I:%M%p"),
            "status": obj.status, # Sending as boolean to handle in JS
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records, # Update this if you add search functionality
        "data": data,
    })


@login_required(login_url='/')
def create_tags(request, id=None):
    if id is not None:
        tag_detail = Tags.objects.filter(id = id).first()

    if request.POST:
        request.session['data'] = request.POST
        if request.POST.get('id') != "":
            tag = Tags.objects.filter(id=request.POST.get('id')).first()
            tag.name = request.POST.get('name')
            tag.save()
            return JsonResponse({
                "status": "success",
                "message": "Tag updated successfully"
            })
        
        else:
            tag = Tags(
                name = request.POST.get('name'),
                status = True
            )
            tag.save()

            return JsonResponse({
                "status": "success",
                "message": "Tag created successfully"
            })
    
    return render(request, 'create_tags.html', locals())


@require_POST
def delete_tags(request, pk):
    try:
        category = Tags.objects.get(pk=pk)
        category.delete()
        return JsonResponse({'status': 'success', 'message': 'Deleted successfully'})
    except Tags.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Record not found'}, status=404)
    

@require_POST
def update_tags_status(request):
    category_id = request.POST.get('id')
    new_status = request.POST.get('status') == 'true'

    try:
        # Fetch the object
        category = Tags.objects.get(id=category_id)
        category.status = new_status
        category.save()

        return JsonResponse({
            'status': 'success',
            'message': f'Tag is now {"Active" if new_status else "Inactive"}.'
        })
    except Tags.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Tag not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    

@login_required(login_url='/')
def manage_ebooks(request):
    return render(request, 'ebooks.html', locals())


@login_required(login_url='/')
def get_ebooks_listing(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    
    column_mapping = {
        '0': 'id',
        '1': 'name',
        '2': 'created_at', 
        '3': 'status',
    }
    
    order_index = request.GET.get('order[0][column]', '0')
    order_dir = request.GET.get('order[0][dir]', 'desc')
    
    sort_field = column_mapping.get(order_index, 'id')
    
    if order_dir == 'desc':
        sort_field = '-' + sort_field

    queryset = ChapterBooks.objects.all()

    search_value = request.GET.get('search[value]', None)
    if search_value:
        # Filter by name or description
        queryset = queryset.filter(
            name__icontains=search_value
        ) | queryset.filter(
            description__icontains=search_value
        )


    queryset = queryset.order_by(sort_field)

    total_records = queryset.count()
    data_slice = queryset[start:start + length]

    data = []
    for obj in data_slice:
        data.append({
            "id": obj.id,
            "name": obj.name or "N/A",
            "date": obj.created_at.strftime("%Y-%m-%d, %I:%M%p"),
            "status": obj.status, # Sending as boolean to handle in JS
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records, # Update this if you add search functionality
        "data": data,
    })


@login_required(login_url='/')
def create_ebooks(request, id=None):
    if id is not None:
        ebook_detail = ChapterBooks.objects.filter(id = id).first()

    if request.POST:
        request.session['data'] = request.POST
        if request.POST.get('id') != "":
            tag = ChapterBooks.objects.filter(id=request.POST.get('id')).first()
            if request.FILES.get('book_file') !="":
                tag.book_file = request.FILES.get('book_file')
            tag.name = request.POST.get('name')
            tag.description = request.POST.get('description')
            tag.save()
            return JsonResponse({
                "status": "success",
                "message": "eBook updated successfully"
            })
        
        else:
            tag = ChapterBooks(
                name = request.POST.get('name'),
                description = request.POST.get('description'),
                book_file = request.FILES.get('book_file'),
                status = True
            )
            tag.save()

            return JsonResponse({
                "status": "success",
                "message": "eBook created successfully"
            })
    
    return render(request, 'create_ebook.html', locals())


@require_POST
def delete_ebooks(request, pk):
    try:
        category = ChapterBooks.objects.get(pk=pk)
        category.delete()
        return JsonResponse({'status': 'success', 'message': 'Deleted successfully'})
    except ChapterBooks.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Record not found'}, status=404)


@require_POST
def update_ebooks_status(request):
    category_id = request.POST.get('id')
    new_status = request.POST.get('status') == 'true'

    try:
        # Fetch the object
        category = ChapterBooks.objects.get(id=category_id)
        category.status = new_status
        category.save()

        return JsonResponse({
            'status': 'success',
            'message': f'Ebook is now {"Active" if new_status else "Inactive"}.'
        })
    except ChapterBooks.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Ebook not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    


@login_required(login_url='/')
def manage_videos(request):
    return render(request, 'videos.html', locals())


@login_required(login_url='/')
def get_videos_listing(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    
    column_mapping = {
        '0': 'id',
        '1': 'name',
        '2': 'created_at', 
        '3': 'status',
    }
    
    order_index = request.GET.get('order[0][column]', '0')
    order_dir = request.GET.get('order[0][dir]', 'desc')
    
    sort_field = column_mapping.get(order_index, 'id')
    
    if order_dir == 'desc':
        sort_field = '-' + sort_field

    queryset = Videos.objects.all()

    search_value = request.GET.get('search[value]', None)
    if search_value:
        # Filter by name or description
        queryset = queryset.filter(
            name__icontains=search_value
        ) | queryset.filter(
            description__icontains=search_value
        )


    queryset = queryset.order_by(sort_field)

    total_records = queryset.count()
    data_slice = queryset[start:start + length]

    data = []
    for obj in data_slice:
        data.append({
            "id": obj.id,
            "name": obj.name or "N/A",
            "date": obj.created_at.strftime("%Y-%m-%d, %I:%M%p"),
            "status": obj.status, # Sending as boolean to handle in JS
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records, # Update this if you add search functionality
        "data": data,
    })


def get_signed_url(request):
    if request.method == "POST":
        
        info = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
        credentials = service_account.Credentials.from_service_account_info(info)

        storage_client = storage.Client(credentials=credentials, project=credentials.project_id)

        bucket_name = settings.GS_BUCKET_NAME
        bucket = storage_client.bucket(bucket_name)

        current_GMT = time.gmtime()
        ts = calendar.timegm(current_GMT)
        unique_file_name = f"{ts}.mp4"
        
        path = "mini_lms/videos"
        blob_path = f"media/{path}/{unique_file_name}"
        blob = bucket.blob(blob_path)

        content_type = 'video/mp4'

        try:
            # Generate the signed URL
            signed_url = blob.generate_signed_url(
                version='v4',
                expiration=3600, # 1 hour is usually plenty for an upload start
                method='PUT',
                content_type=content_type
            )

            # This is the final URL where the file will live
            public_url = f"https://storage.googleapis.com/{bucket_name}/{blob_path}"

            return JsonResponse({
                'signed_url': signed_url,
                'public_url': public_url,
                "video_file_url": path+"/"+unique_file_name
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        


@login_required(login_url='/')
def create_videos(request, id=None):
    if id is not None:
        video_detail = Videos.objects.filter(id = id).first()

    if request.method == "POST":
        video_id = request.POST.get('id')
        name = request.POST.get('name')
        description = request.POST.get('description')
        video_url = request.POST.get('video_url') # The public_url from the frontend

        if video_id:
            video = Videos.objects.get(id=video_id)
            video.name = name
            video.description = description
            if video_url:
                video.video_file = video_url
            video.save()
        else:
            Videos.objects.create(
                name=name,
                description=description,
                video_file=video_url
            )
            
        return JsonResponse({'message': 'Video saved successfully!'})
    
    return render(request, 'create_videos.html', locals())