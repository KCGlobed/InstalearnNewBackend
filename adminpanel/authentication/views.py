from django.shortcuts import render
from rolepermissions import roles
from rolepermissions.permissions import available_perm_status
from mini_lms.roles import *


def index(request):

    all_role_classes = roles.RolesManager.get_roles()
    roles_data = [
        role_class.get_name()
        for role_class in all_role_classes
        if role_class.get_name() not in ['Student',"Mentor","Instructor"]
    ]


    return render(request, 'login.html', locals())