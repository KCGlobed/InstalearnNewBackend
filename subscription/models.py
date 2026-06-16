from django.db import models
from django_softdelete.models import SoftDeleteModel
from simple_history.models import HistoricalRecords


class PlanType(models.IntegerChoices):
    Monthly = 1, 'Monthly'
    Half_Yearly = 2, 'Half Yearly'
    Yearly = 3, 'Yearly'

class PlanFor(models.IntegerChoices):
    Students = 1, 'Students'
    Corporates = 2, 'Corporates'
    University = 3, 'University'
    ATP = 4, 'ATP'

class Currency(models.TextChoices):
    INR = 'INR'
    USD = 'USD'


class SubscriptionPlans(SoftDeleteModel):
    plan_id = models.CharField(max_length=255, null=True, blank=True)
    plan_name = models.CharField(max_length=255, null=True, blank=True)
    plan_description = models.TextField(null=True, blank=True)
    banner_text = models.CharField(max_length=255, null=True, blank=True)
    original_price = models.FloatField(null=True, blank=True, default=0.0)
    discount_percentage = models.FloatField(null=True, blank=True, default=0.0)
    monthly_amount = models.FloatField(null=True, blank=True, default=0.0)
    amount = models.FloatField(null=True, blank=True, default=0.0)
    gst_amount = models.FloatField(null=True, blank=True, default=0.0)
    amount_without_gst = models.FloatField(null=True, blank=True, default=0.0)
    plan_type = models.IntegerField(choices=PlanType.choices,default=PlanType.Monthly)
    currency = models.CharField(choices=Currency.choices,default=Currency.INR)
    interval = models.IntegerField(null=True, blank=True, default=1)
    plan_cycle = models.IntegerField(null=True, blank=True, default=1)
    feature = models.JSONField(null=True, blank=True)
    status = models.BooleanField(default=True)
    plan_for = models.IntegerField(choices=PlanFor.choices,default=PlanFor.Students)
    no_of_licence = models.IntegerField(null=True, blank=True, default=0)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'Subscription Plans'
        verbose_name_plural = 'Subscription Plans'
        
    def __str__(self):
        return '%s' % self.plan_name


class OrderStatus(models.IntegerChoices):
    Initiate = 1, 'Initiate'
    Active = 2, 'Active'
    Expired = 3, 'Expired'
    Paused = 4, 'Paused'
    Cancelled = 5, 'Cancelled'

class PaymentMethod(models.IntegerChoices):
    Online = 1, 'Online'
    Offline = 2, 'Offline'


class Order(models.Model):
    orderID = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    billing_address = models.TextField(null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    gst_number = models.CharField(max_length=255, null=True, blank=True)
    pincode = models.CharField(max_length=255, null=True, blank=True)
    amount = models.FloatField(null=True, blank=True, default=0.0)
    gst_amount = models.FloatField(null=True, blank=True, default=0.0)
    discount_percentage = models.FloatField(null=True, blank=True, default=0.0)
    discount_amount = models.FloatField(null=True, blank=True, default=0.0)
    total_amount = models.FloatField(null=True, blank=True, default=0.0)
    razorpay_order_id = models.CharField(max_length=255,null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=255,null=True, blank=True)
    razorpay_signature = models.TextField(null=True, blank=True)
    coupon = models.ForeignKey('Coupon', null=True, blank=True, on_delete=models.SET_NULL)
    plan = models.ForeignKey('SubscriptionPlans', null=True, blank=True, on_delete=models.SET_NULL)
    subscription_id = models.CharField(max_length=255, null=True, blank=True)
    subscription_response = models.JSONField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    next_due = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    subscription_url = models.CharField(max_length=255, null=True, blank=True)
    subscription_status = models.IntegerField(choices=OrderStatus.choices,default=OrderStatus.Initiate)
    subscription_type = models.IntegerField(choices=PlanType.choices,default=PlanType.Monthly)
    trail_mode = models.BooleanField(default=False)
    try_for_free = models.BooleanField(default=False)
    payment_method = models.IntegerField(choices=PaymentMethod.choices,default=PaymentMethod.Online)
    order_date = models.DateTimeField(auto_now=True)
    no_of_licence = models.IntegerField(null=True, blank=True, default=0)
    isPaid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Order'

    def __str__(self):
        return '%s' % self.id



class OrderSubscriptionPayments(models.Model):
    order = models.ForeignKey('Order', null=True, blank=True, on_delete=models.SET_NULL)
    payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    invoice_id = models.CharField(max_length=255, null=True, blank=True)
    amount = models.FloatField(null=True, blank=True, default=0.0)
    status = models.CharField(max_length=255, null=True, blank=True)
    payment_method = models.CharField(max_length=255, null=True, blank=True, default='online')
    isPaid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Order Subscription Payments'
        verbose_name_plural = 'Order Subscription Payments'

    def __str__(self):
        return '%s' % self.id


class UserCourses(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.CASCADE)
    order = models.ForeignKey('Order', null=True, blank=True, on_delete=models.CASCADE)
    trail = models.BooleanField(default=False)
    progress_percentage = models.FloatField(null=True, blank=True, default=0.0)
    completed = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    is_started = models.BooleanField(default=False)
    expired_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    
    class Meta:
        verbose_name = 'User Courses'
        verbose_name_plural = 'User Courses'
        
    def __str__(self):
        return '%s' % self.id
    


class Coupon(SoftDeleteModel):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES,default="fixed")
    discount_value = models.DecimalField(max_digits=10, decimal_places=2,default=1)
    expiration_date = models.DateTimeField(null=True, blank=True)
    is_active = models.IntegerField(null=True, blank=True, default=1)

    def __str__(self):
        return self.code


class Cart(models.Model):
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Cart'
        
    def __str__(self):
        return '%s' % self.id
    


class TrailUser(models.Model):
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    
    class Meta:
        verbose_name = 'Trail User'
        verbose_name_plural = 'Trail User'
        
    def __str__(self):
        return '%s' % self.id
    
    

class TrailUserCourses(models.Model):
    trail_user = models.ForeignKey('TrailUser', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    
    class Meta:
        verbose_name = 'Trail User Courses'
        verbose_name_plural = 'Trail User Courses'
        
    def __str__(self):
        return '%s' % self.id