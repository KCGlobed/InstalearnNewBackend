from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from questions.serializers import *
from questions.renderers import QuestionRenderer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from mini_lms.utils import *
from mini_lms.roles import *
from mini_lms.permissions import RoleOrPermissionCheck
from mini_lms.pagination import CustomPageNumberPagination
from rest_framework import filters
import pandas as pd
from datetime import datetime,timezone
from rest_framework import serializers
from django.conf import settings
import os
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import get_template
import pandas as pd
import tempfile
import re
import json
from google.cloud import storage
from google.oauth2 import service_account
info = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
credentials = service_account.Credentials.from_service_account_info(info)
client = storage.Client(credentials=credentials, project=credentials.project_id)


class MCQsListingView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "mcq_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['id_number',"chapter__name"]
    ordering_fields = ['id_number', 'id', 'status']
    def get(self, request, sid = None,format=None):
        if sid is not None:
            question = TestQuestions.objects.filter(chapter_id = sid, question_type = QuestionType.MCQ)
        else:
            question = TestQuestions.objects.filter(question_type = QuestionType.MCQ)

        chapter_id = request.query_params.get('chapter_id')
        if chapter_id:
            question = question.filter(chapter_id=chapter_id)

        
        id_number = request.query_params.get('id_number')
        if id_number:
            question = question.filter(id_number__icontains=id_number)
        
        active = request.query_params.get('status')
        if active:
            question = question.filter(status=active)


        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                question = question.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                question = question.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")


        search_filter = filters.SearchFilter()
        question = search_filter.filter_queryset(request, question, self)

        ordering_filter = filters.OrderingFilter()
        question = ordering_filter.filter_queryset(request, question, self)

        if not question.ordered:
            question = question.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(question, request, view=self)
        serializer = ViewTestQuestionDetailSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ExportMCQsListingExcelView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "mcq_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['id_number',"chapter__name"]
    ordering_fields = ['id_number', 'id', 'status']
    def get(self, request, sid = None,format=None):
        if sid is not None:
            question = TestQuestions.objects.filter(chapter_id = sid, question_type = QuestionType.MCQ)
        else:
            question = TestQuestions.objects.filter(question_type = QuestionType.MCQ)

        chapter_id = request.query_params.get('chapter_id')
        if chapter_id:
            question = question.filter(chapter_id=chapter_id)

        
        id_number = request.query_params.get('id_number')
        if id_number:
            question = question.filter(id_number__icontains=id_number)
        
        active = request.query_params.get('status')
        if active:
            question = question.filter(status=active)


        search_filter = filters.SearchFilter()
        question = search_filter.filter_queryset(request, question, self)

        ordering_filter = filters.OrderingFilter()
        question = ordering_filter.filter_queryset(request, question, self)

        if not question.ordered:
            question = question.order_by('-id')

        serializer = ViewTestQuestionDetailSerializer(question, many=True)

        lis = []
        
        lis.append({
                "name":"MCQs Report",
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":'',
                "solution":"",
                "option_1":"",
                "option_2":"",
                "option_3":"",
                "option_4":"",
                "right_option":"",
                "status":"",
            })

        
        lis.append({
                "name":"",
                "Topic":'',
                "total_videos":'',
                "total_watched_videos":'',
                "total_time_spend":'',
                "solution":"",
                "option_1":"",
                "option_2":"",
                "option_3":"",
                "option_4":"",
                "right_option":"",
                "status":"",
            })
        
        
        lis.append({
                "name":"ID Number",
                "Topic":'Level',
                "total_videos":'Pass Percentage',
                "total_watched_videos":'Chapter Name',
                "total_time_spend":'Question',
                "solution":"Solution",
                "option_1":"Option 1",
                "option_2":"Option 2",
                "option_3":"Option 3",
                "option_4":"Option 4",
                "right_option":"Right Answer",
                "status":"Is Active?",
            })
  

        for order_info in serializer.data:
            
            lis.append({
                "name":order_info['id_number'],
                "Topic":difficulty_level(order_info['level']),
                "total_videos":order_info['pass_percentage'],
                "total_watched_videos":order_info['chapter']['name'],
                "total_time_spend":order_info['question_detail']['question'],
                "solution":order_info['question_detail']['solution_description'],
                "option_1":order_info['options'][0]['option'],
                "option_2":order_info['options'][1]['option'],
                "option_3":order_info['options'][2]['option'],
                "option_4":order_info['options'][3]['option'],
                "right_option":order_info['right_option']['option'],
                "status":order_info['status'],
            })
            
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            pdf_path = temp_file.name
            
            df = pd.DataFrame.from_dict(lis)
            df.to_excel(pdf_path, header=False, index=False)
        
        try:
            timestamp = datetime.now().strftime("%d_%m_%y_%H_%M_%S")
            report_name = "mcq_report"
            gcs_folder_name = "media/reports"
            gcs_file_name = f"{gcs_folder_name}/{report_name}_{timestamp}.xlsx"

            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(pdf_path)

            return success_response(
                message="Success",
                data={"report_url": blob.public_url},
                status_code=status.HTTP_200_OK
            )
        finally:
            os.remove(pdf_path)
    

class ViewMCQDetailView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "mcq_listing",
                            [SuperAdmin]
                        )]
    def get(self, request,  cid , format=None):
        question = TestQuestions.objects.filter(id=cid).first()
        if question is None:
            raise serializers.ValidationError("Invalid MCQ ID!")
        
        serializer = ViewTestQuestionDetailSerializer(question)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class CreateMCQView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_mcq",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateMCQSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="MCQ Created Successfully", data=ViewTestQuestionDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class EditMCQView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_mcq",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        test_question = TestQuestions.objects.filter(id=cid).first()
        if test_question is None:
            raise serializers.ValidationError("Invalid MCQ ID!")
        
        serializer = EditMCQSerializer(test_question, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="MCQ Updated Successfully", data=ViewTestQuestionDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class UpdateMCQStatusView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_mcq",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        test_question = TestQuestions.objects.filter(id=cid).first()
        if test_question is None:
            raise serializers.ValidationError("Invalid MCQ ID!")
        
        serializer = ChangeQuestionStatusSerializer(test_question, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="MCQ Status Updated Successfully", data=ViewTestQuestionDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteMCQView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_mcq",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            question = TestQuestions.objects.get(id = cid)
            QuestionContents.objects.filter(test_question_id = question.id).delete()
            QuestionOptions.objects.filter(test_question_id = question.id).delete()
            question.delete()
            return success_response(message="MCQ Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except TestQuestions.DoesNotExist:
            return error_response(message="MCQ not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        


class ImportMCQsView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_mcq",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = ImportMCQSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):

            excel_file = serializer.validated_data['excel_file']
            try:
                imported_question_ids = []

                colnames=['topic', 'question_no', 'pass_percentage','level','e_question','option_1','option_2','option_3',"option_4","right_option",'e_solution']

                df = pd.read_excel(excel_file, names=colnames, skiprows=4)
                with transaction.atomic():
                    for index, row in df.iterrows():
                        print(str(row.get('question_no', '')).strip())
                        row_number = index
                        question_id_number = str(row.get('question_no', '')).strip()
                        question_text = str(row.get('e_question', '')).strip()
                        solution_description = str(row.get('e_solution', '')).strip()
                        
                        right_option_index_raw = row.get('right_option', '')
                        if pd.isna(right_option_index_raw) or str(right_option_index_raw).strip() == '':
                            right_option_index = None
                        else:
                            try:
                                right_option_index = int(float(str(right_option_index_raw).strip())) 

                                if not (1 <= right_option_index <= 4):
                                    raise ValueError(f"Right option index must be between 1 and 4.")
                            except (ValueError, TypeError):
                                raise ValueError(f"Row {row_number}: 'right_option' must be a number (1, 2, 3, or 4). Found '{right_option_index_raw}'.")
                        

                        if not question_text:
                            raise ValueError(f"Row {row_number}: 'e_question' (Question Text) cannot be empty.")
                        
                        topic_name = str(row.get('topic', '')).strip()

                        if question_id_number:
                            test_question_instance, created_question = TestQuestions.objects.get_or_create(
                                id_number=question_id_number,
                                chapter_id = topic_name,
                                defaults={
                                    'question_type': QuestionType.MCQ, 
                                    'level': row.get('level', 1),
                                    'pass_percentage': int(row.get('pass_percentage', 0.0)  * 100 ),
                                    'status': True
                                }
                            )
                            if not created_question: 
                                test_question_instance.question_type = QuestionType.MCQ
                                test_question_instance.level = row.get('level', 1)
                                test_question_instance.pass_percentage = int(row.get('pass_percentage', 0.0)  * 100)
                                test_question_instance.status = True
                        else:
                            # If no ID Number is provided, always create a new TestQuestions
                            test_question_instance = TestQuestions.objects.create(
                                question_type = QuestionType.MCQ,
                                level = row.get('level', 1),
                                pass_percentage = int(row.get('pass_percentage', 0.0)  * 100 ),
                                status = True
                            )

                        chapter = None

                        if topic_name:
                            try:
                                chapter = Chapters.objects.get(id=topic_name)
                            except Chapters.DoesNotExist:
                                raise ValueError(f"Row {row_number}: Topic '{topic_name}' not found in the database. Please ensure it exists.")
                        else:
                            raise ValueError(f"Row {row_number}: Topic '{topic_name}' is missing")
                        
                        test_question_instance.chapter = chapter
                        test_question_instance.save()

                        question_contents_instance, created_content = QuestionContents.objects.get_or_create(
                            test_question=test_question_instance,
                            defaults={
                                'question': question_text,
                                'solution_description': solution_description
                            }
                        )
                        if not created_content: # If exists, update
                            question_contents_instance.question = question_text
                            question_contents_instance.solution_description = solution_description
                            question_contents_instance.save()


                        current_options = test_question_instance.questionoptions_set.filter(deleted_at=None).order_by('id')
                        existing_options_count = current_options.count()

                        options_instances = []
                        right_option_instance = None 

                        excel_options_list = [] 
                        for j in range(1, 5):
                            option_text = str(row.get(f'option_{j}', '')).strip()
                            excel_options_list.append(option_text) 

                        
                        correct_option_text_from_excel = None
                        if right_option_index is not None and 0 < right_option_index <= len(excel_options_list):
                            correct_option_text_from_excel = excel_options_list[right_option_index - 1] # -1 for 0-indexing
                            if not correct_option_text_from_excel: # Check if the referenced option text is actually present
                                raise ValueError(f"Row {row_number}: 'right_option' index {right_option_index} points to an empty option.")
                        elif right_option_index is not None and right_option_index > len(excel_options_list) and excel_options_list:
                             raise ValueError(f"Row {row_number}: 'right_option' index {right_option_index} is out of bounds for the provided options ({len(excel_options_list)} options found).")


                        actual_excel_options_processed_count = 0
                        for i, option_text_from_excel in enumerate(excel_options_list):
                            if not option_text_from_excel: 
                                continue 

                            option_obj = None
                            if actual_excel_options_processed_count < existing_options_count:
                                option_obj = current_options[actual_excel_options_processed_count]
                                option_obj.option = option_text_from_excel
                                if option_obj.deleted_at:
                                    option_obj.deleted_at = None
                                option_obj.save()
                            else:
                                option_obj = QuestionOptions.objects.create(
                                    test_question=test_question_instance,
                                    option=option_text_from_excel
                                )
                            options_instances.append(option_obj) # Add to list of options actually processed

                            if option_obj.option == correct_option_text_from_excel: # Compare actual text
                                right_option_instance = option_obj
                            
                            actual_excel_options_processed_count += 1


                        if existing_options_count > actual_excel_options_processed_count:
                            for j in range(actual_excel_options_processed_count, existing_options_count):
                                option_to_delete = current_options[j]
                                if not option_to_delete.deleted_at:
                                    option_to_delete.deleted_at = datetime.now()
                                    option_to_delete.save()

                        if right_option_index is not None and right_option_instance is None:
                            if correct_option_text_from_excel: 

                                raise ValueError(f"Row {row_number}: Internal error: Correct option text '{correct_option_text_from_excel}' was identified but no corresponding option object was found/created. This might indicate a logic flaw.")
                            else: 
                                raise ValueError(f"Row {row_number}: 'right_option' index {right_option_index} is invalid or points to an empty option. No correct option identified.")
                        elif right_option_index is None and actual_excel_options_processed_count > 0:
                            raise ValueError(f"Row {row_number}: Options are provided but 'right_option' (index) is missing.")
                        elif actual_excel_options_processed_count == 0 and right_option_index is not None:
                            raise ValueError(f"Row {row_number}: 'right_option' index provided but no Options (option_X) found in row.")
                        elif actual_excel_options_processed_count == 0 and right_option_index is None:
                            pass 

                        test_question_instance.right_option = right_option_instance
                        test_question_instance.save()
                        print(test_question_instance.id)
                        imported_question_ids.append(test_question_instance.id)
                        
            except Exception as e:
                return error_response(message="failed", data = {"error": f"Error processing Excel file: {str(e)}"}, status_code=status.HTTP_400_BAD_REQUEST)

            return success_response(message="MCQ Created Successfully", data={"imported_question_ids": imported_question_ids}, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class GetChapterQuizListingView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_quiz_listing",
                            [SuperAdmin]
                        )]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name',"chapter__name"]
    ordering_fields = ['description',"name", 'id', 'status',"chapter__name"]
    def get(self, request, format=None):
        question = ChapterQuizs.objects.all()

        chapter_id = request.query_params.get('chapter_id')
        if chapter_id:
            question = question.filter(chapter_id=chapter_id)

        
        name = request.query_params.get('name')
        if name:
            question = question.filter(name__icontains=name)

        description = request.query_params.get('description')
        if description:
            question = question.filter(description__icontains=description)
        
        active = request.query_params.get('status')
        if active:
            question = question.filter(status=active)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                question = question.filter(created_at__gte=start_datetime)
            except ValueError:
                raise ValidationError("Invalid start_date format. Use YYYY-MM-DD.")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                question = question.filter(created_at__lte=end_datetime)
            except ValueError:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.")


        search_filter = filters.SearchFilter()
        question = search_filter.filter_queryset(request, question, self)

        ordering_filter = filters.OrderingFilter()
        question = ordering_filter.filter_queryset(request, question, self)

        if not question.ordered:
            question = question.order_by('-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(question, request, view=self)
        serializer = GetChapterQuizListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class ViewChapterQuizDetailView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "chapter_quiz_listing",
                            [SuperAdmin]
                        )]
    def get(self, request,  cid , format=None):
        question = ChapterQuizs.objects.filter(id=cid).first()
        if question is None:
            raise serializers.ValidationError("Invalid Quiz ID!")
        
        serializer = ViewChapterQuizDetailSerializer(question)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class CreateChapterQuizView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_chapter_quiz",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = CreateChapterQuizSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Quiz Created Successfully", data=ViewChapterQuizDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class EditChapterQuizView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter_quiz",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        test_question = ChapterQuizs.objects.filter(id=cid).first()
        if test_question is None:
            raise serializers.ValidationError("Invalid Quiz ID!")
        
        serializer = EditMCQSerializer(test_question, data = request.data, partial=True)
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Quiz Updated Successfully", data=ViewChapterQuizDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class UpdateChapterQuizStatusView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "update_chapter_quiz",
                            [SuperAdmin]
                        )]
    def post(self, request,  cid , format=None):
        test_question = ChapterQuizs.objects.filter(id=cid).first()
        if test_question is None:
            raise serializers.ValidationError("Invalid Quiz ID!")
        
        serializer = ChangeChapterQuizStatusSerializer(test_question, data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Quiz Status Updated Successfully", data=ViewChapterQuizDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class DeleteChapterQuizView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "delete_chapter_quiz",
                            [SuperAdmin]
                        )]
    def delete(self, request, cid, format=None):
        try:
            question = ChapterQuizs.objects.get(id = cid)
            question.delete()
            return success_response(message="Quiz Deleted Successfully", data={"id":cid}, status_code=status.HTTP_200_OK)
        except ChapterQuizs.DoesNotExist:
            return error_response(message="Quiz not found", data = [], status_code=status.HTTP_400_BAD_REQUEST)
        


class GetMCQsListView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "mcq_listing",
                            [SuperAdmin]
                        )]
    def get(self, request,  cid , format=None):
        question = ChapterQuizs.objects.filter(id=cid).first()
        if question is None:
            raise serializers.ValidationError("Invalid Quiz ID!")
        
        question_list = TestQuestions.objects.filter(chapter = question.chapter)
        serializer = MCQListingSerializer(question_list, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class AssignMCQChapterQuizView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_permission_or_roles(
                              "create_chapter_quiz",
                            [SuperAdmin]
                        )]
    def post(self, request, format=None):
        serializer = AssignMCQsChapterQuizSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="MCQs Assigned Successfully", data=ViewChapterQuizDetailSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    


class GetChapterQuizListView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request,  cid , format=None):
        question = ChapterQuizs.objects.filter(chapter_id=cid)
        serializer = GetChapterQuizListSerializer(question, many=True)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class StartPracticeTestView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        serializer = StartPracticeTestSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Quiz Created Successfully!", data=PracticeTestQuestionsSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetPracticeTestQuestionsView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request,  cid , format=None):
        question = PracticeTests.objects.filter(id=cid, user = request.user).first()
        if question is None:
            raise serializers.ValidationError("Invalid Quiz ID!")
        serializer = PracticeTestQuestionsSerializer(question)
        return success_response(message="success", data=serializer.data, status_code=status.HTTP_200_OK)
    

class SubmitPracticeTestAnswerView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        serializer = SubmitPracticeTestAnswerSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Answer Saved Successfully!", data=PracticeTestQuestionResultDetailsSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

class GetPracticeTestResultView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, tid):
        test = PracticeTests.objects.filter(id = tid, user = request.user).first()
        if test is None:
            raise ValidationError("Invalid Test ID!")
        serializer = PracticeTestResultsSerializer(test)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class GetCompletedPracticeTestsView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def get(self, request, cid, chap_id, quiz_id):
        test = PracticeTests.objects.filter(course_id = cid, chapter_id =chap_id ,quiz_id = quiz_id,   user = request.user).order_by("-id")
        serializer = PracticeTestListingSerializer(test,many=True)
        return success_response(message="Success", data=serializer.data, status_code=status.HTTP_200_OK)
    


class RestartPracticeTestView(APIView):
    renderer_classes = [QuestionRenderer]
    permission_classes = [IsAuthenticated, 
                          RoleOrPermissionCheck.for_roles(
                            [Student]
                        )]
    def post(self, request, format=None):
        serializer = RestartPracticeTestSerializer(data = request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception = True):
            user = serializer.save()
            return success_response(message="Quiz Created Successfully!", data=PracticeTestQuestionsSerializer(user).data, status_code=status.HTTP_200_OK)
        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)