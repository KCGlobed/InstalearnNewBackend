from django.shortcuts import render, redirect, get_object_or_404
from rolepermissions import roles
from rolepermissions.permissions import available_perm_status
from mini_lms.roles import *
from django.contrib.auth import authenticate, login
from rolepermissions.checkers import has_role
from users.models import *
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

def index(request):
    
    if request.session.has_key('err'):
        del request.session['err']

    all_role_classes = roles.RolesManager.get_roles()
    roles_data = [
        role_class.get_name()
        for role_class in all_role_classes
        if role_class.get_name() not in ['Student',"Mentor","Instructor"]
    ]

    if request.POST:
        err = {}
        request.session['data'] = request.POST
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        if not email:
            err.update({'email':'Please enter valid email'})
        if not role:
            err.update({'role':'Please select valid role'})
        if not password:
            err.update({'password':'Please enter valid password'})
        
        user = User.objects.filter(email =email.lower()).first()
        if user:
            if user.is_active is False:
                err.update({'email':'User is not active!'})
            
            if user.email_verified == 0:
                err.update({'email':'User email is not verified!'})
            
            if not user.check_password(password):
                err.update({'password':'Invalid Password!'})
            if not has_role(user, role):
                err.update({'role':'Invalid User!'})
        else:
            err.update({'email':'User Not found with this email'})
            
        if err:
            request.session['err'] = err
            return render(request, 'login.html', locals())

        user = authenticate(email = email, password = password)
        if user is not None:
            UserDevices.objects.update_or_create(
                user=user,
                device_id="5as4d5as6ds54ad4ad",
                defaults={
                    'device_type': "desktop",
                    "ip_address":get_client_ip(request),
                    "status":DeviceStatus.Active
                }
            )

            token = get_tokens_for_user(user)
            login(request, user)
            update_last_login(None, user)

            if user.current_refresh is not None:
                try:
                    RefreshToken(user.current_refresh).blacklist()
                except TokenError:
                    pass
            
            user.current_refresh = token['refresh']
            user.save()

            UserLoginActivity.objects.create(
                login_IP=get_client_ip(request), 
                user=user,
                status='Success', 
                country = get_country_from_ip(get_client_ip(request)),
                device_type = "desktop",
                device_id = "5sa4da5sd4s54d5asd4",
                user_agent_info = request.META['HTTP_USER_AGENT']
            )

            UserSession.objects.filter(user = user).delete()
            UserSession.objects.create(
                login_IP=get_client_ip(request), 
                user=user,
                token=token['access'],
            )

            new_alert_login(user, get_client_ip(request))
            
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save()

            return redirect('dashboard')

    return render(request, 'login.html', locals())


def forgot_password(request):

    if request.session.has_key('err'):
        del request.session['err']

    if request.session.has_key('success'):
        del request.session['success']

    if request.POST:
        err = {}
        request.session['data'] = request.POST
        email = request.POST.get('email')
        if not email:
            err.update({'email':'Please enter valid email'})
        
        user = User.objects.filter(email =email.lower()).first()
        if user:
            if user.is_active is False:
                err.update({'email':'User is not active!'})
            
            if user.email_verified == 0:
                err.update({'email':'User email is not verified!'})
            
        else:
            err.update({'email':'User Not found with this email'})
            
        if err:
            request.session['err'] = err
            return render(request, 'forgot-password.html', locals())
        

        uid = urlsafe_base64_encode(force_bytes(user.id))
        token = PasswordResetTokenGenerator().make_token(user)
        
        url = settings.ADMIN_URL+"/admin-reset-password?uid="+uid+'&token='+token

        subject = 'Reset Password Link'
        message = f'Hi {user.first_name} {user.last_name}, Here is the your reset password link: '+url
        
        message = f'Hi you have got a reset password request'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = ["testtechno0@yopmail.com", ]
        html_message = loader.render_to_string(
            'reset_email.html',
            {
                'name': user.first_name +' '+ user.last_name,
                'verification_link': url,
            }
        )

        send_mail( subject, message, email_from, recipient_list,html_message=html_message )
        success_msg = "Password Reset Successfully!"
        request.session['success_msg'] = success_msg

    return render(request, 'forgot-password.html', locals())


def reset_password(request):

    if request.session.has_key('err'):
        del request.session['err']

    if request.session.has_key('success'):
        del request.session['success']

    uid = request.GET.get('uid')
    token = request.GET.get('token')
    
    id = smart_str(urlsafe_base64_decode(uid))
    user = User.objects.filter(id=id).first()
    error_msg = ""
    if user is None:
        error_msg = "Expired Link"
        request.session['error_msg'] = error_msg
    
    if not PasswordResetTokenGenerator().check_token(user, token):
        error_msg = "Expired Link"
        request.session['error_msg'] = error_msg

    if request.POST:
        err = {}
        request.session['data'] = request.POST
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if len(password) < 5:
            err.update({'password':"Password length must be grater than 6 digit"})

        if password != confirm_password:
            err.update({'confirm_password':"Password and confirm password doesn't match"})
            
        if err:
            request.session['err'] = err
            return render(request, 'reset-password.html', locals())
        
        user.set_password(password)
        user.save()

        PasswordChangeLog.objects.create(
            user=user
        )

        success_msg = "Reset Password Email Send Successfully!"
        request.session['success'] = success_msg

    return render(request, 'reset-password.html', locals())

@login_required(login_url='/')
def dashboard(request):
    return render(request, 'dashboard.html', locals())