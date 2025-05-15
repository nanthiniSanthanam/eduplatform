"""
File: backend/users/urls.py
Purpose: Defines URL patterns for user management and authentication in EduPlatform.

This file maps URLs to view functions for the following operations:
- User registration and account creation
- User authentication (login and logout)
- Password management (change, reset)
- Email verification
- User profile management
- User session management
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from .views import (
    RegisterView, LoginView, LogoutView, UserView,
    ProfileView, PasswordChangeView,
    PasswordResetRequestView, PasswordResetConfirmView,
    EmailVerificationView, ResendVerificationView,
    UserSessionViewSet, SubscriptionViewSet
)

# Router for viewsets
router = DefaultRouter()
router.register(r'sessions', UserSessionViewSet, basename='user-sessions')
router.register(r'subscription', SubscriptionViewSet,
                basename='user-subscription')

# URL patterns
urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User management
    path('me/', UserView.as_view(), name='user-detail'),
    path('profile/', ProfileView.as_view(), name='user-profile'),

    # Password management
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
    path('password/reset/', PasswordResetRequestView.as_view(),
         name='password-reset-request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(),
         name='password-reset-confirm'),

    # Email verification
    path('email/verify/', EmailVerificationView.as_view(), name='email-verify'),
    path('email/verify/resend/', ResendVerificationView.as_view(),
         name='email-verify-resend'),

    # Include router URLs
    path('', include(router.urls)),
]
