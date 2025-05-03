from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'courses', views.InstructorCourseViewSet,
                basename='instructor-course')
router.register(r'modules', views.InstructorModuleViewSet,
                basename='instructor-module')
router.register(r'lessons', views.InstructorLessonViewSet,
                basename='instructor-lesson')
router.register(r'resources', views.InstructorResourceViewSet,
                basename='instructor-resource')
router.register(r'assessments', views.InstructorAssessmentViewSet,
                basename='instructor-assessment')

urlpatterns = [
    path('', include(router.urls)),
]
