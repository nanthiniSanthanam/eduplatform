from django.shortcuts import render

# Create your views here.


from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from courses.models import Course, Module, Lesson, Resource, Assessment, Question, CourseInstructor
from .serializers import (
    InstructorCourseSerializer, InstructorModuleSerializer, InstructorLessonSerializer,
    InstructorResourceSerializer, InstructorAssessmentSerializer, InstructorQuestionSerializer
)


class IsInstructorOrAdmin(permissions.BasePermission):
    """
    Permission to only allow instructors or admins to access the view.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == 'instructor' or
            request.user.role == 'administrator' or
            request.user.is_staff
        )

    def has_object_permission(self, request, view, obj):
        # Check if user is admin
        if request.user.role == 'administrator' or request.user.is_staff:
            return True

        # If it's a Course object, check if user is an instructor
        if isinstance(obj, Course):
            return obj.instructors.filter(instructor=request.user).exists()

        # If it's a Module, check its course
        if isinstance(obj, Module):
            return obj.course.instructors.filter(instructor=request.user).exists()

        # If it's a Lesson, check its module's course
        if isinstance(obj, Lesson):
            return obj.module.course.instructors.filter(instructor=request.user).exists()

        # If it's a Resource, check its lesson's module's course
        if isinstance(obj, Resource):
            return obj.lesson.module.course.instructors.filter(instructor=request.user).exists()

        # If it's an Assessment, check its lesson's module's course
        if isinstance(obj, Assessment):
            return obj.lesson.module.course.instructors.filter(instructor=request.user).exists()

        # If it's a Question, check its assessment's lesson's module's course
        if isinstance(obj, Question):
            return obj.assessment.lesson.module.course.instructors.filter(instructor=request.user).exists()

        return False


class InstructorCourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for instructors to manage their courses
    """
    serializer_class = InstructorCourseSerializer
    permission_classes = [IsInstructorOrAdmin]
    lookup_field = 'slug'  # Use slug for lookups instead of pk

    def get_queryset(self):
        # Return only courses where the user is an instructor
        user = self.request.user
        print(f"InstructorCourseViewSet.get_queryset: User {user}")

        if user.role == 'administrator' or user.is_staff:
            return Course.objects.all()

        return Course.objects.filter(instructors__instructor=user)

    def perform_create(self, serializer):
        # Automatically add the current user as an instructor
        course = serializer.save()
        CourseInstructor.objects.create(
            course=course,
            instructor=self.request.user,
            is_lead=True
        )

    @action(detail=True, methods=['get'])
    def modules(self, request, slug=None):
        """Get all modules for a specific course"""
        course = self.get_object()
        modules = Module.objects.filter(course=course).order_by('order')
        serializer = InstructorModuleSerializer(modules, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['put'])
    def publish(self, request, slug=None):
        """Publish or unpublish a course"""
        course = self.get_object()
        should_publish = request.data.get('publish', True)

        # Check if course has enough content to be published
        if should_publish:
            # Validate course has required components
            modules_count = course.modules.count()
            if modules_count == 0:
                return Response(
                    {"detail": "Course needs at least one module to be published."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if at least one module has lessons
            has_lessons = False
            for module in course.modules.all():
                if module.lessons.count() > 0:
                    has_lessons = True
                    break

            if not has_lessons:
                return Response(
                    {"detail": "Course needs at least one lesson to be published."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Update published status
        course.is_published = should_publish
        course.save()

        serializer = self.get_serializer(course)
        return Response(serializer.data)


class InstructorModuleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for instructors to manage modules within their courses
    """
    serializer_class = InstructorModuleSerializer
    permission_classes = [IsInstructorOrAdmin]

    def get_queryset(self):
        # Filter by course if specified
        course_id = self.request.query_params.get('course')
        if course_id:
            return Module.objects.filter(course_id=course_id)

        # Otherwise, return all modules for courses where the user is an instructor
        if self.request.user.role == 'administrator' or self.request.user.is_staff:
            return Module.objects.all()
        return Module.objects.filter(course__instructors__instructor=self.request.user)

    def perform_create(self, serializer):
        course_id = self.request.data.get('course')
        if not course_id:
            return Response(
                {"detail": "Course ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        course = get_object_or_404(Course, id=course_id)

        # Check if user is an instructor for this course
        if not course.instructors.filter(instructor=self.request.user).exists() and not (
            self.request.user.role == 'administrator' or self.request.user.is_staff
        ):
            return Response(
                {"detail": "You do not have permission to create modules in this course."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer.save(course=course)


class InstructorLessonViewSet(viewsets.ModelViewSet):
    """
    API endpoint for instructors to manage lessons within their modules
    """
    serializer_class = InstructorLessonSerializer
    permission_classes = [IsInstructorOrAdmin]

    def get_queryset(self):
        # Filter by module if specified
        module_id = self.request.query_params.get('module')
        if module_id:
            return Lesson.objects.filter(module_id=module_id)

        # Otherwise, return all lessons for modules where the user is an instructor
        if self.request.user.role == 'administrator' or self.request.user.is_staff:
            return Lesson.objects.all()
        return Lesson.objects.filter(module__course__instructors__instructor=self.request.user)

    def perform_create(self, serializer):
        module_id = self.request.data.get('module')
        if not module_id:
            return Response(
                {"detail": "Module ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        module = get_object_or_404(Module, id=module_id)

        # Check if user is an instructor for this module's course
        if not module.course.instructors.filter(instructor=self.request.user).exists() and not (
            self.request.user.role == 'administrator' or self.request.user.is_staff
        ):
            return Response(
                {"detail": "You do not have permission to create lessons in this module."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer.save(module=module)


class InstructorResourceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for instructors to manage resources within their lessons
    """
    serializer_class = InstructorResourceSerializer
    permission_classes = [IsInstructorOrAdmin]

    def get_queryset(self):
        # Filter by lesson if specified
        lesson_id = self.request.query_params.get('lesson')
        if lesson_id:
            return Resource.objects.filter(lesson_id=lesson_id)

        # Otherwise, return all resources for lessons where the user is an instructor
        if self.request.user.role == 'administrator' or self.request.user.is_staff:
            return Resource.objects.all()
        return Resource.objects.filter(lesson__module__course__instructors__instructor=self.request.user)

    def perform_create(self, serializer):
        lesson_id = self.request.data.get('lesson')
        if not lesson_id:
            return Response(
                {"detail": "Lesson ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Check if user is an instructor for this lesson's module's course
        if not lesson.module.course.instructors.filter(instructor=self.request.user).exists() and not (
            self.request.user.role == 'administrator' or self.request.user.is_staff
        ):
            return Response(
                {"detail": "You do not have permission to add resources to this lesson."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer.save(lesson=lesson)


class InstructorAssessmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for instructors to manage assessments for their lessons
    """
    serializer_class = InstructorAssessmentSerializer
    permission_classes = [IsInstructorOrAdmin]

    def get_queryset(self):
        # Filter by lesson if specified
        lesson_id = self.request.query_params.get('lesson')
        if lesson_id:
            return Assessment.objects.filter(lesson_id=lesson_id)

        # Otherwise, return all assessments for lessons where the user is an instructor
        if self.request.user.role == 'administrator' or self.request.user.is_staff:
            return Assessment.objects.all()
        return Assessment.objects.filter(lesson__module__course__instructors__instructor=self.request.user)

    def perform_create(self, serializer):
        lesson_id = self.request.data.get('lesson')
        if not lesson_id:
            return Response(
                {"detail": "Lesson ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Check if user is an instructor for this lesson's module's course
        if not lesson.module.course.instructors.filter(instructor=self.request.user).exists() and not (
            self.request.user.role == 'administrator' or self.request.user.is_staff
        ):
            return Response(
                {"detail": "You do not have permission to create assessments for this lesson."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if lesson already has an assessment
        if hasattr(lesson, 'assessment'):
            return Response(
                {"detail": "This lesson already has an assessment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save(lesson=lesson)

    @action(detail=True, methods=['post'])
    def add_question(self, request, pk=None):
        """
        Add a question to an assessment
        """
        assessment = self.get_object()

        serializer = InstructorQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(assessment=assessment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
