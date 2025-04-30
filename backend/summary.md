File: C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform\backend\setup_database.md
Purpose: Instructions for setting up the local PostgreSQL database

This file provides:

1. Step-by-step guide to install and configure PostgreSQL
2. Commands to create database and required tables
3. Connection settings for the Django backend

Variables to modify:

- DATABASE_NAME: Name of your database (default: eduplatform)
- DATABASE_USER: Database username (default: postgres)
- DATABASE_PASSWORD: Vajjiram@79

psql -U postgres -d eduplatform

---

Comprehensive Summary of Educational Platform Backend (EduPlatform)
Current Date and Time (UTC): 2025-04-27 08:55:48
Current User's Login: cadsanthanam

Complete Backend System Architecture and Functionality
The educational platform's backend consists of two main Django applications: users and courses, orchestrated through the central educore configuration. The core of the system is a three-tiered access model implemented using the CustomUser and Subscription models in the users app, which connect to content filtering logic in the courses app through the LessonSerializer class. Authentication uses JWT tokens via Django REST framework, with token generation happening in LoginView and validation in CustomJWTAuthentication. The subscription system defines three tiers ('free', 'basic', 'premium') in Subscription.SUBSCRIPTION_TIERS which map to three access levels ('basic', 'intermediate', 'advanced') determined by the get_user_access_level function in courses/utils.py. This function checks request.user.subscription.tier and subscription.is_active() to determine appropriate content visibility. Course content is stored in the Lesson model with fields for different access levels (content, intermediate_content, basic_content), and the to_representation method in LessonSerializer filters content based on user's access level. When a request arrives, the API view obtains the user from the JWT token, determines access level, adds it to serializer context, and then the serializer applies appropriate content filtering. Additionally, the system handles certificate generation in CompleteLesson view, which checks user_access_level == 'advanced' before creating certificates. API endpoints are defined in educore/urls.py and segregated by function into categories (/api/courses/, /api/user/, etc.). Database configuration uses PostgreSQL with connection parameters in db_settings.py, and the settings.py file configures Django with SIMPLE_JWT, REST_FRAMEWORK, and other critical settings to enable the tiered access system. The system tracks user sessions in the UserSession model to handle concurrent logins and provide security features like session invalidation. Email verification uses the EmailVerification model with token generation logic in RegisterView and validation in EmailVerificationView. The entire platform uses models with descriptive field names that clearly indicate their purpose, serializers that handle data validation and transformation, viewsets/views that implement business logic, and URL configurations that map endpoints to views, creating a complete RESTful API for the educational platform with tiered access control.

Detailed Component Analysis

1. Core Configuration (educore)
   The educore package serves as the central configuration hub for the Django project:

settings.py: Contains critical configuration like SECRET_KEY, INSTALLED_APPS (includes 'users', 'courses', 'rest_framework', 'corsheaders'), MIDDLEWARE, REST_FRAMEWORK configuration with authentication classes, and SIMPLE_JWT settings with token lifetimes. Routes are defined through ROOT_URLCONF = 'educore.urls'. The custom user model is specified with AUTH_USER_MODEL = 'users.CustomUser'.

urls.py: Defines all API endpoints, registering viewsets with the DefaultRouter (CategoryViewSet, CourseViewSet, ModuleViewSet, LessonViewSet, EnrollmentViewSet), JWT token endpoints ('/api/token/'), and includes app-specific URLs like 'api/user/' which includes all endpoints from users.urls.

db_settings.py: Contains PostgreSQL database configuration including name, user, password, host, and port.

2. Users App
   The users app manages authentication, user profiles, and subscription tiers:

models.py: Defines CustomUser model extending AbstractUser with email-based authentication, roles ('student', 'instructor', 'admin', 'staff'), and security features like failed login tracking. Profile model contains additional user information. Subscription model defines three tiers ('free', 'basic', 'premium') with status tracking, expiration dates, and the critical is_active() method that determines if a subscription grants access.

views.py: Implements user management endpoints including RegisterView (creates users with default free subscription), LoginView (authenticates and generates JWT tokens), and SubscriptionViewSet with actions for upgrading/downgrading subscriptions.

serializers.py: Contains serializers like UserSerializer, ProfileSerializer, and SubscriptionSerializer which add the vital access_level mapping to subscription tiers in the to_representation method.

authentication.py: Provides CustomJWTAuthentication class that extends JWTAuthentication to validate tokens and track active sessions.

3. Courses App
   The courses app manages educational content and implements the tiered access system:

models.py: Contains models for Category, Course, Module, Lesson (with fields for different content tiers: content, intermediate_content, basic_content, and access_level that can be 'basic', 'intermediate', or 'advanced'), Resource (with premium boolean field), and Certificate (linked to enrollments).

views.py: Implements viewsets like CourseViewSet, LessonViewSet, and CertificateViewSet. Key views include LessonDetailView which adds user_access_level to serializer context and CompleteLesson which checks subscription before generating certificates.

serializers.py: The critical LessonSerializer implements the to_representation method that filters content based on user_access_level from context, showing appropriate content for each access tier.

utils.py: Contains the essential get_user_access_level function that determines a user's access level based on authentication status and subscription tier, and get_restricted_content_message which generates appropriate messages for restricted content.

permissions.py: Contains permission classes like IsEnrolled to restrict certain actions to enrolled users.

4. API and Tiered Access Flow
   The complete request flow for the tiered access system works as follows:

JWT authentication middleware validates the token and identifies the user
View handlers like LessonDetailView call get_user_access_level(request) from utils.py
This function checks if the user is authenticated, then examines subscription tier and active status
The access level ('basic', 'intermediate', 'advanced') is added to serializer context
LessonSerializer.to_representation method filters content based on this access level
For basic users (unauthenticated), only basic_content is shown or a registration message
For intermediate users (free/basic subscription), intermediate_content is shown
For advanced users (premium subscription), full content is shown including premium resources
Certificate generation in CompleteLesson is restricted to users with premium subscriptions
This comprehensive tiered access system ensures that content is properly restricted based on subscription level while providing appropriate messaging to encourage upgrades.
