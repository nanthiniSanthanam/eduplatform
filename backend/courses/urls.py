from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, CourseViewSet, ModuleViewSet, LessonDetailView,
    CompleteLesson, AssessmentDetailView, StartAssessment, SubmitAssessment,
    NoteViewSet, UserEnrollmentsView, UserProgressView
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'modules', ModuleViewSet)
router.register(r'notes', NoteViewSet, basename='notes')

urlpatterns = [
    path('', include(router.urls)),
    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('lessons/<int:pk>/complete/',
         CompleteLesson.as_view(), name='complete-lesson'),
    path('assessments/<int:pk>/', AssessmentDetailView.as_view(),
         name='assessment-detail'),
    path('assessments/<int:pk>/start/',
         StartAssessment.as_view(), name='start-assessment'),
    path('assessment-attempts/<int:pk>/submit/',
         SubmitAssessment.as_view(), name='submit-assessment'),
    path('user/enrollments/', UserEnrollmentsView.as_view(),
         name='user-enrollments'),
    path('user/progress/<int:course_id>/',
         UserProgressView.as_view(), name='user-progress'),
]
