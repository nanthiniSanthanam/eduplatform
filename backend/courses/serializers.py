"""
File: backend/courses/serializers.py
Purpose: Serializers for converting courses app models to JSON for the API

Key serializers:
- CategorySerializer: For course categories
- CourseSerializer: Basic course information
- CourseDetailSerializer: Extended course information with modules and progress
- ModuleSerializer: Course modules/sections
- LessonSerializer: Lesson content with tiered access control
- ResourceSerializer: Learning materials
- AssessmentSerializer: Quiz and test information
- QuestionSerializer: Assessment questions
- EnrollmentSerializer: Student enrollments
- ProgressSerializer: Student progress tracking
- CertificateSerializer: Course completion certificates

Modified for tiered access:
- LessonSerializer implements to_representation method for access control
- Added get_premium_resources method to filter resources by subscription
- Uses user_access_level context variable to control content visibility
- Uses utils.get_restricted_content_message for consistent messaging

Variables to modify:
- Access control logic in LessonSerializer.to_representation if access tiers change

Connected files:
1. backend/courses/views.py - Uses these serializers in API views
2. backend/courses/models.py - Models being serialized
3. backend/courses/utils.py - Utility functions for access control
4. frontend/src/services/api.js - Makes API calls to endpoints using these serializers
"""

from rest_framework import serializers
from .models import (
    Category, Course, Module, Lesson, Resource, Assessment, Question, Answer,
    Enrollment, Progress, AssessmentAttempt, AttemptAnswer, Review, Note, Certificate,
    CourseInstructor
)
from django.contrib.auth import get_user_model
from .utils import get_restricted_content_message

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for course categories"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'icon', 'slug']


class ResourceSerializer(serializers.ModelSerializer):
    """Serializer for lesson resources"""
    class Meta:
        model = Resource
        fields = ['id', 'title', 'type', 'file',
                  'url', 'description', 'premium']


class AnswerSerializer(serializers.ModelSerializer):
    """
    Basic answer serializer for students
    Intentionally excludes is_correct to prevent cheating
    """
    class Meta:
        model = Answer
        fields = ['id', 'answer_text']  # Don't expose is_correct to students


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for assessment questions"""
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'question_text', 'question_type', 'order', 'answers']


class QuestionDetailSerializer(serializers.ModelSerializer):
    """
    Detailed question serializer for instructors/admins
    Includes correct answer information
    """
    answers = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'question_text', 'question_type',
                  'order', 'points', 'answers']

    def get_answers(self, obj):
        answers = obj.answers.all()
        return [{
            'id': answer.id,
            'answer_text': answer.answer_text,
            'is_correct': answer.is_correct,
            'explanation': answer.explanation
        } for answer in answers]


class AssessmentSerializer(serializers.ModelSerializer):
    """Serializer for lesson assessments"""
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Assessment
        fields = ['id', 'title', 'description',
                  'time_limit', 'passing_score', 'questions']


class LessonSerializer(serializers.ModelSerializer):
    """
    Serializer for course lessons with tiered access control.

    This handles showing different content based on user's subscription level:
    - basic: Unregistered users get limited preview content
    - intermediate: Registered users get standard content
    - advanced: Paid subscribers get full premium content
    """
    resources = ResourceSerializer(many=True, read_only=True)
    premium_resources = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    assessment = AssessmentSerializer(read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'content', 'access_level', 'duration',
            'type', 'order', 'has_assessment', 'has_lab',
            'is_free_preview', 'resources', 'premium_resources',
            'is_completed', 'assessment'
        ]
        # Basic_content and intermediate_content aren't directly exposed
        # They're used in to_representation based on access level

    def get_is_completed(self, obj):
        """Check if the current user has completed this lesson"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        try:
            enrollment = Enrollment.objects.get(
                user=request.user,
                course=obj.module.course
            )
            # Check if progress record exists with is_completed=True
            progress = Progress.objects.filter(
                enrollment=enrollment,
                lesson=obj,
                is_completed=True
            ).exists()
            return progress
        except Enrollment.DoesNotExist:
            return False
        except Exception as e:
            print(f"Error determining lesson completion status: {e}")
            return False

    def get_premium_resources(self, obj):
        """Get resources accessible only to premium subscribers"""
        user_access_level = self.context.get('user_access_level', 'basic')

        # Only return premium resources for advanced access level
        if user_access_level != 'advanced':
            return []

        premium_resources = obj.resources.filter(premium=True)
        return ResourceSerializer(premium_resources, many=True, context=self.context).data

    def to_representation(self, instance):
        """Customize representation based on user access level"""
        data = super().to_representation(instance)
        user_access_level = self.context.get('user_access_level', 'basic')

        # Handle content based on access level
        lesson_access_level = instance.access_level

        # For advanced content, check user access
        if lesson_access_level == 'advanced' and user_access_level != 'advanced':
            # User doesn't have premium access, show intermediate content if available
            if instance.intermediate_content and user_access_level == 'intermediate':
                data['content'] = instance.intermediate_content
            elif instance.basic_content:
                data['content'] = instance.basic_content
            else:
                # Use utility function for restricted content message
                data['content'] = get_restricted_content_message(
                    instance.title, user_access_level)

        # For intermediate content, check if user is at least registered
        elif lesson_access_level == 'intermediate' and user_access_level == 'basic':
            if instance.basic_content:
                data['content'] = instance.basic_content
            else:
                # Use utility function for restricted content message
                data['content'] = get_restricted_content_message(
                    instance.title, user_access_level)

        # Add a flag indicating if the content is restricted
        data['is_restricted'] = (
            (lesson_access_level == 'advanced' and user_access_level != 'advanced') or
            (lesson_access_level == 'intermediate' and user_access_level == 'basic')
        )

        return data


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for course modules/sections with nested lessons"""
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'duration', 'lessons']


class ModuleDetailSerializer(serializers.ModelSerializer):
    """Detailed module serializer including lessons"""
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'duration', 'lessons']


class CourseInstructorSerializer(serializers.ModelSerializer):
    """Serializer for course instructor information"""
    instructor = serializers.SerializerMethodField()

    class Meta:
        model = CourseInstructor  # Fixed: was incorrectly using Module
        fields = ['instructor', 'title', 'bio', 'is_lead']

    def get_instructor(self, obj):
        user = obj.instructor
        return {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'username': user.username
        }


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for course information"""
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    instructors = CourseInstructorSerializer(many=True, read_only=True)
    rating = serializers.FloatField(read_only=True)
    enrolled_students = serializers.IntegerField(read_only=True)
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'subtitle', 'slug', 'description', 'category',
            'category_id', 'thumbnail', 'price', 'discount_price', 'discount_ends',
            'level', 'duration', 'has_certificate', 'is_featured',
            'published_date', 'updated_date', 'instructors', 'rating',
            'enrolled_students', 'is_enrolled'
        ]

    def get_is_enrolled(self, obj):
        """Check if the current user is enrolled in this course"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        return Enrollment.objects.filter(
            user=request.user,
            course=obj
        ).exists()


class CourseDetailSerializer(CourseSerializer):
    """Extended course serializer with detailed modules and user progress"""
    modules = ModuleSerializer(many=True, read_only=True)
    user_progress = serializers.SerializerMethodField()

    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + [
            'modules', 'user_progress', 'requirements', 'skills'
        ]

    def get_user_progress(self, obj):
        """Get the user's progress in this course"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        try:
            enrollment = Enrollment.objects.get(
                user=request.user,
                course=obj
            )

            # Get total and completed lessons
            total_lessons = Lesson.objects.filter(module__course=obj).count()

            if total_lessons == 0:
                return {
                    'completed': 0,
                    'total': 0,
                    'percentage': 0,
                    'completed_lessons': []
                }

            completed_progresses = Progress.objects.filter(
                enrollment=enrollment,
                is_completed=True
            )

            completed_lessons = completed_progresses.count()
            percentage = (completed_lessons / total_lessons) * \
                100 if total_lessons > 0 else 0

            # Get IDs of completed lessons
            completed_lesson_ids = list(
                completed_progresses.values_list('lesson__id', flat=True))

            return {
                'completed': completed_lessons,
                'total': total_lessons,
                'percentage': round(percentage, 1),
                'completed_lessons': completed_lesson_ids
            }
        except Enrollment.DoesNotExist:
            return None


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for student course enrollments"""
    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source='course',
        write_only=True
    )

    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'course_id', 'enrolled_date', 'last_accessed',
            'status', 'completion_date'
        ]
        read_only_fields = ['enrolled_date', 'last_accessed']


class ProgressSerializer(serializers.ModelSerializer):
    """Serializer for student lesson progress"""
    lesson = LessonSerializer(read_only=True)

    class Meta:
        model = Progress
        fields = [
            'id', 'lesson', 'is_completed', 'completed_date', 'time_spent'
        ]


class AssessmentAttemptSerializer(serializers.ModelSerializer):
    """Serializer for student assessment attempts"""
    class Meta:
        model = AssessmentAttempt
        fields = [
            'id', 'assessment', 'start_time', 'end_time', 'score', 'passed',
            'score_percentage'
        ]
        read_only_fields = ['start_time', 'end_time',
                            'score', 'passed', 'score_percentage']


class AttemptAnswerSerializer(serializers.ModelSerializer):
    """Serializer for student answers in assessment attempts"""
    class Meta:
        model = AttemptAnswer
        fields = [
            'id', 'question', 'selected_answer', 'text_answer', 'is_correct',
            'points_earned'
        ]
        read_only_fields = ['is_correct', 'points_earned']


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for course reviews"""
    user = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'rating', 'title', 'content', 'date_created',
            'helpful_count'
        ]
        read_only_fields = ['date_created', 'helpful_count']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'username': obj.user.username
        }


class NoteSerializer(serializers.ModelSerializer):
    """Serializer for student notes on lessons"""
    class Meta:
        model = Note
        fields = [
            'id', 'lesson', 'content', 'created_date', 'updated_date'
        ]
        read_only_fields = ['created_date', 'updated_date']


class CertificateSerializer(serializers.ModelSerializer):
    """Serializer for course completion certificates"""
    enrollment = EnrollmentSerializer(read_only=True)
    course = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = [
            'id', 'enrollment', 'issue_date', 'certificate_number',
            'course', 'user'
        ]
        read_only_fields = ['issue_date', 'certificate_number']

    def get_course(self, obj):
        return {
            'id': obj.enrollment.course.id,
            'title': obj.enrollment.course.title,
            'slug': obj.enrollment.course.slug
        }

    def get_user(self, obj):
        user = obj.enrollment.user
        return {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'username': user.username
        }
