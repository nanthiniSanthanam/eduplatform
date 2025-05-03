"""
URL configuration for educore project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from courses.views import CategoryViewSet, CourseViewSet, ModuleViewSet, LessonViewSet, EnrollmentViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import db_status, db_stats

# Create a router for API viewsets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'modules', ModuleViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')


urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    # Include router URLs directly under /api/
    path('api/', include(router.urls)),

    # User authentication endpoints using JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # System endpoints
    path('api/system/db-status/', db_status, name='db-status'),
    path('api/system/db-stats/', db_stats, name='db-stats'),

    # Include user app URLs
    path('api/user/', include('users.urls')),
    path('api/instructor/', include('instructor_portal.urls')),

    # Django REST browsable API authentication
    path('api-auth/', include('rest_framework.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
