# fmt: off
# fmt: skip
# isort: skip
"""
File: backend/instructor_portal/serializers.py
Version: 2.1.2
Date: 2025-05-25 05:50:55
Author: mohithasanthanam
Last Modified: 2025-05-25 05:50:55 UTC

Enhanced Instructor Portal Serializers with Existing Utils Integration

Key Improvements:
1. Integration with existing courses/utils.py functions
2. Enhanced course serializer with file upload support
3. Improved error handling and validation messages
4. Access level validation using existing utility patterns
5. Better JSON field handling for requirements and skills
6. Added JSON coercion helper for string input

This module provides serializers for instructors to manage:
- Courses with proper validation and file upload support
- Modules with lesson counting and validation
- Lessons with tiered access level support using existing access control
- Resources with premium restrictions
- Assessments with questions and answers

Connected files that need to be consistent:
- backend/instructor_portal/views.py - API endpoint handlers
- backend/courses/models.py - Model definitions and choices
- backend/courses/utils.py - Existing utility functions for access control
- frontend/src/services/instructorService.js - API client
- frontend/src/pages/instructor/wizardSteps/ContentCreationStep.jsx - UI components
"""

from rest_framework import serializers
from courses.models import Course, Module, Lesson, Resource, Assessment, Question, Answer, Category
from courses.utils import get_user_access_level, get_restricted_content_message


class InstructorResourceSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating resources by instructors

    Handles file uploads, URL validation, and premium resource settings
    """
    class Meta:
        model = Resource
        fields = [
            'id', 'title', 'type', 'file', 'url', 'description', 'premium'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        """
        Validate that either file or URL is provided based on resource type
        """
        resource_type = data.get('type')
        file_data = data.get('file')
        url_data = data.get('url')

        if resource_type in ['document', 'video', 'code'] and not file_data and not url_data:
            raise serializers.ValidationError(
                "Either file or URL must be provided for this resource type."
            )

        if resource_type == 'link' and not url_data:
            raise serializers.ValidationError(
                "URL is required for external link resources."
            )

        return data


class InstructorLessonSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating lessons by instructors

    Handles tiered content access levels and validation using existing utils
    """
    resources = InstructorResourceSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'content', 'basic_content', 'intermediate_content',
            'access_level', 'duration', 'type', 'order', 'has_assessment',
            'has_lab', 'is_free_preview', 'resources'
        ]
        read_only_fields = ['id']

    def validate_access_level(self, value):
        """
        Validate that access level is one of the allowed choices
        """
        valid_choices = [choice[0] for choice in Lesson.ACCESS_LEVEL_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(
                f"Invalid access level. Must be one of: {', '.join(valid_choices)}"
            )
        return value

    def validate(self, data):
        """
        Validate lesson content based on access level
        """
        access_level = data.get('access_level', 'intermediate')
        content = data.get('content', '')
        basic_content = data.get('basic_content', '')
        intermediate_content = data.get('intermediate_content', '')

        # Ensure at least one content field is provided
        if not any([content, basic_content, intermediate_content]):
            raise serializers.ValidationError(
                "At least one content field must be provided."
            )

        # If access level is basic, ensure basic_content is provided
        if access_level == 'basic' and not basic_content:
            raise serializers.ValidationError(
                "Basic content must be provided for basic access level lessons."
            )

        # If access level is intermediate, ensure intermediate_content or content is provided
        if access_level == 'intermediate' and not (intermediate_content or content):
            raise serializers.ValidationError(
                "Intermediate content or full content must be provided for intermediate access level lessons."
            )

        return data

    def to_representation(self, instance):
        """
        Customize the representation based on user access level using existing utils
        """
        data = super().to_representation(instance)
        request = self.context.get('request')

        if request and hasattr(request, 'user'):
            user = request.user

            # For instructors, always show full content
            if user.is_authenticated and hasattr(user, 'role') and user.role == 'instructor':
                return data

            # Get user's access level using existing utility function
            user_access_level = get_user_access_level(request)

            # Apply access restrictions based on lesson requirements
            if instance.access_level == 'advanced' and user_access_level != 'advanced':
                # User doesn't have premium access, show restricted message
                data['content'] = get_restricted_content_message(
                    instance.title, 
                    user_access_level
                )
                data['intermediate_content'] = None

            elif instance.access_level == 'intermediate' and user_access_level == 'basic':
                # Unregistered user trying to access registered content
                if not instance.is_free_preview:
                    data['content'] = get_restricted_content_message(
                        instance.title, 
                        user_access_level
                    )
                    data['intermediate_content'] = None

        return data


class InstructorModuleSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating modules by instructors

    Includes lesson count and nested lesson data
    """
    lessons_count = serializers.SerializerMethodField()
    lessons = InstructorLessonSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'order', 'duration', 'lessons_count', 'lessons'
        ]
        read_only_fields = ['id']

    def get_lessons_count(self, obj):
        """
        Get the count of lessons in this module
        """
        return obj.lessons.count()

    def validate_order(self, value):
        """
        Validate that order is a positive integer
        """
        if value < 1:
            raise serializers.ValidationError("Order must be a positive integer.")
        return value


class InstructorCourseSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating courses by instructors

    Handles file uploads, category assignment, and JSON fields
    """
    modules_count = serializers.SerializerMethodField()
    modules = InstructorModuleSerializer(many=True, read_only=True, required=False)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    # Add category name for read operations
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'subtitle', 'slug', 'description', 'category',
            'category_id', 'category_name', 'thumbnail', 'price', 'discount_price',
            'level', 'duration', 'has_certificate', 'is_featured', 'is_published',
            'modules_count', 'modules', 'requirements', 'skills'
        ]
        read_only_fields = ['id', 'slug', 'category']

    def get_modules_count(self, obj):
        """
        Get the count of modules in this course
        """
        return obj.modules.count()

    def validate_price(self, value):
        """
        Validate that price is not negative
        """
        if value is not None and value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_discount_price(self, value):
        """
        Validate that discount price is not negative and less than regular price
        """
        if value is not None:
            if value < 0:
                raise serializers.ValidationError("Discount price cannot be negative.")

            # If we have access to the price field, validate discount is less than price
            price = self.initial_data.get('price')
            if price is not None and value >= float(price):
                raise serializers.ValidationError("Discount price must be less than regular price.")

        return value

    def _coerce_json(self, v):
        """
        Helper method to coerce string to JSON 
        """
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v

    def validate_requirements(self, value):
        """
        Validate requirements field (should be a list)
        """
        value = self._coerce_json(value)
        if value is not None and not isinstance(value, (list, dict)):
            raise serializers.ValidationError("Requirements must be a list or object.")
        return value

    def validate_skills(self, value):
        """
        Validate skills field (should be a list)
        """
        value = self._coerce_json(value)
        if value is not None and not isinstance(value, (list, dict)):
            raise serializers.ValidationError("Skills must be a list or object.")
        return value

    def validate_thumbnail(self, value):
        """
        Validate thumbnail file upload
        """
        if value:
            # Check file size (5MB limit)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Thumbnail file size cannot exceed 5MB.")

            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(value, 'content_type') and value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    "Thumbnail must be a JPEG, PNG, GIF, or WebP image."
                )

        return value

    def create(self, validated_data):
        """
        Create a new course with proper handling of JSON fields
        """
        # Handle JSON fields that might come as strings from FormData
        for field in ['requirements', 'skills']:
            if field in validated_data and isinstance(validated_data[field], str):
                try:
                    import json
                    validated_data[field] = json.loads(validated_data[field])
                except json.JSONDecodeError:
                    # If it's not valid JSON, treat as a simple string and wrap in list
                    validated_data[field] = [validated_data[field]]

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update course with proper handling of JSON fields
        """
        # Handle JSON fields that might come as strings from FormData
        for field in ['requirements', 'skills']:
            if field in validated_data and isinstance(validated_data[field], str):
                try:
                    import json
                    validated_data[field] = json.loads(validated_data[field])
                except json.JSONDecodeError:
                    # If it's not valid JSON, treat as a simple string and wrap in list
                    validated_data[field] = [validated_data[field]]

        return super().update(instance, validated_data)


class InstructorAnswerSerializer(serializers.ModelSerializer):
    """
    Serializer for assessment answers
    """
    class Meta:
        model = Answer
        fields = ['id', 'answer_text', 'is_correct', 'explanation']
        read_only_fields = ['id']

    def validate_answer_text(self, value):
        """
        Validate that answer text is not empty
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Answer text cannot be empty.")
        return value


class InstructorQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for assessment questions with nested answers
    """
    answers = InstructorAnswerSerializer(many=True)

    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'question_type', 'order', 'points', 'answers'
        ]
        read_only_fields = ['id']

    def validate_answers(self, value):
        """
        Validate that questions have appropriate answers
        """
        if not value:
            raise serializers.ValidationError("At least one answer is required.")

        # For multiple choice and true/false, check that exactly one answer is correct
        question_type = self.initial_data.get('question_type')
        if question_type in ['multiple_choice', 'true_false']:
            correct_answers = [answer for answer in value if answer.get('is_correct')]
            if len(correct_answers) != 1:
                raise serializers.ValidationError(
                    f"Exactly one answer must be marked as correct for {question_type} questions."
                )

        return value

    def create(self, validated_data):
        """
        Create question with nested answers
        """
        answers_data = validated_data.pop('answers')
        question = Question.objects.create(**validated_data)

        for answer_data in answers_data:
            Answer.objects.create(question=question, **answer_data)

        return question

    def update(self, instance, validated_data):
        """
        Update question and its answers
        """
        answers_data = validated_data.pop('answers', [])

        # Update question fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update answers (simple approach: delete all and recreate)
        instance.answers.all().delete()
        for answer_data in answers_data:
            Answer.objects.create(question=instance, **answer_data)

        return instance


class InstructorAssessmentSerializer(serializers.ModelSerializer):
    """
    Serializer for assessments with nested questions
    """
    questions = InstructorQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'description', 'time_limit', 'passing_score', 
            'questions', 'questions_count'
        ]
        read_only_fields = ['id']

    def get_questions_count(self, obj):
        """
        Get the count of questions in this assessment
        """
        return obj.questions.count()

    def validate_time_limit(self, value):
        """
        Validate time limit is not negative
        """
        if value < 0:
            raise serializers.ValidationError("Time limit cannot be negative.")
        return value

    def validate_passing_score(self, value):
        """
        Validate passing score is between 0 and 100
        """
        if not (0 <= value <= 100):
            raise serializers.ValidationError("Passing score must be between 0 and 100.")
        return value