from rest_framework import serializers
from .models import (
    Category, Course, CourseInstructor, Module, Lesson,
    Resource, Assessment, Question, Answer, Enrollment,
    Progress, AssessmentAttempt, AttemptAnswer, Review,
    Note, Certificate
)
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model providing basic user information"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Course Categories"""
    class Meta:
        model = Category
        fields = '__all__'


class ResourceSerializer(serializers.ModelSerializer):
    """Serializer for Lesson Resources"""
    class Meta:
        model = Resource
        fields = '__all__'


class AnswerSerializer(serializers.ModelSerializer):
    """Serializer for Question Answers (without showing correct answer)"""
    class Meta:
        model = Answer
        fields = ['id', 'answer_text', 'explanation']


class AnswerDetailSerializer(serializers.ModelSerializer):
    """Detailed Answer serializer including correctness (for instructors/admins)"""
    class Meta:
        model = Answer
        fields = ['id', 'answer_text', 'is_correct', 'explanation']


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for Questions including their answers"""
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'question_text', 'question_type',
                  'order', 'points', 'answers']


class QuestionDetailSerializer(serializers.ModelSerializer):
    """Detailed Question serializer showing answer correctness"""
    answers = AnswerDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'question_text', 'question_type',
                  'order', 'points', 'answers']


class AssessmentSerializer(serializers.ModelSerializer):
    """Serializer for Assessments including their questions"""
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Assessment
        fields = ['id', 'title', 'description',
                  'time_limit', 'passing_score', 'questions']


class LessonSerializer(serializers.ModelSerializer):
    """Serializer for Lessons including their resources"""
    resources = ResourceSerializer(many=True, read_only=True)
    has_assessment = serializers.BooleanField(read_only=True)

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content', 'duration', 'type', 'order',
                  'has_assessment', 'has_lab', 'is_free_preview', 'resources']


class ModuleSerializer(serializers.ModelSerializer):
    """Basic Module serializer with lesson count"""
    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ['id', 'title', 'description',
                  'order', 'duration', 'lessons_count']

    def get_lessons_count(self, obj):
        """Get the number of lessons in this module"""
        return obj.lessons.count()


class ModuleDetailSerializer(serializers.ModelSerializer):
    """Detailed Module serializer including lesson details"""
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'duration', 'lessons']


class CourseInstructorSerializer(serializers.ModelSerializer):
    """Serializer for Course-Instructor relationship"""
    instructor = UserSerializer(read_only=True)

    class Meta:
        model = CourseInstructor
        fields = ['instructor', 'title', 'bio', 'is_lead']


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for basic Course information"""
    category = CategorySerializer(read_only=True)
    rating = serializers.FloatField(read_only=True)
    enrolled_students = serializers.IntegerField(read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    # Define formatted_price as a SerializerMethodField
    formatted_price = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'subtitle', 'slug', 'description', 'category',
                  'thumbnail', 'price', 'discount_price', 'formatted_price', 'discount_ends',
                  'level', 'duration', 'has_certificate', 'is_featured',
                  'published_date', 'updated_date', 'rating', 'enrolled_students',
                  'is_enrolled']

    def get_is_enrolled(self, obj):
        """Check if current user is enrolled in this course"""
        request = self.context.get('request')
        # Add extra null/authentication checks to prevent errors
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.enrollments.filter(user=request.user).exists()
        return False

    def get_formatted_price(self, obj):
        """Format the price with currency symbol"""
        currency = self.context.get('currency', 'INR')
        if currency == 'INR':
            return f"₹{obj.price}"
        return f"${obj.price}"


class CourseDetailSerializer(serializers.ModelSerializer):
    """Detailed Course serializer for single course view"""
    category = CategorySerializer(read_only=True)
    instructors = CourseInstructorSerializer(many=True, read_only=True)
    modules = ModuleSerializer(many=True, read_only=True)
    rating = serializers.FloatField(read_only=True)
    enrolled_students = serializers.IntegerField(read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    formatted_price = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'subtitle', 'slug', 'description', 'category',
                  'thumbnail', 'price', 'formatted_price', 'discount_price', 'discount_ends',
                  'level', 'duration', 'has_certificate', 'requirements', 'skills',
                  'published_date', 'updated_date', 'rating', 'enrolled_students',
                  'instructors', 'modules', 'is_enrolled', 'user_progress']

    def get_is_enrolled(self, obj):
        """Check if current user is enrolled in this course"""
        request = self.context.get('request')
        # Add extra null/authentication checks to prevent errors
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.enrollments.filter(user=request.user).exists()
        return False

    def get_user_progress(self, obj):
        """Get user's progress for this course if enrolled"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                enrollment = Enrollment.objects.get(
                    user=request.user, course=obj)
                completed_lessons = Progress.objects.filter(
                    enrollment=enrollment, is_completed=True
                ).count()
                total_lessons = Lesson.objects.filter(
                    module__course=obj).count()
                if total_lessons > 0:
                    percentage = (completed_lessons / total_lessons) * 100
                    return {
                        'completed': completed_lessons,
                        'total': total_lessons,
                        'percentage': round(percentage, 1)
                    }
            except Enrollment.DoesNotExist:
                pass
            except Exception as e:
                # Log error but don't crash
                print(f"Error getting user progress: {str(e)}")
        return None

    def get_formatted_price(self, obj):
        """Format the price with currency symbol"""
        currency = self.context.get('currency', 'INR')
        if currency == 'INR':
            return f"₹{obj.price}"
        return f"${obj.price}"


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for user enrollments"""
    user = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'user', 'course', 'enrolled_date', 'last_accessed',
                  'status', 'completion_date']


class ProgressSerializer(serializers.ModelSerializer):
    """Serializer for user lesson progress"""
    lesson = LessonSerializer(read_only=True)

    class Meta:
        model = Progress
        fields = ['id', 'lesson', 'is_completed',
                  'completed_date', 'time_spent']


class AttemptAnswerSerializer(serializers.ModelSerializer):
    """Serializer for user answers in assessment attempts"""
    question = QuestionSerializer(read_only=True)
    selected_answer = AnswerSerializer(read_only=True)

    class Meta:
        model = AttemptAnswer
        fields = ['id', 'question', 'selected_answer', 'text_answer',
                  'is_correct', 'points_earned']


class AssessmentAttemptSerializer(serializers.ModelSerializer):
    """Serializer for user assessment attempts"""
    answers = AttemptAnswerSerializer(many=True, read_only=True)
    assessment = AssessmentSerializer(read_only=True)
    score_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = AssessmentAttempt
        fields = ['id', 'assessment', 'start_time', 'end_time',
                  'score', 'score_percentage', 'passed', 'answers']


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for course reviews"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'title', 'content',
                  'date_created', 'helpful_count']


class NoteSerializer(serializers.ModelSerializer):
    """Serializer for user notes"""
    class Meta:
        model = Note
        fields = ['id', 'lesson', 'content', 'created_date', 'updated_date']


class CertificateSerializer(serializers.ModelSerializer):
    """Serializer for course completion certificates"""
    enrollment = EnrollmentSerializer(read_only=True)

    class Meta:
        model = Certificate
        fields = ['id', 'enrollment', 'issue_date', 'certificate_number']
