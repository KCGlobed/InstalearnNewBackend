from rest_framework import serializers
from questions.models import *
from courses.models import *
from django.db import transaction
from django.core.validators import FileExtensionValidator
import html2text
from mini_lms.utils import *
import random

class MCQListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestQuestions
        fields = ["id","id_number","level","pass_percentage","status","created_at"]


class ChapterInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapters
        fields = ["id","name"]

class QuestionInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionContents
        fields = ["id","question","solution_description"]

class QuestionOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOptions
        fields = ["id","option"]
        

class ViewTestQuestionDetailSerializer(serializers.ModelSerializer):
    chapter = serializers.SerializerMethodField('get_chapter')
    question_detail = serializers.SerializerMethodField('get_question_detail')
    options = serializers.SerializerMethodField('get_options')
    right_option = serializers.SerializerMethodField('get_right_option')
    
    def get_right_option(self, obj):
        if obj.right_option is None:
            return []
        option = QuestionOptions.objects.filter(id=obj.right_option.id).first()
        return QuestionOptionsSerializer(option).data
    
    def get_options(self, obj):
        option = QuestionOptions.objects.filter(test_question_id=obj.id)
        return QuestionOptionsSerializer(option, many=True).data

    def get_question_detail(self, obj):
        question = QuestionContents.objects.filter(test_question_id=obj.id).first()
        return QuestionInfoSerializer(question).data
    
    def get_chapter(self, obj):
        if obj.chapter is None:
            return []
        category = Chapters.objects.filter(id=obj.chapter.id).first()
        return ChapterInfoSerializer(category).data
    
    class Meta:
        model = TestQuestions
        fields = ["id","id_number","level","pass_percentage","chapter","status","question_detail","options","right_option","created_at"]



class CreateMCQSerializer(serializers.ModelSerializer) :
    id_number = serializers.CharField(max_length = 255, required=True)
    level = serializers.ChoiceField(required=True,choices=Level)
    pass_percentage = serializers.IntegerField(required=True)
    chapter_id = serializers.IntegerField(required=True)
    question = serializers.CharField(required=True)
    solution_description = serializers.CharField(required=True)
    options = serializers.ListField(
                            child=serializers.CharField(required=True),
                            min_length=4,
                            max_length=4,
                            allow_empty=False,
                            required=True)
    right_option = serializers.ChoiceField(required=True,choices=[1,2,3,4])

    class Meta:
        model = TestQuestions
        fields = ['id_number','level','pass_percentage','chapter_id',"question","solution_description","options","right_option"]
        
    def validate(self, data):
        topic_count = Chapters.objects.filter(id=data.get('chapter_id')).count()
        if topic_count == 0:
            raise serializers.ValidationError("Chapter ID not found")
        
        question_count = TestQuestions.objects.filter(id_number=data.get('id_number'), chapter_id = data.get('chapter_id')).count()
        if question_count > 0:
            raise serializers.ValidationError("ID Number already exists")

        return data

    def create(self , validate_data):
        try:
            with transaction.atomic():

                chapter_info = Chapters.objects.get(id=validate_data.get('chapter_id'))
                test_question = TestQuestions(
                    id_number = validate_data.get('id_number'),
                    level = validate_data.get('level'),
                    pass_percentage = validate_data.get('pass_percentage'),
                    chapter = chapter_info,
                    question_type = QuestionType.MCQ,
                    status = True
                )
                test_question.save()

                question_content = QuestionContents(
                    test_question = test_question,
                    question = validate_data.get('question'),
                    solution_description = validate_data.get('solution_description')
                )
                question_content.save()

                options_instances = []
                for i, option_text in enumerate(validate_data.get('options')):

                    current_option = QuestionOptions(
                        test_question=test_question,
                        option=option_text
                    )
                    current_option.save()
                    options_instances.append(current_option)

                right_option_index = int(validate_data.get('right_option')) - 1 
                if 0 <= right_option_index < len(options_instances):
                    test_question.right_option = options_instances[right_option_index]
                else:
                    raise serializers.ValidationError("Right Option is not Matched")
                
                test_question.save()

        except ValueError as ve:
            raise serializers.ValidationError(f"An error occurred: {ve}")
        except Exception as e:
            raise serializers.ValidationError(f"An error occurred while saving options/question: {e}")

        return test_question
    

class EditMCQSerializer(serializers.ModelSerializer):
    id_number = serializers.CharField(max_length = 255, required=True)
    level = serializers.ChoiceField(required=False,choices=Level)
    pass_percentage = serializers.IntegerField(required=False)
    chapter_id = serializers.IntegerField(required=False)
    question = serializers.CharField(required=False)
    solution_description = serializers.CharField(required=False)
    options = serializers.ListField(
                            child=serializers.CharField(required=False),
                            min_length=4,
                            max_length=4,
                            allow_empty=True,
                            required=False)
    right_option = serializers.ChoiceField(required=False,choices=[1,2,3,4])

    class Meta:
        model = TestQuestions
        fields = ['id_number','level','pass_percentage','chapter_id',"question","solution_description","options","right_option"]
        
    def validate(self, data):
        parent = data.get('chapter_id', None) 
        if parent is not None:
            topic_count = Chapters.objects.filter(id=data.get('chapter_id')).count()
            if topic_count == 0:
                raise serializers.ValidationError("Chapter ID not found")

        return data


    @transaction.atomic
    def update(self , question, validate_data):
        question_count = TestQuestions.objects.filter(id_number=validate_data.get('id_number'), chapter_id = validate_data.get('chapter_id')).exclude(id = question.id).count()
        if question_count > 0:
            raise serializers.ValidationError("ID Number already exists")
        

        chapter_id = validate_data.get('chapter_id', None) 
        if chapter_id is not None:
            question.chapter = Chapters.objects.get(id=validate_data.get('chapter_id'))

        question.id_number = validate_data.get('id_number', question.id_number)
        question.level = validate_data.get('level', question.level)
        question.pass_percentage = validate_data.get('pass_percentage', question.pass_percentage)
        question.save()

        content = QuestionContents.objects.filter(test_question_id = question.id).first()
        content.question = validate_data.get('question', content.question)
        content.solution_description = validate_data.get('solution_description', content.solution_description)
        content.save()

        options_data = validate_data.pop('options', None)

        options_instances = []
        if options_data is not None:
            current_options = question.questionoptions_set.all() # Use _set or related_name

            for i, option_text in enumerate(options_data):
                option = current_options[i]
                option.option = option_text
                option.save()
                options_instances.append(option)


        right_option_index = validate_data.get('right_option', None)
        if right_option_index is not None:
            right_option_index = int(validate_data.get('right_option')) - 1 
            if 0 <= right_option_index < len(options_instances):
                question.right_option = options_instances[right_option_index]
            else:
                raise serializers.ValidationError("Right Option is not Matched")
        
        question.save()

        return question


class ChangeQuestionStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = TestQuestions
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()
        return category
    

class ImportMCQSerializer(serializers.ModelSerializer) :
    excel_file = serializers.FileField(required=True, validators=[FileExtensionValidator( ['xlsx','xls'])])
    
    class Meta:
        model = TestQuestions
        fields = ['excel_file']
        
    def validate(self, data):
        return data


class GetChapterQuizListSerializer(serializers.ModelSerializer):
    chapter = serializers.SerializerMethodField('get_chapter')
    total_question = serializers.SerializerMethodField('get_total_question')
    
    def get_total_question(self, obj):
        option = QuizQuestions.objects.filter(chapter_quiz_id=obj.id).count()
        return option
    
    
    def get_chapter(self, obj):
        if obj.chapter is None:
            return []
        category = Chapters.objects.filter(id=obj.chapter.id).first()
        return ChapterInfoSerializer(category).data
    
    class Meta:
        model = ChapterQuizs
        fields = ["id","name","description","thumbnail","chapter","status","pass_percentage","total_question","created_at"]


    

class ViewQuizQuestionDetailSerializer(serializers.ModelSerializer):
    question_detail = serializers.SerializerMethodField('get_question_detail')

    def get_question_detail(self, obj):
        question = QuestionContents.objects.filter(test_question_id=obj.id).first()
        return QuestionInfoSerializer(question).data
    
    class Meta:
        model = TestQuestions
        fields = ["id","id_number","question_detail"]


class QuizQuestionsSerializer(serializers.ModelSerializer):
    question_detail = serializers.SerializerMethodField('get_question_detail')

    def get_question_detail(self, obj):
        question = TestQuestions.objects.filter(id=obj.test_question.id).first()
        return ViewQuizQuestionDetailSerializer(question).data
    
    class Meta:
        model = QuizQuestions
        fields = ["id","question_detail"]


class ViewChapterQuizDetailSerializer(serializers.ModelSerializer):
    chapter = serializers.SerializerMethodField('get_chapter')
    total_question = serializers.SerializerMethodField('get_total_question')
    quiz_questions = serializers.SerializerMethodField('get_quiz_questions')
    
    def get_quiz_questions(self, obj):
        option = QuizQuestions.objects.filter(chapter_quiz_id=obj.id)
        return QuizQuestionsSerializer(option, many=True).data
    
    def get_total_question(self, obj):
        option = QuizQuestions.objects.filter(chapter_quiz_id=obj.id).count()
        return option
    
    def get_chapter(self, obj):
        if obj.chapter is None:
            return []
        category = Chapters.objects.filter(id=obj.chapter.id).first()
        return ChapterInfoSerializer(category).data
    
    class Meta:
        model = ChapterQuizs
        fields = ["id","name","description","thumbnail","chapter","status","pass_percentage","total_question","quiz_questions","created_at"]



class CreateChapterQuizSerializer(serializers.ModelSerializer) :
    name = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(required=True)
    pass_percentage = serializers.IntegerField(required=True)
    chapter_id = serializers.IntegerField(required=True)
    thumbnail = serializers.FileField(required=False,allow_null=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp","svg"])])


    class Meta:
        model = ChapterQuizs
        fields = ['name','description','pass_percentage','chapter_id',"thumbnail"]
        
    def validate(self, data):
        topic_count = Chapters.objects.filter(id=data.get('chapter_id')).count()
        if topic_count == 0:
            raise serializers.ValidationError("Chapter ID not found")
        
        return data

    def create(self , validate_data):
        chapter_info = Chapters.objects.get(id=validate_data.get('chapter_id'))
        test_question = ChapterQuizs(
            name = validate_data.get('name'),
            description = validate_data.get('description'),
            pass_percentage = validate_data.get('pass_percentage'),
            thumbnail = validate_data.get('thumbnail'),
            chapter = chapter_info
        )
        test_question.save()
        return test_question
    

class EditMCQSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length = 255, required=True)
    description = serializers.CharField(required=True)
    pass_percentage = serializers.IntegerField(required=True)
    chapter_id = serializers.IntegerField(required=True)
    thumbnail = serializers.FileField(required=False,allow_null=True, validators=[FileExtensionValidator( ['png','jpg','jpeg',"webp","svg"])])


    class Meta:
        model = ChapterQuizs
        fields = ['name','description','pass_percentage','chapter_id',"thumbnail"]
        
    def validate(self, data):
        topic_count = Chapters.objects.filter(id=data.get('chapter_id')).count()
        if topic_count == 0:
            raise serializers.ValidationError("Chapter ID not found")
        
        return data

    def update(self , question, validate_data):
        chapter_id = validate_data.get('chapter_id', None) 
        if chapter_id is not None:
            question.chapter = Chapters.objects.get(id=validate_data.get('chapter_id'))

        question.name = validate_data.get('name', question.name)
        question.description = validate_data.get('description', question.description)
        question.pass_percentage = validate_data.get('pass_percentage', question.pass_percentage)
        question.thumbnail = validate_data.get('thumbnail', question.thumbnail)
        question.save()

        return question
    

class ChangeChapterQuizStatusSerializer(serializers.ModelSerializer) :
    status = serializers.BooleanField(required=True)
    class Meta:
        model = ChapterQuizs
        fields = ['status']
        
    def validate(self, data):
        return data

    def update(self , category, validate_data):
        category.status = validate_data.get('status', category.status)
        category.save()
        return category
    

class AssignMCQsChapterQuizSerializer(serializers.ModelSerializer) :
    quiz_id = serializers.IntegerField(required=True)
    mcq_ids = serializers.ListField(
                            child=serializers.IntegerField(required=True),
                            min_length=5,
                            required=True)

    class Meta:
        model = QuizQuestions
        fields = ['quiz_id','mcq_ids']
        
    def validate(self, data):
        return data

    def create(self , validate_data):
        question = ChapterQuizs.objects.get(id=validate_data.get('quiz_id'))
        if validate_data.get('mcq_ids') is not None:
            QuizQuestions.objects.filter(chapter_quiz_id = validate_data.get('quiz_id')).delete()
            for i, option_text in enumerate(validate_data.get('mcq_ids')):
                option = QuizQuestions(
                    chapter_quiz = question,
                    test_question_id = option_text,
                )
                option.save()

        return question
    


class StartPracticeTestSerializer(serializers.ModelSerializer):
    quiz_id = serializers.IntegerField(required=True)
    course_id = serializers.IntegerField(required=True)
    
    class Meta:
        model = ChapterQuizs
        fields = ['quiz_id',"course_id"]


    def validate(self, data):
        return data
    

    def create(self , validate_data):
        user = self.context.get('user')
        course = Course.objects.get(id=validate_data.get('course_id'))
        quiz_info = ChapterQuizs.objects.get(id=validate_data.get('quiz_id'))
        question_ids = list(QuizQuestions.objects.filter(
            chapter_quiz_id=validate_data.get('quiz_id')
        ).values_list('id', flat=True))

        random.shuffle(question_ids)
        random.shuffle(question_ids)
        quiz_questions = QuizQuestions.objects.filter(id__in=question_ids)

        practice_test = PracticeTests(
            course = course,
            user = user,
            total_question = len(quiz_questions),
            total_never_attempt_question = len(quiz_questions),
            chapter = quiz_info.chapter,
            quiz = quiz_info
        )
        practice_test.save()

        for questions in quiz_questions:
            info = PracticeTestQuestions(
                    user = user,
                    practice_test = practice_test,
                    question = questions.test_question,
                )
            info.save()


        return True