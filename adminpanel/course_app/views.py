from django.shortcuts import render, redirect, get_object_or_404
from rolepermissions import roles
from rolepermissions.permissions import available_perm_status
from mini_lms.roles import *
from django.contrib.auth import authenticate, login
from rolepermissions.checkers import has_role
from users.models import *
from courses.models import *
from mini_lms.utils import *
from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator 
from django.utils.encoding import smart_str, force_bytes
from django.http import JsonResponse
from django.views.decorators.http import require_POST


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