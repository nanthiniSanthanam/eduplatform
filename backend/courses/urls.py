"""
File: backend/courses/urls.py
Purpose: URL routing configuration for course-related APIs

This file defines URL patterns for:
1. Course listing and detail views
2. Module and lesson endpoints
3. Enrollment and progress tracking
4. Assessment and certificate endpoints

Modified for tiered access:
- Added certificate endpoints
- Updated permissions on lesson URLs

Variables to modify:
- API URL prefix if you want to change the base path

Connected files:
1. backend/courses/views.py - Contains the view functions these URLs connect to
2. backend/educore/urls.py - The root URL configuration that includes this file
3. frontend/src/services/api.js - Should match these endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'modules', views.ModuleViewSet)
router.register(r'lessons', views.LessonViewSet)
router.register(r'enrollments', views.EnrollmentViewSet, basename='enrollment')
router.register(r'notes', views.NoteViewSet, basename='note')
router.register(r'certificates', views.CertificateViewSet,
                basename='certificate')

urlpatterns = [
    path('', include(router.urls)),
    path('lessons/<int:pk>/detail/',
         views.LessonDetailView.as_view(), name='lesson-detail'),
    path('lessons/<int:pk>/complete/',
         views.CompleteLesson.as_view(), name='complete-lesson'),
    path('assessments/<int:pk>/', views.AssessmentDetailView.as_view(),
         name='assessment-detail'),
    path('assessments/<int:pk>/start/',
         views.StartAssessment.as_view(), name='start-assessment'),
    path('assessment-attempts/<int:pk>/submit/',
         views.SubmitAssessment.as_view(), name='submit-assessment'),
    path('user/enrollments/', views.UserEnrollmentsView.as_view(),
         name='user-enrollments'),
    path('user/courses/<int:course_id>/progress/',
         views.UserProgressView.as_view(), name='user-course-progress'),
]
