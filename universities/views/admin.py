from rest_framework import status
from rest_framework.views import APIView
from universities.serializers import *
from universities.renderers import UniversityRenderer
from rest_framework.permissions import IsAuthenticated
from mini_lms.utils import *
from mini_lms.roles import *
from rest_framework.exceptions import NotFound , ValidationError
from mini_lms.permissions import RoleOrPermissionCheck
from mini_lms.pagination import CustomPageNumberPagination
from rest_framework import filters
from django.utils import timezone
from google.cloud import storage
from django.conf import settings
import tempfile
import os
import json
from google.oauth2 import service_account
info = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
credentials = service_account.Credentials.from_service_account_info(info)
client = storage.Client(credentials=credentials, project=credentials.project_id)
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import get_template
from datetime import timedelta
import pandas as pd



class GetUniversityRequestsListingView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "university_requests_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name','last_name',"work_email","status"]
    ordering_fields = ['first_name', 'created_at', 'id', 'last_name',"work_email","status","approved_status"] 
    def get(self, request, format=None):
        
        plans = University.objects.all()
        
        first_name = request.query_params.get('first_name')
        if first_name:
            plans = plans.filter(first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            plans = plans.filter(last_name__icontains = last_name)

        work_email = request.query_params.get('work_email')
        if work_email:
            plans = plans.filter(work_email__icontains = work_email)

        country = request.query_params.get('country')
        if country:
            plans = plans.filter(country__icontains = country)

        institution_name = request.query_params.get('institution_name')
        if institution_name:
            plans = plans.filter(institution_name__icontains = institution_name)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                plans = plans.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                plans = plans.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")


        search_filter = filters.SearchFilter()
        plans = search_filter.filter_queryset(request, plans, self)

        ordering_filter = filters.OrderingFilter()
        plans = ordering_filter.filter_queryset(request, plans, self)

        if not plans.ordered:
            plans = plans.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(plans, request, view=self)
        serializer = UniversityRequestsSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ViewUniversityRequestDetailView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "view_university_requests_detail",
                            [SuperAdmin]
                        )]
    def get(self, request, sid=None):
        users_list = University.objects.filter(id = sid).first()
        if users_list is None:
            raise ValidationError("Invalid Request ID!")
        
        serializer = UniversityRequestsDetailSerializer(users_list)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)



class UpdateUniversityRequestStatusView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_university_requests_status",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = University.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Request ID!")
        
        serializer = ChangeUniversitystatusSerializer(category, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="University Status Updated Successfully", data=UniversityRequestsSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class ApproveRejectUniversityRequestStatusView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_university_requests_status",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = University.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid Request ID!")
        
        serializer = ApproveRejectUniversitystatusSerializer(category, data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="University Status Updated Successfully", data=UniversityRequestsSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class AssignSubscriptiontoCorporateAdminUserView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_university_subscription",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        category = University.objects.filter(id=cid).first()
        if category is None:
            raise ValidationError("Invalid University ID!")
        
        serializer = AssignSubscriptiontoUniversitySerializer(data = request.data, context={'university':category})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Subscription assigned Successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)



class PDFUniversityRequestsReportView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "partner_request_pdf_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', "last_name","email","mobile"]
    ordering_fields = ['first_name', "last_name","email","mobile",'created_at', 'id'] 
    def get(self, request, format=None):
        
        plans = University.objects.all()
                
        first_name = request.query_params.get('first_name')
        if first_name:
            plans = plans.filter(first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            plans = plans.filter(last_name__icontains = last_name)

        work_email = request.query_params.get('work_email')
        if work_email:
            plans = plans.filter(work_email__icontains = work_email)

        country = request.query_params.get('country')
        if country:
            plans = plans.filter(country__icontains = country)

        institution_name = request.query_params.get('institution_name')
        if institution_name:
            plans = plans.filter(institution_name__icontains = institution_name)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                plans = plans.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                plans = plans.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")


        search_filter = filters.SearchFilter()
        plans = search_filter.filter_queryset(request, plans, self)

        ordering_filter = filters.OrderingFilter()
        plans = ordering_filter.filter_queryset(request, plans, self)

        if not plans.ordered:
            plans = plans.order_by('-id')

        serializer = UniversityRequestsSerializer(plans, many=True)
        
        data = {
            "info":serializer.data
        }


        template = get_template('pdf/uniersity_requests_report.html')
        html  = template.render(data)
        # Use tempfile to create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            html = html.encode('latin-1', 'replace').decode('latin-1')
            pdf = pisa.CreatePDF(BytesIO(html.encode("ISO-8859-1")), dest=temp_file)

            if pdf.err:
                raise Exception("PDF generation error!")
        
        try:
            timestamp = int(datetime.now().timestamp() * 1000)
            report_name = "uniersity_requests_report"
            gcs_folder_name = "media/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.pdf"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            # Ensure the temporary file is deleted from the server's disk
            os.remove(pdf_path)



class CSVUniversityRequestsReportView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "partner_request_excel_report",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', "last_name","email","mobile"]
    ordering_fields = ['first_name', "last_name","email","mobile",'created_at', 'id'] 
    def get(self, request, format=None):
        
        plans = University.objects.all()
                        
        first_name = request.query_params.get('first_name')
        if first_name:
            plans = plans.filter(first_name__icontains = first_name)

        last_name = request.query_params.get('last_name')
        if last_name:
            plans = plans.filter(last_name__icontains = last_name)

        work_email = request.query_params.get('work_email')
        if work_email:
            plans = plans.filter(work_email__icontains = work_email)

        country = request.query_params.get('country')
        if country:
            plans = plans.filter(country__icontains = country)

        institution_name = request.query_params.get('institution_name')
        if institution_name:
            plans = plans.filter(institution_name__icontains = institution_name)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                plans = plans.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                plans = plans.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")


        search_filter = filters.SearchFilter()
        plans = search_filter.filter_queryset(request, plans, self)

        ordering_filter = filters.OrderingFilter()
        plans = ordering_filter.filter_queryset(request, plans, self)

        if not plans.ordered:
            plans = plans.order_by('-id')

        serializer = UniversityRequestsSerializer(plans, many=True)

        lis = []

        # Title Header
        lis.append({
            "first_name": "University Request Report",
            "last_name": "",
            "phone_number": "",
            "work_email": "",
            "institution_type": "",
            "institution_name": "",
            "country": "",
            "job_role": "",
            "department": "",
            "created_at": "",
        })

        # Empty Spacers
        lis.append({
            "first_name": "",
            "last_name": "",
            "phone_number": "",
            "work_email": "",
            "institution_type": "",
            "institution_name": "",
            "country": "",
            "job_role": "",
            "department": "",
            "created_at": "",
        })

        lis.append({
            "first_name": "",
            "last_name": "",
            "phone_number": "",
            "work_email": "",
            "institution_type": "",
            "institution_name": "",
            "country": "",
            "job_role": "",
            "department": "",
            "created_at": "",
        })

        # Column Headers
        lis.append({
            "first_name": "First Name",
            "last_name": "Last Name",
            "phone_number": "Phone Number",
            "work_email": "Work Email",
            "institution_type": "Institution Type",
            "institution_name": "Institution Name",
            "country": "Country",
            "job_role": "Job Role",
            "department": "Department",
            "created_at": "Created At",
        })

        # Data Rows
        for item in serializer.data:
            lis.append({
                "first_name": item.get("first_name", ""),
                "last_name": item.get("last_name", ""),
                "phone_number": item.get("phone_number", ""),
                "work_email": item.get("work_email", ""),
                "institution_type": item.get("institution_type", ""),
                "institution_name": item.get("institution_name", ""),
                "country": item.get("country", ""),
                "job_role": item.get("job_role", ""),
                "department": item.get("department", ""),
                "created_at": item.get("created_at", ""),
            })

        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            # GCS file naming logic
            timestamp = int(datetime.now().timestamp() * 1000)
            report_name = "job_application_report"
            gcs_folder_name = "media/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            # Upload the temporary file to GCS
            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            # Ensure the temporary file is deleted
            os.remove(pdf_path)



class ImportUniversityStudentsView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "import_students",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = ImportStudentsSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):

            excel_file = serializer.validated_data['excel_file']
            university_id = serializer.validated_data['university_id']
            university = University.objects.filter(id = university_id).first()
            try:
                imported_emails = []

                colnames=['first_name', 'last_name', 'email','phone_number']

                df = pd.read_excel(excel_file, names=colnames, skiprows=2)
                df = df.fillna('')

                df['email'] = df['email'].astype(str).str.strip().str.lower()
                
                file_emails = [email for email in df['email'].tolist() if email]

                duplicate_file_emails = set([email for email in file_emails if file_emails.count(email) > 1])
                if duplicate_file_emails:
                    return error_response(
                        message="Import failed: Duplicate emails found within the uploaded file.",
                        data={"duplicate_emails": list(duplicate_file_emails)},
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                existing_db_emails = set(
                    User.objects.filter(email__in=file_emails).values_list('email', flat=True)
                )
                if existing_db_emails:
                    return error_response(
                        message="Import failed: Some emails already exist in the database.",
                        data={"existing_emails": list(existing_db_emails)},
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                valid_rows_df = df[
                    (df['first_name'] != '') | 
                    (df['last_name'] != '') | 
                    (df['email'] != '') | 
                    (df['phone_number'] != '')
                ]
                total_incoming_students = len(valid_rows_df)

                total_licenses = Order.objects.filter(
                    university_id=university_id
                ).aggregate(total=Sum('no_of_licence'))['total'] or 0

                if total_incoming_students > total_licenses:
                    return error_response(
                        message="Import failed: Student count exceeds available license limit.",
                        data={
                            "allowed_licenses": total_licenses,
                            "excel_student_count": total_incoming_students
                        },
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                password = generate_random_password(8)

                for index, row in df.iterrows():

                    info = { "first_name": str(row['first_name']).strip(),"last_name": str(row['last_name']).strip(), 'email': row['email'].lower(), 'password': password}
                    
                    user_info = User.objects.create_user(**info)
                    assign_role(user_info, "Student")
        
                    user_info.role = User.Student
                    user_info.email_verified = 1
                    user_info.university = university
                    user_info.is_active = True
                    user_info.save()
        
                    imported_emails.append(user_info.email)


                url = settings.BASE_URL+"/login"
                
                subject = 'Thank you for registering!'
        
                message = f''
                email_from = settings.EMAIL_HOST_USER
                recipient_list = imported_emails
                html_message = loader.render_to_string(
                    'new_user_email.html',
                    {
                        'name': "User",
                        'verification_link': url,
                        "email": "Registered Email",
                        "password": password,
        
                    }
                )
                send_mail( subject, message, email_from, recipient_list,html_message=html_message )

                        
            except Exception as e:
                return error_response(message="failed", data = {"error": f"Error processing Excel file: {str(e)}"}, status_code=status.HTTP_400_BAD_REQUEST)

            return success_response(message="Student Imported Successfully", data={"imported_emails": imported_emails}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)



class CreateStudentView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_university_student",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateStudentSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="User Created Successfully", data={}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class CreateUniversityView(APIView):
    renderer_classes = [UniversityRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_university",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateUniversitySerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="User Created Successfully", data=UniversityRequestsSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)