from rest_framework import serializers
from questions.models import *
from courses.models import *
from django.db import transaction
from django.core.validators import FileExtensionValidator
import html2text
from mini_lms.utils import *
import random
from datetime import datetime, date, timedelta
from django.db.models import Sum, Count, Case, When, IntegerField,Avg, Q

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
    

class EditChaperQuizSerializer(serializers.ModelSerializer):
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


        return practice_test
    


class QuestionDetailsSerializer(serializers.ModelSerializer):
    question_detail = QuestionInfoSerializer(source="questioncontents_set.first", read_only=True)
    options = QuestionOptionsSerializer(source="questionoptions_set", many=True, read_only=True)
    
    class Meta:
        model = TestQuestions
        fields = ['id', 'level', "id_number", "question_detail", "options"]
    
    def to_representation(self, instance):
        import random
        representation = super().to_representation(instance)
        if 'options' in representation and isinstance(representation['options'], list):
            random.shuffle(representation['options'])
        
        return representation
    
class PracticeTestQuestionDetailsSerializer(serializers.ModelSerializer):
    question_info = QuestionDetailsSerializer(source="question", read_only=True)
    selected_option = QuestionOptionsSerializer(read_only=True)

    class Meta:
        model = PracticeTestQuestions
        fields = ['id', "question_info", "result", "attempted", "time_taken","selected_option"]


class PracticeTestQuestionsSerializer(serializers.ModelSerializer):
    test_questions = serializers.SerializerMethodField('get_test_questions')
    def get_test_questions(self, obj):
        category = PracticeTestQuestions.objects.filter(practice_test_id=obj.id).order_by("id")
        return PracticeTestQuestionDetailsSerializer(category, many=True).data
    
    class Meta:
        model = PracticeTests
        fields = ['id','total_question','total_right_answer_given', 'total_wrong_answer_given','total_never_attempt_question',"total_time_taken","status","created_at","test_questions"]


class QuestionResultDetailsSerializer(serializers.ModelSerializer):
    question_detail = QuestionInfoSerializer(source="questioncontents_set.first", read_only=True)
    options = QuestionOptionsSerializer(source="questionoptions_set", many=True, read_only=True)
    
    class Meta:
        model = TestQuestions
        fields = ['id', 'level', "id_number", "question_detail", "options","right_option"]


class PracticeTestQuestionResultDetailsSerializer(serializers.ModelSerializer):
    question_info = QuestionResultDetailsSerializer(source="question", read_only=True)
    selected_option = QuestionOptionsSerializer(read_only=True)

    class Meta:
        model = PracticeTestQuestions
        fields = ['id', "question_info", "result", "attempted", "time_taken","selected_option"]



class SubmitPracticeTestAnswerSerializer(serializers.ModelSerializer):
    practice_test_id = serializers.IntegerField(required=True)
    question_id = serializers.IntegerField(required=True)
    selected_option_id = serializers.IntegerField(required=True, allow_null=True)
    time_taken = serializers.IntegerField(required=True)
    is_completed = serializers.BooleanField(required=True)

    class Meta:
        model = PracticeTestQuestions
        fields = ['practice_test_id',"question_id","selected_option_id","time_taken","is_completed"]

    
    def validate(self, data):

        attempt = data.get('practice_test_id')
        attempt_count = PracticeTests.objects.filter(id=attempt).count()
        if attempt_count == 0:
            raise serializers.ValidationError("Practice Test ID not found")
        
        question = PracticeTestQuestions.objects.filter(id = data.get('question_id')).first()
        if question is None:
            raise serializers.ValidationError("Invalid Question ID : "+str(data.get('question_id')))
        
        if data.get('selected_option_id') is None:
            raise serializers.ValidationError({"selected_option_id": "This field is required. Question ID : "+str(data.get('question_id'))})
            
        return data
    
    def create(self , validate_data):
        user = self.context.get('user')

        with transaction.atomic():
        
            question = PracticeTestQuestions.objects.get(id = validate_data.get("question_id"))
        
            result = False
            if question.question.right_option.id == validate_data.get("selected_option_id"):
                result = True

            question.selected_option = QuestionOptions.objects.get(id = validate_data.get("selected_option_id"))
            question.time_taken = validate_data.get("time_taken")
            question.attempted = True
            question.result = result
            question.save()

            
            test_question_list = PracticeTestQuestions.objects.filter(practice_test_id =validate_data.get("practice_test_id"))
            results1 = test_question_list.aggregate(
                        right_answer=Count(
                            Case(
                                When(result=True, attempted=True, then=1),
                                    output_field=IntegerField()
                            )
                        ),
                        wrong_answer=Count(
                            Case(
                                When(result=False, attempted=True, then=1),
                                output_field=IntegerField()
                            )
                        ),
                        not_attempted=Count(
                            Case(
                                When(attempted=False, then=1),
                                output_field=IntegerField()
                            )
                        ),
                        total_time=Sum('time_taken'),
                        average_time_per_question=Avg('time_taken'),
                        total_question=Count(
                            Case(
                                When(attempted=True, then=1),
                                output_field=IntegerField()
                            )
                        )
                    )

            test_info = PracticeTests.objects.filter(id=validate_data.get("practice_test_id")).first()

            total_question = PracticeTestQuestions.objects.only("id").filter(practice_test_id =validate_data.get("practice_test_id")).count()

            right_practice = PracticeTestQuestions.objects.only("id").filter(practice_test_id =validate_data.get("practice_test_id"), attempted = True, result = 1).count()

            mcq_score = 0
            if total_question > 0:
                mcq_score =  custom_round(right_practice * 100 / total_question)

            test_info.total_right_answer_given = results1['right_answer']
            test_info.total_wrong_answer_given = results1['wrong_answer']
            test_info.total_never_attempt_question = results1['not_attempted']
            test_info.total_time_taken = results1['total_time']
            test_info.avg_time_per_question = results1['average_time_per_question']
            test_info.score = custom_round(mcq_score)

            if test_info.total_question == results1['total_question'] or validate_data.get("is_completed", False):
                test_info.status = True
                test_info.end_time = datetime.now()

            test_info.save()

        
        return question
    

class PracticeTestResultsSerializer(serializers.ModelSerializer):
    test_questions = serializers.SerializerMethodField('get_test_questions')
    def get_test_questions(self, obj):
        category = PracticeTestQuestions.objects.filter(practice_test_id=obj.id).order_by("id")
        return PracticeTestQuestionResultDetailsSerializer(category, many=True).data
    
    class Meta:
        model = PracticeTests
        fields = ['id','total_question','total_right_answer_given', 'total_wrong_answer_given','total_never_attempt_question',"total_time_taken","status","created_at","test_questions"]



class PracticeTestListingSerializer(serializers.ModelSerializer):
    result = serializers.SerializerMethodField('get_result')
    def get_result(self, obj):
        if obj.quiz.pass_percentage > obj.score:
            return "Fail"
        return "Pass"

    class Meta:
        model = PracticeTests
        fields = ['id','start_time','status',"result", 'score',"created_at"]



class RestartPracticeTestSerializer(serializers.ModelSerializer):
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
        
        PracticeTests.objects.filter(
            course = course,
            user = user,
            chapter = quiz_info.chapter,
            quiz = quiz_info,
            status = False
        ).delete()


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


        return practice_test