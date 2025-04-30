"""
File: backend/courses/views.py
Purpose: API views for handling course-related data and enforcing access controls

Key views:
- CategoryViewSet: Course categories
- CourseViewSet: Course details and enrollment
- LessonViewSet: Lessons with tiered access control
- LessonDetailView: Lessons with tiered access control
- CompleteLesson: Mark lessons as completed
- CertificateViewSet: Access to course completion certificates (premium users only)

Modified for tiered access:
- Added user_access_level to context in views using utils.get_user_access_level
- Updated access control for certificates
- Added tiered content access to resource endpoints

Connected files:
1. backend/courses/serializers.py - Used by these views to format API responses
2. backend/courses/models.py - The database models being accessed
3. backend/courses/urls.py - Configures URL routing to these views
4. backend/users/models.py - User and subscription models
5. backend/courses/utils.py - Utility functions for access control
"""

from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Avg
from django.shortcuts import get_object_or_404

from .models import (
    Category, Course, Module, Lesson, Resource, Assessment,
    Question, Answer, Enrollment, Progress, AssessmentAttempt,
    AttemptAnswer, Review, Note, Certificate
)
from .serializers import (
    CategorySerializer, CourseSerializer, CourseDetailSerializer,
    ModuleSerializer, ModuleDetailSerializer, LessonSerializer,
    ResourceSerializer, AssessmentSerializer, QuestionSerializer,
    QuestionDetailSerializer, EnrollmentSerializer, ProgressSerializer,
    AssessmentAttemptSerializer, ReviewSerializer, NoteSerializer,
    CertificateSerializer
)
from .permissions import IsEnrolledOrReadOnly, IsEnrolled
from .utils import get_user_access_level


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    # Allow public GET requests
    permission_classes = [IsAuthenticatedOrReadOnly]


class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    # Update permission_classes to allow unauthenticated access with restrictions
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user_access_level'] = get_user_access_level(self.request)
        return context


class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return enrollments for the current user only"""
        return Enrollment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Ensure the current user is set as the enrollment user"""
        serializer.save(user=self.request.user)


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Course.objects.filter(is_published=True)
    lookup_field = 'slug'
    # Allow public GET requests
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'request': self.request,
            'currency': 'INR',  # Add currency information
        })

        # Add user access level to context
        context['user_access_level'] = get_user_access_level(self.request)
        return context

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, slug=None):
        course = self.get_object()
        user = request.user

        # Check if already enrolled
        if Enrollment.objects.filter(user=user, course=course).exists():
            return Response(
                {'detail': 'You are already enrolled in this course.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create enrollment
        enrollment = Enrollment.objects.create(
            user=user,
            course=course,
            status='active'
        )

        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def modules(self, request, slug=None):
        course = self.get_object()
        modules = course.modules.all().order_by('order')
        serializer = ModuleSerializer(modules, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def reviews(self, request, slug=None):
        course = self.get_object()
        reviews = course.reviews.all().order_by('-date_created')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsEnrolled])
    def review(self, request, slug=None):
        course = self.get_object()
        user = request.user

        # Check if user has already reviewed this course
        if Review.objects.filter(user=user, course=course).exists():
            return Response(
                {'detail': 'You have already reviewed this course.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate data
        rating = request.data.get('rating')
        content = request.data.get('content')
        title = request.data.get('title', '')

        if not rating or not content:
            return Response(
                {'detail': 'Rating and content are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'detail': 'Rating must be a number between 1 and 5.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create review
        review = Review.objects.create(
            user=user,
            course=course,
            rating=rating,
            title=title,
            content=content
        )

        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Module.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ModuleDetailSerializer
        return ModuleSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user_access_level'] = get_user_access_level(self.request)
        return context

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly])
    def lessons(self, request, pk=None):
        module = self.get_object()
        lessons = module.lessons.all().order_by('order')

        # Add user's access level to context
        context = self.get_serializer_context()
        serializer = LessonSerializer(lessons, many=True, context=context)
        return Response(serializer.data)


class LessonDetailView(generics.RetrieveAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    # Update permission_classes to allow unauthenticated access with restrictions
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user_access_level'] = get_user_access_level(self.request)
        return context

    def retrieve(self, request, *args, **kwargs):
        lesson = self.get_object()

        # For authenticated users, update access timestamp
        if request.user.is_authenticated:
            try:
                enrollment = Enrollment.objects.get(
                    user=request.user,
                    course=lesson.module.course
                )
                enrollment.last_accessed = timezone.now()
                enrollment.save(update_fields=['last_accessed'])
            except Enrollment.DoesNotExist:
                pass

        return super().retrieve(request, *args, **kwargs)


class CompleteLesson(generics.UpdateAPIView):
    # Only authenticated and enrolled users can complete lessons
    permission_classes = [IsEnrolled]

    def update(self, request, pk=None):
        lesson = get_object_or_404(Lesson, pk=pk)

        # Get or create progress record
        enrollment = get_object_or_404(
            Enrollment,
            user=request.user,
            course=lesson.module.course
        )

        progress, created = Progress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson
        )

        # Mark as completed if not already
        if not progress.is_completed:
            progress.is_completed = True
            progress.completed_date = timezone.now()

            # Update time spent if provided
            time_spent = request.data.get('time_spent')
            if time_spent and isinstance(time_spent, int):
                progress.time_spent = time_spent

            progress.save()

        # Check if course is completed
        total_lessons = Lesson.objects.filter(
            module__course=lesson.module.course
        ).count()

        completed_lessons = Progress.objects.filter(
            enrollment=enrollment,
            is_completed=True
        ).count()

        # If all lessons are completed, mark course as completed
        if total_lessons == completed_lessons:
            enrollment.status = 'completed'
            enrollment.completion_date = timezone.now()
            enrollment.save()

            # Generate certificate if course has certificate feature
            if lesson.module.course.has_certificate:
                # Check if user has premium subscription for certificate
                user_access_level = get_user_access_level(request)
                has_premium = user_access_level == 'advanced'

                # Only create certificate for premium users
                if has_premium:
                    certificate, created = Certificate.objects.get_or_create(
                        enrollment=enrollment,
                        defaults={
                            'certificate_number': f"CERT-{enrollment.id}-{timezone.now().strftime('%Y%m%d%H%M')}"
                        }
                    )

        return Response({
            'is_completed': True,
            'progress': {
                'completed': completed_lessons,
                'total': total_lessons,
                'percentage': round((completed_lessons / total_lessons) * 100, 1) if total_lessons > 0 else 0
            }
        })


class AssessmentDetailView(generics.RetrieveAPIView):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [IsEnrolled]


class StartAssessment(generics.CreateAPIView):
    serializer_class = AssessmentAttemptSerializer
    permission_classes = [IsEnrolled]

    def create(self, request, pk=None):
        assessment = get_object_or_404(Assessment, pk=pk)

        # Check if there's an active attempt
        active_attempt = AssessmentAttempt.objects.filter(
            user=request.user,
            assessment=assessment,
            end_time__isnull=True
        ).first()

        if active_attempt:
            serializer = self.get_serializer(active_attempt)
            return Response(serializer.data)

        # Create new attempt
        attempt = AssessmentAttempt.objects.create(
            user=request.user,
            assessment=assessment
        )

        serializer = self.get_serializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SubmitAssessment(generics.UpdateAPIView):
    permission_classes = [IsEnrolled]

    def update(self, request, pk=None):
        attempt = get_object_or_404(
            AssessmentAttempt,
            pk=pk,
            user=request.user,
            end_time__isnull=True
        )

        # Mark attempt as completed
        attempt.end_time = timezone.now()

        # Process answers
        answers_data = request.data.get('answers', [])
        total_score = 0

        for answer_data in answers_data:
            question_id = answer_data.get('question_id')
            selected_answer_id = answer_data.get('answer_id')
            text_answer = answer_data.get('text_answer', '')

            question = get_object_or_404(Question, pk=question_id)

            # For multiple choice and true/false questions
            if question.question_type in ['multiple_choice', 'true_false']:
                if selected_answer_id:
                    selected_answer = get_object_or_404(
                        Answer, pk=selected_answer_id)
                    is_correct = selected_answer.is_correct
                    points_earned = question.points if is_correct else 0

                    AttemptAnswer.objects.create(
                        attempt=attempt,
                        question=question,
                        selected_answer=selected_answer,
                        is_correct=is_correct,
                        points_earned=points_earned
                    )

                    total_score += points_earned

            # For short answer questions (simplified - would need more sophisticated matching in production)
            elif question.question_type == 'short_answer' and text_answer:
                # Get correct answer
                correct_answer = Answer.objects.filter(
                    question=question,
                    is_correct=True
                ).first()

                is_correct = False
                points_earned = 0

                if correct_answer and text_answer.lower().strip() == correct_answer.answer_text.lower().strip():
                    is_correct = True
                    points_earned = question.points

                AttemptAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    text_answer=text_answer,
                    is_correct=is_correct,
                    points_earned=points_earned
                )

                total_score += points_earned

        # Save total score and determine if passed
        attempt.score = total_score
        max_score = sum(q.points for q in attempt.assessment.questions.all())

        if max_score > 0:
            score_percentage = (total_score / max_score) * 100
            attempt.passed = score_percentage >= attempt.assessment.passing_score

        attempt.save()

        # Mark lesson as completed if assessment passed
        if attempt.passed:
            lesson = attempt.assessment.lesson
            enrollment = get_object_or_404(
                Enrollment,
                user=request.user,
                course=lesson.module.course
            )

            progress, created = Progress.objects.get_or_create(
                enrollment=enrollment,
                lesson=lesson,
                defaults={
                    'is_completed': True,
                    'completed_date': timezone.now()
                }
            )

            if not progress.is_completed:
                progress.is_completed = True
                progress.completed_date = timezone.now()
                progress.save()

        serializer = AssessmentAttemptSerializer(attempt)
        return Response(serializer.data)


class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserEnrollmentsView(generics.ListAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user)


class UserProgressView(generics.ListAPIView):
    serializer_class = ProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        enrollment = get_object_or_404(
            Enrollment,
            user=self.request.user,
            course_id=course_id
        )
        return Progress.objects.filter(enrollment=enrollment)


class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for accessing course completion certificates.
    Only available to users with premium subscriptions.
    """
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only certificates for the current user"""
        user = self.request.user
        user_access_level = get_user_access_level(self.request)

        # Check if user has premium subscription
        if user_access_level != 'advanced':
            # Non-premium users don't see certificates
            return Certificate.objects.none()

        # Return certificates for premium users
        return Certificate.objects.filter(enrollment__user=user)

    @action(detail=False, methods=['get'])
    def course(self, request):
        """Get certificate for a specific course"""
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response(
                {'error': 'Course ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user has premium subscription
        user_access_level = get_user_access_level(request)
        if user_access_level != 'advanced':
            return Response(
                {'error': 'Premium subscription required to access certificates'},
                status=status.HTTP_403_FORBIDDEN
            )

        certificate = get_object_or_404(
            Certificate,
            enrollment__user=request.user,
            enrollment__course_id=course_id
        )

        serializer = self.get_serializer(certificate)
        return Response(serializer.data)
