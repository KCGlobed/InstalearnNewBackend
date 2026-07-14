import uuid
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import BaseUserManager , AbstractBaseUser, PermissionsMixin
from rolepermissions.roles import assign_role
from mini_lms.roles import *
from django_softdelete.models import SoftDeleteModel

class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, confirm_password=None, phone=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email.lower()),
            first_name=first_name,
            last_name=last_name,
            phone1=phone,
        )

        user.set_password(password)
        user.save(using=self._db)
        
        return user
    
    def create_social_user(self, email, name, social_id, social_type):
        if not email:
            raise ValueError('Users must have an email address')
        
        full_name = name.strip()
        
        first_name = ""
        last_name = ""
        
        if full_name:
            # split(' ', 1) splits only at the first space found
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0]
            if len(name_parts) > 1:
                last_name = name_parts[1]

        user = self.model(
            email=self.normalize_email(email.lower()),
            first_name=first_name,
            last_name=last_name,
        )
        user.social_id = social_id
        user.social_type = social_type
        user.set_password(social_id)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, first_name,last_name, password=None):
        user = self.create_user(
            email.lower(),
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        user.is_admin = True
        user.role = User.SuperAdmin
        user.is_active = True
        user.email_verified = 1
        user.superuser_status = True
        user.save(using=self._db)
        assign_role(user, "SuperAdmin")
        return user


class User(AbstractBaseUser, PermissionsMixin):

    SuperAdmin = 1
    SubAdmin = 2
    Manager = 4
    SalesUser = 3
    MarketingUser = 5
    CustomerSupportUser = 6
    ContentManagementUser = 7
    FinanceUser = 8
    UniversityAdmin = 9
    UniversityStaff = 10
    CorporateAdmin = 11
    CorporateStaff = 12
    ATPAdmin = 13
    ATPStaff = 14
    Instructor = 15
    Student = 16
    Mentor = 17

 

    ROLE_CHOICES = (
        (SuperAdmin, 'SuperAdmin'),
        (SubAdmin, 'SubAdmin'),
        (Manager, 'Manager'),
        (SalesUser, 'SalesUser'),
        (MarketingUser, 'MarketingUser'),
        (CustomerSupportUser, 'CustomerSupportUser'),
        (ContentManagementUser, 'ContentManagementUser'),
        (FinanceUser, 'FinanceUser'),
        (UniversityAdmin, 'UniversityAdmin'),
        (UniversityStaff, 'UniversityStaff'),
        (CorporateAdmin, 'CorporateAdmin'),
        (CorporateStaff, 'CorporateStaff'),
        (ATPAdmin, 'ATPAdmin'),
        (ATPStaff, 'ATPStaff'),
        (Instructor, 'Instructor'),
        (Student, 'Student'),
        (Mentor, 'Mentor'),
    )

    STUDENT_CATEGORY = (
        ('ATP', 'ATP'),
        ('RESELLER', 'Reseller'),
        ('BUSINESS_ASSOCIATE', 'Business Associate'),
        ('CORPORATE', 'Corporate'),
        ('INSTITUTION', 'institution'),
        ('GOV', 'gov'),
        ('DIRECT', 'direct'),
        ('OTHERS', 'others')
    )

    STUDENT_TYPE = (
        ('Institue', 'Institue'),
        ('Corporate', 'Corporate'),
        ('Retail', 'Retail'),
        ('Government', 'Government'),
    )


    SOCIAL_LOGIN_CHOICES = (
        ('Email', 'Email'),
        ('Google', 'Google'),
        ('Facebook', 'Facebook')
    )
    
    uid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4, blank=True, null=True, verbose_name='Public identifier')
    corporate = models.ForeignKey('User', null=True, blank=True, on_delete=models.SET_NULL)
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, blank=True, null=True, default=16)
    reference_id = models.CharField(max_length=100, blank=True,null=True)
    category = models.CharField(max_length=20, choices=STUDENT_CATEGORY, default='DIRECT')
    student_type = models.CharField(max_length=20, choices=STUDENT_TYPE, blank=True,null=True)
    social_id = models.CharField(max_length=255, blank=True,null=True)
    social_type = models.CharField(max_length=20, choices=SOCIAL_LOGIN_CHOICES, default='Email')
    username = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100, blank=True,null=True)
    last_name = models.CharField(max_length=100 ,blank=True,null=True)
    company_name = models.CharField(max_length=255, blank=True,null=True)
    email = models.EmailField(max_length=255,unique=True)
    phone1 = models.CharField(max_length=100,blank=True,null=True)
    phone2 = models.CharField(max_length=100,blank=True,null=True)
    address = models.CharField(max_length=255,blank=True,null=True)
    city = models.CharField(max_length=120,blank=True,null=True)
    state = models.CharField(max_length=120,blank=True,null=True)
    country = models.CharField(max_length=120,blank=True,null=True)
    pincode = models.CharField(max_length=120,blank=True,null=True)
    dob = models.DateField(blank=True, null=True)
    lastlogin = models.BigIntegerField(default=0)
    current_refresh = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    unlocked_on = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    email_verified = models.IntegerField(blank=True, null=True, default=0)
    image = models.ImageField(blank=True, null=True)
    banner_image = models.ImageField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name','last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'User'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    def is_locked(self):
        if self.locked_until:
            return True
        return False

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return self.is_admin
    


class UserOTP(models.Model):
    otp = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey('User', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User OTP'
        verbose_name_plural = 'User OTP'


class UserAccountLockDetail(models.Model):
    device_id = models.CharField(max_length=255, null=True, blank=True)
    device_type = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user = models.ForeignKey('User', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name = 'User Account Lock Detail'
        verbose_name_plural = 'User Account Lock Detail'


class DeviceStatus(models.IntegerChoices):
    Active = 1, 'Active'
    Inactive = 2, 'Inactive'

    
class UserDevices(models.Model):
    device_id = models.CharField(max_length=255, null=True, blank=True)
    device_type = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user = models.ForeignKey('User', null=True, blank=True, on_delete=models.CASCADE)
    status = models.IntegerField(choices=DeviceStatus.choices, default=DeviceStatus.Active)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name = 'User Devices'
        verbose_name_plural = 'User Devices'


class UserSession(models.Model):
    login_IP = models.GenericIPAddressField(null=True, blank=True)
    token = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey('User', null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'User Session'
        verbose_name_plural = 'User Session'



class UserLoginActivity(models.Model):
    SUCCESS = 'S'
    FAILED = 'F'

    LOGIN_STATUS = ((SUCCESS, 'Success'),
                           (FAILED, 'Failed'))

    login_IP = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(max_length=255, default=SUCCESS, choices=LOGIN_STATUS, null=True, blank=True)
    user_agent_info = models.TextField(null=True, blank=True)
    device_id = models.CharField(max_length=255, null=True, blank=True)
    device_type = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey('User', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name = 'User Login Activity'
        verbose_name_plural = 'User Login Activity'


class RolePermissions(models.Model):
    role = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    code = models.CharField(max_length=255, null=True, blank=True)
    status = models.BooleanField(null=True, blank=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'System Role Permissions'
        verbose_name_plural = 'System Role Permissions'
        
    def __str__(self):
        return '%s' % self.id
    

class AccountResetPermission(models.Model):
    user = models.ForeignKey('User', null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Account Reset Permission'
        verbose_name_plural = 'Account Reset Permission'



class PasswordChangeLog(models.Model):
    user = models.ForeignKey('User', null=True, blank=True, on_delete=models.CASCADE)
    change_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    
    class Meta:
        ordering = ['-change_date']
        verbose_name = "Password Change Log"

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} changed password on {self.change_date.strftime("%Y-%m-%d %H:%M:%S")}'
    
