# Educational Platform Project Documentation

## 1. Project Overview

**Educational Platform** is a modern e-learning system that facilitates online education with a structured learning approach. The platform is built using Django REST Framework for the backend API and React for the frontend user interface. It allows course creators to build modular courses with rich content, while learners can enroll, track progress, complete assessments, and earn certificates.

## 2. System Architecture

### 2.1 Technology Stack

**Backend:**

- Framework: Django 4.x with Django REST Framework
- Database: PostgreSQL 15.x
- Authentication: JWT (JSON Web Tokens)
- Media Storage: Local filesystem with potential for cloud storage integration
- Development Language: Python 3.13.x

**Frontend:**

- Framework: React 18.x
- State Management: React Context API
- Routing: React Router 6.x
- API Integration: Axios with interceptors
- Build Tool: Vite
- CSS Framework: Tailwind CSS
- Development Language: JavaScript (ES6+)

### 2.2 System Components

The system consists of the following key components:

1. **Authentication System**: JWT-based authentication with token refresh mechanism
2. **Course Management**: CRUD operations for courses, modules, and lessons
3. **Enrollment System**: User enrollment in courses and progress tracking
4. **Assessment Engine**: Quiz/assessment creation, attempt handling, and grading
5. **User Profile Management**: User data and preferences
6. **Certificate Generation**: Automatic certificate issuance for completed courses

### 2.3 Repository Structure

```
eduplatform/
├── backend/
│   ├── config/             # Configuration files
│   ├── courses/            # Course management app
│   ├── educore/            # Project settings
│   ├── scripts/            # Utility scripts
│   ├── users/              # User management app
│   └── requirements.txt    # Dependencies
└── frontend/
    ├── public/             # Static assets
    ├── src/                # Source code
    │   ├── assets/         # Assets (images, etc.)
    │   ├── components/     # React components
    │   ├── contexts/       # Context providers
    │   ├── pages/          # Page components
    │   ├── services/       # API services
    │   ├── styles/         # CSS styles
    │   └── utils/          # Utility functions
    ├── package.json        # NPM dependencies
    └── tailwind.config.js  # Tailwind configuration
```

## 3. Database Architecture

### 3.1 Core Tables and Relationships

The database follows a relational model with the following key tables:

1. **User**: Extended Django user model
2. **UserProfile**: Additional user information
3. **Category**: Course categories
4. **Course**: Main course entity
5. **CourseInstructor**: Linking instructors to courses
6. **Module**: Course modules/sections
7. **Lesson**: Content units within modules
8. **Resource**: Supplementary materials for lessons
9. **Assessment**: Quizzes/tests for lessons
10. **Question**: Individual assessment questions
11. **Answer**: Possible answers for questions
12. **Enrollment**: User enrollment in courses
13. **Progress**: Tracking user progress through lessons
14. **AssessmentAttempt**: User attempts at assessments
15. **Review**: User reviews for courses
16. **Note**: User notes for lessons
17. **Certificate**: Certificates issued upon course completion

### 3.2 Entity Relationship Diagram

The system follows these key relationships:

- Users can enroll in multiple courses (1:N)
- Courses contain multiple modules (1:N)
- Modules contain multiple lessons (1:N)
- Lessons can have one assessment (1:1)
- Assessments contain multiple questions (1:N)
- Questions have multiple answers (1:N)
- Users can make multiple assessment attempts (1:N)
- Each enrollment can have one certificate (1:1)
- Users can create multiple notes for lessons (1:N)
- Users can leave one review per course (1:1)

### 3.3 Data Models

#### 3.3.1 User Models

- **UserProfile**:
  - `user`: ForeignKey to Django User (OneToOne)
  - `bio`: TextField (optional)
  - `avatar`: ImageField (optional)
  - `website`: URLField (optional)
  - `occupation`: CharField (optional)
  - `organization`: CharField (optional)
  - `interests`: JSONField (list)
  - `settings`: JSONField (dict)
  - `created_at`: DateTimeField (auto)
  - `updated_at`: DateTimeField (auto)

#### 3.3.2 Course Models

- **Category**:

  - `name`: CharField
  - `description`: TextField (optional)
  - `icon`: CharField (optional)
  - `slug`: SlugField (unique)

- **Course**:

  - `title`: CharField
  - `subtitle`: CharField (optional)
  - `slug`: SlugField (unique)
  - `description`: TextField
  - `category`: ForeignKey to Category
  - `thumbnail`: ImageField (optional)
  - `price`: DecimalField
  - `discount_price`: DecimalField (optional)
  - `discount_ends`: DateTimeField (optional)
  - `level`: CharField (choices: beginner, intermediate, advanced, all_levels)
  - `duration`: CharField (optional)
  - `has_certificate`: BooleanField
  - `is_featured`: BooleanField
  - `is_published`: BooleanField
  - `published_date`: DateTimeField (auto)
  - `updated_date`: DateTimeField (auto)
  - `requirements`: JSONField (optional)
  - `skills`: JSONField (optional)

- **CourseInstructor**:

  - `course`: ForeignKey to Course
  - `instructor`: ForeignKey to User
  - `title`: CharField (optional)
  - `bio`: TextField (optional)
  - `is_lead`: BooleanField

- **Module**:

  - `course`: ForeignKey to Course
  - `title`: CharField
  - `description`: TextField (optional)
  - `order`: PositiveIntegerField
  - `duration`: CharField (optional)

- **Lesson**:

  - `module`: ForeignKey to Module
  - `title`: CharField
  - `content`: TextField
  - `duration`: CharField (optional)
  - `type`: CharField (choices: video, reading, interactive, quiz, lab)
  - `order`: PositiveIntegerField
  - `has_assessment`: BooleanField
  - `has_lab`: BooleanField
  - `is_free_preview`: BooleanField

- **Resource**:
  - `lesson`: ForeignKey to Lesson
  - `title`: CharField
  - `type`: CharField (choices: document, video, link, code, tool)
  - `file`: FileField (optional)
  - `url`: URLField (optional)
  - `description`: TextField (optional)

#### 3.3.3 Assessment Models

- **Assessment**:

  - `lesson`: OneToOneField to Lesson
  - `title`: CharField
  - `description`: TextField (optional)
  - `time_limit`: PositiveIntegerField (minutes, 0 = no limit)
  - `passing_score`: PositiveIntegerField (percentage)

- **Question**:

  - `assessment`: ForeignKey to Assessment
  - `question_text`: TextField
  - `question_type`: CharField (choices: multiple_choice, true_false, short_answer, matching)
  - `order`: PositiveIntegerField
  - `points`: PositiveIntegerField

- **Answer**:
  - `question`: ForeignKey to Question
  - `answer_text`: CharField
  - `is_correct`: BooleanField
  - `explanation`: TextField (optional)

#### 3.3.4 Progress Tracking Models

- **Enrollment**:

  - `user`: ForeignKey to User
  - `course`: ForeignKey to Course
  - `enrolled_date`: DateTimeField (auto)
  - `last_accessed`: DateTimeField (auto)
  - `status`: CharField (choices: active, completed, dropped)
  - `completion_date`: DateTimeField (optional)
  - Unique constraint: (user, course)

- **Progress**:

  - `enrollment`: ForeignKey to Enrollment
  - `lesson`: ForeignKey to Lesson
  - `is_completed`: BooleanField
  - `completed_date`: DateTimeField (optional)
  - `time_spent`: PositiveIntegerField (seconds)
  - Unique constraint: (enrollment, lesson)

- **AssessmentAttempt**:

  - `user`: ForeignKey to User
  - `assessment`: ForeignKey to Assessment
  - `start_time`: DateTimeField (auto)
  - `end_time`: DateTimeField (optional)
  - `score`: PositiveIntegerField
  - `passed`: BooleanField

- **AttemptAnswer**:
  - `attempt`: ForeignKey to AssessmentAttempt
  - `question`: ForeignKey to Question
  - `selected_answer`: ForeignKey to Answer (optional)
  - `text_answer`: TextField (optional)
  - `is_correct`: BooleanField
  - `points_earned`: PositiveIntegerField

#### 3.3.5 Engagement Models

- **Review**:

  - `user`: ForeignKey to User
  - `course`: ForeignKey to Course
  - `rating`: PositiveSmallIntegerField (1-5)
  - `title`: CharField (optional)
  - `content`: TextField
  - `date_created`: DateTimeField (auto)
  - `helpful_count`: PositiveIntegerField
  - Unique constraint: (user, course)

- **Note**:

  - `user`: ForeignKey to User
  - `lesson`: ForeignKey to Lesson
  - `content`: TextField
  - `created_date`: DateTimeField (auto)
  - `updated_date`: DateTimeField (auto)

- **Certificate**:
  - `enrollment`: OneToOneField to Enrollment
  - `issue_date`: DateTimeField (auto)
  - `certificate_number`: CharField (unique)

## 4. Backend Architecture

### 4.1 API Endpoints

#### 4.1.1 Authentication Endpoints

- `POST /api/token/`: Obtain JWT token pair
- `POST /api/token/refresh/`: Refresh JWT token
- `POST /api/users/register/`: Create new user account
- `GET /api/users/me/`: Get current user profile
- `PUT /api/users/me/`: Update user profile
- `POST /api/users/change-password/`: Change user password
- `POST /api/users/request-password-reset/`: Request password reset email
- `POST /api/users/reset-password/`: Reset password with token

#### 4.1.2 Course Management Endpoints

- `GET /api/categories/`: List all categories
- `GET /api/categories/{slug}/`: Get category details
- `GET /api/courses/`: List all published courses
- `GET /api/courses/{slug}/`: Get course details
- `POST /api/courses/{slug}/enroll/`: Enroll in a course
- `GET /api/courses/{slug}/modules/`: Get course modules
- `GET /api/courses/{slug}/reviews/`: Get course reviews
- `POST /api/courses/{slug}/review/`: Add review to course
- `GET /api/modules/{id}/`: Get module details
- `GET /api/modules/{id}/lessons/`: Get module lessons
- `GET /api/lessons/{id}/`: Get lesson details
- `PUT /api/lessons/{id}/complete/`: Mark lesson as completed

#### 4.1.3 Assessment Endpoints

- `GET /api/assessments/{id}/`: Get assessment details
- `POST /api/assessments/{id}/start/`: Start assessment attempt
- `PUT /api/assessment-attempts/{id}/submit/`: Submit assessment answers

#### 4.1.4 User Progress Endpoints

- `GET /api/enrollments/`: List user enrollments
- `GET /api/user/enrollments/`: Get current user enrollments
- `GET /api/user/progress/{course_id}/`: Get progress for course

#### 4.1.5 Note Management Endpoints

- `GET /api/notes/`: List user notes
- `POST /api/notes/`: Create note
- `GET /api/notes/{id}/`: Get note details
- `PUT /api/notes/{id}/`: Update note
- `DELETE /api/notes/{id}/`: Delete note

### 4.2 Authentication System

The platform uses JWT (JSON Web Token) authentication with the following configuration:

- Access tokens valid for 15 minutes
- Refresh tokens valid for 7 days
- Token refresh mechanism via Axios interceptors
- Authorization header format: `Bearer <token>`

### 4.3 Permission System

Custom permission classes control access to resources:

- `IsEnrolled`: Allows access only to users enrolled in the related course
- `IsEnrolledOrReadOnly`: Allows read access to all, but requires enrollment for write operations
- Standard DRF permissions: `IsAuthenticated`, `IsAuthenticatedOrReadOnly`

### 4.4 Core Business Logic

#### 4.4.1 Enrollment Process

1. User requests enrollment via `POST /api/courses/{slug}/enroll/`
2. System checks if the user is already enrolled
3. If not enrolled, creates a new enrollment record with "active" status
4. Returns enrollment details to frontend

#### 4.4.2 Course Completion Logic

1. User completes a lesson via `PUT /api/lessons/{id}/complete/`
2. System marks the lesson as completed and updates progress
3. System checks if all course lessons are completed:
   - If all complete, marks enrollment as "completed"
   - Sets completion date
   - If course has certificate feature, generates certificate

#### 4.4.3 Assessment Process

1. User starts assessment via `POST /api/assessments/{id}/start/`
2. System creates assessment attempt record
3. User submits answers via `PUT /api/assessment-attempts/{id}/submit/`
4. System evaluates each answer based on question type:
   - Multiple choice: Checks if selected answer is correct
   - True/false: Checks if selected answer is correct
   - Short answer: Compares with correct answer text
5. Calculates total score and determines pass/fail status
6. If passed, marks associated lesson as completed

## 5. Frontend Architecture

### 5.1 Component Structure

```
src/
├── components/
│   ├── assessments/        # Assessment components
│   ├── blog/               # Blog components
│   │   └── BlogPostList.jsx
│   ├── common/             # Shared UI components
│   │   ├── Accordion.jsx
│   │   ├── Alert.jsx
│   │   ├── Button.jsx
│   │   ├── Card.jsx
│   │   ├── FormInput.jsx
│   │   ├── Modal.jsx
│   │   └── ...
│   ├── courses/            # Course components
│   │   └── CourseList.jsx
│   ├── layouts/            # Layout components
│   │   ├── Footer.jsx
│   │   ├── Header.jsx
│   │   └── MainLayout.jsx
│   ├── routes/             # Routing components
│   │   └── ProtectedRoute.jsx
│   └── testimonials/       # Testimonial components
│       └── TestimonialList.jsx
├── contexts/
│   └── AuthContext.jsx     # Authentication context
├── pages/
│   ├── auth/
│   │   ├── LoginPage.jsx
│   │   └── RegisterPage.jsx
│   ├── courses/
│   │   ├── AssessmentPage.jsx
│   │   ├── CourseContentPage.jsx
│   │   └── CourseLandingPage.jsx
│   ├── user/
│   │   └── ProfilePage.jsx
│   ├── HomePage.jsx
│   └── NotFoundPage.jsx
└── services/
    └── api.js              # API integration
```

### 5.2 Routing Structure

The app uses React Router 6.x with the following routes:

- `/`: Home page (public)
- `/login`: Login page (public)
- `/register`: Registration page (public)
- `/courses/:courseSlug`: Course landing page (public)
- `/courses/:courseSlug/content/:moduleId/:lessonId`: Lesson content (protected)
- `/courses/:courseSlug/assessment/:lessonId`: Assessment page (protected)
- `/profile`: User profile page (protected)
- `*`: 404 not found page

Protected routes require authentication and redirect to login if not authenticated.

### 5.3 State Management

#### 5.3.1 Authentication Context

The AuthContext provides application-wide authentication state:

- `currentUser`: Current authenticated user object
- `loading`: Authentication loading state
- `error`: Authentication error state
- `login(credentials)`: Login function
- `register(userData)`: Registration function
- `logout()`: Logout function
- `updateProfile(userData)`: Profile update function
- `resetPassword(emailData)`: Password reset function

#### 5.3.2 API Integration

The API service layer uses Axios with the following features:

- Base URL configuration from environment variables
- Request interceptor to add authentication headers
- Response interceptor for token refresh
- Automatic logout on authentication failure
- Consistent error handling

### 5.4 UI Design System

#### 5.4.1 Theme Configuration

The platform uses a custom Tailwind CSS configuration with:

- **Color Palette**:

  - Primary: Blue (#3d74f4)
  - Secondary: Orange (#ff7425)
  - Tertiary: Teal (#19b29a)
  - Various shades of each color for different UI elements

- **Typography**:

  - Body text: 'Inter' font family
  - Headings: 'Plus Jakarta Sans' font family
  - Responsive font sizes with appropriate line heights

- **Spacing System**:

  - Consistent spacing scale using Tailwind's default spacing
  - Container widths adapted for different screen sizes

- **Component Styling**:
  - Consistent border radius (rounded-xl for buttons, rounded-lg for cards)
  - Subtle shadows for elevation (shadow-sm, shadow-md)
  - Hover and active states for interactive elements

#### 5.4.2 Responsive Design

The interface follows a mobile-first approach with breakpoints:

- Default: Mobile design
- sm: 640px (Small devices)
- md: 768px (Medium devices)
- lg: 1024px (Large devices)
- xl: 1280px (Extra large devices)

#### 5.4.3 Animation System

- Subtle transitions for hover/focus states (0.3s duration)
- Reveal animations for content as user scrolls
- Loading spinners for async operations
- Micro-interactions for enhanced UX

### 5.5 Key Components

#### 5.5.1 Layout Components

- **MainLayout**: Container with header, main content, and footer
- **Header**: Navigation bar with responsive menu and user dropdown
- **Footer**: Site information, links, copyright, etc.

#### 5.5.2 Course Components

- **CourseList**: Grid display of course cards with filtering and sorting
- **CourseCard**: Visual presentation of course with thumbnail, details, and action buttons
- **ModuleAccordion**: Expandable list of modules with progress indicators
- **LessonList**: Ordered list of lessons with completion status

#### 5.5.3 Learning Experience Components

- **LessonViewer**: Content display based on lesson type with navigation controls
- **AssessmentRenderer**: Question presentation and answer submission system
- **AssessmentResult**: Score display and feedback after assessment completion

#### 5.5.4 User Interface Components

- **Button**: Configurable button with different styles and states
- **Card**: Content container with consistent styling
- **FormInput**: Input fields with validation and error states
- **Modal**: Popup dialogs for various interactions
- **Alert**: Notification display for success/error messages

## 6. Key User Flows

### 6.1 User Registration and Login

1. **Registration**:

   - User navigates to `/register`
   - Completes registration form with username, email, password
   - Form validates input (client-side)
   - On submit, POST request to `/api/users/register/`
   - If successful, user is automatically logged in
   - Redirected to homepage or onboarding

2. **Login**:
   - User navigates to `/login`
   - Enters credentials
   - On submit, POST request to `/api/token/`
   - Tokens stored in localStorage
   - User redirected to intended destination or homepage

### 6.2 Course Discovery and Enrollment

1. **Course Browsing**:

   - User browses courses on homepage or `/courses`
   - Can filter by category, level, price, etc.
   - Course cards show key information (title, instructor, rating, price)

2. **Course Details**:

   - User clicks on course to view details
   - Course landing page shows comprehensive information
   - Curriculum overview with module/lesson structure
   - Instructor information, reviews, requirements

3. **Enrollment**:
   - User clicks "Enroll" button
   - If not logged in, redirected to login page
   - After login, enrollment processed
   - Redirected to course content

### 6.3 Learning Experience

1. **Course Navigation**:

   - After enrollment, user sees course dashboard
   - Sidebar shows module/lesson structure
   - Main area displays current lesson content
   - Top navigation shows progress and course title

2. **Content Consumption**:

   - User views lesson content based on type
   - Progress automatically tracked
   - User marks lesson complete when finished
   - Navigation to next lesson

3. **Assessment Completion**:
   - User encounters assessment in curriculum
   - Starts assessment when ready
   - Answers questions within time limit (if applicable)
   - Submits assessment for grading
   - Views results with feedback
   - If passed, continues to next lesson

### 6.4 Certificate Generation

1. **Course Completion**:

   - User completes all lessons and assessments
   - System recognizes 100% completion
   - Certificate automatically generated
   - User notified of certificate availability

2. **Certificate Access**:
   - User views certificate in course completion page
   - Can download certificate as PDF
   - Certificate includes user name, course title, date, unique number

## 7. Deployment Architecture

### 7.1 Development Environment

- Local Django development server
- Vite dev server for frontend
- SQLite or PostgreSQL database
- Environment variables via .env file

### 7.2 Production Environment

- Django with Gunicorn WSGI server
- Nginx as reverse proxy and static file server
- PostgreSQL database
- Redis for caching (optional)
- Docker containers for application components
- AWS/Azure/GCP hosting options

## 8. Security Considerations

### 8.1 Authentication Security

- Passwords stored using Django's secure hashing
- JWT tokens with short expiration (15 minutes)
- Refresh token rotation for enhanced security
- CSRF protection for form submissions
- Rate limiting on authentication endpoints

### 8.2 API Security

- Proper authorization checks on all endpoints
- Input validation for all API requests
- Protection against common vulnerabilities (XSS, CSRF, SQL injection)
- Sensitive data encryption in transit (HTTPS)

### 8.3 Data Protection

- User data encrypted in database where appropriate
- Payment information handled securely
- Compliance with relevant data protection regulations
- Regular security audits and updates

## 9. Performance Optimization

### 9.1 Backend Optimizations

- Database query optimization with select_related and prefetch_related
- Caching for frequently accessed data
- Pagination for large result sets
- Efficient file storage and delivery

### 9.2 Frontend Optimizations

- Code splitting for reduced bundle size
- Lazy loading of components and assets
- Image optimization and responsive images
- Minimized network requests

## 10. Future Enhancements

### 10.1 Technical Enhancements

- Real-time features with WebSockets
- Enhanced analytics dashboard
- Mobile application
- Offline content access
- AI-powered learning recommendations

### 10.2 Feature Enhancements

- Live sessions and webinars
- Discussion forums and community features
- Gamification elements (badges, leaderboards)
- Advanced assessment types
- Integration with third-party learning tools

## 11. Requirements

### 11.1 Backend Requirements

```
Django>=4.0.0,<5.0.0
djangorestframework>=3.14.0,<4.0.0
djangorestframework-simplejwt>=5.2.0,<6.0.0
psycopg2-binary>=2.9.3,<3.0.0
Pillow>=9.0.0,<10.0.0
python-dotenv>=0.19.2,<1.0.0
gunicorn>=20.1.0,<21.0.0
whitenoise>=6.0.0,<7.0.0
```

### 11.2 Frontend Requirements

```
"react": "^18.2.0",
"react-dom": "^18.2.0",
"react-router-dom": "^6.4.0",
"axios": "^1.3.0",
"tailwindcss": "^3.2.0",
"@fortawesome/fontawesome-free": "^6.2.0"
```

## 12. Conclusion

This documentation provides a comprehensive overview of the Educational Platform project, covering its architecture, data models, API endpoints, frontend components, and user flows. The system is designed to be scalable, performant, and user-friendly, with a focus on providing an excellent learning experience for users.
