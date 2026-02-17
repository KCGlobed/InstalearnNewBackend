from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from rolepermissions.checkers import has_role
from mini_lms.roles import *
from users.models import *
import logging
logger = logging.getLogger()
from urllib.parse import urlparse
import random
import string
import math
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from courses.models import *


CHUNK_SIZE = 1024 * 1024 * 10
ROLE_MAPPING = { SuperAdmin: "SuperAdmin", SubAdmin: "SubAdmin", SalesUser: "SalesUser", MarketingUser: "MarketingUser", Manager: "Manager", CustomerSupportUser: "CustomerSupportUser", ContentManagementUser: "ContentManagementUser", FinanceUser: "FinanceUser", UniversityAdmin: "UniversityAdmin", UniversityStaff: "UniversityStaff", CorporateAdmin: "CorporateAdmin", CorporateStaff: "CorporateStaff", ATPAdmin: "ATPAdmin", ATPStaff: "ATPStaff", Instructor: "Instructor", Student: "Student", Mentor: "Mentor", }

URL_ROLE_MAPPING = { User.SalesUser: "sales_user", User.MarketingUser: "marketing_user", User.Manager: "manager", User.CustomerSupportUser: "customer_support_user", User.ContentManagementUser: "content_management_user", User.Instructor: "instructor",User.FinanceUser: "finance_user"}

URL_ROLE_CLASS_MAPPING = { SalesUser: "sales_user", MarketingUser: "marketing_user", Manager: "manager", CustomerSupportUser: "customer_support_user", ContentManagementUser: "content_management_user", Instructor: "instructor", FinanceUser: "finance_user"}


DEVICES_ROLE_MAPPING = { SuperAdmin: "SuperAdmin", SubAdmin: "SubAdmin", SalesUser: "SalesUser", MarketingUser: "MarketingUser", Manager: "Manager", CustomerSupportUser: "CustomerSupportUser", ContentManagementUser: "ContentManagementUser", FinanceUser: "FinanceUser", UniversityAdmin: "UniversityAdmin", UniversityStaff: "UniversityStaff", CorporateAdmin: "CorporateAdmin", CorporateStaff: "CorporateStaff", ATPAdmin: "ATPAdmin", ATPStaff: "ATPStaff"}

def plan_interval(value):
    if value == 1:
        return {"period": "monthly", "interval": 1}
    elif value == 2:
        return {"period": "monthly", "interval": 6}
    else:
        return {"period": "yearly", "interval": 1}
    
    
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    return (
        x_forwarded_for.split(",")[0]
        if x_forwarded_for
        else request.META.get("REMOTE_ADDR")
    )


def create_response(success, message, data=None, status_code=status.HTTP_200_OK):
    response_data = {
        "success": success,
        "status": str(status_code),
        "message": message,
        "data": data if data is not None else {}
    }
   
    logger.info(f"Response: {message} - Status: {status_code}")
   
    return Response(response_data, status=status_code)
 
def success_response(message, data=None, status_code=status.HTTP_200_OK):
    return create_response(True, message, data, status_code)
 
def error_response(message, data=None, status_code=status.HTTP_400_BAD_REQUEST):
    return create_response(False, message, data, status_code)



def parse_gcs_url(file_url):
    parsed_url = urlparse(file_url)
    if parsed_url.scheme != 'https':
        raise ValueError("URL must start with 'https://'")
    
    if not parsed_url.netloc.endswith('storage.googleapis.com'):
        raise ValueError("Invalid Google Cloud Storage URL")

    path_parts = parsed_url.path.lstrip('/').split('/', 1)
    if len(path_parts) != 2:
        raise ValueError("Invalid GCS URL format")


    bucket_name, object_name = path_parts
    return bucket_name, object_name


def check_domain_match(email, target_domain='kcglobed.com'):
    try:
        domain = email.split('@')[1]
        return domain.lower() == target_domain.lower()
    except IndexError:
        return False
    

def check_devices_login(user , device_type, device_id, setting):

    for role, role_name in DEVICES_ROLE_MAPPING.items(): 
        if has_role(user, [role]): 
            return True 
        
    user_devices_count = UserDevices.objects.filter(device_type = device_type,user = user, status = DeviceStatus.Active).count()

    devices = UserDevices.objects.filter(device_type = device_type, device_id = device_id, user = user, status = DeviceStatus.Active).count()

    if device_type == "desktop":
        if user_devices_count >= setting.allowed_desktop and devices == 0:
            return False
    if device_type == "phone":
        if user_devices_count >= setting.allowed_phone and devices == 0:
            return False
    if device_type == "tablet":
        if user_devices_count >= setting.allowed_tablet and devices == 0:
            return False
        
    return True


def get_country_from_ip(ip_address):
    try:
        import requests
        api_url = f"http://ip-api.com/json/{ip_address}"
        response = requests.get(api_url, timeout=5)
        response.raise_for_status() 
        data = response.json()
        if data.get('status') == 'success':
            return data.get('country')
        else:
            return None
        
    except Exception as e:
        return None
    

def get_user_role(user): 
    for role, role_name in ROLE_MAPPING.items(): 
        if has_role(user, [role]): 
            return role_name 
    return None


def get_role(role_info): 
    for role, role_name in ROLE_MAPPING.items(): 
        if role_info == role_name: 
            return role 
    return None


def user_role_report(value):
    role_map = dict(User.ROLE_CHOICES)
    return role_map.get(value, None)

def get_url_role(role_info): 
    for role, role_name in URL_ROLE_MAPPING.items(): 
        if role_info == role_name: 
            return role 
    return None

def get_url_role_class(role_info): 
    for role, role_name in URL_ROLE_CLASS_MAPPING.items(): 
        if role_info == role_name: 
            return role 
    return None


def generate_random_password(length=8):
    letters = string.ascii_letters 
    digits = string.digits       
    special_characters = '@#$%&*'
    password = [
        random.choice(special_characters),  
        random.choice(letters),             
        random.choice(digits)
    ]
    all_characters = letters + digits + special_characters
    password += random.choices(all_characters, k=length - 3)
    random.shuffle(password)
    return ''.join(password)


def custom_round(number):
    if not isinstance(number, (int, float)):
        raise TypeError("Input must be a number.")

    if 0 < number < 1:
        if (number - math.floor(number)) < 0.50:
            return 1
        else:
            return math.ceil(number)
    else:
        if (number - math.floor(number)) < 0.50:
            return math.floor(number)
        else:
            return math.ceil(number)
    
        
def generate_random_password(length=8):
    letters = string.ascii_letters 
    digits = string.digits       
    special_characters = '@#$%&*'
    password = [
        random.choice(special_characters),  
        random.choice(letters),             
        random.choice(digits)
    ]
    all_characters = letters + digits + special_characters
    password += random.choices(all_characters, k=length - 3)
    random.shuffle(password)
    return ''.join(password)


def validate_course_id_list(id_list):
    if not isinstance(id_list, list):
        raise serializers.ValidationError("Expected a list of IDs.")

    if len(id_list) == 0:
        raise serializers.ValidationError("Course IDs is required field!")
    
    existing_tag_ids = set(Course.objects.filter(id__in=id_list).values_list('id', flat=True))
    non_existent_ids = [str(tag_id) for tag_id in id_list if tag_id not in existing_tag_ids]

    if non_existent_ids:
        raise serializers.ValidationError(
            f"The following Course IDs do not exist: {', '.join(non_existent_ids)}."
        )

    return id_list


def new_alert_login(user, ip_address):
    pass
    # notification_setting = UserNotificationSetting.objects.filter(user = user).first()
    # if notification_setting is not None:
    #     if notification_setting.new_login == 1:
    #         user_act = UserLoginActivity.objects.only("id","login_IP").filter(user = user).first()
    #         if user_act is not None:
    #             if user_act.login_IP != ip_address:
    #                 Notification.objects.create(
    #                     title='New Login Alert',
    #                     user=user,
    #                     description='You have successfully logged into the system.', 
    #                     notification_type = NotificationType.New_Login_Alert
    #                 )
    #         else:
    #             Notification.objects.create(
    #                 title='New Login Alert',
    #                 user=user,
    #                 description='You have successfully logged into the system.', 
    #                 notification_type = NotificationType.New_Login_Alert
    #             )