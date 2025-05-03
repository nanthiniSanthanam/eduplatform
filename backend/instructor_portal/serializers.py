from rest_framework import serializers
from courses.models import Course, Module, Lesson, Resource, Assessment, Question, Answer


class InstructorResourceSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating resources by instructors"""
    class Meta:
        model = Resource
        fields = ['id', 'title', 'type', 'file',
                  'url', 'description', 'premium']
        read_only_fields = ['id']


class InstructorLessonSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating lessons by instructors"""
    resources = InstructorResourceSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'content', 'basic_content', 'intermediate_content',
            'access_level', 'duration', 'type', 'order', 'has_assessment',
            'has_lab', 'is_free_preview', 'resources'
        ]
        read_only_fields = ['id']


class InstructorModuleSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating modules by instructors"""
    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ['id', 'title', 'description',
                  'order', 'duration', 'lessons_count']
        read_only_fields = ['id']

    def get_lessons_count(self, obj):
        return obj.lessons.count()


class InstructorCourseSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating courses by instructors"""
    modules_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'subtitle', 'slug', 'description', 'category',
            'thumbnail', 'price', 'level', 'duration', 'has_certificate',
            'is_featured', 'is_published', 'modules_count'
        ]
        read_only_fields = ['id', 'slug']

    def get_modules_count(self, obj):
        return obj.modules.count()


class InstructorAnswerSerializer(serializers.ModelSerializer):
    """Serializer for assessment answers"""
    class Meta:
        model = Answer
        fields = ['id', 'answer_text', 'is_correct', 'explanation']
        read_only_fields = ['id']


class InstructorQuestionSerializer(serializers.ModelSerializer):
    """Serializer for assessment questions"""
    answers = InstructorAnswerSerializer(many=True)

    class Meta:
        model = Question
        fields = ['id', 'question_text', 'question_type',
                  'order', 'points', 'answers']
        read_only_fields = ['id']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        question = Question.objects.create(**validated_data)

        for answer_data in answers_data:
            Answer.objects.create(question=question, **answer_data)

        return question


class InstructorAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for assessments"""
    questions = InstructorQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Assessment
        fields = ['id', 'title', 'description',
                  'time_limit', 'passing_score', 'questions']
        read_only_fields = ['id']
