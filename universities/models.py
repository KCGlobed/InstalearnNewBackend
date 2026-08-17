from django.db import models

INSTITUTION_TYPE_CHOICES = [
        ('University/4 Year College', 'University/4 Year College'),
        ('2 Year College', '2 Year College'),
        ('Graduate or Professional School', 'Graduate or Professional School'),
        ('Ministry of Education', 'Ministry of Education'),
        ('Other', 'Other'),
    ]

JOB_ROLE_CHOICES = [
        ('President/Provost', 'President/Provost'),
        ('Chancellor/Rector', 'Chancellor/Rector'),
        ('Vice-Chancellor/Vice-Rector', 'Vice-Chancellor/Vice-Rector'),
        ('Vice-President/Vice-Provost', 'Vice-President/Vice-Provost'),
        ('Registrar', 'Registrar'),
        ('CEO', 'CEO'),
        ('COO/CIO', 'COO/CIO'),
        ('Dean', 'Dean'),
        ('Department Head', 'Department Head'),
        ('Director', 'Director'),
        ('Professor', 'Professor'),
        ('Student', 'Student'),
    ]

DEPARTMENT_CHOICES = [
        ('Academic Affairs', 'Academic Affairs'),
        ('Career Services', 'Career Services'),
        ('Continuing Education', 'Continuing Education'),
        ('Enrollment Management', 'Enrollment Management'),
        ('Executive Leadership', 'Executive Leadership'),
        ('International', 'International'),
        ('Strategic Planning', 'Strategic Planning'),
        ('Student Affairs', 'Student Affairs'),
        ('Teaching/Faculty/Research', 'Teaching/Faculty/Research'),
        ('Other', 'Other'),
    ]

class UniversityStatus(models.IntegerChoices):
    New = 1, 'New'
    Approved = 2, 'Approved'
    Rejected = 3, 'Rejected'


class University(models.Model):
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    work_email = models.EmailField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    institution_type = models.CharField(max_length=50, choices=INSTITUTION_TYPE_CHOICES, default='Other')
    institution_name = models.CharField(max_length=255, null=True, blank=True)
    job_role = models.CharField(max_length=50, choices=JOB_ROLE_CHOICES, default='student')
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, default='Other')
    country = models.CharField(max_length=255, null=True, blank=True)
    status = models.BooleanField(default=True)
    approved_status = models.IntegerField(choices=UniversityStatus.choices,default=UniversityStatus.New)
    approved_by = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.CASCADE, related_name="apporved_by_user")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        verbose_name = 'University'
        verbose_name_plural = 'University'
        
    def __str__(self):
        return '%s' % self.id